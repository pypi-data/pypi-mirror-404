"""
ExpandableGroupBox - A QGroupBox-like widget with maximize/restore functionality.

Provides a group container with a title bar that includes a maximize button.
When maximized, the group signals its parent to hide sibling groups.
"""

from typing import Optional
from enum import Enum

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame, QSizePolicy,QScrollArea, QApplication
)
from PySide6.QtCore import Qt, Signal

class FrameState(Enum):
    MINIMIZE = -1
    NORMAL = 0
    MAXIMIZE = 1


class ExpandableGroupBox(QWidget):
    """
    A group box widget with maximize/restore functionality.
    
    Signals:
        maximize_requested: Emitted when user clicks maximize button
        restore_requested: Emitted when user clicks restore button
    """
    
    # Signals
    maximize_requested = Signal(object)  # Emits self
    restore_requested = Signal()    
    frame_state_changed = Signal(object,object)
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        
        self.frame_state_changed.connect(self.on_frame_state_changed)
        self.setObjectName("expandableGroupBox")
        self._title = title
        self._frame_state = FrameState.NORMAL
        
        self._content_widget = None
        self._original_max_height = None  # Store original maxHeight constraint
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        self._main_layout = QVBoxLayout(self)
        self._main_layout.setContentsMargins(0, 0, 0, 0)
        self._main_layout.setSpacing(0)
        
        # Title bar frame
        self._title_bar = QFrame()
        self._title_bar.setObjectName("expandableGroupTitleBar")
        title_layout = QHBoxLayout(self._title_bar)
        title_layout.setContentsMargins(2, 2, 2, 2)
        
        # Title label
        self._title_label = QLabel(self._title)
        self._title_label.setObjectName("expandableGroupTitle")
        title_layout.addWidget(self._title_label)
        
        title_layout.addStretch()
        
        
        # Minimize/Restore button
        self._toggle_button2 = QPushButton()
        self._toggle_button2.setObjectName("expandableGroupToggleButton")
        self._toggle_button2.setFixedSize(20, 20)
        self._toggle_button2.clicked.connect(self._on_toggle_clicked2)
        title_layout.addWidget(self._toggle_button2)

        
        # Maximize/Restore button
        self._toggle_button = QPushButton()
        self._toggle_button.setObjectName("expandableGroupToggleButton")
        self._toggle_button.setFixedSize(20, 20)
        self._toggle_button.clicked.connect(self._on_toggle_clicked)
        title_layout.addWidget(self._toggle_button)

        self._main_layout.addWidget(self._title_bar)
        
        # Content frame (where the actual content goes)
        self._content_frame = QFrame()
        self._content_frame.setObjectName("expandableGroupContent")
        self._content_layout = QVBoxLayout(self._content_frame)
        self._content_layout.setContentsMargins(2, 2, 2, 2)
        self._main_layout.addWidget(self._content_frame,1)

        self._update_button_icon()
        self._update_content_visibility()

        self._with_mimized__property=[self._title_bar, self._title_label, self._toggle_button, self._toggle_button2]
        
    
    def setFrameState(self, state: FrameState):
        """Set the current frame state."""
        previous_state=self._frame_state
        self._frame_state = state
        for w in self._with_mimized__property:
            w.setProperty("isMinimized", state==FrameState.MINIMIZE)
            w.style().unpolish(w)
            w.style().polish(w)
            w.update()

        self.frame_state_changed.emit(previous_state,self._frame_state)

    def _update_button_icon(self):
        """Update button text based on frame state."""
        if self._frame_state == FrameState.MAXIMIZE:
            self._toggle_button2.setText("🗕")  # Minimize icon (square)
            self._toggle_button2.setToolTip("Minimize this section")

            self._toggle_button.setText("🗗")  # Restore icon (overlapping squares)
            self._toggle_button.setToolTip("Restore to normal view")


        elif self._frame_state == FrameState.MINIMIZE:
            self._toggle_button2.setText("🗗")  # Restore icon (overlapping squares)
            self._toggle_button2.setToolTip("Restore to normal view")

            self._toggle_button.setText("🗖")  # Maximize icon (square)
            self._toggle_button.setToolTip("Maximize this section")

        else:
            self._toggle_button2.setText("🗕")  # Minimize icon (square)
            self._toggle_button2.setToolTip("Minimize this section")

            self._toggle_button.setText("🗖")  # Maximize icon (square)
            self._toggle_button.setToolTip("Maximize this section")

    
    def _on_toggle_clicked(self):
        """Handle toggle button click."""
        if self._frame_state == FrameState.MAXIMIZE:
            self.setFrameState(FrameState.NORMAL)
        else:
            self.setFrameState(FrameState.MAXIMIZE)

    def _on_toggle_clicked2(self):
        """Handle toggle button click."""
        if self._frame_state == FrameState.MINIMIZE:
            self.setFrameState(FrameState.NORMAL)
        else:
            self.setFrameState(FrameState.MINIMIZE)

    
    def _update_content_visibility(self):
        if self._frame_state == FrameState.MINIMIZE:
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Fixed
                )
            self._content_frame.setVisible(False)
        else:
            self.setSizePolicy(
                QSizePolicy.Policy.Preferred,
                QSizePolicy.Policy.Expanding
                )
            self._content_frame.setVisible(True)
        self.updateGeometry()
        
    
    def setLayout(self, layout):
        """Set the content layout (mimics QGroupBox behavior)."""
        # Clear existing content layout
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            if item.widget():
                item.widget().setParent(None)
            if item.layout():
                item.layout().setParent(None)
                
        
        self._content_layout.addLayout(layout)
    
    def layout(self):
        """Return the content layout."""
        return self._content_layout

    def on_frame_state_changed(self,previous_state,current_state):
        self._update_content_visibility()
        self._update_button_icon()
        if current_state == FrameState.MAXIMIZE:
           self.maximize_requested.emit(self)
        elif previous_state == FrameState.MAXIMIZE:
            self.restore_requested.emit()
            
    
    def isMaximized(self) -> bool:
        """Return whether the group is maximized."""
        return self._frame_state == FrameState.MAXIMIZE
    
    def title(self) -> str:
        """Return the group title."""
        return self._title
    
    def setTitle(self, title: str):
        """Set the group title."""
        self._title = title
        self._title_label.setText(title)


class ExpandableGroupContainer(QScrollArea):
    """
    Container that manages multiple ExpandableGroupBox widgets.
    
    Handles maximize/restore behavior: when one group is maximized,
    others are hidden.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Scroll area behavior
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setObjectName("expandableGroupContainer")
        
        self._groups: list[ExpandableGroupBox] = []
        self._maximized_group: Optional[ExpandableGroupBox] = None
        
        # The scroll area needs a single "widget" as its content
        self._content = QWidget()
        self.setWidget(self._content)
        
        self._layout = QVBoxLayout(self._content)
        self._layout.setContentsMargins(0, 0, 0, 0)
    
        self._layout.addStretch()
        #self.emptyFrame=QFrame()
        #self._layout.addWidget(self.emptyFrame,1)

    def addGroup(self, group: ExpandableGroupBox):
        """Add a group to the container."""
        self._groups.append(group)
        self._layout.insertWidget(self._layout.count()-1,group)
        
        # Connect signals
        group.maximize_requested.connect(self._on_maximize_requested)
        group.restore_requested.connect(self._on_restore_requested)
    
    def addStretch(self):
        """Add stretch to the layout."""
        self._layout.addStretch()

    def _on_maximize_requested(self, group: ExpandableGroupBox):
        """Handle maximize request from a group."""
        self._maximized_group = group
        for i,g in enumerate(self._groups):
            if g is group:
                g.show()
                self._layout.setStretch(i,1)
            else:
                g.hide()
        
    def _on_restore_requested(self):
        """Handle restore request."""
        self._maximized_group = None
        
        for i,g in enumerate(self._groups):
            g.show()
            self._layout.setStretch(i,0)
 
    def insertLayout(self, index: int, layout):
        """Insert a layout at a specific position (for non-group items like workbook selector)."""
        self._layout.insertLayout(index, layout)
