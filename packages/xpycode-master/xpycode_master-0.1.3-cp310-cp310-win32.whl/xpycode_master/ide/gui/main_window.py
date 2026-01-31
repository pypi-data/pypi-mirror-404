"""
XPyCode IDE - Main Window

This module provides the main window for the XPyCode IDE, implementing
a layout with dock widgets for Project Explorer, Editors, Object Inspector,
and Console.
"""

import ast
import hashlib
import html
import json
import logging
import os
import re
from typing import Dict, Optional, List
from PySide6.QtWidgets import (
    QMainWindow,
    QDockWidget,
    QTabWidget,
    QTextEdit,
    QWidget,
    QVBoxLayout,
    QLabel,
    QToolBar,
    QMessageBox,
    QInputDialog,
    QSizePolicy,
    QToolButton,
    QMenu,
    QApplication,
    QStackedWidget,
    QFrame,
)
from PySide6.QtCore import Qt, QUrl, QTimer
from PySide6.QtGui import QAction, QKeySequence, QTextCursor, QIcon, QActionGroup, QCloseEvent

from .widgets.edits import QTextEditWithClear
from ..config import SettingsManager
from .project_explorer import ProjectExplorer
from .monaco_editor import MonacoEditor
from .package_manager import PackageManager
from .event_manager import EventManager
from .function_publisher import FunctionPublisher
from .object_inspector import ObjectInspector
from .icon_utils import strip_icon_prefix
from .ai_login_widget import AILoginWidget
from .debug_panel import DebugPanel
from .breakpoint_manager import BreakpointManager
from .theme_loader import ThemeLoader
from .settings_dialog import SettingsDialog
from .settings_actions import bind_actions_to_instance, get_settings_action, OutputLevel
from .utils.decorators_pyside6_threadsafe import run_in_qt_thread
from .welcome_widget import WelcomeWidget
from .advanced_actions import AdvancedAction, register_action, get_tabs, get_actions, clear_actions


# Configure logging
from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)

# Default values for function publications
DEFAULT_DIMENSION = "Scalar"
DEFAULT_STREAMING = False


def _strip_py_extension(name: str) -> str:
    """Strip .py extension from module name if present."""
    if name.endswith('.py'):
        return name[:-3]
    return name


class MainWindow(QMainWindow):
    """Main window for the XPyCode IDE."""
    
    # Special workbook ID for the welcome tab
    WELCOME_TAB_ID = "__welcome__"
    
    # Hover mode constants
    HOVER_MODE_COMPACT = "compact"
    HOVER_MODE_DETAILED = "detailed"
    
    # Debug configuration
    DEBUG_LINE_HIGHLIGHT_DELAY_MS = 100  # Delay before highlighting debug line in newly opened tabs

    def __init__(self):
        super().__init__()
        self.setWindowTitle("XPyCode Editor")
        self.setMinimumSize(1200, 800)
        
        # Initialize settings manager first
        self.settings_manager = SettingsManager()
        
        # Initialize theme loader
        self._theme_loader = ThemeLoader()
        
        # Set window icon - set at application level now
        #icon_path = os.path.join(os.path.dirname(__file__), "resources", "icons", "XPY.png")
        #if os.path.exists(icon_path):
        #    self.setWindowIcon(QIcon(icon_path))
        
        # Module sync tracking: {workbook_id: {module_name: hash}}
        # Tracks the hash of module code last synced to the Kernel
        self._synced_module_hashes: Dict[str, Dict[str, str]] = {}
        
        # Module cache from Business Layer: {workbook_id: {module_name: code}}
        self._module_cache: Dict[str, Dict[str, str]] = {}

        # Workbook names cache: {workbook_id: workbook_name}
        self._workbook_names: Dict[str, str] = {}
        
        # Global minimap setting
        self._minimap_visible: bool = True
        
        # Theme setting
        self._current_theme: str = "vs-dark"
        
        # App-level theme setting
        self._current_app_theme: str = "xpy-dark"
        
        # Editor settings cache for new tabs
        self._editor_tab_size: int = 4
        self._editor_insert_spaces: bool = True
        self._editor_word_wrap: bool = False
        self.editor_font_size: int = 12

        # Settings cache for reading values
        self._settings_cache: dict = {}
        
        # Debug state
        self._debug_active: bool = False
        self._current_debug_workbook: Optional[str] = None
        self._current_debug_editor: Optional[MonacoEditor] = None
        self._show_debug_console_messages: bool = False  # Default is False
        self._pending_debug_line: Optional[Dict] = None  # {workbook_id, module_name, line}
        self._at_debug_exception: bool = False  # Track if paused at exception
        
        # Error alert state
        self._has_unnoticed_error: bool = False
        
        # Console source filter setting
        self._console_source_filter: str = "all"  # "all" or "ide_only"
        
        # Console output level setting
        self._console_output_level: OutputLevel = OutputLevel.SIMPLE
        
        # Cache package errors by workbook: {workbook_id: {package_name: [error_messages]}}
        self._workbook_package_errors: Dict[str, Dict[str, list]] = {}
        
        # WebSocket client reference (set later via set_websocket_client)
        self.websocket_client: Optional['WebSocketClient'] = None
        self.websocket: Optional['WebSocketClient'] = None  # Alias for backwards compatibility
        
        self.welcome_widget: Optional[WelcomeWidget] = None
        self._setup_central_widget()
        self._setup_dock_widgets()
        self._setup_toolbar()
        self._setup_menu_bar()
        self._setup_status_bar()
        # Note: WebSocket setup is now done in main.py via set_websocket_client()
        
        # Bind settings actions to this instance
        bind_actions_to_instance(self)
        
        # Apply default app theme
        self._set_app_theme(self._current_app_theme)

    def _setup_central_widget(self):
        """Setup the central widget with stacked layout for welcome/editor views."""
        # Create the stacked widget as central widget
        self.central_stack = QStackedWidget()
        self.central_stack.setObjectName("centralStack")
        
        # Index 0: Welcome Widget
        self.welcome_widget = WelcomeWidget()
        self.welcome_widget.open_settings_requested.connect(self._open_settings_dialog)
        self.central_stack.addWidget(self.welcome_widget)
        
        # Index 1: Editor Tabs
        self.editor_tabs = QTabWidget()
        self.editor_tabs.setTabsClosable(True)
        self.editor_tabs.setMovable(True)
        self.editor_tabs.tabCloseRequested.connect(self._close_editor_tab)
        self.editor_tabs.currentChanged.connect(self._on_tab_changed)
        self.central_stack.addWidget(self.editor_tabs)
        
        # Start with welcome widget (index 0)
        self.central_stack.setCurrentIndex(0)
        
        self.setCentralWidget(self.central_stack)


    def _on_tab_changed(self, index: int):
        """
        Handle tab change events.
        
        Switches central stack between welcome widget (when no tabs) and editor tabs.
        Also syncs Project Explorer selection.
        
        Args:
            index: The index of the newly selected tab, or -1 if no tabs.
        """
        # Switch stack based on whether we have tabs
        if index == -1:
            # No tabs - show welcome widget
            self.central_stack.setCurrentIndex(0)
            return
        else:
            # Has tabs - show editor tabs
            self.central_stack.setCurrentIndex(1)
        # Safety check: Project explorer might not be initialized yet during startup
        if not hasattr(self, 'project_explorer'):
            return
        
        tab_widget = self.editor_tabs.widget(index)
        if not isinstance(tab_widget, MonacoEditor):
            return
        
        workbook_id = tab_widget.workbook_id
        if not workbook_id:
            # Clear selection for tabs without workbook
            self.project_explorer.clearSelection()
            return
        
        module_name = self.editor_tabs.tabText(index)
        
        # Find and select the corresponding item in Project Explorer
        self._select_module_in_project_explorer(workbook_id, module_name)
    
    def _on_ai_provider_changed(self, provider: str, model: str):
        """
        Handle AI provider/model change events.
        
        Args:
            provider: The selected AI provider name
            model: The selected model name
        """
        logger.info(f"AI provider changed: {provider}, model: {model}")

    def _select_module_in_project_explorer(self, workbook_id: str, module_name: str):
        """
        Find and select a module in the Project Explorer tree.
        
        Args:
            workbook_id: The workbook ID containing the module.
            module_name: The module name to select.
        """
        # Get the workbook item using public method
        workbook_item = self.project_explorer.get_workbook_item(workbook_id)
        if not workbook_item:
            return
        
        # Find the module item under the workbook
        for i in range(workbook_item.childCount()):
            child = workbook_item.child(i)
            # Strip icon prefix from tree item text for comparison
            child_module_name = strip_icon_prefix(child.text(0))
            if child_module_name == module_name:
                # Select this item
                self.project_explorer.setCurrentItem(child)
                return

    def _setup_dock_widgets(self):
        """Setup the dock widgets for different panels."""
        # Left: Project Explorer
        self.project_explorer_dock = QDockWidget("🗄 Project Explorer", self)
        self.project_explorer_dock.setObjectName("ProjectExplorerDock")
        self.project_explorer_frame=QFrame()
        self.project_explorer_frame.setContentsMargins(0,0,0,0)
        self.project_explorer_frame.setObjectName("projectExplorerFrame")
        self.project_explorer_dock.setWidget(self.project_explorer_frame)
        self.project_explorer_layout=QVBoxLayout(self.project_explorer_frame)
        self.project_explorer_layout.setContentsMargins(0,0,0,0)
        self.project_explorer = ProjectExplorer()
        self.project_explorer_layout.addWidget(self.project_explorer)
        self.project_explorer_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea, self.project_explorer_dock)
        
        # Right: Object Inspector
        self.object_inspector_dock = QDockWidget("🧩 Objects", self)
        self.object_inspector_dock.setObjectName("ObjectInspectorDock")
        self.object_inspector = ObjectInspector()
        self.object_inspector_dock.setWidget(self.object_inspector)
        self.object_inspector_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.object_inspector_dock)
        
        # Right: Event Manager (stacked with Object Inspector)
        self.event_manager_dock = QDockWidget("⚡ Events", self)
        self.event_manager_dock.setObjectName("EventManagerDock")
        self.event_manager = EventManager()
        self.event_manager_dock.setWidget(self.event_manager)
        self.event_manager_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.event_manager_dock)
        self.tabifyDockWidget(self.object_inspector_dock, self.event_manager_dock)
        
        # Right: Function Publisher (stacked with Object Inspector and Event Manager)
        self.function_publisher_dock = QDockWidget("Ƒ Functions", self)
        self.function_publisher_dock.setObjectName("FunctionPublisherDock")
        self.function_publisher = FunctionPublisher()
        self.function_publisher_dock.setWidget(self.function_publisher)
        self.function_publisher_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.function_publisher_dock)
        self.tabifyDockWidget(self.event_manager_dock, self.function_publisher_dock)
        self.function_publisher._modules_cache=self._module_cache
        
        # Connect FunctionPublisher signals
        self.function_publisher.update_module_cache_requested.connect(self.update_event_manager_module_cache)
        self.function_publisher.sync_published_functions_requested.connect(self._on_sync_published_functions)
        
        # Right: Package Manager (stacked with others)
        self.package_manager_dock = QDockWidget("📦 Packages", self)
        self.package_manager_dock.setObjectName("PackageManagerDock")
        self.package_manager = PackageManager()
        self.package_manager_dock.setWidget(self.package_manager)
        self.package_manager_dock.setMinimumWidth(200)
        self.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.package_manager_dock)
        self.tabifyDockWidget(self.function_publisher_dock, self.package_manager_dock)
        
        # Connect PackageManager signals
        self.package_manager.install_requested.connect(self._on_package_install_requested)
        self.package_manager.get_versions_requested.connect(self._on_get_versions_requested)
        self.package_manager.get_extras_requested.connect(self._on_get_extras_requested)
        self.package_manager.search_package_requested.connect(self._on_search_package_requested)
        self.package_manager.add_package_requested.connect(self._on_add_package_requested)
        self.package_manager.update_package_requested.connect(self._on_update_package_requested)
        self.package_manager.remove_package_requested.connect(self._on_remove_package_requested)
        # Phase 2 signals
        self.package_manager.install_all_requested.connect(self._on_install_all_requested)
        self.package_manager.reorder_requested.connect(self._on_reorder_requested)
        # New signals
        self.package_manager.get_workbook_packages_requested.connect(self._on_get_workbook_packages_requested)
        self.package_manager.restore_requested.connect(self._on_restore_requested)
        self.package_manager.see_resolution_requested.connect(self._on_see_resolution_requested)
        self.package_manager.update_package_status_requested.connect(self._on_update_package_status_requested)
        self.package_manager.update_python_paths_requested.connect(self._on_update_python_paths_requested)
        
        # Connect ObjectInspector signals
        self.object_inspector.refresh_requested.connect(self._on_object_registry_refresh_requested)
        
        # Connect ProjectExplorer signals
        self.project_explorer.new_module_requested.connect(self._on_new_module_requested)
        self.project_explorer.open_module_requested.connect(self._on_open_module_requested)
        self.project_explorer.delete_module_requested.connect(self._on_delete_module_requested)
        self.project_explorer.rename_module_requested.connect(self._on_rename_module_requested)

        # Connect workbook signals to PackageManager for auto-sync
        self.project_explorer.workbook_added.connect(self.package_manager.add_workbook)
        self.project_explorer.workbook_removed.connect(self.package_manager.remove_workbook)

        # Connect workbook signals to EventManager for auto-sync
        self.project_explorer.workbook_added.connect(self.event_manager.add_workbook)
        self.project_explorer.workbook_removed.connect(self.event_manager.remove_workbook)

        # Connect workbook signals to FunctionPublisher for auto-sync
        self.project_explorer.workbook_added.connect(self.function_publisher.add_workbook)
        self.project_explorer.workbook_removed.connect(self.function_publisher.remove_workbook)

        # Connect workbook signals to ObjectInspector for auto-sync
        self.project_explorer.workbook_added.connect(self.object_inspector.add_workbook)
        self.project_explorer.workbook_removed.connect(self.object_inspector.remove_workbook)
        
        # Connect EventManager signals
        self.event_manager.refresh_state_requested.connect(self._on_refresh_state_requested)
        self.event_manager.assign_handler_requested.connect(self._on_assign_handler_requested)
        self.event_manager.create_handler_requested.connect(self._on_create_handler_requested)
        
        # Raise the Object Inspector to be the active tab
        self.object_inspector_dock.raise_()
        
        # Bottom: Console
        self.console_dock = QDockWidget("🖥 Console", self)
        self.console_dock.setObjectName("ConsoleDock")
        self.console = self._create_console()
        self.console_dock.setWidget(self.console)
        self.console_dock.setMinimumHeight(150)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.console_dock)
        
        # Bottom: Debug Panel (hidden by default, shown when debugging)
        self.debug_panel_dock = QDockWidget("🐛 Debug", self)
        self.debug_panel_dock.setObjectName("DebugPanelDock")
        self.debug_panel = DebugPanel()
        self.debug_panel_dock.setWidget(self.debug_panel)
        self.debug_panel_dock.setMinimumHeight(150)
        self.addDockWidget(Qt.DockWidgetArea.BottomDockWidgetArea, self.debug_panel_dock)
        self.tabifyDockWidget(self.console_dock, self.debug_panel_dock)
        # Hide debug panel by default
        self.debug_panel_dock.setVisible(False)
        
        # Connect debug panel signals
        self.debug_panel.evaluate_expression.connect(self._on_debug_evaluate_expression)
        
        # Initialize breakpoint manager
        self.breakpoint_manager = BreakpointManager()

    def _setup_toolbar(self):
        """Setup the toolbar with run and debug actions."""
        toolbar = QToolBar("Main Toolbar", self)
        toolbar.setObjectName("MainToolbar")
        self.addToolBar(toolbar)
        
        # Run action (Smart Run) - supports both Ctrl+R and F5
        self.run_action = QAction("▶️ Run", self)
        self.run_action.setToolTip("Run the code in the current editor (Ctrl+R or F5)")
        self.run_action.setShortcuts([QKeySequence("Ctrl+R"), QKeySequence("F5")])
        self.run_action.triggered.connect(self._run_code)
        toolbar.addAction(self.run_action)
        
        # Debug action (F5 when debugging enabled)
        self.debug_action = QAction("🐛 Debug", self)
        self.debug_action.setToolTip("Debug the code in the current editor (Shift+F5)")
        self.debug_action.setShortcut(QKeySequence("Shift+F5"))
        self.debug_action.triggered.connect(self._debug_code)
        toolbar.addAction(self.debug_action)
        
        # Debug control actions (hidden by default)
        toolbar.addSeparator()
        
        self.debug_stop_action = QAction("⏹ Stop", self)
        self.debug_stop_action.setToolTip("Stop debugging")
        self.debug_stop_action.triggered.connect(self._debug_stop)
        self.debug_stop_action.setVisible(False)
        toolbar.addAction(self.debug_stop_action)
        
        self.debug_continue_action = QAction("▶️ Continue", self)
        self.debug_continue_action.setToolTip("Continue execution (Shift+F5)")
        self.debug_continue_action.setShortcut(QKeySequence("Shift+F5"))
        self.debug_continue_action.triggered.connect(self._debug_continue)
        self.debug_continue_action.setVisible(False)
        toolbar.addAction(self.debug_continue_action)
        
        self.debug_step_over_action = QAction("⤵️ Step Over", self)
        self.debug_step_over_action.setToolTip("Step over (F10)")
        self.debug_step_over_action.setShortcut(QKeySequence("F10"))
        self.debug_step_over_action.triggered.connect(self._debug_step_over)
        self.debug_step_over_action.setVisible(False)
        toolbar.addAction(self.debug_step_over_action)
        
        self.debug_step_into_action = QAction("⬇️ Step Into", self)
        self.debug_step_into_action.setToolTip("Step into (F11)")
        self.debug_step_into_action.setShortcut(QKeySequence("F11"))
        self.debug_step_into_action.triggered.connect(self._debug_step_into)
        self.debug_step_into_action.setVisible(False)
        toolbar.addAction(self.debug_step_into_action)
        
        self.debug_step_out_action = QAction("⬆️ Step Out", self)
        self.debug_step_out_action.setToolTip("Step out (Shift+F11)")
        self.debug_step_out_action.setShortcut(QKeySequence("Shift+F11"))
        self.debug_step_out_action.triggered.connect(self._debug_step_out)
        self.debug_step_out_action.setVisible(False)
        toolbar.addAction(self.debug_step_out_action)
        
        # Add spacer widget to push AI login widget to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        toolbar.addWidget(spacer)
        
        # Add error alert light (hidden by default)
        self.error_light_button = QToolButton()
        self.error_light_button.setText("🔴")
        self.error_light_button.setToolTip("Error detected - Click to acknowledge")
        self.error_light_button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        
        # Create dropdown menu for error light
        error_menu = QMenu(self)
        acknowledge_action = QAction("✓ Noticed", self)
        acknowledge_action.triggered.connect(self._acknowledge_error)
        error_menu.addAction(acknowledge_action)
        self.error_light_button.setMenu(error_menu)
        
        self.error_light_button.setVisible(False)  # Hidden by default
        #DONT'T add the error to the toolbar
        #It is commented on purpose
        #toolbar.addWidget(self.error_light_button)
        #####
        
        # Add AI login widget (right-aligned)
        self.ai_login_widget = AILoginWidget(self.settings_manager, self)
        self.ai_login_widget.provider_changed.connect(self._on_ai_provider_changed)
        #DONT'T add the ai_login to the toolbar
        #It is commented on purpose
        #toolbar.addWidget(self.ai_login_widget)
        #####
        
        # Hide AI widget by default - enable later for inline completions
        # Check settings to allow manual override if needed
        self.ai_login_widget.setVisible(self.settings_manager.get_setting("ai/ui_visible", False))

    def _create_console(self) -> QTextEdit:
        """Create the Console widget."""
        console = QTextEditWithClear()
        console.setReadOnly(True)
        console.setPlaceholderText("Console output will appear here...")
        console.setObjectName("consoleText")
        return console

    def _setup_menu_bar(self):
        """Setup the menu bar."""
        menu_bar = self.menuBar()
        
        # File menu
        file_menu = menu_bar.addMenu("&File")
        #file_menu.addAction("New", self._new_file)
        #file_menu.addAction("Open...", self._open_file)
        #file_menu.addSeparator()
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self._open_settings_dialog)
        file_menu.addAction(settings_action)
        file_menu.addSeparator()
        exit_action = QAction("Exit", self)
        exit_action.setShortcut(QKeySequence("Alt+F4"))
        exit_action.triggered.connect(self.exit_application)
        file_menu.addAction(exit_action)
        
        # Edit menu
        #edit_menu = menu_bar.addMenu("&Edit")
        #edit_menu.addAction("Undo")
        #edit_menu.addAction("Redo")
        #edit_menu.addSeparator()
        #edit_menu.addAction("Cut")
        #edit_menu.addAction("Copy")
        #edit_menu.addAction("Paste")
        
        # Run menu
        run_menu = menu_bar.addMenu("&Run")
        run_menu.addAction(self.run_action)
        run_menu.addSeparator()
        
        # Debug menu
        debug_menu = menu_bar.addMenu("&Debug")
        debug_menu.addAction(self.debug_action)
        debug_menu.addSeparator()
        debug_menu.addAction(self.debug_continue_action)
        debug_menu.addAction(self.debug_step_over_action)
        debug_menu.addAction(self.debug_step_into_action)
        debug_menu.addAction(self.debug_step_out_action)
        debug_menu.addSeparator()
        debug_menu.addAction(self.debug_stop_action)
        debug_menu.addSeparator()
        
        # Toggle breakpoint action
        self.toggle_breakpoint_action = QAction("Toggle Breakpoint", self)
        self.toggle_breakpoint_action.setToolTip("Toggle breakpoint at current line (F9)")
        self.toggle_breakpoint_action.setShortcut(QKeySequence("F9"))
        self.toggle_breakpoint_action.triggered.connect(self._toggle_breakpoint)
        debug_menu.addAction(self.toggle_breakpoint_action)
        
        debug_menu.addSeparator()
        
        # Show debug messages in console toggle
        self.show_debug_messages_action = QAction("Show debug messages in console", self)
        self.show_debug_messages_action.setCheckable(True)
        self.show_debug_messages_action.setChecked(self._show_debug_console_messages)
        self.show_debug_messages_action.triggered.connect(self._toggle_show_debug_messages)
        debug_menu.addAction(self.show_debug_messages_action)
        
        # View menu
        view_menu = menu_bar.addMenu("&View")
        
        # Widgets submenu (move existing dock widget toggles here)
        widgets_menu = view_menu.addMenu("Widgets")
        widgets_menu.addAction(self.project_explorer_dock.toggleViewAction())
        widgets_menu.addAction(self.object_inspector_dock.toggleViewAction())
        widgets_menu.addAction(self.event_manager_dock.toggleViewAction())
        widgets_menu.addAction(self.function_publisher_dock.toggleViewAction())
        widgets_menu.addAction(self.package_manager_dock.toggleViewAction())
        widgets_menu.addAction(self.console_dock.toggleViewAction())
        
        # Advanced menu
        self._setup_advanced_menu(menu_bar)
        
        # Help menu
        help_menu = menu_bar.addMenu("&Help")
        
        # Open Documentation action
        open_docs_action = QAction("Open Documentation", self)
        open_docs_action.triggered.connect(self._open_documentation)
        help_menu.addAction(open_docs_action)
        
        help_menu.addSeparator()
        
        about_action = QAction("About XPyCode IDE", self)
        about_action.triggered.connect(self._open_about)
        help_menu.addAction(about_action)
        
        # Create minimap action for programmatic use (not added to menu since it's in settings now)
        self.minimap_action = QAction("Show Minimap", self)
        self.minimap_action.setCheckable(True)
        self.minimap_action.setChecked(self._minimap_visible)

    def _setup_status_bar(self):
        """Setup the status bar."""
        status_bar = self.statusBar()
        status_bar.showMessage("Ready")
    
    def _setup_advanced_menu(self, menu_bar):
        """Setup the Advanced menu with dynamic actions."""
        # Clear and register actions
        clear_actions()
        self._register_advanced_actions()
        
        # Create Advanced menu
        advanced_menu = menu_bar.addMenu("&Advanced")
        
        # Loop through tabs and create submenus
        for tab_name in get_tabs():
            tab_submenu = advanced_menu.addMenu(tab_name)
            
            # Add actions for this tab
            for action_def in get_actions(tab_name):
                action = QAction(action_def.short_name, self)
                action.setToolTip(action_def.description)
                action.triggered.connect(action_def.action_function)
                tab_submenu.addAction(action)
    
    def _register_advanced_actions(self):
        """Register advanced actions."""
        # Register Kill Kernel action under Master tab
        register_action("Master", AdvancedAction(
            short_name="Restart Kernel",
            description="Stop and restart the Python Kernel for a workbook",
            action_function=self._advanced_kill_kernel_dialog
        ))
        
        # Register Restart Add-In action under Master tab
        register_action("Master", AdvancedAction(
            short_name="Restart Add-In and Kernel",
            description="Restart the Add-In and Kernel for a workbook",
            action_function=self._advanced_restart_addin_dialog
        ))
    
    def _advanced_kill_kernel_dialog(self):
        """Show dialog to select workbook and kill its kernel."""
        # Build list of workbook choices
        if not self._workbook_names:
            QMessageBox.warning(
                self,
                "No Workbooks",
                "No workbooks are currently connected."
            )
            return
        
        # Get workbook names and IDs
        workbook_names = list(self._workbook_names.values())
        workbook_ids = list(self._workbook_names.keys())
        
        # Show selection dialog
        selected_name, ok = QInputDialog.getItem(
            self,
            "Select Workbook",
            "Select workbook to kill kernel:",
            workbook_names,
            0,
            False
        )
        
        if ok and selected_name:
            # Find corresponding workbook_id
            for i, name in enumerate(workbook_names):
                if name == selected_name:
                    workbook_id = workbook_ids[i]
                    self._send_kill_kernel(workbook_id)
                    break
    
    def _send_kill_kernel(self, workbook_id: str):
        """Send kill_kernel message to business layer."""
        workbook_name = self._workbook_names.get(workbook_id, workbook_id)
        
        # Create and send message
        message = json.dumps({
            "type": "kill_kernel",
            "workbook_id": workbook_id
        })
        self.websocket.sendTextMessage(message)
        
        # Log to console
        self.log_to_console(f"Killing kernel for: {workbook_name}...", level=OutputLevel.SIMPLE)
        logger.info(f"[IDE] Sent kill_kernel request for workbook: {workbook_id}")
    
    def _advanced_restart_addin_dialog(self):
        """Show dialog to select workbook and restart its add-in."""
        # Build list of workbook choices
        if not self._workbook_names:
            QMessageBox.warning(
                self,
                "No Workbooks",
                "No workbooks are currently connected."
            )
            return
        
        # Get workbook names and IDs
        workbook_names = list(self._workbook_names.values())
        workbook_ids = list(self._workbook_names.keys())
        
        # Show selection dialog
        selected_name, ok = QInputDialog.getItem(
            self,
            "Select Workbook",
            "Select workbook to restart add-in:",
            workbook_names,
            0,
            False
        )
        
        if ok and selected_name:
            # Find corresponding workbook_id
            for i, name in enumerate(workbook_names):
                if name == selected_name:
                    workbook_id = workbook_ids[i]
                    self._send_restart_addin(workbook_id)
                    break
    
    def _send_restart_addin(self, workbook_id: str):
        """Send restart_addin message to business layer."""
        workbook_name = self._workbook_names.get(workbook_id, workbook_id)
        
        # Create and send message
        message = json.dumps({
            "type": "restart_addin",
            "workbook_id": workbook_id
        })
        self.websocket.sendTextMessage(message)
        
        # Log to console
        self.log_to_console(f"Restarting add-in for: {workbook_name}...", level=OutputLevel.SIMPLE)
        logger.info(f"[IDE] Sent restart_addin request for workbook: {workbook_id}")
    
    def _set_hover_mode(self, mode: str):
        """
        Set hover mode and broadcast to all kernels.
        
        Args:
            mode: Either "compact" or "detailed"
        """
        # Validate mode parameter
        if mode not in (self.HOVER_MODE_COMPACT, self.HOVER_MODE_DETAILED):
            logger.warning(f"[IDE] Invalid hover mode '{mode}', ignoring request")
            return
        
        logger.debug(f"[IDE] Setting hover mode to: {mode}")
        message = json.dumps({
            "type": "set_hover_mode",
            "mode": mode,
        })
        self.websocket.sendTextMessage(message)
    
    def _toggle_minimap(self):
        """Toggle minimap visibility for all editors."""
        self._minimap_visible = self.minimap_action.isChecked()
        logger.debug(f"[IDE] Toggling minimap visibility to: {self._minimap_visible}")
        
        # Apply to all existing editors
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_minimap_visible(self._minimap_visible)

    def _toggle_console_filter(self, checked: bool):
        """Toggle console output filtering."""
        if checked:
            self._console_source_filter = "ide_only"
            self.log_to_console("Console filter: showing IDE output only", "#E67E22", level=OutputLevel.DETAILED)
        else:
            self._console_source_filter = "all"
            self.log_to_console("Console filter: showing all output", "#E67E22", level=OutputLevel.DETAILED)
    
    def _apply_console_only_ide(self, value: bool):
        """Apply console only IDE filter setting."""
        self._toggle_console_filter(value)

    def _set_theme(self, theme_id: str):
        """
        Set the editor theme for all open editors.
        
        Args:
            theme_id: The Monaco theme identifier (e.g., 'vs-dark', 'vs')
        """
        self._current_theme = theme_id
        logger.info(f"[IDE] Setting theme to: {theme_id}")
        
        # Apply to all existing editors
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_theme(theme_id)

        if self.welcome_widget:
            for editor in self.welcome_widget.editors:
                editor.set_theme(theme_id)

    def _get_app_stylesheet(self, theme_id: str) -> str:
        """
        Get the Qt stylesheet for the specified app theme.
        
        Args:
            theme_id: The app theme identifier
            
        Returns:
            The Qt stylesheet string
        """
        return self._theme_loader.generate_stylesheet(theme_id)

    def _set_app_theme(self, theme_id: str):
        """
        Set the app-level Qt stylesheet theme.
        
        Args:
            theme_id: The app theme identifier (e.g., 'xpy-dark', 'xpy-light')
        """
        self._current_app_theme = theme_id
        logger.info(f"[IDE] Setting app theme to: {theme_id}")
        
        # Get and apply the stylesheet
        stylesheet = self._get_app_stylesheet(theme_id)
        self.setStyleSheet(stylesheet)

    def _show_error_light(self):
        """Show the error alert light in the toolbar."""
        ##NOT USED NOW ON PURPOSE
        ##DON'T REMOVE THE RETURN
        return
        
        if not self._has_unnoticed_error:
            self._has_unnoticed_error = True
            self.error_light_button.setVisible(True)
            logger.debug("[IDE] Error light shown")

    def _acknowledge_error(self):
        """Acknowledge the error and hide the error alert light."""
        self._has_unnoticed_error = False
        self.error_light_button.setVisible(False)
        logger.debug("[IDE] Error acknowledged, light hidden")


    def _new_file(self):
        """Create a new editor tab."""
        editor = MonacoEditor()
        index = self.editor_tabs.addTab(editor, "Untitled")
        self.editor_tabs.setCurrentIndex(index)

    def _open_file(self):
        """Open a file (placeholder)."""
        # Placeholder for file dialog
        self.log_to_console("Open file dialog not yet implemented")
    
    def _open_settings_dialog(self):
        """Open the settings dialog."""
        # Request settings from business layer
        request_id = f"settings_{id(self)}"
        message = json.dumps({
            "type": "get_all_settings",
            "request_id": request_id
        })
        self.websocket.sendTextMessage(message)
        logger.debug("[IDE] Requested settings from business layer")
        
        # Note: The dialog will be opened when the response arrives
        # See _handle_all_settings_response

    def _open_about(self):
        import webbrowser
        url = 'https://xpycode.com'
        try:
            webbrowser.open(url)
            logger.info(f"[IDE] Opened about at {url}")
        except Exception as e:
            logger.error(f"[IDE] Failed to open about: {e}")
            QMessageBox.warning(
                self,
                "About Error",
                f"Failed to open about: {e}"
            )

    def _open_documentation(self):
        """Open the documentation in the default web browser."""
        import webbrowser
        
        # Get docs_port from instance (set in main.py)
        docs_port = getattr(self, 'docs_port', 0)
        
        if docs_port:
            if docs_port>0:
                url = f"http://127.0.0.1:{docs_port}"
            else:
                url = 'https://docs.xpycode.com'
            try:
                webbrowser.open(url)
                logger.info(f"[IDE] Opened documentation at {url}")
            except Exception as e:
                logger.error(f"[IDE] Failed to open documentation: {e}")
                QMessageBox.warning(
                    self,
                    "Documentation Error",
                    f"Failed to open documentation: {e}"
                )
        else:
            QMessageBox.information(
                self,
                "Documentation",
                "Documentation server is not available.\n\n"
                "You can view the documentation online at:\n"
                "https://gb-bge-advisory.github.io/xpycode_master_repo/"
            )

    def _close_editor_tab(self, index: int):
        """
        Close an editor tab.
        
        When the last tab is closed, the central stack automatically
        switches to the welcome widget via _on_tab_changed.
        """
        self.editor_tabs.removeTab(index)
        # Note: _on_tab_changed will be called automatically with index=-1
        # when the last tab is closed, which will show the welcome widget

    def _close_tabs_for_workbook(self, workbook_id: str):
        """
        Close all editor tabs belonging to a specific workbook.
        
        This is called when a workbook disconnects to prevent orphaned tabs.
        Iterates through all tabs in reverse order to safely remove tabs.
        
        Args:
            workbook_id: The workbook ID whose tabs should be closed.
        """
        # Iterate in reverse order to safely remove tabs during iteration
        for i in range(self.editor_tabs.count() - 1, -1, -1):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if tab_widget.workbook_id == workbook_id:
                    self.editor_tabs.removeTab(i)
        
        # Note: _on_tab_changed handles showing welcome widget if no tabs remain

    def _update_workbook_name(self, workbook_id: str, new_name: str):
        """
        Update workbook name in Project Explorer.
        
        Args:
            workbook_id: The workbook ID.
            new_name: The new workbook name.
        """
        self._workbook_names[workbook_id] = new_name
        item = self.project_explorer.get_workbook_item(workbook_id)
        if item:
            item.setText(0, f"📗 {new_name}")

    def get_workbook_name(self, workbook_id: str) -> str:
        """
        Get the workbook name for a given workbook ID.
        
        Args:
            workbook_id: The workbook ID.
        Returns:
        The workbook name, or workbook_id if not found.
        """
        return self._workbook_names.get(workbook_id, workbook_id)

    def set_workbook_name(self, workbook_id: str, name: str):
        """
        Set the workbook name for a given workbook ID.
        
        Args:
            workbook_id: The workbook ID.
            name: The workbook name.
        """
        self._workbook_names[workbook_id] = name

    def _run_code(self, debug: bool = False):
        """
        Run the code in the current editor with Smart Synchronization.
        
        Smart Sync ensures the Kernel has the latest version of ALL modules 
        for the workbook before execution:
        1. Collects code from ALL open editors for the workbook
        2. Merges with cached modules from the Business Layer
        3. Only sends update_module for modules that have changed since last sync
        4. Sends run_module message with optional debug mode
        
        F5/Ctrl+R behavior:
        - If cursor is inside a function, runs that function automatically
        - If cursor is not in a function, shows a warning
        
        Args:
            debug: Whether to run in debug mode (default: False)
        
        This ensures inter-module dependencies work correctly because the
        Kernel's InMemoryModuleLoader handles import resolution for all modules.
        """
        # Check if we should clear console on run
        clear_on_run = self._get_setting("console.clear_on_run", False)
        if clear_on_run:
            self.console.clear()
        
        # Get the currently active editor
        current_widget = self.editor_tabs.currentWidget()
        if not isinstance(current_widget, MonacoEditor):
            self.log_to_console("No active editor found", level=OutputLevel.DETAILED)
            return
        
        editor = current_widget
        current_index = self.editor_tabs.currentIndex()
        tab_title = self.editor_tabs.tabText(current_index)
        
        # Get workbook_id from editor, fall back to project explorer selection
        workbook_id = editor.workbook_id
        # Ignore the special welcome tab workbook_id
        if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
            workbook_id = self.project_explorer.get_selected_workbook_id()
        
        if not workbook_id:
            QMessageBox.warning(
                self,
                "No Workbook Selected",
                "Please select a workbook in the Project Explorer before running code."
            )
            return
        
        # Initialize sync tracking for this workbook if needed
        if workbook_id not in self._synced_module_hashes:
            self._synced_module_hashes[workbook_id] = {}
        
        # Collect all open editors for this workbook
        editors_to_update = []
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if tab_widget.workbook_id == workbook_id:
                    tab_name = self.editor_tabs.tabText(i)
                    editors_to_update.append((i, tab_widget, tab_name))
        
        # Dictionary to collect code from open editors
        # Keys: index, Values: (module_name, code)
        collected_files = {}
        # Flag to prevent multiple executions
        execution_triggered = [False]
        # Store cursor position for function detection
        cursor_position = [None]  # [{'lineNumber': int, 'column': int}]
        
        def _compute_hash(code: str) -> str:
            """Compute SHA256 hash of code for change detection."""
            return hashlib.sha256(code.encode('utf-8')).hexdigest()
        
        def on_all_files_collected():
            """Called when all files have been collected, proceeds with sync and execution."""
            # Get target module name (tab titles no longer have .py extension)
            target_module_name = _strip_py_extension(tab_title)
            
            target_code = None
            
            # Merge open editor code with cached modules
            # Priority: open editors > cached modules (editor code is always fresher)
            all_modules: Dict[str, str] = {}
            
            # First, add cached modules from Business Layer
            if workbook_id in self._module_cache:
                all_modules.update(self._module_cache[workbook_id])
            
            # Then, overlay with open editor code (overrides cache)
            for idx, (module_name, code) in collected_files.items():
                # Module names no longer have .py extension
                module_name = _strip_py_extension(module_name)
                if module_name and code is not None:
                    all_modules[module_name] = code
                    # Also update the cache
                    if workbook_id not in self._module_cache:
                        self._module_cache[workbook_id] = {}
                    self._module_cache[workbook_id][module_name] = code
            
            if not all_modules:
                self.log_to_console("No modules found for this workbook", level=OutputLevel.DETAILED)
                return
            
            # Smart sync: only send update_module for changed modules
            modules_synced = 0
            for module_name, code in all_modules.items():
                if not code:
                    continue
                    
                # Validate that module_name is a valid Python identifier
                if not module_name or not module_name.isidentifier():
                    logger.warning(
                        f"[IDE] Skipping module '{module_name}': not a valid Python identifier"
                    )
                    continue
                
                # Track the target module's code for function parsing
                if module_name == target_module_name:
                    target_code = code
                
                # Compute hash and check if changed
                code_hash = _compute_hash(code)
                prev_hash = self._synced_module_hashes[workbook_id].get(module_name)
                
                if code_hash != prev_hash:
                    # Module has changed, send update
                    update_message = json.dumps({
                        "type": "update_module",
                        "workbook_id": workbook_id,
                        "module_name": module_name,
                        "code": code,
                    })
                    logger.info(f"[IDE] Sending update_module for module: {module_name}")
                    self.websocket.sendTextMessage(update_message)
                    
                    # Update the synced hash
                    self._synced_module_hashes[workbook_id][module_name] = code_hash
                    modules_synced += 1
                else:
                    logger.debug(f"[IDE] Module '{module_name}' unchanged, skipping sync")
            
            if modules_synced > 0:
                logger.info(f"[IDE] Synced {modules_synced} module(s) to Kernel")
            
            # Validate the target module
            if not target_module_name or not target_module_name.isidentifier():
                self.log_to_console(
                    f"Cannot run: Module name '{target_module_name}' is not a valid Python identifier. "
                    f"Rename the tab to use only letters, numbers, and underscores (e.g., 'my_module').",
                    "#ff6b6b", 
                    level=OutputLevel.SIMPLE
                )
                return
            
            if not target_code or not target_code.strip():
                self.log_to_console("No code to run", level=OutputLevel.SIMPLE)
                return
            
            # Determine the function to run based on cursor position
            selected_function = None
            cursor_line = cursor_position[0].get('lineNumber', 1) if cursor_position[0] else 1
            
            # Find the function at the cursor position
            function_at_cursor = self._find_function_at_cursor(target_code, cursor_line)
            
            if function_at_cursor:
                # Validate function name as a Python identifier to prevent code injection
                if not function_at_cursor.isidentifier():
                    self.log_to_console(
                        f"Cannot run: Function name '{function_at_cursor}' is not a valid Python identifier.",
                        "#ff6b6b", 
                        level=OutputLevel.SIMPLE
                    )
                    return
                selected_function = function_at_cursor
                self.log_to_console(f"Running function: {function_at_cursor}()", level=OutputLevel.COMPLETE)
            else:
                # Cursor is not positioned on a function - show warning
                self.log_to_console(
                    "No function at cursor position. Place your cursor inside a function definition to run it.",
                    "#E67E22",  # Orange color for warning
                    level=OutputLevel.SIMPLE                )
                return
            
            # Build the execution code using import statement (old method, kept for reference)
            # Now using run_module message type for unified execution
            if not selected_function:
                # No function selected - should not happen since we validate earlier
                return
            
            # Get breakpoints for this workbook (Phase 1: Debug support)
            breakpoints = self.breakpoint_manager.get_breakpoints(workbook_id)
            
            # Send run_module request to Business Layer
            # This unifies IDE Run with Excel function execution
            message = json.dumps({
                "type": "run_module",
                "workbook_id": workbook_id,
                "module_name": target_module_name,
                "function_name": selected_function,
                "args": [],  # IDE run always uses no args
                "debug": debug,  # Use debug parameter
                "breakpoints": breakpoints,  # Pass breakpoints for debug mode
                "source": "ide",  # Track execution source
            })
            
            workbook_name=self.get_workbook_name(workbook_id)

            if debug:
                logger.info(f"[IDE] Sending run_module (DEBUG MODE) for workbook: {workbook_id}")
                self.log_to_console(f"🐛 Debugging {target_module_name}.{selected_function}() for workbook: {workbook_name}", level=OutputLevel.SIMPLE)
                # Set debug state
                self._set_debug_state(True, workbook_id)
            else:
                logger.info(f"[IDE] Sending run_module for workbook: {workbook_id}")
                self.log_to_console(f"Running {target_module_name}.{selected_function}() for workbook: {workbook_name}", level=OutputLevel.SIMPLE)
            
            logger.debug(f"[IDE] Running: {target_module_name}.{selected_function}()")
            self.websocket.sendTextMessage(message)
            logger.debug("[IDE] Message sent via WebSocket")
        
        def make_callback(idx, tab_name):
            """Create a callback function for a specific editor."""
            def on_text_received(code):
                # Module name is the tab title (no longer has .py extension)
                module_name = _strip_py_extension(tab_name)
                collected_files[idx] = (module_name, code)
                
                # Check if all files have been collected and execution hasn't been triggered
                if len(collected_files) == expected_count and not execution_triggered[0]:
                    execution_triggered[0] = True
                    on_all_files_collected()
            return on_text_received
        
        def on_cursor_position_received(pos):
            """Called when cursor position is received from the current editor."""
            cursor_position[0] = pos
            logger.debug(f"[IDE] Cursor position: {pos}")
            
            # Now collect files from all editors
            for idx, tab_widget, tab_name in editors_to_update:
                callback = make_callback(idx, tab_name)
                tab_widget.get_text_sync(callback)
        
        # Handle case where no editors are open for this workbook
        expected_count = len(editors_to_update)
        if expected_count == 0:
            # Still try to run if we have cached modules
            if workbook_id in self._module_cache and self._module_cache[workbook_id]:
                execution_triggered[0] = True
                cursor_position[0] = {'lineNumber': 1, 'column': 1}
                on_all_files_collected()
            else:
                self.log_to_console("No modules found for this workbook", level=OutputLevel.SIMPLE)
            return
        
        # First, get cursor position from the current editor
        # Then, request code from all open editors
        editor.get_cursor_position(on_cursor_position_received)

    def _find_top_level_functions(self, code: str) -> list:
        """
        Find all top-level function definitions in the code.
        
        Uses AST parsing first, falls back to regex if AST fails.
        
        Args:
            code: The Python code to parse.
            
        Returns:
            A list of function names.
        """
        functions = []
        
        try:
            # Try AST parsing first (more accurate)
            tree = ast.parse(code)
            # Iterate directly over tree.body for O(n) complexity
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    functions.append(node.name)
        except SyntaxError:
            # Fall back to regex for code with syntax errors
            pattern = re.compile(r'^def\s+(\w+)\s*\(', re.MULTILINE)
            matches = pattern.findall(code)
            functions = matches
        
        return functions

    def _find_function_at_cursor(self, code: str, line: int) -> Optional[str]:
        """
        Find the function that contains the given cursor line.
        
        Uses AST parsing to find which function definition the cursor is inside.
        
        Args:
            code: The Python code to parse.
            line: The 1-based line number of the cursor.
            
        Returns:
            The name of the function at the cursor, or None if not in a function.
        """
        try:
            tree = ast.parse(code)
            # Find the function that contains this line
            for node in tree.body:
                if isinstance(node, ast.FunctionDef):
                    # Check if cursor line is within the function definition
                    # node.lineno is the line where 'def' starts (1-based)
                    # node.end_lineno is the last line of the function (1-based)
                    start_line = node.lineno
                    end_line = node.end_lineno or start_line
                    if start_line <= line <= end_line:
                        return node.name
        except SyntaxError:
            # If code has syntax errors, try a simpler approach
            # Look for the nearest 'def' above the cursor
            lines = code.split('\n')
            for i in range(line - 1, -1, -1):
                match = re.match(r'^def\s+(\w+)\s*\(', lines[i])
                if match:
                    # Found a function definition above the cursor
                    # This is a rough approximation - may not be accurate
                    # if the cursor is after the function ends
                    return match.group(1)
        
        return None

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
        color_style=f"color: {color}; " if color else ""
        return f'<span style="{color_style}white-space: pre-wrap">{escaped_text}</span>'

    def log_to_console(
        self, 
        message: str, 
        color: Optional[str] = None,
        level: OutputLevel = OutputLevel.SIMPLE
    ):
        """
        Log a message to the console with optional color and level filtering.
        
        This method ensures proper line breaks for status messages.
        If the message doesn't end with a newline, one is added.
        For stdout/stderr from code execution, use direct insertHtml calls
        which preserve the exact newline behavior from print().
        
        Args:
            message: The message to log.
            color: The color to use for the message (default: gray/white #d4d4d4).
            level: Output level (SIMPLE, DETAILED, COMPLETE).
                   Message is only shown if current setting allows this level.
                   
        Output Level filtering:
            Setting = SIMPLE    → Only SIMPLE messages shown
            Setting = DETAILED  → SIMPLE + DETAILED messages shown
            Setting = COMPLETE  → All messages shown (SIMPLE + DETAILED + COMPLETE)
        """
        # Check if current setting allows this level
        if not self._console_output_level.allows(level):
            return  # Don't output, level is higher than current setting
        
        self.console.moveCursor(QTextCursor.MoveOperation.End)
        formatted_html = self._format_console_html(message, color)
        # Only add trailing <br> if the message doesn't already end with a newline
        # (which would have been converted to <br> by _format_console_html)
        #if message and not message.endswith('\n'):
        #    formatted_html += "<br>"
        self.console.insertHtml(formatted_html)

        doc = self.console.document()
        cursor = QTextCursor(doc)
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertBlock()  # this is what creates a new QTextBlock
        
        # Enforce max lines after adding content
        self._enforce_console_max_lines()

    def add_editor_tab(self, title: str, content: str = "", workbook_id: Optional[str] = None) -> MonacoEditor:
        """
        Add a new editor tab with the given title and content.
        
        Args:
            title: The tab title.
            content: The initial content of the editor.
            workbook_id: Optional workbook ID to associate with this editor.
            
        Returns:
            The created MonacoEditor instance.
        """
        logger.debug(f"[IDE] add_editor_tab: title={title}, content_length={len(content) if content else 0}, workbook_id={workbook_id}")
        
        editor = MonacoEditor()
        if workbook_id:
            editor.workbook_id = workbook_id
        
        # Ensure we're showing the editor tabs (not welcome widget)
        #self.central_stack.setCurrentIndex(1)
        
        # Connect content change signal BEFORE setting text
        # This ensures the handler is in place, but MonacoEditor._on_bridge_content_changed
        # will filter out spurious signals during programmatic text setting
        index = self.editor_tabs.addTab(editor, title)
        
        def on_content_changed(new_content: str, tab_idx=index):
            self._on_editor_content_changed(tab_idx, new_content)
        editor.contentChanged.connect(on_content_changed)
        
        # Connect completion request signal
        def on_completion_requested(request_json: str, ed=editor):
            self._handle_completion_request(ed, request_json)
        editor.completionRequested.connect(on_completion_requested)
        
        # Connect signature help request signal
        def on_signature_help_requested(request_json: str, ed=editor):
            self._handle_signature_help_request(ed, request_json)
        editor.signatureHelpRequested.connect(on_signature_help_requested)
        
        # Connect hover request signal
        def on_hover_requested(request_json: str, ed=editor):
            self._handle_hover_request(ed, request_json)
        editor.hoverRequested.connect(on_hover_requested)
        
        # Connect diagnostic request signal
        def on_diagnostic_requested(request_json: str, ed=editor):
            self._handle_diagnostic_request(ed, request_json)
        editor.diagnosticRequested.connect(on_diagnostic_requested)
        
        # Connect breakpoints changed signal
        def on_breakpoints_changed(changes_json: str, ed=editor):
            self._on_breakpoints_changed(ed, changes_json)
        editor.breakpointsChanged.connect(on_breakpoints_changed)
        
        # Apply current settings to new editor
        editor.set_minimap_visible(self._minimap_visible)
        editor.set_tab_size(self._editor_tab_size)
        editor.set_insert_spaces(self._editor_insert_spaces)
        editor.set_word_wrap(self._editor_word_wrap)
        editor.set_font_size(self._editor_font_size)
        
        # Apply current theme to new editor
        editor.set_theme(self._current_theme)
        
        # Now set the content (after signal connection)
        if content:
            logger.debug(f"[IDE] add_editor_tab: Setting initial content for '{title}'")
            editor.set_text(content)
        
        self.editor_tabs.setCurrentIndex(index)
        
        # Restore breakpoints for this editor if it has a workbook_id
        if workbook_id:
            module_name = _strip_py_extension(title)
            self._restore_breakpoints_for_editor(editor, workbook_id, module_name)
        
        editor.setFocus()
        return editor

    def _on_editor_content_changed(self, tab_index: int, content: str):
        """
        Handle editor content change for auto-save.
        
        This is called when the Monaco editor content changes (debounced).
        Saves the module to the Business Layer and updates local cache.
        
        Safeguards:
        - Validates that the tab still exists and has an associated workbook.
        - If the editor reports empty content but the editor is not yet fully initialized,
          ignores the update to prevent cache corruption.
        
        Args:
            tab_index: The index of the tab that changed.
            content: The new content of the editor.
        """
        # Get the tab widget and module info
        if tab_index >= self.editor_tabs.count():
            logger.debug(f"[IDE] _on_editor_content_changed: tab_index {tab_index} out of range")
            return
        
        tab_widget = self.editor_tabs.widget(tab_index)
        if not isinstance(tab_widget, MonacoEditor):
            return
        
        workbook_id = tab_widget.workbook_id
        module_name = self.editor_tabs.tabText(tab_index)
        
        if not workbook_id or not module_name:
            logger.debug(f"[IDE] _on_editor_content_changed: missing workbook_id or module_name")
            return
        
        # Strip .py extension if present
        module_name = _strip_py_extension(module_name)
        
        # Safeguard: If editor is not fully initialized and reports empty content,
        # don't overwrite existing cached content (prevents cache corruption during init)
        # Note: User-initiated empty content is allowed because the editor will be
        # initialized at that point (is_initialized=True)
        if not content and not tab_widget.is_initialized:
            existing_content = self._module_cache.get(workbook_id, {}).get(module_name)
            if existing_content:
                logger.debug(
                    f"[IDE] _on_editor_content_changed: Ignoring empty content update for "
                    f"'{module_name}' (editor not initialized, cached content exists)"
                )
                return
        
        logger.debug(f"[IDE] _on_editor_content_changed: Updating cache for '{module_name}', content_length={len(content)}")
        
        # Update local cache
        if workbook_id not in self._module_cache:
            self._module_cache[workbook_id] = {}
        self._module_cache[workbook_id][module_name] = content
        
        # Update EventManager and FunctionPublisher module cache
        self.event_manager.set_module_cache(workbook_id, self._module_cache.get(workbook_id, {}))
        #self.function_publisher.set_modules_cache(workbook_id, self._module_cache.get(workbook_id, {}))
        
        # Save to Business Layer (which will forward to the workbook)
        message = json.dumps({
            "type": "save_module",
            "workbook_id": workbook_id,
            "module_name": module_name,
            "code": content,
        })
        self.websocket.sendTextMessage(message)
        logger.debug(f"[IDE] Auto-saved module '{module_name}' for workbook '{workbook_id}'")

    def _collect_dirty_files_sync(self, workbook_id: str) -> Dict[str, str]:
        """
        Collect current content from all open editor tabs for a workbook.
        
        This collects "dirty files" - the current editor state that may not
        yet be synced to the kernel. This is used for cross-module completion
        to ensure Jedi sees the latest code in all modules.
        
        Cache Mechanism:
            The `_module_cache` is updated on every debounced content change
            via `_on_editor_content_changed` (triggered 500ms after typing stops).
            This means the cache may be up to 500ms stale, but this is acceptable
            for LSP operations as the user is typically still editing.
        
        Limitations:
            - Content changes made in the last 500ms may not be reflected.
            - If the user types very quickly across multiple files, there may
              be brief inconsistencies between modules.
        
        Alternative Approach:
            For truly real-time content, each call would need to asynchronously
            fetch content from all editor tabs using get_text_sync() with callbacks.
            This would be more accurate but significantly slower and more complex.
        
        Args:
            workbook_id: The workbook ID to collect files for.
            
        Returns:
            Dictionary of {module_name: content} for all modules in the workbook.
        """
        dirty_files: Dict[str, str] = {}
        
        # Collect from module cache which is updated on every debounced content change
        if workbook_id in self._module_cache:
            dirty_files.update(self._module_cache[workbook_id])
        
        logger.debug(f"[IDE] Collected {len(dirty_files)} dirty files for workbook '{workbook_id}'")
        return dirty_files

    def update_event_manager_module_cache(self, workbook_id: str):
        """
        DEPRECATED: 
        
        """
        return
        """
        Force update the EventManager's and FunctionPublisher's module cache with current editor content.
        
        This method synchronously collects content from all open editor tabs
        for the specified workbook and updates the EventManager's and FunctionPublisher's module cache.
        This ensures that the FunctionSelectorDialog has access to the latest
        code, including newly written functions that may not have been saved yet.
        
        Called by EventManager before opening the FunctionSelectorDialog to ensure
        newly written functions appear immediately.
        
        Args:
            workbook_id: The workbook ID to update the cache for.
        """
        # Collect current content from all open editors for this workbook
        current_modules = self._collect_dirty_files_sync(workbook_id)
        
        # Update the EventManager's and FunctionPublisher's module cache
        self.event_manager.set_module_cache(workbook_id, current_modules)
        self.function_publisher.set_modules_cache(workbook_id, current_modules)
        
        logger.debug(f"[IDE] Updated EventManager and FunctionPublisher module cache with {len(current_modules)} modules for workbook '{workbook_id}'")

    def _handle_completion_request(self, editor: MonacoEditor, request_json: str):
        """
        Handle code completion request from a Monaco editor.
        
        Injects workbook_id, module_name, and dirty_files from the editor/tab
        into the request and forwards it to the Business Layer via WebSocket.
        
        Args:
            editor: The MonacoEditor instance that requested completion.
            request_json: JSON string containing the completion request from JavaScript.
        """
        try:
            request = json.loads(request_json)
        except json.JSONDecodeError as e:
            logger.warning(f"[IDE] Failed to parse completion request: {e}")
            return
        
        # Get workbook_id from editor
        workbook_id = editor.workbook_id
        if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
            logger.debug("[IDE] Completion request ignored: no workbook_id or welcome tab")
            return
        
        # Find the module name from the tab title
        module_name = None
        for i in range(self.editor_tabs.count()):
            if self.editor_tabs.widget(i) is editor:
                module_name = self.editor_tabs.tabText(i)
                break
        
        if not module_name:
            logger.debug("[IDE] Completion request ignored: could not find module name")
            return
        
        # Strip .py extension if present
        module_name = _strip_py_extension(module_name)
        
        # Collect dirty files for cross-module completion
        dirty_files = self._collect_dirty_files_sync(workbook_id)
        
        # Send completion request to Business Layer with injected workbook/module info
        message = json.dumps({
            "type": "completion_request",
            "workbook_id": workbook_id,
            "module_name": module_name,
            "code": request.get("code", ""),
            "line": request.get("line", 1),
            "column": request.get("column", 0),
            "request_id": request.get("request_id"),
            "dirty_files": dirty_files,
        })
        logger.debug(f"[IDE] Sending completion_request for module '{module_name}' with {len(dirty_files)} dirty files")
        self.websocket.sendTextMessage(message)

    def _handle_signature_help_request(self, editor: MonacoEditor, request_json: str):
        """
        Handle signature help request from a Monaco editor.
        
        Injects workbook_id, module_name, and dirty_files from the editor/tab
        into the request and forwards it to the Business Layer via WebSocket.
        
        Args:
            editor: The MonacoEditor instance that requested signature help.
            request_json: JSON string containing the signature help request from JavaScript.
        """
        try:
            request = json.loads(request_json)
        except json.JSONDecodeError as e:
            logger.warning(f"[IDE] Failed to parse signature help request: {e}")
            return
        
        # Get workbook_id from editor
        workbook_id = editor.workbook_id
        if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
            logger.debug("[IDE] Signature help request ignored: no workbook_id or welcome tab")
            return
        
        # Find the module name from the tab title
        module_name = None
        for i in range(self.editor_tabs.count()):
            if self.editor_tabs.widget(i) is editor:
                module_name = self.editor_tabs.tabText(i)
                break
        
        if not module_name:
            logger.debug("[IDE] Signature help request ignored: could not find module name")
            return
        
        # Strip .py extension if present
        module_name = _strip_py_extension(module_name)
        
        # Collect dirty files for cross-module resolution
        dirty_files = self._collect_dirty_files_sync(workbook_id)
        
        # Send signature help request to Business Layer
        message = json.dumps({
            "type": "signature_help_request",
            "workbook_id": workbook_id,
            "module_name": module_name,
            "code": request.get("code", ""),
            "line": request.get("line", 1),
            "column": request.get("column", 0),
            "request_id": request.get("request_id"),
            "dirty_files": dirty_files,
        })
        logger.debug(f"[IDE] Sending signature_help_request for module '{module_name}'")
        self.websocket.sendTextMessage(message)

    def _handle_hover_request(self, editor: MonacoEditor, request_json: str):
        """
        Handle hover request from a Monaco editor.
        
        Injects workbook_id, module_name, and dirty_files from the editor/tab
        into the request and forwards it to the Business Layer via WebSocket.
        
        Args:
            editor: The MonacoEditor instance that requested hover.
            request_json: JSON string containing the hover request from JavaScript.
        """
        try:
            request = json.loads(request_json)
        except json.JSONDecodeError as e:
            logger.warning(f"[IDE] Failed to parse hover request: {e}")
            return
        
        # Get workbook_id from editor
        workbook_id = editor.workbook_id
        if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
            logger.debug("[IDE] Hover request ignored: no workbook_id or welcome tab")
            return
        
        # Find the module name from the tab title
        module_name = None
        for i in range(self.editor_tabs.count()):
            if self.editor_tabs.widget(i) is editor:
                module_name = self.editor_tabs.tabText(i)
                break
        
        if not module_name:
            logger.debug("[IDE] Hover request ignored: could not find module name")
            return
        
        # Strip .py extension if present
        module_name = _strip_py_extension(module_name)
        
        # Collect dirty files for cross-module resolution
        dirty_files = self._collect_dirty_files_sync(workbook_id)
        
        # Send hover request to Business Layer
        message = json.dumps({
            "type": "hover_request",
            "workbook_id": workbook_id,
            "module_name": module_name,
            "code": request.get("code", ""),
            "line": request.get("line", 1),
            "column": request.get("column", 0),
            "request_id": request.get("request_id"),
            "dirty_files": dirty_files,
        })
        logger.debug(f"[IDE] Sending hover_request for module '{module_name}'")
        self.websocket.sendTextMessage(message)

    def _handle_diagnostic_request(self, editor: MonacoEditor, request_json: str):
        """
        Handle diagnostic request from a Monaco editor.
        
        Injects workbook_id and module_name from the editor/tab
        into the request and forwards it to the Business Layer via WebSocket.
        
        Args:
            editor: The MonacoEditor instance that requested diagnostics.
            request_json: JSON string containing the diagnostic request from JavaScript.
        """
        try:
            request = json.loads(request_json)
        except json.JSONDecodeError as e:
            logger.warning(f"[IDE] Failed to parse diagnostic request: {e}")
            return
        
        # Get workbook_id from editor
        workbook_id = editor.workbook_id
        if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
            logger.debug("[IDE] Diagnostic request ignored: no workbook_id or welcome tab")
            return
        
        # Find the module name from the tab title
        module_name = None
        for i in range(self.editor_tabs.count()):
            if self.editor_tabs.widget(i) is editor:
                module_name = self.editor_tabs.tabText(i)
                break
        
        if not module_name:
            logger.debug("[IDE] Diagnostic request ignored: could not find module name")
            return
        
        # Strip .py extension if present
        module_name = _strip_py_extension(module_name)
        
        # Send diagnostic request to Business Layer
        message = json.dumps({
            "type": "diagnostic_request",
            "workbook_id": workbook_id,
            "module_name": module_name,
            "code": request.get("code", ""),
            "request_id": request.get("request_id"),
        })
        logger.debug(f"[IDE] Sending diagnostic_request for module '{module_name}'")
        self.websocket.sendTextMessage(message)
    
    def _on_breakpoints_changed(self, editor: MonacoEditor, changes_json: str):
        """
        Handle breakpoint position changes from editor.
        
        Updates the breakpoint manager when line insertions/deletions cause
        breakpoint decorations to move.
        
        Args:
            editor: The MonacoEditor instance where breakpoints changed.
            changes_json: JSON string of {oldLine: newLine} mappings.
        """
        try:
            changes = json.loads(changes_json)
            workbook_id = editor.workbook_id
            
            if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
                return
            
            # Find the module name from the tab title
            module_name = None
            for i in range(self.editor_tabs.count()):
                if self.editor_tabs.widget(i) is editor:
                    module_name = self.editor_tabs.tabText(i)
                    break
            
            if not module_name:
                return
            
            # Strip .py extension if present
            module_name = _strip_py_extension(module_name)
            
            # Update breakpoint positions
            for old_line_str, new_line in changes.items():
                old_line = int(old_line_str)
                self.breakpoint_manager.move_breakpoint(workbook_id, module_name, old_line, new_line)
                logger.debug(f"[IDE] Breakpoint moved from line {old_line} to {new_line} in {module_name}")
        except Exception as e:
            logger.error(f"[IDE] Error updating breakpoint positions: {e}")

    def _on_new_module_requested(self, workbook_id: str):
        """
        Handle new module request from project explorer.
        
        Prompts the user for a module name and creates a new editor tab.
        Module names are stored WITHOUT the .py extension.
        
        Args:
            workbook_id: The workbook ID to associate with the new module.
        """
        module_name, ok = QInputDialog.getText(
            self,
            "New Module",
            "Enter module name (e.g., my_module):"
        )
        
        if ok and module_name:
            # Strip .py extension if user included it
            module_name = _strip_py_extension(module_name)
            
            # Validate module name is a valid Python identifier
            if not module_name.isidentifier():
                QMessageBox.warning(
                    self,
                    "Invalid Module Name",
                    f"'{module_name}' is not a valid Python module name.\n"
                    "Use only letters, numbers, and underscores (cannot start with a number)."
                )
                return
            
            # Create a new editor tab (use module_name without .py)
            editor = self.add_editor_tab(module_name, "", workbook_id)
            editor.focus_editor()

            # Add the module to the project explorer
            self.project_explorer.add_module(workbook_id, module_name)
            
            # Save empty module to Business Layer
            message = json.dumps({
                "type": "save_module",
                "workbook_id": workbook_id,
                "module_name": module_name,
                "code": "",
            })
            self.websocket.sendTextMessage(message)
            
            # Update local cache
            for cache in [self._module_cache, self.event_manager._module_cache,self.function_publisher._modules_cache]:
                if workbook_id not in cache:
                    cache[workbook_id] = {}
                cache[workbook_id][module_name] = ""
            
            self.log_to_console(f"Created new module: {module_name}", level=OutputLevel.DETAILED)

    def _on_open_module_requested(self, workbook_id: str, module_name: str):
        """
        Handle request to open a module from project explorer.
        
        Opens the module in a new editor tab. If the module is already open,
        switches to that tab. If not cached, fetches from the Business Layer.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name (without .py extension)
        """
        logger.debug(f"[IDE] _on_open_module_requested: workbook_id={workbook_id}, module_name={module_name}")
        
        # Check if already open in a tab
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if (tab_widget.workbook_id == workbook_id and 
                    self.editor_tabs.tabText(i) == module_name):
                    # Already open, switch to it
                    logger.debug(f"[IDE] Module '{module_name}' already open in tab {i}, switching to it")
                    self.editor_tabs.setCurrentIndex(i)
                    editor=self.editor_tabs.widget(i)
                    editor.focus_editor()
                    return
        
        # Check if we have it cached
        if workbook_id in self._module_cache and module_name in self._module_cache[workbook_id]:
            code = self._module_cache[workbook_id][module_name]
            logger.debug(f"[IDE] Module '{module_name}' found in cache, content_length={len(code) if code else 0}")
            editor = self.add_editor_tab(module_name, code, workbook_id)
            editor.focus_editor()
            return
        
        logger.debug(f"[IDE] Module '{module_name}' not in cache, requesting from Business Layer")
        # Request module content from Business Layer
        message = json.dumps({
            "type": "get_module",
            "workbook_id": workbook_id,
            "module_name": module_name,
        })
        self.websocket.sendTextMessage(message)
        self.log_to_console(f"Fetching module: {module_name}", level=OutputLevel.COMPLETE)

    def _on_delete_module_requested(self, workbook_id: str, module_name: str):
        """
        Handle request to delete a module from project explorer.
        
        Checks for dependencies (event handlers and published functions) and shows
        a detailed confirmation dialog if dependencies exist. If confirmed, unregisters
        events and removes function publications before deleting the module.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name (without .py extension)
        """
        # Check for dependencies
        events_using_module = self._get_events_using_module(workbook_id, module_name)
        published_functions = self._get_published_functions_from_module(workbook_id, module_name)
        
        # Build confirmation message
        if events_using_module or published_functions:
            message_parts = [
                f"Module '{module_name}' has the following dependencies:",
                ""
            ]
            
            if events_using_module:
                message_parts.append("Event Handlers:")
                for event_desc in events_using_module:
                    message_parts.append(f"  • {event_desc}")
                message_parts.append("")
            
            if published_functions:
                message_parts.append("Published Functions:")
                for func_desc in published_functions:
                    message_parts.append(f"  • {func_desc}")
                message_parts.append("")
            
            message_parts.append("Deleting this module will unregister all event handlers and remove all function publications.")
            message_parts.append("")
            message_parts.append("Are you sure you want to continue?")
            
            confirmation_message = "\n".join(message_parts)
            
            result = QMessageBox.question(
                self,
                "Delete Module with Dependencies",
                confirmation_message,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result != QMessageBox.StandardButton.Yes:
                return
            
            # Unregister events and remove function publications
            self._unregister_events_for_module(workbook_id, module_name)
            self._remove_function_publications_for_module(workbook_id, module_name)
        else:
            # No dependencies, simple confirmation
            result = QMessageBox.question(
                self,
                "Delete Module",
                f"Are you sure you want to delete '{module_name}'?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if result != QMessageBox.StandardButton.Yes:
                return
        
        # Request deletion from Business Layer
        message = json.dumps({
            "type": "delete_module",
            "workbook_id": workbook_id,
            "module_name": module_name,
        })
        self.websocket.sendTextMessage(message)
        
        # Close any open editor tabs for this module
        for i in range(self.editor_tabs.count() - 1, -1, -1):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if (tab_widget.workbook_id == workbook_id and 
                    self.editor_tabs.tabText(i) == module_name):
                    self.editor_tabs.removeTab(i)
        
        # Remove from local cache
        if workbook_id in self._module_cache and module_name in self._module_cache[workbook_id]:
            del self._module_cache[workbook_id][module_name]
        
        # Remove from synced hashes
        if workbook_id in self._synced_module_hashes and module_name in self._synced_module_hashes[workbook_id]:
            del self._synced_module_hashes[workbook_id][module_name]
        
        # Remove from project explorer
        self.project_explorer.remove_module(workbook_id, module_name)
        
        self.log_to_console(f"Deleted module: {module_name}", level=OutputLevel.DETAILED)
    
    def _get_events_using_module(self, workbook_id: str, module_name: str) -> List[str]:
        """
        Get a list of event descriptions that use handlers from the specified module.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
            
        Returns:
            List of event descriptions (e.g., "Sheet1.onSelectionChanged -> my_module.handler")
        """
        
        events = []
        event_config = self.event_manager.getHandlersByWorkbbokId().get(workbook_id, [])
        for handler_data in event_config:
            function_name=handler_data.get('python_function','')
            if function_name.startswith(f"{module_name}."):
                object_type=handler_data.get("object_type","Object")
                object_id=handler_data.get("object_id","")
                event_name=handler_data.get("event_name","")
                events.append(f"{object_type}[{object_id}].{event_name} -> {function_name}")

        
        return events


    
    def _get_published_functions_from_module(self, workbook_id: str, module_name: str) -> List[str]:
        """
        Get a list of published function descriptions from the specified module.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
            
        Returns:
            List of function descriptions (e.g., "my_module.my_func -> MY_FUNC")
        """
        functions = []
        
        if workbook_id in self.function_publisher._publications:
            publications = self.function_publisher._publications[workbook_id]
            for pub_tuple in publications:
                # Handle both old format (2 items) and new format (4 items)
                if len(pub_tuple) == 2:
                    python_func, excel_name = pub_tuple
                elif len(pub_tuple) == 4:
                    python_func, excel_name, _, _ = pub_tuple
                else:
                    # Unexpected format, skip
                    logger.warning(f"Unexpected publication tuple length: {len(pub_tuple)}")
                    continue
                
                if python_func.startswith(f"{module_name}."):
                    functions.append(f"{python_func} -> {excel_name}")
        
        return functions
    
    def _unregister_events_for_module(self, workbook_id: str, module_name: str):
        """
        Unregister all event handlers from the specified module.
        
        Sends unregister_module_handlers message to the Business Layer to remove
        all event registrations for handlers in the module.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
        """

        events_to_delete = []
        event_config = self.event_manager.getHandlersByWorkbbokId().get(workbook_id, [])
        for handler_data in event_config:
            function_name=handler_data.get('python_function','')
            if function_name.startswith(f"{module_name}."):
                events_to_delete.append(handler_data)
        

        if not events_to_delete:
            logger.debug(f"[IDE] No events to events_to_delete for module rename: {module_name}")
            return
        
    
        for event_info in events_to_delete:
            self.event_manager._on_clear_handler(workbook_id, 
                                        event_info["object_id"],
                                        event_info["object_name"],
                                        event_info["object_type"],
                                        event_info["event_name"],
                                    )

        self.log_to_console(f"Unregistered event handlers from module: {module_name}", level=OutputLevel.SIMPLE)
    
    def _remove_function_publications_for_module(self, workbook_id: str, module_name: str):
        """
        Remove all function publications from the specified module.
        
        Updates the FunctionPublisher's internal state and syncs with the server.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
        """
        if workbook_id in self.function_publisher._publications:
            publications = self.function_publisher._publications[workbook_id]
            
            # Filter out publications from this module
            updated_publications = []
            for pub_tuple in publications:
                # All valid tuples should have at least 2 items (python_func, excel_name)
                # but we'll be defensive and handle edge cases
                if len(pub_tuple) >= 2:
                    python_func = pub_tuple[0]
                    if not python_func.startswith(f"{module_name}."):
                        updated_publications.append(pub_tuple)
                else:
                    logger.warning(f"Skipping invalid publication tuple: {pub_tuple}")
            
            # Update the publications list
            self.function_publisher._publications[workbook_id] = updated_publications
            
            # Refresh the table if this is the current workbook
            if self.function_publisher.get_current_workbook() == workbook_id:
                self.function_publisher._refresh_publications_table(workbook_id)
            
            # Sync with server
            self.function_publisher._sync_publications(workbook_id)
        
        self.log_to_console(f"Removed function publications from module: {module_name}", level=OutputLevel.SIMPLE)
    
    def _on_rename_module_requested(self, workbook_id: str, old_name: str, new_name: str):
        """
        Handle request to rename a module.
        
        Renames the module by:
        1. Updating event registrations via Business Layer message
        2. Updating function publications locally
        3. Renaming editor tab if open
        4. Updating caches
        5. Deleting old module and saving new module to Business Layer
        6. Updating project explorer
        
        Args:
            workbook_id: The workbook ID
            old_name: The old module name (without .py extension)
            new_name: The new module name (without .py extension)
        """
        # Check if new module name already exists
        if workbook_id in self._module_cache:
            if new_name in self._module_cache[workbook_id]:
                QMessageBox.warning(
                    self,
                    "Module Exists",
                    f"A module named '{new_name}' already exists in this workbook."
                )
                return
        
        # Get the module code
        if workbook_id not in self._module_cache or old_name not in self._module_cache[workbook_id]:
            QMessageBox.warning(
                self,
                "Module Not Found",
                f"Module '{old_name}' not found."
            )
            return
        
        module_code = self._module_cache[workbook_id][old_name]
        
        # Update event registrations via Business Layer
        self._update_event_registrations_for_module_rename(workbook_id, old_name, new_name)
        
        # Update function publications
        self._update_function_publications_for_module_rename(workbook_id, old_name, new_name)
        
        # Rename editor tab if open
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if (tab_widget.workbook_id == workbook_id and 
                    self.editor_tabs.tabText(i) == old_name):
                    self.editor_tabs.setTabText(i, new_name)
                    break
        
        # Update caches
        if workbook_id in self._module_cache:
            self._module_cache[workbook_id][new_name] = module_code
            del self._module_cache[workbook_id][old_name]
        
        if workbook_id in self._synced_module_hashes:
            if old_name in self._synced_module_hashes[workbook_id]:
                old_hash = self._synced_module_hashes[workbook_id][old_name]
                self._synced_module_hashes[workbook_id][new_name] = old_hash
                del self._synced_module_hashes[workbook_id][old_name]
        
        # Delete old module and save new module to Business Layer
        delete_message = json.dumps({
            "type": "delete_module",
            "workbook_id": workbook_id,
            "module_name": old_name,
        })
        self.websocket.sendTextMessage(delete_message)
        
        save_message = json.dumps({
            "type": "save_module",
            "workbook_id": workbook_id,
            "module_name": new_name,
            "code": module_code,
        })
        self.websocket.sendTextMessage(save_message)
        
        # Update project explorer
        self.project_explorer.remove_module(workbook_id, old_name)
        self.project_explorer.add_module(workbook_id, new_name)
        
        self.log_to_console(f"Renamed module: {old_name} -> {new_name}", level=OutputLevel.DETAILED)
    
    def _update_event_registrations_for_module_rename(self, workbook_id: str, old_name: str, new_name: str):
        """
        Update event registrations when a module is renamed.
        
        Unregisters all event handlers using the old module name and re-registers
        them with the new module name.
        
        Args:
            workbook_id: The workbook ID
            old_name: The old module name
            new_name: The new module name
        """
        # Get events using the old module name
        events_to_update = []
        event_config = self.event_manager.getHandlersByWorkbbokId().get(workbook_id, [])
        for handler_data in event_config:
            function_name=handler_data.get('python_function','')
            if function_name.startswith(f"{old_name}."):
                events_to_update.append(handler_data)
        

        if not events_to_update:
            logger.debug(f"[IDE] No events to update for module rename: {old_name} -> {new_name}")
            return
        
    
        for event_info in events_to_update:
            #self.event_manager._on_clear_handler(workbook_id, 
            #                        event_info["object_id"],
            #                        event_info["object_name"],
            #                        event_info["object_type"],
            #                        event_info["event_name"],
            #                        )

            func_name = event_info["python_function"]
            new_func_name= f"{new_name}.{func_name.split('.', 1)[1]}"

            self._on_assign_handler_requested(workbook_id,
                                              event_info["object_id"],
                                              event_info["object_type"],
                                              event_info["event_name"],
                                              new_func_name,)
        
        self.log_to_console(
            f"Updated {len(events_to_update)} event handler(s) for module rename: {old_name} -> {new_name}",
            level=OutputLevel.SIMPLE
        )
    
    def _update_function_publications_for_module_rename(self, workbook_id: str, old_name: str, new_name: str):
        """
        Update function publications when a module is renamed.
        
        Updates the FunctionPublisher's internal state to use the new module name
        for all published functions from the renamed module.
        
        Args:
            workbook_id: The workbook ID
            old_name: The old module name
            new_name: The new module name
        """
        if workbook_id in self.function_publisher._publications:
            publications = self.function_publisher._publications[workbook_id]
            updated_publications = []
            
            for pub_tuple in publications:
                # Handle both old format (2 items) and new format (4 items)
                if len(pub_tuple) == 2:
                    python_func, excel_name = pub_tuple
                    dimension = DEFAULT_DIMENSION
                    streaming = DEFAULT_STREAMING
                else:
                    python_func, excel_name, dimension, streaming = pub_tuple
                
                # Check if this function is from the renamed module
                if python_func.startswith(f"{old_name}."):
                    func_name = python_func.split(".", 1)[1]
                    new_python_func = f"{new_name}.{func_name}"
                    updated_publications.append((new_python_func, excel_name, dimension, streaming))
                else:
                    updated_publications.append(pub_tuple)
            
            # Update the publications list
            self.function_publisher._publications[workbook_id] = updated_publications
            
            # Refresh the table if this is the current workbook
            if self.function_publisher.get_current_workbook() == workbook_id:
                self.function_publisher._refresh_publications_table(workbook_id)
            
            # Sync with server
            self.function_publisher._sync_publications(workbook_id)
    
    def _on_sync_published_functions(self, workbook_id: str, functions_list: list):
        """
        Handle sync_published_functions signal from FunctionPublisher.
        
        Sends update_published_functions message to the Business Layer server.
        
        Args:
            workbook_id: The workbook identifier
            functions_list: List of dicts with 'python_function' and 'excel_name' keys
        """
        message = json.dumps({
            "type": "update_published_functions",
            "workbook_id": workbook_id,
            "functions": functions_list,
        })
        self.websocket.sendTextMessage(message)

    def set_websocket_client(self, client):
        """
        Set the WebSocket client reference.
        
        Args:
            client: WebSocketClient instance
        """
        self.websocket_client = client
        # For backwards compatibility
        self.websocket = client
    
        
    def apply_startup_settings(self):
        """
        Apply all startup settings before window is shown.
        """

        request_id = f"initial_settings_{id(self)}"
        message = {
            "type": "get_all_settings",
            "request_id": request_id,
            "initial": True  # Mark as initial settings request
        }
        self.websocket.send_and_wait_response(message, lambda msg:self._apply_initial_settings(msg.get("settings", {})))
        
    
    def _apply_initial_theme(self):
        """Apply initial theme from cached settings or defaults."""
        # Theme is already applied in __init__, this is a placeholder for future enhancements
        pass
    
    def _apply_initial_editor_settings(self):
        """Apply initial editor settings."""
        # Editor settings are applied when editors are created, this is a placeholder
        pass
    
    def _apply_initial_view_settings(self):
        """Apply initial view settings."""
        # View settings are handled by dock widgets, this is a placeholder
        pass

    def _handle_pip_output(self, data: dict):
        """Handle pip output messages from the Business Layer."""
        output_type = data.get("output_type", "")
        content = data.get("content", "")
        message = data.get("message", "")  # Legacy format support
        workbook_id = data.get("workbook_id", "")
        
        # Use content if available, otherwise fall back to message
        text = content if content else message
        if not text:
            return
        
        # Format and color based on output_type
        if output_type == "error":
            # Red for errors - don't add extra ✗ if already present
            if not text.startswith("✗") and not text.startswith("ERROR"):
                text = f"✗ {text}"
            self.package_manager.log_pip_output_colored(text, "#E74C3C")  # Red
            self.log_to_console(f"Package installation error: {text}", level=OutputLevel.DETAILED)
            # Show error light
            self._show_error_light()
        elif output_type == "success":
            # Green for success - don't add extra ✓ if already present
            if not text.startswith("✓"):
                text = f"✓ {text}"
            self.package_manager.log_pip_output_colored(text, "#2ECC71")  # Green
            self.log_to_console(f"Package installed for {workbook_id}: {text}", level=OutputLevel.DETAILED)
        elif output_type == "cached":
            # Green for cached
            if not text.startswith("✓"):
                text = f"✓ Using cached: {text}"
            self.package_manager.log_pip_output_colored(text, "#2ECC71")  # Green
        elif output_type == "stderr":
            # Orange/amber for stderr warnings
            self.package_manager.log_pip_output_colored(text, "#E67E22")  # Amber
        else:
            # Default gray for stdout and other
            self.package_manager.log_pip_output(text)

    def _handle_completion_response(self, data: dict):
        """
        Handle completion response from the Business Layer.
        
        Routes the completion response to the correct MonacoEditor tab
        based on workbook_id and module_name.
        
        Args:
            data: The completion response data containing:
                - workbook_id: The workbook identifier
                - module_name: The module name
                - completions: List of completion items
                - error: Optional error message
                - request_id: The original request ID for correlation
        """
        workbook_id = data.get("workbook_id")
        module_name = data.get("module_name")
        
        if not workbook_id:
            logger.debug("[IDE] Completion response missing workbook_id")
            return
        
        if module_name is None:
            logger.warning("[IDE] Completion response missing module_name, using first matching editor for workbook")
        
        # Find the corresponding editor tab
        target_editor = None
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if tab_widget.workbook_id == workbook_id:
                    tab_title = self.editor_tabs.tabText(i)
                    tab_module_name = _strip_py_extension(tab_title)
                    # If module_name is specified, match it; otherwise use first matching workbook
                    if module_name is None or tab_module_name == module_name:
                        target_editor = tab_widget
                        break
        
        if target_editor:
            # Send the completion response to the editor
            response = {
                "completions": data.get("completions", []),
                "error": data.get("error"),
                "request_id": data.get("request_id"),
            }
            logger.debug(f"[IDE] Sending completion response to editor: {len(response['completions'])} items")
            target_editor.send_completion_response(response)
        else:
            logger.debug(f"[IDE] Could not find editor for completion response: workbook={workbook_id}, module={module_name}")

    def _handle_signature_help_response(self, data: dict):
        """
        Handle signature help response from the Business Layer.
        
        Routes the signature help response to the correct MonacoEditor tab
        based on workbook_id and module_name.
        
        Args:
            data: The signature help response data containing:
                - workbook_id: The workbook identifier
                - module_name: The module name
                - signatures: List of signature information
                - activeSignature: Index of the active signature
                - activeParameter: Index of the active parameter
                - error: Optional error message
                - request_id: The original request ID for correlation
        """
        workbook_id = data.get("workbook_id")
        module_name = data.get("module_name")
        
        if not workbook_id:
            logger.debug("[IDE] Signature help response missing workbook_id")
            return
        
        # Find the corresponding editor tab
        target_editor = None
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if tab_widget.workbook_id == workbook_id:
                    tab_title = self.editor_tabs.tabText(i)
                    tab_module_name = _strip_py_extension(tab_title)
                    if module_name is None or tab_module_name == module_name:
                        target_editor = tab_widget
                        break
        
        if target_editor:
            response = {
                "signatures": data.get("signatures", []),
                "activeSignature": data.get("activeSignature", 0),
                "activeParameter": data.get("activeParameter", 0),
                "error": data.get("error"),
                "request_id": data.get("request_id"),
            }
            logger.debug(f"[IDE] Sending signature help response to editor: {len(response['signatures'])} signatures")
            target_editor.send_signature_help_response(response)
        else:
            logger.debug(f"[IDE] Could not find editor for signature help response: workbook={workbook_id}, module={module_name}")

    def _handle_hover_response(self, data: dict):
        """
        Handle hover response from the Business Layer.
        
        Routes the hover response to the correct MonacoEditor tab
        based on workbook_id and module_name.
        
        Args:
            data: The hover response data containing:
                - workbook_id: The workbook identifier
                - module_name: The module name
                - contents: Hover content as markdown or plain text
                - error: Optional error message
                - request_id: The original request ID for correlation
        """
        workbook_id = data.get("workbook_id")
        module_name = data.get("module_name")
        
        if not workbook_id:
            logger.debug("[IDE] Hover response missing workbook_id")
            return
        
        # Find the corresponding editor tab
        target_editor = None
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if tab_widget.workbook_id == workbook_id:
                    tab_title = self.editor_tabs.tabText(i)
                    tab_module_name = _strip_py_extension(tab_title)
                    if module_name is None or tab_module_name == module_name:
                        target_editor = tab_widget
                        break
        
        if target_editor:
            response = {
                "contents": data.get("contents"),
                "error": data.get("error"),
                "request_id": data.get("request_id"),
            }
            logger.debug(f"[IDE] Sending hover response to editor: has_contents={response['contents'] is not None}")
            target_editor.send_hover_response(response)
        else:
            logger.debug(f"[IDE] Could not find editor for hover response: workbook={workbook_id}, module={module_name}")

    def _handle_diagnostic_response(self, data: dict):
        """
        Handle diagnostic response from the Business Layer.
        
        Routes the diagnostic response to the correct MonacoEditor tab
        based on workbook_id and module_name.
        
        Args:
            data: The diagnostic response data containing:
                - workbook_id: The workbook identifier
                - module_name: The module name
                - diagnostics: List of diagnostic objects
                - error: Optional error message
                - request_id: The original request ID for correlation
        """
        workbook_id = data.get("workbook_id")
        module_name = data.get("module_name")
        
        if not workbook_id:
            logger.debug("[IDE] Diagnostic response missing workbook_id")
            return
        
        # Find the corresponding editor tab
        target_editor = None
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if tab_widget.workbook_id == workbook_id:
                    tab_title = self.editor_tabs.tabText(i)
                    tab_module_name = _strip_py_extension(tab_title)
                    if module_name is None or tab_module_name == module_name:
                        target_editor = tab_widget
                        break
        
        if target_editor:
            response = {
                "diagnostics": data.get("diagnostics", []),
                "error": data.get("error"),
                "request_id": data.get("request_id"),
            }
            logger.debug(f"[IDE] Sending diagnostic response to editor: {len(response['diagnostics'])} diagnostics")
            target_editor.send_diagnostic_response(response)
        else:
            logger.debug(f"[IDE] Could not find editor for diagnostic response: workbook={workbook_id}, module={module_name}")

    def _on_package_install_requested(self, workbook_id: str, package_name: str):
        """
        Handle package installation request from the PackageManager widget.
        
        Sends a package_install_request message to the Business Layer.
        """
        if not workbook_id or not package_name:
            self.log_to_console("Cannot install package: workbook or package name missing", level=OutputLevel.DETAILED)
            return
        
        # Clear previous pip output
        self.package_manager.clear_pip_output()
        self.package_manager.log_pip_output(f"Installing {package_name}...")
        
        # Send package install request to Business Layer
        message = json.dumps({
            "type": "package_install_request",
            "workbook_id": workbook_id,
            "package": package_name,
        })
        logger.info(f"[IDE] Sending package_install_request: {package_name} for {workbook_id}")
        self.websocket.sendTextMessage(message)
        logger.debug("[IDE] Package install message sent via WebSocket")
        self.log_to_console(f"Requested installation of {package_name} for {workbook_id}", level=OutputLevel.DETAILED)

    def _on_get_versions_requested(self, package_name: str):
        """
        Handle package versions query request from the PackageManager widget.
        
        Sends a get_package_versions_request message to the Business Layer.
        """
        if not package_name:
            return
        
        # Generate a unique request ID
        request_id = f"versions_{package_name}_{id(self)}"
        
        # Send request to Business Layer
        message = json.dumps({
            "type": "get_package_versions_request",
            "package_name": package_name,
            "request_id": request_id,
        })
        logger.info(f"[IDE] Requesting versions for package: {package_name}")
        self.websocket.sendTextMessage(message)

    def _on_get_extras_requested(self, package_name: str, version: str):
        """
        Handle package extras query request from the PackageManager widget.
        
        Sends a get_package_extras_request message to the Business Layer.
        """
        if not package_name:
            return
        
        # Generate a unique request ID
        request_id = f"extras_{package_name}_{version}_{id(self)}"
        
        # Send request to Business Layer
        message = json.dumps({
            "type": "get_package_extras_request",
            "package_name": package_name,
            "version": version,
            "request_id": request_id,
        })
        logger.info(f"[IDE] Requesting extras for package: {package_name} {version}")
        self.websocket.sendTextMessage(message)

    def _on_search_package_requested(self, package_name: str):
        """
        Handle package search request from the PackageManager widget.
        
        Sends a get_package_info_request message to the Business Layer.
        """
        if not package_name:
            return
        
        # Generate a unique request ID
        request_id = f"info_{package_name}_{id(self)}"
        
        # Send request to Business Layer
        message = json.dumps({
            "type": "get_package_info_request",
            "package_name": package_name,
            "request_id": request_id,
        })
        logger.info(f"[IDE] Searching for package: {package_name}")
        self.websocket.sendTextMessage(message)

    def _send_message(self, objMessage:List | Dict):
        textMessage=json.dumps(objMessage)
        self.websocket.sendTextMessage(textMessage)
    
    def _on_add_package_requested(
        self, workbook_id: str, package_name: str, version: str, extras: list
    ):
        """
        Handle add package request from the PackageManager widget.
        
        Sends add_workbook_package message to the Business Layer.
        """
        if not workbook_id or not package_name or not version:
            return
        
        message = {
            "type": "add_workbook_package",
            "workbook_id": workbook_id,
            "package_name": package_name,
            "version": version,
            "extras": extras if extras else []
        }
        self._send_message(message)
        self.package_manager.log_pip_output(
            f"Added {package_name}=={version} with extras: {extras if extras else 'none'}"
        )

    def _on_remove_package_requested(self, workbook_id: str, package_name: str):
        """
        Handle remove package request from the PackageManager widget.
        
        Sends remove_workbook_package message to the Business Layer.
        """
        if not workbook_id or not package_name:
            return
        
        message = {
            "type": "remove_workbook_package",
            "workbook_id": workbook_id,
            "package_name": package_name
        }
        self._send_message(message)
        self.package_manager.log_pip_output(f"Removed {package_name}")
    
    def _on_update_package_requested(
        self, workbook_id: str, package_name: str, version: str, extras: list
    ):
        """
        Handle update package request from the PackageManager widget.
        
        Sends update_workbook_package message to the Business Layer.
        """
        if not workbook_id or not package_name or not version:
            return
        
        message = {
            "type": "update_workbook_package",
            "workbook_id": workbook_id,
            "package_name": package_name,
            "version": version,
            "extras": extras if extras else []
        }
        self._send_message(message)
        self.package_manager.log_pip_output(
            f"Updated {package_name}=={version} with extras: {extras if extras else 'none'}"
        )
    
    def _on_get_workbook_packages_requested(self, workbook_id: str):
        """
        Handle get workbook packages request from PackageManager.
        
        Sends get_workbook_packages message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = {
            "type": "get_workbook_packages",
            "workbook_id": workbook_id
        }
        self._send_message(message)
    
    def _on_restore_requested(self, workbook_id: str):
        """
        Handle restore request from PackageManager.
        
        Sends restore_workbook_packages message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = {
            "type": "restore_workbook_packages",
            "workbook_id": workbook_id
        }
        self._send_message(message)
    
    def _on_see_resolution_requested(self, workbook_id: str):
        """
        Handle see resolution request from PackageManager.
        
        Sends get_resolved_deps message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = {
            "type": "get_resolved_deps",
            "workbook_id": workbook_id
        }
        self._send_message(message)
    
    def _on_update_package_status_requested(self, workbook_id: str, package_name: str, status: str):
        """
        Handle update package status request from PackageManager.
        
        Sends update_package_status message to the Business Layer.
        """
        if not workbook_id or not package_name or not status:
            return
        
        message = {
            "type": "update_package_status",
            "workbook_id": workbook_id,
            "package_name": package_name,
            "status": status
        }
        self._send_message(message)
    
    def _on_update_python_paths_requested(self, workbook_id: str, python_paths: list):
        """
        Handle update python paths request from PackageManager.
        
        Sends update_python_paths message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = {
            "type": "update_python_paths",
            "workbook_id": workbook_id,
            "python_paths": python_paths
        }
        self._send_message(message)
        logger.debug(f"[IDE] Sent update_python_paths with {len(python_paths)} paths")
    
    def _handle_package_paths_updated(self, data: dict):
        """
        Handle package paths update from server.
        
        This is called when packages are installed/removed and paths change.
        In the current architecture, LSP runs in the Python kernel, so this
        message is primarily for logging. In the future, if LSP moves to IDE,
        this would update the IDE's LSP client.
        
        Args:
            data: Message data containing workbook_id, paths, and old_paths
        """
        workbook_id = data.get("workbook_id")
        paths = data.get("paths", [])
        old_paths = data.get("old_paths", [])
        
        # Log the update
        if paths:
            self.log_to_console(f"Package paths updated: {len(paths)} active path(s)", level=OutputLevel.DETAILED)
        
        # Note: In the current architecture, LSPBridge runs in the Python kernel
        # and is updated automatically when sys.path changes in the kernel.
        # If LSP were to move to the IDE in the future, we would update it here:
        # if self.lsp_client:
        #     self._update_lsp_paths(old_paths, paths)

    def _handle_package_versions_response(self, data: dict):
        """
        Handle package versions response from the Business Layer.
        
        Forwards the versions to the PackageManager widget.
        """
        package_name = data.get("package_name", "")
        versions = data.get("versions", [])
        error = data.get("error")
        
        if error:
            self.package_manager.log_pip_output_colored(f"Error fetching versions for {package_name}: {error}","#E74C3C")
            self.package_manager.set_available_versions(package_name, [])
        else:
            self.package_manager.set_available_versions(package_name, versions)

    def _handle_package_extras_response(self, data: dict):
        """
        Handle package extras response from the Business Layer.
        
        Forwards the extras to the PackageManager widget.
        """
        package_name = data.get("package_name", "")
        version = data.get("version", "")
        extras = data.get("extras", [])
        error = data.get("error")
        
        if error:
            self.package_manager.log_pip_output_colored(f"Error fetching extras for {package_name}: {error}","#E74C3C")
            self.package_manager.set_available_extras(package_name, version, [])
        else:
            self.package_manager.set_available_extras(package_name, version, extras)

    def _handle_package_info_response(self, data: dict):
        """
        Handle package info response from the Business Layer.
        
        Forwards the info to the PackageManager widget.
        """
        package_name = data.get("package_name", "")
        info = {}
        
        if "error" in data:
            info["error"] = data["error"]
        else:
            info["name"] = data.get("name", package_name)
            info["latest_version"] = data.get("latest_version", "")
            info["summary"] = data.get("summary", "")
        
        self.package_manager.set_package_info(package_name, info)
    
    def _on_install_all_requested(self, workbook_id: str):
        """
        Handle install all packages request from PackageManager.
        
        Sends install_workbook_packages message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = {
            "type": "install_workbook_packages",
            "workbook_id": workbook_id
        }
        self._send_message(message)
        self.package_manager.log_pip_output(f"Installing all packages for workbook {workbook_id}...")
    
    def _on_reorder_requested(self, workbook_id: str, package_names: list):
        """
        Handle package reorder request from PackageManager.
        
        Sends reorder_workbook_packages message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = {
            "type": "reorder_workbook_packages",
            "workbook_id": workbook_id,
            "package_names": package_names
        }
        self._send_message(message)

    # ========== Event Manager Handlers ==========

    def _on_refresh_state_requested(self, workbook_id: str):
        """
        Handle refresh state request from EventManager.
        
        Sends a refresh_event_manager_state message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = json.dumps({
            "type": "refresh_event_manager_state",
            "workbook_id": workbook_id,
        })
        logger.debug(f"[IDE] Sending refresh_event_manager_state for workbook: {workbook_id}")
        self.websocket.sendTextMessage(message)

    def _on_object_registry_refresh_requested(self, workbook_id: str):
        """
        Handle object registry refresh request from ObjectInspector.
        
        Sends a get_object_registry message to the Business Layer.
        """
        if not workbook_id:
            return
        
        message = json.dumps({
            "type": "get_object_registry",
            "workbook_id": workbook_id,
        })
        logger.debug(f"[IDE] Sending get_object_registry for workbook: {workbook_id}")
        self.websocket.sendTextMessage(message)

    def _on_assign_handler_requested(
        self, workbook_id: str, object_id: str, object_type: str, event_name: str, function_name: str
    ):
        """
        Handle assign handler request from EventManager.
        
        Sends register_handler or unregister_handler message to Business Layer
        instead of directly saving event config.
        
        Args:
            workbook_id: The workbook identifier
            object_id: The Excel object ID (e.g., sheet ID, table ID)
            object_type: The Excel object type (e.g., "Worksheet", "Table")
            event_name: The event name (e.g., "onSelectionChanged")
            function_name: The Python function to assign (e.g., "my_module.on_change")
                          Empty string to clear the handler.
        """
        if not workbook_id or not object_id or not event_name:
            return
        
        if function_name:
            # Parse function_name to extract module_name and function_name
            parts = function_name.rsplit(".", 1)
            if len(parts) == 2:
                module_name, func_name = parts
            else:
                logger.error(f"[IDE] Invalid function_name format (expected 'module.function'): {function_name}")
                self.log_to_console(f"Error: Invalid function format. Expected 'module.function', got '{function_name}'", level=OutputLevel.COMPLETE)
                return
            
            # Register handler via Business Layer with split fields
            message = json.dumps({
                "type": "register_handler",
                "workbook_id": workbook_id,
                "object_id": object_id,
                "object_type": object_type,
                "event_name": event_name,
                "module_name": module_name,
                "function_name": func_name,
            })
            logger.debug(f"[IDE] Sending register_handler: {object_type}[{object_id}].{event_name} -> {module_name}.{func_name}")
            self.log_to_console(
                f"Registering handler: {object_type}[{object_id}].{event_name} -> {module_name}.{func_name}", 
                level=OutputLevel.DETAILED
            )
        else:
            # Unregister handler via Business Layer
            message = json.dumps({
                "type": "unregister_handler",
                "workbook_id": workbook_id,
                "object_id": object_id,
                "event_name": event_name,
            })
            logger.debug(f"[IDE] Sending unregister_handler: {object_id}.{event_name}")
            self.log_to_console(f"Unregistering handler: {object_id}.{event_name}", level=OutputLevel.DETAILED)
        
        self.websocket.sendTextMessage(message)

    def _on_create_handler_requested(
        self, workbook_id: str, object_id: str, object_name: str, object_type: str, event_name: str, function_name: str, arg_type: str
    ):
        """
        Handle create new handler request from EventManager.
        
        Creates a new Python handler function by:
        1. Creating/updating excel_events.py with the handler scaffold
        2. Initializing with import xpycode if module doesn't exist
        3. Focusing existing tab if already open
        4. Assigning the handler to the event
        
        Args:
            workbook_id: The workbook identifier
            object_id: The Excel object ID (e.g., sheet ID, table ID)
            object_type: The Excel object type (e.g., "Worksheet")
            event_name: The event name (e.g., "onSelectionChanged")
            function_name: The function name to create (e.g., "on_sheet1_change")
            arg_type: Event argument type (e.g., "xpycode.Excel.WorksheetSelectionChangedEventArgs")
        """
        if not workbook_id or not object_id or not event_name or not function_name:
            return
        
        # Always use excel_events.py as the target module
        module_name = "excel_events"
        
        # Generate handler scaffold code with type hints
        # object_id is passed as object_identifier to be used in docs/comments
        handler_code = self._generate_handler_scaffold(
            function_name, object_name, object_type, event_name, arg_type
        )
        
        # Check if module already exists in cache
        existing_code = self._module_cache.get(workbook_id, {}).get(module_name, "")
        if existing_code:
            # Append the handler to existing module
            final_code = existing_code.rstrip() + "\n\n\n" + handler_code
        else:
            # Create new module with import xpycode
            final_code = "import xpycode\n\n\n" + handler_code
        
        # Update local cache
        if workbook_id not in self._module_cache:
            self._module_cache[workbook_id] = {}
        self._module_cache[workbook_id][module_name] = final_code
        
        # Update EventManager module cache
        self.event_manager.set_module_cache(workbook_id, self._module_cache.get(workbook_id, {}))
        #self.function_publisher.set_modules_cache(workbook_id, self._module_cache.get(workbook_id, {}))
        
        # Save the module to Business Layer
        save_message = json.dumps({
            "type": "save_module",
            "workbook_id": workbook_id,
            "module_name": module_name,
            "code": final_code,
        })
        self.websocket.sendTextMessage(save_message)
        
        # Add to project explorer if not already there
        self.project_explorer.add_module(workbook_id, module_name)
        
        # Check if excel_events.py is already open in an editor tab
        tab_found = False
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                if (tab_widget.workbook_id == workbook_id and 
                    self.editor_tabs.tabText(i) == module_name):
                    # Tab is already open, focus it and update content
                    self.editor_tabs.setCurrentIndex(i)
                    tab_widget.set_text(final_code)
                    tab_found = True
                    break
        
        if not tab_found:
            # Open the module in a new editor tab
            self.add_editor_tab(module_name, final_code, workbook_id)
        
        # Now assign the handler
        qualified_name = f"{module_name}.{function_name}"
        self._on_assign_handler_requested(
            workbook_id, object_id, object_type, event_name, qualified_name
        )
        
        self.log_to_console(f"Created handler: {qualified_name}", level=OutputLevel.DETAILED)

    def _get_tab_string(self) -> str:
        """Get the tab string based on IDE settings."""
        use_spaces = self._editor_insert_spaces
        tab_size = self._editor_tab_size
        return " " * tab_size if use_spaces else "\t"

    
    def _generate_handler_scaffold(
        self, function_name: str, object_identifier: str, object_type: str, event_name: str, arg_type: str = "dict"
    ) -> str:
        """
        Generate scaffold code for a new event handler with type hints.
        
        Args:
            function_name: The function name
            object_identifier: The Excel object ID or name for display
            object_type: The Excel object type (e.g., "Worksheet", "Table", "Chart")
            event_name: The event name (e.g., "onSelectionChanged")
            arg_type: Event argument type (e.g., "xpycode.Excel.WorksheetSelectionChangedEventArgs")
            
        Returns:
            The scaffold Python code with type hints
        """
        # Generate appropriate parameter based on event name

        tab_string=self._get_tab_string()        
        
        param_doc = f"{tab_string}Args:\n{tab_string}{tab_string}event_args: Event arguments"
        
        code = f'''def {function_name}(event_args: {arg_type}):
{tab_string}"""
{tab_string}Handler for {object_type}[{object_identifier}].{event_name} event.
{tab_string}
{param_doc}
{tab_string}"""
{tab_string}# TODO: Implement your handler logic here
{tab_string}print("Event {event_name} fired on {object_type}[{object_identifier}]")
{tab_string}print(f"Event args: {{event_args}}")
'''
        return code

    def _handle_save_event_config_response(self, data: dict):
        """
        Handle save_event_config_response from Business Layer.
        
        Args:
            data: Response data containing:
                - success: Whether the save was successful
                - error: Optional error message
        """
        success = data.get("success", False)
        
        if success:
            logger.debug("[IDE] Event config saved successfully")
        else:
            error = data.get("error", "Unknown error")
            logger.warning(f"[IDE] save_event_config_response failed: {error}")
            self.log_to_console(f"Failed to save event config: {error}", "#ff6b6b", level=OutputLevel.SIMPLE)

    def _handle_validate_handler_response(self, data: dict):
        """
        Handle validate_handler_response from Business Layer.
        
        Updates the EventManager with handler validation status.
        
        Args:
            data: Response data containing:
                - workbook_id: The workbook identifier
                - object_name: The Excel object name
                - event_type: The event type
                - is_valid: Whether the handler function is valid
                - error: Optional error message if invalid
        """
        workbook_id = data.get("workbook_id")
        object_name = data.get("object_name")
        event_type = data.get("event_type")
        is_valid = data.get("is_valid", True)
        
        if not workbook_id or not object_name or not event_type:
            logger.warning("[IDE] validate_handler_response missing required fields")
            return
        
        logger.debug(
            f"[IDE] Handler validation: {object_name}.{event_type} = {is_valid}"
        )
        
        # Update the Event Manager with validation status
        self.event_manager.update_validation(
            workbook_id, object_name, event_type, is_valid
        )
    
    # Debug methods
    
    def _debug_code(self):
        """Start debugging the current code (Shift+F5)."""
        # Simply call _run_code with debug=True
        self._run_code(debug=True)
    
    def _run_code_internal(self, debug: bool = False):
        """
        Internal method to run code with optional debug mode.
        
        This is a refactored version of _run_code that supports both
        normal execution and debugging.
        """
        # This would be a refactored version of _run_code
        # For now, we'll keep the existing _run_code and add debug support there
        # by passing debug parameter through the run_module message
        pass
    
    def _debug_continue(self):
        """Continue execution from debug pause."""
        if not self._debug_active or not self._current_debug_workbook:
            return
        
        message = json.dumps({
            "type": "debug_continue",
            "workbook_id": self._current_debug_workbook,
        })
        self.websocket.sendTextMessage(message)
        logger.info("[IDE] Sent debug_continue")
    
    def _debug_step_over(self):
        """Step over to next line (F10)."""
        if not self._debug_active or not self._current_debug_workbook:
            return
        
        message = json.dumps({
            "type": "debug_step_over",
            "workbook_id": self._current_debug_workbook,
        })
        self.websocket.sendTextMessage(message)
        logger.info("[IDE] Sent debug_step_over")
    
    def _debug_step_into(self):
        """Step into function call (F11)."""
        if not self._debug_active or not self._current_debug_workbook:
            return
        
        message = json.dumps({
            "type": "debug_step_into",
            "workbook_id": self._current_debug_workbook,
        })
        self.websocket.sendTextMessage(message)
        logger.info("[IDE] Sent debug_step_into")
    
    def _debug_step_out(self):
        """Step out of current function (Shift+F11)."""
        if not self._debug_active or not self._current_debug_workbook:
            return
        
        message = json.dumps({
            "type": "debug_step_out",
            "workbook_id": self._current_debug_workbook,
        })
        self.websocket.sendTextMessage(message)
        logger.info("[IDE] Sent debug_step_out")
    
    def _debug_stop(self):
        """Stop debugging session."""
        if not self._debug_active or not self._current_debug_workbook:
            return
        
        logger.info("[IDE] Stopping debug session...")
        
        # Clear debug line and error line BEFORE resetting state
        if self._current_debug_editor:
            self._current_debug_editor.clear_debug_line()
            if hasattr(self._current_debug_editor, 'clear_error_line'):
                self._current_debug_editor.clear_error_line()
            self._current_debug_editor = None
        
        # Send stop message to kernel
        message = json.dumps({
            "type": "debug_stop",
            "workbook_id": self._current_debug_workbook,
        })
        self.websocket.sendTextMessage(message)
        logger.info("[IDE] Sent debug_stop message")
        
        # Reset all debug state - this will:
        # - Reset _at_debug_exception flag
        # - Re-enable Run and Debug actions
        # - Hide debug toolbar actions  
        # - Set editors back to editable
        # - Clear debug panel
        self._set_debug_state(False)
        
        self.log_to_console("🐛 Debug session stopped", level=OutputLevel.SIMPLE)
    
    def _toggle_breakpoint(self):
        """Toggle breakpoint at current line (F9)."""
        # Get current editor and cursor position
        current_widget = self.editor_tabs.currentWidget()
        if not isinstance(current_widget, MonacoEditor):
            return
        
        editor = current_widget
        workbook_id = editor.workbook_id
        if not workbook_id or workbook_id == self.WELCOME_TAB_ID:
            return
        
        current_index = self.editor_tabs.currentIndex()
        tab_title = self.editor_tabs.tabText(current_index)
        module_name = _strip_py_extension(tab_title)
        
        # Get cursor position from editor
        def on_cursor_position(pos):
            line = pos.get('lineNumber', 1)
            
            # Toggle breakpoint in manager
            added = self.breakpoint_manager.toggle_breakpoint(workbook_id, module_name, line)
            
            if added:
                self.log_to_console(f"Breakpoint added: {module_name}:{line}", level=OutputLevel.DETAILED)
                editor.add_breakpoint(line)  # Add visual indicator
            else:
                self.log_to_console(f"Breakpoint removed: {module_name}:{line}", level=OutputLevel.DETAILED)
                editor.remove_breakpoint(line)  # Remove visual indicator
            
            # Send updated breakpoints to the debugger if debugging is active
            if self._debug_active and self._current_debug_workbook:
                breakpoints = self.breakpoint_manager.get_breakpoints(self._current_debug_workbook)
                message = json.dumps({
                    "type": "debug_update_breakpoints",
                    "workbook_id": self._current_debug_workbook,
                    "breakpoints": breakpoints,
                })
                self.websocket.sendTextMessage(message)
                logger.info(f"[IDE] Sent debug_update_breakpoints: {len(breakpoints)} breakpoints")
        
        editor.get_cursor_position(on_cursor_position)
    
    def _toggle_show_debug_messages(self, checked: bool):
        """Toggle showing debug messages in console."""
        self._show_debug_console_messages = checked
        logger.info(f"[IDE] Debug console messages {'enabled' if checked else 'disabled'}")
    
    def _on_debug_evaluate_expression(self, expression: str, source: str = "watch"):
        """Handle expression evaluation request from debug panel."""
        if not self._debug_active or not self._current_debug_workbook:
            self.debug_panel.add_console_message("Error: No active debug session")
            return
        
        # Generate unique request ID that includes the source
        request_id = f"debug_eval_{source}_{id(self)}_{expression}"
        
        message = json.dumps({
            "type": "debug_evaluate",
            "workbook_id": self._current_debug_workbook,
            "expression": expression,
            "request_id": request_id,
        })
        self.websocket.sendTextMessage(message)
        logger.info(f"[IDE] Sent debug_evaluate ({source}): {expression}")
    
    def _set_debug_exception_state(self, at_exception: bool):
        """
        Set debug state when paused at an exception.
        
        When at_exception=True:
        - Disables stepping commands (Continue, Step Over, Step Into, Step Out)
          so they appear grayed out in toolbar and menu
        - Keeps Stop enabled and active
        - Watch and console remain functional for variable inspection
        
        When at_exception=False:
        - Re-enables all stepping commands
        
        Args:
            at_exception: True if paused at exception, False otherwise
        """
        self._at_debug_exception = at_exception
        
        # Disable/enable stepping commands based on exception state
        # When disabled, they appear grayed out in both toolbar and menu
        stepping_enabled = not at_exception
        self.debug_continue_action.setEnabled(stepping_enabled)
        self.debug_step_over_action.setEnabled(stepping_enabled)
        self.debug_step_into_action.setEnabled(stepping_enabled)
        self.debug_step_out_action.setEnabled(stepping_enabled)
        
        # Stop is always enabled during debug session
        self.debug_stop_action.setEnabled(True)
        
        if at_exception:
            logger.info("[IDE] Debug exception state: stepping commands disabled, only Stop available")
    
    def _set_debug_state(self, active: bool, workbook_id: Optional[str] = None):
        """
        Set debug state and update UI accordingly.
        
        Args:
            active: Whether debugging is active
            workbook_id: The workbook being debugged (if active)
        """
        self._debug_active = active
        self._current_debug_workbook = workbook_id if active else None
        
        # Always reset exception state when changing debug state
        self._at_debug_exception = False
        
        # Show/hide debug panel
        self.debug_panel_dock.setVisible(active)
        if active:
            self.debug_panel_dock.raise_()
        
        # Disable/enable Run and Debug actions during debug session
        self.run_action.setEnabled(not active)
        self.debug_action.setEnabled(not active)
        
        # Show/hide debug toolbar actions
        self.debug_stop_action.setVisible(active)
        self.debug_continue_action.setVisible(active)
        self.debug_step_over_action.setVisible(active)
        self.debug_step_into_action.setVisible(active)
        self.debug_step_out_action.setVisible(active)
        
        # When showing debug actions, ensure they start enabled (not grayed)
        # Exception state will disable them if needed
        if active:
            self.debug_stop_action.setEnabled(True)
            self.debug_continue_action.setEnabled(True)
            self.debug_step_over_action.setEnabled(True)
            self.debug_step_into_action.setEnabled(True)
            self.debug_step_out_action.setEnabled(True)
        
        # Set all editors readonly during debug
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_readonly(active)
        
        # Log message about readonly state when starting debug
        if active:
            self.log_to_console("⚠️ Editors are read-only during debugging", "#E67E22", level=OutputLevel.SIMPLE)
        
        # Clear debug panel when stopping
        if not active:
            self.debug_panel.clear()
            # Also clear any lingering debug/error line highlighting
            if hasattr(self, '_current_debug_editor') and self._current_debug_editor:
                self._current_debug_editor.clear_debug_line()
                if hasattr(self._current_debug_editor, 'clear_error_line'):
                    self._current_debug_editor.clear_error_line()
                self._current_debug_editor = None
            
            logger.info("[IDE] Debug state reset: all actions restored to normal")
    
    def _restore_breakpoints_for_editor(self, editor: MonacoEditor, workbook_id: str, module_name: str):
        """
        Restore breakpoint decorations for an editor.
        
        Args:
            editor: The Monaco editor instance
            workbook_id: The workbook ID
            module_name: The module name
        """
        breakpoint_lines = self.breakpoint_manager.get_module_breakpoints(workbook_id, module_name)
        for line in breakpoint_lines:
            editor.add_breakpoint(line)
        
        if breakpoint_lines:
            logger.debug(f"[IDE] Restored {len(breakpoint_lines)} breakpoints for {module_name}")
    
    def _find_or_open_debug_module(self, workbook_id: str, module_name: str, filename: str = "") -> Optional[MonacoEditor]:
        """
        Find or open a module tab for debugging.
        Uses the same process as double-clicking on module in project explorer.
        
        Args:
            workbook_id: Workbook ID
            module_name: Module name
            filename: Full file path if available (ignored - only in-memory modules supported)
            
        Returns:
            MonacoEditor instance or None if not found
        """
        # First check if already open
        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if isinstance(widget, MonacoEditor):
                tab_title = self.editor_tabs.tabText(i)
                tab_module = _strip_py_extension(tab_title)
                if tab_module == module_name and widget.workbook_id == workbook_id:
                    self.editor_tabs.setCurrentIndex(i)
                    return widget
        
        # Not open - use the EXACT same method as project explorer double-click
        # This will either open from cache or request from Business Layer
        self._on_open_module_requested(workbook_id, module_name)
        
        # After calling _on_open_module_requested, check if the tab was created
        # (it may be async if fetching from Business Layer, but for cached modules it's sync)
        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if isinstance(widget, MonacoEditor):
                tab_title = self.editor_tabs.tabText(i)
                tab_module = _strip_py_extension(tab_title)
                if tab_module == module_name and widget.workbook_id == workbook_id:
                    return widget
        
        # Module might be loading from Business Layer - return None for now
        # The debug line will be set when the tab opens via pending_debug_line mechanism
        return None
    
    def _open_module_from_cache(self, workbook_id: str, module_name: str) -> Optional[MonacoEditor]:
        """
        Open a module from cache - same as project explorer double-click.
        
        Args:
            workbook_id: Workbook ID
            module_name: Module name
            
        Returns:
            MonacoEditor instance or None if not found
        """
        # Get module content from cache
        if workbook_id not in self._module_cache:
            logger.warning(f"[IDE] Workbook {workbook_id} not in module cache")
            return None
        
        if module_name not in self._module_cache[workbook_id]:
            logger.warning(f"[IDE] Module {module_name} not in cache for workbook {workbook_id}")
            return None
        
        code = self._module_cache[workbook_id][module_name]
        
        # Use add_editor_tab - the same method used by project explorer
        # This ensures all signal connections and proper initialization
        editor = self.add_editor_tab(module_name, code, workbook_id)
        
        return editor
    
    def _handle_debug_paused(self, data: dict):
        """
        Handle debug_paused message from kernel.
        
        Args:
            data: Message data with module, line, file, locals, globals, call_stack
        """
        module = data.get("module", "")
        line = data.get("line", 1)
        workbook_id = data.get("workbook_id", "")
        filename = data.get("file", "")  # Full file path if available
        locals_list = data.get("locals", [])
        globals_list = data.get("globals", [])
        call_stack = data.get("call_stack", [])
        
        logger.info(f"[IDE] Debug paused at {module}:{line}")
        
        # Clear previous debug line first
        if hasattr(self, '_current_debug_editor') and self._current_debug_editor:
            self._current_debug_editor.clear_debug_line()
        
        # Update debug panel
        self.debug_panel.update_variables(locals_list, globals_list)
        self.debug_panel.update_call_stack(call_stack)
        
        # Set all watches to "Evaluating..." before re-evaluating
        self.debug_panel.set_all_watches_evaluating()
        
        # Re-evaluate all watch expressions
        for watch_expr in self.debug_panel.watch_expressions:
            self._on_debug_evaluate_expression(watch_expr, "watch")
        
        # Find or open the module tab
        editor = self._find_or_open_debug_module(workbook_id, module, filename)
        
        if editor:
            # Highlight the current line (use QTimer to ensure editor is ready)
            QTimer.singleShot(self.DEBUG_LINE_HIGHLIGHT_DELAY_MS, lambda: editor.set_debug_line(line))
            self._current_debug_editor = editor
            # Only show in console if enabled
            if self._show_debug_console_messages:
                self.log_to_console(f"🐛 Paused at {module}:{line}", "#E67E22", level=OutputLevel.COMPLETE)
        else:
            # Module not found - store pending debug line for when module loads
            self._pending_debug_line = {
                "workbook_id": workbook_id,
                "module_name": module,
                "line": line
            }
            # Module not found - external package or loading from Business Layer
            if self._show_debug_console_messages:
                self.log_to_console(f"🐛 Paused in module: {module}:{line} (loading...)", "#E67E22", level=OutputLevel.COMPLETE)
            self._current_debug_editor = None
    
    def _handle_debug_resumed(self, data: dict):
        """Handle debug_resumed message from kernel."""
        if self._current_debug_editor:
            self._current_debug_editor.clear_debug_line()
        logger.info("[IDE] Debug resumed")
        if self._show_debug_console_messages:
            self.log_to_console("🐛 Debug resumed", level=OutputLevel.COMPLETE)
    
    def _handle_debug_exception(self, data: dict):
        """
        Handle debug_exception message from kernel.
        
        Highlights the error line, shows a popup, but keeps the debug session active
        so the user can inspect variables and use the watch/console.
        """
        module = data.get("module", "")
        line = data.get("line", 1)
        workbook_id = data.get("workbook_id", "")
        filename = data.get("file", "")
        exception_type = data.get("exception_type", "Exception")
        exception_message = data.get("exception_message", "Unknown error")
        exception_traceback = data.get("exception_traceback", "")
        locals_list = data.get("locals", [])
        globals_list = data.get("globals", [])
        call_stack = data.get("call_stack", [])
        
        logger.info(f"[IDE] Received debug_exception: module={module}, line={line}, "
                    f"exception={exception_type}: {exception_message}")
        logger.error(f"[IDE] Debug exception at {module}:{line}: {exception_type}: {exception_message}")
        
        # Clear previous debug line (but not error line yet)
        if self._current_debug_editor:
            self._current_debug_editor.clear_debug_line()
            # Don't clear error line here - we're about to set a new one
        
        # Update debug panel with variables if available
        if locals_list or globals_list:
            self.debug_panel.update_variables(locals_list, globals_list)
        if call_stack:
            self.debug_panel.update_call_stack(call_stack)
        
        # Print traceback and error to debug console
        self.debug_panel.add_console_message(f"❌ {exception_type}: {exception_message}")
        if exception_traceback:
            # Print traceback in a distinct format
            self.debug_panel.add_console_message("Traceback:")
            for tb_line in exception_traceback.strip().split('\n'):
                self.debug_panel.add_console_message(f"  {tb_line}")
        
        # Find or open the module tab
        editor = self._find_or_open_debug_module(workbook_id, module, filename)
        
        if editor:
            # Highlight the error line in red
            def highlight_error():
                if hasattr(editor, 'set_error_line'):
                    editor.set_error_line(line)
                else:
                    # Fallback to debug line if set_error_line not available
                    editor.set_debug_line(line)
            QTimer.singleShot(self.DEBUG_LINE_HIGHLIGHT_DELAY_MS, highlight_error)
            self._current_debug_editor = editor
        
        # Log to console
        self.log_to_console(f"❌ Exception at {module}:{line}: {exception_type}: {exception_message}", "#ff6b6b", level=OutputLevel.SIMPLE)
        
        # Set debug exception state - disables step commands but keeps Stop active
        self._set_debug_exception_state(True)
        
        # Show error popup (non-blocking) - updated message
        QMessageBox.critical(
            self,
            f"Debug Exception: {exception_type}",
            f"An exception occurred during debugging:\n\n"
            f"{exception_type}: {exception_message}\n\n"
            f"Location: {module}:{line}\n\n"
            f"The debugger is paused at the exception. You can:\n"
            f"• Inspect variables in the Debug panel\n"
            f"• Evaluate expressions in the Debug console\n"
            f"• View watch expressions\n\n"
            f"Click 'Stop' to end the debug session."
        )
    
    def _handle_debug_terminated(self, data: dict):
        """Handle debug_terminated message from kernel."""
        logger.info("[IDE] Received debug_terminated from kernel")
        
        # Clear highlighting
        if self._current_debug_editor:
            self._current_debug_editor.clear_debug_line()
            if hasattr(self._current_debug_editor, 'clear_error_line'):
                self._current_debug_editor.clear_error_line()
            self._current_debug_editor = None
        
        # Always show "Debug session ended" message
        self.log_to_console("🐛 Debug session ended", level=OutputLevel.SIMPLE)
        
        # Reset all debug state
        # This handles: exception flag, actions, editors, panel, etc.
        self._set_debug_state(False)
    
    def _handle_debug_evaluate_result(self, data: dict):
        """Handle debug_evaluate_result message from kernel."""
        expression = data.get("expression", "")
        request_id = data.get("request_id", "")
        
        # Log for debugging
        logger.debug(f"[IDE] debug_evaluate_result: expression='{expression}', data={data}")
        
        # Build result dict
        if "error" in data:
            result_dict = {"error": data.get("error")}
        else:
            result_dict = {
                "result": data.get("result", data.get("repr", "")),
                "result_type": data.get("result_type", ""),
                "success": True
            }
        
        # Determine source from request_id (format: debug_eval_{source}_{id}_{expression})
        source = "watch"  # Default to watch
        if request_id.startswith("debug_eval_"):
            parts = request_id.split("_", 3)  # Split into at most 4 parts
            if len(parts) >= 3:
                source = parts[2]  # Extract source from second position
        
        # Update console only if this was a console evaluation
        if source == "console" or self.debug_panel.is_console_expression(expression):
            self.debug_panel.update_console_result(expression, result_dict)
            self.debug_panel.clear_console_expression(expression)
        
        # Update watch if this expression is being watched (regardless of source)
        if expression and expression in self.debug_panel.watch_expressions:
            self.debug_panel.update_watch_result(expression, result_dict)
    
    def _request_initial_settings(self):
        """Request settings from business layer to apply at startup."""
        request_id = f"initial_settings_{id(self)}"
        message = json.dumps({
            "type": "get_all_settings",
            "request_id": request_id,
            "initial": True  # Mark as initial settings request
        })
        self.websocket.sendTextMessage(message)
        logger.debug("[IDE] Requested initial settings from business layer")
    
    def _handle_all_settings_response(self, data: dict):
        """Handle all_settings_response from business layer."""
        settings = data.get("settings", {})
        is_initial = data.get("initial", False)
        
        # Store settings in cache
        self._settings_cache = settings
        
        if is_initial:
            # Apply initial settings without showing dialog
            self._apply_initial_settings(settings)
        else:
            # User opened settings dialog - show it
            # Create and show settings dialog
            dialog = SettingsDialog(self)
            dialog.load_settings(settings)
            
            # Connect signals for immediate application
            dialog.theme_changed.connect(get_settings_action('view.theme')) #(self._set_app_theme)
            dialog.editor_theme_changed.connect(get_settings_action('view.editor_theme')) #(self._set_theme)
            dialog.minimap_changed.connect(get_settings_action('editor.show_minimap')) #(self._apply_minimap_setting)
            
            dialog.font_size_changed.connect(get_settings_action('view.font_size')) #(self._apply_font_size)
            dialog.insert_spaces_changed.connect(get_settings_action('editor.insert_spaces')) #(self._apply_insert_spaces)
            dialog.tab_size_changed.connect(get_settings_action('editor.tab_size')) #(self._apply_tab_size)
            
            dialog.word_wrap_changed.connect(get_settings_action('editor.word_wrap')) #(self._apply_word_wrap)
            dialog.hover_style_changed.connect(get_settings_action('editor.hover_style')) #(self._set_hover_mode)
            dialog.console_output_level_changed.connect(get_settings_action('console.output_level')) #(self._apply_output_level)
            dialog.console_only_ide_changed.connect(get_settings_action('console.only_ide')) #(self._apply_console_only_ide)
            
            # Connect settings_changed signal to save settings
            dialog.settings_changed.connect(self._save_settings)
            
            # Show dialog (no longer checking result since it always saves on close)
            dialog.exec()
    
    @run_in_qt_thread
    def _apply_initial_settings(self, settings: dict):
        """
        Apply all saved settings at IDE startup.
        This uses the SETTINGS_ACTIONS dictionary to apply settings programmatically.
        """
        if settings:
            # Store settings in cache for _get_setting to use
            self._settings_cache = settings
            # Apply settings recursively using the SETTINGS_ACTIONS dictionary
            self._apply_settings_recursive(settings, "")
            logger.info("[IDE] Applied initial settings")
    
    @run_in_qt_thread
    def _apply_settings_recursive(self, settings: dict, prefix: str):
        """
        Recursively apply all settings using the SETTINGS_ACTIONS dictionary.
        
        Args:
            settings: Dictionary of settings to apply
            prefix: Current path prefix (e.g., "view", "editor")
        """
        for key, value in settings.items():
            path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                # Recurse into nested settings
                self._apply_settings_recursive(value, path)
            else:
                # Apply the action for this setting
                action = get_settings_action(path)
                try:
                    action(value)
                    logger.debug(f"[IDE] Applied setting {path} = {value}")
                except (TypeError, ValueError, AttributeError) as e:
                    logger.warning(f"Failed to apply setting {path} = {value}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error applying setting {path} = {value}: {e}", exc_info=True)
    
    @run_in_qt_thread
    def _apply_minimap_setting(self, checked: bool):
        """Apply minimap setting - called when setting changes."""
        self._minimap_visible = checked
        # Update the menu action state
        if hasattr(self, 'minimap_action'):
            self.minimap_action.setChecked(checked)
        # Apply to all existing editors
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_minimap_visible(checked)
    
    @run_in_qt_thread
    def _apply_font_size(self, font_size: int):
        """Apply font size setting to all editors and console."""
        # Apply to all editors
        self._editor_font_size = font_size
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_font_size(font_size)
        
        # Apply to console (if it has a setFontSize or similar method)
        # For now, we'll skip console font size since QTextEdit uses stylesheet
        logger.debug(f"[IDE] Applied font size: {font_size}")
    
    @run_in_qt_thread
    def _apply_insert_spaces(self, insert_spaces: bool):
        """Apply insert spaces setting to all editors."""
        self._editor_insert_spaces = insert_spaces
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_insert_spaces(insert_spaces)
        logger.debug(f"[IDE] Applied insert spaces: {insert_spaces}")
    
    @run_in_qt_thread
    def _apply_tab_size(self, tab_size: int):
        """Apply tab size setting to all editors."""
        self._editor_tab_size = tab_size
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_tab_size(tab_size)
        logger.debug(f"[IDE] Applied tab size: {tab_size}")
    
    @run_in_qt_thread
    def _apply_word_wrap(self, enabled: bool):
        """Apply word wrap setting to all editors."""
        self._editor_word_wrap = enabled
        for i in range(self.editor_tabs.count()):
            tab_widget = self.editor_tabs.widget(i)
            if isinstance(tab_widget, MonacoEditor):
                tab_widget.set_word_wrap(enabled)
        logger.debug(f"[IDE] Applied word wrap: {enabled}")
    
    
    @run_in_qt_thread
    def _apply_output_level(self, value: str):
        """Apply output level setting."""
        level = OutputLevel.from_string(value)
        self._console_output_level = level
        logger.debug(f"[IDE] Applied output level: {level.value}")
    
    def _get_all_editors(self):
        """Get all open Monaco editors."""
        editors = []
        for i in range(self.editor_tabs.count()):
            widget = self.editor_tabs.widget(i)
            if isinstance(widget, MonacoEditor):
                editors.append(widget)
        return editors
    
    def _get_setting(self, path: str, default=None):
        """
        Get a setting value by path.
        
        Args:
            path: Setting path like 'console.max_lines'
            default: Default value if setting not found
            
        Returns:
            The setting value or default
        """
        keys = path.split(".")
        value = self._settings_cache
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
                if value is None:
                    return default
            else:
                return default
        return value if value is not None else default
    
    def _enforce_console_max_lines(self):
        """Remove old lines if console exceeds max_lines setting."""
        max_lines = self._get_setting("console.max_lines", 10000)
        if max_lines <= 0:
            return  # No limit
        
        document = self.console.document()
        block_count = document.blockCount()
        
        if block_count > max_lines:
            # Remove oldest lines
            lines_to_remove = block_count - max_lines
            cursor = QTextCursor(document)
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            
            for _ in range(lines_to_remove):
                cursor.movePosition(QTextCursor.MoveOperation.Down, QTextCursor.MoveMode.KeepAnchor)
            
            cursor.movePosition(QTextCursor.MoveOperation.StartOfLine, QTextCursor.MoveMode.KeepAnchor)
            cursor.removeSelectedText()
    
    def _save_settings(self, new_settings: dict):
        """Save settings to business layer."""
        # Send each setting to business layer
        for section, section_data in new_settings.items():
            if isinstance(section_data, dict):
                for key, value in section_data.items():
                    path = f"{section}.{key}"
                    if isinstance(value, dict):
                        # Nested dict - send each key
                        for sub_key, sub_value in value.items():
                            sub_path = f"{path}.{sub_key}"
                            message = json.dumps({
                                "type": "set_setting",
                                "path": sub_path,
                                "value": sub_value
                            })
                            self.websocket.sendTextMessage(message)
                    else:
                        # Direct value
                        message = json.dumps({
                            "type": "set_setting",
                            "path": path,
                            "value": value
                        })
                        self.websocket.sendTextMessage(message)
        
        self.log_to_console("Settings saved successfully", level=OutputLevel.DETAILED)
        logger.info("[IDE] Settings saved")
    
    def _handle_settings_response(self, data: dict):
        """Handle settings_response from business layer."""
        path = data.get("path", "")
        value = data.get("value")
        logger.debug(f"[IDE] Received setting: {path} = {value}")


    def closeEvent(self, event: QCloseEvent):
        """Override close event to hide instead of close.
        
        Args:
            event: The close event
        """
        # Hide the window instead of closing it
        event.ignore()
        self.hide()
        logger.info("[IDE] Window hidden (close button clicked)")
    
    def show_and_focus(self):
        """Show window and bring to focus."""
        self.show()
        self.setWindowState(
            self.windowState() | Qt.WindowState.WindowMinimized
            
        )
        self.setWindowState(
            self.windowState() & ~Qt.WindowState.WindowMinimized
            
        )
        self.raise_()
        self.activateWindow()
        
        logger.info("[IDE] Window shown and focused")
    
    def exit_application(self):
        """Actually close and quit the application."""
        logger.info("[IDE] Application exit requested")
        # Stop the websocket client if it exists
        if self.websocket_client:
            self.websocket_client.stop()
        # Close the window for real
        QApplication.quit()
