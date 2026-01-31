"""
XPyCode IDE - Welcome Widget

Displays a welcome screen when no editor tabs are open.
Shows the XPyCode logo, quick actions, and keyboard shortcuts.
"""

import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QGridLayout, QSizePolicy, QScrollArea
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QFont
from .monaco_editor import MonacoEditor


class WelcomeWidget(QScrollArea):
    """
    Welcome screen widget shown when no editor tabs are open.
    
    Displays:
    - XPyCode logo
    - Getting started section with quick actions
    - Keyboard shortcuts reference
    """
    
    # Signals for actions
    open_settings_requested = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the welcome widget UI."""
        self.setObjectName('welcomeMainFrame')
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        self.editors=[]

        self.centralWidget=QWidget()
        self.setWidget(self.centralWidget)
        layout = QVBoxLayout(self.centralWidget)
        #layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignHCenter)

        layout.setSpacing(10)
        
        # Add stretch to center content vertically
        layout.addStretch(1)
        
        # Logo section
        logo_label = QLabel()
        logo_path = os.path.join(
            os.path.dirname(__file__),
            "resources",
            "Logo_XPyCode.png"
        )
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            # Scale to reasonable size while maintaining aspect ratio
            scaled_pixmap = pixmap.scaledToWidth(300, Qt.TransformationMode.SmoothTransformation)
            logo_label.setPixmap(scaled_pixmap)
        else:
            logo_label.setText("XPyCode IDE")
            font = QFont()
            font.setPointSize(32)
            font.setBold(True)
            logo_label.setFont(font)
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        
        # Usage of Monaco Editor for welcome message
        # Mandatory to have Monaco Editor loaded at startup to avoid delays later
        welcome_editor=MonacoEditor()
        welcome_message="""import xpycode

def main():
    print("Welcome to XPyCode IDE!")"""
        welcome_editor.set_text(welcome_message)

        welcome_editor.set_readonly(True)
        welcome_editor.set_minimap_visible(False)
        
        monaco_widget=QWidget()
        monaco_widget.setObjectName("welcomeMainFrame")
        monaco_widget.setMinimumWidth(400)
        monaco_widget.setMinimumHeight(100)
        monaco_layout=QVBoxLayout(monaco_widget)
        monaco_layout.addWidget(welcome_editor)
        self.editors.append(welcome_editor)

        #layout.addWidget(empty_editor)
        #layout.addLayout(monaco_layout)
        layout.addWidget(monaco_widget)
        
        # Tagline
        #Commented out tagline for cleaner look using Monaco editor
        '''
        tagline = QLabel("Excel + Python Integration")
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        tagline_font = QFont()
        tagline_font.setPointSize(14)
        tagline.setFont(tagline_font)
        tagline.setStyleSheet("color: #888888;")
        layout.addWidget(tagline)
        '''
        
        layout.addSpacing(5)
        
        # Getting Started section
        getting_started_frame = self._create_getting_started_section()
        layout.addWidget(getting_started_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
        layout.addSpacing(10)
        
        # Keyboard Shortcuts section
        shortcuts_frame = self._create_shortcuts_section()
        layout.addWidget(shortcuts_frame, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Add stretch to center content vertically
        layout.addStretch(1)
    
    def _create_getting_started_section(self) -> QFrame:
        """Create the Getting Started section."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setObjectName("gettingStartedFrame")
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(15)
        
        # Section title
        title = QLabel("Getting Started")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Steps
        steps = [
            ("1.", "Connect an Excel workbook", "Open Excel with the XPyCode add-in loaded"),
            ("2.", "Create a module", "Right-click in Project Explorer → New Module"),
            ("3.", "Write Python code", "Double-click a module to open it in the editor"),
            ("4.", "Run your code", "Press Ctrl+R or F5 to execute"),
        ]
        
        steps_layout = QGridLayout()
        steps_layout.setSpacing(10)
        
        for row, (num, action, description) in enumerate(steps):
            num_label = QLabel(num)
            num_label.setStyleSheet("color: #4FC3F7; font-weight: bold; font-size: 14px;")
            
            action_label = QLabel(action)
            action_label.setStyleSheet("font-weight: bold; font-size: 13px;")
            
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #888888; font-size: 12px;")
            
            steps_layout.addWidget(num_label, row, 0, Qt.AlignmentFlag.AlignTop)
            steps_layout.addWidget(action_label, row, 1, Qt.AlignmentFlag.AlignTop)
            steps_layout.addWidget(desc_label, row, 2, Qt.AlignmentFlag.AlignTop)
        
        layout.addLayout(steps_layout)
        
        # Settings button
        settings_btn = QPushButton("⚙️  Open Settings")
        settings_btn.setObjectName("orangeButton")
        
        settings_btn.clicked.connect(self.open_settings_requested.emit)
        layout.addWidget(settings_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        
        return frame
    
    def _create_shortcuts_section(self) -> QFrame:
        """Create the Keyboard Shortcuts section."""
        frame = QFrame()
        frame.setFrameShape(QFrame.Shape.StyledPanel)
        frame.setObjectName("gettingStartedFrame")
        
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)
        
        # Section title
        title = QLabel("⌨️ Keyboard Shortcuts")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title.setFont(title_font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Shortcuts in a grid
        shortcuts = [
            ("Ctrl+R / F5", "Run Code"),
            ("Shift+F5", "Debug Code"),
            ("F9", "Toggle Breakpoint"),
            ("F10", "Step Over"),
            ("F11", "Step Into"),
            ("Shift+F11", "Step Out"),
            ("Alt+F4", "Exit"),
        ]
        
        shortcuts_layout = QHBoxLayout()
        shortcuts_layout.setSpacing(10)
        
        # Split into two columns
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()
        
        for i, (key, action) in enumerate(shortcuts):
            shortcut_widget = self._create_shortcut_item(key, action)
            if i < 4:
                left_col.addWidget(shortcut_widget)
            else:
                right_col.addWidget(shortcut_widget)
        
        # Add stretch to right column if needed
        while right_col.count() < left_col.count():
            right_col.addStretch()
        
        shortcuts_layout.addLayout(left_col)
        shortcuts_layout.addLayout(right_col)
        
        layout.addLayout(shortcuts_layout)
        
        return frame
    
    def _create_shortcut_item(self, key: str, action: str) -> QWidget:
        """Create a single shortcut item widget."""
        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)
        
        key_label = QLabel(key)
        key_label.setObjectName("shortcutKeyLabel")
        key_label.setFixedWidth(100)
        
        action_label = QLabel(action)
        action_label.setStyleSheet("color: #aaaaaa; font-size: 12px;")
        
        layout.addWidget(key_label)
        layout.addWidget(action_label)
        layout.addStretch()
        
        return widget
