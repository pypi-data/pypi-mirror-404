"""
WebSocket Client for XPyCode IDE.

This module provides a threaded WebSocket client that runs independently of Qt's
event loop, preventing modal dialogs from blocking keepalive messages.
"""

import asyncio
import json
import logging
import threading
from turtle import color
import uuid
from typing import Callable, Dict, Optional, Any
import websockets
from websockets.exceptions import ConnectionClosed
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QMessageBox

from .utils.decorators_pyside6_threadsafe import run_in_qt_thread
from .settings_actions import OutputLevel

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class WebSocketClient:
    """
    Threaded WebSocket client for IDE communication with Business Layer.
    
    Runs in a separate thread to avoid blocking Qt's main event loop.
    This prevents keepalive timeout issues when modal dialogs are open.
    """
    
    def __init__(self, main_window, host: str = "localhost", port: int = 8000):
        """
        Initialize WebSocket client.
        
        Args:
            main_window: Reference to MainWindow for UI updates
            host: WebSocket server host
            port: WebSocket server port
        """
        self.main_window = main_window
        self.host = host
        self.port = port
        self.url = f"ws://{host}:{port}/ws/ide/main_ide"
        
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        
        # Pending requests for send_and_wait_response pattern
        self._pending_requests: Dict[str, dict] = {}
        
        # Reconnection settings
        self._reconnect_delay = 1.0
        self._max_reconnect_delay = 30.0
        self._reconnect_attempts = 0
        
        # Connection state
        self._connected = False
        
        # Setup message handlers
        self._setup_message_handlers()
        
    def start(self):
        """Start the WebSocket client in a separate thread."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        logger.info(f"[WebSocketClient] Started, connecting to {self.url}")
    
    def stop(self):
        """Stop the WebSocket client."""
        self._running = False
        if self._loop:
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread:
            self._thread.join(timeout=5.0)
        logger.info("[WebSocketClient] Stopped")
    
    def _run_event_loop(self):
        """Run the asyncio event loop in the dedicated thread."""
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        
        try:
            self._loop.run_until_complete(self._connect_and_listen())
        except Exception as e:
            logger.error(f"[WebSocketClient] Event loop error: {e}")
        finally:
            self._loop.close()
    
    @property
    def connected(self):
        return self._connected
    
    async def _connect_and_listen(self):
        """Connect to WebSocket server and listen for messages."""
        while self._running:
            try:
                async with websockets.connect(
                    self.url,
                    ping_interval=20,
                    ping_timeout=60,
                    close_timeout=10
                ) as ws:
                    self.ws = ws
                    self._reconnect_attempts = 0
                    self._reconnect_delay = 1.0
                    
                    logger.info("[WebSocketClient] Connected to Business Layer")
                    self._on_connected()
                    
                    self._connected = True
                    # Listen for messages
                    async for message in ws:
                        await self._handle_message(message)
                        
            except ConnectionClosed as e:
                logger.warning(f"[WebSocketClient] Connection closed: {e}")
                self._connected = False
                self._on_disconnected()
                
            except Exception as e:
                logger.error(f"[WebSocketClient] Connection error: {e}")
                self._connected = False
                self._on_disconnected()
            
            # Reconnect logic
            if self._running:
                await self._reconnect()
    
    async def _reconnect(self):
        """Handle reconnection with exponential backoff."""
        self._reconnect_attempts += 1
        delay = min(self._reconnect_delay * (2 ** (self._reconnect_attempts - 1)), self._max_reconnect_delay)
        
        logger.info(f"[WebSocketClient] Reconnecting in {delay:.1f}s (attempt {self._reconnect_attempts})...")
        self._on_reconnecting(self._reconnect_attempts, delay)
        await asyncio.sleep(delay)
    
    def send_message(self, message: dict):
        """
        Send a message to the server.
        
        Thread-safe: can be called from Qt thread.
        """
        if not self._connected or not self.ws:
            logger.warning("[WebSocketClient] Cannot send message: not connected")
            return
        
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._async_send(message),
                self._loop
            )
    
    async def _async_send(self, message: dict):
        """Async send implementation."""
        if self.ws:
            try:
                await self.ws.send(json.dumps(message))
            except Exception as e:
                logger.error(f"[WebSocketClient] Send error: {e}")
    
    def send_text_message(self, message: str):
        """
        Send a raw text message to the server.
        
        Thread-safe: can be called from Qt thread.
        For backwards compatibility with existing code using websocket.sendTextMessage().
        """
        if not self._connected or not self.ws:
            logger.warning("[WebSocketClient] Cannot send message: not connected")
            return
        
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._async_send_text(message),
                self._loop
            )
    
    # Alias for backwards compatibility
    def sendTextMessage(self, message: str):
        """Alias for send_text_message for backwards compatibility."""
        self.send_text_message(message)
    
    async def _async_send_text(self, message: str):
        """Async send text implementation."""
        if self.ws:
            try:
                await self.ws.send(message)
            except Exception as e:
                logger.error(f"[WebSocketClient] Send error: {e}")
    
    def is_connected(self) -> bool:
        """Check if connected to server."""
        return self._connected
    
    def send_and_wait_response(
        self,
        message: dict,
        callback: Callable[[dict], None],
        response_type: Optional[str] = None,
        timeout: float = 30.0
    ) -> str:
        """
        Send a message and register a callback for the response.
        
        This is ASYNCHRONOUS - it does NOT block. The callback is called
        when the response arrives (or on timeout).
        
        Args:
            message: The message to send (will add request_id if not present)
            callback: Function to call with the response dict
            response_type: Expected response message type (optional)
            timeout: Timeout in seconds
        
        Returns:
            The request_id used for this request
        """
        request_id = message.get("request_id") or str(uuid.uuid4())
        message["request_id"] = request_id
        
        self._pending_requests[request_id] = {
            "callback": callback,
            "response_type": response_type,
        }
        
        self.send_message(message)
        
        if self._loop:
            asyncio.run_coroutine_threadsafe(
                self._check_timeout(request_id, timeout),
                self._loop
            )
        
        return request_id
    
    async def _check_timeout(self, request_id: str, timeout: float):
        """Check for request timeout."""
        await asyncio.sleep(timeout)
        
        if request_id in self._pending_requests:
            pending = self._pending_requests.pop(request_id)
            callback = pending["callback"]
            self._invoke_callback_in_qt_thread(callback, {
                "error": "timeout",
                "request_id": request_id,
                "message": f"Request timed out after {timeout}s"
            })
    
    def _try_handle_response(self, message: dict) -> bool:
        """Try to handle message as a response to a pending request."""
        request_id = message.get("request_id")
        if not request_id or request_id not in self._pending_requests:
            return False
        
        pending = self._pending_requests.pop(request_id)
        callback = pending["callback"]
        expected_type = pending.get("response_type")
        
        if expected_type and message.get("type") != expected_type:
            self._pending_requests[request_id] = pending
            return False
        self._invoke_callback_in_qt_thread(callback, message)
        return True
    
    @run_in_qt_thread
    def _invoke_callback_in_qt_thread(self, callback: Callable, data: dict):
        """Invoke callback in Qt thread using QTimer."""
        callback(data)
        #QTimer.singleShot(0, lambda: callback(data))
    
    def _setup_message_handlers(self):
        """Setup message type to handler mapping."""
        self.MESSAGE_HANDLERS: Dict[str, Callable] = {
            # Watchdog info
            "watchdog_info": self._handle_watchdog_info,
            
            # Workbook management
            "workbook_connected": self._handle_workbook_connected,
            "workbook_disconnected": self._handle_workbook_disconnected,
            "workbook_name_changed": self._handle_workbook_name_changed,
            "workbook_list": self._handle_workbook_list,
            
            # Module management
            "module_content": self._handle_module_content,
            "module_deleted": self._handle_module_deleted,
            "module_saved": self._handle_module_saved,
            "module_list": self._handle_module_list,
            "all_modules": self._handle_all_modules,
            
            # Package management
            "pip_output": self._handle_pip_output,
            "get_package_versions_response": self._handle_package_versions_response,
            "get_package_extras_response": self._handle_package_extras_response,
            "get_package_info_response": self._handle_package_info_response,
            "workbook_packages_update": self._handle_workbook_packages_update,
            "package_install_progress": self._handle_package_install_progress,
            "package_installation_complete": self._handle_package_installation_complete,
            "resolved_deps_response": self._handle_resolved_deps_response,
            "package_paths_updated": self._handle_package_paths_updated,
            
            # Execution output
            "stdout": self._handle_stdout,
            "stderr": self._handle_stderr,
            "result_output": self._handle_result_output,
            "execution_result": self._handle_execution_result,
            
            # LSP responses
            "completion_response": self._handle_completion_response,
            "signature_help_response": self._handle_signature_help_response,
            "hover_response": self._handle_hover_response,
            "diagnostic_response": self._handle_diagnostic_response,
            
            # Event management
            "event_manager_state": self._handle_event_manager_state,
            "register_handler_result": self._handle_register_handler_result,
            "unregister_handler_result": self._handle_unregister_handler_result,
            "save_event_config_response": self._handle_save_event_config_response,
            "validate_handler_response": self._handle_validate_handler_response,
            
            # Function publishing
            "published_functions_state": self._handle_published_functions_state,
            
            # Object registry
            "object_registry_update": self._handle_object_registry_update,
            "object_registry_response": self._handle_object_registry_response,
            
            # Debugging
            "debug_paused": self._handle_debug_paused,
            "debug_exception": self._handle_debug_exception,
            "debug_resumed": self._handle_debug_resumed,
            "debug_terminated": self._handle_debug_terminated,
            "debug_evaluate_result": self._handle_debug_evaluate_result,
            
            # Settings
            "all_settings_response": self._handle_all_settings_response,
            "settings_response": self._handle_settings_response,
            "setting_saved": self._handle_setting_saved,
            
            # IDE control
            "show_ide": self._handle_show_ide,
            "message_ide": self._handle_message_ide,

            # Console output
            "log_to_console": self._handle_log_to_console,
        }
    
    async def _handle_message(self, raw_message: str):
        """
        Top-level message handler.
        
        1. Parse JSON
        2. Try to handle as response to pending request
        3. Dispatch to handler based on message type
        """
        try:
            data = json.loads(raw_message)
            message_type = data.get("type")
            
            if self._try_handle_response(data):
                return
            
            handler = self.MESSAGE_HANDLERS.get(message_type)
            if handler:
                handler(data)
            else:
                logger.warning(f"[WebSocketClient] No handler for message type: {message_type}")
                
        except json.JSONDecodeError as e:
            logger.error(f"[WebSocketClient] Failed to parse message: {e}")
        except Exception as e:
            logger.error(f"[WebSocketClient] Error handling message: {e}", exc_info=True)
    
    # ============================================================
    # Connection State Handlers
    # ============================================================
    
    def _on_connected(self):
        """Called when WebSocket connection is established."""
        self._on_connected_qt()
        #QTimer.singleShot(0, self._on_connected_qt)
    
    @run_in_qt_thread
    def _on_connected_qt(self):
        """Handle connection in Qt thread."""
        self.main_window.log_to_console("Connected to XPyCode Server",level=OutputLevel.DETAILED)
        self.main_window.statusBar().showMessage("Connected to XPyCode Server")
        #self.main_window._request_initial_settings()
    
    def _on_disconnected(self):
        """Called when WebSocket connection is lost."""
        self._on_disconnected_qt()
        #QTimer.singleShot(0, self._on_disconnected_qt)
    
    @run_in_qt_thread
    def _on_disconnected_qt(self):
        """Handle disconnection in Qt thread."""
        self.main_window.log_to_console("Disconnected from XPyCode Server",level=OutputLevel.DETAILED)
        self.main_window.statusBar().showMessage("Disconnected - Reconnecting...")
    
    def _on_reconnecting(self, attempt: int, delay: float):
        """Called during reconnection attempts."""
        self._on_reconnecting_qt(attempt, delay)
        #QTimer.singleShot(0, lambda: self._on_reconnecting_qt(attempt, delay))
    
    @run_in_qt_thread
    def _on_reconnecting_qt(self, attempt: int, delay: float):
        """Handle reconnection status in Qt thread."""
        self.main_window.statusBar().showMessage(
            f"Reconnecting... (attempt {attempt}, next try in {delay:.0f}s)"
        )
    
    # ============================================================
    # Message Handlers - Use @run_in_qt_thread for PyQt interactions
    # ============================================================
    
    @run_in_qt_thread
    def _handle_workbook_connected(self, data: dict):
        """Handle workbook_connected message."""
        workbook_id = data.get("workbook_id")
        name = data.get("name")
        modules = data.get("modules", {})
        module_names = list(modules.keys())
        
        if workbook_id:
            self.main_window.project_explorer.add_workbook(workbook_id, name)
            if module_names:
                self.main_window.project_explorer.set_modules(workbook_id, module_names)
            
            self.main_window._module_cache[workbook_id] = modules
            self.main_window.event_manager.set_module_cache(workbook_id, modules)
            
            display_name = name if name else workbook_id
            self.main_window.log_to_console(f"Workbook connected: {display_name}",level=OutputLevel.DETAILED)
    
    @run_in_qt_thread
    def _handle_workbook_disconnected(self, data: dict):
        """Handle workbook_disconnected message."""
        workbook_id = data.get("workbook_id")
        if workbook_id:
            if self.main_window._debug_active and self.main_window._current_debug_workbook == workbook_id:
                logger.info(f"[IDE] Stopping debugger - workbook {workbook_id} disconnected")
                self.main_window._debug_stop()
            
            self.main_window.project_explorer.remove_workbook(workbook_id)
            self.main_window._close_tabs_for_workbook(workbook_id)
            
            if workbook_id in self.main_window._module_cache:
                del self.main_window._module_cache[workbook_id]
            if workbook_id in self.main_window.event_manager._module_cache:
                del self.main_window.event_manager._module_cache[workbook_id]
            if workbook_id in self.main_window._synced_module_hashes:
                del self.main_window._synced_module_hashes[workbook_id]
            
            self.main_window.log_to_console(f"Workbook disconnected: {workbook_id}",level=OutputLevel.DETAILED)
    
    @run_in_qt_thread
    def _handle_workbook_name_changed(self, data: dict):
        """Handle workbook_name_changed message."""
        workbook_id = data.get("workbook_id")
        old_name = data.get("old_name")
        new_name = data.get("new_name")
        
        if workbook_id and new_name:
            self.main_window._update_workbook_name(workbook_id, new_name)
            self.main_window.event_manager.update_workbook_name(workbook_id, new_name)
            self.main_window.function_publisher.update_workbook_name(workbook_id, new_name)
            self.main_window.object_inspector.update_workbook_name(workbook_id, new_name)
            self.main_window.package_manager.update_workbook_name(workbook_id, new_name)
            self.main_window.log_to_console(f"Workbook renamed: {old_name} -> {new_name}",level=OutputLevel.DETAILED)
    
    @run_in_qt_thread
    def _handle_workbook_list(self, data: dict):
        """Handle workbook_list message."""
        workbooks = data.get("workbooks", [])
        current_workbooks = set(self.main_window.project_explorer._workbook_items.keys())
        
        new_workbooks_dict = {}
        new_workbooks_modules = {}
        for wb in workbooks:
            if isinstance(wb, dict):
                wb_id = wb.get("id")
                if wb_id is not None:
                    new_workbooks_dict[wb_id] = wb.get("name")
                    new_workbooks_modules[wb_id] = wb.get("modules", {})
            else:
                new_workbooks_dict[wb] = None
                new_workbooks_modules[wb] = []
        
        new_workbook_ids = set(new_workbooks_dict.keys())
        
        for workbook_id in new_workbook_ids - current_workbooks:
            name = new_workbooks_dict.get(workbook_id)
            self.main_window.set_workbook_name(workbook_id, name)
            self.main_window.project_explorer.add_workbook(workbook_id, name)
            modules = new_workbooks_modules.get(workbook_id, {})
            module_names = list(modules.keys())
            if module_names:
                self.main_window.project_explorer.set_modules(workbook_id, module_names)
            self.main_window._module_cache[workbook_id] = modules
        
        for workbook_id in current_workbooks - new_workbook_ids:
            self.main_window.project_explorer.remove_workbook(workbook_id)
            if workbook_id in self.main_window._module_cache:
                del self.main_window._module_cache[workbook_id]
            if workbook_id in self.main_window._synced_module_hashes:
                del self.main_window._synced_module_hashes[workbook_id]
        
        self.main_window.log_to_console(f"Received workbook list: {len(workbooks)} workbooks",level=OutputLevel.DETAILED)
    
    @run_in_qt_thread
    def _handle_module_content(self, data: dict):
        """Handle module_content message."""
        from .monaco_editor import MonacoEditor
        
        workbook_id = data.get("workbook_id")
        module_name = data.get("module_name")
        code = data.get("code")
        
        if workbook_id and module_name and code is not None:
            if workbook_id not in self.main_window._module_cache:
                self.main_window._module_cache[workbook_id] = {}
            self.main_window._module_cache[workbook_id][module_name] = code
            self.main_window.event_manager.set_module_cache(workbook_id, self.main_window._module_cache.get(workbook_id, {}))
            self.main_window.add_editor_tab(module_name, code, workbook_id)
            self.main_window.log_to_console(f"Opened module: {module_name}",level=OutputLevel.DETAILED)
            
            # Check if there's a pending debug line for this module
            if self.main_window._pending_debug_line:
                pending = self.main_window._pending_debug_line
                if pending["workbook_id"] == workbook_id and pending["module_name"] == module_name:
                    pending_line = pending["line"]
                    for i in range(self.main_window.editor_tabs.count()):
                        widget = self.main_window.editor_tabs.widget(i)
                        if isinstance(widget, MonacoEditor):
                            tab_title = self.main_window.editor_tabs.tabText(i)
                            # Strip .py extension
                            tab_module = tab_title[:-3] if tab_title.endswith('.py') else tab_title
                            if tab_module == module_name and widget.workbook_id == workbook_id:
                                QTimer.singleShot(self.main_window.DEBUG_LINE_HIGHLIGHT_DELAY_MS, lambda line=pending_line: widget.set_debug_line(line))
                                self.main_window._current_debug_editor = widget
                                break
                    self.main_window._pending_debug_line = None
        elif code is None:
            self.main_window.log_to_console(f"Module not found: {module_name}", "#ff6b6b",level=OutputLevel.DETAILED)
    
    @run_in_qt_thread
    def _handle_module_deleted(self, data: dict):
        """Handle module_deleted message."""
        workbook_id = data.get("workbook_id")
        module_name = data.get("module_name")
        success = data.get("success", False)
        if success:
            logger.debug(f"Module '{module_name}' deleted from Business Layer")
        else:
            logger.warning(f"Failed to delete module '{module_name}' from Business Layer")
    
    @run_in_qt_thread
    def _handle_module_saved(self, data: dict):
        """Handle module_saved message."""
        workbook_id = data.get("workbook_id")
        module_name = data.get("module_name")
        logger.debug(f"Module '{module_name}' saved to Business Layer")
    
    @run_in_qt_thread
    def _handle_module_list(self, data: dict):
        """Handle module_list message."""
        workbook_id = data.get("workbook_id")
        modules = data.get("modules", [])
        if workbook_id:
            self.main_window.project_explorer.set_modules(workbook_id, modules)
    
    @run_in_qt_thread
    def _handle_all_modules(self, data: dict):
        """Handle all_modules message."""
        workbook_id = data.get("workbook_id")
        modules = data.get("modules", {})
        if workbook_id and modules:
            self.main_window._module_cache[workbook_id] = modules
            self.main_window.event_manager.set_module_cache(workbook_id, modules)
            self.main_window.project_explorer.set_modules(workbook_id, list(modules.keys()))
    
    @run_in_qt_thread
    def _handle_pip_output(self, data: dict):
        """Handle pip_output message."""
        self.main_window._handle_pip_output(data)
    
   
    @run_in_qt_thread
    def _handle_package_versions_response(self, data: dict):
        """Handle get_package_versions_response message."""
        self.main_window._handle_package_versions_response(data)
    
    @run_in_qt_thread
    def _handle_package_extras_response(self, data: dict):
        """Handle get_package_extras_response message."""
        self.main_window._handle_package_extras_response(data)
    
    @run_in_qt_thread
    def _handle_package_info_response(self, data: dict):
        """Handle get_package_info_response message."""
        self.main_window._handle_package_info_response(data)
    
    @run_in_qt_thread
    def _handle_workbook_packages_update(self, data: dict):
        """Handle workbook_packages_update message."""
        workbook_id = data.get("workbook_id")
        packages = data.get("packages", None)
        package_errors = data.get("package_errors", None if packages is None else {} )
        python_paths = data.get("python_paths", None)
        
        logger.info(f"[PYTHON_PATH] Received workbook_packages_update for {workbook_id}")
        logger.info(f"[PYTHON_PATH] python_paths in message: {python_paths}")
        
        self.main_window.package_manager.update_caches.emit(workbook_id, packages, package_errors, python_paths)
    
    @run_in_qt_thread
    def _handle_package_install_progress(self, data: dict):
        """Handle package_install_progress message."""
        workbook_id = data.get("workbook_id")
        package_name = data.get("package_name")
        status = data.get("status")
        error = data.get("error", "")
        
        if workbook_id and package_name and status:
            current_workbook = self.main_window.package_manager.get_current_workbook()
            if current_workbook == workbook_id:
                self.main_window.package_manager.update_package_status(package_name, status, error)
            
            if status == "installing":
                self.main_window.package_manager.log_pip_output(f"Installing {package_name}...")
            elif status == "installed":
                self.main_window.package_manager.log_pip_output(f"Successfully installed {package_name}")
            elif status == "error":
                self.main_window.package_manager.log_pip_output(f"Error installing {package_name}: {error}")
    
    @run_in_qt_thread
    def _handle_package_installation_complete(self, data: dict):
        """Handle package_installation_complete message."""
        workbook_id = data.get("workbook_id")
        message = data.get("message", "Installation complete.")
        if workbook_id:
            current_workbook = self.main_window.package_manager.get_current_workbook()
            if current_workbook == workbook_id:
                self.main_window.package_manager.log_pip_output_colored(message, "#2ECC71")
    
    @run_in_qt_thread
    def _handle_resolved_deps_response(self, data: dict):
        """Handle resolved_deps_response message."""
        workbook_id = data.get("workbook_id")
        deps = data.get("deps", [])
        if workbook_id:
            current_workbook = self.main_window.package_manager.get_current_workbook()
            if current_workbook == workbook_id:
                self.main_window.package_manager.show_resolved_deps_popup(deps)
    
    @run_in_qt_thread
    def _handle_package_paths_updated(self, data: dict):
        """Handle package_paths_updated message."""
        self.main_window._handle_package_paths_updated(data)

    @run_in_qt_thread
    def _handle_log_to_console(self, data: dict):
        """Handle stdout message."""
            
        content = data.get("content", "")
        content = content.strip('\n')

        color = data.get("color", None)
        
        if not content:
            return
        
        self.main_window.log_to_console(content,color,level=OutputLevel.DETAILED)
    
    @run_in_qt_thread
    def _handle_stdout(self, data: dict):
        """Handle stdout message."""
        
        source = data.get("source", "ide")
        if self.main_window._console_source_filter == "ide_only" and source != "ide":
            return
            
        content = data.get("content", "")
        content = content.strip('\n')
        
        if not content:
            return
        
        self.main_window.log_to_console(content,"#4daafc",level=OutputLevel.SIMPLE)

    
    @run_in_qt_thread
    def _handle_stderr(self, data: dict):
        """Handle stderr message."""
        
        source = data.get("source", "ide")
        if self.main_window._console_source_filter == "ide_only" and source != "ide":
            return
        
        content = data.get("content", "")
        content = content.strip('\n')
        
        if not content:
            return

        self.main_window.log_to_console(content,"#ff6b6b",level=OutputLevel.SIMPLE)
        
        self.main_window._show_error_light()
    
    @run_in_qt_thread
    def _handle_result_output(self, data: dict):
        """Handle result_output message."""
        
        source = data.get("source", "ide")
        if self.main_window._console_source_filter == "ide_only" and source != "ide":
            return
        
        content = data.get("content", "")
        content = content.strip('\n')
        self.main_window.log_to_console(content,"#4caf50",level=OutputLevel.SIMPLE)

    @run_in_qt_thread
    def _handle_execution_result(self, data: dict):
        """Handle execution_result message."""
        source = data.get("source", "ide")
        if self.main_window._console_source_filter == "ide_only" and source != "ide":
            return
        
        success = data.get("success", False)
        function_name = data.get("function_name", "")
        
        if success:
            if function_name:
                self.main_window.log_to_console(f"Execution completed successfully for {function_name}()", "#4caf50",level=OutputLevel.SIMPLE)
            else:
                self.main_window.log_to_console(f"Execution completed successfully", "#4caf50",level=OutputLevel.SIMPLE)
        else:
            error = data.get("error", "Unknown error")
            if function_name:
                self.main_window.log_to_console(f"Execution failed for {function_name}(): {error}", "#ff6b6b",level=OutputLevel.SIMPLE)
            else:
                self.main_window.log_to_console(f"Execution failed: {error}", "#ff6b6b",level=OutputLevel.SIMPLE)
    
    @run_in_qt_thread
    def _handle_completion_response(self, data: dict):
        """Handle completion_response message."""
        self.main_window._handle_completion_response(data)
    
    @run_in_qt_thread
    def _handle_signature_help_response(self, data: dict):
        """Handle signature_help_response message."""
        self.main_window._handle_signature_help_response(data)
    
    @run_in_qt_thread
    def _handle_hover_response(self, data: dict):
        """Handle hover_response message."""
        self.main_window._handle_hover_response(data)
    
    @run_in_qt_thread
    def _handle_diagnostic_response(self, data: dict):
        """Handle diagnostic_response message."""
        self.main_window._handle_diagnostic_response(data)
    
    @run_in_qt_thread
    def _handle_event_manager_state(self, data: dict):
        """Handle event_manager_state message."""
        workbook_id = data.get("workbook_id")
        if workbook_id:
            self.main_window.event_manager.update_state(workbook_id, data)
            logger.debug(f"[IDE] Updated event manager state for workbook: {workbook_id}")
    
    @run_in_qt_thread
    def _handle_register_handler_result(self, data: dict):
        """Handle register_handler_result message."""
        object_id = data.get("object_id")
        event_name = data.get("event_name")
        success = data.get("success", False)
        if success:
            self.main_window.log_to_console(f"Handler registered: {object_id}.{event_name}", level=OutputLevel.SIMPLE)
        else:
            self.main_window.log_to_console(f"Failed to register handler: {object_id}.{event_name}", "#ff6b6b", level=OutputLevel.SIMPLE)
    
    @run_in_qt_thread
    def _handle_unregister_handler_result(self, data: dict):
        """Handle unregister_handler_result message."""
        object_id = data.get("object_id")
        event_name = data.get("event_name")
        success = data.get("success", False)
        if success:
            self.main_window.log_to_console(f"Handler unregistered: {object_id}.{event_name}", level=OutputLevel.SIMPLE)
        else:
            self.main_window.log_to_console(f"Failed to unregister handler: {object_id}.{event_name}", "#ff6b6b", level=OutputLevel.SIMPLE)
    
    @run_in_qt_thread
    def _handle_save_event_config_response(self, data: dict):
        """Handle save_event_config_response message."""
        self.main_window._handle_save_event_config_response(data)
    
    @run_in_qt_thread
    def _handle_validate_handler_response(self, data: dict):
        """Handle validate_handler_response message."""
        self.main_window._handle_validate_handler_response(data)
    
    @run_in_qt_thread
    def _handle_published_functions_state(self, data: dict):
        """Handle published_functions_state message."""
        workbook_id = data.get("workbook_id")
        functions = data.get("functions", [])
        if workbook_id:
            self.main_window.function_publisher.update_publications_from_server(workbook_id, functions)
            logger.debug(f"[IDE] Updated published functions for workbook: {workbook_id}")
    
    @run_in_qt_thread
    def _handle_object_registry_update(self, data: dict):
        """Handle object_registry_update message."""
        workbook_id = data.get("workbook_id")
        action = data.get("action")
        if workbook_id and action:
            self.main_window.object_inspector.handle_registry_update(workbook_id, action, data)
            logger.debug(f"[IDE] Handled object_registry_update: {action} for {workbook_id}")
    
    @run_in_qt_thread
    def _handle_object_registry_response(self, data: dict):
        """Handle object_registry_response message."""
        workbook_id = data.get("workbook_id")
        objects = data.get("objects", [])
        if workbook_id:
            self.main_window.object_inspector.handle_registry_response(workbook_id, objects)
            logger.debug(f"[IDE] Handled object_registry_response for {workbook_id}")
    
    @run_in_qt_thread
    def _handle_debug_paused(self, data: dict):
        """Handle debug_paused message."""
        self.main_window._handle_debug_paused(data)
        workbook_id = data.get("workbook_id")
        if not self.main_window._debug_active and workbook_id:
            self.main_window._set_debug_state(True, workbook_id)
    
    @run_in_qt_thread
    def _handle_debug_exception(self, data: dict):
        """Handle debug_exception message."""
        self.main_window._handle_debug_exception(data)
    
    @run_in_qt_thread
    def _handle_debug_resumed(self, data: dict):
        """Handle debug_resumed message."""
        self.main_window._handle_debug_resumed(data)
    
    @run_in_qt_thread
    def _handle_debug_terminated(self, data: dict):
        """Handle debug_terminated message."""
        self.main_window._handle_debug_terminated(data)
    
    @run_in_qt_thread
    def _handle_debug_evaluate_result(self, data: dict):
        """Handle debug_evaluate_result message."""
        self.main_window._handle_debug_evaluate_result(data)
    
    @run_in_qt_thread
    def _handle_all_settings_response(self, data: dict):
        """Handle all_settings_response message."""
        self.main_window._handle_all_settings_response(data)
    
    @run_in_qt_thread
    def _handle_settings_response(self, data: dict):
        """Handle settings_response message."""
        self.main_window._handle_settings_response(data)
    
    @run_in_qt_thread
    def _handle_setting_saved(self, data: dict):
        """Handle setting_saved message."""
        logger.debug("[IDE] Setting saved successfully")

    @run_in_qt_thread
    def _handle_show_ide(self, data: dict):
        """Handle show_ide message from business layer."""
        logger.info("[IDE] Received show_ide message")
        self.main_window.show_and_focus()

    @run_in_qt_thread
    def _handle_watchdog_info(self, data: dict):
        """Handle watchdog_info message from business layer."""
        watchdog_port = data.get("watchdog_port", 0)
        auth_token = data.get("auth_token", "")
        self.main_window.watchdog_port = watchdog_port
        self.main_window.auth_token = auth_token
        logger.info(f"[IDE] Received watchdog info: port={watchdog_port}")

    @run_in_qt_thread
    def _handle_message_ide(self, data: dict):
        """Handle message_ide message from business layer."""
        message = data.get("message", "")
        from_client = data.get("from_client", "Unknown")
        
        # Ensure message is a string for logging
        message_str = str(message) if message is not None else ""
        logger.info(f"[IDE] Received message_ide from {from_client}: {message_str[:50]}...")
        
        # Show popup with the message
        msg_box = QMessageBox(self.main_window)
        msg_box.setWindowTitle("Message from Addin")
        msg_box.setText(message_str)
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
