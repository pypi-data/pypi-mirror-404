"""
Python Kernel - Per-workbook execution environment for XPyCode V3.

This module provides:
- WebSocket connection to the Business Layer
- Execution loop for code requests
- CodeExecutor class using exec() for Python code execution
- Stdout/stderr capture and streaming
- Virtual environment structure with sys.path modification
- Integration with xpycode module for COM-like Excel bridge

SECURITY NOTE:
This kernel is intentionally designed to execute arbitrary Python code
provided by users. The exec()/eval() usage is a core feature, not a
vulnerability. Security should be enforced at the deployment level
(e.g., container isolation, sandboxing, network restrictions).
"""

import asyncio
import concurrent.futures
import functools
import importlib.abc
import importlib.machinery
import importlib.util
import linecache
import inspect
import json
import logging
import sys
import io
import threading
import time
import traceback
import uuid
from contextlib import redirect_stdout, redirect_stderr
from typing import Dict, Any, Optional, List, Set

import websockets

# Try to use orjson for faster JSON serialization
try:
    import orjson
    def json_dumps(obj):
        return orjson.dumps(obj).decode('utf-8')
except ImportError:
    def json_dumps(obj):
        return json.dumps(obj)

# Import LSPBridge for autocompletion (uses jedi configured like pylsp)
# Use try/except to handle both package import and direct script execution
try:
    from .lsp_bridge import LSPBridge
except ImportError:
    from lsp_bridge import LSPBridge

# Import Agent for natural language command processing
try:
    from .agent import Agent
except ImportError:
    from agent import Agent

# Import EventManager for Excel event registration and dispatching
try:
    from .event_manager import EventManager
except ImportError:
    from event_manager import EventManager

# Import debugger - handle both package import and direct script execution
try:
    from .debugger import XPyCodeDebugger
except ImportError:
    from debugger import XPyCodeDebugger


# Configure logging early so it's available for all classes
from ..logging_config import setup_logging_subprocess, get_logger
setup_logging_subprocess()
logger = get_logger(__name__)

# Debug message send timeout (in seconds)
DEBUG_MESSAGE_SEND_TIMEOUT = 5.0


def _parse_error_location(traceback_str: str, in_memory_modules: set) -> dict:
    """
    Parse a traceback string to find the error location in user code.
    
    Looks for lines like:
      File "<virtual:module_name>", line 10, in function_name
    
    Args:
        traceback_str: The formatted traceback string
        in_memory_modules: Set of in-memory module names
        
    Returns:
        Dict with 'module', 'line', 'file' keys, or empty dict if not found
    """
    import re
    
    # Pattern to match traceback lines
    # Example: File "<virtual:cc>", line 10, in sdg
    pattern = r'File ["\']<virtual:(\w+)>["\'], line (\d+)'
    
    matches = re.findall(pattern, traceback_str)
    
    # Return the last match (closest to the actual error)
    if matches:
        module_name, line_str = matches[-1]
        return {
            "module": module_name,
            "line": int(line_str),
            "file": f"<virtual:{module_name}>"
        }
    
    # Also try to match regular file paths for in-memory modules
    # This handles cases where the virtual file pattern might differ
    for module_name in in_memory_modules:
        pattern2 = rf'File ["\'][^"\']*{re.escape(module_name)}[^"\']*["\'], line (\d+)'
        match = re.search(pattern2, traceback_str)
        if match:
            return {
                "module": module_name,
                "line": int(match.group(1)),
                "file": f"<virtual:{module_name}>"
            }
    
    return {}

def extract_tracebak_string(e:Exception) -> str:
    """Extract formatted traceback string from an exception."""
    tb_lines = traceback.format_exception(type(e), e, e.__traceback__)
    return ''.join(tb_lines)

class InMemoryModuleLoader(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """
    Custom module loader that supports importing modules from in-memory source code.

    This loader implements both MetaPathFinder (to locate modules) and Loader
    (to execute module code) interfaces from importlib.abc.
    """

    def __init__(self):
        # Dictionary mapping module names to source code strings
        self.source_cache: Dict[str, str] = {}

    def find_spec(self, fullname: str, path, target=None):
        """
        Find the module spec for a module name if it exists in source_cache.

        Args:
            fullname: The fully qualified module name.
            path: The path(s) to search for the module.
            target: Optional target module (used for reloads).

        Returns:
            ModuleSpec if module is in source_cache, None otherwise.
        """
        if fullname in self.source_cache:
            return importlib.machinery.ModuleSpec(fullname, self)
        return None

    def create_module(self, spec):
        """
        Return None to use default module creation semantics.
        """
        return None

    def exec_module(self, module):
        """
        Execute the module's source code in the module's namespace.

        Args:
            module: The module object to execute code in.

        Raises:
            ImportError: If the module source is not found in the cache.
        """
        fullname = module.__name__
        if fullname not in self.source_cache:
            raise ImportError(f"No source code found for module '{fullname}'")
        source = self.source_cache[fullname]

        file_name=f"<virtual:{fullname}>"
        linecache.cache[file_name] = (
                                len(source), 
                                  None, 
                                  [line+ '\n' for line in source.splitlines()],
                                   file_name,
                                  )

        # Compile and execute the source code in the module's namespace
        try:
            code = compile(source, file_name, "exec")
            exec(code, module.__dict__)
        except Exception as e:
            logger.error(f"[InMemoryModuleLoader] Error executing module '{fullname}': {e}")
            tb = e.__traceback__
            this_module_name = __name__

            while tb is not None:
                frame_module = tb.tb_frame.f_globals.get("__name__")
                if frame_module != this_module_name:
                    break
                tb = tb.tb_next

            # Re-raise the same exception, but starting at the first non-proxy frame.
            raise e.with_traceback(tb) from None

    def update_module(self, module_name: str, code: str):
        """
        Update or add a module's source code in the cache.

        If the module is already imported (in sys.modules), it is removed
        to force a fresh import on the next `import` statement.

        Args:
            module_name: The name of the module.
            code: The source code for the module.
        """
        self.source_cache[module_name] = code
        # Force reload by removing from sys.modules if it exists
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.debug(
                f"[InMemoryModuleLoader] Removed '{module_name}' from sys.modules to force reload"
            )
    
    def delete_module(self, module_name: str):
        """
        Delete a module from the source cache and sys.modules.
        
        Args:
            module_name: The name of the module to delete.
        """
        # Remove from source cache
        if module_name in self.source_cache:
            del self.source_cache[module_name]
            logger.debug(f"[InMemoryModuleLoader] Removed '{module_name}' from source_cache")
        
        # Remove from sys.modules if it exists
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.debug(f"[InMemoryModuleLoader] Removed '{module_name}' from sys.modules")
        
        # Also remove from linecache if it was cached
        file_name = f"<virtual:{module_name}>"
        if file_name in linecache.cache:
            del linecache.cache[file_name]
            logger.debug(f"[InMemoryModuleLoader] Removed '{file_name}' from linecache")

# Import xpycode module for COM-like Excel bridge
# Use try/except to handle both package import and direct script execution
try:
    from . import xpycode
    sys.modules['xpycode']=xpycode
except ImportError:
    import xpycode


# Maximum message size (1MB)
MAX_MESSAGE_SIZE = 1024 * 1024

# Constants for chunking
CHUNK_SIZE = 64 * 1024  # 64KB chunks (safe for most WebSocket implementations)
CHUNK_HEADER_TYPE = "chunk"

# Global in-memory module loader instance
# This is registered in sys.meta_path to support virtual module imports
in_memory_loader = InMemoryModuleLoader()

# Register the loader at position 0 in sys.meta_path to take precedence
# This allows `import module_name` to work for modules sent via update_module
if in_memory_loader not in sys.meta_path:
    sys.meta_path.insert(0, in_memory_loader)


class VirtualEnvironment:
    """
    Mock virtual environment structure for managing sys.path.

    This allows per-workbook Python environments with custom package paths.
    """

    def __init__(self, workbook_id: str):
        self.workbook_id = workbook_id
        self.original_path = sys.path.copy()
        self.custom_paths: list = []

    def add_path(self, path: str):
        """Add a path to the virtual environment's sys.path."""
        if path not in self.custom_paths:
            self.custom_paths.append(path)
            if path not in sys.path:
                sys.path.insert(0, path)

    def remove_path(self, path: str):
        """Remove a path from the virtual environment's sys.path."""
        if path in self.custom_paths:
            self.custom_paths.remove(path)
            if path in sys.path:
                sys.path.remove(path)

    def reset_path(self):
        """Reset sys.path to original state."""
        sys.path.clear()
        sys.path.extend(self.original_path)
        self.custom_paths.clear()

    def get_paths(self) -> list:
        """Get current custom paths."""
        return self.custom_paths.copy()


class StreamCapture(io.TextIOBase):
    """
    Custom stream class that captures output and streams it in real-time.

    This class inherits from io.TextIOBase and calls a callback function
    whenever data is written, allowing for real-time streaming of stdout/stderr.
    """

    def __init__(self, on_write=None):
        """
        Initialize the StreamCapture.

        Args:
            on_write: Callback function that receives the written text.
                      Signature: on_write(text: str) -> None
        """
        super().__init__()
        self._buffer = io.StringIO()
        self._on_write = on_write

    def write(self, text: str) -> int:
        """Write text to the stream and call the callback."""
        if not text:
            return 0
        self._buffer.write(text)
        if self._on_write:
            try:
                self._on_write(text)
            except Exception:
                # Don't let callback errors affect code execution
                pass
        return len(text)

    def getvalue(self) -> str:
        """Get all captured output."""
        return self._buffer.getvalue()

    def flush(self):
        """Flush the stream (no-op for StringIO-backed buffer)."""
        pass

    def readable(self):
        """Return False as this stream is not readable."""
        return False

    def writable(self):
        """Return True as this stream is writable."""
        return True


class KernelStreamHook(io.TextIOBase):
    """
    Custom stream hook for kernel-level stdout/stderr streaming.
    
    This hook intercepts all writes to stdout/stderr and immediately sends
    them as stdout/stderr messages to the Business Layer, enabling real-time
    logging in both the IDE and Add-in.
    """

    def __init__(self, stream_type: str, send_callback):
        """
        Initialize the KernelStreamHook.

        Args:
            stream_type: Either 'stdout' or 'stderr' to identify the stream.
            send_callback: Callback function to send stdout/stderr messages.
                          Signature: send_callback(stream_type: str, content: str) -> None
        """
        super().__init__()
        self.stream_type = stream_type
        self.send_callback = send_callback
        self._original_stream = sys.stdout if stream_type == 'stdout' else sys.stderr

    def write(self, text: str) -> int:
        """Write text to the stream and send it immediately via stdout/stderr message."""
        if not text:
            return 0
        
        # Write to original stream for local console visibility
        try:
            self._original_stream.write(text)
            self._original_stream.flush()
        except Exception:
            pass

        # Send via stdout/stderr message
        if self.send_callback:
            try:
                self.send_callback(self.stream_type, text)
            except Exception as e:
                # Don't let callback errors affect code execution
                # But log to original stream for debugging
                try:
                    self._original_stream.write(f"[KernelStreamHook Error] {e}\n")
                except Exception:
                    pass
        
        return len(text)

    def flush(self):
        """Flush the stream."""
        try:
            self._original_stream.flush()
        except Exception:
            pass

    def readable(self):
        """Return False as this stream is not readable."""
        return False

    def writable(self):
        """Return True as this stream is writable."""
        return True


class CodeExecutor:
    """
    Executes Python code and captures output.

    Uses exec() for code execution and captures stdout/stderr.
    Injects xpycode module (excel, context) into user namespace.
    """

    def __init__(self):
        # Global namespace for code execution (persists between executions)
        # Inject xpycode module and its key components
        self.globals: Dict[str, Any] = {
            "__builtins__": __builtins__,
            "xpycode": xpycode,
            "excel": xpycode.excel,
            "context": xpycode.context,
        }
        # Local namespace
        self.locals: Dict[str, Any] = {}

    def execute(
        self,
        code: str,
        stdout_callback=None,
        stderr_callback=None,
    ) -> Dict[str, Any]:
        """
        Execute Python code and return results.

        Args:
            code: The Python code to execute.
            stdout_callback: Optional callback for real-time stdout streaming.
                             Signature: callback(text: str) -> None
            stderr_callback: Optional callback for real-time stderr streaming.
                             Signature: callback(text: str) -> None

        Returns:
            dict with keys: 'success', 'stdout', 'stderr', 'error', 'result'
        """
        stdout_capture = StreamCapture(on_write=stdout_callback)
        stderr_capture = StreamCapture(on_write=stderr_callback)

        result = {
            "success": True,
            "stdout": "",
            "stderr": "",
            "error": None,
            "result": None,
        }

        try:
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                # Determine if code is an expression without triggering exception chaining
                is_expression = False
                compiled = None
                try:
                    compiled = compile(code, "<kernel>", "eval")
                    is_expression = True
                except SyntaxError:
                    # Not an expression, will execute as statements
                    pass

                if is_expression:
                    result["result"] = eval(compiled, self.globals, self.locals)
                else:
                    # Handle "import module; module.function()" pattern to capture return value
                    # This pattern is generated by the IDE when running functions
                    # Split on semicolons to separate import from function call
                    if '; ' in code:
                        parts = code.split('; ', 1)
                        import_stmt, call_expr = parts[0], parts[1] if len(parts) > 1 else ''
                        if call_expr:
                            # First, execute the import statement
                            exec(import_stmt, self.globals, self.locals)
                            # Then, try to evaluate the function call as an expression
                            try:
                                call_compiled = compile(call_expr, "<kernel>", "eval")
                                result["result"] = eval(call_compiled, self.globals, self.locals)
                            except SyntaxError:
                                # If the second part isn't an expression, execute it as a statement
                                exec(call_expr, self.globals, self.locals)
                        else:
                            exec(code, self.globals, self.locals)
                    else:
                        exec(code, self.globals, self.locals)
                
                # Flush stdout/stderr to ensure all output is captured
                sys.stdout.flush()
                sys.stderr.flush()

        except Exception as e:
            result["success"] = False
            result["error"] = {
                "type": type(e).__name__,
                "message": str(e),
                "traceback":extract_tracebak_string(e),# traceback.format_exc(),
            }
            # Also flush stdout/stderr when an exception occurs to capture any partial output
            try:
                sys.stdout.flush()
                sys.stderr.flush()
            except Exception:
                pass

        result["stdout"] = stdout_capture.getvalue()
        result["stderr"] = stderr_capture.getvalue()

        return result

    def reset_namespace(self):
        """Reset the execution namespace while keeping xpycode injected."""
        self.globals = {
            "__builtins__": __builtins__,
            "xpycode": xpycode,
            "excel": xpycode.excel,
            "context": xpycode.context,
        }
        self.locals = {}


class MessageBatcher:
    """
    Batches outgoing messages to reduce WebSocket overhead.
    
    Collects messages for a short interval (default 10ms) then sends
    them as a single batch message, reducing per-message overhead.
    """
    
    FLUSH_INTERVAL = 0.01  # 10ms batching window
    
    def __init__(self, kernel: 'PythonKernel'):
        self._kernel = kernel
        self._queue: asyncio.Queue = asyncio.Queue()
        self._flush_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self):
        """Start the background flush loop."""
        self._running = True
        self._flush_task = asyncio.create_task(self._flush_loop())
    
    async def stop(self):
        """Stop the batcher and flush remaining messages."""
        self._running = False
        if self._flush_task:
            self._flush_task.cancel()
            try:
                await self._flush_task
            except asyncio.CancelledError:
                pass
        # Flush any remaining messages
        await self._flush_now()
    
    async def enqueue(self, message: dict):
        """Add a message to the batch queue."""
        await self._queue.put(message)
    
    async def _flush_loop(self):
        """Background loop that flushes batches periodically."""
        while self._running:
            await asyncio.sleep(self.FLUSH_INTERVAL)
            await self._flush_now()
    
    async def _flush_now(self):
        """Flush all queued messages as a batch."""
        batch = []
        while not self._queue.empty():
            try:
                msg = self._queue.get_nowait()
                batch.append(msg)
            except asyncio.QueueEmpty:
                break
        
        if not batch:
            return
        
        if len(batch) == 1:
            # Single message - send directly
            await self._kernel._send_message_direct(batch[0])
        else:
            # Multiple messages - send as batch
            await self._kernel._send_message_direct({
                "type": "batch",
                "messages": batch
            })


class PythonKernel:
    """
    Python Kernel that connects to the Business Layer and executes code.
    
    Architecture (Producer-Consumer/Worker Thread Model):
    -------------------------------------------------------
    1. **Socket Listener Thread** (Main Async Event Loop):
       - Runs in the main thread as an asyncio event loop
       - Receives messages from the Business Layer via WebSocket
       - Dispatches execution requests to the worker thread pool
       - Handles sys_response messages immediately to unblock workers
       
    2. **Worker Thread Pool** (ThreadPoolExecutor):
       - Executes Python functions in separate threads
       - Multiple workers (WORKER_POOL_SIZE) prevent deadlock
       - Workers can make synchronous sys_request calls
       - Each worker blocks on threading.Event waiting for sys_response
       
    3. **Thread Safety**:
       - Socket writes are protected by _socket_lock (asyncio.Lock)
       - Response futures are protected by _response_lock (threading.Lock)
       - stdout/stderr hooks are thread-safe via asyncio scheduling
       
    This architecture prevents deadlock when a Python function calls back
    to Excel (e.g., xpycode.read_range) because:
    - The socket listener continues processing messages while workers block
    - Multiple workers allow parallel execution
    - sys_response messages immediately unblock waiting workers
    
    Integrates with xpycode module to provide COM-like Excel bridge.
    User code is executed in a separate thread to allow synchronous
    xpycode calls while the async WebSocket message loop continues.
    """
    
    # Number of worker threads for executing Python code
    # This value is chosen to allow multiple concurrent function executions
    # while preventing excessive context switching overhead. It allows up to
    # 10 functions to execute in parallel, which is sufficient for typical
    # workbook scenarios where functions may call back to Excel via sys_request.
    WORKER_POOL_SIZE = 10

    def __init__(self, workbook_id: str, host: str = "127.0.0.1", port:str="8000"):
        self.workbook_id = workbook_id
        self.server_url = f"ws://{host}:{port}"
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.executor = CodeExecutor()
        self.virtual_env = VirtualEnvironment(workbook_id)
        self.running = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        # Use a thread pool with multiple workers to prevent deadlock
        # when functions make sys_request calls that wait for sys_response
        self._thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=self.WORKER_POOL_SIZE)
        # Initialize LSP bridge for autocompletion
        self._lsp_bridge = LSPBridge()
        # Initialize Agent for natural language command processing
        self.agent = Agent(xpycode.excel, xpycode.context)
        # Initialize EventManager for Excel event registration and dispatching
        self.event_manager = EventManager()
        
        # ObjectKeeper dictionary for storing user objects
        self._object_keeper: Dict[str, Any] = {}
        self._object_keeper_lock = threading.Lock()
        
        # Response futures for synchronous sys_request/sys_response mechanism
        self._response_futures: Dict[str, threading.Event] = {}
        self._response_data: Dict[str, dict] = {}
        self._response_lock = threading.Lock()
        
        # Track canceled streaming requests
        self._canceled_streaming_requests: Set[str] = set()
        
        # Chunk reassembly buffers for incoming messages
        self._chunk_buffers: Dict[str, Dict[str, Any]] = {}
        
        # Socket write lock for thread-safe message sending (asyncio.Lock)
        # Initialized as None and set to asyncio.Lock() in connect() after event loop starts
        self._socket_lock: Optional[asyncio.Lock] = None
        
        # Message batcher for reducing WebSocket overhead
        self._batcher: Optional[MessageBatcher] = None
        
        # Original stdout/stderr for restoration
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        
        # Ensure InMemoryModuleLoader is registered in sys.meta_path
        # This is a defensive check to ensure imports work for in-memory modules
        if in_memory_loader not in sys.meta_path:
            sys.meta_path.insert(0, in_memory_loader)
            logger.debug("[Kernel] Registered InMemoryModuleLoader in sys.meta_path")
    
    @property
    def has_active_debugger(self) -> bool:
        """Check if there is an active debugger instance."""
        return hasattr(self, '_debugger') and self._debugger is not None

    async def connect(self):
        """
        Connect to the Business Layer WebSocket endpoint.
        
        Threading Note: This method must be called from the main async event loop.
        It initializes the _socket_lock which will be used by worker threads to
        safely send messages through the WebSocket.
        
        Raises:
            RuntimeError: If not called from within a running async event loop
        """
        ws_url = f"{self.server_url}/ws/kernel/{self.workbook_id}"
        self.websocket = await websockets.connect(ws_url)
        self.running = True
        # get_running_loop() will raise RuntimeError if not in a running event loop
        self._loop = asyncio.get_running_loop()
        
        # Initialize asyncio lock for thread-safe socket writes
        # This lock protects the WebSocket from concurrent writes by multiple worker threads
        self._socket_lock = asyncio.Lock()

        # Configure xpycode messaging to use this kernel's event loop
        xpycode.messaging.loop = self._loop
        xpycode.messaging.loop_thread = threading.current_thread()
        
        # Set kernel instance reference for ObjectKeeper functions
        xpycode._kernel_instance = self
        
        # Start message batcher
        self._batcher = MessageBatcher(self)
        await self._batcher.start()

        # Install kernel-level stdout/stderr hooks for real-time streaming
        def send_stream_message(stream_type: str, content: str):
            """Send stdout/stderr message for real-time log streaming."""
            try:
                message = {
                    "type": stream_type,  # "stdout" or "stderr"
                    "content": content,
                    "workbook_id": self.workbook_id,
                }
                # Schedule the send on the event loop
                asyncio.run_coroutine_threadsafe(
                    self.send_message(message), self._loop
                )
            except Exception as e:
                # Don't let streaming errors affect code execution
                logger.debug(f"[Kernel] {stream_type} streaming error: {e}")

        # Replace sys.stdout and sys.stderr with kernel hooks
        sys.stdout = KernelStreamHook('stdout', send_stream_message)
        sys.stderr = KernelStreamHook('stderr', send_stream_message)

        # Register a send handler with xpycode.messaging that forwards
        # sys_request messages through the Business Layer to the add-in
        def send_sys_request(payload: dict, timeout: float = 30.0):
            """
            Send a sys_request message and wait for sys_response.
            
            This function is called from worker threads when Python code
            makes synchronous calls to Excel (e.g., xpycode.read_range).
            It blocks the worker thread until the listener thread receives
            and processes the sys_response message.
            
            Threading Model:
            - Called from: Worker thread (ThreadPoolExecutor)
            - Blocks: Current worker thread only (via threading.Event.wait())
            - Does NOT block: Listener thread (continues processing WebSocket messages)
            - Synchronization: threading.Lock protects _response_futures dict
            """
            request_id = payload.get("requestId")
            thread_name = threading.current_thread().name
            
            # Defensive check: Calling this from the event loop thread would cause deadlock
            # since event.wait() would block the only thread that can process sys_response.
            # Note: In the current architecture, this is prevented by design (workers only),
            # but we check defensively in case of future refactoring.
            if xpycode.messaging.loop_thread is not None:
                if threading.current_thread() == xpycode.messaging.loop_thread:
                    raise RuntimeError(
                        "send_sys_request must not be called from the async event loop thread "
                        "to avoid deadlock"
                    )
            
            logger.debug(f"[Kernel] [Worker Thread {thread_name}] Sending sys_request: {request_id}")
            
            # Create an event for this request
            # Threading Note: threading.Event is thread-safe for wait/set operations
            event = threading.Event()
            with self._response_lock:
                self._response_futures[request_id] = event
            
            # Send the sys_request message via the listener thread's event loop
            message = {
                "type": "sys_request",
                "payload": payload,
            }
            asyncio.run_coroutine_threadsafe(
                self.send_message(message), self._loop
            )
            
            logger.debug(f"[Kernel] [Worker Thread {thread_name}] Waiting for sys_response: {request_id}")
            # Wait for the sys_response (blocks the worker thread, but listener thread continues)
            # Threading Note: event.wait() releases the GIL, allowing the listener thread to continue
            if not event.wait(timeout=timeout):
                # Timeout - clean up and raise
                with self._response_lock:
                    self._response_futures.pop(request_id, None)
                    self._response_data.pop(request_id, None)
                logger.error(f"[Kernel] [Worker Thread {thread_name}] sys_request timeout: {request_id}")
                raise TimeoutError(f"sys_request timeout after {timeout}s: {request_id}")
            
            logger.debug(f"[Kernel] [Worker Thread {thread_name}] Received sys_response: {request_id}")
            # Get the response data
            # Threading Note: Lock protects concurrent dict access from listener thread
            with self._response_lock:
                response = self._response_data.pop(request_id, None)
                self._response_futures.pop(request_id, None)
            
            # Validate we got the response (should always be present after event is set)
            if response is None:
                error_msg = f"sys_response data missing for request_id: {request_id}"
                logger.error(f"[Kernel] {error_msg}")
                raise RuntimeError(error_msg)
            
            return response

        # Replace the xpycode messaging send handler to use sys_request
        def new_send_request_sync(req: Dict[str, Any], timeout: float = 30.0):
            """Send request using sys_request/sys_response mechanism."""
            rid = uuid.uuid4().hex
            env = {**req, "requestId": rid, "kind": "request"}
            response = send_sys_request(env, timeout=timeout)
            return response
        
        xpycode.messaging.send_request_sync = new_send_request_sync

    async def disconnect(self):
        """Disconnect from the Business Layer."""
        self.running = False
        # Stop batcher before disconnecting
        if self._batcher:
            await self._batcher.stop()
        # Reset xpycode messaging state
        xpycode.messaging.reset()
        # Clear kernel instance reference
        xpycode._kernel_instance = None
        # Restore original stdout/stderr
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr
        if self.websocket:
            await self.websocket.close()
        # Shutdown thread pool
        self._thread_pool.shutdown(wait=False)

    async def send_message(self, message: dict):
        """
        Send a JSON message to the Business Layer.
        
        Thread-safe: Uses an asyncio lock to ensure multiple worker threads can safely
        send messages without corrupting the WebSocket stream.
        """
        message_type = message.get("type", "")
        
        # Batch function results and streaming results
        if False and message_type in ("execution_result", "execution_error"):
            if self._batcher:
                await self._batcher.enqueue(message)
                return
        
        # Send other messages directly
        await self._send_message_direct(message)
    
    async def _send_message_direct(self, message: dict):
        """Send a message directly, chunking if necessary."""
        message_type = message.get("type", "unknown")
        request_id = message.get("request_id", "N/A")
        
        if self.websocket and self._socket_lock is not None:
            logger.debug(f"[TIMING] Acquiring socket lock for: type={message_type}, request_id={request_id}")
            start_time = time.time()
            
            raw_json = json_dumps(message)
            
            # Check if message needs chunking
            if len(raw_json) > CHUNK_SIZE:
                await self._send_chunked_message(raw_json, message_type, request_id)
            else:
                # Use asyncio lock to ensure thread-safe writes to WebSocket
                async with self._socket_lock:
                    lock_wait_ms = (time.time() - start_time) * 1000
                    if lock_wait_ms > 5:  # Only log if waited more than 5ms
                        logger.warning(f"[TIMING] Socket lock waited {lock_wait_ms:.1f}ms for: type={message_type}")
                    
                    await self.websocket.send(raw_json)
            
            logger.debug(f"[TIMING] Message sent: type={message_type}, request_id={request_id}")
        else:
            # Log warning if trying to send before connection is established
            if not self.websocket:
                logger.warning(f"[Kernel] Cannot send message type '{message_type}': WebSocket not connected")
            elif self._socket_lock is None:
                logger.warning(f"[Kernel] Cannot send message type '{message_type}': Socket lock not initialized")
    
    async def _send_chunked_message(self, raw_json: str, message_type: str, request_id: str):
        """Send a large message in chunks."""
        chunk_id = str(uuid.uuid4())
        total_chunks = (len(raw_json) + CHUNK_SIZE - 1) // CHUNK_SIZE
        
        logger.info(f"[Kernel] Chunking large message: type={message_type}, size={len(raw_json)}, chunks={total_chunks}")
        
        async with self._socket_lock:
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
                    "original_type": message_type,
                    "request_id": request_id
                }
                await self.websocket.send(json_dumps(chunk_message))
        
        logger.debug(f"[Kernel] Sent {total_chunks} chunks for message: type={message_type}, chunk_id={chunk_id}")
    
    async def _handle_chunk_message(self, message: dict) -> Optional[dict]:
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
            logger.error("[Kernel] Invalid chunk message: missing required fields")
            return None
        
        if not isinstance(chunk_index, int) or not isinstance(total_chunks, int):
            logger.error("[Kernel] Invalid chunk message: chunk_index and total_chunks must be integers")
            return None
        
        if chunk_index < 0 or chunk_index >= total_chunks:
            logger.error(f"[Kernel] Invalid chunk_index {chunk_index} for total_chunks {total_chunks}")
            return None
        
        # Initialize buffer for this chunk_id if needed
        if chunk_id not in self._chunk_buffers:
            self._chunk_buffers[chunk_id] = {
                "chunks": [None] * total_chunks,
                "received": 0,
                "total": total_chunks
            }
        
        buffer = self._chunk_buffers[chunk_id]
        
        # Store the chunk
        if buffer["chunks"][chunk_index] is None:
            buffer["chunks"][chunk_index] = chunk_data
            buffer["received"] += 1
        
        # Check if all chunks received
        if buffer["received"] == buffer["total"]:
            # Verify all chunks are present (prevent None in join)
            if any(chunk is None for chunk in buffer["chunks"]):
                logger.error(f"[Kernel] Incomplete chunk buffer for chunk_id {chunk_id}")
                del self._chunk_buffers[chunk_id]
                return None
            
            # Reassemble the message
            full_json = "".join(buffer["chunks"])
            del self._chunk_buffers[chunk_id]
            
            try:
                reassembled = json.loads(full_json)
                # Prevent recursive chunk nesting - if reassembled message is also a chunk, reject it
                if isinstance(reassembled, dict) and reassembled.get("type") == "chunk":
                    logger.error(f"[Kernel] Nested chunk message detected for chunk_id {chunk_id}, rejecting")
                    return None
                return reassembled
            except json.JSONDecodeError as e:
                logger.error(f"[Kernel] Failed to parse reassembled message: {e}")
                return None
        
        return None

    async def _execute_code_async(self, code: str, request_id: Optional[str], function_name: Optional[str] = None, source: str = "ide"):
        """
        Execute code in a worker thread.

        This method dispatches code execution to the thread pool and sends results back.
        It runs as an async task so the listener thread can continue processing messages
        (like sys_response) while code execution is in progress.

        Args:
            code: The Python code to execute.
            request_id: The request ID for correlating results.
            function_name: Optional function name being executed (for result messages).
            source: Execution source ("ide" or "addin", default: "ide")
        """
        start_time = time.time()
        logger.debug(f"[TIMING] Execution started: request_id={request_id}, function={function_name}")
        
        try:
            logger.debug(f"[Kernel] [Async Task] Submitting execution to worker thread pool (request_id={request_id})")
            loop = asyncio.get_running_loop()

            # Create real-time streaming callbacks that use asyncio.run_coroutine_threadsafe
            # to send stdout/stderr messages immediately from the worker thread
            def stdout_callback(text: str):
                """Stream stdout in real-time from worker thread."""
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.send_message({
                            "type": "stdout",
                            "content": text,
                            "request_id": request_id,
                            "workbook_id": self.workbook_id,
                            "source": source,
                        }),
                        loop
                    )
                except Exception as e:
                    # Don't let streaming errors affect code execution
                    logger.debug(f"[Kernel] stdout streaming error: {e}")

            def stderr_callback(text: str):
                """Stream stderr in real-time from worker thread."""
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.send_message({
                            "type": "stderr",
                            "content": text,
                            "request_id": request_id,
                            "workbook_id": self.workbook_id,
                            "source": source,
                        }),
                        loop
                    )
                except Exception as e:
                    # Don't let streaming errors affect code execution
                    logger.debug(f"[Kernel] stderr streaming error: {e}")

            # Execute with real-time streaming callbacks in worker thread
            def execute_with_callbacks():
                thread_name = threading.current_thread().name
                logger.debug(f"[Kernel] [Worker Thread {thread_name}] Executing code (request_id={request_id})")
                result = self.executor.execute(
                    code,
                    stdout_callback=stdout_callback,
                    stderr_callback=stderr_callback,
                )
                logger.debug(f"[Kernel] [Worker Thread {thread_name}] Execution completed (request_id={request_id})")
                return result

            result = await loop.run_in_executor(
                self._thread_pool, execute_with_callbacks
            )
            
            elapsed_ms = (time.time() - start_time) * 1000
            logger.debug(f"[TIMING] Execution completed: request_id={request_id}, elapsed={elapsed_ms:.1f}ms")
            logger.debug(f"[Kernel] [Async Task] Execution finished, success={result['success']} (request_id={request_id})")

            # Note: stdout and stderr have already been streamed in real-time
            # via the callbacks, so we don't need to send them again here.
            # The result dict still contains the full output for logging purposes.

            # Send result or error
            if result["success"]:
                logger.info(f"[Kernel] Sending execution_result (success) for request_id={request_id}")
                
                # If there's a return value, print it to the console with a distinct prefix
                if result["result"] is not None:
                    result_repr = repr(result["result"])
                    # Send as a special result_output message for distinct console coloring
                    await self.send_message({
                        "type": "result_output",
                        "content": f"Out: {result_repr}\n",
                        "request_id": request_id,
                        "workbook_id": self.workbook_id,
                        "source": source,
                    })
                
                # Serialize the result using Serializer.to_wire for UDF execution
                # For UDF calls (identified by function_name), the result is already
                # serialized in the generated script, so just pass it through.
                # For IDE executions, we use repr for backward compatibility.
                if function_name:
                    # UDF execution - result is already serialized in the script
                    serialized_result = result["result"]
                else:
                    # IDE execution - use repr for backward compatibility
                    serialized_result = repr(result["result"]) if result["result"] is not None else None
                
                await self.send_message(
                    {
                        "type": "execution_result",
                        "success": True,
                        "result": serialized_result,
                        "request_id": request_id,
                        "function_name": function_name,
                        "workbook_id": self.workbook_id,
                        "source": source,
                    }
                )
            else:
                logger.info(f"[Kernel] Sending execution_error for request_id={request_id}: {result['error']}")
                await self.send_message(
                    {
                        "type": "execution_error",
                        "success": False,
                        "error": result["error"],
                        "request_id": request_id,
                        "function_name": function_name,
                        "workbook_id": self.workbook_id,
                        "source": source,
                    }
                )
        except Exception as e:
            # Handle any unexpected errors in the execution task
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"[TIMING] Execution failed: request_id={request_id}, elapsed={elapsed_ms:.1f}ms, error={e}")
            logger.error(f"[Kernel] Unexpected error in _execute_code_async: {e}")
            try:
                await self.send_message(
                    {
                        "type": "execution_error",
                        "success": False,
                        "error": {
                            "type": type(e).__name__,
                            "message": str(e),
                            "traceback": extract_tracebak_string(e),# traceback.format_exc(),
                        },
                        "request_id": request_id,
                        "source": source,
                    }
                )
            except Exception as send_error:
                logger.error(f"[Kernel] Failed to send error message: {send_error}")

    async def handle_message(self, message: dict):
        """
        Handle incoming messages from the Business Layer.
        
        This method runs in the Socket Listener thread (main async event loop).
        It dispatches execution requests to worker threads and handles
        sys_response messages immediately to unblock waiting workers.
        """
        message_type = message.get("type")
        request_id = message.get("request_id", "N/A")
        
        # Handle chunk messages first
        if message_type == "chunk":
            reassembled = await self._handle_chunk_message(message)
            if reassembled:
                # Process the reassembled message by calling handle_message recursively
                await self.handle_message(reassembled)
            return  # Don't process chunk messages further
        
        logger.debug(f"[TIMING] Message received: type={message_type}, request_id={request_id}")
        logger.debug(f"[Kernel] [Listener Thread] Received message type: {message_type}")

        if message_type == "execution_request":
            code = message.get("code", "")
            request_id = message.get("request_id")
            function_name = message.get("function_name")
            source = message.get("source", "ide")  # Default to "ide" for backwards compatibility
            logger.info(f"[Kernel] [Listener Thread] Received execution_request (source={source}, request_id={request_id})")
            logger.debug(f"[Kernel] Code length: {len(code)} chars")

            # Dispatch to worker thread pool via async task
            # The listener thread continues processing messages immediately
            asyncio.create_task(self._execute_code_async(code, request_id, function_name, source))

        elif message_type == "add_path":
            path = message.get("path", "")
            self.virtual_env.add_path(path)
            await self.send_message(
                {"type": "path_added", "path": path, "current_paths": sys.path}
            )

        elif message_type == "remove_path":
            path = message.get("path", "")
            self.virtual_env.remove_path(path)
            await self.send_message(
                {"type": "path_removed", "path": path, "current_paths": sys.path}
            )

        elif message_type == "reset_namespace":
            self.executor.reset_namespace()
            await self.send_message({"type": "namespace_reset"})

        elif message_type == "reset_path":
            self.virtual_env.reset_path()
            await self.send_message(
                {"type": "path_reset", "current_paths": sys.path}
            )
        
        elif message_type == "set_package_paths":
            # Handle package path replacement with proper cleanup (Phase 2)
            old_paths = message.get("old_paths", [])
            new_paths = message.get("new_paths", [])
            
            # Step 1: Find all modules loaded from old paths
            modules_from_old_paths = []
            for module_name, module in list(sys.modules.items()):
                if hasattr(module, '__file__') and module.__file__ is not None:
                    for old_path in old_paths:
                        if module.__file__.startswith(old_path):
                            modules_from_old_paths.append(module_name)
                            break
            
            # Step 2: Extract base package names (e.g., "numpy" from "numpy.core.multiarray")
            base_packages = set()
            for module_name in modules_from_old_paths:
                # Get the top-level package name
                base_package = module_name.split('.')[0]
                base_packages.add(base_package)
            
            # Step 3: Find ALL modules that start with those base names (all submodules)
            # Optimized: Check each module once against the base_packages set
            modules_to_remove = []
            for module_name in list(sys.modules.keys()):
                # Check if module is in base_packages or is a submodule of any base package
                base_package = module_name.split('.')[0]
                if base_package in base_packages:
                    modules_to_remove.append(module_name)
            
            # Step 4: Sort by depth (deepest first) to remove submodules before parents
            # This prevents issues where a parent module might try to access a deleted submodule
            modules_to_remove.sort(key=lambda x: x.count('.'), reverse=True)
            
            # Step 5: Remove modules
            for module_name in modules_to_remove:
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    logger.debug(f"Unloaded module: {module_name}")
            
            # Remove old paths from sys.path
            for old_path in old_paths:
                if old_path in sys.path:
                    sys.path.remove(old_path)
                    logger.debug(f"Removed old path from sys.path: {old_path}")
            
            # Add new paths to sys.path (at position 0 for priority)
            for path in reversed(new_paths):
                if path not in sys.path:
                    sys.path.insert(0, path)
                    logger.debug(f"Added new path to sys.path: {path}")
            
            # Update tracking
            self.virtual_env.custom_paths = new_paths.copy()
            
            # Update LSP Bridge with new sys.path for import resolution
            # Always update LSP, even if new_paths is empty (to handle removals)
            if self._lsp_bridge:
                self._lsp_bridge.update_sys_paths(new_paths)
            
            await self.send_message({
                "type": "package_paths_updated",
                "paths_added": len(new_paths),
                "modules_unloaded": len(modules_to_remove),
                "workbook_id": self.workbook_id
            })
            logger.info(f"Package paths updated: {len(new_paths)} paths added, {len(modules_to_remove)} modules unloaded")
        
        elif message_type == "set_python_paths":
            # Handle user-added python paths (no module cleanup needed)
            old_paths = message.get("old_paths", [])
            new_paths = message.get("new_paths", [])
            
            # Remove old paths from sys.path
            for old_path in old_paths:
                if old_path in sys.path:
                    sys.path.remove(old_path)
                    logger.debug(f"Removed old python path from sys.path: {old_path}")
            
            # Add new paths to sys.path (at the end, after package paths)
            for path in new_paths:
                if path not in sys.path:
                    sys.path.append(path)
                    logger.debug(f"Added new python path to sys.path: {path}")
            
            # Update LSP Bridge with updated sys.path
            if self._lsp_bridge:
                # Get all current sys.path for LSP
                self._lsp_bridge.update_sys_paths(sys.path.copy())
            
            await self.send_message({
                "type": "python_paths_updated",
                "paths_added": len(new_paths),
                "workbook_id": self.workbook_id
            })
            logger.info(f"Python paths updated: {len(new_paths)} paths added")
        
        elif message_type == "unload_and_clear_paths":
            # Handle unload request for given paths
            paths = message.get("paths", [])
            
            # Step 1: Find all modules loaded from given paths
            modules_from_paths = []
            for module_name, module in list(sys.modules.items()):
                if hasattr(module, '__file__') and module.__file__ is not None:
                    for path in paths:
                        if module.__file__.startswith(path):
                            modules_from_paths.append(module_name)
                            break
            
            # Step 2: Extract base package names (e.g., "numpy" from "numpy.core.multiarray")
            base_packages = set()
            for module_name in modules_from_paths:
                # Get the top-level package name
                base_package = module_name.split('.')[0]
                base_packages.add(base_package)
            
            # Step 3: Find ALL modules that start with those base names (all submodules)
            modules_to_remove = []
            for module_name in list(sys.modules.keys()):
                # Check if module is in base_packages or is a submodule of any base package
                base_package = module_name.split('.')[0]
                if base_package in base_packages:
                    modules_to_remove.append(module_name)
            
            # Step 4: Sort by depth (deepest first) to remove submodules before parents
            modules_to_remove.sort(key=lambda x: x.count('.'), reverse=True)
            
            # Step 5: Remove modules
            for module_name in modules_to_remove:
                if module_name in sys.modules:
                    del sys.modules[module_name]
                    logger.debug(f"Unloaded module: {module_name}")
            
            # Step 6: Remove paths from sys.path
            for path in paths:
                if path in sys.path:
                    sys.path.remove(path)
                    logger.debug(f"Removed path from sys.path: {path}")
            
            await self.send_message({
                "type": "modules_unloaded",
                "modules_unloaded": len(modules_to_remove),
                "paths_cleared": len(paths),
                "workbook_id": self.workbook_id
            })
            logger.info(f"Modules unloaded: {len(modules_to_remove)}, paths cleared: {len(paths)}")

        elif message_type == "update_module":
            # Handle virtual module updates
            module_name = message.get("module_name", "")
            code = message.get("code", "")
            if module_name:
                in_memory_loader.update_module(module_name, code)
                logger.info(f"[Kernel] Updated virtual module: {module_name}")
                await self.send_message(
                    {"type": "module_updated", "module_name": module_name}
                )
            else:
                logger.warning("[Kernel] Received update_module without module_name")
                await self.send_message(
                    {"type": "error", "message": "update_module requires module_name"}
                )

        elif message_type == "delete_module":
            # Handle virtual module deletion
            module_name = message.get("module_name", "")
            if module_name:
                in_memory_loader.delete_module(module_name)
                
                # Also delete from LSP temp directory
                if self._lsp_bridge:
                    self._lsp_bridge.delete_module(module_name)
                
                logger.info(f"[Kernel] Deleted virtual module: {module_name}")
                await self.send_message(
                    {"type": "module_deleted", "module_name": module_name}
                )
            else:
                logger.warning("[Kernel] Received delete_module without module_name")
                await self.send_message(
                    {"type": "error", "message": "delete_module requires module_name"}
                )

        elif message_type == "completion_request":
            # Handle autocompletion requests using LSPBridge
            await self._handle_completion_request(message)

        elif message_type == "signature_help_request":
            # Handle signature help requests using LSPBridge
            await self._handle_signature_help_request(message)

        elif message_type == "hover_request":
            # Handle hover requests using LSPBridge
            await self._handle_hover_request(message)

        elif message_type == "diagnostic_request":
            # Handle diagnostic requests using LSPBridge
            await self._handle_diagnostic_request(message)

        elif message_type == "shutdown":
            await self.disconnect()

        elif message_type == "custom_function_call":
            # Dispatch custom function call to worker thread pool
            # The listener thread continues processing messages immediately
            logger.info(f"[Kernel] [Listener Thread] Dispatching custom_function_call to worker")
            asyncio.create_task(self._handle_custom_function_call(message))

        elif message_type == "run_module":
            # Dispatch run_module to worker thread pool (unified with custom_function_call)
            # The listener thread continues processing messages immediately
            logger.info(f"[Kernel] [Listener Thread] Dispatching run_module to worker")
            asyncio.create_task(self._handle_run_module(message))

        elif message_type == "event_execution":
            # Dispatch event execution to worker thread pool
            # The listener thread continues processing messages immediately
            logger.info(f"[Kernel] [Listener Thread] Dispatching event_execution to worker")
            asyncio.create_task(self._handle_event_execution(message))

        elif message_type == "python_function_call":
            # Handle Python callable invocation from Excel
            # Dispatch to worker thread pool for execution
            logger.info(f"[Kernel] [Listener Thread] Dispatching python_function_call to worker")
            asyncio.create_task(self._handle_python_function_call(message))

        elif message_type == "execute_streaming_function":
            # Dispatch to background task - DO NOT await directly
            logger.debug(f"[TIMING] Dispatching streaming function to background task")
            logger.info(f"[Kernel] [Listener Thread] Dispatching execute_streaming_function to background task")
            asyncio.create_task(self._execute_streaming_function(
                message.get("request_id"),
                message.get("module_name"),
                message.get("function_name"),
                message.get("args", []),
                message.get("workbook_id",""),
                message.get("source", "addin"),
            ))
            # Return immediately so event loop can process other messages
            return

        elif message_type == "cancel_streaming_function":
            # Handle streaming function cancellation
            request_id = message.get("request_id")
            logger.info(f"[Kernel] Received cancel_streaming_function for request_id: {request_id}")
            self._canceled_streaming_requests.add(request_id)

        elif message_type == "debug_continue":
            # Continue execution from debug pause
            if self.has_active_debugger:
                self._debugger.continue_execution()
                await self.send_message({"type": "debug_resumed"})

        elif message_type == "debug_step_over":
            # Step over to next line
            if self.has_active_debugger:
                self._debugger.step_over()

        elif message_type == "debug_step_into":
            # Step into function call
            if self.has_active_debugger:
                self._debugger.step_into()

        elif message_type == "debug_step_out":
            # Step out of current function
            if self.has_active_debugger:
                self._debugger.step_out()

        elif message_type == "debug_stop":
            # Stop debugging session
            if self.has_active_debugger:
                self._debugger.stop_debugging()
                await self.send_message({
                    "type": "debug_terminated",
                    "workbook_id": self.workbook_id,
                })
                self._debugger = None

        elif message_type == "debug_evaluate":
            # Evaluate expression in debug context
            expression = message.get("expression", "")
            request_id = message.get("request_id")
            if self.has_active_debugger:
                result = self._debugger.evaluate_expression(expression)
                await self.send_message({
                    "type": "debug_evaluate_result",
                    "workbook_id": self.workbook_id,
                    "request_id": request_id,
                    "expression": expression,
                    **result
                })
            else:
                await self.send_message({
                    "type": "debug_evaluate_result",
                    "workbook_id": self.workbook_id,
                    "request_id": request_id,
                    "expression": expression,
                    "error": "No active debug session"
                })

        elif message_type == "debug_update_breakpoints":
            # Update breakpoints during an active debug session
            breakpoints = message.get("breakpoints", [])
            if self.has_active_debugger:
                if isinstance(breakpoints, list):
                    self._debugger.set_breakpoints(breakpoints)
                    logger.info(f"[Kernel] Updated breakpoints during debug session: {len(breakpoints)} breakpoints")
                else:
                    logger.warning(f"[Kernel] Invalid breakpoints data type: {type(breakpoints)}")
            else:
                logger.warning("[Kernel] Received debug_update_breakpoints but no active debugger")

        elif message_type == "sys_response":
            # Handle sys_response from the Add-in (via Business Layer)
            # CRITICAL: This runs immediately in the listener thread to unblock
            # worker threads that are waiting on sys_request calls
            # This resolves the pending event for synchronous sys_request calls
            #
            # Threading Note: This handler runs in the listener thread and must
            # quickly set the event to unblock the waiting worker thread.
            # The _response_lock ensures thread-safe access to the response data.
            payload = message.get("payload")
            if not payload:
                # If payload is missing or empty, the message itself is the payload
                payload = message
            
            request_id = payload.get("requestId")
            logger.debug(f"[Kernel] [Listener Thread] Received sys_response for request_id: {request_id}, unblocking worker")
            
            if request_id:
                with self._response_lock:
                    # Store the response data
                    self._response_data[request_id] = payload
                    # Signal the waiting worker thread immediately
                    # Threading Note: event.set() is thread-safe and will wake up
                    # the worker thread blocked in event.wait()
                    event = self._response_futures.get(request_id)
                    if event:
                        event.set()
                        logger.debug(f"[Kernel] [Listener Thread] Worker unblocked for request_id: {request_id}")
                    else:
                        logger.warning(f"[Kernel] Received sys_response for unknown request_id: {request_id}")
            else:
                logger.warning("[Kernel] Received sys_response without requestId")

        elif message_type == "get_object_registry":
            # Handle request for the full object registry
            logger.debug("[Kernel] Received get_object_registry request")
            registry = self.get_object_registry()
            await self.send_message({
                "type": "object_registry_response",
                "objects": registry,
                "workbook_id": self.workbook_id,
            })
        
        elif message_type == "set_hover_mode":
            # Handle hover mode change from IDE
            mode = message.get("mode", "compact")
            logger.debug(f"[Kernel] Received set_hover_mode: {mode}")
            if self._lsp_bridge:
                self._lsp_bridge.set_hover_mode(mode)
                await self.send_message({
                    "type": "hover_mode_updated",
                    "mode": mode,
                    "workbook_id": self.workbook_id,
                })
            else:
                logger.warning("[Kernel] LSP Bridge not available for hover mode change")

    async def _handle_completion_request(self, message: dict):
        """
        Handle autocompletion requests using LSPBridge.

        Args:
            message: The completion request message containing:
                - code: Source text
                - line: 1-based line number
                - column: 0-based column number
                - path: Optional file path for context
                - request_id: Optional request ID for correlation
                - workbook_id: Optional workbook ID for routing response
                - module_name: Optional module name for routing response
                - dirty_files: Optional dict of {module_name: content} for unsaved files
        """
        request_id = message.get("request_id")
        code = message.get("code", "")
        line = message.get("line", 1)
        column = message.get("column", 0)
        path = message.get("path")
        workbook_id = message.get("workbook_id")
        module_name = message.get("module_name")
        dirty_files = message.get("dirty_files")
        dirty_files_count = len(dirty_files) if dirty_files else 0

        # Log the incoming request
        logger.debug(
            f"[LSP] Request received: line={line}, column={column}, "
            f"path={path}, code_length={len(code)}, dirty_files={dirty_files_count}"
        )

        # Retrieve all modules from in-memory loader for cross-module completion
        modules = in_memory_loader.source_cache.copy()

        # Use LSPBridge for completions with synced modules and dirty files
        result = self._lsp_bridge.get_completions(
            code=code,
            line=line,
            column=column,
            path=path,
            modules=modules,
            dirty_files=dirty_files
        )

        # Log the response
        completions = result.get("completions", [])
        error = result.get("error")
        logger.debug(
            f"[LSP] Response: {len(completions)} completions, error={error}"
        )

        # Send response with workbook_id and module_name for routing
        await self.send_message({
            "type": "completion_response",
            "completions": completions,
            "error": error,
            "request_id": request_id,
            "workbook_id": workbook_id,
            "module_name": module_name,
        })

    async def _handle_signature_help_request(self, message: dict):
        """
        Handle signature help requests using LSPBridge.

        Args:
            message: The signature help request message containing:
                - code: Source text
                - line: 1-based line number
                - column: 0-based column number
                - path: Optional file path for context
                - request_id: Optional request ID for correlation
                - workbook_id: Optional workbook ID for routing response
                - module_name: Optional module name for routing response
                - dirty_files: Optional dict of {module_name: content} for unsaved files
        """
        request_id = message.get("request_id")
        code = message.get("code", "")
        line = message.get("line", 1)
        column = message.get("column", 0)
        path = message.get("path")
        workbook_id = message.get("workbook_id")
        module_name = message.get("module_name")
        dirty_files = message.get("dirty_files")

        # Log the incoming request
        logger.debug(
            f"[LSP] Signature help request: line={line}, column={column}, "
            f"path={path}, code_length={len(code)}"
        )

        # Retrieve all modules from in-memory loader for cross-module resolution
        modules = in_memory_loader.source_cache.copy()

        # Use LSPBridge for signature help
        result = self._lsp_bridge.get_signature_help(
            code=code,
            line=line,
            column=column,
            path=path,
            modules=modules,
            dirty_files=dirty_files
        )

        # Log the response
        signatures = result.get("signatures", [])
        error = result.get("error")
        logger.debug(
            f"[LSP] Signature help response: {len(signatures)} signatures, error={error}"
        )

        # Send response with workbook_id and module_name for routing
        await self.send_message({
            "type": "signature_help_response",
            "signatures": result.get("signatures", []),
            "activeSignature": result.get("activeSignature", 0),
            "activeParameter": result.get("activeParameter", 0),
            "error": error,
            "request_id": request_id,
            "workbook_id": workbook_id,
            "module_name": module_name,
        })

    async def _handle_hover_request(self, message: dict):
        """
        Handle hover requests using LSPBridge.

        Args:
            message: The hover request message containing:
                - code: Source text
                - line: 1-based line number
                - column: 0-based column number
                - path: Optional file path for context
                - request_id: Optional request ID for correlation
                - workbook_id: Optional workbook ID for routing response
                - module_name: Optional module name for routing response
                - dirty_files: Optional dict of {module_name: content} for unsaved files
        """
        request_id = message.get("request_id")
        code = message.get("code", "")
        line = message.get("line", 1)
        column = message.get("column", 0)
        path = message.get("path")
        workbook_id = message.get("workbook_id")
        module_name = message.get("module_name")
        dirty_files = message.get("dirty_files")

        # Log the incoming request
        logger.debug(
            f"[LSP] Hover request: line={line}, column={column}, "
            f"path={path}, code_length={len(code)}"
        )

        # Retrieve all modules from in-memory loader for cross-module resolution
        modules = in_memory_loader.source_cache.copy()

        # Use LSPBridge for hover
        result = self._lsp_bridge.get_hover(
            code=code,
            line=line,
            column=column,
            path=path,
            modules=modules,
            dirty_files=dirty_files
        )

        # Log the response
        contents = result.get("contents")
        error = result.get("error")
        logger.debug(
            f"[LSP] Hover response: has_contents={contents is not None}, error={error}"
        )

        # Send response with workbook_id and module_name for routing
        await self.send_message({
            "type": "hover_response",
            "contents": contents,
            "error": error,
            "request_id": request_id,
            "workbook_id": workbook_id,
            "module_name": module_name,
        })

    async def _handle_diagnostic_request(self, message: dict):
        """
        Handle diagnostic requests using LSPBridge.

        Args:
            message: The diagnostic request message containing:
                - code: Source text
                - request_id: Optional request ID for correlation
                - workbook_id: Optional workbook ID for routing response
                - module_name: Optional module name for routing response
        """
        request_id = message.get("request_id")
        code = message.get("code", "")
        workbook_id = message.get("workbook_id")
        module_name = message.get("module_name")

        # Log the incoming request
        logger.debug(
            f"[LSP] Diagnostic request: code_length={len(code)}, module={module_name}"
        )

        # Use LSPBridge for diagnostics with module name for better error context
        result = self._lsp_bridge.get_diagnostics(code=code, module_name=module_name)

        # Log the response
        diagnostics = result.get("diagnostics", [])
        error = result.get("error")
        logger.debug(
            f"[LSP] Diagnostic response: {len(diagnostics)} diagnostics, error={error}"
        )

        # Send response with workbook_id and module_name for routing
        await self.send_message({
            "type": "diagnostic_response",
            "diagnostics": diagnostics,
            "error": error,
            "request_id": request_id,
            "workbook_id": workbook_id,
            "module_name": module_name,
        })

    async def _handle_custom_function_call(self, message: dict):
        """
        Handle custom function call requests from the Business Layer.

        This method implements the new execution model where module_name and function_name
        are provided separately. It:
        1. Retrieves the module using sys.modules[module_name]
        2. Retrieves the function using getattr(module, function_name)
        3. Deserializes all arguments using Serializer.from_wire
        4. Executes the function
        5. Serializes the result using Serializer.to_wire
        6. Returns the serialized result

        Args:
            message: The custom_function_call message containing:
                - module_name: The module name (e.g., "my_module")
                - function_name: The function name (e.g., "my_function")
                - args: List of wire-format arguments
                - request_id: Unique request identifier
                - workbook_id: The workbook ID
                - source: Execution source ("ide" or "addin", default: "addin")
        """
        module_name = message.get("module_name", "")
        function_name = message.get("function_name", "")
        args = message.get("args", [])
        request_id = message.get("request_id")
        workbook_id = message.get("workbook_id")
        source = message.get("source", "addin")  # Default to "addin" for UDF calls

        logger.info(
            f"[Kernel] Received custom_function_call: {module_name}.{function_name} "
            f"(source={source}, request_id={request_id})"
        )

        async def send_error(error_type: str, error_message: str, traceback_str: str = ""):
            """
            Send an error message back to the Business Layer.
            
            Args:
                error_type: The error type (e.g., "ValidationError", "ImportError")
                error_message: The error message
                traceback_str: Optional traceback string
                
            Note: Sends both execution_error (for general logging) and function_execution_result
            (for UDF compatibility) to ensure all clients receive the error notification.
            """
            error_dict = {
                "type": error_type,
                "message": error_message,
                "traceback": traceback_str,
            }
            
            # Send execution_error
            await self.send_message({
                "type": "execution_error",
                "success": False,
                "error": error_dict,
                "request_id": request_id,
                "module_name": module_name,
                "function_name": function_name,
                "workbook_id": workbook_id,
                "source": source,
            })
            
            # Also send function_execution_result for UDF compatibility
            await self.send_message({
                "type": "function_execution_result",
                "request_id": request_id,
                "status": "error",
                "error": error_dict,
            })

        if not module_name:
            await send_error("ValidationError", "Missing module_name")
            return

        if not function_name:
            await send_error("ValidationError", "Missing function_name")
            return

        try:
            # Dispatch execution to worker thread pool
            logger.debug(f"[Kernel] [Async Task] Dispatching custom_function_call to worker: {module_name}.{function_name}")
            loop = asyncio.get_running_loop()
            
            def execute_function():
                """Execute the function in a worker thread with stdout/stderr capture."""
                thread_name = threading.current_thread().name
                logger.debug(f"[Kernel] [Worker Thread {thread_name}] Executing custom function: {module_name}.{function_name}")
                
                # Create stdout/stderr callbacks that send messages in real-time
                def stdout_callback(text: str):
                    """Stream stdout in real-time from worker thread."""
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.send_message({
                                "type": "stdout",
                                "content": text,
                                "request_id": request_id,
                                "workbook_id": workbook_id,
                                "source": source,
                            }),
                            loop
                        )
                    except Exception as e:
                        logger.debug(f"[Kernel] stdout streaming error: {e}")

                def stderr_callback(text: str):
                    """Stream stderr in real-time from worker thread."""
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.send_message({
                                "type": "stderr",
                                "content": text,
                                "request_id": request_id,
                                "workbook_id": workbook_id,
                                "source": source,
                            }),
                            loop
                        )
                    except Exception as e:
                        logger.debug(f"[Kernel] stderr streaming error: {e}")
                
                # Create StreamCapture instances with callbacks
                stdout_capture = StreamCapture(on_write=stdout_callback)
                stderr_capture = StreamCapture(on_write=stderr_callback)
                
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    try:

                        # DON'T REMOVE: To ensure module lazy-load
                        # DON'T TRY to use importlib instead of excec
                        exec(f"import {module_name}")  # Ensure module is imported}
                        """
                        try:
                            exec(f"import {module_name}")  # Ensure module is imported}
                        except Exception as egui:
                            pass  # Ignore import errors here; will check sys.modules next
                        """
                        
                        # 1. Retrieve the module from sys.modules
                        if module_name not in sys.modules:
                            raise ImportError(f"Module '{module_name}' not found in sys.modules. "
                                            f"Make sure the module has been synced via update_module.")
                        
                        module = sys.modules[module_name]
                        
                        # 2. Retrieve the function using getattr
                        if not hasattr(module, function_name):
                            raise AttributeError(f"Function '{function_name}' not found in module '{module_name}'")
                        
                        func = getattr(module, function_name)
                        
                        # 3. Deserialize all arguments using Serializer.from_wire
                        deserialized_args = self._deserialize_args(args)
                        
                        # 4. Execute the function
                        try:
                            result = func(*deserialized_args)
                            
                            # Check if result is a generator using inspect.isgenerator()
                            if inspect.isgenerator(result):
                                # This is a generator - handle streaming by collecting all yielded values
                                # Note: All values are collected into memory before returning.
                                # For large generators, this may impact memory usage.
                                # Future enhancement: implement incremental streaming.
                                results = []
                                try:
                                    for item in result:
                                        # Serialize and store each yielded item
                                        serialized_item = xpycode.Serializer.to_wire(item)
                                        results.append(serialized_item)
                                except Exception as iteration_error:
                                    #traceback.print_exc(file=sys.stderr)
                                    raise iteration_error
                                
                                # For now, return all results as an array
                                # The streaming flag in metadata will indicate this is a streaming function
                                serialized_result = results
                            else:
                                # Regular function - serialize single result
                                serialized_result = xpycode.Serializer.to_wire(result)
                        except Exception as e:
                            #traceback.print_exc(file=sys.stderr)
                            raise e
                    
                    
                    except Exception as e:
                        # Get captured logs even on error
                        traceback.print_exc(file=sys.stderr)
                        logs = stdout_capture.getvalue() + stderr_capture.getvalue()

                        return {
                                "status": "error",
                                "result": None,
                                "logs": "",
                                "error": extract_tracebak_string(e),# traceback.format_exc()
                            }
    
                    
                    finally:
                        # Get captured logs
                        logs = stdout_capture.getvalue() + stderr_capture.getvalue()
                    
                return {
                    "status": "success",
                    "result": serialized_result,
                    "base_result": result,
                    "logs": logs
                }



            
            # Execute in thread pool
            result_dict = await loop.run_in_executor(self._thread_pool, execute_function)
            
            # Log any captured output
            if result_dict.get("logs"):
                logger.info(f"[Kernel] Function logs:\n{result_dict['logs']}")
            
            if result_dict["status"] == "success":
                # Send result_output for IDE console display
                if result_dict["result"] is not None:
                    result_repr = repr(result_dict["base_result"])
                    await self.send_message({
                        "type": "result_output",
                        "content": f"Out: {result_repr}\n",
                        "request_id": request_id,
                        "workbook_id": workbook_id,
                        "source": source,
                    })
                
                # Send execution_result
                await self.send_message({
                    "type": "execution_result",
                    "success": True,
                    "result": result_dict["result"],
                    "logs": result_dict.get("logs", ""),
                    "request_id": request_id,
                    "module_name": module_name,
                    "function_name": function_name,
                    "workbook_id": workbook_id,
                    "source": source,
                })
                
                # Also send function_execution_result for UDF compatibility
                await self.send_message({
                    "type": "function_execution_result",
                    "request_id": request_id,
                    "status": "success",
                    "result": result_dict["result"],
                    "logs": result_dict.get("logs", ""),
                })
                
                logger.info(f"[Kernel] Custom function call succeeded: {module_name}.{function_name}")
            else:
                # Send error with structured response
                error_msg = result_dict.get("error", "Unknown error")
                
                # Send execution_error
                await self.send_message({
                    "type": "execution_error",
                    "success": False,
                    "error": error_msg,
                    "logs": result_dict.get("logs", ""),
                    "request_id": request_id,
                    "module_name": module_name,
                    "function_name": function_name,
                    "workbook_id": workbook_id,
                    "source": source,
                })
                
                # Also send function_execution_result for UDF compatibility
                await self.send_message({
                    "type": "function_execution_result",
                    "request_id": request_id,
                    "status": "error",
                    "result": None,
                    "logs": result_dict.get("logs", ""),
                    "error": error_msg,
                })
                
                logger.error(f"[Kernel] Custom function call failed: {module_name}.{function_name}")
                
        except Exception as e:
            # Handle any unexpected errors
            logger.error(f"[Kernel] Unexpected error in _handle_custom_function_call: {e}")
            await send_error(type(e).__name__, str(e), extract_tracebak_string(e)) #traceback.format_exc())

    async def _handle_run_module(self, message: dict):
        """
        Handle run_module requests from the IDE.
        
        This method provides a unified execution path for IDE Run (F5) and Excel function calls.
        It uses the same execution logic as custom_function_call, with optional debug support.
        
        Args:
            message: The run_module message containing:
                - workbook_id: The workbook ID
                - module_name: The module name (e.g., "main")
                - function_name: The function name (e.g., "foo")
                - args: List of arguments (default: [])
                - debug: Whether to run in debug mode (default: false)
                - breakpoints: List of breakpoints (optional)
                - source: Execution source ("ide" or "addin", default: "ide")
        """
        workbook_id = message.get("workbook_id", "")
        module_name = message.get("module_name", "")
        function_name = message.get("function_name", "")
        args = message.get("args", [])
        debug = message.get("debug", False)
        breakpoints = message.get("breakpoints", [])
        request_id = message.get("request_id")
        source = message.get("source", "ide")  # Default to "ide" for backwards compatibility
        
        logger.info(
            f"[Kernel] Received run_module: {module_name}.{function_name} "
            f"(workbook_id={workbook_id}, debug={debug}, source={source}, request_id={request_id})"
        )
        
        # Phase 1: Integrate with debugger when debug=True
        if debug:
            await self._handle_debug_run_module(
                module_name, function_name, args, breakpoints, 
                request_id, workbook_id, source
            )
        else:
            # Regular execution - reuse custom_function_call logic
            await self._handle_custom_function_call({
                "type": "custom_function_call",
                "module_name": module_name,
                "function_name": function_name,
                "args": args,
                "request_id": request_id,
                "workbook_id": workbook_id,
                "source": source,
            })
    
    async def _handle_debug_run_module(self, module_name: str, function_name: str, 
                                       args: List, breakpoints: List, 
                                       request_id: Optional[str], workbook_id: str, source: str = "ide"):
        """
        Handle run_module in debug mode using the debugger.
        
        Args:
            module_name: Module name
            function_name: Function name
            args: Function arguments
            breakpoints: List of breakpoint dicts
            request_id: Request ID
            workbook_id: Workbook ID
            source: Execution source ("ide" or "addin", default: "ide")
        """
        try:
            # Create debugger instance
            self._debugger = XPyCodeDebugger(self.send_message, workbook_id)
            self._debugger.loop = asyncio.get_running_loop()
            
            # Set initial step mode to None into first user code line
            # Changing with 'into' will ensure the debugger pauses at the first line of the function being debugged
            self._debugger.step_mode = None
            
            # Set breakpoints
            self._debugger.set_breakpoints(breakpoints)
            
            # Pass in-memory modules to debugger
            in_memory_modules = list(in_memory_loader.source_cache.keys())
            self._debugger.set_in_memory_modules(in_memory_modules)
            
            # Dispatch to worker thread for debugging
            loop = asyncio.get_running_loop()
            
            def debug_execute():
                """Execute function under debugger in worker thread."""
                # Create stdout/stderr callbacks that send messages in real-time
                def stdout_callback(text: str):
                    """Stream stdout in real-time from worker thread."""
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.send_message({
                                "type": "stdout",
                                "content": text,
                                "request_id": request_id,
                                "workbook_id": workbook_id,
                                "source": source,
                            }),
                            loop
                        )
                    except Exception as e:
                        logger.debug(f"[Kernel] stdout streaming error: {e}")

                def stderr_callback(text: str):
                    """Stream stderr in real-time from worker thread."""
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.send_message({
                                "type": "stderr",
                                "content": text,
                                "request_id": request_id,
                                "workbook_id": workbook_id,
                                "source": source,
                            }),
                            loop
                        )
                    except Exception as e:
                        logger.debug(f"[Kernel] stderr streaming error: {e}")
                
                # Create StreamCapture instances with callbacks
                stdout_capture = StreamCapture(on_write=stdout_callback)
                stderr_capture = StreamCapture(on_write=stderr_callback)
                
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    try:
                        # Import the module
                        # SECURITY NOTE: module_name is validated in business_layer/server.py
                        # via validate_python_identifier() before reaching here
                        exec(f"import {module_name}")
                        
                        if module_name not in sys.modules:
                            raise ImportError(f"Module '{module_name}' not found")
                        
                        module = sys.modules[module_name]
                        
                        if not hasattr(module, function_name):
                            raise AttributeError(f"Function '{function_name}' not found in module '{module_name}'")
                        
                        func = getattr(module, function_name)
                        
                        # Deserialize arguments
                        deserialized_args = self._deserialize_args(args)
                        
                        # Run under debugger - this returns the result
                        result = self._debugger.runcall(func, *deserialized_args)
                        
                        # Check if result is a generator
                        if inspect.isgenerator(result):
                            
                            def iteration_to_debug():
                                # Iterate through generator to execute yield statements
                                # Note: The debugger is still active during this iteration,
                                # so users can step through yield statements and breakpoints
                                # in the generator function will be hit
                                yielded_values = []
                                yield_count = 0
                                for value in func(*deserialized_args):
                                    yield_count += 1
                                    yielded_values.append(value)
                                    
                                    # Send result_output for each yield (for IDE console)
                                    value_repr = repr(value)
                                    asyncio.run_coroutine_threadsafe(
                                        self.send_message({
                                            "type": "result_output",
                                            "content": f"Yield [{yield_count}]: {value_repr}\n",
                                            "request_id": request_id,
                                            "workbook_id": workbook_id,
                                            "source": source,
                                        }),
                                        loop
                                    )
                                return yielded_values, yield_count
                            iterator_result = self._debugger.runcall(iteration_to_debug)
                            if iterator_result:
                                yielded_values, yield_count=iterator_result
                            else:
                                yielded_values, yield_count=[],-1
                                
                            return {
                                "status": "success",
                                "result": yielded_values,
                                "is_generator": True,
                                "yield_count": yield_count
                            }
                        else:
                            # Regular function result
                            return {
                                "status": "success",
                                "result": result,
                                "is_generator": False
                            }
                        
                    except Exception as e:
                        logger.error(f"[Kernel] Debug execution error: {e}")
                        tb_str = extract_tracebak_string(e) #traceback.format_exc()
                        logger.error(f"[Kernel] Traceback: {tb_str}")
                        
                        # Parse traceback to find error location in user code
                        error_location = _parse_error_location(tb_str, in_memory_loader.source_cache.keys())
                        logger.info(f"[Kernel] Parsed error location: {error_location}")
                        
                        # Send debug_exception message to IDE and WAIT for it to be sent
                        debug_exception_sent = False
                        if self._debugger and self._debugger.loop:
                            logger.info(f"[Kernel] Sending debug_exception message...")
                            try:
                                future = asyncio.run_coroutine_threadsafe(
                                    self.send_message({
                                        "type": "debug_exception",
                                        "workbook_id": workbook_id,
                                        "module": error_location.get("module", module_name),
                                        "line": error_location.get("line", 1),
                                        "file": error_location.get("file", ""),
                                        "exception_type": type(e).__name__,
                                        "exception_message": str(e),
                                        "exception_traceback": tb_str,
                                        "locals": [],  # Can't get locals after exception propagated
                                        "globals": [],
                                        "call_stack": [],
                                    }),
                                    self._debugger.loop
                                )
                                # WAIT for the message to be sent (with timeout)
                                future.result(timeout=DEBUG_MESSAGE_SEND_TIMEOUT)
                                debug_exception_sent = True
                                logger.info(f"[Kernel] debug_exception message sent successfully")
                            except Exception as send_error:
                                logger.error(f"[Kernel] Failed to send debug_exception: {send_error}")
                        else:
                            logger.warning(f"[Kernel] Cannot send debug_exception - no debugger or loop")
                        
                        return {
                            "status": "error",
                            "type": type(e).__name__,
                            "message": str(e),
                            "traceback": tb_str,
                            "debug_exception_sent": debug_exception_sent
                        }
            
            # Execute in thread pool
            result = await loop.run_in_executor(self._thread_pool, debug_execute)
            
            # Send completion message
            if result["status"] == "success":
                # Send result_output for IDE console display
                if result.get("is_generator"):
                    # For generators, show summary
                    yield_count = result.get("yield_count", 0)
                    if yield_count>=0:
                        await self.send_message({
                            "type": "result_output",
                            "content": f"Out: Generator completed with {yield_count} yields\n",
                            "request_id": request_id,
                            "workbook_id": workbook_id,
                            "source": source,
                        })
                    else:
                        await self.send_message({
                            "type": "result_output",
                            "content": f"Out: Generator stoped before ending\n",
                            "request_id": request_id,
                            "workbook_id": workbook_id,
                            "source": source,
                        })
                elif "result" in result:
                    # For regular functions, show the result repr
                    result_repr = repr(result["result"])
                    await self.send_message({
                        "type": "result_output",
                        "content": f"Out: {result_repr}\n",
                        "request_id": request_id,
                        "workbook_id": workbook_id,
                        "source": source,
                    })
                
                logger.info("[Kernel] Debug execution completed successfully, sending debug_terminated")
                await self.send_message({
                    "type": "debug_terminated",
                    "request_id": request_id,
                    "workbook_id": workbook_id,
                })
            else:
                # Check if debug_exception was already sent
                if result.get("debug_exception_sent"):
                    logger.info("[Kernel] Debug exception already sent, sending debug_terminated")
                    # Just send debug_terminated, don't send execution_error (avoid duplicate)
                    
                    #In case of error the termination is managed by user
                    #No need for termination on kernell side
                    '''
                    await self.send_message({
                        "type": "debug_terminated",
                        "request_id": request_id,
                        "workbook_id": workbook_id,
                        "reason": "exception",
                    })
                    '''
                else:
                    # Fallback - send execution_error
                    logger.error(f"[Kernel] Debug execution failed: {result}")
                    await self.send_message({
                        "type": "execution_error",
                        "success": False,
                        "error": result,
                        "request_id": request_id,
                        "workbook_id": workbook_id,
                        "source": source,
                    })
            
            # Clean up debugger
            self._debugger = None
            logger.debug("[Kernel] Debugger instance cleaned up")
            
        except Exception as e:
            logger.error(f"[Kernel] Error in debug execution: {e}")
            logger.error(f"[Kernel] Traceback: {traceback.format_exc()}")
            await self.send_message({
                "type": "execution_error",
                "success": False,
                "error": {
                    "type": type(e).__name__, 
                    "message": str(e),
                    "traceback": extract_tracebak_string(e),#traceback.format_exc()
                },
                "request_id": request_id,
                "workbook_id": workbook_id,
                "source": source,
            })
            self._debugger = None


    async def _handle_event_execution(self, message: dict):
        """
        Handle event execution requests from the Excel Add-in.

        NO BACKWARD COMPATIBILITY - requires split module_name and function_name.

        Args:
            message: The event execution message containing:
                - module_name: The module name (REQUIRED)
                - function_name: The function name (REQUIRED)
                - args: List of serialized arguments [{name, value}, ...]
                - object_name: The name of the Excel object that fired the event
                - event_type: The type of event
                - object_type: The type of the Excel object
                - request_id: Optional request identifier for tracking
        """
        module_name = message.get("module_name", "")
        function_name = message.get("function_name", "")
        request_id = message.get("request_id")
        workbook_id = message.get("workbook_id", self.workbook_id)
        
        if not module_name or not function_name:
            logger.error("[Kernel] event_execution missing module_name or function_name")
            return
        
        args = message.get("args", [])
        object_name = message.get("object_name", "")
        event_type = message.get("event_type", "")
        object_type = message.get("object_type", "")

        logger.info(
            f"[Kernel] [Async Task] Received event_execution: {module_name}.{function_name} "
            f"(object={object_type}/{object_name}, event={event_type})"
        )

        # Dispatch to worker thread pool to avoid blocking the listener
        logger.debug(f"[Kernel] [Async Task] Dispatching event_execution to worker: {module_name}.{function_name}")
        loop = asyncio.get_running_loop()
        
        def execute_event():
            """Execute event handler in worker thread with stdout/stderr capture."""
            thread_name = threading.current_thread().name
            logger.debug(f"[Kernel] [Worker Thread {thread_name}] Executing event handler: {module_name}.{function_name}")
            
            # Create stdout/stderr callbacks that send messages in real-time
            def stdout_callback(text: str):
                """Stream stdout in real-time from worker thread."""
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.send_message({
                            "type": "stdout",
                            "content": text,
                            "request_id": request_id,
                            "workbook_id": workbook_id,
                            "source": "addin",
                        }),
                        loop
                    )
                except Exception as e:
                    logger.debug(f"[Kernel] stdout streaming error: {e}")

            def stderr_callback(text: str):
                """Stream stderr in real-time from worker thread."""
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.send_message({
                            "type": "stderr",
                            "content": text,
                            "request_id": request_id,
                            "workbook_id": workbook_id,
                            "source": "addin",
                        }),
                        loop
                    )
                except Exception as e:
                    logger.debug(f"[Kernel] stderr streaming error: {e}")
            
            # Create StreamCapture instances with callbacks
            stdout_capture = StreamCapture(on_write=stdout_callback)
            stderr_capture = StreamCapture(on_write=stderr_callback)
            
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    # Convert args from wire format to Python objects
                    deserialized_args = self._deserialize_args(args)

                    # DON'T REMOVE: To ensure module lazy-load
                    # DON'T TRY to use importlib instead of excec
                    exec(f"import {module_name}")  # Ensure module is imported}
                    """
                    try:
                        exec(f"import {module_name}")  # Ensure module is imported}
                    except Exception as egui:
                        pass  # Ignore import errors here; will check sys.modules next
                    """

                    
                    # Retrieve the module from sys.modules
                    if module_name not in sys.modules:
                        raise ImportError(f"Module '{module_name}' not found in sys.modules")
                    
                    module = sys.modules[module_name]
                    
                    # Retrieve the function using getattr
                    if not hasattr(module, function_name):
                        raise AttributeError(f"Function '{function_name}' not found in module '{module_name}'")
                    
                    func = getattr(module, function_name)

                    
                    # Execute the function
                    try:
                        func(*deserialized_args)
                    except Exception as e:
                        #traceback.print_exc(file=sys.stderr)
                        raise e
                
               
                
                except Exception as e:
                    traceback.print_exc(file=sys.stderr)
                    return {
                        "status": "error",
                        "logs": stdout_capture.getvalue() + stderr_capture.getvalue(),
                        "error": extract_tracebak_string(e),# traceback.format_exc()
                    }
                
                return {
                    "status": "success",
                    "logs": stdout_capture.getvalue() + stderr_capture.getvalue(),
                    "error": None
                }

        try:
            # Execute in thread pool
            result_dict = await loop.run_in_executor(self._thread_pool, execute_event)
            
            # Log any captured output
            if result_dict.get("logs"):
                logger.info(f"[Kernel] Event handler logs:\n{result_dict['logs']}")
            
            if result_dict["status"] == "success":
                logger.info(
                    f"[Kernel] Event handler executed successfully: {module_name}.{function_name}"
                )
                
                # Send success response with logs
                await self.send_message({
                    "type": "event_execution_result",
                    "status": "success",
                    "logs": result_dict.get("logs", ""),
                    "error": None,
                    "request_id": request_id,
                    "module_name": module_name,
                    "function_name": function_name,
                    "workbook_id": workbook_id,
                })
            else:
                # Send error response with logs
                error_msg = result_dict.get("error", "Unknown error")
                logger.error(f"[Kernel] Event handler failed: {module_name}.{function_name}")
                
                await self.send_message({
                    "type": "event_execution_result",
                    "status": "error",
                    "logs": result_dict.get("logs", ""),
                    "error": error_msg,
                    "request_id": request_id,
                    "module_name": module_name,
                    "function_name": function_name,
                    "workbook_id": workbook_id,
                })
                
        except Exception as e:
            # Handle any unexpected errors
            logger.error(f"[Kernel] Unexpected error in _handle_event_execution: {e}")
            await self.send_message({
                "type": "event_execution_result",
                "status": "error",
                "logs": "",
                "error": extract_tracebak_string(e),# traceback.format_exc(),
                "request_id": request_id,
                "module_name": module_name,
                "function_name": function_name,
                "workbook_id": workbook_id,
            })

    async def _handle_python_function_call(self, message: dict):
        """
        Handle Python callable invocation from Excel.
        
        This method:
        1. Retrieves the callable from xpycode.messaging using the callable_id
        2. Deserializes arguments using Serializer.from_wire
        3. Executes the callable with stdout/stderr capture
        4. Serializes the result using Serializer.to_wire
        5. Returns the result to the Business Layer
        
        Args:
            message: The python_function_call message containing:
                - callable_id: The ID of the registered callable
                - args: List of wire-format arguments
                - request_id: Unique request identifier
                - workbook_id: The workbook ID
        """
        callable_id = message.get("callable_id", "")
        args = message.get("args", [])
        request_id = message.get("request_id")
        workbook_id = message.get("workbook_id")
        
        logger.info(
            f"[Kernel] Received python_function_call: callable_id={callable_id} "
            f"(request_id={request_id})"
        )
        
        async def send_error(error_type: str, error_message: str, traceback_str: str = ""):
            """Send an error message back to the Business Layer."""
            error_dict = {
                "type": error_type,
                "message": error_message,
                "traceback": traceback_str,
            }
            
            await self.send_message({
                "type": "python_function_result",
                "success": False,
                "error": error_dict,
                "request_id": request_id,
                "workbook_id": workbook_id,
            })
        
        if not callable_id:
            await send_error("ValidationError", "Missing callable_id")
            return
        
        try:
            # Dispatch execution to worker thread pool
            logger.debug(f"[Kernel] [Async Task] Dispatching python_function_call to worker: callable_id={callable_id}")
            loop = asyncio.get_running_loop()
            
            def execute_callable():
                """Execute the callable in a worker thread with stdout/stderr capture."""
                thread_name = threading.current_thread().name
                logger.debug(f"[Kernel] [Worker Thread {thread_name}] Executing callable: {callable_id}")
                
                # Create stdout/stderr callbacks that send messages in real-time
                def stdout_callback(text: str):
                    """Stream stdout in real-time from worker thread."""
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.send_message({
                                "type": "stdout",
                                "content": text,
                                "request_id": request_id,
                                "workbook_id": workbook_id,
                                "source": "addin",
                            }),
                            loop
                        )
                    except Exception as e:
                        logger.debug(f"[Kernel] stdout streaming error: {e}")
                
                def stderr_callback(text: str):
                    """Stream stderr in real-time from worker thread."""
                    try:
                        asyncio.run_coroutine_threadsafe(
                            self.send_message({
                                "type": "stderr",
                                "content": text,
                                "request_id": request_id,
                                "workbook_id": workbook_id,
                                "source": "addin",
                            }),
                            loop
                        )
                    except Exception as e:
                        logger.debug(f"[Kernel] stderr streaming error: {e}")
                
                # Create StreamCapture instances with callbacks
                stdout_capture = StreamCapture(on_write=stdout_callback)
                stderr_capture = StreamCapture(on_write=stderr_callback)
                
                try:
                    with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                        # 1. Retrieve the callable from the messaging registry
                        callable_obj = xpycode.messaging.get_callable(callable_id)
                        
                        if callable_obj is None:
                            raise ValueError(f"Callable '{callable_id}' not found in registry")
                        
                        if not callable(callable_obj):
                            raise TypeError(f"Object with id '{callable_id}' is not callable")
                        
                        # 2. Deserialize all arguments using Serializer.from_wire
                        deserialized_args = self._deserialize_args(args)
                        
                        # 3. Execute the callable and serialize result
                        try:
                            result = callable_obj(*deserialized_args)
                            
                            # 4. Serialize the result using Serializer.to_wire
                            serialized_result = xpycode.Serializer.to_wire(result)
                        except Exception as e:
                            # Print traceback to stderr for real-time streaming
                            traceback.print_exc(file=sys.stderr)
                            raise e
                    
                    # Get captured logs
                    logs = stdout_capture.getvalue() + stderr_capture.getvalue()
                    
                    return {
                        "status": "success",
                        "result": serialized_result,
                        "base_result": result,
                        "logs": logs
                    }
                    
                except Exception as e:
                    # Get captured logs even on error
                    logs = stdout_capture.getvalue() + stderr_capture.getvalue()
                    
                    return {
                        "status": "error",
                        "result": None,
                        "logs": logs,
                        "error": extract_tracebak_string(e),# traceback.format_exc()
                    }
            
            # Execute in thread pool
            result_dict = await loop.run_in_executor(self._thread_pool, execute_callable)
            
            # Log any captured output
            if result_dict.get("logs"):
                logger.info(f"[Kernel] Callable logs:\n{result_dict['logs']}")
            
            if result_dict["status"] == "success":
                # Send result_output for IDE console display
                if result_dict["result"] is not None:
                    result_repr = repr(result_dict["base_result"])
                    await self.send_message({
                        "type": "result_output",
                        "content": f"Out: {result_repr}\n",
                        "request_id": request_id,
                        "workbook_id": workbook_id,
                    })
                
                # Send success response
                await self.send_message({
                    "type": "python_function_result",
                    "success": True,
                    "result": result_dict["result"],
                    "logs": result_dict.get("logs", ""),
                    "request_id": request_id,
                    "workbook_id": workbook_id,
                })
                
                logger.info(f"[Kernel] Python function call succeeded: callable_id={callable_id}")
            else:
                # Send error response
                error_msg = result_dict.get("error", "Unknown error")
                
                await self.send_message({
                    "type": "python_function_result",
                    "success": False,
                    "error": error_msg,
                    "logs": result_dict.get("logs", ""),
                    "request_id": request_id,
                    "workbook_id": workbook_id,
                })
                
                logger.error(f"[Kernel] Python function call failed: callable_id={callable_id}")
                
        except Exception as e:
            # Handle any unexpected errors
            logger.error(f"[Kernel] Unexpected error in _handle_python_function_call: {e}")
            await send_error(type(e).__name__, str(e), extract_tracebak_string(e))#traceback.format_exc())

    async def _execute_streaming_function(self, request_id: str, module_name: str, function_name: str, args: list, workbook_id:str, source:str):
        """
        Execute a streaming (generator) function in a worker thread.
        
        Uses run_in_executor to avoid blocking the event loop while
        iterating through the generator.
        
        Note: module_name and function_name have already been validated by the 
        business layer using validate_python_identifier() to prevent code injection.
        
        Args:
            request_id: Unique identifier for this execution
            module_name: Name of the module containing the function (validated)
            function_name: Name of the generator function to execute (validated)
            args: List of arguments in wire format
        """
        start_time = time.time()
        logger.debug(f"[TIMING] Streaming execution started: request_id={request_id}, function={module_name}.{function_name}")
        logger.info(f"[Kernel] _execute_streaming_function: module={module_name}, function={function_name}, request_id={request_id}")
        
        # Check if module is available before dispatching to thread pool
        if module_name not in in_memory_loader.source_cache:
            # Request module sync from server/IDE
            logger.warning(f"[Kernel] Module '{module_name}' not in cache, requesting sync")
            await self.send_message({
                "type": "request_module_sync",
                "module_name": module_name,
                "workbook_id": self.workbook_id
            })
            
            # Wait briefly for sync (with timeout)
            max_wait = 5.0  # 5 seconds max
            wait_interval = 0.1
            waited = 0.0
            while module_name not in in_memory_loader.source_cache and waited < max_wait:
                await asyncio.sleep(wait_interval)
                waited += wait_interval
            
            if module_name not in in_memory_loader.source_cache:
                elapsed_ms = (time.time() - start_time) * 1000
                logger.error(f"[TIMING] Streaming failed: request_id={request_id}, elapsed={elapsed_ms:.1f}ms, error=Module not found after sync")
                logger.error(f"[Kernel] Module '{module_name}' not found after sync attempt")
                await self.send_message({
                    "type": "streaming_function_result",
                    "request_id": request_id,
                    "error": f"Module '{module_name}' not found after sync attempt",
                    "done": True,
                    "workbook_id": self.workbook_id,
                })
                return
        
        loop = asyncio.get_running_loop()
        
        def run_streaming_in_thread():
            """Run the generator iteration in a worker thread."""
            thread_name = threading.current_thread().name
            logger.debug(f"[TIMING] Streaming worker started: thread={thread_name}, request_id={request_id}")
            # Create stdout/stderr callbacks that send messages in real-time
            def stdout_callback(text: str):
                """Stream stdout in real-time from worker thread."""
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.send_message({
                            "type": "stdout",
                            "content": text,
                            "request_id": request_id,
                            "workbook_id": workbook_id,
                            "source": source,
                        }),
                        loop
                    )
                except Exception as e:
                    logger.debug(f"[Kernel] stdout streaming error: {e}")

            def stderr_callback(text: str):
                """Stream stderr in real-time from worker thread."""
                try:
                    asyncio.run_coroutine_threadsafe(
                        self.send_message({
                            "type": "stderr",
                            "content": text,
                            "request_id": request_id,
                            "workbook_id": workbook_id,
                            "source": source,
                        }),
                        loop
                    )
                except Exception as e:
                    logger.debug(f"[Kernel] stderr streaming error: {e}")
                
            # Create StreamCapture instances with callbacks
            stdout_capture = StreamCapture(on_write=stdout_callback)
            stderr_capture = StreamCapture(on_write=stderr_callback)
                
            with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                try:
                    # Get the module
                    # DON'T REMOVE: To ensure module lazy-load
                    # DON'T TRY to use importlib instead of exec
                    exec(f"import {module_name}")  # Ensure module is imported
                    '''
                    try:
                        exec(f"import {module_name}")  # Ensure module is imported
                    except Exception as egui:
                        pass  # Ignore import errors here; will check sys.modules next
                    '''

                    if module_name not in sys.modules:
                        logger.error(f"[Kernel] Module not found in sys.modules: {module_name}")
                        # Show a sample of available modules (limit to 20 to avoid excessive logging)
                        available_modules = [m for m in sys.modules.keys() if not m.startswith('_')]
                        logger.error(f"[Kernel] Sample of available modules: {available_modules[:20]}")
                        logger.error(f"[Kernel] in_memory_loader.source_cache keys: {list(in_memory_loader.source_cache.keys())}")
                        return {"error": f"Module not found: {module_name}"}
                
                    module = sys.modules[module_name]
                    logger.debug(f"[Kernel] Found module in sys.modules: {module_name}")
                
                    # Get the function
                    if not hasattr(module, function_name):
                        logger.error(f"[Kernel] Function not found in module: {function_name}")
                        logger.error(f"[Kernel] Available functions in module: {[name for name in dir(module) if not name.startswith('_')]}")
                        return {"error": f"Function not found: {function_name}"}
                
                    func = getattr(module, function_name)
                    logger.debug(f"[Kernel] Found function: {function_name}")
                
                    # Convert args from wire format
                    converted_args = self._deserialize_args(args)
                
                    # Call the generator function
                    generator = func(*converted_args)
                
                    # Check if it's actually a generator
                    if not inspect.isgenerator(generator):
                        logger.error(f"[Kernel] Function {function_name} is not a generator function")
                        return {"error": f"Function {function_name} is not a generator function"}
                
                    logger.info(f"[Kernel] Starting to stream results from generator: {function_name}")
                
                    # Iterate and send each result
                    result_count = 0
                    for result in generator:
                        # Check if canceled
                        if request_id in self._canceled_streaming_requests:
                            self._canceled_streaming_requests.discard(request_id)
                            asyncio.run_coroutine_threadsafe(
                                self.send_message({
                                    "type": "streaming_function_result",
                                    "request_id": request_id,
                                    "result": "Canceled",
                                    "done": True,
                                    "workbook_id": self.workbook_id,
                                }),
                                loop
                            ).result(timeout=1.0)  # Wait for send to complete
                            return {"canceled": True}
                    
                        # Serialize and send intermediate result
                        wire_result = xpycode.Serializer.to_wire(result)
                        asyncio.run_coroutine_threadsafe(
                            self.send_message({
                                "type": "streaming_function_result",
                                "request_id": request_id,
                                "result": wire_result,
                                "done": False,
                                "workbook_id": self.workbook_id,
                            }),
                            loop
                        ).result(timeout=1.0)  # Wait for send to complete
                    
                        result_count += 1
                    
                        # Yield to other threads periodically
                        if result_count % 10 == 0:
                            time.sleep(0.001)  # 1ms yield
                
                    return {"success": True, "result_count": result_count}
                
                except Exception as e:
                    traceback.print_exc(file=sys.stderr)
                    logger.error(f"[TIMING] Streaming error: request_id={request_id}, error={e}")
                    return {"error": str(e), "traceback": traceback.format_exc()}
        
        try:
            # Run generator iteration in thread pool
            result = await loop.run_in_executor(self._thread_pool, run_streaming_in_thread)
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if result.get("error"):
                logger.error(f"[TIMING] Streaming failed: request_id={request_id}, elapsed={elapsed_ms:.1f}ms, error={result['error']}")
                await self.send_message({
                    "type": "streaming_function_result",
                    "request_id": request_id,
                    "error": result["error"],
                    "done": True,
                    "workbook_id": self.workbook_id,
                })
            elif result.get("canceled"):
                logger.debug(f"[TIMING] Streaming canceled: request_id={request_id}, elapsed={elapsed_ms:.1f}ms")
            else:
                logger.debug(f"[TIMING] Streaming completed: request_id={request_id}, elapsed={elapsed_ms:.1f}ms, results={result.get('result_count', 0)}")
                # Send final "done" message
                await self.send_message({
                    "type": "streaming_function_result",
                    "request_id": request_id,
                    "done": True,
                    "workbook_id": self.workbook_id,
                })
                
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"[TIMING] Streaming exception: request_id={request_id}, elapsed={elapsed_ms:.1f}ms, error={e}")
            await self.send_message({
                "type": "streaming_function_result",
                "request_id": request_id,
                "error": str(e),
                "done": True,
                "workbook_id": self.workbook_id,
            })
        finally:
            self._canceled_streaming_requests.discard(request_id)

    def _deserialize_args(self, args: list) -> List[Any]:
        """
        Deserialize  arguments from wire format to Python objects.

        Each argument in the args list is expected to be in a format known by Serializer.from_wire

        Args:
            args: List of argument 

        Returns:
            A list of arguments deserialized into Python values.
        """
        if not args:
            return []

        deserialized = []
        for arg in args:
            # Deserialize the wire-formatted value using Serializer.from_wire
            deserialized_arg = xpycode.Serializer.from_wire(arg)
            deserialized.append(deserialized_arg)

        return deserialized

    def save_object(self, key: str, value: Any):
        """
        Store an object in the ObjectKeeper and notify IDE.
        
        Threading Note: This method is thread-safe due to _object_keeper_lock.
        Can be called from any thread (worker or listener).
        
        Args:
            key: String key for the object
            value: Object to store
            
        Raises:
            ValueError: If key is not a non-empty string
        """
        # Validate key parameter
        if not isinstance(key, str) or not key:
            raise ValueError("ObjectKeeper key must be a non-empty string")
        
        with self._object_keeper_lock:
            self._object_keeper[key] = value
        
        # Send object_registry_update message
        asyncio.run_coroutine_threadsafe(
            self.send_message({
                "type": "object_registry_update",
                "action": "update",
                "key": key,
                "object_type": type(value).__name__,
                "repr": repr(value),
                "workbook_id": self.workbook_id,
            }),
            self._loop
        )
        logger.debug(f"[Kernel] Saved object: {key} (type: {type(value).__name__})")

    def get_object(self, key: str) -> Optional[Any]:
        """
        Retrieve an object from the ObjectKeeper.
        
        Threading Note: This method is thread-safe due to _object_keeper_lock.
        Can be called from any thread (worker or listener).
        
        Args:
            key: String key for the object
            
        Returns:
            The stored object or None if not found
        """
        with self._object_keeper_lock:
            return self._object_keeper.get(key)

    def clear_object(self, key: str):
        """
        Remove an object from the ObjectKeeper and notify IDE.
        
        Threading Note: This method is thread-safe due to _object_keeper_lock.
        Can be called from any thread (worker or listener).
        
        Args:
            key: String key for the object to remove
        """
        with self._object_keeper_lock:
            if key in self._object_keeper:
                del self._object_keeper[key]
        
        # Send object_registry_update message
        asyncio.run_coroutine_threadsafe(
            self.send_message({
                "type": "object_registry_update",
                "action": "delete",
                "key": key,
                "workbook_id": self.workbook_id,
            }),
            self._loop
        )
        logger.debug(f"[Kernel] Cleared object: {key}")

    def clear_all_objects(self):
        """
        Clear all objects from the ObjectKeeper and notify IDE.
        
        Threading Note: This method is thread-safe due to _object_keeper_lock.
        Can be called from any thread (worker or listener).
        """
        with self._object_keeper_lock:
            self._object_keeper.clear()
        
        # Send object_registry_update message
        asyncio.run_coroutine_threadsafe(
            self.send_message({
                "type": "object_registry_update",
                "action": "clear_all",
                "workbook_id": self.workbook_id,
            }),
            self._loop
        )
        logger.debug("[Kernel] Cleared all objects")


    def set_enable_events(self, enable: bool):
        """
        Enable or disable event handling in the Excel add-in.

        Args:
            enable: True to enable events, False to disable
        """
        asyncio.run_coroutine_threadsafe(
            self.send_message({
                "type": "set_enable_events",
                "enable": enable,
                "workbook_id": self.workbook_id,
            }),
            self._loop
        )
        logger.debug(f"[Kernel] Set enable_events: {enable}")

    def show_message_box(self, message: str, title: str = "XPyCode", type:str="Info"):
        """
        Show a message box in the Excel add-in UI.
        
        Threading Note: This method is thread-safe due to _loop usage.
        Can be called from any thread (worker or listener).
        
        Args:
            message: The message to display
            title: The title of the message box (default: "XPyCode")
            type: The type of message box ("Info", "Warning", "Error")
        """
        asyncio.run_coroutine_threadsafe(
            self.send_message({
                "type": "show_message_box",
                "message": message,
                "title": title,
                "msg_type": type,
                "workbook_id": self.workbook_id,
            }),
            self._loop
        )
        logger.debug(f"[Kernel] Requested message box: title='{title}', type='{type}'")
        
    def get_object_registry(self) -> list:
        """
        Get the full object registry.
        
        Threading Note: This method is thread-safe due to _object_keeper_lock.
        Can be called from any thread (worker or listener).
        
        Returns:
            List of dicts with keys: key, type, repr
        """
        with self._object_keeper_lock:
            return [
                {
                    "key": key,
                    "type": type(value).__name__,
                    "repr": repr(value)
                }
                for key, value in self._object_keeper.items()
            ]

    async def listen(self):
        """
        Main loop to listen for messages from the Business Layer.
        
        Processes messages asynchronously while allowing user code in the thread
        pool to make synchronous sys_request calls without deadlocking.
        """
        try:
            async for message in self.websocket:
                # Validate message size to prevent memory exhaustion
                if len(message) > MAX_MESSAGE_SIZE:
                    logger.warning(f"Message too large: {len(message)} bytes")
                    await self.send_message(
                        {"type": "error", "message": "Message too large"}
                    )
                    continue

                try:
                    data = json.loads(message)
                    await self.handle_message(data)
                except json.JSONDecodeError:
                    await self.send_message(
                        {"type": "error", "message": "Invalid JSON received"}
                    )
        except websockets.ConnectionClosed:
            self.running = False

    async def run(self):
        """Connect and start listening for messages."""
        try:
            await self.connect()
            logger.info(f"Kernel connected for workbook: {self.workbook_id}")
            await self.listen()
        except Exception as e:
            logger.error(f"Kernel error: {e}")
        finally:
            await self.disconnect()
            logger.info(f"Kernel disconnected for workbook: {self.workbook_id}")


async def main(workbook_id: str, port:str):
    """Main entry point for the kernel."""
    kernel = PythonKernel(workbook_id, port=port)
    await kernel.run()
