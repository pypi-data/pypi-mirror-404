"""
XPyCode IDE - Object Inspector

This module provides the Object Inspector widget for viewing objects
stored in the kernel's ObjectKeeper.
"""

import logging
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
    QFrame,
)
from PySide6.QtCore import Signal, Qt
from typing import Dict, List

# Configure logging
from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)



class ObjectInspector(QFrame):
    """
    Object Inspector widget for viewing objects in the kernel's ObjectKeeper.
    
    Provides functionality to:
    - Select a target workbook from a dropdown
    - View stored objects with their keys, types, and repr values
    - Refresh the object registry on demand
    """

    # Signal to request the full object registry from the kernel
    refresh_requested = Signal(str)  # workbook_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("tabMainWidget")
        # Track workbook names: {workbook_id: display_name}
        self._workbook_names: Dict[str, str] = {}
        # Track objects per workbook: {workbook_id: [{key, type, repr}, ...]}
        self._objects: Dict[str, List[dict]] = {}
        self._setup_ui()

    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QVBoxLayout(self)
        
        # Workbook selection section
        workbook_layout = QHBoxLayout()
        workbook_label = QLabel("Target Workbook:")
        self.workbook_dropdown = QComboBox()
        self.workbook_dropdown.setMinimumWidth(200)
        self.workbook_dropdown.currentIndexChanged.connect(self._on_workbook_changed)
        workbook_layout.addWidget(workbook_label)
        workbook_layout.addWidget(self.workbook_dropdown)
        workbook_layout.addStretch()
        layout.addLayout(workbook_layout)
        
        # Object table section
        objects_label = QLabel("Stored Objects:")
        layout.addWidget(objects_label)
        
        self.object_table = QTableWidget()
        self.object_table.setColumnCount(3)
        self.object_table.setHorizontalHeaderLabels(["Key", "Type", "Value (Repr)"])
        self.object_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Interactive
        )
        self.object_table.horizontalHeader().setSectionResizeMode(
            1, QHeaderView.ResizeMode.Interactive
        )
        self.object_table.horizontalHeader().setSectionResizeMode(
            2, QHeaderView.ResizeMode.Stretch
        )
        self.object_table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.object_table.setSelectionMode(
            QTableWidget.SelectionMode.SingleSelection
        )
        self.object_table.setEditTriggers(
            QTableWidget.EditTrigger.NoEditTriggers
        )
        layout.addWidget(self.object_table)
        
        # Refresh button
        button_layout = QHBoxLayout()
        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        button_layout.addWidget(self.refresh_button)
        button_layout.addStretch()
        layout.addLayout(button_layout)

    def add_workbook(self, workbook_id: str, display_name: str):
        """
        Add a workbook to the dropdown.
        
        Args:
            workbook_id: Unique identifier for the workbook
            display_name: Human-readable name for display
        """
        if workbook_id in self._workbook_names:
            logger.debug(f"Workbook {workbook_id} already exists, skipping add")
            return
        
        self._workbook_names[workbook_id] = display_name
        self._objects[workbook_id] = []
        
        # Add to dropdown with icon
        self.workbook_dropdown.addItem(f"📗 {display_name}", workbook_id)
        logger.debug(f"Added workbook to Object Inspector: {display_name}")

    def remove_workbook(self, workbook_id: str):
        """
        Remove a workbook from the dropdown.
        
        Args:
            workbook_id: Unique identifier for the workbook
        """
        if workbook_id not in self._workbook_names:
            logger.debug(f"Workbook {workbook_id} not found, skipping remove")
            return
        
        # Check if this is the currently selected workbook
        current_workbook_id = self._get_current_workbook_id()
        was_selected = (current_workbook_id == workbook_id)
        
        # Remove from dropdown
        for i in range(self.workbook_dropdown.count()):
            if self.workbook_dropdown.itemData(i) == workbook_id:
                self.workbook_dropdown.removeItem(i)
                break
        
        # Clean up data
        del self._workbook_names[workbook_id]
        self._objects.pop(workbook_id, None)
        
        # If it was the only workbook or the selected one was removed, clear the table
        if self.workbook_dropdown.count() == 0:
            self.object_table.setRowCount(0)
        elif was_selected and self.workbook_dropdown.count() > 0:
            # Selection will automatically change to another workbook, triggering refresh
            pass
        
        logger.debug(f"Removed workbook from Object Inspector: {workbook_id}")

    def update_workbook_name(self, workbook_id: str, new_name: str):
        """
        Update the display name of a workbook in the dropdown.
        
        Args:
            workbook_id: The workbook identifier
            new_name: The new display name for the workbook
        """
        for i in range(self.workbook_dropdown.count()):
            if self.workbook_dropdown.itemData(i) == workbook_id:
                self.workbook_dropdown.setItemText(i, f"📗 {new_name}")
                break
        # Also update the cached name
        if workbook_id in self._workbook_names:
            self._workbook_names[workbook_id] = new_name

    def _get_current_workbook_id(self) -> str:
        """Get the currently selected workbook ID."""
        index = self.workbook_dropdown.currentIndex()
        if index >= 0:
            return self.workbook_dropdown.itemData(index)
        return None

    def _on_workbook_changed(self, index: int):
        """Handle workbook selection change."""
        if index < 0:
            self._refresh_table([])
            return
        
        workbook_id = self.workbook_dropdown.itemData(index)
        if workbook_id:
            # Display cached objects for the selected workbook
            objects = self._objects.get(workbook_id, [])
            self._refresh_table(objects)
            logger.debug(f"Switched to workbook: {workbook_id}")

    def _on_refresh_clicked(self):
        """Handle refresh button click."""
        workbook_id = self._get_current_workbook_id()
        if workbook_id:
            logger.debug(f"Requesting object registry refresh for: {workbook_id}")
            self.refresh_requested.emit(workbook_id)
        else:
            logger.debug("No workbook selected, cannot refresh")

    def handle_registry_update(self, workbook_id: str, action: str, data: dict):
        """
        Handle object_registry_update message.
        
        Args:
            workbook_id: Workbook that sent the update
            action: "update", "delete", or "clear_all"
            data: Update data (contains key, type, repr for "update"; key for "delete")
        """
        if workbook_id not in self._objects:
            logger.debug(f"Received update for unknown workbook: {workbook_id}")
            return
        
        objects = self._objects[workbook_id]
        
        if action == "update":
            # Update or add object
            key = data.get("key")
            obj_type = data.get("object_type")
            obj_repr = data.get("repr")
            
            # Find existing object with same key
            found = False
            for i, obj in enumerate(objects):
                if obj["key"] == key:
                    objects[i] = {"key": key, "type": obj_type, "repr": obj_repr}
                    found = True
                    break
            
            if not found:
                objects.append({"key": key, "type": obj_type, "repr": obj_repr})
            
            logger.debug(f"Updated object: {key} in workbook {workbook_id}")
        
        elif action == "delete":
            # Remove object
            key = data.get("key")
            objects[:] = [obj for obj in objects if obj["key"] != key]
            logger.debug(f"Deleted object: {key} from workbook {workbook_id}")
        
        elif action == "clear_all":
            # Clear all objects
            objects.clear()
            logger.debug(f"Cleared all objects in workbook {workbook_id}")
        
        # Refresh table if this is the currently selected workbook
        current_workbook = self._get_current_workbook_id()
        if current_workbook == workbook_id:
            self._refresh_table(objects)

    def handle_registry_response(self, workbook_id: str, objects: List[dict]):
        """
        Handle full object_registry_response message.
        
        Args:
            workbook_id: Workbook that sent the response
            objects: List of objects [{key, type, repr}, ...]
        """
        if workbook_id not in self._objects:
            logger.debug(f"Received response for unknown workbook: {workbook_id}")
            return
        
        # Update cached objects
        self._objects[workbook_id] = objects
        logger.debug(f"Received {len(objects)} objects for workbook {workbook_id}")
        
        # Refresh table if this is the currently selected workbook
        current_workbook = self._get_current_workbook_id()
        if current_workbook == workbook_id:
            self._refresh_table(objects)

    def _refresh_table(self, objects: List[dict]):
        """
        Refresh the object table with the given objects.
        
        Args:
            objects: List of objects [{key, type, repr}, ...]
        """
        # Clear and repopulate table
        self.object_table.setRowCount(0)
        
        for obj in objects:
            row = self.object_table.rowCount()
            self.object_table.insertRow(row)
            
            # Key column
            key_item = QTableWidgetItem(obj.get("key", ""))
            key_item.setFlags(key_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.object_table.setItem(row, 0, key_item)
            
            # Type column
            type_item = QTableWidgetItem(obj.get("type", ""))
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.object_table.setItem(row, 1, type_item)
            
            # Repr column
            repr_item = QTableWidgetItem(obj.get("repr", ""))
            repr_item.setFlags(repr_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.object_table.setItem(row, 2, repr_item)
        
        logger.debug(f"Refreshed object table with {len(objects)} objects")
