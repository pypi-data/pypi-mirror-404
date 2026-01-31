"""
XPyCode IDE - Package Manager

This module provides the Package Manager widget for managing Python packages
in workbooks. Includes package search, version/extras selection, and installation.
"""

import html
import logging
from threading import currentThread

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QTableWidget,
    QTableWidgetItem,
    QPushButton,
    QTextEdit,
    QLabel,
    QHeaderView,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QGroupBox,
    QDialog,
    QDialogButtonBox,
    QStyledItemDelegate,
    QMenu,
    QCheckBox,
    QFrame,
)
from .widgets.expandable_group_box import ExpandableGroupBox, ExpandableGroupContainer, FrameState
from .widgets.edits import QTextEditWithClear

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QStandardItemModel, QStandardItem, QTextCursor
from typing import Dict, List, Union, Optional

# Configure logging
from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


# Status color constants for package states (using QColor for proper color values)
STATUS_COLORS = {
    "pending": QColor("#FFA500"),         # Amber - newly added
    "pending_update": QColor("#FFA500"),  # Amber - version/extras changed
    "to_remove": QColor("#FFA500"),       # Amber - marked for removal
    "resolving": QColor("#3498DB"),       # Blue
    "installing": QColor("#3498DB"),      # Blue
    "installed": QColor("#2ECC71"),       # Green
    "installed_with_errors": QColor("#2ECC71"),  # Still green - package itself is installed
    "cached": QColor("#2ECC71"),          # Green
    "error": QColor("#E74C3C"),           # Red
}

STATUS_LABELS = {
    "pending": "Pending",
    "pending_update": "Pending Update",
    "to_remove": "To Remove",
    "resolving": "Resolving...",
    "installing": "Installing...",
    "installed": "Installed",
    "installed_with_errors": "Installed (with errors)",  # New status
    "cached": "Cached",
    "error": "Error",
}

# Legacy color constants for backward compatibility
STATUS_COLOR_PENDING = QColor("#FFA500")
STATUS_COLOR_INSTALLING = QColor("#3498DB")
STATUS_COLOR_INSTALLED = QColor("#2ECC71")
STATUS_COLOR_ERROR = QColor("#E74C3C")

# Delegate constants
LOADING_TEXT = "Loading..."
NO_EXTRAS_TEXT = "No extras available"

class PackageManager(QFrame):
    """
    Package Manager widget for managing Python packages in workbooks.
    
    Provides functionality to:
    - Select a workbook from a dropdown
    - Search for packages and query available versions/extras
    - Add packages to the list with specific version and extras
    - View installed packages with their versions and extras
    - Install/Update/Remove packages
    - View pip output in a console area
    """

    # Signals for package operations
    install_requested = Signal(str, str)  # workbook_id, package_name
    update_requested = Signal(str, str)  # workbook_id, package_name
    
    # New signals for package search and management
    search_package_requested = Signal(str)  # package_name
    get_versions_requested = Signal(str)  # package_name
    get_extras_requested = Signal(str, str)  # package_name, version
    add_package_requested = Signal(str, str, str, list)  # workbook_id, package_name, version, extras
    update_package_requested = Signal(str, str, str, list)  # workbook_id, package_name, version, extras
    remove_package_requested = Signal(str, str)  # workbook_id, package_name
    
    # Phase 2 signals for package list management
    install_all_requested = Signal(str)  # workbook_id
    reorder_requested = Signal(str, list)  # workbook_id, package_names_in_order
    
    
    # New signal for workbook selection change
    get_workbook_packages_requested = Signal(str)  # workbook_id
    
    # New signal for restore functionality
    restore_requested = Signal(str)  # workbook_id
    
    # New signal for see resolution
    see_resolution_requested = Signal(str)  # workbook_id
    
    # New signal for package status update
    update_package_status_requested = Signal(str, str, str)  # workbook_id, package_name, status
    
    # New signal for python path updates
    update_python_paths_requested = Signal(str, list)  # workbook_id, python_paths

    # Signal to update all caches
    update_caches=Signal(str, object, object, object)  # workbook_id, packages, package_errors, python_paths

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tabMainWidget")

        # Track workbook names: {workbook_id: display_name}
        self._workbook_names: Dict[str, str] = {}
        # Store current search results
        self._current_package_name: str = ""
        self._available_versions: List[str] = []
        self._available_extras: List[str] = []
        # Pending edit state for double-click editing
        self._pending_edit_version = None
        self._pending_edit_extras = []
        # Store package errors: {package_name: [error_messages]}
        self._package_errors: Dict[str, Dict] = {}
        # Store python paths for current workbook: [path_string, ...]
        #self._python_paths: List[str] = []
        #Cache data for package list and python paths:
        self._packages: Dict[List[Dict]] = {}
        self._python_paths: Dict[List[str]] = {}


        self._setup_ui()


    def _setup_ui(self):
        """Setup the widget UI."""
        main_layout = QVBoxLayout(self)
        
        # Workbook selection section (stays outside the expandable container)
        workbook_layout = QHBoxLayout()
        workbook_label = QLabel("Workbook:")
        self.workbook_dropdown = QComboBox()
        self.workbook_dropdown.setMinimumWidth(200)
        self.workbook_dropdown.currentIndexChanged.connect(self._on_workbook_changed)
        workbook_layout.addWidget(workbook_label)
        workbook_layout.addWidget(self.workbook_dropdown)
        workbook_layout.addStretch()
        main_layout.addLayout(workbook_layout)
        
        # Create expandable container for the 4 groups
        self._group_container = ExpandableGroupContainer()
        container_layout = QVBoxLayout()

        container_layout.addWidget(self._group_container)
        main_layout.addLayout(container_layout)
        
        # Group 1: Add Package
        self._search_group = ExpandableGroupBox("Add Package")
        search_layout = QVBoxLayout()
        
        # Package name input
        name_layout = QHBoxLayout()
        name_label = QLabel("Package Name:")
        self.package_name_input = QLineEdit()
        self.package_name_input.setPlaceholderText("Enter package name (e.g., requests)")
        self.package_name_input.returnPressed.connect(self._on_search_clicked)
        self.package_name_input.editingFinished.connect(self._on_package_name_editing_finished)
        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search_clicked)
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.package_name_input)
        name_layout.addWidget(self.search_button)
        search_layout.addLayout(name_layout)
        
        # Version selection
        version_layout = QHBoxLayout()
        version_label = QLabel("Version:")
        self.version_dropdown = QComboBox()
        self.version_dropdown.setMinimumWidth(150)
        self.version_dropdown.setEnabled(False)
        self.version_dropdown.currentIndexChanged.connect(self._on_version_changed)
        version_layout.addWidget(version_label)
        version_layout.addWidget(self.version_dropdown)
        version_layout.addStretch()
        search_layout.addLayout(version_layout)
        
        # Extras selection
        self.extras_label = QLabel("Extras (optional):")
        search_layout.addWidget(self.extras_label)
        self.extras_list = QListWidget()
        #self.extras_list.setMaximumHeight(100)
        self.extras_list.setMinimumHeight(30)
        self.extras_list.setEnabled(False)
        
        search_layout.addWidget(self.extras_list,1)
        
        # Manual extras input
        manual_extras_layout = QHBoxLayout()
        self.manual_extra_input = QLineEdit()
        self.manual_extra_input.setPlaceholderText("Enter custom extra (e.g., dev, test)")
        self.add_extra_button = QPushButton("Add Extra")
        self.add_extra_button.clicked.connect(self._on_add_manual_extra_clicked)
        manual_extras_layout.addWidget(self.manual_extra_input)
        manual_extras_layout.addWidget(self.add_extra_button)
        search_layout.addLayout(manual_extras_layout)
        
        # Add to list button
        add_button_layout = QHBoxLayout()
        #add_button_layout.addStretch()
        self.add_to_list_button = QPushButton("Add to List")
        self.add_to_list_button.setObjectName("orangeButton")
        self.add_to_list_button.setEnabled(False)
        self.add_to_list_button.clicked.connect(self._on_add_to_list_clicked)
        add_button_layout.addWidget(self.add_to_list_button)
        search_layout.addLayout(add_button_layout)
        self._search_group.setLayout(search_layout)
        self._group_container.addGroup(self._search_group)
        
        self._search_group.setFrameState(FrameState.MINIMIZE)

        # Group 2: Packages
        self._packages_group = ExpandableGroupBox("Packages")
        packages_layout = QVBoxLayout()
        
        self.package_table = QTableWidget()
        self.package_table.setColumnCount(4)
        self.package_table.setHorizontalHeaderLabels(["Name", "Version", "Extras", "Status"])
            
        # Column widths - allow manual resizing
        header = self.package_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Interactive)  # Name - interactive
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Interactive)  # Version - interactive
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)  # Extras - interactive
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Interactive)  # Status - interactive
        # Set initial widths
        header.resizeSection(0, 150)  # Name
        header.resizeSection(1, 100)  # Version
        header.resizeSection(2, 100)  # Extras
        header.resizeSection(3, 120)  # Status
        self.package_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.package_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        
        # Make table readonly - remove delegates and disable editing
        # self.version_delegate = VersionComboDelegate(self, self.package_table)
        # self.package_table.setItemDelegateForColumn(1, self.version_delegate)
        # self.extras_delegate = ExtrasComboDelegate(self, self.package_table)
        # self.package_table.setItemDelegateForColumn(2, self.extras_delegate)
        
        # Make table not editable
        self.package_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Connect double-click to fill form
        self.package_table.doubleClicked.connect(self._on_package_double_clicked)
        
        # Enable context menu for package table
        self.package_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.package_table.customContextMenuRequested.connect(self._on_package_context_menu)
        self.package_table.setSizeAdjustPolicy(QTableWidget.SizeAdjustPolicy.AdjustToContents)
        packages_layout.addWidget(self.package_table,1)
        
        # Buttons section
        button_layout = QHBoxLayout()
        
        self.remove_button = QPushButton("Remove")
        self.remove_button.clicked.connect(self._on_remove_clicked)
        
        self.restore_button = QPushButton("Restore")
        self.restore_button.clicked.connect(self._on_restore_clicked)
        
        self.see_resolution_button = QPushButton("See Resolution")
        self.see_resolution_button.clicked.connect(self._on_see_resolution_clicked)
        
        self.install_update_button = QPushButton("Install/Update")
        self.install_update_button.setObjectName("orangeButton")
        self.install_update_button.clicked.connect(self._on_install_all_clicked)
        
        button_layout.addWidget(self.remove_button)
        button_layout.addWidget(self.restore_button)
        button_layout.addWidget(self.see_resolution_button)
        button_layout.addStretch()
        button_layout.addWidget(self.install_update_button)
        
        packages_layout.addLayout(button_layout)
        
        self._packages_group.setLayout(packages_layout)
        self._group_container.addGroup(self._packages_group)

        self._packages_group.setFrameState(FrameState.MINIMIZE)
        
        # Group 3: Pip Output
        self._pip_group = ExpandableGroupBox("Pip Output")
        pip_layout = QVBoxLayout()
        
        self.pip_console = QTextEditWithClear()
        self.pip_console.setObjectName("consoleText")
        self.pip_console.setReadOnly(True)
        self.pip_console.setPlaceholderText("Pip output will appear here...")
        #self.pip_console.setMaximumHeight(150)
        pip_layout.addWidget(self.pip_console,1)
        
        self._pip_group.setLayout(pip_layout)
        self._group_container.addGroup(self._pip_group)

        self._pip_group.setFrameState(FrameState.MINIMIZE)

        # Group 4: Python Paths
        self._paths_group = ExpandableGroupBox("Python Paths")
        paths_layout = QVBoxLayout()
        
        # Table for python paths
        self.paths_table = QTableWidget()
        self.paths_table.setColumnCount(1)
        self.paths_table.setHorizontalHeaderLabels(["Path"])
        #self.paths_table.setMaximumHeight(150)
        
        # Column widths
        paths_header = self.paths_table.horizontalHeader()
        paths_header.setStretchLastSection(True)
        
        self.paths_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.paths_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.paths_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        paths_layout.addWidget(self.paths_table,1)
        
        # Buttons for paths
        paths_button_layout = QHBoxLayout()
        self.add_path_btn = QPushButton("Add Path")
        self.add_path_btn.setObjectName("orangeButton")
        self.add_path_btn.clicked.connect(self._on_add_path_clicked)
        self.remove_path_btn = QPushButton("Remove Path")
        self.remove_path_btn.clicked.connect(self._on_remove_path_clicked)
        paths_button_layout.addWidget(self.add_path_btn)
        paths_button_layout.addWidget(self.remove_path_btn)
        paths_button_layout.addStretch()
        paths_layout.addLayout(paths_button_layout)
        
        self._paths_group.setLayout(paths_layout)
        self._group_container.addGroup(self._paths_group)
        self._paths_group.setFrameState(FrameState.MINIMIZE)

        #Cache update connection
        self.update_caches.connect(self._update_caches)

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
        
        # If it was the only workbook or the selected one was removed, clear the table
        if self.workbook_dropdown.count() == 0:
            self.package_table.setRowCount(0)
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
    
    def _on_workbook_changed(self, index):
        """Handle workbook selection change - request packages."""
        workbook_id = self.get_current_workbook()
        if workbook_id:
            packages=self._packages.get(workbook_id, [])
            package_errors=self._package_errors.get(workbook_id, {})
            for pkg in packages:
                pkg_name = pkg.get("name", "")
                pkg_status = pkg.get("status", "")
                            
                # If package is installed but has dependency errors, show "installed_with_errors"
                if pkg_status == "installed" and pkg_name in package_errors:
                    pkg["status"] = "installed_with_errors"

            self.set_package_list(packages)
            python_paths=self._python_paths.get(workbook_id, [])
            logger.debug(f"[PYTHON_PATH] Setting python paths for workbook {workbook_id}: {python_paths}")
            self.set_python_paths(python_paths)

            #self.get_workbook_packages_requested.emit(workbook_id)

    def _update_caches(self,workbook_id:str, packages: List[Dict],package_errors:Dict ,python_paths: List[str]):
        """
        Update the cached data for a workbook.
        
        Args:
            workbook_id: The workbook identifier
            packages: List of package dicts
            package_errors: Dict of package errors
            python_paths: List of python paths
        """
        if packages is not None:
            self._packages[workbook_id] = packages
        if packages is not None:
            self._package_errors[workbook_id] = package_errors
        if python_paths is not None:
            self._python_paths[workbook_id] = python_paths
        logger.debug(f"[PYTHON_PATH] Cached python paths for workbook {workbook_id}: {python_paths}={self._python_paths.get(workbook_id)}")
        current_workbook_id=self.get_current_workbook()
        if current_workbook_id == workbook_id:
            self._on_workbook_changed(-1)


    def set_packages(self, packages: List[Dict]):
        """
        Set the package list.
        
        Args:
            packages: List of package dicts with 'name', 'version', 'extras', 'status' keys
        """
        self.package_table.setRowCount(len(packages))
        for row, pkg in enumerate(packages):
            self.package_table.setItem(
                row, 0, QTableWidgetItem(pkg.get("name", ""))
            )
            self.package_table.setItem(
                row, 1, QTableWidgetItem(pkg.get("version", ""))
            )
            self.package_table.setItem(
                row, 2, QTableWidgetItem(pkg.get("extras", ""))
            )
            self.package_table.setItem(
                row, 3, QTableWidgetItem(pkg.get("status", ""))
            )

    def log_pip_output(self, message: str):
        """
        Log a message to the pip console.
        
        Args:
            message: The message to log
        """
        
        self.log_pip_output_colored(message)
        '''
        if message and not message.endswith('\n'):
            message += "\n"
        
        self.pip_console.append(message)
        '''

    def _format_console_html(self, text: str, color: Optional[str]) -> str:
        """
        Format text for console output with HTML escaping and newline handling.
        
        Args:
            text: The text to format.
            color: The color to use for the text.
            
        Returns:
            HTML formatted string with proper color and newline handling.
        """
        escaped_text = html.escape(text)
        # Replace newlines with <br> for proper HTML display
        formatted_text = escaped_text.replace('\n', '<br>')
        color_style=f'color: {color};' if color else ''
        return f'<span style="{color_style}">{formatted_text}</span>'

    def log_pip_output_colored(self, message: str, color: Optional[str] = None):
        """
        Log a message to the console with optional color.
        
        This method ensures proper line breaks for status messages.
        If the message doesn't end with a newline, one is added.
        For stdout/stderr from code execution, use direct insertHtml calls
        which preserve the exact newline behavior from print().
        
        Args:
            message: The message to log.
            color: The color to use for the message (default: gray/white #d4d4d4).
        """
        self.pip_console.moveCursor(QTextCursor.MoveOperation.End)
        formatted_html = self._format_console_html(message, color)
        # Only add trailing <br> if the message doesn't already end with a newline
        # (which would have been converted to <br> by _format_console_html)
        if message and not message.endswith('\n') and not message.endswith('<br>'):
            formatted_html += "<br>"
        self.pip_console.insertHtml(formatted_html)


    def clear_pip_output(self):
        """Clear the pip console output."""
        self.pip_console.clear()

    def set_package_errors(self, errors: Dict[str, List[str]]):
        """
        Set the package errors dictionary.
        
        Args:
            errors: Dictionary of {package_name: [error_messages]}
        """
        self._package_errors = errors

    def _on_package_context_menu(self, position):
        """Handle right-click context menu on package table."""
        item = self.package_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        package_name_item = self.package_table.item(row, 0)
        if not package_name_item:
            return
        
        package_name = package_name_item.text()
        
        # Check if this package has errors
        workbook_id=self.get_current_workbook()
        errors = self._package_errors.get(workbook_id,{}).get(package_name, [])
        
        menu = QMenu(self)
        
        if errors:
            show_errors_action = menu.addAction(f"Show Errors ({len(errors)})")
            show_errors_action.triggered.connect(
                lambda: self._show_package_errors_popup(package_name, errors)
            )
        else:
            no_errors_action = menu.addAction("No errors")
            no_errors_action.setEnabled(False)
        
        menu.exec(self.package_table.mapToGlobal(position))

    def _show_package_errors_popup(self, package_name: str, errors: List[str]):
        """
        Show a readonly popup with package errors.
        
        Args:
            package_name: The package name
            errors: List of error messages
        """
        dialog = QDialog(self)
        dialog.setWindowTitle(f"Errors for {package_name}")
        dialog.resize(500, 300)
        
        layout = QVBoxLayout()
        
        # Header label
        label = QLabel(f"Errors encountered while installing {package_name}:")
        layout.addWidget(label)
        
        # Error text area (readonly)
        error_text = QTextEdit()
        error_text.setReadOnly(True)
        error_text.setStyleSheet("""
            QTextEdit {
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 12px;
                background-color: #1e1e1e;
                color: #E74C3C;
            }
        """)
        
        # Add each error on its own line
        #error_text.setText("\n\n".join(errors))
        error_text.setText("\n".join(errors))
        layout.addWidget(error_text)
        
        # OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec()

    def _on_search_clicked(self):
        """Handle search button click."""
        package_name = self.package_name_input.text().strip()
        if package_name:
            self._current_package_name = package_name
            self.log_pip_output(f"Searching for package: {package_name}")
            # Request versions for the package
            self.get_versions_requested.emit(package_name)
            # Disable controls while loading
            self.version_dropdown.setEnabled(False)
            self.extras_list.setEnabled(False)
            self.add_to_list_button.setEnabled(False)
    
    def _on_package_name_editing_finished(self):
        """Handle when user leaves package name input - trigger search if text changed."""
        package_name = self.package_name_input.text().strip()
        if package_name and package_name != self._current_package_name:
            self._on_search_clicked()

    def _on_version_changed(self, index):
        """Handle version dropdown selection change."""
        if index >= 0 and self._current_package_name:
            version = self.version_dropdown.currentText()
            if version:
                self.log_pip_output(f"Loading extras for {self._current_package_name} {version}...")
                # Request extras for the selected version
                self.get_extras_requested.emit(self._current_package_name, version)
                self.extras_list.setEnabled(False)
                self.add_to_list_button.setEnabled(False)

    def _on_add_to_list_clicked(self):
        """Handle add to list button click - update existing or add new."""
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            self.log_pip_output("Error: No workbook selected")
            return
        
        if not self._current_package_name:
            self.log_pip_output("Error: No package selected")
            return
        
        version = self.version_dropdown.currentText()
        if not version:
            self.log_pip_output("Error: No version selected")
            return
        
        # Get selected extras
        selected_extras = []
        for i in range(self.extras_list.count()):
            item = self.extras_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                selected_extras.append(item.text())
        
        # Check if package already exists in the list
        for row in range(self.package_table.rowCount()):
            existing_name = self.package_table.item(row, 0).text()
            if existing_name.lower() == self._current_package_name.lower():
                # Update existing row
                existing_version = self.package_table.item(row, 1).text()
                existing_extras = self.package_table.item(row, 2).text()
                
                new_extras_str = ",".join(sorted(selected_extras)) if selected_extras else ""
                
                if existing_version == version and existing_extras == new_extras_str:
                    # No change
                    self.log_pip_output(f"Package {self._current_package_name}=={version} already in list with same configuration")
                    return
                
                # Update row
                self.package_table.item(row, 1).setText(version)
                self.package_table.item(row, 2).setText(new_extras_str)
                self.update_package_status(self._current_package_name, "pending_update")
                
                # Emit update signal
                self.update_package_requested.emit(workbook_id, self._current_package_name, version, selected_extras)
                
                self.log_pip_output(
                    f"Updated package: {self._current_package_name}=={version} "
                    f"with extras: {selected_extras if selected_extras else 'none'}"
                )
                return
        
        # Add new package
        self.log_pip_output(
            f"Adding package: {self._current_package_name}=={version} "
            f"with extras: {selected_extras if selected_extras else 'none'}"
        )
        
        # Emit signal to add package
        self.add_package_requested.emit(
            workbook_id,
            self._current_package_name,
            version,
            selected_extras
        )

    def _on_package_double_clicked(self, index):
        """Handle double-click on package row - fill Add Package form."""
        row = index.row()
        
        # Get package data from row
        name_item = self.package_table.item(row, 0)
        version_item = self.package_table.item(row, 1)
        extras_item = self.package_table.item(row, 2)
        
        if not name_item:
            return
        
        package_name = name_item.text()
        version = version_item.text() if version_item else ""
        extras_str = extras_item.text() if extras_item else ""
        
        # Parse extras
        extras = [e.strip() for e in extras_str.split(",") if e.strip()]
        
        # Store for later selection after async responses
        self._pending_edit_version = version
        self._pending_edit_extras = extras
        
        # Fill package name and trigger search
        self.package_name_input.setText(package_name)
        self._current_package_name = package_name
        
        self.log_pip_output(f"Editing package: {package_name}")
        
        # Trigger search to get versions
        self.get_versions_requested.emit(package_name)
        
        # Disable controls while loading
        self.version_dropdown.setEnabled(False)
        self.extras_list.setEnabled(False)
        self.add_to_list_button.setEnabled(False)
    
    def _clear_pending_edit_state(self):
        """Clear pending edit state after use."""
        self._pending_edit_version = None
        self._pending_edit_extras = []
    
    def _on_add_manual_extra_clicked(self):
        """Handle adding a manual extra to the extras list."""
        extra_name = self.manual_extra_input.text().strip()
        if not extra_name:
            return
        
        # Validate extra name (alphanumeric with hyphens/underscores)
        import re
        if not re.match(r'^[a-zA-Z0-9_-]+$', extra_name):
            self.log_pip_output(f"Invalid extra name: {extra_name}. Use only letters, numbers, hyphens, underscores.")
            return
        
        # Check if already exists
        for i in range(self.extras_list.count()):
            if self.extras_list.item(i).text() == extra_name:
                self.log_pip_output(f"Extra '{extra_name}' already in list")
                return
        
        # Add to list (checked by default)
        item = QListWidgetItem(extra_name)
        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
        item.setCheckState(Qt.CheckState.Checked)
        self.extras_list.addItem(item)
        
        # Clear input
        self.manual_extra_input.clear()
        self.log_pip_output(f"Added custom extra: {extra_name}")

    def _on_remove_clicked(self):
        """Handle remove button click - set status to 'to_remove' instead of removing."""
        workbook_id = self.get_current_workbook()
        selected_rows = self.package_table.selectionModel().selectedRows()
        if workbook_id and selected_rows:
            row = selected_rows[0].row()
            package_name = self.package_table.item(row, 0).text()
            self.log_pip_output(f"Marking package for removal: {package_name}")
            self.update_package_status(package_name, "to_remove")
            # Emit signal to sync status to server
            self.update_package_status_requested.emit(workbook_id, package_name, "to_remove")
    
    def _on_restore_clicked(self):
        """Restore package list to last installed state."""
        workbook_id = self.get_current_workbook()
        if workbook_id:
            self.restore_requested.emit(workbook_id)
            self.log_pip_output(f"Restoring package list to last installed state...")
    
    def _on_see_resolution_clicked(self):
        """Handle see resolution button click."""
        workbook_id = self.get_current_workbook()
        if workbook_id:
            self.see_resolution_requested.emit(workbook_id)

    def set_available_versions(self, package_name: str, versions: List[str]):
        """
        Set the available versions for a package.
        
        Args:
            package_name: The package name.
            versions: List of version strings (descending order, latest first).
        """
        # Remove duplicates while preserving order
        seen = set()
        unique_versions = []
        for v in versions:
            if v not in seen:
                seen.add(v)
                unique_versions.append(v)
        
        # Update search UI only if this is for the current search
        if package_name != self._current_package_name:
            return  # Skip UI update for stale responses
        
        self._available_versions = unique_versions
        self.version_dropdown.clear()
        
        if unique_versions:
            self.version_dropdown.addItems(unique_versions)
            self.version_dropdown.setEnabled(True)
            self.log_pip_output(f"Found {len(unique_versions)} versions for {package_name}")
            
            # If we have a pending edit version, select it
            if self._pending_edit_version:
                idx = self.version_dropdown.findText(self._pending_edit_version)
                if idx >= 0:
                    self.version_dropdown.setCurrentIndex(idx)
                # Clear only version, extras will be cleared when they load
                self._pending_edit_version = None
            
            # Trigger extras query
            if self.version_dropdown.count() > 0:
                self._on_version_changed(self.version_dropdown.currentIndex())
        else:
            self.log_pip_output(f"No versions found for {package_name}")
            self.version_dropdown.setEnabled(False)
            self.extras_list.clear()
            self.extras_list.setEnabled(False)
            self.add_to_list_button.setEnabled(False)

    def set_available_extras(self, package_name: str, version: str, extras: List[str]):
        """
        Set the available extras for a package version.
        
        Args:
            package_name: The package name.
            version: The package version.
            extras: List of extra names.
        """
        # Update search UI only if this is for the current search
        if package_name != self._current_package_name:
            return  # Skip UI update for stale responses
        
        current_version = self.version_dropdown.currentText()
        if version != current_version:
            return  # Skip UI update for stale responses
        
        self._available_extras = extras
        self.extras_list.clear()
        
        if extras:
            for extra in sorted(extras):
                item = QListWidgetItem(extra)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                
                # If we have pending edit extras, check matching ones
                if extra in self._pending_edit_extras:
                    item.setCheckState(Qt.CheckState.Checked)
                else:
                    item.setCheckState(Qt.CheckState.Unchecked)
                
                self.extras_list.addItem(item)
            
            # Clear all pending state after extras are loaded
            self._clear_pending_edit_state()
            
            self.extras_list.setEnabled(True)
            self.log_pip_output(f"Found {len(extras)} extras for {package_name} {version}")
        else:
            self.log_pip_output(f"No extras available for {package_name} {version}")
            self.extras_list.setEnabled(True)  # Enable anyway to show empty state
        
        # Enable add button now that we have all the info
        self.add_to_list_button.setEnabled(True)

    def set_package_info(self, package_name: str, info: Dict):
        """
        Display package information.
        
        Args:
            package_name: The package name.
            info: Dictionary with 'name', 'latest_version', 'summary', or 'error'.
        """
        if "error" in info:
            self.log_pip_output(f"Error: {info['error']}")
        else:
            name = info.get("name", package_name)
            version = info.get("latest_version", "unknown")
            summary = info.get("summary", "No description")
            self.log_pip_output(f"{name} ({version}): {summary}")

    def _on_install_all_clicked(self):
        """Handle install/update button click."""
        workbook_id = self.get_current_workbook()
        if workbook_id:
            self.install_all_requested.emit(workbook_id)
    
    def update_package_status(self, package_name: str, status: str, message: str = ""):
        """
        Update the status of a package in the table.
        
        Args:
            package_name: Name of the package
            status: Status string ("pending", "installing", "installed", "error")
            message: Optional status message
        """
        for row in range(self.package_table.rowCount()):
            if self.package_table.item(row, 0).text() == package_name:
                status_item = self.package_table.item(row, 3)
                if not status_item:
                    status_item = QTableWidgetItem()
                    self.package_table.setItem(row, 3, status_item)
                
                # Update text and color based on status
                if status in STATUS_COLORS:
                    # Use STATUS_LABELS for display text
                    if status == "error" and message:
                        display_text = f"Error: {message}"
                    else:
                        display_text = STATUS_LABELS.get(status, status.capitalize())
                    
                    status_item.setText(display_text)
                    status_item.setForeground(STATUS_COLORS[status])
                else:
                    # Fallback for unknown status
                    status_item.setText(status)
                break
    
    def set_package_list(self, packages: List[dict]):
        """
        Set the full package list from the server.
        
        Args:
            packages: List of package dictionaries with "name", "version", "extras", "status"
        """
        self.package_table.setRowCount(0)
        for pkg in packages:
            row = self.package_table.rowCount()
            self.package_table.insertRow(row)
            
            # Name
            name_item = QTableWidgetItem(pkg["name"])
            self.package_table.setItem(row, 0, name_item)
            
            # Version
            version_item = QTableWidgetItem(pkg["version"])
            self.package_table.setItem(row, 1, version_item)
            
            # Extras
            extras = pkg.get("extras", [])
            extras_str = ", ".join(extras) if extras else ""
            extras_item = QTableWidgetItem(extras_str)
            self.package_table.setItem(row, 2, extras_item)
            
            # Status
            status = pkg.get("status", "pending")
            status_item = QTableWidgetItem()
            self.package_table.setItem(row, 3, status_item)
            self.update_package_status(pkg["name"], status)
    
    def _on_add_path_clicked(self):
        """Handle add path button click - open folder dialog."""
        from PySide6.QtWidgets import QFileDialog
        
        # Open folder selection dialog
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Python Library Path",
            ""
        )
        
        if folder:
            # Add to paths table
            self._add_path_to_table(folder)
            # Update the server
            self._sync_python_paths()
    
    def _on_remove_path_clicked(self):
        """Handle remove path button click."""
        current_row = self.paths_table.currentRow()
        if current_row >= 0:
            self.paths_table.removeRow(current_row)
            # Update the server
            self._sync_python_paths()
    
    
    def _add_path_to_table(self, path: str):
        """Add a path to the paths table."""
        logger.info(f"[PYTHON_PATH] _add_path_to_table: path={path}")
        
        row = self.paths_table.rowCount()
        self.paths_table.insertRow(row)
        
        # Path
        path_item = QTableWidgetItem(path)
        self.paths_table.setItem(row, 0, path_item)
    
    def _sync_python_paths(self):
        """Sync python paths to server."""
        workbook_id = self.get_current_workbook()
        if not workbook_id:
            return
        
        # Collect paths from table (now just simple strings)
        paths = []
        for row in range(self.paths_table.rowCount()):
            path_item = self.paths_table.item(row, 0)
            if path_item:
                path = path_item.text()
                paths.append(path)
        
        # Emit signal to update
        self.update_python_paths_requested.emit(workbook_id, paths)
    
    def set_python_paths(self, paths: List[Union[str, dict]]):
        """
        Set python paths from server.
        
        Args:
            paths: List of path strings or dicts (for backwards compatibility with old format)
        """
        logger.info(f"[PYTHON_PATH] set_python_paths called with {len(paths)} paths")
        logger.info(f"[PYTHON_PATH] paths={paths}")
        
        # Build temporary list of normalized paths
        # Note: We normalize here rather than importing business_layer.server.normalize_python_paths
        # to maintain separation between GUI and business layer (avoid circular dependencies)
        normalized_paths = []
        for i, path in enumerate(paths):
            # Handle both old dict format and new string format
            if path is None:
                # Skip None values silently
                continue
            elif isinstance(path, dict):
                path_str = path.get("path", "")
                logger.debug(f"[PYTHON_PATH] Converting dict to string: {path} -> {path_str}")
            else:
                path_str = str(path) if path else ""
            
            if path_str:
                logger.info(f"[PYTHON_PATH] Adding path {i}: {path_str}")
                normalized_paths.append(path_str)
        
        # Update instance variable and table atomically
        #self._python_paths = normalized_paths
        
        # Clear and repopulate table
        self.paths_table.setRowCount(0)
        for path_str in normalized_paths:
            self._add_path_to_table(path_str)
    
    def show_resolved_deps_popup(self, deps: List[dict]):
        """
        Show readonly popup with resolved dependencies.
        
        Args:
            deps: List of resolved dependency dicts with keys:
                  - name: Package name
                  - version: Resolved version
                  - extras: List of extras
                  - is_direct: True if directly requested, False if transitive dependency
                  - from_dist: True if from current Python environment
        """
        from PySide6.QtWidgets import QDialog, QVBoxLayout, QTableWidget, QTableWidgetItem, QDialogButtonBox, QLabel
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Resolved Dependencies")
        dialog.resize(700, 400)  # Slightly wider for new column
        
        layout = QVBoxLayout()
        
        # Add explanation label
        label = QLabel("All resolved dependencies (including transitive dependencies):")
        layout.addWidget(label)
        
        # Create table with 5 columns now
        table = QTableWidget()
        table.setColumnCount(5)  # Changed from 4 to 5
        table.setHorizontalHeaderLabels(["Name", "Version", "Extras", "Type", "From Env"])  # Added "From Env"
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Populate table
        table.setRowCount(len(deps))
        for row, dep in enumerate(deps):
            # Name
            name_item = QTableWidgetItem(dep["name"])
            table.setItem(row, 0, name_item)
            
            # Version
            version_item = QTableWidgetItem(dep["version"])
            table.setItem(row, 1, version_item)
            
            # Extras
            extras = dep.get("extras", [])
            extras_str = ", ".join(extras) if extras else ""
            extras_item = QTableWidgetItem(extras_str)
            table.setItem(row, 2, extras_item)
            
            # Type (Direct/Dependency)
            dep_type = "Direct" if dep.get("is_direct", False) else "Dependency["+','.join(dep.get("source", []))+"]"
            type_item = QTableWidgetItem(dep_type)
            table.setItem(row, 3, type_item)
            
            # From Env (new column)
            from_dist = dep.get("from_dist", False)
            from_env_str = "Yes" if from_dist else "No"
            from_env_item = QTableWidgetItem(from_env_str)
            table.setItem(row, 4, from_env_item)

            is_error=dep.get('is_error', False)
            if is_error:    
                for item in [name_item, version_item, extras_item, type_item, from_env_item]:
                    item.setForeground(STATUS_COLORS.get("error", Qt.GlobalColor.red))

        
        # Resize columns to content
        table.resizeColumnsToContents()
        layout.addWidget(table)
        
        # Add OK button
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)
        
        dialog.setLayout(layout)
        dialog.exec()
