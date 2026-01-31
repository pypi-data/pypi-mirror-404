"""
Debug Panel - Debug dock widget with tabs for variables, call stack, watch, and console.

This module provides the debug panel UI for the XPyCode IDE.
"""

import logging
from typing import Dict, List, Any, Set
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QTabWidget,
    QTreeWidget,
    QTreeWidgetItem,
    QTextEdit,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QSplitter,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)



class DebugPanel(QWidget):
    """
    Debug panel widget with tabs for:
    - Variables (locals/globals)
    - Call Stack
    - Watch expressions
    - Debug Console (REPL)
    """
    
    # Signal emitted when user wants to evaluate an expression
    # Parameters: (expression: str, source: str) where source is "watch" or "console"
    evaluate_expression = Signal(str, str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.watch_expressions: List[str] = []
        # Track pending console evaluations to distinguish from watch evaluations
        self._pending_console_expressions: Set[str] = set()
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the debug panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create tab widget
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Variables tab
        self.variables_tree = QTreeWidget()
        self.variables_tree.setHeaderLabels(["Name", "Type", "Value"])
        self.variables_tree.setColumnWidth(0, 150)
        self.variables_tree.setColumnWidth(1, 100)
        self.tabs.addTab(self.variables_tree, "Variables")
        
        # Call Stack tab
        self.call_stack_tree = QTreeWidget()
        self.call_stack_tree.setHeaderLabels(["Function", "Module", "Line"])
        self.call_stack_tree.setColumnWidth(0, 200)
        self.call_stack_tree.setColumnWidth(1, 150)
        self.tabs.addTab(self.call_stack_tree, "Call Stack")
        
        # Watch tab
        watch_widget = QWidget()
        watch_layout = QVBoxLayout(watch_widget)
        
        # Watch input
        watch_input_layout = QHBoxLayout()
        self.watch_input = QLineEdit()
        self.watch_input.setPlaceholderText("Enter expression to watch...")
        self.watch_input.returnPressed.connect(self._add_watch_expression)
        watch_input_layout.addWidget(self.watch_input)
        
        add_watch_btn = QPushButton("Add")
        add_watch_btn.clicked.connect(self._add_watch_expression)
        watch_input_layout.addWidget(add_watch_btn)
        
        watch_layout.addLayout(watch_input_layout)
        
        # Watch expressions tree
        self.watch_tree = QTreeWidget()
        self.watch_tree.setHeaderLabels(["Expression", "Type", "Value"])
        self.watch_tree.setColumnWidth(0, 150)
        self.watch_tree.setColumnWidth(1, 80)
        self.watch_tree.setColumnWidth(2, 200)
        watch_layout.addWidget(self.watch_tree)
        
        self.tabs.addTab(watch_widget, "Watch")
        
        # Debug Console tab
        console_widget = QWidget()
        console_layout = QVBoxLayout(console_widget)
        
        # Console output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)
        self.console_output.setFont(QFont("Courier New", 10))
        console_layout.addWidget(self.console_output)
        
        # Console input
        console_input_layout = QHBoxLayout()
        self.console_input = QLineEdit()
        self.console_input.setPlaceholderText("Evaluate expression...")
        self.console_input.returnPressed.connect(self._evaluate_console_expression)
        console_input_layout.addWidget(self.console_input)
        
        eval_btn = QPushButton("Evaluate")
        eval_btn.clicked.connect(self._evaluate_console_expression)
        console_input_layout.addWidget(eval_btn)
        
        console_layout.addLayout(console_input_layout)
        
        self.tabs.addTab(console_widget, "Debug Console")
    
    def _add_watch_item(self, expression: str):
        """Add a single watch item to the tree without clearing existing items."""
        item = QTreeWidgetItem(self.watch_tree)
        item.setText(0, expression)
        item.setText(1, "")  # Type (will be filled when result arrives)
        item.setText(2, "Evaluating...")
    
    def _add_watch_expression(self):
        """Add a watch expression."""
        expression = self.watch_input.text().strip()
        if expression and expression not in self.watch_expressions:
            self.watch_expressions.append(expression)
            self.watch_input.clear()
            # Add only the new item to the tree (don't rebuild entire tree)
            self._add_watch_item(expression)
            # Request evaluation with source="watch"
            self.evaluate_expression.emit(expression, "watch")
    
    def _evaluate_console_expression(self):
        """Evaluate an expression in the debug console."""
        expression = self.console_input.text().strip()
        if expression:
            # Display the expression in the console
            self.console_output.append(f">>> {expression}")
            self.console_input.clear()
            # Track this as a console expression
            self._pending_console_expressions.add(expression)
            # Request evaluation with source="console"
            self.evaluate_expression.emit(expression, "console")
    
    def _update_watch_tree(self):
        """Update the watch expressions tree."""
        self.watch_tree.clear()
        for expr in self.watch_expressions:
            item = QTreeWidgetItem(self.watch_tree)
            item.setText(0, expr)
            item.setText(1, "")  # Type (will be filled when result arrives)
            item.setText(2, "Evaluating...")
    
    def update_variables(self, locals_list: List[Dict], globals_list: List[Dict]):
        """
        Update the variables tree with locals and globals.
        
        Args:
            locals_list: List of local variable dicts
            globals_list: List of global variable dicts
        """
        self.variables_tree.clear()
        
        # Add locals section
        if locals_list:
            locals_root = QTreeWidgetItem(self.variables_tree)
            locals_root.setText(0, "Locals")
            locals_root.setExpanded(True)
            
            for var in locals_list:
                item = QTreeWidgetItem(locals_root)
                item.setText(0, var.get("name", ""))
                item.setText(1, var.get("type", ""))
                item.setText(2, var.get("value", ""))
        
        # Add globals section
        if globals_list:
            globals_root = QTreeWidgetItem(self.variables_tree)
            globals_root.setText(0, "Globals")
            globals_root.setExpanded(False)
            
            for var in globals_list:
                item = QTreeWidgetItem(globals_root)
                item.setText(0, var.get("name", ""))
                item.setText(1, var.get("type", ""))
                item.setText(2, var.get("value", ""))
    
    def update_call_stack(self, call_stack: List[Dict]):
        """
        Update the call stack tree.
        
        Args:
            call_stack: List of stack frame dicts
        """
        self.call_stack_tree.clear()
        
        for frame in call_stack:
            item = QTreeWidgetItem(self.call_stack_tree)
            item.setText(0, frame.get("function", ""))
            item.setText(1, frame.get("module", ""))
            item.setText(2, str(frame.get("line", "")))
    
    def update_watch_result(self, expression: str, result: Dict):
        """
        Update a watch expression result.
        
        Args:
            expression: The expression that was evaluated
            result: Result dict with 'result'/'success' or 'error' key
        """
        logger.debug(f"[DebugPanel] update_watch_result: expression='{expression}', result={result}")
        
        # Find the watch item
        found = False
        for i in range(self.watch_tree.topLevelItemCount()):
            item = self.watch_tree.topLevelItem(i)
            if item.text(0) == expression:
                found = True
                if "error" in result:
                    item.setText(1, "error")
                    item.setText(2, f"Error: {result['error']}")
                elif result.get("success") or "result" in result:
                    result_type = result.get("result_type", "")
                    value = result.get("result", result.get("repr", ""))
                    item.setText(1, result_type)
                    item.setText(2, str(value))
                else:
                    # Unexpected result format - log for debugging
                    logger.warning(f"[DebugPanel] Unexpected watch result format for '{expression}': {result}")
                    item.setText(1, "")
                    item.setText(2, "Evaluating...")
                break
        
        if not found:
            logger.warning(f"[DebugPanel] Watch expression not found: '{expression}'")
    
    def update_console_result(self, expression: str, result: Dict):
        """
        Update the debug console with an evaluation result.
        
        Args:
            expression: The expression that was evaluated
            result: Result dict with 'result' or 'error' key
        """
        if "error" in result:
            self.console_output.append(f"Error: {result['error']}")
        else:
            value = result.get("result", "")
            self.console_output.append(f"{value}")
    
    def set_all_watches_evaluating(self):
        """Set all watch expressions to 'Evaluating...' state (for re-evaluation on step)."""
        for i in range(self.watch_tree.topLevelItemCount()):
            item = self.watch_tree.topLevelItem(i)
            item.setText(1, "")
            item.setText(2, "Evaluating...")
    
    def is_console_expression(self, expression: str) -> bool:
        """Check if an expression was submitted from the console."""
        return expression in self._pending_console_expressions
    
    def clear_console_expression(self, expression: str):
        """Remove an expression from pending console expressions."""
        self._pending_console_expressions.discard(expression)
    
    def clear(self):
        """Clear all debug information."""
        self.variables_tree.clear()
        self.call_stack_tree.clear()
        self.watch_tree.clear()
        self.console_output.clear()
        self.watch_expressions.clear()
        self._pending_console_expressions.clear()
    
    def add_console_message(self, message: str):
        """
        Add a message to the debug console output.
        
        Args:
            message: The message to display in the console
        """
        # Append to the console text area
        self.console_output.append(message)
        # Auto-scroll to bottom
        scrollbar = self.console_output.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
