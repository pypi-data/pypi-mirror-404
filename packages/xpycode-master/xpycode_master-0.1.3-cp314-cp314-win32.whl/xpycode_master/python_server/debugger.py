"""
XPyCode Debugger - Python debugger using bdb module.

This module provides a debugger for XPyCode that supports:
- Setting breakpoints
- Step over/into/out
- Pausing at breakpoints
- Evaluating expressions in paused context
- Sending debug state to IDE
"""

import asyncio
import bdb
import inspect
import logging
import os
import sys
import threading
import time
import traceback
import types
from typing import Dict, Any, Optional, List, Callable

from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class XPyCodeDebugger(bdb.Bdb):
    """
    Custom debugger using Python's bdb module.
    
    Supports breakpoints, stepping, and variable inspection.
    """
    
    def __init__(self, send_message_callback: Callable, workbook_id: str = ""):
        """
        Initialize the debugger.
        
        Args:
            send_message_callback: Async callback to send messages to IDE.
                Should accept a dict message parameter.
            workbook_id: Workbook ID for message routing (optional).
            
        Raises:
            TypeError: If send_message_callback is not callable
        """
        super().__init__()
        
        # Validate callback parameter
        if not callable(send_message_callback):
            raise TypeError("send_message_callback must be a callable function")
        
        self.send_message_callback = send_message_callback
        self.workbook_id = workbook_id
        self.breakpoints: Dict[str, List[int]] = {}  # {module_name: [line_numbers]}
        self.paused = False
        self.step_mode = None  # None, 'over', 'into', 'out'
        self.current_frame = None
        
        # Threading Note: threading.Event is used instead of asyncio.Event because
        # the debugger runs in a worker thread, not the async event loop.
        # The event allows the worker thread to block while waiting for continue/step commands.
        self.continue_event = threading.Event()
        self.loop = None  # Will be set when running for async message sending
        self.in_memory_modules = set()  # Set of in-memory module names (user code)
        self._returning_from_external = False  # Flag for returning from external code
        
    def set_breakpoints(self, breakpoints: List[Dict[str, Any]]):
        """
        Set breakpoints for the debug session.
        
        Args:
            breakpoints: List of breakpoint dicts with 'module' and 'line' keys.
        """
        logger.info(f"[Debugger] Received breakpoints to set: {breakpoints}")
        self.breakpoints.clear()
        for bp in breakpoints:
            module = bp.get("module")
            line = bp.get("line")
            if module and line:
                if module not in self.breakpoints:
                    self.breakpoints[module] = []
                self.breakpoints[module].append(line)
        logger.info(f"[Debugger] Set breakpoints: {self.breakpoints}")
    
    def set_in_memory_modules(self, modules: List[str]):
        """
        Set the list of in-memory module names (user code).
        
        Args:
            modules: List of in-memory module names
        """
        self.in_memory_modules = set(modules)
        logger.info(f"[Debugger] Set in-memory modules: {self.in_memory_modules}")
    
    def user_line(self, frame):
        """
        Called when debugger stops at a line.
        
        This is the core bdb hook that gets called when stepping or hitting breakpoints.
        """
        if self.paused:
            return  # Already paused, don't re-trigger
        
        # Extract information about current position
        filename = frame.f_code.co_filename
        line = frame.f_lineno
        module_name = self._get_module_name(frame)
        
        # Add diagnostic logging
        logger.debug(f"[Debugger] user_line called: module={module_name}, line={line}, "
                     f"step_mode={self.step_mode}, returning_from_external={self._returning_from_external}, "
                     f"is_in_memory={self._is_in_memory_module(module_name)}")
        
        # Skip modules that are not in-memory (external packages)
        if not self._is_in_memory_module(module_name):
            # ALWAYS set up fast-return from external modules
            # This prevents stepping through every line of external code
            # regardless of whether we're in step mode or running to a breakpoint
            self.set_return(frame)
            self._returning_from_external = True
            logger.debug(f"[Debugger] Set return from external module: {module_name}, waiting for return to user code")
            return

        # Only debug log for in-memory modules
        # Note: debug logs are commented out as they would trigger for each line executed
        # Uncomment for detailed debugging if needed:
        # logger.debug(f"[Debugger] user_line: {module_name}:{line}, breakpoints={self.breakpoints}")
        
        # Check if we should pause here
        should_pause = False
        
        # Check breakpoints - try exact match first
        if module_name in self.breakpoints and line in self.breakpoints[module_name]:
            should_pause = True
            logger.info(f"[Debugger] Hit breakpoint at {module_name}:{line}")
        
        # If no exact match, try fuzzy matching for breakpoints
        # This handles cases where IDE sends "main" but debugger sees "__main__"
        if not should_pause:
            for bp_module, bp_lines in self.breakpoints.items():
                if line in bp_lines:
                    # Check if module names are similar
                    if (bp_module in module_name or module_name in bp_module or
                        bp_module.split('.')[-1] == module_name.split('.')[-1]):
                        should_pause = True
                        logger.info(f"[Debugger] Hit breakpoint (fuzzy match) at {module_name}:{line} (bp_module={bp_module})")
                        break
        
        # Check step mode
        if self.step_mode:
            should_pause = True
            logger.info(f"[Debugger] Step mode '{self.step_mode}' at {module_name}:{line}")
            self.step_mode = None  # Clear step mode after pause
        
        if should_pause:
            self.current_frame = frame
            self.paused = True
            
            # Send debug_paused message to IDE
            if self.loop:
                try:
                    asyncio.run_coroutine_threadsafe(
                        self._send_paused_state(module_name, line, frame),
                        self.loop
                    )
                except Exception as e:
                    logger.error(f"[Debugger] Failed to send debug_paused message: {e}")
            
            # Wait for continue command
            # Threading Note: This is a synchronous blocking wait using threading.Event.
            # The debugger runs in a worker thread, so blocking here does not affect
            # the listener thread which continues processing WebSocket messages.
            # The listener thread will call continue_event.set() when it receives
            # a debug command (continue, step, stop) from the IDE.
            self.continue_event.clear()
            # Block execution until debugger is continued
            # Note: This is a synchronous wait in the debugger thread using threading.Event
            self.continue_event.wait()
            
            self.paused = False
    
    def user_return(self, frame, return_value):
        """Called when a function returns."""
        # For step out functionality
        if self.step_mode == 'out':
            self.step_mode = None
            # Will pause at next line in caller
    
    def user_exception(self, frame, exc_info):
        """Called when an exception occurs."""
        module_name = self._get_module_name(frame)
        
        # Only handle exceptions in in-memory modules
        if not self._is_in_memory_module(module_name):
            return
        
        exc_type, exc_value, exc_tb = exc_info
        line = frame.f_lineno
        
        logger.error(f"[Debugger] Exception in {module_name}:{line}: {exc_value}")
        
        # Pause at exception and notify IDE
        self.current_frame = frame
        self.paused = True
        
        # Send debug_exception message to IDE
        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send_exception_state(module_name, line, frame, exc_info),
                self.loop
            )
        
        # Wait for user to continue/stop
        self.continue_event.clear()
        self.continue_event.wait()
        self.paused = False
    
    def _get_module_name(self, frame) -> str:
        """Extract module name from frame."""
        # Try to get module name from frame globals
        module = frame.f_globals.get('__name__', '')
        if module:
            return module
        
        # Fallback to filename
        filename = frame.f_code.co_filename
        if filename.endswith('.py'):
            # Extract module name from filename
            return os.path.basename(filename)[:-3]
        
        return filename
    
    def _is_in_memory_module(self, module_name: str) -> bool:
        """
        Check if module is an in-memory module (user code).
        
        Args:
            module_name: Module name to check
            
        Returns:
            True if module is in-memory (user code), False otherwise
        """
        # Check if module name is in our known in-memory modules
        return module_name in self.in_memory_modules
    

    async def _send_paused_state(self, module_name: str, line: int, frame):
        """
        Send debug_paused message with current state.
        
        Args:
            module_name: Current module name
            line: Current line number
            frame: Current stack frame
        """
        # Extract locals and globals (limit size to avoid huge messages)
        locals_dict = self._serialize_variables(frame.f_locals)
        globals_dict = self._serialize_variables(frame.f_globals, limit=20)
        
        # Build call stack
        call_stack = self._build_call_stack(frame)
        
        message = {
            "type": "debug_paused",
            "module": module_name,
            "line": line,
            "locals": locals_dict,
            "globals": globals_dict,
            "call_stack": call_stack,
        }
        
        # Include workbook_id if available
        if self.workbook_id:
            message["workbook_id"] = self.workbook_id
        
        await self.send_message_callback(message)
    
    async def _send_exception_state(self, module_name: str, line: int, frame, exc_info):
        """
        Send exception state to IDE.
        
        Args:
            module_name: Module name where exception occurred
            line: Line number where exception occurred
            frame: Current stack frame
            exc_info: Exception info tuple (exc_type, exc_value, exc_tb)
        """
        exc_type, exc_value, exc_tb = exc_info
        
        # Get exception details
        exception_type = exc_type.__name__ if exc_type else "Exception"
        exception_message = str(exc_value) if exc_value else "Unknown error"
        exception_traceback = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
        
        # Get local variables and call stack
        locals_list = self._serialize_variables(frame.f_locals)
        globals_list = self._serialize_variables(frame.f_globals)
        call_stack = self._build_call_stack(frame)
        
        message = {
            "type": "debug_exception",
            "workbook_id": self.workbook_id,
            "module": module_name,
            "line": line,
            "file": frame.f_code.co_filename,
            "exception_type": exception_type,
            "exception_message": exception_message,
            "exception_traceback": exception_traceback,
            "locals": locals_list,
            "globals": globals_list,
            "call_stack": call_stack,
        }
        
        await self.send_message_callback(message)
    
    def _serialize_variables(self, vars_dict: Dict, limit: int = 50) -> List[Dict]:
        """
        Serialize variables for transmission to IDE.
        
        Args:
            vars_dict: Dictionary of variables
            limit: Maximum number of variables to include
            
        Returns:
            List of {name, type, value, repr} dicts
        """
        result = []
        count = 0
        
        # Filter out internal variables
        for name, value in vars_dict.items():
            if name.startswith('__') and name.endswith('__'):
                continue
            
            try:
                result.append({
                    "name": name,
                    "type": type(value).__name__,
                    "value": str(value)[:200],  # Limit value length
                    "repr": repr(value)[:200],
                })
                count += 1
                if count >= limit:
                    break
            except Exception as e:
                logger.debug(f"[Debugger] Error serializing variable {name}: {e}")
        
        return result
    
    def _build_call_stack(self, frame) -> List[Dict]:
        """
        Build call stack from current frame.
        
        Returns:
            List of {module, function, line, file} dicts (only in-memory modules)
        """
        stack = []
        current = frame
        
        while current is not None:
            module_name = self._get_module_name(current)
            
            # Only include in-memory modules in call stack
            if self._is_in_memory_module(module_name):
                function_name = current.f_code.co_name
                line = current.f_lineno
                filename = current.f_code.co_filename
                
                stack.append({
                    "module": module_name,
                    "function": function_name,
                    "line": line,
                    "file": filename,
                })
            
            current = current.f_back
            
            # Limit stack depth
            if len(stack) >= 20:
                break
        
        return stack
    
    def evaluate_expression(self, expression: str, frame=None) -> Dict[str, Any]:
        """
        Evaluate an expression in the current debug context.
        
        Args:
            expression: Python expression to evaluate
            frame: Stack frame to use (defaults to current_frame)
            
        Returns:
            Dict with 'result' or 'error' key
        """
        if frame is None:
            frame = self.current_frame
        
        if not frame:
            return {"error": "No active debug frame"}
        
        try:
            # Evaluate in the context of the paused frame
            # SECURITY NOTE: Using eval() is intentional for debugging functionality.
            # This allows users to evaluate arbitrary expressions during debug sessions.
            # Security is enforced at the deployment level (container isolation, etc.)
            result = eval(expression, frame.f_globals, frame.f_locals)
            return {
                "result": str(result),
                "result_type": type(result).__name__,
                "repr": repr(result)[:500],
            }
        except Exception as e:
            return {
                "error": str(e),
                "traceback": traceback.format_exc(),
            }
    
    def continue_execution(self):
        """
        Continue execution from paused state.
        
        Threading Note: This method is called from the listener thread in response
        to a debug command. It sets the continue_event to unblock the worker thread
        that is paused in user_line() or user_exception().
        """
        logger.info("[Debugger] Continue execution")
        self.step_mode = None
        # Threading Note: event.set() is thread-safe and will wake up the worker thread
        self.continue_event.set()
    
    def step_over(self):
        """
        Step over to next line.
        
        Threading Note: This method is called from the listener thread.
        Sets the debugger to step mode and unblocks the worker thread.
        """
        logger.info("[Debugger] Step over")
        self.step_mode = 'over'
        self.set_next(self.current_frame)
        self.continue_event.set()
    
    def step_into(self):
        """
        Step into function call.
        
        Threading Note: This method is called from the listener thread.
        Sets the debugger to step mode and unblocks the worker thread.
        """
        logger.info("[Debugger] Step into")
        self.step_mode = 'into'
        self.set_step()
        self.continue_event.set()
    
    def step_out(self):
        """
        Step out of current function.
        
        Threading Note: This method is called from the listener thread.
        Sets the debugger to step mode and unblocks the worker thread.
        """
        logger.info("[Debugger] Step out")
        self.step_mode = 'out'
        self.set_return(self.current_frame)
        self.continue_event.set()
    
    def stop_debugging(self):
        """
        Stop the debugging session.
        
        Threading Note: This method is called from the listener thread.
        Stops the debugger and unblocks the worker thread.
        """
        logger.info("[Debugger] Stop debugging")
        self.set_quit()
        self.continue_event.set()
