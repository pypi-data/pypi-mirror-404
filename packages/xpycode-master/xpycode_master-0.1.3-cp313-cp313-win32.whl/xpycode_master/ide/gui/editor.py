"""
XPyCode IDE - Editor

This module provides the code editor widget for the XPyCode IDE.
"""

from typing import Optional
from PySide6.QtWidgets import QPlainTextEdit, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QTextCharFormat, QColor


class Editor(QPlainTextEdit):
    """
    Code editor widget for editing Python code and modules.
    
    Inherits from QPlainTextEdit to provide basic text editing capabilities
    with code-friendly defaults.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._workbook_id: Optional[str] = None
        self._setup_ui()

    @property
    def workbook_id(self) -> Optional[str]:
        """Get the workbook ID associated with this editor."""
        return self._workbook_id

    @workbook_id.setter
    def workbook_id(self, value: Optional[str]):
        """Set the workbook ID associated with this editor."""
        self._workbook_id = value

    def _setup_ui(self):
        """Setup the editor UI."""
        # Set monospace font
        font = QFont("Consolas", 11)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self.setFont(font)
        
        # Set tab width
        self.setTabStopDistance(40)  # Approximately 4 spaces
        
        # Enable line wrapping
        self.setLineWrapMode(QPlainTextEdit.LineWrapMode.NoWrap)
        
        # Set placeholder text
        self.setPlaceholderText("Enter your Python code here...")
        
        # Style the editor
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                selection-background-color: #264f78;
                selection-color: #ffffff;
            }
        """)

    def get_current_line_number(self) -> int:
        """Get the current line number (1-indexed)."""
        cursor = self.textCursor()
        return cursor.blockNumber() + 1

    def get_current_column(self) -> int:
        """Get the current column number (1-indexed)."""
        cursor = self.textCursor()
        return cursor.columnNumber() + 1

    def go_to_line(self, line_number: int):
        """
        Navigate to the specified line number.
        
        Args:
            line_number: The line number to navigate to (1-indexed)
        """
        block = self.document().findBlockByLineNumber(line_number - 1)
        if block.isValid():
            cursor = self.textCursor()
            cursor.setPosition(block.position())
            self.setTextCursor(cursor)
            self.centerCursor()

    def get_text(self) -> str:
        """Get the entire text content of the editor."""
        return self.toPlainText()

    def set_text(self, text: str):
        """
        Set the text content of the editor.
        
        Args:
            text: The text to set
        """
        self.setPlainText(text)

    def insert_text_at_cursor(self, text: str):
        """
        Insert text at the current cursor position.
        
        Args:
            text: The text to insert
        """
        self.insertPlainText(text)
