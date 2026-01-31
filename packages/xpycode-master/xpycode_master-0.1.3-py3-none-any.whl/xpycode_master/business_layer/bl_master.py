"""
Business Layer Server - Central message broker for XPyCode V3.

This module provides:
- A FastAPI application as the central message broker
- WebSocket endpoint for Add-in, IDE, and Python Kernel connections
- ConnectionManager to track active connections
- Logic to spawn Python Kernel processes for workbooks
- Message forwarding between Add-in and Python Kernel
- Smart Synchronization: workbook is source of truth for modules
"""

import asyncio
import ast
import hashlib
import json
import keyword
import logging
import re
import signal
import subprocess
import sys
import os
import time
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Union
from collections.abc import Callable
from starlette.websockets import WebSocketState
from fastapi import WebSocket, WebSocketDisconnect

from .packages import PackageManager, init_handlers
from .packages import (
    handle_package_install_request,
    handle_get_package_versions_request,
    handle_get_package_extras_request,
    handle_get_package_info_request,
    handle_add_workbook_package,
    handle_remove_workbook_package,
    handle_update_workbook_package,
    handle_restore_workbook_packages,
    handle_update_package_status,
    handle_reorder_workbook_packages,
    handle_install_workbook_packages,
    handle_get_workbook_packages,
    handle_get_resolved_deps,
    handle_update_python_paths,
)
from .dependency_resolver import DependencyResolver, PackageSpec
from .inspector_launcher import launch_inspector, terminate_inspector, is_inspector_running
from .settings_manager import SettingsManager
from .ide_manager import IDEProcessManager
from ..logging_config import get_logger


# Get logger for this module - logging is already configured by launcher
logger = get_logger(__name__)

# Maximum message size (1MB)
MAX_MESSAGE_SIZE = 1024 * 1024

# Constants for chunking
CHUNK_SIZE = 64 * 1024  # 64KB chunks (safe for most WebSocket implementations)
CHUNK_HEADER_TYPE = "chunk"

# Valid workbook ID pattern (alphanumeric, hyphens, underscores only)
VALID_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]+$")

# Valid Python identifier pattern (used for module and function names)
# Allows dots for nested modules (e.g., "package.module") but each part must be a valid identifier
VALID_PYTHON_IDENTIFIER_PART = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def compute_code_hash(code: str) -> str:
    """
    Compute SHA256 hash of code for change detection.

    Args:
        code: The source code to hash.

    Returns:
        The SHA256 hex digest of the code.
    """
    return hashlib.sha256(code.encode('utf-8')).hexdigest()


def normalize_python_paths(python_paths: List[Union[str, dict]]) -> List[str]:
    """
    Normalize python_paths to a list of strings.
    
    Handles both old dict format {"path": "...", "relative": bool} 
    and new string format for backwards compatibility.
    
    Args:
        python_paths: List of paths (can be strings or dicts)
        
    Returns:
        List of path strings (empty strings filtered out)
    """
    result = []
    for path in python_paths:
        if path is None:
            # Skip None values silently
            continue
        elif isinstance(path, dict):
            # Old format: {"path": "C:\\libs", "relative": False}
            path_str = path.get("path", "")
        elif isinstance(path, str):
            # New format: simple string
            path_str = path
        else:
            # Unknown format, skip with warning
            logger.warning(f"Skipping unknown python_path format: {type(path)} - {path}")
            continue
        
        if path_str:  # Only add non-empty strings
            result.append(path_str)
    
    return result


def validate_python_identifier(name: str) -> Tuple[bool, str]:
    """
    Validate a Python identifier or dotted name (e.g., "module.function").

    Each part separated by dots must be a valid Python identifier.
    Python keywords are not allowed to prevent code injection.

    Returns (is_valid, error_message).
    """
    if not name:
        return False, "Name cannot be empty"
    if len(name) > 256:
        return False, "Name too long (max 256 characters)"

    # Use Python's built-in keyword module for automatic updates with new Python versions
    python_keywords = set(keyword.kwlist)

    parts = name.split(".")
    for part in parts:
        if not part:
            return False, "Name contains empty parts"
        if not VALID_PYTHON_IDENTIFIER_PART.match(part):
            return False, f"Invalid identifier: {part}"
        if part in python_keywords:
            return False, f"Python keyword not allowed: {part}"

    return True, ""


def validate_client_id(client_id: str) -> Tuple[bool, str]:
    """
    Validate client ID to prevent injection attacks.

    Returns (is_valid, error_message).
    """
    if not client_id:
        return False, "Client ID cannot be empty"
    if len(client_id) > 256:
        return False, "Client ID too long (max 256 characters)"
    if not VALID_ID_PATTERN.match(client_id):
        return False, "Client ID contains invalid characters"
    return True, ""


def extract_function_parameters(code: str, function_name: str) -> List[Dict[str, str]]:
    """
    Extract parameter names and types from a function definition in Python source code.
    
    Uses ast.walk() to find functions at any level (top-level functions, class methods,
    nested functions). Excludes 'self' and 'cls' parameters which are common in methods.
    
    Args:
        code: The Python source code containing the function
        function_name: The name of the function to extract parameters from
    
    Returns:
        List of parameter dictionaries with 'name' and 'type' keys.
        Types default to "any" if annotation is missing or complex.
        Returns empty list if function not found or on parse error.
    """
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                params = []
                for arg in node.args.args:
                    # Skip 'self' and 'cls' parameters (common in methods)
                    if arg.arg not in ('self', 'cls'):
                        # Extract type annotation if present
                        param_type = "any"  # Default type
                        if arg.annotation:
                            # Try to extract simple type names
                            param_type = _extract_type_from_annotation(arg.annotation)
                        
                        params.append({
                            "name": arg.arg,
                            "type": param_type
                        })
                return params
        
        # Function not found
        return []
    except SyntaxError as e:
        logger.warning(f"Syntax error in code when extracting parameters for '{function_name}': {e}")
        return []
    except Exception as e:
        logger.warning(f"Unexpected error extracting parameters for '{function_name}': {e}")
        return []


def _extract_type_from_annotation(annotation) -> str:
    """
    Extract a simple type string from an AST annotation node.
    
    Per requirements, all types are forced to "any" regardless of Python type hints.
    This ensures maximum compatibility with Excel's dynamic typing system.
    
    Args:
        annotation: An AST node representing a type annotation (ignored)
    
    Returns:
        Always returns "any"
    """
    # Requirements: Ignore all Python type hints and always return "any"
    return "any"


class ResultBatcher:
    """
    Coalesces function results before sending to Add-in.
    
    Accumulates results for a short delay, then sends as a batch
    to reduce WebSocket message overhead.
    """
    
    COALESCE_DELAY = 0.005  # 5ms coalescing window
    
    def __init__(self, manager: 'ConnectionManager'):
        self._manager = manager
        self._pending: Dict[str, List[dict]] = {}  # workbook_id -> messages
        self._flush_tasks: Dict[str, asyncio.Task] = {}
        self._lock = asyncio.Lock()
    
    async def add_result(self, workbook_id: str, message: dict):
        """Add a result to be batched for the given workbook."""
        async with self._lock:
            if workbook_id not in self._pending:
                self._pending[workbook_id] = []
            self._pending[workbook_id].append(message)
            
            # Schedule flush if not already scheduled
            if workbook_id not in self._flush_tasks:
                self._flush_tasks[workbook_id] = asyncio.create_task(
                    self._flush_after_delay(workbook_id)
                )
    
    async def _flush_after_delay(self, workbook_id: str):
        """Wait for coalesce delay, then flush results."""
        await asyncio.sleep(self.COALESCE_DELAY)
        await self._flush_workbook(workbook_id)
    
    async def _flush_workbook(self, workbook_id: str):
        """Flush all pending results for a workbook."""
        async with self._lock:
            messages = self._pending.pop(workbook_id, [])
            self._flush_tasks.pop(workbook_id, None)
        
        if not messages:
            return
        
        if len(messages) == 1:
            # Single result - send directly
            await self._manager.send_message("addin", workbook_id, messages[0])
        else:
            # Multiple results - send as batch
            await self._manager.send_message("addin", workbook_id, {
                "type": "batch_results",
                "results": messages
            })
    
    async def flush_all(self):
        """Flush all pending results immediately."""
        async with self._lock:
            workbook_ids = list(self._pending.keys())
        
        for workbook_id in workbook_ids:
            await self._flush_workbook(workbook_id)


class ConnectionManager:
    """Manages WebSocket connections for different client types."""

    def __init__(self):
        # Structure: {client_type: {client_id: websocket}}
        self.active_connections: Dict[str, Dict[str, WebSocket]] = {
            "addin": {},
            "ide": {},
            "kernel": {},
            "inspector": {},
        }
        # Track kernel processes: {workbook_id: subprocess}
        self.kernel_processes: Dict[str, subprocess.Popen] = {}
        # Track client names: {client_id: name}
        self.client_names: Dict[str, str] = {}
        # Module storage per workbook: {workbook_id: {module_name: code}}
        # This serves as an in-memory cache; the workbook is the source of truth
        self.workbook_modules: Dict[str, Dict[str, str]] = {}
        # Generic pending requests cache: {request_id: asyncio.Future}
        self._pending_requests: Dict[str, asyncio.Future] = {}
        # Track synced module hashes per workbook: {workbook_id: {module_name: hash}}
        # Used for full code sync to detect which modules have changed since last sync
        self._synced_hashes: Dict[str, Dict[str, str]] = {}
        
        # Event System State Management
        # Workbook tree structure from Add-in: {workbook_id: tree_dict}
        self.workbook_tree: Dict[str, dict] = {}
        # Event definitions from Add-in: {workbook_id: event_definitions_dict}
        self.event_definitions: Dict[str, dict] = {}
        # Registered event handlers: {workbook_id: {(object_id, event_name): {"module_name": "...", "function_name": "..."}}}
        self.registered_handlers: Dict[str, Dict[tuple, dict]] = {}
        
        # UDF/Custom Functions State Management
        # Published functions per workbook: {workbook_id: [{"module_name": "...", "function_name": "...", "excel_name": "..."}, ...]}
        self.published_functions: Dict[str, List[Dict[str, str]]] = {}
        
        # Track function_execution requests by request_id: {request_id: workbook_id}
        # This is used to send function_execution_result back to the add-in
        self._pending_function_executions: Dict[str, str] = {}
        
        # Per-workbook package lists: {workbook_id: [{"name": str, "version": str, "extras": list, "status": str}, ...]}
        self.workbook_packages: Dict[str, List[dict]] = {}
        
        # Resolved dependencies per workbook (for IDE readonly popup)
        # {workbook_id: [{"name": str, "version": str, "extras": list, "is_direct": bool}, ...]}
        self.workbook_resolved_deps: Dict[str, List[dict]] = {}
        
        # Current package paths per workbook (for kernel cleanup)
        # {workbook_id: [path1, path2, ...]}
        self.workbook_package_paths: Dict[str, List[str]] = {}
        
        # Per-package pip outputs: {workbook_id: {package_name: [output_lines]}}
        self.workbook_pip_outputs: Dict[str, Dict[str, List[str]]] = {}
        
        # Last installed packages per workbook (for restore)
        # {workbook_id: [{"name": str, "version": str, "extras": list}, ...]}
        self.workbook_installed_packages: Dict[str, List[dict]] = {}
        
        # Package errors per workbook: {workbook_id: {package_name: [error_messages]}}
        self.package_errors: Dict[str, Dict[str, List[str]]] = {}
        
        # Per-package stderr outputs: {workbook_id: {package_key: [stderr_lines]}}
        # package_key format: "name==version[extras]"
        self.package_stderr: Dict[str, Dict[str, List[str]]] = {}
        
        # Python paths per workbook: {workbook_id: [path_str, ...]}
        # Normalized to list of strings (old dict format converted on input)
        self.workbook_python_paths: Dict[str, List[str]] = {}
        
        # Result batcher for coalescing function results
        self._result_batcher = ResultBatcher(self)
        
        # Chunk reassembly buffers: {client_id: {chunk_id: {chunks: [...], received: int, total: int}}}
        self._chunk_buffers: Dict[str, Dict[str, dict]] = {}


    async def connect(
        self, client_type: str, client_id: str, websocket: WebSocket, name: Optional[str] = None
    ):
        """Accept and register a new WebSocket connection."""
        await websocket.accept()
        if client_type not in self.active_connections:
            self.active_connections[client_type] = {}
        self.active_connections[client_type][client_id] = websocket
        if name:
            self.client_names[client_id] = name

    def disconnect(self, client_type: str, client_id: str):
        """Remove a WebSocket connection."""
        if (
            client_type in self.active_connections
            and client_id in self.active_connections[client_type]
        ):
            del self.active_connections[client_type][client_id]
        # Clean up client name
        if client_id in self.client_names:
            del self.client_names[client_id]

    def get_connection(
        self, client_type: str, client_id: str
    ) -> Optional[WebSocket]:
        """Get a specific connection."""
        return self.active_connections.get(client_type, {}).get(client_id)

    async def send_message(self, client_type: str, client_id: str, message: dict):
        """Send a JSON message to a specific client."""
        websocket = self.get_connection(client_type, client_id)
        if websocket:
            await websocket.send_json(message)
    
    async def send_to_ide(self, message: dict):
        """Send a message to IDE clients (broadcast)."""
        await self.broadcast("ide", message)
    
    async def send_to_addin(self, workbook_id: str, message: dict):
        """Send a message to a specific addin."""
        await self.send_message("addin", workbook_id, message)
    
    async def send_and_wait_response(
        self,
        client_type: str,
        client_id: str,
        message: dict,
        timeout: float = 30.0
    ) -> dict:
        """
        Send a message to a client and wait for a response.
        
        Args:
            client_type: "addin" or "ide"
            client_id: The client identifier (e.g., workbook_id for addin)
            message: The message dict to send (can use "request_id" or "requestId")
            timeout: Timeout in seconds (default 30)
        
        Returns:
            The response message dict
        
        Raises:
            TimeoutError: If no response received within timeout
            ConnectionError: If client not connected
            Exception: If response contains an error
        
        Note:
            The Add-in uses camelCase "requestId" while Python code uses snake_case "request_id".
            This method accepts both but normalizes to "request_id" internally for consistency.
            The generated request_id is added to the message with the key "request_id".
        """
        # Generate request_id if not present (check both naming conventions)
        request_id = message.get("request_id") or message.get("requestId")
        if not request_id:
            request_id = str(uuid.uuid4())
        # Always use request_id internally for consistency
        message["request_id"] = request_id
        message["requestId"] = request_id
        
        # Create future for response
        loop = asyncio.get_event_loop()
        future: asyncio.Future = loop.create_future()
        self._pending_requests[request_id] = future
        
        try:

            websocket = self.get_connection(client_type, client_id)
            if not websocket:
                raise ConnectionError(f"{client_type} {client_id} not connected")
            
            # Send the message
            await websocket.send_json(message)
            logger.debug(f"Sent message to {client_type} {client_id}: {message.get('type')}")
            
            # Wait for response with timeout
            response = await asyncio.wait_for(future, timeout=timeout)
            
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"Timeout waiting for response to {message.get('type')} from {client_type} {client_id}")
            raise TimeoutError(f"Timeout waiting for response from {client_type} {client_id}")
        finally:
            # Always clean up pending request
            self._pending_requests.pop(request_id, None)
    
    def handle_response(self, message: dict) -> bool:
        """
        Handle a response message by completing the pending request future.
        
        Args:
            message: The response message dict
        
        Returns:
            True if this was a pending request response, False otherwise
        """
        request_id = message.get("request_id") or message.get("requestId")
        if not request_id:
            return False
        
        future = self._pending_requests.get(request_id)
        if future and not future.done():
            future.set_result(message)
            logger.debug(f"Completed pending request: {request_id}")
            return True
        
        return False

    async def broadcast(self, client_type: str, message: dict):
        """
        Broadcast a message to all clients of a specific type in parallel.
        
        Uses asyncio.gather with return_exceptions=True to prevent one client
        failure from affecting others. Note: Disconnected clients should be
        cleaned up by the disconnect handler.
        """

        connections = self.active_connections.get(client_type, {})
        if connections:
            await asyncio.gather(*[
                websocket.send_json(message) 
                for websocket in connections.values()
            ], return_exceptions=True)
    
    async def _handle_chunk_message(self, client_type: str, client_id: str, message: dict) -> Optional[dict]:
        """
        Handle a chunk message and return the reassembled message when complete.
        Returns None if more chunks are expected.
        """
        chunk_id = message.get("chunk_id")
        chunk_index = message.get("chunk_index")
        total_chunks = message.get("total_chunks")
        chunk_data = message.get("data", "")
        
        # Validate chunk parameters
        if chunk_index is None or total_chunks is None or chunk_id is None:
            logger.error("[BusinessLayer] Invalid chunk message: missing required fields")
            return None
        
        if not isinstance(chunk_index, int) or not isinstance(total_chunks, int):
            logger.error("[BusinessLayer] Invalid chunk message: chunk_index and total_chunks must be integers")
            return None
        
        if chunk_index < 0 or chunk_index >= total_chunks:
            logger.error(f"[BusinessLayer] Invalid chunk_index {chunk_index} for total_chunks {total_chunks}")
            return None
        
        # Initialize buffer for this client if needed
        if client_id not in self._chunk_buffers:
            self._chunk_buffers[client_id] = {}
        
        # Initialize buffer for this chunk_id if needed
        if chunk_id not in self._chunk_buffers[client_id]:
            self._chunk_buffers[client_id][chunk_id] = {
                "chunks": [None] * total_chunks,
                "received": 0,
                "total": total_chunks
            }
        
        buffer = self._chunk_buffers[client_id][chunk_id]
        
        # Store the chunk
        if buffer["chunks"][chunk_index] is None:
            buffer["chunks"][chunk_index] = chunk_data
            buffer["received"] += 1
        
        # Check if all chunks received
        if buffer["received"] == buffer["total"]:
            # Verify all chunks are present (prevent None in join)
            if any(chunk is None for chunk in buffer["chunks"]):
                logger.error(f"[BusinessLayer] Incomplete chunk buffer for chunk_id {chunk_id}")
                del self._chunk_buffers[client_id][chunk_id]
                return None
            
            # Reassemble the message
            full_json = "".join(buffer["chunks"])
            del self._chunk_buffers[client_id][chunk_id]
            
            try:
                reassembled = json.loads(full_json)
                # Prevent recursive chunk nesting - if reassembled message is also a chunk, reject it
                if isinstance(reassembled, dict) and reassembled.get("type") == "chunk":
                    logger.error(f"[BusinessLayer] Nested chunk message detected for chunk_id {chunk_id}, rejecting")
                    return None
                return reassembled
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse reassembled message: {e}")
                return None
        
        return None
    
    async def send_message_with_chunking(self, client_type: str, client_id: str, message: dict):
        """Send a JSON message to a specific client, chunking if necessary."""
        websocket = self.get_connection(client_type, client_id)
        if not websocket:
            return
        
        raw_json = json.dumps(message)
        
        if len(raw_json) > CHUNK_SIZE:
            await self._send_chunked_to_client(websocket, raw_json, message)
        else:
            await websocket.send_json(message)
    
    async def _send_chunked_to_client(self, websocket, raw_json: str, original_message: dict):
        """Send a large message in chunks to a client."""
        chunk_id = str(uuid.uuid4())
        total_chunks = (len(raw_json) + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        logger.info(f"[BusinessLayer] Chunking large message: type={original_message.get('type')}, size={len(raw_json)}, chunks={total_chunks}")
        
        for i in range(total_chunks):
            start = i * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(raw_json))
            chunk_data = raw_json[start:end]
            
            chunk_message = {
                "type": "chunk",
                "chunk_id": chunk_id,
                "chunk_index": i,
                "total_chunks": total_chunks,
                "data": chunk_data,
                "original_type": original_message.get("type", "unknown")
            }
            await websocket.send_json(chunk_message)
        
        logger.debug(f"[BusinessLayer] Sent {total_chunks} chunks, chunk_id={chunk_id}")

    def spawn_kernel(self, workbook_id: str) -> Optional[subprocess.Popen]:
        """
        Spawn a new Python Kernel process for a workbook.

        Returns the process if successful, None if validation fails or spawn fails.
        """
        # Validate workbook_id before using in subprocess
        is_valid, error = validate_client_id(workbook_id)
        if not is_valid:
            logger.error(f"Invalid workbook_id: {error}")
            return None

        '''
        kernel_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "python_server",
            "kernel.py",
        )
        '''
        kernel_path='xpycode_master.python_server'

        try:
            process = subprocess.Popen(
                [sys.executable,'-m', kernel_path, workbook_id, str(_port)],
                stdout=sys.stdout,
                stderr=sys.stderr,
            )
            self.kernel_processes[workbook_id] = process
            logger.info(f"Spawned kernel for workbook: {workbook_id}")
            return process
        except (OSError, subprocess.SubprocessError) as e:
            logger.error(f"Failed to spawn kernel for {workbook_id}: {e}")
            return None

    def terminate_kernel(self, workbook_id: str):
        """Terminate a kernel process."""
        if workbook_id in self.kernel_processes:
            process = self.kernel_processes[workbook_id]
            process.terminate()
            del self.kernel_processes[workbook_id]

    def kill_and_restart_kernel(self, workbook_id: str) -> bool:
        """
        Hard kill and restart a kernel process for a workbook.
        
        Args:
            workbook_id: The workbook identifier.
            
        Returns:
            True if kernel was killed and restarted successfully, False otherwise.
        """
        # Check if kernel exists
        if workbook_id not in self.kernel_processes:
            logger.warning(f"No kernel found for workbook: {workbook_id}")
            return False
        
        process = self.kernel_processes[workbook_id]
        pid = process.pid
        logger.info(f"Killing kernel for workbook {workbook_id} (PID: {pid})")
        
        # Hard kill using platform-specific method
        try:
            if sys.platform == 'win32':
                # Windows: Use taskkill with /F /T /PID flags
                subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(pid)],
                    capture_output=True
                )
            else:
                # Unix: Use SIGTERM first, then SIGKILL if needed
                try:
                    os.killpg(os.getpgid(pid), signal.SIGTERM)
                    # Wait briefly for graceful shutdown
                    time.sleep(0.2)
                    # Check if process terminated, kill with SIGKILL if still alive
                    try:
                        os.kill(pid, 0)  # Test if process exists
                        # Still alive, use SIGKILL
                        os.killpg(os.getpgid(pid), signal.SIGKILL)
                    except ProcessLookupError:
                        # Process already dead
                        pass
                except ProcessLookupError:
                    # Process group doesn't exist, try direct kill
                    try:
                        os.kill(pid, signal.SIGTERM)
                        time.sleep(0.2)
                        # Check if process terminated
                        try:
                            os.kill(pid, 0)  # Test if process exists
                            os.kill(pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    except ProcessLookupError:
                        pass
        except Exception as e:
            logger.error(f"Error killing kernel process {pid}: {e}")
        
        # Remove from tracking
        del self.kernel_processes[workbook_id]
        
        # Remove from active connections if exists
        if workbook_id in self.active_connections.get('kernel', {}):
            del self.active_connections['kernel'][workbook_id]
        
        # Wait briefly for cleanup
        time.sleep(0.5)
        
        # Spawn new kernel
        new_process = self.spawn_kernel(workbook_id)
        if new_process:
            logger.info(f"Successfully restarted kernel for workbook: {workbook_id}")
            return True
        else:
            logger.error(f"Failed to restart kernel for workbook: {workbook_id}")
            return False

    def save_module(self, workbook_id: str, module_name: str, code: str):
        """
        Save a module's code for a workbook.

        Args:
            workbook_id: The workbook identifier.
            module_name: The module name (without .py extension).
            code: The module's source code.
        """
        if workbook_id not in self.workbook_modules:
            self.workbook_modules[workbook_id] = {}
        self.workbook_modules[workbook_id][module_name] = code
        logger.debug(f"Saved module '{module_name}' for workbook '{workbook_id}'")

    def delete_module(self, workbook_id: str, module_name: str) -> bool:
        """
        Delete a module from a workbook.

        Args:
            workbook_id: The workbook identifier.
            module_name: The module name to delete.

        Returns:
            True if module was deleted, False if not found.
        """
        if workbook_id in self.workbook_modules:
            if module_name in self.workbook_modules[workbook_id]:
                del self.workbook_modules[workbook_id][module_name]
                logger.debug(f"Deleted module '{module_name}' from workbook '{workbook_id}'")
                return True
        return False

    def get_module(self, workbook_id: str, module_name: str) -> Optional[str]:
        """
        Get a module's code for a workbook.

        Args:
            workbook_id: The workbook identifier.
            module_name: The module name.

        Returns:
            The module's code, or None if not found.
        """
        return self.workbook_modules.get(workbook_id, {}).get(module_name)

    def list_modules(self, workbook_id: str) -> Dict[str, str]:
        """
        List all modules for a workbook from the in-memory cache.

        Args:
            workbook_id: The workbook identifier.

        Returns:
            Dictionary of {module_name: code} for the workbook.
        """
        return self.workbook_modules.get(workbook_id, {})

    async def request_modules_from_addin(self, workbook_id: str) -> Dict[str, str]:
        """
        Request the list of all modules from the Excel Add-in (workbook source of truth).

        This sends a get_modules_request to the Add-in and waits for the response.
        The modules are then cached in workbook_modules.

        Args:
            workbook_id: The workbook identifier.

        Returns:
            Dictionary of {module_name: code} for the workbook.
        """
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "get_modules_request",
                },
                timeout=10.0
            )
            modules = response.get("modules", {})
            # Update cache
            self.workbook_modules[workbook_id] = modules
            logger.debug(f"Fetched {len(modules)} modules from workbook: {workbook_id}")
            return modules
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error fetching modules from workbook {workbook_id}: {e}")
            return {}

    async def request_functions_from_addin(self, workbook_id: str) -> Optional[List[dict]]:
        """
        Request published functions from the add-in.
        
        Sends get_functions_request to add-in and waits for response.
        Response format matches client_sync_functions message.
        
        Args:
            workbook_id: The workbook ID to request functions for
            
        Returns:
            List of function dicts or None if request fails/times out
        """
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "get_functions_request",
                },
                timeout=10.0
            )
            functions = response.get("functions", [])
            logger.info(f"Received {len(functions)} functions from addin for workbook {workbook_id}")
            return functions
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error requesting functions from addin for workbook {workbook_id}: {e}")
            return None

    async def request_packages_from_addin(self, workbook_id: str) -> Optional[dict]:
        """
        Request packages and python paths from the add-in.
        
        Sends get_packages_request to add-in and waits for response.
        Response format matches client_sync_packages message.
        
        Args:
            workbook_id: The workbook ID to request packages for
            
        Returns:
            Dict with 'packages' and 'python_paths' keys, or None if request fails/times out
        """
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "get_packages_request",
                },
                timeout=10.0
            )
            packages = response.get("packages", [])
            python_paths = response.get("python_paths", [])
            logger.info(f"Received {len(packages)} packages and {len(python_paths)} python paths from addin for workbook {workbook_id}")
            return {
                "packages": packages,
                "python_paths": python_paths
            }
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error requesting packages from addin for workbook {workbook_id}: {e}")
            return None


    async def request_events_info_from_addin(self, workbook_id: str) -> Optional[dict]:
        """
        Request events info( registered events, events definition and event objects tree) from the add-in.
        
        Sends get_events_request to add-in and waits for response.
        
        Args:
            workbook_id: The workbook ID to request packages for
            
        Returns:
            Dict with 'events_registered', 'events_defintion' and 'events_tree' keys, or None if request fails/times out
        """
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "get_events_request",
                },
                timeout=10.0
            )
            events_registered = response.get("events_registered", {}) or {}
            events_definition = response.get("events_definition", {}) or {}
            events_tree = response.get("events_tree", {}) or {}
            logger.info(f"Received {len(events_registered)} events_registered and {len(events_definition)} events_definition and {len(events_tree)} events_tree from addin for workbook {workbook_id}")
            return {
                "events_registered": events_registered,
                "events_definition": events_definition,
                "events_tree": events_tree,
            }
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error requesting events from addin for workbook {workbook_id}: {e}")
            return None


    async def save_module_to_addin(self, workbook_id: str, module_name: str, code: str) -> bool:
        """
        Save a module to the Excel Add-in (workbook source of truth).

        This sends a save_module_request to the Add-in and waits for confirmation.

        Args:
            workbook_id: The workbook identifier.
            module_name: The module name (without .py extension).
            code: The module's source code.

        Returns:
            True if save was successful, False otherwise.
        """
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "save_module_request",
                    "module_name": module_name,
                    "code": code,
                },
                timeout=10.0
            )
            success = response.get("success", False)
            if success:
                # Update cache
                if workbook_id not in self.workbook_modules:
                    self.workbook_modules[workbook_id] = {}
                self.workbook_modules[workbook_id][module_name] = code
                logger.debug(f"Saved module '{module_name}' to workbook: {workbook_id}")
            return success
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error saving module to workbook {workbook_id}: {e}")
            return False

    async def load_module_from_addin(self, workbook_id: str, module_name: str) -> Optional[str]:
        """
        Load a specific module from the Excel Add-in (workbook source of truth).

        Args:
            workbook_id: The workbook identifier.
            module_name: The module name (without .py extension).

        Returns:
            The module's source code, or None if not found.
        """
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "load_module_request",
                    "module_name": module_name,
                },
                timeout=10.0
            )
            code = response.get("code")
            if code is not None:
                # Update cache
                if workbook_id not in self.workbook_modules:
                    self.workbook_modules[workbook_id] = {}
                self.workbook_modules[workbook_id][module_name] = code
                logger.debug(f"Loaded module '{module_name}' from workbook: {workbook_id}")
            return code
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error loading module from workbook {workbook_id}: {e}")
            return None

    async def delete_module_from_addin(self, workbook_id: str, module_name: str) -> bool:
        """
        Delete a module from the Excel Add-in (workbook source of truth).

        Args:
            workbook_id: The workbook identifier.
            module_name: The module name (without .py extension).

        Returns:
            True if delete was successful, False otherwise.
        """
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "delete_module_request",
                    "module_name": module_name,
                },
                timeout=10.0
            )
            success = response.get("success", False)
            if success:
                # Update cache
                if workbook_id in self.workbook_modules:
                    self.workbook_modules[workbook_id].pop(module_name, None)
                logger.debug(f"Deleted module '{module_name}' from workbook: {workbook_id}")
            return success
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error deleting module from workbook {workbook_id}: {e}")
            return False

    # ------------ Event System Methods
    
    def handle_workbook_structure_update(self, workbook_id: str, tree: dict):
        """
        Handle workbook structure update from Add-in.
        
        Updates local tree state and pushes merged state to IDE.
        
        Args:
            workbook_id: The workbook identifier
            tree: The workbook tree structure from Add-in
        """
        logger.info(f"Received workbook structure update for: {workbook_id}")
        self.workbook_tree[workbook_id] = tree
        
        # Push updated state to IDE
        asyncio.create_task(self._push_event_manager_state(workbook_id))
    
    def handle_event_definitions_update(self, workbook_id: str, definitions: dict):
        """
        Handle event definitions update from Add-in.
        
        Updates local event definitions and pushes merged state to IDE.
        
        Args:
            workbook_id: The workbook identifier
            definitions: Event definitions dictionary from Add-in
        """
        logger.info(f"Received event definitions for: {workbook_id}")
        self.event_definitions[workbook_id] = definitions
        
        # Push updated state to IDE
        asyncio.create_task(self._push_event_manager_state(workbook_id))
    
    async def handle_register_handler(
        self, workbook_id: str, object_type: str, object_id: str, 
        event_name: str, module_name: str, function_name: str
    ) -> bool:
        """
        Handle register_handler request from IDE.
        
        Updates local registry and forwards request to Add-in.
        
        Args:
            workbook_id: The workbook identifier
            object_type: The Excel object type
            object_id: The Excel object ID
            event_name: The event name (e.g., "onSelectionChanged")
            module_name: The Python module name
            function_name: The Python function name
            
        Returns:
            True if registration successful, False otherwise
        """
        logger.info(f"Registering handler: {workbook_id}/{object_type}[{object_id}].{event_name} -> {module_name}.{function_name}")
        
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "register_handler_request",
                    "object_type": object_type,
                    "object_id": object_id,
                    "event_name": event_name,
                    "module_name": module_name,
                    "function_name": function_name,
                },
                timeout=10.0
            )
            success = response.get("success", False)
            if success:
                # Update local registry with split fields
                if workbook_id not in self.registered_handlers:
                    self.registered_handlers[workbook_id] = {}
                self.registered_handlers[workbook_id][(object_id, event_name)] = {
                    "module_name": module_name,
                    "function_name": function_name,
                    "object_type":object_type
                }
                logger.debug(f"Registered handler in local registry")
                
                # Push updated state to IDE
                await self._push_event_manager_state(workbook_id)
            return success
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error registering handler: {e}")
            return False
    
    async def handle_unregister_handler(
        self, workbook_id: str, object_id: str, event_name: str
    ) -> bool:
        """
        Handle unregister_handler request from IDE.
        
        Updates local registry and forwards request to Add-in.
        
        Args:
            workbook_id: The workbook identifier
            object_id: The Excel object ID
            event_name: The event name (e.g., "onSelectionChanged")
            
        Returns:
            True if unregistration successful, False otherwise
        """
        logger.info(f"Unregistering handler: {workbook_id}/{object_id}.{event_name}")
        
        try:
            response = await self.send_and_wait_response(
                client_type="addin",
                client_id=workbook_id,
                message={
                    "type": "unregister_handler_request",
                    "object_id": object_id,
                    "event_name": event_name,
                },
                timeout=10.0
            )
            success = response.get("success", False)
            if success:
                # Update local registry
                if workbook_id in self.registered_handlers:
                    key = (object_id, event_name)
                    self.registered_handlers[workbook_id].pop(key, None)
                logger.debug(f"Unregistered handler from local registry")
                
                # Push updated state to IDE
                await self._push_event_manager_state(workbook_id)
            return success
        except (TimeoutError, ConnectionError) as e:
            logger.warning(f"Error unregistering handler: {e}")
            return False
    
 
    def _merge_tree_with_events(self, tree: dict, definitions: dict, registry: dict) -> list:
        """
        Recursively merge tree structure with event definitions and registry.
        
        Creates a unified view model containing object hierarchy with embedded event data.
        
        Args:
            tree: Workbook tree structure (hierarchical dict with type, id, name, children)
            definitions: Event definitions dict (maps object type to list of event definitions)
            registry: Registered handlers dict (maps (object_id, event_name) to dict with module_name and function_name)
            
        Returns:
            List representing the merged view model for the root node's children
        """
        def merge_node(node: dict) -> dict:
            """
            Merge a single node with its events and children.
            
            Args:
                node: Node dict with type, id, name, children
                
            Returns:
                Merged node dict with events list and merged children
            """
            node_type = node.get("type", "")
            node_id = node.get("id", "")
            node_name = node.get("name", "")
            children = node.get("children", [])
            
            # Get event definitions for this object type
            type_events = definitions.get(node_type, [])
            
            # Build events list with assigned functions
            events_list = []
            for event_def in type_events:
                event_type = event_def.get("eventType", "")
                event_name = event_def.get("eventName", "")
                arg_type = event_def.get("eventArgsType", "")
                
                # Look up assigned function from registry using event_name
                handler_info = registry.get((node_id, event_name), {})
                
                # Build python_function string for IDE display (module.function)
                if isinstance(handler_info, dict):
                    module_name = handler_info.get("module_name", "")
                    function_name = handler_info.get("function_name", "")
                    python_function = f"{module_name}.{function_name}" if module_name and function_name else ""
                else:
                    # Should not happen with new format
                    python_function = ""
                
                events_list.append({
                    "name": event_name,
                    "type": event_type,
                    "arg_type": arg_type,
                    "python_function": python_function
                })
            
            # Recursively merge children
            merged_children = [merge_node(child) for child in children]
            
            # Build merged node
            merged = {
                "id": node_id,
                "name": node_name,
                "type": node_type,
                "events": events_list,
                "children": merged_children
            }
            
            return merged
        
        # If tree is empty, return empty list
        if not tree:
            return []
        
        # Merge the root node
        merged_root = merge_node(tree)
        
        # Return as a single-element list (root wrapped)
        return [merged_root]
    
    async def _push_event_manager_state(self, workbook_id: str, websocket: Optional[WebSocket]=None):
        """
        Push merged event manager state to IDE.
        
        Creates a unified view_model by merging tree, event definitions, and handlers,
        then sends it to the IDE.
        
        Args:
            workbook_id: The workbook identifier
        """
        # Get raw data
        tree = self.workbook_tree.get(workbook_id, {})
        definitions = self.event_definitions.get(workbook_id, {})
        handlers = self.registered_handlers.get(workbook_id, {})
        
        # Merge tree with events and handlers into unified view_model
        view_model = self._merge_tree_with_events(tree, definitions, handlers)
        
        # Send the merged view_model to all IDEs (with workbook_id for routing)
        # Note: IDEs can manage multiple workbooks, so we broadcast to all IDEs
        # and include workbook_id for client-side routing to the correct EventManager
        state = {
            "type": "event_manager_state",
            "workbook_id": workbook_id,
            "view_model": view_model
        }
        
        try:
            if websocket:
                await websocket.send_json(state)
                logger.debug(f"Pushed merged event manager state to IDE websocket for: {workbook_id}. {len(handlers)} handlers.")
            else:
                await self.broadcast("ide", state)
            logger.debug(f"Pushed merged event manager state to IDE for: {workbook_id}. {len(handlers)} handlers.")
        except Exception as e:
            logger.error(f"Error pushing event manager state: {e}")
    
    # ------------ UDF/Custom Functions Methods
    
    def _validate_function_entry(self, func: dict) -> bool:
        """
        Validate a function entry structure.
        
        Args:
            func: Function dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        # Check required fields
        if not isinstance(func, dict):
            return False
        if "module_name" not in func or "function_name" not in func or "excel_name" not in func:
            return False
        
        # Dimension and streaming are optional for backward compatibility
        # They will be added with defaults if missing
        return True
    
    async def handle_update_published_functions(self, workbook_id: str, functions: List[Dict[str, str]]):
        """
        Handle update_published_functions request from IDE.
        
        Updates server-side state and forwards sync_custom_functions to Add-in.
        
        Args:
            workbook_id: The workbook identifier
            functions: List of dicts with 'module_name', 'function_name', 'excel_name', 'dimension', and 'streaming' keys
        """
        logger.info(f"Updating published functions for workbook: {workbook_id}, count: {len(functions)}")
        
        # Update server-side state (last-writer-wins strategy)
        # The server broadcasts the new state back to all IDEs to maintain consistency
        # across multiple connections. This is acceptable for this use case as:
        # 1. Updates are typically initiated by a single IDE at a time
        # 2. All IDEs receive the broadcasted state and synchronize their UI
        self.published_functions[workbook_id] = functions
        
        # Forward sync_custom_functions message to Add-in
        await self._push_custom_functions_to_addin(workbook_id, functions)
        
        # Also push state back to IDEs for synchronization
        await self._push_published_functions_state(workbook_id, functions)
    
    async def _push_custom_functions_to_addin(self, workbook_id: str, functions: Optional[List[Dict[str, str]]]=None):
        """
        Push custom functions to the Add-in for registration.
        
        Extracts parameter names and types from function source code and includes them in the message.
        Parameter types default to "any" if annotation is missing or complex to ensure Excel compatibility.
        
        Args:
            workbook_id: The workbook identifier
            functions: List of dicts with 'module_name', 'function_name', 'excel_name', 'dimension', and 'streaming' keys
        """
        functions=functions or self.published_functions.get(workbook_id,[])
        
        # Get the modules for this workbook to extract parameter information
        modules = self.workbook_modules.get(workbook_id, {})
        
        # Enhance function list with parameter information
        enhanced_functions = []
        for func in functions:
            module_name = func.get("module_name", "")
            function_name = func.get("function_name", "")
            excel_name = func.get("excel_name", "")
            dimension = func.get("dimension", "Scalar")
            streaming = func.get("streaming", False)
            
            if not module_name or not function_name:
                logger.warning(f"Skipping function with missing module_name or function_name: {func}")
                continue
            
            # Get the module code
            module_code = modules.get(module_name, "")
            
            # Extract parameters from the function
            parameters = extract_function_parameters(module_code, function_name)
            
            enhanced_functions.append({
                "module": module_name,
                "function": function_name,
                "excel_name": excel_name,
                "parameters": parameters,
                "dimension": dimension,
                "streaming": streaming
            })
        
        message = {
            "type": "sync_custom_functions",
            "functions": enhanced_functions
        }
        
        try:
            await self.send_to_addin(workbook_id,message)
            logger.debug(f"Pushed custom functions to Add-in for: {workbook_id}")
        except Exception as e:
            logger.error(f"Error pushing custom functions to Add-in: {e}")
    
    async def _push_published_functions_state(self, workbook_id: str, functions: Optional[List[Dict[str, str]]]=None, websocket: Optional[WebSocket]=None):
        """
        Push published functions state to all IDEs.
        
        Args:
            workbook_id: The workbook identifier
            functions: List of dicts with 'module_name', 'function_name', 'excel_name', 'dimension', and 'streaming' keys
        """
        if functions is None:
            functions=manager.published_functions.get(workbook_id,[])

        state = {
            "type": "published_functions_state",
            "workbook_id": workbook_id,
            "functions": functions
        }
        
        try:
            if websocket:
                await websocket.send_json(state)
                logger.debug(f"Pushed published functions state to IDE websocket for: {workbook_id}")
            else:
                await self.broadcast("ide", state)
            logger.debug(f"Pushed published functions state to IDE for: {workbook_id}")
        except Exception as e:
            logger.error(f"Error pushing published functions state: {e}")


    async def _push_modules(self, workbook_id: str, modules: Optional[Dict[str,str]]=None, websocket: Optional[WebSocket]=None):
        """
        Push modules state to all IDEs.
        
        Args:
            workbook_id: The workbook identifier
            modules: Dict of {module_name: code}
            websocket: Optional WebSocket to send to a specific IDE connection
        """
        modules= modules or self.workbook_modules.get(workbook_id,{})

        state = {
            "type": "workbook_connected",
            "workbook_id": workbook_id,
            "modules": modules,
            "name":self.client_names.get(workbook_id,"")

        }
        
        try:
            if websocket:
                await websocket.send_json(state)
                logger.debug(f"Pushed modules state to IDE websocket for: {workbook_id}")
            else:
                await self.broadcast("ide", state)
            logger.debug(f"Pushed modules state to IDE for: {workbook_id}")
        except Exception as e:
            logger.error(f"Error pushing modules state: {e}")


    async def _push_packages_and_python_paths(self, workbook_id: str, packages: Optional[List[str]]=None, python_paths: Optional[List[str]]=None, package_errors: Optional[Dict]=None, websocket: Optional[WebSocket]=None):
        """
        Push packages and python paths state to all IDEs.
        
        Args:
            workbook_id: The workbook identifier
            packages: List of package names
            python_paths: List of python paths
            package_errors: Dict of package installation errors
            websocket: Optional WebSocket to send to a specific IDE connection
        """

        packages= packages or manager.workbook_packages.get(workbook_id,[])
        python_paths=python_paths or manager.workbook_python_paths.get(workbook_id,[])
        package_errors=package_errors or manager.package_errors.get(workbook_id,{})
        
        state = {
            "type": "workbook_packages_update",
            "workbook_id": workbook_id,
            "packages": packages,
            "python_paths":python_paths,
            "package_errors": package_errors
        }
        
        try:
            if websocket:
                await websocket.send_json(state)
                logger.debug(f"Pushed packages and python paths state to IDE websocket for: {workbook_id}")
            else:
                await self.broadcast("ide", state)
            logger.debug(f"Pushed packages and python paths state to IDE for: {workbook_id}")
        except Exception as e:
            logger.error(f"Error pushing packages and python paths state: {e}")


    async def _push_events_config_to_addin(self, workbook_id: str, events_config: Optional[dict]=None, save: bool=True, websocket: Optional[WebSocket]=None):
        """
        Push events configuration to all IDEs.
        
        Args:
            workbook_id: The workbook identifier
            events_config: Events configuration dict
            websocket: Optional WebSocket to send to a specific IDE connection
        """
        events_config= events_config or self.registered_handlers.get(workbook_id,{})
        state = {
            "type": "save_event_config_request",
            "workbook_id": workbook_id,
            "config": _events_from_ide_to_addin(events_config),
            "request_id": (request_id:=str(uuid.uuid4())),
            "requestId": request_id,  # For backward compatibility,
            "save":save,
        }
        
        try:
            if websocket:
                await websocket.send_json(state)
                logger.debug(f"Pushed events configuration to IDE websocket for: {workbook_id}")
            else:
                await self.send_to_addin(workbook_id, state)
            logger.debug(f"Pushed events configuration to IDE for: {workbook_id}")
        except Exception as e:
            logger.error(f"Error pushing events configuration: {e}")

    async def _push_object_clear(self, workbook_id: str, websocket: Optional[WebSocket]=None):
        """
        Push object clear command to all IDEs.
        
        Args:
            workbook_id: The workbook identifier
            websocket: Optional WebSocket to send to a specific IDE connection
        """
        state = {
            "type": "object_registry_update",
            "action": "clear_all",
            "workbook_id": workbook_id,
        }
        
        try:
            if websocket:
                await websocket.send_json(state)
                logger.debug(f"Pushed object clear to IDE websocket for: {workbook_id}")
            else:
                await self.broadcast("ide", state)
            logger.debug(f"Pushed object clear to IDE for: {workbook_id}")
        except Exception as e:
            logger.error(f"Error pushing object clear: {e}")


    async def _push_message_to_ide_console(self, message: str, color: Optional[str]=None, websocket: Optional[WebSocket]=None):
        """
        Push a message to the IDE console.
        
        Args:
            workbook_id: The workbook identifier
            message: The message string
            level: The log level ("info", "warning", "error", etc.)
            websocket: Optional WebSocket to send to a specific IDE connection
        """
        state = {
            "type": "log_to_console",
            "content": message,
        }
        if color:
            state["color"] = color
        
        try:
            if websocket:
                await websocket.send_json(state)
                logger.debug(f"Pushed console message to IDE websocket")
            else:
                await self.broadcast("ide", state)
            logger.debug(f"Pushed console message to IDE")
        except Exception as e:
            logger.error(f"Error pushing console message: {e}")

manager = ConnectionManager()


base_dir:Path=Path().home() / ".xpycode"
# Settings manager instance
settings_manager = SettingsManager(base_dir=base_dir)

# Package manager instance with settings integration
package_manager = PackageManager(base_dir=str(base_dir), settings_manager=settings_manager)

# Note: Package handlers will be initialized after handle_workbook_packages_install is defined

# IDE process manager instance (initialized in run_server)
ide_manager: Optional[IDEProcessManager] = None



# ------------ Module-Level Helper Functions for Message Handling

async def _try_handle_response(message: dict) -> bool:
    """
    Try to handle message as a response to pending request.
    
    Returns:
        True if message was handled as a response, False otherwise
    """
    try:
        return manager.handle_response(message)
    except Exception as e:
        logger.error(f"Error handling response: {e}", exc_info=e)
        return False


async def handle_forward_to_kernel(client_id: str, message: dict):
    """Forward message from addin to kernel without modification."""
    await manager.send_message("kernel", client_id, message)


async def handle_forward_to_addin(client_id: str, message: dict):
    """Forward message from kernel/IDE to addin."""
    workbook_id = message.get("workbook_id", client_id)
    await manager.send_message("addin", workbook_id, message)


async def handle_broadcast_to_ide(client_id: str, message: dict):
    """Broadcast message from addin/kernel to all IDEs."""
    await manager.broadcast("ide", message)


# ------------ Addin Message Handlers ------------

async def handle_execution_request(client_id: str, message: dict):
    """Forward execution request from addin to kernel."""
    await manager.send_message("kernel", client_id, message)


async def handle_spawn_kernel(client_id: str, message: dict):
    """Handle explicit request to spawn a kernel."""
    manager.spawn_kernel(client_id)


async def handle_terminate_kernel(client_id: str, message: dict):
    """Terminate a kernel for a workbook."""
    manager.terminate_kernel(client_id)


async def handle_excel_response(client_id: str, message: dict):
    """Forward excel_response from addin to kernel."""
    await manager.send_message("kernel", client_id, message)


async def handle_sys_response(client_id: str, message: dict):
    """Forward sys_response from addin to kernel (for synchronous COM-like calls)."""
    logger.debug(f"[Server] Routing sys_response from addin {client_id} to kernel")
    await manager.send_message("kernel", client_id, message)


async def handle_function_event_execution(client_id: str, message: dict):
    """
    Handle function_execution and event_execution messages from the Add-in.

    Forwards the message to the kernel with module_name and function_name separated.
    The kernel will:
    1. Retrieve the module using sys.modules[module_name]
    2. Retrieve the function using getattr(module, function_name)
    3. Deserialize all arguments using Serializer.from_wire
    4. Execute the function
    5. Serialize the result using Serializer.to_wire
    6. Return the serialized result

    Args:
        workbook_id: The workbook ID (used to route to the correct kernel)
        message: The function_execution or event_execution message containing:
            - type: "function_execution" or "event_execution"
            - module_name: Module name (NEW FORMAT)
            - function_name: Function name (NEW FORMAT)
            - args: Array of wire-format objects to pass as arguments
            - request_id: Unique request identifier (required for function_execution)
            - For event_execution: object_name, event_type, object_type (metadata)
    """
    workbook_id=client_id
    message_type = message.get("type", "")
    module_name = message.get("module_name", "")
    function_name = message.get("function_name", "")
    args = message.get("args", [])
    request_id = message.get("request_id", str(uuid.uuid4()))
    is_function_execution = message_type == "function_execution"

    async def send_error(error_msg: str):
        """Send an execution_error message back to the add-in."""
        error_message = {
            "type": "execution_error",
            "success": False,
            "error": {"type": "ValidationError", "message": error_msg},
            "request_id": request_id,
            "workbook_id": workbook_id,
            "module_name": module_name,
            "function_name": function_name,
        }
        await manager.send_message("addin", workbook_id, error_message)
        
        # For function_execution, also send function_execution_result
        if is_function_execution:
            await manager.send_message("addin", workbook_id, {
                "type": "function_execution_result",
                "request_id": request_id,
                "success": False,
                "error": {"type": "ValidationError", "message": error_msg}
            })

    if not module_name:
        error_msg = "function_execution/event_execution missing module_name"
        logger.warning(error_msg)
        await send_error(error_msg)
        return

    if not function_name:
        error_msg = "function_execution/event_execution missing function_name"
        logger.warning(error_msg)
        await send_error(error_msg)
        return

    # Validate module_name and function_name to prevent code injection
    is_valid_module, module_error = validate_python_identifier(module_name)
    if not is_valid_module:
        error_msg = f"Invalid module name '{module_name}': {module_error}"
        logger.warning(error_msg)
        await send_error(error_msg)
        return

    is_valid_function, function_error = validate_python_identifier(function_name)
    if not is_valid_function:
        error_msg = f"Invalid function name '{function_name}': {function_error}"
        logger.warning(error_msg)
        await send_error(error_msg)
        return

    await full_code_sync(workbook_id)
    
    # Create the custom_function_call message with separated module and function names
    # Note: custom_function_call is used for UDF execution (returns result)
    # event_execution is used for event handlers (no return value expected)
    custom_function_call_message = {
        "type": "custom_function_call" if is_function_execution else "event_execution",
        "module_name": module_name,
        "function_name": function_name,
        "args": args,
        "request_id": request_id,
        "workbook_id": workbook_id,
    }
    
    # For event_execution, add extra metadata
    if not is_function_execution:
        custom_function_call_message.update({
            "object_name": message.get("object_name", ""),
            "event_type": message.get("event_type", ""),
            "object_type": message.get("object_type", ""),
        })

    # Send to the kernel
    logger.debug(f"Forwarding function/event execution to kernel: {module_name}.{function_name}")
    logger.debug(f"[TIMING] Forwarded to kernel: type={custom_function_call_message['type']}, request_id={request_id}")
    
    # Track function_execution requests to send function_execution_result back
    # Note: Direct access to manager._pending_function_executions is acceptable here
    # as this function is in the same module and part of the internal implementation
    if is_function_execution:
        manager._pending_function_executions[request_id] = workbook_id
    
    await manager.send_message("kernel", workbook_id, custom_function_call_message)


async def _send_streaming_error(client_id: str, request_id: str, error_msg: str):
    """Helper to send streaming function error response."""
    await manager.send_to_addin(client_id, {
        "type": "streaming_function_result",
        "request_id": request_id,
        "error": error_msg,
        "done": True
    })


async def handle_streaming_function_execution(client_id: str, message: dict):
    """Handle streaming function execution from addin."""
    request_id = message.get("request_id")
    module_name = message.get("module_name")
    function_name = message.get("function_name")
    args = message.get("args", [])
    
    # Validate required fields
    if not request_id:
        logger.warning("streaming_function_execution missing request_id")
        return
    
    if not module_name:
        error_msg = "streaming_function_execution missing module_name"
        logger.warning(error_msg)
        await _send_streaming_error(client_id, request_id, error_msg)
        return
    
    if not function_name:
        error_msg = "streaming_function_execution missing function_name"
        logger.warning(error_msg)
        await _send_streaming_error(client_id, request_id, error_msg)
        return
    
    # Validate module_name and function_name to prevent code injection
    is_valid_module, module_error = validate_python_identifier(module_name)
    if not is_valid_module:
        error_msg = f"Invalid module name '{module_name}': {module_error}"
        logger.warning(error_msg)
        await _send_streaming_error(client_id, request_id, error_msg)
        return
    
    is_valid_function, function_error = validate_python_identifier(function_name)
    if not is_valid_function:
        error_msg = f"Invalid function name '{function_name}': {function_error}"
        logger.warning(error_msg)
        await _send_streaming_error(client_id, request_id, error_msg)
        return
    
    await full_code_sync(client_id)
    
    # Forward to kernel
    logger.debug(f"[TIMING] Forwarded to kernel: type={message.get('type')}, request_id={request_id}")
    await manager.send_message("kernel", client_id, {
        "type": "execute_streaming_function",
        "request_id": request_id,
        "module_name": module_name,
        "function_name": function_name,
        "args": args
    })


async def handle_cancel_streaming_function(client_id: str, message: dict):
    """Handle streaming function cancellation from addin."""
    request_id = message.get("request_id")
    await manager.send_message("kernel", client_id, {
        "type": "cancel_streaming_function",
        "request_id": request_id
    })


async def handle_python_function_call(client_id: str, message: dict):
    """Handle Python callable invocation from Excel."""
    callable_id = message.get("callable_id")
    args = message.get("args", [])
    request_id = message.get("requestId")  # Note: requestId from add-in sendRequest
    
    if not callable_id:
        error_msg = "python_function_call missing callable_id"
        logger.warning(error_msg)
        await manager.send_to_addin(client_id, {
            "kind": "response",
            "requestId": request_id,
            "ok": False,
            "error": {"message": error_msg}
        })
        return
    
    logger.info(f"[Server] Routing python_function_call: callable_id={callable_id}, request_id={request_id}")
    
    # Forward to kernel with proper message structure
    await manager.send_message("kernel", client_id, {
        "type": "python_function_call",
        "callable_id": callable_id,
        "args": args,
        "request_id": request_id,
        "workbook_id": client_id
    })


async def handle_workbook_structure_update(client_id: str, message: dict):
    """Handle workbook structure update from Add-in."""
    tree = message.get("tree", {})
    manager.handle_workbook_structure_update(client_id, tree)


async def handle_workbook_name_changed(client_id: str, message: dict):
    """Handle workbook name change from Add-in."""
    old_name = message.get("old_name")
    new_name = message.get("new_name")
    path = message.get("path", "")
    
    # Update the name in cache
    manager.client_names[client_id] = new_name
    logger.info(f"Workbook name changed: {old_name} -> {new_name} (workbook_id: {client_id}, path: {path})")
    
    # Broadcast to all IDE clients
    await manager.send_to_ide({
        "type": "workbook_name_changed",
        "workbook_id": client_id,
        "old_name": old_name,
        "new_name": new_name,
        "path": path
    })


async def handle_event_definitions_update(client_id: str, message: dict):
    """Handle event definitions update from Add-in."""
    definitions = message.get("definitions", {})
    manager.handle_event_definitions_update(client_id, definitions)


async def handle_event_config_response(client_id: str, message: dict):
    """Forward event config response from addin to IDE."""
    message["workbook_id"] = client_id
    await manager.send_to_ide(message)


async def handle_log_entry(client_id: str, message: dict):
    """Handle log entries from Add-in for debugging."""
    from ..logging_config import get_logger
    
    level = message.get("level", "DEBUG").upper()
    messages = message.get("messages", [])
    caller = message.get("caller", "")
    timestamp = message.get("timestamp", "")
    
    # Build the log message from the messages list
    message_parts = []
    temp_logger = get_logger("addin")  # Get logger early for error logging
    for m in messages:
        if isinstance(m, (dict, list)):
            try:
                message_parts.append(json.dumps(m))
            except (TypeError, ValueError) as e:
                # Log the serialization error for debugging
                temp_logger.debug(f"Failed to serialize object: {e}")
                message_parts.append(str(m))
        else:
            message_parts.append(str(m))
    
    log_message = " ".join(message_parts)
    
    # Extract file name from caller for logger name
    # Caller format: "at functionName (https://localhost:3000/path/file.js:123:45)"
    # or: "at https://localhost:3000/path/file.js:123:45"
    logger_name = "addin"
    if caller:
        import re
        # Try to extract file name from URL in caller string
        match = re.search(r'/([^/]+\.js):\d+:\d+', caller)
        if match:
            logger_name = f"addin.{match.group(1).replace('.js', '')}"
    
    # Get logger and log at appropriate level
    addin_logger = get_logger(logger_name)
    
    # Too verbose logging. Kept commented for reference.
    #full_message = f"[{client_id}] {log_message}"
    #if caller:
    #    full_message += f" (from: {caller})"

    full_message = log_message

    
    if level == "ERROR":
        addin_logger.error(full_message)
    elif level == "WARNING":
        addin_logger.warning(full_message)
    elif level == "INFO":
        addin_logger.info(full_message)
    else:  # DEBUG or unknown
        addin_logger.debug(full_message)




def get_functions_from_addin_message(message: dict) -> List[dict]:
    """Extract and convert functions from addin message format to server format."""

    functions = message.get("functions", [])
    logger.info(f"[Server] Client syncing {len(functions)} functions")
    
    # Convert from addin format to server format
    server_functions = []
    for func in functions:
        if isinstance(func, dict):
            module_name = func.get("module") if "module" in func else func.get("module_name", "")
            function_name = func.get("function") if "function" in func else func.get("function_name", "")
            excel_name = func.get("excel_name", "")
            dimension = func.get("dimension", "Scalar")
            streaming = func.get("streaming", False)
            
            if module_name and function_name and excel_name:
                server_functions.append({
                    "module_name": module_name,
                    "function_name": function_name,
                    "excel_name": excel_name,
                    "dimension": dimension,
                    "streaming": streaming
                })
    return server_functions

async def handle_client_sync_functions(client_id: str, message: dict):
    """Handle function synchronization from Add-in on WebSocket connection."""
    server_functions= get_functions_from_addin_message(message)
    # Update server-side published functions registry
    manager.published_functions[client_id] = server_functions
    
    # Push state to all IDEs for synchronization
    await manager._push_published_functions_state(client_id, server_functions)
    logger.debug(f"[Server] Synced functions to IDE for workbook: {client_id}")


async def handle_client_restored_functions(client_id: str, message: dict):
    """Handle restored functions notification from Add-in."""
    functions = message.get("functions", [])
    logger.info(f"[Server] Client restored {len(functions)} functions for workbook: {client_id}")
    
    # Convert from addin format to server format
    server_functions = []
    for func in functions:
        if isinstance(func, dict):
            module_name = func.get("module") if "module" in func else func.get("module_name", "")
            function_name = func.get("function") if "function" in func else func.get("function_name", "")
            excel_name = func.get("excel_name", "")
            dimension = func.get("dimension", "Scalar")
            streaming = func.get("streaming", False)
            
            if module_name and function_name and excel_name:
                server_functions.append({
                    "module_name": module_name,
                    "function_name": function_name,
                    "excel_name": excel_name,
                    "dimension": dimension,
                    "streaming": streaming
                })
    
    # Update server-side published functions registry
    manager.published_functions[client_id] = server_functions
    
    # Push state to all IDEs for synchronization
    await manager._push_published_functions_state(client_id, server_functions)
    logger.debug(f"[Server] Synced restored functions to IDE for workbook: {client_id}")


def get_pacakages_and_python_paths_from_addin_message(message: dict) -> Tuple[list,list]:
    """Extract packages and python_paths from addin message format."""
    packages = message.get("packages", [])
    python_paths = message.get("python_paths", [])

    for pkg in packages:
        pkg["status"] = "pending"

    return packages, python_paths



async def handle_client_sync_packages(client_id: str, message: dict):
    """Handle package synchronization from Add-in on WebSocket connection."""
    return
    packages = message.get("packages", [])
    python_paths = message.get("python_paths", [])
    logger.info(f"[Server] Client syncing {len(packages)} packages and {len(python_paths)} python paths for workbook: {client_id}")
    
    # Normalize python_paths to strings (handles old dict format)
    python_paths = normalize_python_paths(python_paths)
    logger.debug(f"[Server] Normalized python_paths: {python_paths}")
    
    # Set all packages status to "pending" immediately
    for pkg in packages:
        if pkg.get("status") != "installed":
            pkg["status"] = "pending"
    
    # Update server-side package registry
    manager.workbook_packages[client_id] = packages
    
    old_python_paths = manager.workbook_python_paths.get(client_id, [])
    manager.workbook_python_paths[client_id] = python_paths
    if python_paths or old_python_paths:
        await manager.send_message("kernel", client_id, {
            "type": "set_python_paths",
            "old_paths": old_python_paths,
            "new_paths": python_paths
        })
    
    # Push state to all IDEs for synchronization
    await manager.send_to_ide({
        "type": "workbook_packages_update",
        "workbook_id": client_id,
        "packages": packages,
        "python_paths": python_paths,
        "package_errors": manager.package_errors.get(client_id, {})
    })
    logger.debug(f"[Server] Synced packages and python paths to IDE for workbook: {client_id}")
    
    # Auto-install if there are packages
    if packages:
        logger.info(f"[Server] Auto-installing {len(packages)} packages for workbook: {client_id}")
        task = asyncio.create_task(handle_workbook_packages_install(client_id))
        task.add_done_callback(
            lambda t: logger.error(f"Auto-install task failed: {t.exception()}", exc_info=t.exception())
            if t.exception() else None
        )


# ------------ Kernel Message Handlers ------------

async def handle_kernel_batch(client_id: str, message: dict):
    """Handle batch messages from kernel."""
    messages = message.get("messages", [])
    # Process each message in the batch
    await asyncio.gather(*[
        handle_message('kernel',client_id, msg)
        for msg in messages
    ], return_exceptions=True)


kernel_handles={
        }

async def handle_kernel_to_addin(client_id: str, message: dict):
    """
    Handle messages from kernel to addin
    """
    await manager.send_to_addin(client_id, message)

async def handle_kernel_to_ide(client_id: str, message: dict):
    """
    Handle messages from kernel to IDE.
    """
    workbook_id = message.get("workbook_id") or client_id
    message["workbook_id"] = workbook_id  # Ensure workbook_id is in the message
    logger.info(f"[BusinessLayer] Forwarded {message.get('type')} to IDE for workbook {workbook_id}")
    await  manager.broadcast("ide", message)

async def handle_kernel_transfert(client_id: str, message: dict):
    """
    Handle transfert message from kernel to IDE and Addin.
    """
    await manager.send_message("addin", client_id, message)
    await manager.broadcast("ide", message)

async def handle_kernel_execution_result(client_id: str, message: dict):
    request_id = message.get("request_id", "N/A")
    is_function_execution = request_id and request_id in manager._pending_function_executions
    if not is_function_execution:
        await handle_kernel_transfert(client_id, message)
    else:
        workbook_id = manager._pending_function_executions.pop(request_id)
        function_result = {
            "type": "function_execution_result",
            "request_id": request_id,
            "status": "success",
            "result": message.get("result"),
            "logs": message.get("logs", "")
        }
        # Use result batcher instead of direct send
        await manager._result_batcher.add_result(workbook_id, function_result)
        logger.debug(f"Queued function_execution_result for request_id: {request_id}")

async def handle_kernel_execution_error(client_id: str, message: dict):
    request_id = message.get("request_id", "N/A")
    is_function_execution = request_id and request_id in manager._pending_function_executions
    if not is_function_execution:
        await handle_kernel_transfert(client_id, message)
    else:
        workbook_id = manager._pending_function_executions.pop(request_id)
        function_result = {
            "type": "function_execution_result",
            "request_id": request_id,
            "status": "error",
            "error": message.get("error", {"message": "Unknown error"}),
            "logs": message.get("logs", "")
        }
        # Use result batcher instead of direct send
        await manager._result_batcher.add_result(workbook_id, function_result)
        logger.debug(f"Queued function_execution_result (error) for request_id: {request_id}")


async def handle_kernel_request_module_sync(client_id: str, message: dict):
   # Handle module sync request from kernel
    # This happens when a streaming function is called but the module is not in cache
    module_name = message.get("module_name")
    workbook_id = message.get("workbook_id", client_id)
        
    logger.info(f"[Server] Kernel requesting module sync: {module_name} for workbook: {workbook_id}")
        
    # Get module from cache or request from addin
    module_code = manager.get_module(workbook_id, module_name)
        
    if module_code:
        # Send module to kernel
        logger.info(f"[Server] Sending cached module {module_name} to kernel")
        await manager.send_message("kernel", workbook_id, {
            "type": "update_module",
            "module_name": module_name,
            "code": module_code
        })
    else:
        # Request from addin if not in server cache
        logger.info(f"[Server] Module {module_name} not in cache, requesting from addin")
        manager.send_to_addin(workbook_id,{
                "type": "get_module_request",
                "module_name": module_name,
                "for_streaming": True
            })

# ------------ IDE Message Handlers ------------

async def handle_ide_execution_request(client_id: str, message: dict):
    """Forward execution request from IDE to kernel."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        await manager.send_message("kernel", target_workbook, message)
    else:
        logger.warning("Received execution_request from IDE without workbook_id")


async def handle_run_module(client_id: str, message: dict):
    """Route run_module from IDE to kernel."""
    target_workbook = message.get("workbook_id")
    module_name = message.get("module_name")
    function_name = message.get("function_name")
    
    # Validate required fields
    if not target_workbook:
        logger.warning("Received run_module from IDE without workbook_id")
        return
    if not module_name:
        logger.warning("Received run_module from IDE without module_name")
        return
    if not function_name:
        logger.warning("Received run_module from IDE without function_name")
        return
    
    # Validate module_name and function_name to prevent code injection
    is_valid_module, module_error = validate_python_identifier(module_name)
    if not is_valid_module:
        logger.warning(f"Invalid module name '{module_name}': {module_error}")
        return
    
    is_valid_function, function_error = validate_python_identifier(function_name)
    if not is_valid_function:
        logger.warning(f"Invalid function name '{function_name}': {function_error}")
        return
    
    # Forward to kernel
    logger.info(f"[BusinessLayer] Routing run_module to kernel: {module_name}.{function_name} (workbook_id={target_workbook})")
    await manager.send_message("kernel", target_workbook, message)


async def handle_update_module(client_id: str, message: dict):
    """Forward update_module to kernel and save to workbook."""
    target_workbook = message.get("workbook_id")
    module_name = message.get("module_name")
    code = message.get("code", "")
    if target_workbook and module_name:
        # Save module to workbook (source of truth) and cache
        asyncio.create_task(
            manager.save_module_to_addin(target_workbook, module_name, code)
        )
        # Also update in-memory cache immediately for responsiveness
        manager.save_module(target_workbook, module_name, code)
        # Forward to kernel
        await manager.send_message("kernel", target_workbook, message)
    else:
        logger.warning("Received update_module from IDE without workbook_id or module_name")


async def handle_save_module(client_id: str, message: dict):
    """Save module to workbook (source of truth)."""
    target_workbook = message.get("workbook_id")
    module_name = message.get("module_name")
    code = message.get("code", "")
    if target_workbook and module_name:
        # Save to workbook asynchronously
        success = await manager.save_module_to_addin(target_workbook, module_name, code)
        # Also update in-memory cache
        manager.save_module(target_workbook, module_name, code)
        # Send confirmation back to IDE
        await manager.send_to_ide({
            "type": "module_saved",
            "workbook_id": target_workbook,
            "module_name": module_name,
            "success": success,
        })
    else:
        logger.warning("Received save_module from IDE without workbook_id or module_name")


async def handle_delete_module(client_id: str, message: dict):
    """Delete module from workbook (source of truth)."""
    target_workbook = message.get("workbook_id")
    module_name = message.get("module_name")
    if target_workbook and module_name:
        # Delete from workbook
        deleted = await manager.delete_module_from_addin(target_workbook, module_name)
        # Also update in-memory cache
        manager.delete_module(target_workbook, module_name)
        
        # Forward delete_module to kernel to remove from sys.modules
        await manager.send_message("kernel", target_workbook, {
            "type": "delete_module",
            "workbook_id": target_workbook,
            "module_name": module_name,
        })
        
        # Also clean up synced hashes
        if target_workbook in manager._synced_hashes:
            manager._synced_hashes[target_workbook].pop(module_name, None)
        
        # Send confirmation back to IDE
        await manager.send_to_ide({
            "type": "module_deleted",
            "workbook_id": target_workbook,
            "module_name": module_name,
            "success": deleted,
        })
    else:
        logger.warning("Received delete_module from IDE without workbook_id or module_name")


async def handle_debug_command(client_id: str, message: dict):
    """Forward debug commands to kernel."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        await manager.send_message("kernel", target_workbook, message)
    else:
        logger.warning(f"Received {message.get('type')} from IDE without workbook_id")


async def handle_list_modules(client_id: str, message: dict):
    """List all modules for a workbook."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        modules = manager.list_modules(target_workbook)
        # Send module list back to IDE
        await manager.send_to_ide({
            "type": "module_list",
            "workbook_id": target_workbook,
            "modules": list(modules.keys()),
        })
    else:
        logger.warning("Received list_modules from IDE without workbook_id")


async def handle_get_module(client_id: str, message: dict):
    """Get a specific module's code."""
    target_workbook = message.get("workbook_id")
    module_name = message.get("module_name")
    if target_workbook and module_name:
        # First check cache
        code = manager.get_module(target_workbook, module_name)
        # If not in cache, load from workbook
        if code is None:
            code = await manager.load_module_from_addin(target_workbook, module_name)
        # Send module content back to IDE
        await manager.send_to_ide({
            "type": "module_content",
            "workbook_id": target_workbook,
            "module_name": module_name,
            "code": code,
        })
    else:
        logger.warning("Received get_module from IDE without workbook_id or module_name")


async def handle_get_all_modules(client_id: str, message: dict):
    """Get all modules with their code for a workbook."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        modules = manager.list_modules(target_workbook)
        # Send all modules back to IDE
        await manager.send_to_ide({
            "type": "all_modules",
            "workbook_id": target_workbook,
            "modules": modules,
        })
    else:
        logger.warning("Received get_all_modules from IDE without workbook_id")


async def handle_lsp_request(client_id: str, message: dict):
    """Forward LSP request to kernel."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        await manager.send_message("kernel", target_workbook, message)
    else:
        logger.warning(f"Received {message.get('type')} from IDE without workbook_id")


async def handle_set_hover_mode(client_id: str, message: dict):
    """Forward hover mode change to all kernels."""
    mode = message.get("mode", "compact")
    logger.debug(f"[Server] Broadcasting set_hover_mode to all kernels: {mode}")
    # Broadcast to all active kernels
    for workbook_id in list(manager.active_connections['kernel'].keys()):
        await manager.send_message("kernel", workbook_id, {
            "type": "set_hover_mode",
            "mode": mode
        })


async def handle_get_object_registry(client_id: str, message: dict):
    """Forward get_object_registry to kernel."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        logger.debug(f"[Server] Forwarding get_object_registry to kernel {target_workbook}")
        await manager.send_message("kernel", target_workbook, message)
    else:
        logger.warning("Received get_object_registry from IDE without workbook_id")


async def handle_event_request_to_addin(client_id: str, message: dict):
    """Forward event-related requests from IDE to addin."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        await manager.send_to_addin(target_workbook, message)
    else:
        logger.warning(f"Received {message.get('type')} from IDE without workbook_id")


async def handle_refresh_event_manager_state(client_id: str, message: dict):
    """Handle refresh_event_manager_state request from IDE."""
    target_workbook = message.get("workbook_id")
    if target_workbook:
        # Check if we have cached data
        if (target_workbook in manager.workbook_tree and 
            target_workbook in manager.event_definitions):
            # Push the current cached state immediately
            await manager._push_event_manager_state(target_workbook)
            logger.debug(f"Pushed cached event manager state for: {target_workbook}")
        else:
            # No cache, trigger a scan request to the Add-in
            logger.debug(f"No cached data, triggering scan for: {target_workbook}")
            await manager.send_to_addin(target_workbook, {
                "type": "scan_objects_request",
                "workbook_id": target_workbook
            })
    else:
        logger.warning("Received refresh_event_manager_state from IDE without workbook_id")


async def handle_register_handler(client_id: str, message: dict):
    """Handle register_handler request from IDE."""
    target_workbook = message.get("workbook_id")
    object_type = message.get("object_type")
    object_id = message.get("object_id")
    event_name = message.get("event_name")
    module_name = message.get("module_name")
    function_name = message.get("function_name")
    
    if all([target_workbook, object_type, object_id, event_name, module_name, function_name]):
        success = await manager.handle_register_handler(
            target_workbook, object_type, object_id, event_name, module_name, function_name
        )
        # Send response back to IDE
        await manager.send_to_ide({
            "type": "register_handler_result",
            "workbook_id": target_workbook,
            "object_id": object_id,
            "event_name": event_name,
            "success": success
        })
    else:
        logger.warning("Received register_handler from IDE with missing parameters")


async def handle_unregister_handler(client_id: str, message: dict):
    """Handle unregister_handler request from IDE."""
    target_workbook = message.get("workbook_id")
    object_id = message.get("object_id")
    event_name = message.get("event_name")
    
    if all([target_workbook, object_id, event_name]):
        success = await manager.handle_unregister_handler(
            target_workbook, object_id, event_name
        )
        # Send response back to IDE
        await manager.send_to_ide({
            "type": "unregister_handler_result",
            "workbook_id": target_workbook,
            "object_id": object_id,
            "event_name": event_name,
            "success": success
        })
    else:
        logger.warning("Received unregister_handler from IDE with missing parameters")


async def handle_rename_module_in_events(client_id: str, message: dict):
    """
    Handle rename_module_in_events request from IDE.
    
    Unregisters event handlers using the old module name and re-registers them
    with the new module name.
    """
    workbook_id = message.get("workbook_id")
    old_module_name = message.get("old_module_name")
    new_module_name = message.get("new_module_name")
    events = message.get("events", [])
    
    if not all([workbook_id, old_module_name, new_module_name]):
        logger.warning("Received rename_module_in_events from IDE with missing parameters")
        return
    
    if not events:
        logger.debug(f"[BusinessLayer] No events to update for module rename: {old_module_name} -> {new_module_name}")
        return
    
    logger.info(f"[BusinessLayer] Renaming module in {len(events)} event handler(s): {old_module_name} -> {new_module_name}")
    
    # Process each event: unregister old, register new
    for event_info in events:
        object_type = event_info.get("object_type")
        object_id = event_info.get("object_id")
        event_name = event_info.get("event_name")
        function_name = event_info.get("function_name")
        
        if not all([object_type, object_id, event_name, function_name]):
            logger.warning(f"[BusinessLayer] Skipping event with missing parameters: {event_info}")
            continue
        
        # Unregister old handler
        await manager.handle_unregister_handler(
            workbook_id, object_id, event_name
        )
        
        # Register new handler with new module name
        await manager.handle_register_handler(
            workbook_id, object_type, object_id, event_name, new_module_name, function_name
        )
    
    logger.info(f"[BusinessLayer] Successfully updated event handlers for module rename")


async def handle_update_published_functions(client_id: str, message: dict):
    """Handle update_published_functions request from IDE."""
    target_workbook = message.get("workbook_id")
    functions = message.get("functions", [])
    
    if not target_workbook:
        logger.warning("Received update_published_functions from IDE without workbook_id")
    elif not isinstance(functions, list):
        logger.warning(f"Received update_published_functions with invalid functions type: {type(functions)}")
    else:
        # Validate function structure
        valid_functions = []
        for func in functions:
            if manager._validate_function_entry(func):
                valid_functions.append(func)
            else:
                logger.warning(f"Skipping invalid function entry: {func}")
        
        await manager.handle_update_published_functions(target_workbook, valid_functions)


async def handle_get_function_at_position(client_id: str, message: dict):
    """Forward inspector request to inspector service."""
    inspector_ws = manager.get_connection("inspector", "main")
    if inspector_ws:
        await inspector_ws.send_json(message)
        logger.debug(f"Forwarded get_function_at_position to inspector")
    else:
        logger.warning("Inspector not connected, cannot process get_function_at_position")
        # Send error response back to IDE
        await manager.send_to_ide({
            "type": "function_at_position_result",
            "request_id": message.get("request_id"),
            "function_name": None,
            "error": "Inspector service not available"
        })


# ------------ Inspector Message Handlers ------------

async def handle_inspector_result(client_id: str, message: dict):
    """Forward inspector results to IDE."""
    await manager.send_to_ide(message)
    logger.debug(f"Forwarded {message.get('type')} to IDE")


# ------------ No-op Handler for Response Messages ------------

async def handle_response_message(client_id: str, message: dict):
    """No-op handler for response messages handled by _try_handle_response."""
    pass


# ------------ Settings Message Handlers ------------

async def handle_get_settings(client_id: str, message: dict):
    """Handle get_settings request."""
    path = message.get("path", "")
    value = settings_manager.get(path)
    await manager.send_to_ide({
        "type": "settings_response",
        "request_id": message.get("request_id"),
        "path": path,
        "value": value
    })


async def handle_set_setting(client_id: str, message: dict):
    """Handle set_setting request."""
    path = message.get("path")
    value = message.get("value")
    settings_manager.set(path, value)
    await manager.send_to_ide({
        "type": "setting_saved",
        "request_id": message.get("request_id"),
        "path": path,
        "success": True
    })


async def handle_get_all_settings(client_id: str, message: dict):
    """Handle get_all_settings request."""
    await manager.send_to_ide({
        "type": "all_settings_response",
        "request_id": message.get("request_id"),
        "initial": message.get("initial",False),
        "settings": settings_manager.get_all()
    })


async def handle_show_ide(client_id: str, message: dict):
    """Handle show_ide request from add-in."""
    global ide_manager
    
    if ide_manager is None:
        logger.error("IDE manager not initialized")
        return
    
    logger.info(f"Received show_ide request from addin: {client_id}")
    
    # Ensure IDE is running
    if ide_manager.ensure_running():
        # Send show_ide message to IDE through WebSocket
        await manager.send_to_ide({
            "type": "show_ide"
        })
        logger.info("Sent show_ide message to IDE")
    else:
        logger.error("Failed to start IDE")


async def handle_kill_ide(client_id: str, message: dict):
    """
    Handle kill_ide message from addin.
    Kills the IDE process and restarts it.
    """
    logger.info(f"[BusinessLayer] Received kill_ide from {client_id}")
    
    if ide_manager:
        success = ide_manager.kill_and_restart()
        if success:
            logger.info("[BusinessLayer] IDE killed and restarted successfully")
            # Send show_ide to the new IDE once it connects
            # The IDE will show itself when it starts
        else:
            logger.error("[BusinessLayer] Failed to restart IDE")
    else:
        logger.warning("[BusinessLayer] IDE manager not initialized")


async def handle_message_ide(client_id: str, message: dict):
    """
    Handle message_ide message from addin.
    Forwards the message to the IDE.
    """
    logger.info(f"[BusinessLayer] Received message_ide from {client_id}")
    
    msg_content = message.get("message", "")
    
    # Forward to IDE
    await manager.send_to_ide({
        "type": "message_ide",
        "message": msg_content,
        "from_client": client_id
    })
    logger.debug(f"[BusinessLayer] Forwarded message_ide to IDE: {msg_content[:50]}...")


async def handle_kill_kernel(client_id: str, message: dict):
    """
    Handle kill_kernel message from addin or ide.
    Kills the kernel process and restarts it.
    """
    # Get workbook_id from message, fallback to client_id if not provided or empty
    workbook_id = message.get("workbook_id")
    if not workbook_id:
        workbook_id = client_id
    
    logger.info(f"[BusinessLayer] Received kill_kernel request for workbook: {workbook_id}")
    
    # Kill and restart the kernel
    success = manager.kill_and_restart_kernel(workbook_id)
    
    # Send response to both addin and IDE
    response = {
        "type": "kill_kernel_response",
        "workbook_id": workbook_id,
        "success": success
    }
    
    await manager.send_to_addin(workbook_id, response)
    await manager.broadcast("ide", response)
    
    if success:
        logger.info(f"[BusinessLayer] Kernel killed and restarted successfully for: {workbook_id}")
    else:
        logger.error(f"[BusinessLayer] Failed to restart kernel for: {workbook_id}")

async def handle_restart_addin(client_id: str, message: dict):
    """
    Handle restart_addin message from IDE.
    Forwards the message to the add-in to trigger a restart.
    """
    # Get workbook_id from message, fallback to client_id if not provided or empty
    workbook_id = message.get("workbook_id")
    if not workbook_id:
        workbook_id = client_id
    
    logger.info(f"[BusinessLayer] Received restart_addin request for workbook: {workbook_id}")
    
    # Forward restart_addin message to the add-in
    await manager.send_to_addin(workbook_id, {
        "type": "restart_addin"
    })
    
    logger.info(f"[BusinessLayer] Sent restart_addin to add-in: {workbook_id}")


# ------------ Message Dispatch Dictionary ------------

MESSAGE_HANDLERS: Dict[str, Dict[str, Callable]] = {
    "addin": {
        "execution_request": handle_execution_request,
        "spawn_kernel": handle_spawn_kernel,
        "terminate_kernel": handle_terminate_kernel,
        "excel_response": handle_excel_response,
        "sys_response": handle_sys_response,
        "function_execution": handle_function_event_execution,
        "event_execution": handle_function_event_execution,
        "streaming_function_execution": handle_streaming_function_execution,
        "cancel_streaming_function": handle_cancel_streaming_function,
        "python_function_call": handle_python_function_call,
        # IDE control
        "show_ide": handle_show_ide,
        "kill_ide": handle_kill_ide,
        "message_ide": handle_message_ide,
        "kill_kernel": handle_kill_kernel,
        # Response messages handled by _try_handle_response
        "get_modules_response": handle_response_message,
        "get_functions_response": handle_response_message,
        "get_packages_response": handle_response_message,
        "save_module_response": handle_response_message,
        "load_module_response": handle_response_message,
        "delete_module_response": handle_response_message,
        "register_handler_response": handle_response_message,
        "unregister_handler_response": handle_response_message,
        "get_event_config_response": handle_response_message,
        # State updates
        "workbook_structure_update": handle_workbook_structure_update,
        "workbook_name_changed": handle_workbook_name_changed,
        "event_definitions_update": handle_event_definitions_update,

        "save_event_config_response": handle_event_config_response,
        "validate_handler_response": handle_event_config_response,
        # Logging
        "log_entry": handle_log_entry,
        # Function synchronization
        "client_sync_functions": handle_client_sync_functions,
        "client_restored_functions": handle_client_restored_functions,
        # Package synchronization
        "client_sync_packages": handle_client_sync_packages,
    },
    "kernel": {
        "batch": handle_kernel_batch,
        "stdout":handle_kernel_transfert,
        "stderr":handle_kernel_transfert,
        "result_output":handle_kernel_transfert,
        "event_execution_result":handle_kernel_transfert,
        "streaming_function_result":handle_kernel_transfert,
        "execution_result":handle_kernel_execution_result,
        "execution_error":handle_kernel_execution_error,
        "sys_request":handle_kernel_to_addin,
        "completion_response":handle_kernel_to_ide,
        "signature_help_response":handle_kernel_to_ide,
        "hover_response":handle_kernel_to_ide,
        "diagnostic_response":handle_kernel_to_ide,
        "object_registry_update":handle_kernel_to_ide,
        "object_registry_response":handle_kernel_to_ide,
        "debug_terminated":handle_kernel_to_ide,
        "debug_paused":handle_kernel_to_ide,
        "debug_exception":handle_kernel_to_ide,
        "debug_evaluate_result":handle_kernel_to_ide,
        "request_module_sync":handle_kernel_request_module_sync,
        "show_message_box":handle_kernel_to_addin,
        "set_enable_events":handle_kernel_to_addin,
    },
    "ide": {
        "execution_request": handle_ide_execution_request,
        "run_module": handle_run_module,
        "update_module": handle_update_module,
        "save_module": handle_save_module,
        "delete_module": handle_delete_module,
        # Debug commands
        "debug_continue": handle_debug_command,
        "debug_step_over": handle_debug_command,
        "debug_step_into": handle_debug_command,
        "debug_step_out": handle_debug_command,
        "debug_stop": handle_debug_command,
        "debug_evaluate": handle_debug_command,
        "debug_update_breakpoints": handle_debug_command,
        # Module management
        "list_modules": handle_list_modules,
        "get_module": handle_get_module,
        "get_all_modules": handle_get_all_modules,
        # Kernel lifecycle
        "spawn_kernel": handle_spawn_kernel,
        "terminate_kernel": handle_terminate_kernel,
        "kill_kernel": handle_kill_kernel,
        "restart_addin": handle_restart_addin,
        # LSP requests
        "completion_request": handle_lsp_request,
        "signature_help_request": handle_lsp_request,
        "diagnostic_request": handle_lsp_request,
        "hover_request": handle_lsp_request,
        "set_hover_mode": handle_set_hover_mode,
        "get_object_registry": handle_get_object_registry,
        # Package management
        "package_install_request": handle_package_install_request,
        "get_package_versions_request": handle_get_package_versions_request,
        "get_package_extras_request": handle_get_package_extras_request,
        "get_package_info_request": handle_get_package_info_request,
        "add_workbook_package": handle_add_workbook_package,
        "remove_workbook_package": handle_remove_workbook_package,
        "update_workbook_package": handle_update_workbook_package,
        "restore_workbook_packages": handle_restore_workbook_packages,
        "update_package_status": handle_update_package_status,
        "reorder_workbook_packages": handle_reorder_workbook_packages,
        "install_workbook_packages": handle_install_workbook_packages,
        "get_workbook_packages": handle_get_workbook_packages,
        "get_resolved_deps": handle_get_resolved_deps,
        "update_python_paths": handle_update_python_paths,
        # Event management
        "scan_objects_request": handle_event_request_to_addin,
        "get_event_config_request": handle_event_request_to_addin,
        "save_event_config_request": handle_event_request_to_addin,
        "refresh_event_manager_state": handle_refresh_event_manager_state,
        "register_handler": handle_register_handler,
        "unregister_handler": handle_unregister_handler,
        "rename_module_in_events": handle_rename_module_in_events,
        # Function publishing
        "update_published_functions": handle_update_published_functions,
        # Inspector
        "get_function_at_position": handle_get_function_at_position,
        # Settings
        "get_settings": handle_get_settings,
        "set_setting": handle_set_setting,
        "get_all_settings": handle_get_all_settings,
    },
    "inspector": {
        "function_at_position_result": handle_inspector_result,
        "list_functions_result": handle_inspector_result,
        "validate_syntax_result": handle_inspector_result,
    }
}


async def startup_event():
    """Launch Python Inspector on server startup."""
    logger.info("Starting Business Layer server...")
    
    # Launch Python Inspector
    process = launch_inspector(_port)
    if process:
        # Wait a bit for inspector to connect
        await asyncio.sleep(1)
        logger.info("Python Inspector launched successfully")
    else:
        logger.warning("Failed to launch Python Inspector - some features may not work")


async def shutdown_event():
    """Cleanup on server shutdown."""
    logger.info("Shutting down Business Layer server...")
    terminate_inspector()




async def send_workbook_list_to_ide(websocket: Optional[WebSocket]=None):
    """Send the list of workbooks to the Add-in."""
    addin_connections = manager.active_connections.get("addin", {})
    workbook_list = [
        {
            "id": wid,
            "name": manager.client_names.get(wid, "Untitled"),
            "modules": manager.workbook_modules.get(wid, {}),
        }
        for wid in addin_connections.keys()
    ]
    if websocket:
        await websocket.send_json(
            {"type": "workbook_list", "workbooks": workbook_list}
        )
    else:
        await manager.broadcast("ide",
            {"type": "workbook_list", "workbooks": workbook_list}
        )

async def send_workbook_info_to_ide(workbook_id: str, websocket: Optional[WebSocket]=None):
    """Send workbook info to the Add-in."""    
    await manager._push_event_manager_state(workbook_id,websocket)

    await manager._push_published_functions_state(workbook_id, websocket=websocket)

    await manager._push_packages_and_python_paths(workbook_id, websocket=websocket)

    await manager._push_modules(workbook_id, websocket=websocket)



async def send_modules_to_kernel(workbook_id:str):
    modules = manager.workbook_modules.get(workbook_id, {})
    for module_name, code in modules.items():
        await manager.send_message(
            "kernel",
            workbook_id,
            {
                "type": "update_module",
                "workbook_id": workbook_id,
                "module_name": module_name,
                "code": code,
            },
        )
    logger.info(f"Synced {len(modules)} module(s) to kernel for workbook: {workbook_id}")

async def send_python_paths_to_kernel(workbook_id:str):
    python_paths = manager.workbook_python_paths.get(workbook_id, [])
    if python_paths:
        await manager.send_message("kernel", workbook_id, {
            "type": "set_python_paths",
            "old_paths": [],
            "new_paths": python_paths
        })
        logger.info(f"Sent {len(python_paths)} python paths to kernel for workbook {workbook_id}")


def _events_from_addin_to_ide(config:Dict[str,Dict]):
    rep={}
    for object_key,events in config.items():
        object_type=events['ObjectType']
        for event_name,event_info in events['events'].items():
            event_value=dict(event_info)
            event_value['object_type']=object_type
            rep[(object_key,event_name)]=event_value
    return rep

def _events_from_ide_to_addin(events:Dict[Tuple[str,str],dict]):
    rep={}
    for (object_key,event_name),event_info in events.items():
        if object_key not in rep:
            rep[object_key]={
                'ObjectType': event_info['object_type'],
                'events':{}
            }
        rep[object_key]['events'][event_name]=dict(event_info)
    return rep


#### ------------ Connection Handlers ------------

### All synchronization at connection time happens here ###

async def on_addin_coonection(
    websocket: WebSocket, client_type: str, client_id: str
):
    """Handle special tasks on Add-in connection."""
    await asyncio.sleep(0.5)
    modules = await manager.request_modules_from_addin(client_id)
    manager.workbook_modules[client_id] = modules

    functions_response=await manager.request_functions_from_addin(client_id)   
    server_functions= get_functions_from_addin_message({'functions':functions_response})
    manager.published_functions[client_id] = server_functions

    packages_and_python_paths_response= await manager.request_packages_from_addin(client_id)
    packages,python_paths  = get_pacakages_and_python_paths_from_addin_message(packages_and_python_paths_response)
    manager.workbook_packages[client_id] = packages
    manager.workbook_installed_packages[client_id]=packages
    manager.workbook_python_paths[client_id] = normalize_python_paths(python_paths)
    manager.package_errors[client_id] = {}

    all_events=await manager.request_events_info_from_addin(client_id)
    manager.event_definitions[client_id] = all_events.get('events_definition',{})
    manager.workbook_tree[client_id] = all_events.get('events_tree',{})
    manager.registered_handlers[client_id] = _events_from_addin_to_ide(all_events.get('events_registered',{}))


    # Check if kernel already exists for this workbook
    kernel_ws = manager.get_connection("kernel", client_id)
    if not kernel_ws:
        # Spawn kernel process - it will connect back via WebSocket
        process = manager.spawn_kernel(client_id)
        if process:
            # Give the kernel time to start and connect
            await asyncio.sleep(0.5)
        else:
            logger.warning(f"Failed to spawn kernel for {client_id}")

    await send_workbook_list_to_ide()
    await send_workbook_info_to_ide(client_id)
    
    

async def on_ide_connection(
    websocket: WebSocket, client_type: str, client_id: str
    ):
    """Handle special tasks on IDE connection."""
    await asyncio.sleep(0.5)
    
    await send_workbook_list_to_ide(websocket)
    addin_connections = manager.active_connections.get("addin", {})
    for wid in addin_connections.keys():
        await send_workbook_info_to_ide(wid)

        
async def on_kernel_connection(
    websocket: WebSocket, client_type: str, client_id: str
    ):
    """Handle special tasks on Kernel connection."""
    await asyncio.sleep(0.5)
    addin_connection= manager.active_connections.get("addin", {}).get(client_id)
    if addin_connection:
        # Send existing modules to kernel
        await send_modules_to_kernel(client_id) 
        # Send python paths to kernel
        await send_python_paths_to_kernel(client_id)

    await handle_workbook_packages_install(client_id)

    await manager._push_custom_functions_to_addin(client_id)
    await manager._push_events_config_to_addin(client_id,save=False)
    await manager._push_object_clear(client_id)
    await manager._push_message_to_ide_console(f'Kernell connected for workbook {manager.client_names.get(client_id,client_id)}')

#### ------------ WebSocket Endpoint ------------

async def websocket_endpoint(
    websocket: WebSocket, client_type: str, client_id: str
):
    """
    WebSocket endpoint for client connections.

    client_type: 'addin', 'ide', 'kernel', or 'inspector'
    client_id: Unique identifier for the client (e.g., workbook_id)
    Query parameter 'name': Optional display name for the client (default: 'Untitled')
    """
    if client_type not in ["addin", "ide", "kernel", "inspector"]:
        await websocket.close(code=4001, reason="Invalid client type")
        return

    # Validate client_id
    is_valid, error = validate_client_id(client_id)
    if not is_valid:
        await websocket.close(code=4002, reason=f"Invalid client ID: {error}")
        return


    # Extract name from query parameters
    name = websocket.query_params.get("name", "")

    await manager.connect(client_type, client_id, websocket, name)
    logger.info(f"Client connected: {client_type}/{client_id} (name: {name})")
    
    pending_tasks = set()


    first_connection_status=False

    todo={
        "addin": on_addin_coonection,
        "ide": on_ide_connection,
        "kernel": on_kernel_connection,
        }
    if client_type in todo:
        task = asyncio.create_task(todo[client_type](websocket, client_type, client_id))
        pending_tasks.add(task)
        task.add_done_callback(pending_tasks.discard)


    try:
        try:
            await websocket.send_json({'type':'ping'})
        except WebSocketDisconnect as wsd:
            raise wsd
        first_connection_status=True
        while True:
            # Create task instead of awaiting
            data = await websocket.receive_json()
            task = asyncio.create_task(handle_message(client_type, client_id, data))
            pending_tasks.add(task)
            task.add_done_callback(pending_tasks.discard)
    except WebSocketDisconnect:
        # Cancel pending tasks on disconnect
        for task in pending_tasks: 
            task.cancel()
        logger.info(f"Client disconnected: {client_type}/{client_id}")
        manager.disconnect(client_type, client_id)
        # If add-in disconnects, terminate its kernel
        if client_type == "addin":
            manager.terminate_kernel(client_id)
            # Broadcast workbook_disconnected to all IDE clients
            # Don't broadcast if first connection failed
            if first_connection_status:
                await manager.broadcast(
                    "ide",
                    {"type": "workbook_disconnected", "workbook_id": client_id},
                )
        elif client_type == "kernel":
            # Notify add-in if kernel disconnects
            await manager.send_message(
                "addin",
                client_id,
                {"type": "kernel_disconnected", "workbook_id": client_id},
            )




        


async def handle_message(client_type: str, client_id: str, message: dict):
    """
    Handle and route messages between clients using dispatch dictionary.

    Message format: {"type": "...", ...}
    """
    message_type = message.get("type")
    request_id = message.get("request_id", "N/A")
    
    # 1. Handle chunk messages first
    if message_type == "chunk":
        reassembled = await manager._handle_chunk_message(client_type, client_id, message)
        if reassembled:
            # Process the reassembled message by calling handle_message recursively
            await handle_message(client_type, client_id, reassembled)
        return  # Don't process chunk messages further
    
    # 2. Try to handle as a response to a pending request (in new asyncio task)
    asyncio.create_task(_try_handle_response(message))
    
    logger.debug(f"[TIMING] Received from {client_type}: type={message_type}, request_id={request_id}")
    start_time = time.time()
    
    # 3. Dispatch to handler from MESSAGE_HANDLERS
    handlers = MESSAGE_HANDLERS.get(client_type, {})
    handler = handlers.get(message_type)
    
    if handler:
        await handler(client_id, message)
    else:
        logger.warning(f"No handler for {client_type}/{message_type}")



async def full_code_sync(workbook_id:str):
    """
    ========== Full Code Sync ==========
    Before sending the custom_function_call, synchronize ALL modules that have
    changed since the last sync. This prevents ModuleNotFoundError when
    chains of dependencies are modified.
    """
    
    # Initialize synced hashes for this workbook if needed
    if workbook_id not in manager._synced_hashes:
        manager._synced_hashes[workbook_id] = {}
    
    # Get all modules for this workbook from the cache
    workbook_modules = manager.workbook_modules.get(workbook_id, {})
    modules_synced = 0
    
    # Iterate through all modules and sync those that have changed
    for mod_name, code in workbook_modules.items():
        if not code:
            continue
        
        # Compute hash of current code
        code_hash = compute_code_hash(code)
        prev_hash = manager._synced_hashes[workbook_id].get(mod_name)
        
        if code_hash != prev_hash:
            # Module has changed, send update_module to kernel
            update_message = {
                "type": "update_module",
                "workbook_id": workbook_id,
                "module_name": mod_name,
                "code": code,
            }
            await manager.send_message("kernel", workbook_id, update_message)
            
            # Update synced hash
            manager._synced_hashes[workbook_id][mod_name] = code_hash
            modules_synced += 1
            logger.debug(f"[Full Sync] Synced module '{mod_name}' to kernel")
    
    if modules_synced > 0:
        logger.info(f"[Full Sync] Synced {modules_synced} module(s) to kernel for workbook: {workbook_id}")
        

def _get_package_key(name: str, version: str, extras: Optional[List[str]] = None) -> str:
    """
    Generate a unique key for a package/version/extras combination.
    
    The key format is "name==version[extra1,extra2]" where extras are sorted alphabetically.
    This ensures consistent keys regardless of the order extras are specified.
    
    Args:
        name: Package name
        version: Package version
        extras: Optional list of extras (e.g., ["dev", "test"])
        
    Returns:
        A unique string key in format "name==version[extras]" or "name==version" if no extras
        
    Examples:
        _get_package_key("requests", "2.28.0", None) -> "requests==2.28.0"
        _get_package_key("requests", "2.28.0", ["security"]) -> "requests==2.28.0[security]"
        _get_package_key("pkg", "1.0", ["b", "a"]) -> "pkg==1.0[a,b]"
    """
    extras_str = f"[{','.join(sorted(extras))}]" if extras else ""
    return f"{name}=={version}{extras_str}"


def _find_package_by_name(packages: List[dict], package_name: str) -> Optional[dict]:
    """
    Find a package in the list by name (case-insensitive).
    
    Args:
        packages: List of package dictionaries
        package_name: Name to search for
        
    Returns:
        Package dict if found, None otherwise
    """
    normalized_name = package_name.lower()
    for pkg in packages:
        if pkg["name"].lower() == normalized_name:
            return pkg
    return None


def _find_direct_packages_for_dependency(workbook_id: str, dep_name: str) -> List[str]:
    """
    Find which direct packages depend on a given dependency.
    
    For now, returns all direct packages since we don't track per-package dependencies.
    This is a simplified approach - errors will be shown for all direct packages.
    
    Args:
        workbook_id: The workbook ID
        dep_name: The dependency package name
        
    Returns:
        List of direct package names
    """
    packages = manager.workbook_packages.get(workbook_id, [])
    return [pkg["name"] for pkg in packages]


def record_package_error(workbook_id: str, failed_package: str, error_msg: str, 
                         direct_package: Optional[str] = None):
    """
    Record an error for a package.
    
    If the failed package is a dependency, the error is attributed to its direct package.
    
    Args:
        workbook_id: The workbook ID
        failed_package: The name of the package that failed
        error_msg: The error message
        direct_package: The direct package this belongs to (if it's a dependency)
    """
    if workbook_id not in manager.package_errors:
        manager.package_errors[workbook_id] = {}
    
    target_package = direct_package if direct_package else failed_package
    
    if target_package not in manager.package_errors[workbook_id]:
        manager.package_errors[workbook_id][target_package] = []
    
    # Format error message to include which package failed
    if direct_package and failed_package != direct_package:
        full_error = f"Dependency '{failed_package}':\n{error_msg}"
    else:
        full_error = error_msg
    
    manager.package_errors[workbook_id][target_package].append(full_error)


async def handle_workbook_packages_install(workbook_id: str):
    """
    Complete package installation flow with proper workflow.
    
    Workflow:
    1. UNLOAD: Get stored paths, send unload request to kernel, kernel removes all modules from those paths
    2. BUILD LIST: Remove "to_remove" packages, keep others
    3. RESOLVE: Resolve all packages together as one dependency tree
    4. INSTALL: For each package, check cache or pip install, stream output to console
    5. STORE: Keep full resolution in memory for "See Resolution" popup
    6. UPDATE UI: All packages show "installed" status
    
    Args:
        workbook_id: The workbook ID to install packages for.
    """
    try:
        # Get workbook packages
        packages = manager.workbook_packages.get(workbook_id, [])
        if not packages:
            logger.info(f"No packages to install for workbook {workbook_id}")
            return
        
        # STEP 1: UNLOAD - Get stored paths and unload modules
        old_paths = manager.workbook_package_paths.get(workbook_id, [])
        if old_paths:
            logger.info(f"Unloading modules from {len(old_paths)} paths for workbook {workbook_id}")
            await manager.send_message("kernel", workbook_id, {
                "type": "unload_and_clear_paths",
                "paths": old_paths
            })
            # Clear the stored paths
            manager.workbook_package_paths[workbook_id] = []
        
        # STEP 2: BUILD LIST - Remove "to_remove" packages, keep others
        packages_to_remove = [pkg for pkg in packages if pkg.get("status") == "to_remove"]
        packages_to_install = [pkg for pkg in packages if pkg.get("status") != "to_remove"]
        
        # Clear any existing errors for this workbook
        manager.package_errors[workbook_id] = {}
        
        # Remove the "to_remove" packages from the list
        if packages_to_remove:
            manager.workbook_packages[workbook_id] = packages_to_install
            packages = packages_to_install
            logger.info(f"Removed {len(packages_to_remove)} packages marked for removal")
            
            # Send update to IDE to reflect removed packages
            await manager.broadcast("ide", {
                "type": "workbook_packages_update",
                "workbook_id": workbook_id,
                "packages": packages,
                "package_errors": manager.package_errors.get(workbook_id, {})
            })
        
        if not packages:
            logger.info(f"No packages to install after removing marked packages for workbook {workbook_id}")
            # Send installation complete message
            await manager.send_message("addin", workbook_id, {
            "type": "save_workbook_packages",
            "packages": []
            })

            await manager.broadcast("ide", {
                "type": "package_installation_complete",
                "workbook_id": workbook_id,
                "message": "✓ All packages removed. No packages to install."
            })
            return
        
        # STEP 3: RESOLVE - Update all to "resolving" status and resolve dependencies
        for pkg in packages:
            pkg["status"] = "resolving"

            # There is no more reason to not resolve all packages
            #if pkg.get("status") in ["pending", "pending_update", "error", "installed"]:
            #    pkg["status"] = "resolving"

        await manager.broadcast("ide", {
            "type": "workbook_packages_update",
            "workbook_id": workbook_id,
            "packages": packages,
            "package_errors": manager.package_errors.get(workbook_id, {})
        })
        
        # Create resolver
        resolver = DependencyResolver(
            settings_manager=package_manager.settings_manager,
            package_cache=package_manager.package_cache
        )
        
        # Convert to PackageSpec objects
        specs = [
            PackageSpec(
                name=pkg["name"],
                version=pkg["version"],
                extras=pkg.get("extras", [])
            )
            for pkg in packages
        ]
        
        # Resolve dependencies
        logger.info(f"Resolving dependencies for {len(specs)} packages in workbook {workbook_id}")
        await manager.broadcast("ide", {
            "type": "pip_output",
            "workbook_id": workbook_id,
            "output_type": "stdout",
            "message": f"Resolving dependencies for {len(specs)} package(s)..."
        })
        
        result = await resolver.resolve(specs)
        
        if not result.success:
            logger.error(f"Dependency resolution failed for workbook {workbook_id}: {result.errors}")
            # Mark all as error
            for pkg in packages:
                pkg["status"] = "error"
            await manager.broadcast("ide", {
                "type": "workbook_packages_update",
                "workbook_id": workbook_id,
                "packages": packages
            })
            # Send error messages to console
            for error in result.errors:
                await manager.broadcast("ide", {
                    "type": "pip_output",
                    "output_type": "error",
                    "workbook_id": workbook_id,
                    "message": f"{error}"
                })
            return
        
        # STEP 4: STORE - Store resolved deps for "See Resolution" popup
        manager.workbook_resolved_deps[workbook_id] = [
            {
                "name": r.spec.name,
                "version": r.spec.version,
                "extras": r.spec.extras,
                "is_direct": r.is_direct,
                "from_dist": r.spec.from_dist,
                "source": list(r.source),
                "is_error":r.is_error
            }
            for r in result.packages
        ]
        
        await manager.broadcast("ide", {
            "type": "pip_output",
            "workbook_id": workbook_id,
            "output_type": "success",
            "message": f"Resolved {len(result.packages)} package(s) including dependencies"
        })
        
        # Log conflicts if any
        if result.conflicts:
            logger.warning(f"Found {len(result.conflicts)} version conflicts: {result.conflicts}")
            for conflict in result.conflicts:
                await manager.broadcast("ide", {
                    "type": "pip_output",
                    "workbook_id": workbook_id,
                    "output_type": "warning",
                    "message": f"WARNING: Version conflict: {conflict}"
                })
        
        # STEP 5: INSTALL - Install each package with retry logic
        installed_paths = []
        successful_paths = []
        failed_packages = []
        
        # Initialize stderr tracking for this workbook
        if workbook_id not in manager.package_stderr:
            manager.package_stderr[workbook_id] = {}
        
        # First pass: Try to install all packages
        for resolved_pkg in result.packages:
            spec = resolved_pkg.spec
            
            # Check if package is from current distribution - skip installation
            if spec.from_dist:
                extras_str = f"[{','.join(spec.extras)}]" if spec.extras else ""
                logger.info(f"Skipping {spec.name}=={spec.version} (from current environment)")
                await manager.broadcast("ide", {
                    "type": "pip_output",
                    "workbook_id": workbook_id,
                    "output_type": "success",
                    "message": f"✓ {spec.name}{extras_str}=={spec.version} (from current environment)"
                })
                
                # Mark direct package as installed
                if resolved_pkg.is_direct:
                    pkg = _find_package_by_name(packages, spec.name)
                    if pkg:
                        pkg["status"] = "installed"
                    await manager.broadcast("ide", {
                        "type": "workbook_packages_update",
                        "workbook_id": workbook_id,
                        "packages": packages,
                        "package_errors": manager.package_errors.get(workbook_id, {})
                    })
                
                continue  # Skip to next package
            
            # Initialize stderr tracking for this package
            package_key = _get_package_key(spec.name, spec.version, spec.extras)
            manager.package_stderr[workbook_id][package_key] = []
            
            # Update direct packages to "installing"
            if resolved_pkg.is_direct:
                pkg = _find_package_by_name(packages, spec.name)
                if pkg:
                    pkg["status"] = "installing"
                await manager.broadcast("ide", {
                    "type": "workbook_packages_update",
                    "workbook_id": workbook_id,
                    "packages": packages,
                    "package_errors": manager.package_errors.get(workbook_id, {})
                })
            
            # Log to console
            extras_str = f"[{','.join(spec.extras)}]" if spec.extras else ""
            await manager.broadcast("ide", {
                "type": "pip_output",
                "workbook_id": workbook_id,
                "output_type": "stdout",
                "message": f"Processing {spec.name}{extras_str}=={spec.version}..."
            })
            
            try:
                # Install package and stream output
                path = None
                cached = False
                error_msg = None
                async for output_type, content in package_manager.install_package_to_cache(
                    spec.name, spec.version, spec.extras
                ):
                    if output_type == "path":
                        path = content
                    elif output_type == "cached":
                        path = content
                        cached = True
                    elif output_type == "stderr":
                        # Track stderr per package
                        manager.package_stderr[workbook_id][package_key].append(content)
                        # Also stream to console
                        await manager.broadcast("ide", {
                            "type": "pip_output",
                            "workbook_id": workbook_id,
                            "output_type": output_type,
                            "message": content
                        })
                    elif output_type == "stdout":
                        # Stream pip output to console
                        await manager.broadcast("ide", {
                            "type": "pip_output",
                            "workbook_id": workbook_id,
                            "output_type": output_type,
                            "message": content
                        })
                    elif output_type == "success":
                        # Log success message
                        if cached:
                            # Issue 8: Log cache hits
                            await manager.broadcast("ide", {
                                "type": "pip_output",
                                "workbook_id": workbook_id,
                                "output_type": "cached",
                                "message": f"Using cached {spec.name}{extras_str}=={spec.version} from {path}"
                            })
                        else:
                            await manager.broadcast("ide", {
                                "type": "pip_output",
                                "workbook_id": workbook_id,
                                "output_type": output_type,
                                "message": f"Installed {spec.name}{extras_str}=={spec.version} to {path}"
                            })
                    elif output_type == "error":
                        error_msg = content
                        logger.error(f"Error installing {spec.name}: {content}")
                
                if path:
                    installed_paths.append(path)
                    successful_paths.append(path)
                    logger.info(f"Installed {spec.name}=={spec.version} to {path}")
                elif error_msg:
                    # Package failed, add to failed list
                    failed_packages.append({
                        "pkg": resolved_pkg,
                        "spec": spec,
                        "error": error_msg,
                        "is_direct": resolved_pkg.is_direct
                    })
                    
                    # Record the error
                    if resolved_pkg.is_direct:
                        # Direct package error
                        record_package_error(workbook_id, spec.name, error_msg)
                    else:
                        # Dependency error - attribute to all direct packages
                        #direct_packages = _find_direct_packages_for_dependency(workbook_id, spec.name)
                        for direct_pkg in resolved_pkg.source:
                            record_package_error(workbook_id, spec.name, error_msg, direct_package=direct_pkg)
                    
                    # Mark direct packages as error (temporarily)
                    if resolved_pkg.is_direct:
                        pkg = _find_package_by_name(packages, spec.name)
                        if pkg:
                            pkg["status"] = "error"
                    await manager.broadcast("ide", {
                        "type": "pip_output",
                        "workbook_id": workbook_id,
                        "output_type": "error",
                        "message": f"{spec.name}{extras_str}=={spec.version}: {error_msg}"
                    })
                    
            except Exception as e:
                logger.error(f"Error installing {spec.name}: {e}")
                # Add to failed list
                failed_packages.append({
                    "pkg": resolved_pkg,
                    "spec": spec,
                    "error": str(e),
                    "is_direct": resolved_pkg.is_direct
                })
                
                # Record the error
                if resolved_pkg.is_direct:
                    # Direct package error
                    record_package_error(workbook_id, spec.name, str(e))
                else:
                    # Dependency error - attribute to all direct packages
                    #direct_packages = _find_direct_packages_for_dependency(workbook_id, spec.name)
                    for direct_pkg in resolved_pkg.source:
                        record_package_error(workbook_id, spec.name, str(e), direct_package=direct_pkg)
                
                # Mark direct packages as error
                if resolved_pkg.is_direct:
                    pkg = _find_package_by_name(packages, spec.name)
                    if pkg:
                        pkg["status"] = "error"
                await manager.broadcast("ide", {
                    "type": "pip_output",
                    "workbook_id": workbook_id,
                    "output_type": "error",
                    "message": f"{spec.name}{extras_str}=={spec.version}: {str(e)}"
                })
        
        # Retry loop for failed packages
        max_retries = 10
        retry_count = 0
        
        while failed_packages and retry_count < max_retries:
            previous_error_count = len(failed_packages)
            
            # Build enhanced environment with successful package paths in PYTHONPATH
            enhanced_env = os.environ.copy()
            existing_pythonpath = enhanced_env.get("PYTHONPATH", "")
            new_paths = os.pathsep.join(successful_paths)
            if existing_pythonpath:
                enhanced_env["PYTHONPATH"] = new_paths + os.pathsep + existing_pythonpath
            else:
                enhanced_env["PYTHONPATH"] = new_paths
            
            # Log retry attempt
            await manager.broadcast("ide", {
                "type": "pip_output",
                "workbook_id": workbook_id,
                "message": f"Retrying {len(failed_packages)} failed package(s) with enhanced environment..."
            })
            
            # Retry each failed package with enhanced env
            new_failed = []
            for fail_info in failed_packages:
                spec = fail_info["spec"]
                package_key = _get_package_key(spec.name, spec.version, spec.extras)
                extras_str = f"[{','.join(spec.extras)}]" if spec.extras else ""
                
                # Reset stderr for retry attempt
                manager.package_stderr[workbook_id][package_key] = []
                
                try:
                    path = None
                    cached = False
                    error_msg = None
                    async for output_type, content in package_manager.install_package_to_cache(
                        spec.name, spec.version, spec.extras, env=enhanced_env
                    ):
                        if output_type == "path":
                            path = content
                        elif output_type == "cached":
                            path = content
                            cached = True
                        elif output_type == "stderr":
                            # Don't Track stderr per package (even in retry)
                            manager.package_stderr[workbook_id][package_key].append(content)
                        elif output_type == "stdout":
                            # Stream pip output to console (suppress verbose output in retries)
                            pass
                        elif output_type == "success":
                            # Success in retry
                            pass
                        elif output_type == "error":
                            error_msg = content
                    
                    if path:
                        # Success!
                        successful_paths.append(path)
                        installed_paths.append(path)
                        # Update enhanced_env with new path
                        enhanced_env["PYTHONPATH"] = path + os.pathsep + enhanced_env["PYTHONPATH"]
                        
                        # Clear stderr for this package since it succeeded
                        if workbook_id in manager.package_stderr:
                            manager.package_stderr[workbook_id].pop(package_key, None)
                        
                        # Clear error from package_errors if this was a direct package
                        if fail_info["is_direct"]:
                            if workbook_id in manager.package_errors:
                                manager.package_errors[workbook_id].pop(spec.name, None)
                        
                        # Log success
                        if cached:
                            await manager.broadcast("ide", {
                                "type": "pip_output",
                                "workbook_id": workbook_id,
                                "output_type": "cached",
                                "message": f"Retry succeeded: {spec.name}{extras_str}=={spec.version} from cache {path}"
                            })
                        else:
                            await manager.broadcast("ide", {
                                "type": "pip_output",
                                "workbook_id": workbook_id,
                                "output_type": "success",
                                "message": f"Retry succeeded: {spec.name}{extras_str}=={spec.version} to {path}"
                            })
                        
                        # Clear error status for direct packages
                        if fail_info["is_direct"]:
                            pkg = _find_package_by_name(packages, spec.name)
                            if pkg:
                                pkg["status"] = "installing"
                    else:
                        # Still failed
                        new_failed.append(fail_info)
                        if error_msg:
                            fail_info["error"] = error_msg
                            
                except Exception as e:
                    logger.error(f"Error retrying {spec.name}: {e}")
                    fail_info["error"] = str(e)
                    new_failed.append(fail_info)
            
            failed_packages = new_failed
            retry_count += 1
            
            # Check if we made progress
            if len(failed_packages) >= previous_error_count:
                # No progress, stop retrying
                break
        
        # Final report on failures
        if failed_packages:
            await manager.broadcast("ide", {
                "type": "pip_output",
                "workbook_id": workbook_id,
                "output_type": "error",
                "message": f"{len(failed_packages)} package(s) failed to install after retries:"
            })
            
            # Build final package_errors from packages still in error
            final_errors = {}
            for fail_info in failed_packages:
                spec = fail_info["spec"]
                package_key = _get_package_key(spec.name, spec.version, spec.extras)
                extras_str = f"[{','.join(spec.extras)}]" if spec.extras else ""
                
                # Get stderr for this package
                stderr_lines = manager.package_stderr.get(workbook_id, {}).get(package_key, [])
                
                # Log to console
                await manager.broadcast("ide", {
                    "type": "pip_output",
                    "workbook_id": workbook_id,
                    "output_type": "error",
                    "message": f"  - {spec.name}{extras_str}=={spec.version}: {fail_info['error']}"
                })
                
                fail_info['pkg'].is_error = True
                # Add to final errors
                if fail_info["is_direct"]:
                    # Direct package error
                    if spec.name not in final_errors:
                        final_errors[spec.name] = []
                    else:
                        final_errors[spec.name].append('\n')
                    # Use stderr lines if available, otherwise use error message
                    if stderr_lines:
                        final_errors[spec.name].extend(stderr_lines)
                    else:
                        final_errors[spec.name].append(fail_info["error"])
                else:
                    # Dependency error - attribute to direct packages
                    #direct_packages = _find_direct_packages_for_dependency(workbook_id, spec.name)
                    for direct_pkg in fail_info['pkg'].source:
                        if direct_pkg not in final_errors:
                            final_errors[direct_pkg] = []
                        else:
                            final_errors[direct_pkg].append('\n')
                        error_msg = f"Dependency '{spec.name}':\n{fail_info['error']}"
                        final_errors[direct_pkg].append(error_msg)
                        # Add stderr lines without prefix - let UI handle formatting
                        final_errors[direct_pkg].extend(stderr_lines)
                
                # Mark direct packages as error
                if fail_info["is_direct"]:
                    pkg = _find_package_by_name(packages, spec.name)
                    if pkg:
                        pkg["status"] = "error"
            
            # Update manager.package_errors with final errors
            manager.package_errors[workbook_id] = final_errors
            manager.workbook_resolved_deps[workbook_id] = [
                {
                    "name": r.spec.name,
                    "version": r.spec.version,
                    "extras": r.spec.extras,
                    "is_direct": r.is_direct,
                    "from_dist": r.spec.from_dist,
                    "source": list(r.source),
                    "is_error":r.is_error
                }
                for r in result.packages
            ]
        
        # STEP 6: UPDATE UI - Update all direct packages status
        for pkg in packages:
            if pkg.get("status") in ["installing", "resolving", "pending", "pending_update"]:
                # Check if this package has errors
                if pkg["name"] in manager.package_errors.get(workbook_id, {}):
                    pkg["status"] = "installed_with_errors"
                else:
                    pkg["status"] = "installed"
        
        await manager.broadcast("ide", {
            "type": "workbook_packages_update",
            "workbook_id": workbook_id,
            "packages": packages,
            "package_errors": manager.package_errors.get(workbook_id, {})
        })
        
        # Save installed state for restore functionality
        manager.workbook_installed_packages[workbook_id] = packages.copy()
        
        # Send paths to kernel
        manager.workbook_package_paths[workbook_id] = installed_paths
        
        if installed_paths:
            await manager.send_message("kernel", workbook_id, {
                "type": "set_package_paths",
                "old_paths": old_paths,  # Include old_paths for proper cleanup
                "new_paths": installed_paths
            })
            logger.info(f"Sent {len(installed_paths)} package paths to kernel for workbook {workbook_id}")
            
            # Broadcast package paths update to IDE
            # (LSP in kernel is already updated; this is for IDE logging and future IDE-based LSP)
            await manager.broadcast("ide", {
                "type": "package_paths_updated",
                "workbook_id": workbook_id,
                "paths": installed_paths,
                "old_paths": old_paths
            })
        
        # Send to Add-in for persistence
        await manager.send_message("addin", workbook_id, {
            "type": "save_workbook_packages",
            "packages": packages
        })
        logger.info(f"Sent package list to Add-in for persistence: {len(packages)} packages")
        
        # Send installation complete message to IDE
        installed_count = sum(1 for pkg in packages if pkg["status"].startswith("installed"))
        await manager.broadcast("ide", {
            "type": "package_installation_complete",
            "workbook_id": workbook_id,
            "message": f"✓ Installation complete. {installed_count} package(s) installed."
        })
        
    except Exception as e:
        logger.error(f"Package installation failed for {workbook_id}: {e}", exc_info=True)
        # Always update IDE
        if workbook_id in manager.workbook_packages:
            await manager.broadcast("ide", {
                "type": "workbook_packages_update",
                "workbook_id": workbook_id,
                "packages": manager.workbook_packages[workbook_id]
            })
            await manager.broadcast("ide", {
                "type": "pip_output",
                "output_type": "error",
                "workbook_id": workbook_id,
                "message": f"Installation failed: {str(e)}"
            })
    finally:
        manager.workbook_installed_packages[workbook_id]=manager.workbook_packages.get(workbook_id, []).copy()

# Initialize package handlers after handle_workbook_packages_install is defined
init_handlers(manager, package_manager, handle_workbook_packages_install)


async def root():
    """Health check endpoint."""
    return {"status": "running", "service": "XPyCode Business Layer"}


async def get_connections():
    """Get current connection status."""
    return {
        client_type: list(connections.keys())
        for client_type, connections in manager.active_connections.items()
    }

_port=8000

def set_port(port: int):
    """Set the global port variable."""
    global _port
    _port = port

def initialize_ide_manager(server_port: int, watchdog_port: int, auth_token: str, docs_port: int):
    """Initialize the IDE manager."""
    global ide_manager
    ide_manager = IDEProcessManager(server_port=server_port, watchdog_port=watchdog_port, auth_token=auth_token, docs_port=docs_port)
    logger.info(f"IDE manager initialized with server port: {server_port}, watchdog port: {watchdog_port}, docs port: {docs_port}")


if __name__ == "__main__":
    # This module should not be run directly
    # Use server.py instead
    pass
