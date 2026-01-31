"""
XPyCode IDE - Project Explorer

This module provides the Project Explorer widget, a tree view for
navigating files and modules in the project.
"""

from PySide6.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from typing import Dict, List, Optional

from .icon_utils import strip_icon_prefix

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)

def _strip_py_extension(name: str) -> str:
    """Strip .py extension from module name if present."""
    if name.endswith('.py'):
        return name[:-3]
    return name


class ProjectExplorer(QTreeWidget):
    """
    Project Explorer widget for navigating project files and modules.
    
    Inherits from QTreeWidget to provide a hierarchical view of the
    project structure.
    
    Module names are stored and displayed WITHOUT the .py extension.
    """

    # Custom signals for menu actions
    new_module_requested = Signal(str)  # workbook_id
    delete_module_requested = Signal(str, str)  # workbook_id, module_name
    rename_module_requested = Signal(str, str, str)  # workbook_id, old_name, new_name
    open_module_requested = Signal(str, str)  # workbook_id, module_name
    
    # Signals for workbook list changes (for syncing with EventManager)
    workbook_added = Signal(str,str)  # workbook_id
    workbook_removed = Signal(str)  # workbook_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workbook_items: Dict[str, QTreeWidgetItem] = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        self.setHeaderLabel("🗃 Project")
        self.setAnimated(True)
        self.setIndentation(20)
        self.setRootIsDecorated(True)
        self.setSortingEnabled(True)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
        # Enable double-click to open modules
        self.itemDoubleClicked.connect(self._on_item_double_clicked)

    def _on_item_double_clicked(self, item: QTreeWidgetItem, column: int):
        """Handle double-click on an item to open a module."""
        # Only open modules (items with a parent workbook)
        parent_item = item.parent()
        if parent_item is None:
            # This is a workbook, not a module - do nothing
            return
        
        # Get workbook_id from parent
        workbook_id = parent_item.data(0, Qt.ItemDataRole.UserRole)
        if workbook_id is None:
            workbook_id = strip_icon_prefix(parent_item.text(0))
        
        # Get module name (strip icon prefix if present)
        module_name = strip_icon_prefix(item.text(0))
        
        # Emit signal to open the module
        self.open_module_requested.emit(workbook_id, module_name)

    def _show_context_menu(self, position):
        """Show context menu for the item at the given position."""
        item = self.itemAt(position)
        menu = QMenu(self)

        if item is None:
            # Clicked on background - show "New Module" if there's exactly one workbook
            # or if a workbook is selected
            workbook_id = self.get_selected_workbook_id()
            if workbook_id:
                new_module_action = QAction("New Module", self)
                new_module_action.triggered.connect(
                    lambda: self.new_module_requested.emit(workbook_id)
                )
                menu.addAction(new_module_action)
            elif len(self._workbook_items) == 1:
                # Only one workbook, use it
                workbook_id = next(iter(self._workbook_items.keys()))
                new_module_action = QAction("New Module", self)
                new_module_action.triggered.connect(
                    lambda: self.new_module_requested.emit(workbook_id)
                )
                menu.addAction(new_module_action)
            else:
                # No workbooks or can't determine which one
                return
        # Check if item is a workbook (top-level item)
        elif item.parent() is None:
            # Get workbook_id from UserRole, fall back to text for backwards compatibility
            workbook_id = item.data(0, Qt.ItemDataRole.UserRole)
            if workbook_id is None:
                workbook_id = strip_icon_prefix(item.text(0))
            new_module_action = QAction("New Module", self)
            new_module_action.triggered.connect(
                lambda: self.new_module_requested.emit(workbook_id)
            )
            menu.addAction(new_module_action)
        else:
            # Item is a module (child of workbook)
            parent_item = item.parent()
            if parent_item:
                # Get workbook_id from UserRole, fall back to text for backwards compatibility
                workbook_id = parent_item.data(0, Qt.ItemDataRole.UserRole)
                if workbook_id is None:
                    workbook_id = strip_icon_prefix(parent_item.text(0))
                module_name = strip_icon_prefix(item.text(0))
                
                rename_module_action = QAction("Rename Module", self)
                rename_module_action.triggered.connect(
                    lambda: self._on_rename_module_action(workbook_id, module_name)
                )
                menu.addAction(rename_module_action)
                
                delete_module_action = QAction("Delete Module", self)
                delete_module_action.triggered.connect(
                    lambda: self.delete_module_requested.emit(workbook_id, module_name)
                )
                menu.addAction(delete_module_action)

        menu.exec(self.mapToGlobal(position))

    def add_workbook(self, workbook_id: str, name: Optional[str] = None) -> QTreeWidgetItem:
        """
        Add a workbook to the project explorer.
        
        Args:
            workbook_id: The unique identifier for the workbook
            name: Optional display name for the workbook
            
        Returns:
            The created workbook item
        """
        if workbook_id in self._workbook_items:
            return self._workbook_items[workbook_id]
        
        item = QTreeWidgetItem(self)
        # Use the provided name for display, fall back to workbook_id
        display_name = name if name else workbook_id
        item.setText(0, f"📗 {display_name}")
        # Store the workbook_id in UserRole for later retrieval
        item.setData(0, Qt.ItemDataRole.UserRole, workbook_id)
        item.setExpanded(True)
        self._workbook_items[workbook_id] = item
        
        # Emit signal for workbook addition
        self.workbook_added.emit(workbook_id,name)
        
        return item

    def remove_workbook(self, workbook_id: str):
        """
        Remove a workbook from the project explorer.
        
        Args:
            workbook_id: The unique identifier for the workbook
        """
        if workbook_id in self._workbook_items:
            item = self._workbook_items[workbook_id]
            index = self.indexOfTopLevelItem(item)
            if index >= 0:
                self.takeTopLevelItem(index)
            del self._workbook_items[workbook_id]
            
            # Emit signal for workbook removal
            self.workbook_removed.emit(workbook_id)

    def update_workbook_name(self, workbook_id: str, new_name: str):
        """
        Update the display name of a workbook.
        
        Args:
            workbook_id: The unique identifier for the workbook
            new_name: The new display name for the workbook
        """
        if workbook_id in self._workbook_items:
            item = self._workbook_items[workbook_id]
            item.setText(0, f"📗 {new_name}")

    def add_module(self, workbook_id: str, module_name: str) -> Optional[QTreeWidgetItem]:
        """
        Add a module under the specified workbook.
        
        Module names should NOT include the .py extension.
        
        Args:
            workbook_id: The workbook to add the module to
            module_name: The name of the module (without .py extension)
            
        Returns:
            The created module item, or None if workbook not found
        """
        if workbook_id not in self._workbook_items:
            return None
        
        # Strip .py extension if present (for backwards compatibility)
        module_name = _strip_py_extension(module_name)
        
        # Check if module already exists
        parent_item = self._workbook_items[workbook_id]
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if child.text(0) == f"🐍 {module_name}":
                return child  # Already exists
        
        module_item = QTreeWidgetItem(parent_item)
        module_item.setText(0, f"🐍 {module_name}")
        return module_item

    def remove_module(self, workbook_id: str, module_name: str) -> bool:
        """
        Remove a module from the specified workbook.
        
        Args:
            workbook_id: The workbook to remove the module from
            module_name: The name of the module (without .py extension)
            
        Returns:
            True if module was removed, False otherwise
        """
        if workbook_id not in self._workbook_items:
            return False
        
        # Strip .py extension if present
        module_name = _strip_py_extension(module_name)
        
        parent_item = self._workbook_items[workbook_id]
        for i in range(parent_item.childCount()):
            child = parent_item.child(i)
            if strip_icon_prefix(child.text(0)) == module_name:
                parent_item.removeChild(child)
                return True
        return False

    def set_modules(self, workbook_id: str, modules: List[str]):
        """
        Set the list of modules for a workbook, replacing any existing modules.
        
        Args:
            workbook_id: The workbook to set modules for
            modules: List of module names (without .py extension)
        """
        if workbook_id not in self._workbook_items:
            return
        
        parent_item = self._workbook_items[workbook_id]
        
        # Remove all existing modules
        while parent_item.childCount() > 0:
            parent_item.removeChild(parent_item.child(0))
        
        # Add new modules
        for module_name in modules:
            # Strip .py extension if present
            module_name = _strip_py_extension(module_name)
            module_item = QTreeWidgetItem(parent_item)
            module_item.setText(0, f"🐍 {module_name}")

    def add_folder(self, name: str, parent: Optional[QTreeWidgetItem] = None) -> QTreeWidgetItem:
        """
        Add a folder to the project explorer.
        
        Args:
            name: The folder name
            parent: The parent item (None for root level)
            
        Returns:
            The created folder item
        """
        if parent is None:
            item = QTreeWidgetItem(self)
        else:
            item = QTreeWidgetItem(parent)
        item.setText(0, name)
        return item

    def add_file(self, name: str, parent: Optional[QTreeWidgetItem] = None) -> QTreeWidgetItem:
        """
        Add a file to the project explorer.
        
        Args:
            name: The file name
            parent: The parent item (None for root level)
            
        Returns:
            The created file item
        """
        if parent is None:
            item = QTreeWidgetItem(self)
        else:
            item = QTreeWidgetItem(parent)
        item.setText(0, name)
        return item

    def clear_project(self):
        """Clear all items from the project explorer."""
        self.clear()
        self._workbook_items.clear()

    def load_project(self, project_path: str):
        """
        Load a project from the given path.
        
        Args:
            project_path: Path to the project directory
        """
        # Placeholder for actual project loading logic
        self.clear()
        root = QTreeWidgetItem(self)
        root.setText(0, project_path.split("/")[-1] if "/" in project_path else project_path)
        root.setExpanded(True)

    def get_selected_workbook_id(self) -> Optional[str]:
        """
        Get the workbook ID of the currently selected item.
        
        Returns:
            The workbook_id if a workbook or its child is selected, None otherwise.
        """
        selected_items = self.selectedItems()
        if not selected_items:
            return None
        
        item = selected_items[0]
        
        # If item is a child (e.g., module), get its parent (workbook)
        if item.parent() is not None:
            item = item.parent()
        
        # Get workbook_id from UserRole, fall back to text for backwards compatibility
        workbook_id = item.data(0, Qt.ItemDataRole.UserRole)
        if workbook_id is None:
            workbook_id = item.text(0)
        
        return workbook_id

    def has_workbook(self, workbook_id: str) -> bool:
        """
        Check if a workbook exists in the project explorer.
        
        Args:
            workbook_id: The workbook ID to check.
            
        Returns:
            True if the workbook exists, False otherwise.
        """
        return workbook_id in self._workbook_items

    def _on_rename_module_action(self, workbook_id: str, old_name: str):
        """
        Handle rename module action from context menu.
        
        Shows an input dialog to get the new module name and emits the
        rename_module_requested signal.
        
        Args:
            workbook_id: The workbook ID containing the module
            old_name: The current module name (without .py extension)
        """
        from PySide6.QtWidgets import QInputDialog
        
        new_name, ok = QInputDialog.getText(
            self,
            "Rename Module",
            f"Enter new name for module '{old_name}':",
            text=old_name
        )
        
        if ok and new_name:
            # Strip .py extension if user added it
            new_name = _strip_py_extension(new_name.strip())
            
            if new_name and new_name != old_name:
                # Emit signal with workbook_id, old_name, and new_name
                self.rename_module_requested.emit(workbook_id, old_name, new_name)

    def keyPressEvent(self, event):
        """Handle keyboard events for the project explorer."""
        from PySide6.QtCore import Qt
        
        current_item = self.currentItem()
        if current_item is None:
            super().keyPressEvent(event)
            return
        
        parent_item = current_item.parent()
        
        # Check if selected item is a module (has a parent workbook)
        if parent_item is not None:
            # This is a module
            workbook_id = parent_item.data(0, Qt.ItemDataRole.UserRole)
            if workbook_id is None:
                workbook_id = strip_icon_prefix(parent_item.text(0))
            module_name = strip_icon_prefix(current_item.text(0))
            
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                # Enter - open the module
                self.open_module_requested.emit(workbook_id, module_name)
                return
            elif event.key() == Qt.Key.Key_F2:
                # F2 - trigger rename
                self._on_rename_module_action(workbook_id, module_name)
                return
            elif event.key() == Qt.Key.Key_Delete:
                # Delete - trigger delete
                self.delete_module_requested.emit(workbook_id, module_name)
                return
        else:
            # This is a workbook (top-level item)
            workbook_id = current_item.data(0, Qt.ItemDataRole.UserRole)
            if workbook_id is None:
                workbook_id = strip_icon_prefix(current_item.text(0))
            
            if event.key() == Qt.Key.Key_N and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                # Ctrl+N - new module
                self.new_module_requested.emit(workbook_id)
                return
        
        # Pass to parent for default handling
        super().keyPressEvent(event)

    def get_workbook_item(self, workbook_id: str) -> Optional[QTreeWidgetItem]:
        """
        Get the tree widget item for a workbook.
        
        Args:
            workbook_id: The workbook ID.
            
        Returns:
            The QTreeWidgetItem for the workbook, or None if not found.
        """
        return self._workbook_items.get(workbook_id)
