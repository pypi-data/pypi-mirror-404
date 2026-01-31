"""
XPyCode IDE - Event Manager

This module provides the Event Manager widget for managing events
on Excel objects (Workbooks, Worksheets, Charts, Tables, etc.).

The Event Manager displays a hierarchical tree view:
- Level 1: Workbook
- Level 2: Objects (Worksheets, Tables, Charts)  
- Level 3: Available Events for each object

Users can assign Python functions to events via context menu.
"""

import ast
import logging
import re
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTreeWidget,
    QTreeWidgetItem,
    QLabel,
    QMenu,
    QInputDialog,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QLineEdit,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction, QColor, QBrush
from typing import Dict, List, Optional, Callable

from .icon_utils import get_icon_for_type, format_display_name

# Configure logging
from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)



class CreateHandlerDialog(QDialog):
    """
    Dialog for creating a new handler function.
    
    Shows headers for Object Context, Event Name, and Expected Signature,
    along with an input field for the function name.
    """
    
    def __init__(
        self,
        parent=None,
        object_name: str = "",
        object_type: str = "",
        event_type: str = "",
        default_name: str = "",
        arg_type: str = ""
    ):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent widget
            object_name: Name of the Excel object (e.g., "Sheet1")
            object_type: Type of the Excel object (e.g., "Worksheet")
            event_type: Type of the event (e.g., "SelectionChanged")
            default_name: Default function name suggestion
            arg_type: Event argument type (e.g., "xpycode.Excel.WorksheetSelectionChangedEventArgs")
        """
        super().__init__(parent)
        self.setWindowTitle("Create New Handler")
        self.setMinimumWidth(450)
        self.object_name = object_name
        self.object_type = object_type
        self.event_type = event_type
        self.arg_type = arg_type or "dict"
        self.function_name: Optional[str] = None
        self._setup_ui(default_name)
    
    def _setup_ui(self, default_name: str):
        """Setup the dialog UI with headers."""
        layout = QVBoxLayout(self)
        
        # Object Context header
        context_header = QLabel("Object Context")
        context_header.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(context_header)
        
        context_value = QLabel(f"{self.object_name} [{self.object_type}]")
        context_value.setStyleSheet("padding: 4px 0 8px 16px;")
        layout.addWidget(context_value)
        
        # Event Name header
        event_header = QLabel("Event Name")
        event_header.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(event_header)
        
        event_value = QLabel(self.event_type)
        event_value.setStyleSheet("padding: 4px 0 8px 16px;")
        layout.addWidget(event_value)
        
        # Expected Signature header
        sig_header = QLabel("Expected Signature")
        sig_header.setStyleSheet("font-weight: bold; color: #666;")
        layout.addWidget(sig_header)
        
        sig_value = QLabel(f"def handler_name(event_args: {self.arg_type}):")
        sig_value.setStyleSheet("padding: 4px 0 8px 16px; font-family: monospace; color: #888;")
        sig_value.setWordWrap(True)
        layout.addWidget(sig_value)
        
        # Function name input
        name_label = QLabel("Function Name:")
        name_label.setStyleSheet("font-weight: bold; margin-top: 8px;")
        layout.addWidget(name_label)
        
        self.name_input = QLineEdit(default_name)
        self.name_input.setPlaceholderText("Enter function name (e.g., on_sheet1_change)")
        layout.addWidget(self.name_input)
        
        # Note about where it will be created
        note_label = QLabel("(will be created in excel_events.py)")
        note_label.setStyleSheet("color: #888; font-style: italic; padding: 4px 0;")
        layout.addWidget(note_label)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self._on_accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _on_accept(self):
        """Handle OK button click."""
        self.function_name = self.name_input.text().strip()
        self.accept()
    
    def get_function_name(self) -> Optional[str]:
        """Get the entered function name."""
        return self.function_name


class FunctionSelectorDialog(QDialog):
    """
    Dialog for selecting an existing handler function from project modules.
    
    Shows a tree view with modules and their functions, along with the
    expected function signature for the event.
    """
    
    def __init__(
        self,
        parent=None,
        modules: Dict[str, str] = None,
        object_name: str = "",
        object_type: str = "",
        event_type: str = "",
        arg_type: str = ""
    ):
        """
        Initialize the dialog.
        
        Args:
            parent: Parent widget
            modules: Dictionary of {module_name: code} for available modules
            object_name: Name of the Excel object (e.g., "Sheet1")
            object_type: Type of the Excel object (e.g., "Worksheet")
            event_type: Type of the event (e.g., "SelectionChanged")
            arg_type: Event argument type (e.g., "xpycode.Excel.WorksheetSelectionChangedEventArgs")
        """
        super().__init__(parent)
        self.setWindowTitle("Select Handler Function")
        self.setMinimumSize(600, 400)
        self.modules = modules or {}
        self.object_name = object_name
        self.object_type = object_type
        self.event_type = event_type
        self.arg_type = arg_type or "dict"
        self.selected_function: Optional[str] = None
        self._setup_ui()
        self._populate_tree()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        
        # Context info at the top: Object and Event
        object_label = QLabel(f"Object: {self.object_name} [{self.object_type}]")
        object_label.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(object_label)
        
        event_label = QLabel(f"Event: {self.event_type}")
        event_label.setStyleSheet("font-weight: bold; padding: 4px;")
        layout.addWidget(event_label)
        
        # Expected signature info
        signature_text = f"Expected signature: def handler_name(event_args: {self.arg_type}):"
        signature_label = QLabel(signature_text)
        signature_label.setWordWrap(True)
        signature_label.setStyleSheet("color: #888888; font-style: italic; padding: 8px;")
        layout.addWidget(signature_label)
        
        # Splitter for modules and functions
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Modules list (left side)
        modules_widget = QWidget()
        modules_layout = QVBoxLayout(modules_widget)
        modules_layout.setContentsMargins(0, 0, 0, 0)
        modules_label = QLabel("Modules:")
        modules_layout.addWidget(modules_label)
        self.modules_list = QListWidget()
        self.modules_list.currentItemChanged.connect(self._on_module_selected)
        modules_layout.addWidget(self.modules_list)
        splitter.addWidget(modules_widget)
        
        # Functions list (right side)
        functions_widget = QWidget()
        functions_layout = QVBoxLayout(functions_widget)
        functions_layout.setContentsMargins(0, 0, 0, 0)
        functions_label = QLabel("Functions:")
        functions_layout.addWidget(functions_label)
        self.functions_list = QListWidget()
        self.functions_list.itemDoubleClicked.connect(self._on_function_double_clicked)
        self.functions_list.currentItemChanged.connect(self._on_function_selected)
        functions_layout.addWidget(self.functions_list)
        splitter.addWidget(functions_widget)
        
        splitter.setSizes([200, 400])
        layout.addWidget(splitter)
        
        # Preview/info area
        preview_label = QLabel("Function Preview:")
        layout.addWidget(preview_label)
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setMaximumHeight(100)
        self.preview_text.setStyleSheet("font-family: monospace;")
        layout.addWidget(self.preview_text)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        self.ok_button = button_box.button(QDialogButtonBox.StandardButton.Ok)
        self.ok_button.setEnabled(False)
        layout.addWidget(button_box)
    
    def _populate_tree(self):
        """Populate the modules list."""
        for module_name in sorted(self.modules.keys()):
            item = QListWidgetItem(module_name)
            item.setData(Qt.ItemDataRole.UserRole, module_name)
            self.modules_list.addItem(item)
        
        # Ensure no module is selected initially so functions list stays empty
        # until the user explicitly selects a module
        self.modules_list.clearSelection()
        self.functions_list.clear()
    
    def _on_module_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle module selection change."""
        self.functions_list.clear()
        self.preview_text.clear()
        self.selected_function = None
        self.ok_button.setEnabled(False)
        
        if not current:
            return
        
        module_name = current.data(Qt.ItemDataRole.UserRole)
        code = self.modules.get(module_name, "")
        
        # Parse functions from the module code
        functions = self._parse_functions(code)
        for func_name, func_code in functions:
            item = QListWidgetItem(func_name)
            item.setData(Qt.ItemDataRole.UserRole, {
                "module": module_name,
                "function": func_name,
                "code": func_code
            })
            self.functions_list.addItem(item)
    
    def _on_function_selected(self, current: QListWidgetItem, previous: QListWidgetItem):
        """Handle function selection change."""
        if not current:
            self.preview_text.clear()
            self.selected_function = None
            self.ok_button.setEnabled(False)
            return
        
        data = current.data(Qt.ItemDataRole.UserRole)
        if data:
            module_name = data.get("module", "")
            func_name = data.get("function", "")
            func_code = data.get("code", "")
            
            self.selected_function = f"{module_name}.{func_name}"
            self.preview_text.setText(func_code[:500])  # Show first 500 chars
            self.ok_button.setEnabled(True)
    
    def _on_function_double_clicked(self, item: QListWidgetItem):
        """Handle double-click on a function to select and accept."""
        self._on_function_selected(item, None)
        if self.selected_function:
            self.accept()
    
    def _parse_functions(self, code: str) -> List[tuple]:
        """
        Parse function definitions from Python code.
        
        Args:
            code: Python source code
            
        Returns:
            List of (function_name, function_code) tuples
        """
        functions = []
        try:
            tree = ast.parse(code)
            lines = code.split('\n')
            
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    # Get the function's start and end line
                    start_line = node.lineno - 1  # 0-indexed
                    end_line = node.end_lineno if node.end_lineno else start_line + 1
                    
                    # Extract the function code
                    func_lines = lines[start_line:end_line]
                    func_code = '\n'.join(func_lines)
                    
                    functions.append((node.name, func_code))
        except SyntaxError:
            # Fall back to regex for code with syntax errors
            pattern = re.compile(r'^def\s+(\w+)\s*\([^)]*\):', re.MULTILINE)
            for match in pattern.finditer(code):
                func_name = match.group(1)
                # Try to get a few lines of the function
                start_pos = match.start()
                end_pos = min(start_pos + 200, len(code))
                func_snippet = code[start_pos:end_pos]
                functions.append((func_name, func_snippet + "..."))
        
        return functions
    
    def get_selected_function(self) -> Optional[str]:
        """Get the selected function as 'module_name.function_name'."""
        return self.selected_function


class EventManager(QFrame):
    """
    Event Manager widget for managing events on Excel objects.
    
    Provides functionality to:
    - View a hierarchy of Excel objects (Workbooks, Worksheets, Charts, Tables)
    - View available events for each object as child nodes
    - Assign/create Python handler functions for events
    - Visual indicators for event count and missing handlers
    """

    # Signals for event operations
    # assign_handler_requested(workbook_id, object_id, object_type, event_name, function_name)
    # Updated to include object_type for proper registration
    assign_handler_requested = Signal(str, str, str, str, str)
    # create_handler_requested(workbook_id, object_id, object_type, event_name, function_name, arg_type)
    create_handler_requested = Signal(str, str, str, str, str, str, str)
    # refresh_state_requested(workbook_id)
    refresh_state_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tabMainWidget")

        # Store view_model from Business Layer: {workbook_id: view_model_list}
        self._view_models: Dict[str, list] = {}
        # Store workbook data: {workbook_id: tree structure from getWorkbookTree} - DEPRECATED, kept for compatibility
        self._workbooks: Dict[str, Dict] = {}
        # Store event definitions from Business Layer: {workbook_id: event_definitions_dict} - DEPRECATED, kept for compatibility
        self.event_definitions: Dict[str, dict] = {}
        # Store event config: {workbook_id: {"ObjectId": {"ObjectType": "...", "events": {"EventType": "python_function"}}}}
        self._event_config: Dict[str, Dict[str, Dict[str, str]]] = {}
        # Store validation results: {workbook_id: {"ObjectId:EventType": bool}}
        self._validation_results: Dict[str, Dict[str, bool]] = {}
        # Available functions for assignment: {workbook_id: [function_names]}
        self._available_functions: Dict[str, List[str]] = {}
        # Module cache for function browser: {workbook_id: {module_name: code}}
        self._module_cache: Dict[str, Dict[str, str]] = {}
        # Store workbook names: {workbook_id: name}
        self._workbook_names: Dict[str, str] = {}
        self._setup_ui()

    def _get_handler_color(self) -> str:
        """
        Get the appropriate handler color based on the current theme.
        
        Returns:
            Color string for valid assigned handlers.
        """
        # Try to get theme from main window
        try:
            main_window = self.window()
            if hasattr(main_window, '_current_app_theme'):
                # Check if it's a light theme
                if 'light' in main_window._current_app_theme.lower():
                    return "#2E7D32"  # Material Green 800 for light themes
        except Exception:
            pass
        
        # Default to lighter green for dark themes
        return "#81C784"  # Material Green 300 for dark themes

    def _setup_ui(self):
        """Setup the widget UI with split view."""
        layout = QVBoxLayout(self)
        
        # Workbook selection section
        workbook_layout = QHBoxLayout()
        workbook_label = QLabel("Workbook:")
        self.workbook_dropdown = QComboBox()
        self.workbook_dropdown.setMinimumWidth(200)
        # Use currentIndexChanged to properly handle workbook ID from UserRole
        self.workbook_dropdown.currentIndexChanged.connect(self._on_workbook_index_changed)
        workbook_layout.addWidget(workbook_label)
        workbook_layout.addWidget(self.workbook_dropdown)
        
        workbook_layout.addStretch()
        layout.addLayout(workbook_layout)
        
        # Split view: Object hierarchy on left, events on right
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left pane: Object hierarchy tree
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        tree_label = QLabel("Object Hierarchy:")
        left_layout.addWidget(tree_label)
        
        self.object_tree = QTreeWidget()
        self.object_tree.setHeaderLabels(["Object", "Info"])
        self.object_tree.setAnimated(True)
        self.object_tree.setIndentation(20)
        self.object_tree.setRootIsDecorated(True)
        self.object_tree.setAlternatingRowColors(True)
        self.object_tree.setColumnWidth(0, 200)
        # Connect selection change
        self.object_tree.currentItemChanged.connect(self._on_tree_selection_changed)
        left_layout.addWidget(self.object_tree)
        
        splitter.addWidget(left_widget)
        
        # Right pane: Events list for selected object
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        events_label = QLabel("Events:")
        right_layout.addWidget(events_label)
        
        # Use QTreeWidget for events to show columns (Event Name, Assigned Function)
        self.events_list = QTreeWidget()
        self.events_list.setHeaderLabels(["Event", "Assigned Handler"])
        self.events_list.setRootIsDecorated(False)
        self.events_list.setAlternatingRowColors(True)
        self.events_list.setColumnWidth(0, 200)
        # Enable context menu on event list
        self.events_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.events_list.customContextMenuRequested.connect(self._show_context_menu)
        # Enable double-click to assign handler
        self.events_list.itemDoubleClicked.connect(self._on_event_double_clicked)
        right_layout.addWidget(self.events_list)
        
        splitter.addWidget(right_widget)
        
        # Set initial splitter sizes (40% left, 60% right)
        splitter.setSizes([300, 450])
        
        layout.addWidget(splitter)

    def add_workbook(self, workbook_id: str, name: Optional[str] = None):
        """
        Add a workbook to the dropdown.
        
        Args:
            workbook_id: The workbook identifier
            name: Optional display name for the workbook (defaults to workbook_id)
        """
        # Check if workbook already exists using UserRole data
        for i in range(self.workbook_dropdown.count()):
            if self.workbook_dropdown.itemData(i, Qt.ItemDataRole.UserRole) == workbook_id:
                return
        
        # Use friendly name if provided, otherwise use workbook_id
        display_name = name if name else workbook_id
        self._workbook_names[workbook_id] = display_name
        self.workbook_dropdown.addItem(f"📗 {display_name}")
        # Store workbook_id in UserRole for retrieval
        self.workbook_dropdown.setItemData(
            self.workbook_dropdown.count() - 1,
            workbook_id,
            Qt.ItemDataRole.UserRole
        )
        
        # Immediately trigger refresh_state to populate the tree
        # This ensures event discovery happens as soon as workbook is added
        self.refresh_state_requested.emit(workbook_id)

    def remove_workbook(self, workbook_id: str):
        """
        Remove a workbook from the dropdown and clean up cached data.
        
        Args:
            workbook_id: The workbook identifier
        """
        # Check if this is the currently selected workbook
        current_workbook_id = self.get_current_workbook()
        was_selected = (current_workbook_id == workbook_id)
        
        # Find by UserRole data, not by display text
        for i in range(self.workbook_dropdown.count()):
            if self.workbook_dropdown.itemData(i, Qt.ItemDataRole.UserRole) == workbook_id:
                self.workbook_dropdown.removeItem(i)
                break
        
        # Clean up cached data
        self._workbooks.pop(workbook_id, None)
        self._event_config.pop(workbook_id, None)
        self._validation_results.pop(workbook_id, None)
        self._available_functions.pop(workbook_id, None)
        self._workbook_names.pop(workbook_id, None)
        
        # If it was the only workbook or the selected one was removed, clear the trees
        if self.workbook_dropdown.count() == 0:
            self.object_tree.clear()
            self.events_list.clear()
        elif was_selected and self.workbook_dropdown.count() > 0:
            # Selection will automatically change to another workbook, triggering refresh
            pass

    def update_workbook_name(self, workbook_id: str, new_name: str):
        """
        Update the display name of a workbook in the dropdown.
        
        Args:
            workbook_id: The workbook identifier
            new_name: The new display name for the workbook
        """
        for i in range(self.workbook_dropdown.count()):
            if self.workbook_dropdown.itemData(i, Qt.ItemDataRole.UserRole) == workbook_id:
                self.workbook_dropdown.setItemText(i, f"📗 {new_name}")
                break
        # Also update the cached name
        if workbook_id in self._workbook_names:
            self._workbook_names[workbook_id] = new_name

    def get_current_workbook(self) -> str:
        """
        Get the currently selected workbook.
        
        Returns:
            The workbook identifier or empty string if none selected
        """
        index = self.workbook_dropdown.currentIndex()
        if index < 0:
            return ""
        workbook_id = self.workbook_dropdown.itemData(index, Qt.ItemDataRole.UserRole)
        return workbook_id if workbook_id else ""

    def update_state(self, workbook_id: str, state: Dict):
        """
        Update the event manager state from Business Layer.
        
        This is the main method for the new event system architecture.
        Receives merged view_model from Business Layer.
        
        Args:
            workbook_id: The workbook identifier
            state: State from Business Layer containing:
                {
                    "view_model": [...]  # Merged view model with tree + events + handlers
                }
                
                OR legacy format (backward compatibility):
                {
                    "tree": {...},  # Workbook tree structure
                    "events": {...},  # Event definitions
                    "handlers": [...]  # Registered handlers list
                }
        """
        # Check if this is the new view_model format or legacy format
        view_model = state.get("view_model")
        
        if view_model is not None:
            # New format: view_model contains merged data
            self._view_models[workbook_id] = view_model
            
            # Extract workbook name from root node if available
            if view_model and len(view_model) > 0:
                root_node = view_model[0]
                workbook_name = root_node.get("name", workbook_id)
        else:
            # Legacy format: tree, events, handlers separate (for backward compatibility)
            tree_data = state.get("tree", {})
            event_definitions = state.get("events", {})
            handlers_list = state.get("handlers", [])
            
            # Store tree data
            self._workbooks[workbook_id] = tree_data
            
            # Store event definitions
            self.event_definitions[workbook_id] = event_definitions
            
            # Convert handlers list to config format for compatibility
            # handlers_list: [{"object_id": ..., "event_type": ..., "python_function": ...}, ...]
            config = {}
            for handler in handlers_list:
                object_id = handler.get("object_id", "")
                event_type = handler.get("event_type", "")
                python_function = handler.get("python_function", "")
                
                if object_id and event_type and python_function:
                    if object_id not in config:
                        config[object_id] = {"events": {}}
                    config[object_id]["events"][event_type] = python_function
            
            self._event_config[workbook_id] = config
            
            # Update the workbook name in the dropdown if we have it
            workbook_name = tree_data.get("name", workbook_id)
            if workbook_name:
                self._workbook_names[workbook_id] = workbook_name
                # Update the display name in the dropdown
                for i in range(self.workbook_dropdown.count()):
                    if self.workbook_dropdown.itemData(i, Qt.ItemDataRole.UserRole) == workbook_id:
                        self.workbook_dropdown.setItemText(i, workbook_name)
                        break
        
        # Refresh tree if this is the selected workbook (with selection preservation)
        if self.get_current_workbook() == workbook_id:
            self.refresh_tree(preserve_selection=True)

    def get_event_config(self, workbook_id: str) -> Dict[str, Dict[str, str]]:
        """
        Get the event configuration for a workbook.
        
        Args:
            workbook_id: The workbook identifier
            
        Returns:
            Event configuration: {"ObjectName": {"EventType": "python_function_name"}}
        """
        return self._event_config.get(workbook_id, {})

    def update_validation(self, workbook_id: str, object_name: str, event_type: str, is_valid: bool):
        """
        Update the validation status for a specific event handler.
        
        Args:
            workbook_id: The workbook identifier
            object_name: The Excel object name
            event_type: The event type
            is_valid: Whether the handler function is valid
        """
        if workbook_id not in self._validation_results:
            self._validation_results[workbook_id] = {}
        
        key = f"{object_name}:{event_type}"
        self._validation_results[workbook_id][key] = is_valid
        
        # Refresh tree if this is the selected workbook
        if self.get_current_workbook() == workbook_id:
            self.refresh_tree()

    def set_available_functions(self, workbook_id: str, functions: List[str]):
        """
        Set the available Python functions for handler assignment.
        
        Args:
            workbook_id: The workbook identifier
            functions: List of available function names (e.g., ["module.func1", "module.func2"])
        """
        self._available_functions[workbook_id] = functions

    def set_module_cache(self, workbook_id: str, modules: Dict[str, str]):
        """
        Set the module cache for a workbook.
        
        This enables the FunctionSelectorDialog to browse available modules
        and functions when assigning handlers.
        
        Args:
            workbook_id: The workbook identifier
            modules: Dictionary of {module_name: code}
        """
        self._module_cache[workbook_id] = modules

    def getHandlersByWorkbbokId(self)->Dict[str, List[Dict]]:
        """
        Get the current handlers by workbook ID.
        
        Returns:
            Dictionary of {workbook_id: [handler_dicts]}
        """
        handlers_by_workbook = {}
        for workbook_id, view_model in self._view_models.items():
            handlers = self._getRecursiveHandlers(view_model)
            handlers_by_workbook[workbook_id] = handlers
        return handlers_by_workbook

    def _getRecursiveHandlers(self,sub_model:List[Dict])->Dict[str, List[Dict]]:
        """
        Recursively extract handlers from the view_model structure.
        
        Args:
            sub_model: Subset of the view_model to process
        """
        rep=[]
        for node in sub_model:
            rep.extend(self._getRecursiveHandlers(node.get("children",[])))
            for event in node.get("events",[]):
                if event.get('python_function',''):
                    rep.append({
                        "object_id":node.get("id",""),
                        "event_name":event.get("name",""),
                        "python_function":event.get("python_function",""),
                        "object_name":node.get("name",""),
                        "object_type":node.get("type",""),
                    })

        return rep


    def _on_workbook_index_changed(self, index: int):
        """Handle workbook selection change by index."""
        if index < 0:
            self.object_tree.clear()
            return
        
        workbook_id = self.workbook_dropdown.itemData(index, Qt.ItemDataRole.UserRole)
        if not workbook_id:
            self.object_tree.clear()
            return
        
        # Request fresh data if we don't have it cached
        if workbook_id not in self._view_models and workbook_id not in self._workbooks:
            self.refresh_state_requested.emit(workbook_id)
        else:
            self.refresh_tree()

    def refresh_tree(self, preserve_selection: bool = False):
        """
        Refresh the tree view with current data.
        
        This is a public method that can be called to force a UI refresh
        after updating the underlying data.
        
        Args:
            preserve_selection: If True, try to restore the previously selected object
        """
        # Store currently selected object ID for preservation
        selected_object_id = None
        if preserve_selection:
            current_item = self.object_tree.currentItem()
            if current_item:
                item_data = current_item.data(0, Qt.ItemDataRole.UserRole)
                if item_data:
                    selected_object_id = item_data.get("id")
        
        # Capture expanded node IDs before clearing
        expanded_ids = self._capture_expanded_nodes()
        
        self.object_tree.clear()
        self.events_list.clear()
        
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            return
        
        # Check if we have new view_model format data
        if workbook_id in self._view_models:
            view_model = self._view_models[workbook_id]
            # Build tree from view_model
            if view_model and len(view_model) > 0:
                # view_model is a list containing the root node
                for root_node in view_model:
                    self._build_tree_from_view_model(None, root_node, expanded_ids)
        elif workbook_id in self._workbooks:
            # Legacy format: use old tree building
            tree_data = self._workbooks[workbook_id]
            config = self._event_config.get(workbook_id, {})
            self._build_tree_node(None, tree_data, config)
        else:
            return
        
        # Expand the root
        if self.object_tree.topLevelItemCount() > 0:
            self.object_tree.topLevelItem(0).setExpanded(True)
        
        # Restore selection if requested
        if preserve_selection and selected_object_id:
            self._restore_selection(selected_object_id)
    
    def _capture_expanded_nodes(self) -> set:
        """
        Capture the IDs of all expanded nodes in the tree.
        
        Returns:
            Set of object IDs that are currently expanded
        """
        expanded_ids = set()
        
        def capture_recursive(item: QTreeWidgetItem):
            """Recursively capture expanded state."""
            if item.isExpanded():
                item_data = item.data(0, Qt.ItemDataRole.UserRole)
                if item_data:
                    node_id = item_data.get("id")
                    if node_id:
                        expanded_ids.add(node_id)
            
            for i in range(item.childCount()):
                capture_recursive(item.child(i))
        
        # Capture all top-level items
        for i in range(self.object_tree.topLevelItemCount()):
            capture_recursive(self.object_tree.topLevelItem(i))
        
        return expanded_ids
    
    def _restore_selection(self, object_id: str):
        """
        Try to restore selection to an object with the given ID.
        
        Args:
            object_id: The object ID to select
        """
        def find_item_by_id(item: QTreeWidgetItem, target_id: str) -> Optional[QTreeWidgetItem]:
            """Recursively search for item with target_id."""
            item_data = item.data(0, Qt.ItemDataRole.UserRole)
            if item_data and item_data.get("id") == target_id:
                return item
            
            for i in range(item.childCount()):
                result = find_item_by_id(item.child(i), target_id)
                if result:
                    return result
            return None
        
        # Search all top-level items
        for i in range(self.object_tree.topLevelItemCount()):
            item = self.object_tree.topLevelItem(i)
            found = find_item_by_id(item, object_id)
            if found:
                self.object_tree.setCurrentItem(found)
                return
    
    def _build_tree_node(self, parent_item: Optional[QTreeWidgetItem], node_data: Dict, config: Dict):
        """
        Recursively build tree nodes from the hierarchical tree data.
        
        Args:
            parent_item: Parent tree item (None for root)
            node_data: Node data with type, id, name, children
            config: Event configuration
        """
        node_type = node_data.get("type", "")
        node_id = node_data.get("id", "")
        node_name = node_data.get("name", "Unknown")
        children = node_data.get("children", [])
        
        # Skip collection nodes in display (we show their children directly)
        if node_type.endswith("Collection"):
            # Don't create a tree item for collections, just process children
            for child_data in children:
                self._build_tree_node(parent_item, child_data, config)
            return
        
        # Create tree item for this node
        if parent_item is None:
            item = QTreeWidgetItem(self.object_tree)
        else:
            item = QTreeWidgetItem(parent_item)
        
        # Get icon for this object type
        icon = get_icon_for_type(node_type)
        
        # Add event count if this object has configured events
        # Try to find config by ID first, then by name (for backward compatibility)
        obj_config = config.get(node_id, {})
        if not obj_config:
            obj_config = config.get(node_name, {})
        
        event_count = None
        if isinstance(obj_config, dict) and obj_config:
            # Check if it's new format with 'events' key
            events_data = obj_config.get("events", obj_config)
            count = sum(1 for v in events_data.values() if v)
            if count > 0:
                event_count = count
        
        # Format display name with icon and optional event count
        display_name = format_display_name(icon, node_name, event_count)
        
        item.setText(0, display_name)
        item.setText(1, f"[{node_type}]")
        
        # Store object data in item
        item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": node_type,
            "id": node_id,
            "name": node_name
        })
        
        item.setExpanded(True)
        
        # Recursively add children
        for child_data in children:
            self._build_tree_node(item, child_data, config)
    
    def _build_tree_from_view_model(self, parent_item: Optional[QTreeWidgetItem], node_data: Dict, expanded_ids: set = None):
        """
        Build tree nodes from the view_model data structure.
        
        The view_model contains merged data with events embedded in each node.
        
        Args:
            parent_item: Parent tree item (None for root)
            node_data: Node data from view_model with id, name, type, events, children
            expanded_ids: Set of object IDs that should be expanded
        """
        if expanded_ids is None:
            expanded_ids = set()
        
        node_type = node_data.get("type", "")
        node_id = node_data.get("id", "")
        node_name = node_data.get("name", "Unknown")
        events_list = node_data.get("events", [])
        children = node_data.get("children", [])
        
        # Render collection nodes explicitly in the tree
        is_collection = node_type.endswith("Collection")
        
        # Create tree item for this node (including collections)
        if parent_item is None:
            item = QTreeWidgetItem(self.object_tree)
        else:
            item = QTreeWidgetItem(parent_item)
        
        # Get icon for this object type
        icon = get_icon_for_type(node_type)
        
        # Count assigned events (events with python_function)
        event_count = sum(1 for evt in events_list if evt.get("python_function", ""))
        
        # Format display name with icon and optional event count
        display_name = format_display_name(icon, node_name, event_count if event_count > 0 else None)
        
        item.setText(0, display_name)
        item.setText(1, f"[{node_type}]")
        
        # Store object data in item including the events list
        item.setData(0, Qt.ItemDataRole.UserRole, {
            "type": node_type,
            "id": node_id,
            "name": node_name,
            "events": events_list  # Store events list from view_model
        })
        
        # Set expanded state based on previous state or defaults
        if node_id in expanded_ids:
            # Restore previous expanded state
            item.setExpanded(True)
        elif node_type == "Worksheet":
            # Worksheet nodes collapsed by default
            item.setExpanded(False)
        else:
            # Other nodes expanded by default
            item.setExpanded(True)
        
        # Recursively add children
        for child_data in children:
            self._build_tree_from_view_model(item, child_data, expanded_ids)
    
    def _on_tree_selection_changed(self, current: QTreeWidgetItem, previous: QTreeWidgetItem):
        """
        Handle tree selection change - populate events list for selected object.
        
        Args:
            current: Currently selected tree item
            previous: Previously selected tree item
        """
        self.events_list.clear()
        
        if not current:
            return
        
        # Get object data from the selected item
        item_data = current.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
        
        object_type = item_data.get("type", "")
        object_id = item_data.get("id", "")
        object_name = item_data.get("name", "")
        
        # Check if we have events embedded in the item data (from view_model)
        events_from_view_model = item_data.get("events")
        
        # Get current workbook
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            return
        
        if events_from_view_model is not None:
            # Use events from view_model (new format)
            validation = self._validation_results.get(workbook_id, {})
            
            for event_data in events_from_view_model:
                event_type = event_data.get("type", "")
                event_name = event_data.get("name", "")
                arg_type = event_data.get("arg_type", "")
                python_function = event_data.get("python_function", "")
                
                # Add xpycode. prefix if arg_type doesn't already have it and is not empty
                if arg_type and not arg_type.startswith("xpycode."):
                    qualified_arg_type = f"xpycode.{arg_type}"
                else:
                    qualified_arg_type = arg_type
                
                item = QTreeWidgetItem(self.events_list)
                
                # Set column values - use event_name for display (e.g., "onSelectionChanged")
                item.setText(0, event_name)
                item.setText(1, python_function if python_function else "(not assigned)")
                
                # Store event data in item
                item.setData(0, Qt.ItemDataRole.UserRole, {
                    "event_type": event_type,
                    "event_name": event_name,
                    "arg_type": qualified_arg_type,
                    "object_id": object_id,
                    "object_name": object_name,
                    "object_type": object_type,
                    "handler": python_function
                })
                
                # Style based on handler status
                validation_key = f"{object_id}:{event_name}"
                if validation_key not in validation:
                    # Try with name for backward compatibility
                    validation_key = f"{object_name}:{event_name}"
                
                if python_function:
                    # Handler is assigned
                    if validation_key in validation and not validation.get(validation_key, True):
                        # Invalid handler - show in red
                        item.setForeground(0, QBrush(QColor("#ff6b6b")))
                        item.setForeground(1, QBrush(QColor("#ff6b6b")))
                        item.setToolTip(0, f"{event_name}\nHandler: {python_function} (invalid)")
                        item.setToolTip(1, f"{python_function} (invalid)")
                    else:
                        # Valid handler - show in bold with theme-aware green
                        font = item.font(0)
                        font.setBold(True)
                        item.setFont(0, font)
                        item.setFont(1, font)
                        handler_color = self._get_handler_color()
                        item.setForeground(0, QBrush(QColor(handler_color)))
                        item.setForeground(1, QBrush(QColor(handler_color)))
                        item.setToolTip(0, f"{event_name}\nHandler: {python_function}")
                        item.setToolTip(1, python_function)
                else:
                    # No handler assigned - show in gray
                    item.setForeground(0, QBrush(QColor("#888888")))
                    item.setForeground(1, QBrush(QColor("#888888")))
                    item.setToolTip(0, f"{event_name}\n(right-click to assign)")
                    item.setToolTip(1, "(right-click to assign)")
        else:
            # Legacy format without embedded events in view_model
            # This code path is kept for backward compatibility only
            logger.warning("Using legacy format without embedded events - this should not happen with new event system")
            return

    def _show_context_menu(self, position):
        """Show context menu for the selected event in the events list."""
        item = self.events_list.itemAt(position)
        if not item:
            return
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
        
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            return
        
        object_id = item_data.get("object_id", "")
        object_name = item_data.get("object_name", "")
        object_type = item_data.get("object_type", "")
        event_name = item_data.get("event_name", "")
        handler = item_data.get("handler", "")
        arg_type = item_data.get("arg_type", "dict")
        
        menu = QMenu(self)
        
        # Assign Handler action
        assign_action = QAction("Assign Handler...", self)
        assign_action.triggered.connect(
            lambda: self._on_assign_handler(workbook_id, object_id, object_name, object_type, event_name, arg_type)
        )
        menu.addAction(assign_action)
        
        # Create New Handler action
        create_action = QAction("Create New Handler...", self)
        create_action.triggered.connect(
            lambda: self._on_create_handler(workbook_id, object_id, object_name, object_type, event_name, arg_type)
        )
        menu.addAction(create_action)
        
        # Clear Handler action (only if handler is assigned)
        if handler:
            menu.addSeparator()
            clear_action = QAction("Clear Handler", self)
            clear_action.triggered.connect(
                lambda: self._on_clear_handler(workbook_id, object_id, object_name, object_type, event_name)
            )
            menu.addAction(clear_action)
        
        menu.exec(self.events_list.mapToGlobal(position))

    def _on_event_double_clicked(self, item: QTreeWidgetItem):
        """
        Handle double-click on an event item.
        
        If the event doesn't have a handler, triggers the "Create New Handler" flow.
        
        Args:
            item: The tree widget item that was double-clicked
        """
        if not item:
            return
        
        item_data = item.data(0, Qt.ItemDataRole.UserRole)
        if not item_data:
            return
        
        handler = item_data.get("handler", "")
        
        # If no handler is assigned, create one
        if not handler:
            workbook_id = self.get_current_workbook()
            if not workbook_id:
                return
            
            object_id = item_data.get("object_id", "")
            object_name = item_data.get("object_name", "")
            object_type = item_data.get("object_type", "")
            event_name = item_data.get("event_name", "")
            arg_type = item_data.get("arg_type", "dict")
            
            self._on_create_handler(workbook_id, object_id, object_name, object_type, event_name, arg_type)

    def _on_assign_handler(
        self, workbook_id: str, object_id: str, object_name: str, object_type: str, event_name: str, arg_type: str = "dict"
    ):
        """
        Handle assign handler action.
        
        Uses FunctionSelectorDialog to allow browsing modules and functions.
        """
        # Request fresh module cache from parent (MainWindow) before opening dialog
        # This ensures newly written functions appear immediately
        parent_window = self.parent()
        if parent_window:
            try:
                # Try to update the module cache from the parent window
                # This method is expected to be present in MainWindow
                parent_window.update_event_manager_module_cache(workbook_id)
            except AttributeError:
                # Parent doesn't have the method (shouldn't happen in normal usage)
                logger.warning("Parent window does not have update_event_manager_module_cache method")
        
        # Get modules from cache (now refreshed)
        modules = self._module_cache.get(workbook_id, {})
        
        if modules:
            # Use FunctionSelectorDialog for browsing
            dialog = FunctionSelectorDialog(
                self,
                modules=modules,
                object_name=object_name,
                object_type=object_type,
                event_type=event_name,  # Pass event_name as event_type for display
                arg_type=arg_type
            )
            
            if dialog.exec() == QDialog.DialogCode.Accepted:
                function_name = dialog.get_selected_function()
                if function_name:
                    logger.debug(f"Assigning handler: {workbook_id}/{object_type}[{object_id}].{event_name} -> {function_name}")
                    # Emit with object_id and object_type for new ID-based tracking
                    self.assign_handler_requested.emit(
                        workbook_id, object_id, object_type, event_name, function_name
                    )
        else:
            # Fallback to simple input dialog if no modules available
            function_name, ok = QInputDialog.getText(
                self,
                "Assign Handler",
                f"Enter handler function for {object_name}.{event_name}:\n"
                "(e.g., excel_events.on_selection_change)"
            )
            
            if ok and function_name:
                # Validate function name format
                if not self._is_valid_function_name(function_name):
                    QMessageBox.warning(
                        self,
                        "Invalid Function Name",
                        f"'{function_name}' is not a valid Python function name.\n"
                        "Use format: module_name.function_name"
                    )
                    return
                
                logger.debug(f"Assigning handler: {workbook_id}/{object_type}[{object_id}].{event_name} -> {function_name}")
                self.assign_handler_requested.emit(
                    workbook_id, object_id, object_type, event_name, function_name
                )

    def _on_create_handler(
        self, workbook_id: str, object_id: str, object_name: str, object_type: str, event_name: str, arg_type: str = "dict"
    ):
        """Handle create new handler action."""
        # Suggest a default function name
        default_name = f"on_{object_name.lower()}_{event_name.lower()}"
        # Make it a valid Python identifier
        default_name = "".join(c if c.isalnum() or c == '_' else '_' for c in default_name)
        
        # Use custom dialog with headers for Object Context, Event Name, Expected Signature
        dialog = CreateHandlerDialog(
            self,
            object_name=object_name,
            object_type=object_type,
            event_type=event_name,  # Pass event_name as event_type for display
            default_name=default_name,
            arg_type=arg_type
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            function_name = dialog.get_function_name()
            if function_name:
                # Validate function name is a valid identifier
                if not function_name.isidentifier():
                    QMessageBox.warning(
                        self,
                        "Invalid Function Name",
                        f"'{function_name}' is not a valid Python identifier.\n"
                        "Use only letters, numbers, and underscores (cannot start with a number)."
                    )
                    return
                
                # Check for duplicate function in excel_events.py
                excel_events_code = self._module_cache.get(workbook_id, {}).get("excel_events", "")
                if excel_events_code:
                    # Simple check for function definition
                    pattern = re.compile(rf'^def\s+{re.escape(function_name)}\s*\(', re.MULTILINE)
                    if pattern.search(excel_events_code):
                        QMessageBox.warning(
                            self,
                            "Duplicate Function",
                            f"A function named '{function_name}' already exists in excel_events.py.\n"
                            "Please choose a different name."
                        )
                        return
                
                logger.debug(f"Creating handler: {workbook_id}/{object_type}[{object_id}].{event_name} -> {function_name}")
                # Emit with object_id for new ID-based tracking
                self.create_handler_requested.emit(
                    workbook_id, object_id, object_name, object_type, event_name, function_name, arg_type
                )

    def _on_clear_handler(self, workbook_id: str, object_id: str, object_name: str, object_type: str, event_name: str):
        """Handle clear handler action."""
        # Emit assign with empty function name to clear
        logger.debug(f"Clearing handler: {workbook_id}/{object_type}[{object_id}].{event_name}")
        self.assign_handler_requested.emit(
            workbook_id, object_id, object_type, event_name, ""
        )

    def _is_valid_function_name(self, name: str) -> bool:
        """
        Validate that a function name is in valid format.
        
        Valid formats:
        - "function_name" (simple function)
        - "module_name.function_name" (qualified function)
        
        Args:
            name: The function name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not name:
            return False
        
        parts = name.split(".")
        # Allow simple function name or module.function format
        if len(parts) > 2:
            return False
        
        for part in parts:
            if not part.isidentifier():
                return False
        
        return True
