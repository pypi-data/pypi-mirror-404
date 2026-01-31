"""
XPyCode IDE - Monaco Editor

This module provides the Monaco Editor widget for the XPyCode IDE,
using PySide6.QtWebEngineWidgets.QWebEngineView to embed the Monaco Editor.
"""

import json
import logging
import os
from typing import Optional
from PySide6.QtCore import Qt, QUrl, Slot, Signal, QObject, QTimer
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebChannel import QWebChannel

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)



class MonacoEditorBridge(QObject):
    """Bridge object for communication between Python and JavaScript."""
    
    # Signal to emit JavaScript errors for debugging
    jsError = Signal(str)
    # Signal emitted when the editor is ready
    ready = Signal()
    # Signal emitted when content changes (from JavaScript)
    contentChanged = Signal(str)
    # Signal emitted when completion request is received (from JavaScript)
    completionRequested = Signal(str)
    # Signal emitted when signature help request is received (from JavaScript)
    signatureHelpRequested = Signal(str)
    # Signal emitted when hover request is received (from JavaScript)
    hoverRequested = Signal(str)
    # Signal emitted when diagnostic request is received (from JavaScript)
    diagnosticRequested = Signal(str)
    # Signal emitted when breakpoint positions change (from JavaScript)
    breakpointsChanged = Signal(str)  # JSON string of {oldLine: newLine}
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._ready = False
    
    @Slot()
    def editorReady(self):
        """Called when the Monaco editor is fully initialized."""
        self._ready = True
        self.ready.emit()
    
    @Slot(str)
    def onContentChanged(self, content: str):
        """Called from JavaScript when editor content changes (debounced)."""
        logger.debug(f"[Monaco Bridge] onContentChanged received, content_length={len(content) if content else 0}")
        self.contentChanged.emit(content)
    
    @Slot(str)
    def getCompletions(self, request_json: str):
        """
        Called from JavaScript to request code completions.
        
        The request is passed to Python for processing via LSPBridge.
        Args:
            request_json: JSON string containing:
                - code: The source code
                - line: 1-based line number
                - column: 0-based column number
                - request_id: Unique request identifier
        """
        logger.debug(f"[LSP] Completion request received from JS: {request_json[:200]}...")
        self.completionRequested.emit(request_json)
    
    @Slot(str)
    def getSignatureHelp(self, request_json: str):
        """
        Called from JavaScript to request signature help.
        
        The request is passed to Python for processing via LSPBridge.
        Args:
            request_json: JSON string containing:
                - code: The source code
                - line: 1-based line number
                - column: 0-based column number
                - request_id: Unique request identifier
        """
        logger.debug(f"[LSP] Signature help request received from JS: {request_json[:200]}...")
        self.signatureHelpRequested.emit(request_json)
    
    @Slot(str)
    def getHover(self, request_json: str):
        """
        Called from JavaScript to request hover information.
        
        The request is passed to Python for processing via LSPBridge.
        Args:
            request_json: JSON string containing:
                - code: The source code
                - line: 1-based line number
                - column: 0-based column number
                - request_id: Unique request identifier
        """
        logger.debug(f"[LSP] Hover request received from JS: {request_json[:200]}...")
        self.hoverRequested.emit(request_json)
    
    @Slot(str)
    def getDiagnostics(self, request_json: str):
        """
        Called from JavaScript to request diagnostics.
        
        The request is passed to Python for processing via LSPBridge.
        Args:
            request_json: JSON string containing:
                - code: The source code
                - request_id: Unique request identifier
        """
        logger.debug(f"[LSP] Diagnostic request received from JS: {request_json[:200]}...")
        self.diagnosticRequested.emit(request_json)
    
    @Slot(str)
    def reportError(self, error_msg: str):
        """Called from JavaScript when an error occurs."""
        logger.error("[Monaco JS Error]: %s", error_msg)
        self.jsError.emit(error_msg)
    
    @Slot(str)
    def logDebug(self, msg: str):
        """Called from JavaScript for debug logging."""
        logger.debug("[Monaco Debug]: %s", msg)
    
    @Slot(str)
    def onBreakpointsChanged(self, changes_json: str):
        """Called when breakpoint positions change due to line insertions/deletions."""
        logger.debug(f"[Monaco Bridge] onBreakpointsChanged received: {changes_json}")
        self.breakpointsChanged.emit(changes_json)
    
    @property
    def is_ready(self) -> bool:
        """Check if the editor is ready."""
        return self._ready


class MonacoEditor(QWebEngineView):
    """
    Monaco Editor widget for editing Python code and modules.
    
    Uses QWebEngineView to embed the Monaco Editor JavaScript library.
    """
    
    # Delay in milliseconds before resetting programmatic text flag
    # This allows time for Monaco's setValue() and event handlers to complete
    PROGRAMMATIC_SET_DELAY_MS = 100
    
    # Signal emitted when content changes (debounced from JavaScript)
    contentChanged = Signal(str)
    # Signal emitted when completion is requested (from JavaScript)
    completionRequested = Signal(str)
    # Signal emitted when signature help is requested (from JavaScript)
    signatureHelpRequested = Signal(str)
    # Signal emitted when hover is requested (from JavaScript)
    hoverRequested = Signal(str)
    # Signal emitted when diagnostics are requested (from JavaScript)
    diagnosticRequested = Signal(str)
    # Signal emitted when breakpoint positions change (from JavaScript)
    breakpointsChanged = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("monacoEditor")
        self._workbook_id: Optional[str] = None
        self._pending_text: Optional[str] = None
        # Flag to suppress contentChanged during programmatic text setting
        self._setting_text_programmatically: bool = False
        # Flag to indicate if initial text has been set (editor initialized with content)
        self._is_initialized: bool = False
        self._bridge = MonacoEditorBridge(self)
        self._configure_settings()
        self._setup_channel()
        self._load_editor()
        self._setup_focus()
        # Connect to ready signal to apply pending text when editor is ready
        self._bridge.ready.connect(self._on_editor_ready)
        # Connect to content changed signal from the bridge
        self._bridge.contentChanged.connect(self._on_bridge_content_changed)
        # Connect to completion requested signal from the bridge
        self._bridge.completionRequested.connect(self._on_completion_requested)
        # Connect to signature help requested signal from the bridge
        self._bridge.signatureHelpRequested.connect(self._on_signature_help_requested)
        # Connect to hover requested signal from the bridge
        self._bridge.hoverRequested.connect(self._on_hover_requested)
        # Connect to diagnostic requested signal from the bridge
        self._bridge.diagnosticRequested.connect(self._on_diagnostic_requested)
        # Connect to breakpoints changed signal from the bridge
        self._bridge.breakpointsChanged.connect(self._on_breakpoints_changed)
        # Cache for JavaScript to execute when ready
        self._pendingJavascript=[]
        
    def _runSecuredJavaScriptWithCallBack(self,script:str, callback):
        js_safe_code=f"(function(){{ return JSON.stringify({script}); }})();"
        self.page().runJavaScript(js_safe_code, lambda result: callback(json.loads(result) if result else None))


    def runJavaScript(self,script:str):
        if self._bridge.is_ready:
            self.page().runJavaScript(script)            
        else:
            self._pendingJavascript.append(script)

    @property
    def workbook_id(self) -> Optional[str]:
        """Get the workbook ID associated with this editor."""
        return self._workbook_id

    @workbook_id.setter
    def workbook_id(self, value: Optional[str]):
        """Set the workbook ID associated with this editor."""
        self._workbook_id = value

    def _configure_settings(self):
        """Configure QWebEngineSettings for the editor."""
        settings = self.page().settings()
        # Allow local content to access remote URLs (needed for Monaco CDN)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True
        )
        # Enable JavaScript (should be on by default, but ensure it)
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptEnabled, True
        )
        # Enable JavaScript access to clipboard
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanAccessClipboard, True
        )
        # Allow JavaScript to paste from clipboard
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.JavascriptCanPaste, True
        )
        # Enable local storage for Monaco settings
        settings.setAttribute(
            QWebEngineSettings.WebAttribute.LocalStorageEnabled, True
        )

    def _setup_focus(self):
        """Configure focus behavior for the editor widget."""
        # Set strong focus policy to accept keyboard input
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

    def _setup_channel(self):
        """Setup the web channel for Python-JavaScript communication."""
        self._channel = QWebChannel(self)
        self._channel.registerObject("pyBridge", self._bridge)
        self.page().setWebChannel(self._channel)

    def _load_editor(self):
        """Load the Monaco Editor HTML file."""
        html_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "resources",
            "monaco_editor.html"
        )
        self.load(QUrl.fromLocalFile(html_path))

    def get_text_sync(self, callback):
        """
        Get the text content asynchronously with a callback.
        
        This is the primary method for retrieving editor content since
        JavaScript execution is inherently asynchronous.
        
        Args:
            callback: Function to call with the text content.
        """
        self._runSecuredJavaScriptWithCallBack("getText()", callback)

    def set_text(self, text: str):
        """
        Set the text content of the editor.
        
        If the editor is not yet ready, the text is stored and will be
        applied when the editor becomes ready.
        
        The contentChanged signal is suppressed when setting text
        programmatically to prevent cache overwrites during initialization.
        
        Args:
            text: The text to set.
        """
        logger.debug(f"[MonacoEditor] set_text called, is_ready={self._bridge.is_ready}, text_length={len(text) if text else 0}")
        if self._bridge.is_ready:
            # Editor is ready, execute JavaScript immediately
            # Set flag to suppress contentChanged during programmatic set
            self._setting_text_programmatically = True
            escaped_text = json.dumps(text)
            self.page().runJavaScript(f"setText({escaped_text})")
            # Mark as initialized after first successful text set
            self._is_initialized = True
            # Reset flag after a short delay to allow the setText operation to complete
            QTimer.singleShot(self.PROGRAMMATIC_SET_DELAY_MS, self._reset_programmatic_flag)
            logger.debug("[MonacoEditor] Text set via JavaScript, _setting_text_programmatically=True")
        else:
            # Editor not ready yet, store text for later
            self._pending_text = text
            logger.debug("[MonacoEditor] Editor not ready, text queued as pending")

    def clear(self):
        """Clear the editor content."""
        self.runJavaScript("clearText()")

    def _reset_programmatic_flag(self):
        """Reset the programmatic text setting flag."""
        self._setting_text_programmatically = False
        logger.debug("[MonacoEditor] Reset _setting_text_programmatically to False")

    def set_language(self, language: str):
        """
        Set the editor language mode.
        
        Args:
            language: The language identifier (e.g., 'python', 'javascript').
        """
        escaped_language = json.dumps(language)
        self.runJavaScript(f"setLanguage({escaped_language})")

    def set_theme(self, theme: str):
        """
        Set the editor theme.
        
        Args:
            theme: The theme identifier (e.g., 'vs-dark', 'vs-light').
        """
        escaped_theme = json.dumps(theme)
        self.runJavaScript(f"setTheme({escaped_theme})")

    def get_selected_text(self, callback):
        """
        Get the selected text asynchronously.
        
        Args:
            callback: Function to call with the selected text.
        """
        self._runSecuredJavaScriptWithCallBack("getSelectedText()", callback)

    def get_cursor_position(self, callback):
        """
        Get the current cursor position asynchronously.
        
        Args:
            callback: Function to call with the cursor position dict
                      containing 'lineNumber' (1-based) and 'column' (1-based).
        """
        self._runSecuredJavaScriptWithCallBack("getCursorPosition()", callback)

    def insert_text_at_cursor(self, text: str):
        """
        Insert text at the current cursor position.
        
        Args:
            text: The text to insert.
        """
        escaped_text = json.dumps(text)
        self.runJavaScript(f"insertTextAtCursor({escaped_text})")

    def focus_editor(self):
        """Focus the Monaco editor to accept keyboard input."""
        self.setFocus()
        self.runJavaScript("focusEditor()")
    
    def set_readonly(self, readonly: bool):
        """
        Set the editor's readonly state.
        
        Args:
            readonly: True to make the editor readonly, False to make it editable.
        """
        readonly_str = "true" if readonly else "false"
        js_code = f"editor.updateOptions({{ readOnly: {readonly_str} }})"
        self.runJavaScript(js_code)
        logger.debug(f"[MonacoEditor] Set readonly to {readonly}")
    
    def set_minimap_visible(self, visible: bool):
        """
        Set the minimap visibility.
        
        Args:
            visible: True to show the minimap, False to hide it.
        """
        enabled_str = "true" if visible else "false"
        js_code = f"editor.updateOptions({{ minimap: {{ enabled: {enabled_str} }} }})"
        self.runJavaScript(js_code)
        logger.debug(f"[MonacoEditor] Set minimap visible to {visible}")
    
    def set_font_size(self, font_size: int):
        """
        Set the editor font size.
        
        Args:
            font_size: Font size in pixels (typically 8-24).
        """
        js_code = f"editor.updateOptions({{ fontSize: {font_size} }})"
        self.runJavaScript(js_code)
        logger.debug(f"[MonacoEditor] Set font size to {font_size}")
    

    def set_insert_spaces(self, insert_spaces: bool):
        """
        Set whether to insert spaces when pressing Tab.
        
        Args:
            insert_spaces: True to insert spaces, False to insert tabs.
        """
        enabled_str = "true" if insert_spaces else "false"
        js_code = f"editor.updateOptions({{ insertSpaces: {enabled_str} }})"
        self.runJavaScript(js_code)
        js_code = f"editor.getModel().updateOptions({{ insertSpaces: {enabled_str} }})"
        self.runJavaScript(js_code)
        logger.debug(f"[MonacoEditor] Set insert spaces to {insert_spaces}")
    
    def set_tab_size(self, tab_size: int):
        """
        Set the tab size (number of spaces per tab).
        
        Args:
            tab_size: Number of spaces (typically 2-8).
        """
        js_code = f"editor.updateOptions({{ tabSize: {tab_size} }})"
        self.runJavaScript(js_code)
        js_code = f"editor.getModel().updateOptions({{ tabSize: {tab_size} }})"
        self.runJavaScript(js_code)
        logger.debug(f"[MonacoEditor] Set tab size to {tab_size}")
    
    def set_word_wrap(self, enabled: bool):
        """
        Enable or disable word wrap.
        
        Args:
            enabled: True to enable word wrap, False to disable.
        """
        wrap_value = "'on'" if enabled else "'off'"
        js_code = f"editor.updateOptions({{ wordWrap: {wrap_value} }})"
        self.runJavaScript(js_code)
        logger.debug(f"[MonacoEditor] Set word wrap to {enabled}")
    
    def add_breakpoint(self, line: int):
        """Add a breakpoint decoration at the specified line."""
        if not isinstance(line, int) or line < 1:
            logger.warning(f"[MonacoEditor] Invalid line number for breakpoint: {line}")
            return
        js_code = f"addBreakpoint({line})"
        self.runJavaScript(js_code)
    
    def remove_breakpoint(self, line: int):
        """Remove a breakpoint decoration from the specified line."""
        if not isinstance(line, int) or line < 1:
            logger.warning(f"[MonacoEditor] Invalid line number for breakpoint removal: {line}")
            return
        js_code = f"removeBreakpoint({line})"
        self.runJavaScript(js_code)
    
    def clear_all_breakpoints(self):
        """Clear all breakpoint decorations."""
        self.runJavaScript("clearAllBreakpoints()")
    
    def set_debug_line(self, line: int):
        """
        Highlight the current debug line.
        
        Args:
            line: Line number to highlight (1-based).
        """
        if not isinstance(line, int) or line < 1:
            logger.warning(f"[MonacoEditor] Invalid line number for debug highlight: {line}")
            return
        js_code = f"setDebugLine({line})"
        self.runJavaScript(js_code)
        logger.debug(f"[MonacoEditor] Set debug line to {line}")
    
    def clear_debug_line(self):
        """Clear the debug line highlight."""
        self.runJavaScript("clearDebugLine()")
        logger.debug("[MonacoEditor] Cleared debug line")
    
    def set_error_line(self, line: int):
        """
        Highlight a line as an error (red background).
        
        Args:
            line: 1-based line number to highlight as error
        """
        if not isinstance(line, int) or line < 1:
            logger.warning(f"[MonacoEditor] Invalid line number for error highlight: {line}")
            return
        self.runJavaScript(f"window.setErrorLine({line})")
        logger.debug(f"[MonacoEditor] Set error line to {line}")
    
    def clear_error_line(self):
        """Clear the error line highlight."""
        self.runJavaScript("window.clearErrorLine()")
        logger.debug("[MonacoEditor] Cleared error line")

    def _on_editor_ready(self):
        """Called when the editor is ready. Applies pending text if any."""
        logger.debug(f"[MonacoEditor] editorReady received, _pending_text={'set' if self._pending_text is not None else 'None'}")


        if self._pending_text is not None:
            text = self._pending_text
            self._pending_text = None
            logger.debug(f"[MonacoEditor] Applying pending text, length={len(text)}")
            self.set_text(text)
        else:
            # No pending text means editor was created without initial content
            # Mark as initialized with empty content
            self._is_initialized = True
            logger.debug("[MonacoEditor] No pending text, marking as initialized")

        while self._pendingJavascript:
            script=self._pendingJavascript.pop(0)
            self.page().runJavaScript(script)


    def _on_bridge_content_changed(self, content: str):
        """
        Handle content changes from the JavaScript bridge.
        
        Filters out changes that occur during programmatic text setting
        to prevent cache overwrites during initialization.
        
        Args:
            content: The new content from the editor.
        """
        # Suppress content changes during programmatic text setting
        if self._setting_text_programmatically:
            logger.debug("[MonacoEditor] Ignoring content change during programmatic set")
            return
        
        # Only emit if editor is initialized
        if not self._is_initialized:
            logger.debug("[MonacoEditor] Ignoring content change before initialization")
            return
        
        logger.debug(f"[MonacoEditor] Content changed, emitting signal, content_length={len(content)}")
        self.contentChanged.emit(content)

    def _on_completion_requested(self, request_json: str):
        """
        Handle completion request from the JavaScript bridge.
        
        Emits the completionRequested signal for the main window to handle.
        
        Args:
            request_json: JSON string containing the completion request.
        """
        logger.debug(f"[LSP] Forwarding completion request, length={len(request_json)}")
        self.completionRequested.emit(request_json)

    def _on_signature_help_requested(self, request_json: str):
        """
        Handle signature help request from the JavaScript bridge.
        
        Emits the signatureHelpRequested signal for the main window to handle.
        
        Args:
            request_json: JSON string containing the signature help request.
        """
        logger.debug(f"[LSP] Forwarding signature help request, length={len(request_json)}")
        self.signatureHelpRequested.emit(request_json)

    def _on_hover_requested(self, request_json: str):
        """
        Handle hover request from the JavaScript bridge.
        
        Emits the hoverRequested signal for the main window to handle.
        
        Args:
            request_json: JSON string containing the hover request.
        """
        logger.debug(f"[LSP] Forwarding hover request, length={len(request_json)}")
        self.hoverRequested.emit(request_json)

    def _on_diagnostic_requested(self, request_json: str):
        """
        Handle diagnostic request from the JavaScript bridge.
        
        Emits the diagnosticRequested signal for the main window to handle.
        
        Args:
            request_json: JSON string containing the diagnostic request.
        """
        logger.debug(f"[LSP] Forwarding diagnostic request, length={len(request_json)}")
        self.diagnosticRequested.emit(request_json)
    
    def _on_breakpoints_changed(self, changes_json: str):
        """
        Handle breakpoint position changes from the JavaScript bridge.
        
        Emits the breakpointsChanged signal for the main window to handle.
        
        Args:
            changes_json: JSON string of {oldLine: newLine} mappings.
        """
        logger.debug(f"[Monaco] Forwarding breakpoints changed: {changes_json}")
        self.breakpointsChanged.emit(changes_json)

    def send_completion_response(self, response: dict):
        """
        Send a completion response back to the JavaScript editor.
        
        Args:
            response: Dictionary containing:
                - completions: List of completion items
                - error: Optional error message
        """
        response_json = json.dumps(response)
        logger.debug(f"[LSP] Sending completion response to JS: {len(response.get('completions', []))} items")
        js_code = f"handleCompletionResponse({response_json})"
        self.runJavaScript(js_code)

    def send_signature_help_response(self, response: dict):
        """
        Send a signature help response back to the JavaScript editor.
        
        Args:
            response: Dictionary containing:
                - signatures: List of signature information
                - activeSignature: Index of the active signature
                - activeParameter: Index of the active parameter
                - error: Optional error message
        """
        response_json = json.dumps(response)
        logger.debug(f"[LSP] Sending signature help response to JS: {len(response.get('signatures', []))} signatures")
        js_code = f"handleSignatureHelpResponse({response_json})"
        self.runJavaScript(js_code)

    def send_hover_response(self, response: dict):
        """
        Send a hover response back to the JavaScript editor.
        
        Args:
            response: Dictionary containing:
                - contents: Hover content as markdown or plain text
                - error: Optional error message
        """
        response_json = json.dumps(response)
        logger.debug(f"[LSP] Sending hover response to JS: has_contents={response.get('contents') is not None}")
        js_code = f"handleHoverResponse({response_json})"
        self.page().runJavaScript(js_code)

    def send_diagnostic_response(self, response: dict):
        """
        Send a diagnostic response back to the JavaScript editor.
        
        Args:
            response: Dictionary containing:
                - diagnostics: List of diagnostic objects
                - error: Optional error message
        """
        response_json = json.dumps(response)
        logger.debug(f"[LSP] Sending diagnostic response to JS: {len(response.get('diagnostics', []))} diagnostics")
        js_code = f"handleDiagnosticResponse({response_json})"
        self.runJavaScript(js_code)

    @property
    def is_initialized(self) -> bool:
        """Check if the editor has been initialized with content."""
        return self._is_initialized
