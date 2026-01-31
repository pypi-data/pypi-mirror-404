"""
XPyCode IDE - Function Publisher

This module provides the Function Publisher widget for publishing Python
functions to Excel as User Defined Functions (UDFs).
"""

import ast
import logging
import re
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QLabel,
    QHeaderView,
    QDialog,
    QMessageBox,
    QMenu,
    QFrame,
)
from PySide6.QtCore import Signal, Qt
from typing import Dict, List, Optional

from .event_manager import FunctionSelectorDialog

# Configure logging
from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


# Excel function name pattern - uppercase letters, numbers, and underscores only
EXCEL_NAME_PATTERN = re.compile(r'^[A-Z0-9_]+$')


def detect_streaming(code: str, function_name: str) -> bool:
    """
    Detect if a function is a generator (uses yield or yield from).
    
    Only detects yield statements directly in the target function,
    not in nested functions defined within it. Handles both regular
    functions and async functions.
    
    Args:
        code: The Python source code containing the function
        function_name: The name of the function to check
    
    Returns:
        True if the function contains yield/yield from, False otherwise
    """
    try:
        tree = ast.parse(code)
        
        for node in ast.walk(tree):
            # Check both FunctionDef and AsyncFunctionDef
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == function_name:
                # Check for yield or yield from only in this function's body
                # Exclude nested function definitions
                for child in node.body:
                    if _contains_yield_not_in_nested_func(child):
                        return True
                return False
        
        # Function not found
        return False
    except SyntaxError:
        return False
    except Exception:
        return False


def _contains_yield_not_in_nested_func(node) -> bool:
    """
    Check if a node contains yield/yield from, excluding nested functions.
    
    Args:
        node: AST node to check
    
    Returns:
        True if node contains yield outside of nested functions
    """
    # If this is a yield node itself, return True
    if isinstance(node, (ast.Yield, ast.YieldFrom)):
        return True
    
    # If this is a function or async function definition, don't recurse into it
    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
        return False
    
    # Recurse into child nodes
    for child in ast.iter_child_nodes(node):
        if _contains_yield_not_in_nested_func(child):
            return True
    
    return False


class FunctionPublisher(QFrame):
    """
    Function Publisher widget for publishing Python functions to Excel.
    
    Provides functionality to:
    - Select a target workbook from a dropdown
    - View published functions with their Excel names
    - Add/Remove function publications
    """

    # Signals for publication operations
    add_publication_requested = Signal(str, str, str)  # workbook_id, python_function, excel_name
    remove_publication_requested = Signal(str, str)  # workbook_id, python_function
    # Signal to request module cache update before opening function selector
    update_module_cache_requested = Signal(str)  # workbook_id
    # Signal to sync published functions with server
    sync_published_functions_requested = Signal(str, list)  # workbook_id, functions list

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tabMainWidget")
        # Track workbook names: {workbook_id: display_name}
        self._workbook_names: Dict[str, str] = {}
        # Track published functions per workbook: {workbook_id: [(python_function, excel_name, dimension, streaming), ...]}
        self._publications: Dict[str, List[tuple]] = {}
        # Store modules cache for function selection: {workbook_id: {module_name: code}}
        self._modules_cache: Dict[str, Dict[str, str]] = {}
        # Flag to prevent recursive calls during uppercase conversion
        self._updating_item: bool = False
        self._setup_ui()



    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        
        # Workbook selection section
        workbook_layout = QHBoxLayout()
        workbook_label = QLabel("Target Workbook:")
        self.workbook_dropdown = QComboBox()
        self.workbook_dropdown.setMinimumWidth(200)
        # Use currentIndexChanged to properly handle workbook ID from UserRole
        self.workbook_dropdown.currentIndexChanged.connect(self._on_workbook_index_changed)
        workbook_layout.addWidget(workbook_label)
        workbook_layout.addWidget(self.workbook_dropdown)
        workbook_layout.addStretch()
        layout.addLayout(workbook_layout)
        
        # Published functions section
        functions_label = QLabel("Published Functions:")
        layout.addWidget(functions_label)
        
        self.function_table = QTableWidget()
        self.function_table.setColumnCount(4)
        self.function_table.setHorizontalHeaderLabels(["Function Source", "Publishing Name", "Dimension", "Streaming"])
        self.function_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.function_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Stretch
        )
        self.function_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Interactive
        )
        self.function_table.horizontalHeader().setSectionResizeMode(
            3, QHeaderView.ResizeMode.Interactive
        )
        self.function_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.function_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        # Make the Publishing Name column editable
        self.function_table.itemChanged.connect(self._on_table_item_changed)
        # Enable context menu on table
        self.function_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.function_table.customContextMenuRequested.connect(self._on_context_menu)
        layout.addWidget(self.function_table)
        
        # Buttons section
        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Publication")
        self.add_button.clicked.connect(self._on_add_clicked)
        self.remove_button = QPushButton("Remove Publication")
        self.remove_button.clicked.connect(self._on_remove_clicked)
        self.sync_button = QPushButton("Sync to Excel")
        self.sync_button.clicked.connect(self._on_sync_clicked)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.sync_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def _validate_excel_name(self, name: str) -> tuple[bool, str]:
        """
        Validate Excel function name against requirements.
        
        Args:
            name: The Excel function name to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not name:
            return False, "Publishing name cannot be empty."
        
        # Check against Excel name pattern (uppercase letters, numbers, underscores)
        if not EXCEL_NAME_PATTERN.match(name):
            return False, "Publishing name must contain only uppercase letters, numbers, and underscores (A-Z, 0-9, _)."
        
        return True, ""
    
    def _on_sync_clicked(self):
        """Handle Sync to Excel button click - manually trigger function sync."""
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            QMessageBox.warning(
                self,
                "No Workbook Selected",
                "Please select a target workbook first."
            )
            return
        
        # Trigger sync with server
        self._sync_publications(workbook_id)
        
        QMessageBox.information(
            self,
            "Sync Complete",
            "Published functions have been synchronized with Excel."
        )

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
        
        # Initialize empty publications list for this workbook
        if workbook_id not in self._publications:
            self._publications[workbook_id] = []


        if self.workbook_dropdown.currentIndex() == -1 and self.workbook_dropdown.count() > 0:
            self.workbook_dropdown.setCurrentIndex(0)

        current_workbook_id = self.get_current_workbook()

        if current_workbook_id == workbook_id:
            self._refresh_publications_table(workbook_id)


    def remove_workbook(self, workbook_id: str):
        """
        Remove a workbook from the dropdown.
        
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
        self._workbook_names.pop(workbook_id, None)
        self._publications.pop(workbook_id, None)
        #self._modules_cache.pop(workbook_id, None)
        
        # If it was the only workbook or the selected one was removed, clear the table
        if self.workbook_dropdown.count() == 0:
            self.function_table.setRowCount(0)
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
        Get the currently selected workbook ID.
        
        Returns:
            The workbook identifier or empty string if none selected
        """
        index = self.workbook_dropdown.currentIndex()
        if index < 0:
            return ""
        workbook_id = self.workbook_dropdown.itemData(index, Qt.ItemDataRole.UserRole)
        return workbook_id if workbook_id else ""
    
    def set_modules_cache(self, workbook_id: str, modules: Dict[str, str]):
        """
        Update the modules cache for a workbook.
        
        Args:
            workbook_id: The workbook identifier
            modules: Dictionary of {module_name: code}
        """
        return 
        self._modules_cache[workbook_id] = modules



    def _on_workbook_index_changed(self, index: int):
        """Handle workbook selection change by index."""
        if index < 0:
            self.function_table.setRowCount(0)
            return
        
        workbook_id = self.workbook_dropdown.itemData(index, Qt.ItemDataRole.UserRole)
        if not workbook_id:
            self.function_table.setRowCount(0)
            return
        
        # Load publications for the selected workbook
        self._refresh_publications_table(workbook_id)

    def _refresh_publications_table(self, workbook_id: str):
        """
        Refresh the publications table for the given workbook.
        
        Args:
            workbook_id: The workbook identifier
        """
        publications = self._publications.get(workbook_id, [])
        
        # Temporarily disconnect itemChanged to avoid triggering during refresh
        self.function_table.itemChanged.disconnect(self._on_table_item_changed)
        
        # Clear existing items from the table
        self.function_table.clearContents()
        
        # Set the row count for the new publications
        self.function_table.setRowCount(len(publications))
        
        for row, pub_tuple in enumerate(publications):
            # Handle both old format (2 items) and new format (4 items)
            if len(pub_tuple) == 2:
                python_function, excel_name = pub_tuple
                dimension = "Scalar"
                streaming = False
            else:
                python_function, excel_name, dimension, streaming = pub_tuple
            
            # Function Source (read-only)
            source_item = QTableWidgetItem(python_function)
            source_item.setFlags(source_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.function_table.setItem(row, 0, source_item)
            
            # Publishing Name (editable)
            name_item = QTableWidgetItem(excel_name)
            self.function_table.setItem(row, 1, name_item)
            
            # Dimension (editable via combo box)
            dimension_combo = QComboBox()
            dimension_combo.addItems(["Scalar", "1-Row", "1-Column", "2-D"])
            dimension_combo.setCurrentText(dimension)
            dimension_combo.currentTextChanged.connect(
                lambda text, r=row: self._on_dimension_changed(r, text)
            )
            self.function_table.setCellWidget(row, 2, dimension_combo)
            
            # Streaming (read-only)
            streaming_item = QTableWidgetItem("Yes" if streaming else "No")
            streaming_item.setFlags(streaming_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.function_table.setItem(row, 3, streaming_item)
        
        # Reconnect itemChanged signal
        self.function_table.itemChanged.connect(self._on_table_item_changed)

    def _on_table_item_changed(self, item: QTableWidgetItem):
        """Handle changes to table items (specifically Publishing Name edits)."""
        if item.column() != 1:  # Only handle Publishing Name column
            return
        
        # Prevent recursive calls during uppercase conversion
        if self._updating_item:
            return
        
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            return
        
        row = item.row()
        new_name = item.text().strip()
        
        # Convert to uppercase before validation
        new_name_upper = new_name.upper()
        if new_name != new_name_upper:
            # Use flag to prevent recursive call
            self._updating_item = True
            try:
                item.setText(new_name_upper)
                new_name = new_name_upper
            finally:
                self._updating_item = False
        
        # Validate the new name
        is_valid, error_msg = self._validate_excel_name(new_name)
        if not is_valid:
            QMessageBox.warning(
                self,
                "Invalid Name",
                error_msg
            )
            # Restore old value
            publications = self._publications.get(workbook_id, [])
            if row < len(publications):
                item.setText(publications[row][1])
            return
        
        # Update the cached publication
        if workbook_id in self._publications and row < len(self._publications[workbook_id]):
            pub_tuple = self._publications[workbook_id][row]
            # Handle both old format (2 items) and new format (4 items)
            if len(pub_tuple) == 2:
                python_function, old_name = pub_tuple
                dimension = "Scalar"
                streaming = False
            else:
                python_function, old_name, dimension, streaming = pub_tuple
            
            self._publications[workbook_id][row] = (python_function, new_name, dimension, streaming)
            
            # Sync with server after editing
            self._sync_publications(workbook_id)
    
    def _on_dimension_changed(self, row: int, new_dimension: str):
        """Handle dimension dropdown changes."""
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            return
        
        # Update the cached publication
        if workbook_id in self._publications and row < len(self._publications[workbook_id]):
            pub_tuple = self._publications[workbook_id][row]
            # Handle both old format (2 items) and new format (4 items)
            if len(pub_tuple) == 2:
                python_function, excel_name = pub_tuple
                streaming = False
            else:
                python_function, excel_name, old_dimension, streaming = pub_tuple
            
            self._publications[workbook_id][row] = (python_function, excel_name, new_dimension, streaming)
            
            # Sync with server after editing
            self._sync_publications(workbook_id)

    def _on_add_clicked(self):
        """Handle add button click - open function selector dialog."""
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            QMessageBox.warning(
                self,
                "No Workbook Selected",
                "Please select a target workbook first."
            )
            return
        
        # Request module cache update from MainWindow to ensure latest editor content
        self.update_module_cache_requested.emit(workbook_id)
        
        # Get modules cache for the current workbook
        modules = self._modules_cache.get(workbook_id, {})
        if not modules:
            QMessageBox.warning(
                self,
                "No Modules Available",
                "No Python modules are available in the selected workbook. Create a module first."
            )
            return
        
        # Open the function selector dialog
        # Note: object_name, object_type, event_type, and arg_type are empty because
        # we're selecting functions for UDF publishing, not event handling.
        # The dialog is designed to work in both contexts.
        dialog = FunctionSelectorDialog(
            parent=self,
            modules=modules,
            object_name="",
            object_type="",
            event_type="",
            arg_type=""
        )
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_function = dialog.get_selected_function()
            if selected_function:
                # selected_function is in format "module_name.function_name"
                self._add_function_to_list(workbook_id, selected_function)

    def _add_function_to_list(self, workbook_id: str, python_function: str):
        """
        Add a function to the publications list with auto-generated Excel name.
        
        Args:
            workbook_id: The workbook identifier
            python_function: The Python function in format "module.function"
        """
        # Extract module and function name
        if "." in python_function:
            module_name, function_name = python_function.rsplit(".", 1)
        else:
            # This fallback should not occur in practice since FunctionSelectorDialog
            # always provides "module.function" format. If reached, streaming detection
            # will be skipped (returns False) since no module code is available.
            module_name = ""
            function_name = python_function
            logger.warning(f"Function without module prefix: {python_function}. Streaming detection skipped.")
        
        # Detect streaming using AST
        modules = self._modules_cache.get(workbook_id, {})
        module_code = modules.get(module_name, "")
        streaming = detect_streaming(module_code, function_name)
        
        # Default dimension
        dimension = "Scalar"
        
        # Generate Excel name without "XPC." prefix (per requirements)
        # Use uppercase and replace invalid characters with underscores
        base_excel_name = function_name.upper()
        # Replace any invalid characters with underscores
        base_excel_name = re.sub(r'[^A-Z0-9_]', '_', base_excel_name)
        excel_name = base_excel_name
        
        # Generate unique Excel name (append _n if duplicate)
        existing_names = {pub[1] for pub in self._publications.get(workbook_id, [])}
        counter = 1
        while excel_name in existing_names:
            excel_name = f"{base_excel_name}_{counter}"
            counter += 1
        
        # Add to publications list with all 4 fields
        if workbook_id not in self._publications:
            self._publications[workbook_id] = []
        self._publications[workbook_id].append((python_function, excel_name, dimension, streaming))
        
        # Refresh the table
        self._refresh_publications_table(workbook_id)
        
        # Sync with server
        self._sync_publications(workbook_id)
        
        # Emit signal for external handling (future registration)
        self.add_publication_requested.emit(workbook_id, python_function, excel_name)

    def _on_remove_clicked(self):
        """Handle remove button click."""
        workbook_id = self.get_current_workbook()
        selected_rows = self.function_table.selectionModel().selectedRows()
        
        if not workbook_id:
            return
        
        if not selected_rows:
            QMessageBox.warning(
                self,
                "No Selection",
                "Please select a function to remove."
            )
            return
        
        row = selected_rows[0].row()
        
        # Get the publication data
        publications = self._publications.get(workbook_id, [])
        if row >= len(publications):
            return
        
        pub_tuple = publications[row]
        # Handle both old format (2 items) and new format (4 items)
        if len(pub_tuple) >= 2:
            python_function = pub_tuple[0]
        else:
            return
        
        # Remove from cached list
        del publications[row]
        
        # Emit signal for external handling
        self.remove_publication_requested.emit(workbook_id, python_function)
        
        # Refresh the table
        self._refresh_publications_table(workbook_id)
        
        # Sync with server
        self._sync_publications(workbook_id)
    
    def _sync_publications(self, workbook_id: str):
        """
        Sync published functions with the server.
        
        Args:
            workbook_id: The workbook identifier
        """
        # First, update streaming info for all functions
        self._update_all_streaming_info(workbook_id)
        
        publications = self._publications.get(workbook_id, [])
        # Convert to list of dicts with module_name, function_name, excel_name, dimension, and streaming keys
        functions_list = []
        for pub_tuple in publications:
            # Handle both old format (2 items) and new format (4 items)
            if len(pub_tuple) == 2:
                python_func, excel_name = pub_tuple
                dimension = "Scalar"
                streaming = False
            else:
                python_func, excel_name, dimension, streaming = pub_tuple
            
            # Parse python_func to extract module_name and function_name
            parts = python_func.rsplit(".", 1)
            if len(parts) == 2:
                module_name, func_name = parts
                functions_list.append({
                    "module_name": module_name,
                    "function_name": func_name,
                    "excel_name": excel_name,
                    "dimension": dimension,
                    "streaming": streaming
                })
            else:
                # Log warning but don't fail - skip invalid entries
                logger.warning(f"Skipping invalid function format (expected 'module.function'): {python_func}")
        self.sync_published_functions_requested.emit(workbook_id, functions_list)
    
    def _is_generator_function(self, workbook_id: str, python_function: str) -> bool:
        """
        Check if a function is a generator function using AST analysis.
        
        Args:
            workbook_id: The workbook identifier
            python_function: The Python function in format "module.function"
        
        Returns:
            True if the function is a generator, False otherwise
        """
        # Extract module and function name
        if "." in python_function:
            module_name, function_name = python_function.rsplit(".", 1)
        else:
            # No module prefix - can't detect
            return False
        
        # Get module code from cache
        modules = self._modules_cache.get(workbook_id, {})
        module_code = modules.get(module_name, "")
        
        if not module_code:
            # No code available - can't detect
            return False
        
        # Use the detect_streaming function
        return detect_streaming(module_code, function_name)
    
    def _update_all_streaming_info(self, workbook_id: str) -> bool:
        """
        Check and update streaming info for all registered functions.
        
        Args:
            workbook_id: The workbook identifier
        
        Returns:
            True if any streaming info was updated, False otherwise.
            This return value is currently not used but is provided for 
            future extensibility (e.g., to show a notification when updates occur).
        """
        publications = self._publications.get(workbook_id, [])
        updated = False
        
        for i, pub_tuple in enumerate(publications):
            # Handle both old format (2 items) and new format (4 items)
            if len(pub_tuple) == 2:
                python_function, excel_name = pub_tuple
                dimension = "Scalar"
                streaming = False
            else:
                python_function, excel_name, dimension, streaming = pub_tuple
            
            new_streaming = self._is_generator_function(workbook_id, python_function)
            if new_streaming != streaming:
                publications[i] = (python_function, excel_name, dimension, new_streaming)
                updated = True
        
        if updated:
            self._refresh_publications_table(workbook_id)
        
        return updated
    
    def _on_context_menu(self, pos):
        """Handle right-click context menu."""
        item = self.function_table.itemAt(pos)
        if not item:
            return
        
        row = item.row()
        column = item.column()
        
        # Only show menu for Streaming column (column 3)
        if column == 3:
            menu = QMenu(self)
            check_action = menu.addAction("Check if Generator")
            action = menu.exec(self.function_table.mapToGlobal(pos))
            
            if action == check_action:
                self._check_streaming_for_row(row)
    
    def _check_streaming_for_row(self, row: int):
        """
        Check and update streaming info for a specific row.
        
        Args:
            row: The row index in the table
        """
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            return
        
        publications = self._publications.get(workbook_id, [])
        if row >= len(publications):
            return
        
        pub_tuple = publications[row]
        # Handle both old format (2 items) and new format (4 items)
        if len(pub_tuple) == 2:
            python_function, excel_name = pub_tuple
            dimension = "Scalar"
            old_streaming = False
        else:
            python_function, excel_name, dimension, old_streaming = pub_tuple
        
        new_streaming = self._is_generator_function(workbook_id, python_function)
        
        if new_streaming != old_streaming:
            publications[row] = (python_function, excel_name, dimension, new_streaming)
            self._refresh_publications_table(workbook_id)
            # Sync with server only when streaming status actually changed
            self._sync_publications(workbook_id)
            
            status = "is a generator" if new_streaming else "is NOT a generator"
            QMessageBox.information(
                self,
                "Streaming Check",
                f"Function '{python_function}' {status}.\nStreaming updated to: {'Yes' if new_streaming else 'No'}"
            )
        else:
            status = "is a generator" if new_streaming else "is NOT a generator"
            QMessageBox.information(
                self,
                "Streaming Check",
                f"Function '{python_function}' {status}.\nNo change needed."
            )
    
    def update_publications_from_server(self, workbook_id: str, functions_list: List[dict]):
        """
        Update publications list from server state.
        
        This is called when switching workbooks or when receiving updates from the server.
        
        Args:
            workbook_id: The workbook identifier
            functions_list: List of dicts with 'module_name', 'function_name', 'excel_name', 'dimension', and 'streaming' keys
        """
        # Convert list of dicts to list of tuples
        publications = []
        for func_dict in functions_list:
            # New format: module_name + function_name + dimension + streaming
            module_name = func_dict.get("module_name", "")
            func_name = func_dict.get("function_name", "")
            excel_name = func_dict.get("excel_name", "")
            dimension = func_dict.get("dimension", "Scalar")
            streaming = func_dict.get("streaming", False)
            
            if module_name and func_name:
                python_function = f"{module_name}.{func_name}"
                publications.append((python_function, excel_name, dimension, streaming))
            else:
                logger.warning(f"Skipping invalid function entry from server: {func_dict}")
        
        self._publications[workbook_id] = publications
        
        # If this is the currently selected workbook, refresh the table
        current_workbook_id = self.get_current_workbook()
        if current_workbook_id == workbook_id:
            self._refresh_publications_table(workbook_id)
