"""
XPyCode IDE - Settings Dialog

This module provides the settings management dialog with tree navigation.
"""

import json
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QStackedWidget, QWidget, QLabel, QComboBox, QCheckBox, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QGroupBox, QFormLayout,
    QDialogButtonBox, QSplitter, QSpinBox, QTableWidget, QTableWidgetItem,
    QHeaderView, QInputDialog, QMessageBox
)
from PySide6.QtCore import Qt, Signal

from .settings_actions import get_settings_action

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)

class SettingsDialog(QDialog):
    """Settings management dialog with tree navigation."""
    
    settings_changed = Signal(dict)  # settings dict
    request_settings = Signal()  # Request settings from business layer
    
    # Signals for immediate application of settings
    theme_changed = Signal(str)  # IDE theme (xpy-dark, xpy-light)
    editor_theme_changed = Signal(str)  # Editor theme (vs-dark, vs-light, etc.)
    minimap_changed = Signal(bool)  # Minimap visibility
    word_wrap_changed = Signal(bool)  # Word wrap enabled
    font_size_changed = Signal(int)  # Font size
    insert_spaces_changed = Signal(bool)  # Insert spaces (not tabs)
    tab_size_changed = Signal(int)  # Tab size
    console_output_level_changed = Signal(str)  # Console output level
    hover_style_changed = Signal(str)  # Hover style (compact, detailed)
    console_only_ide_changed = Signal(bool)  # Console IDE only filter
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.setMinimumSize(800, 600)
        self._settings = {}
        self._load_themes()
        # Hover styles - display name -> setting value mapping
        self._hover_styles = [
            {"id": "compact", "name": "Compact"},
            {"id": "detailed", "name": "Detailed"}
        ]
        self._setup_ui()
    
    def _load_themes(self):
        """Load theme data from themes.json file."""
        themes_file = os.path.join(
            os.path.dirname(__file__),
            "resources",
            "themes.json"
        )
        
        try:
            with open(themes_file, 'r') as f:
                themes_data = json.load(f)
                self._app_themes = themes_data.get("themes", {})
                self._editor_themes = themes_data.get("editor_themes", [])
        except (FileNotFoundError, json.JSONDecodeError) as e:
            # Fallback to defaults if file not found or invalid
            self._app_themes = {
                "xpy-dark": "XPy Dark",
                "xpy-light": "XPy Light"
            }
            self._editor_themes = [
                {"id": "vs-dark", "name": "VS Dark"},
                {"id": "vs-light", "name": "VS Light"},
                {"id": "hc-black", "name": "High Contrast Black"},
                {"id": "hc-light", "name": "High Contrast Light"}
            ]
    
    def showEvent(self, event):
        """Called when dialog is shown - load settings."""
        super().showEvent(event)
        self.request_settings.emit()
    
    def closeEvent(self, event):
        """Called when dialog is closed - always save settings."""
        # Always save settings when closing
        settings = self.get_settings()
        self.settings_changed.emit(settings)
        super().closeEvent(event)
    
    def _setup_ui(self):
        # Left: Tree navigation
        self.tree = QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.tree.setMinimumWidth(200)
        self.tree.currentItemChanged.connect(self._on_tree_selection)
        
        # Build tree
        view_item = QTreeWidgetItem(["View"])
        view_item.setData(0, Qt.ItemDataRole.UserRole, "view")
        themes_item = QTreeWidgetItem(["Themes & Appearance"])
        themes_item.setData(0, Qt.ItemDataRole.UserRole, "view.themes")
        view_item.addChild(themes_item)
        self.tree.addTopLevelItem(view_item)
        
        editor_item = QTreeWidgetItem(["Editor"])
        editor_item.setData(0, Qt.ItemDataRole.UserRole, "editor")
        self.tree.addTopLevelItem(editor_item)
        
        pkg_item = QTreeWidgetItem(["Package Management"])
        pkg_item.setData(0, Qt.ItemDataRole.UserRole, "package_management")
        pip_item = QTreeWidgetItem(["Pip"])
        pip_item.setData(0, Qt.ItemDataRole.UserRole, "package_management.pip")
        pkg_item.addChild(pip_item)
        api_item = QTreeWidgetItem(["API Mappings"])
        api_item.setData(0, Qt.ItemDataRole.UserRole, "package_management.pip_api")
        pkg_item.addChild(api_item)
        self.tree.addTopLevelItem(pkg_item)
        
        console_item = QTreeWidgetItem(["Console"])
        console_item.setData(0, Qt.ItemDataRole.UserRole, "console")
        self.tree.addTopLevelItem(console_item)
        
        self.tree.expandAll()
        
        # Right: Stacked widget for settings pages
        self.stack = QStackedWidget()
        self.stack.addWidget(self._create_empty_page())  # Index 0 - empty placeholder
        self.stack.addWidget(self._create_themes_page())  # Index 1
        self.stack.addWidget(self._create_editor_page())  # Index 2
        self.stack.addWidget(self._create_pip_page())  # Index 3
        self.stack.addWidget(self._create_console_page())  # Index 4
        self.stack.addWidget(self._create_pip_api_page())  # Index 5
        
        # Splitter
        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.stack)
        splitter.setSizes([200, 600])
        
        # Create vertical layout with just the splitter
        v_layout = QVBoxLayout(self)
        v_layout.addWidget(splitter)
    
    def _create_empty_page(self) -> QWidget:
        """Create empty placeholder page for parent nodes."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        label = QLabel("Select a settings category from the tree.")
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        layout.addStretch()
        return widget
    
    def _create_themes_page(self) -> QWidget:
        """Create themes & appearance settings page."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # IDE Theme - populate from themes.json
        self.ide_theme_combo = QComboBox()
        for theme_id, theme_name in self._app_themes.items():
            self.ide_theme_combo.addItem(theme_name, theme_id)
        self.ide_theme_combo.currentIndexChanged.connect(self._on_ide_theme_changed)
        layout.addRow("IDE Theme:", self.ide_theme_combo)
        
        # Editor Theme - populate from themes.json
        self.editor_theme_combo = QComboBox()
        for theme in self._editor_themes:
            self.editor_theme_combo.addItem(theme["name"], theme["id"])
        self.editor_theme_combo.currentIndexChanged.connect(self._on_editor_theme_changed)
        layout.addRow("Editor Theme:", self.editor_theme_combo)
        
        # Font Size
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 24)
        self.font_size_spin.setValue(14)
        self.font_size_spin.valueChanged.connect(self._on_font_size_changed)
        layout.addRow("Font Size:", self.font_size_spin)
        
        layout.addRow(QWidget())  # Spacer
        
        return widget
    
    def _create_editor_page(self) -> QWidget:
        """Create editor settings page."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Tab Size
        self.tab_size_spin = QSpinBox()
        self.tab_size_spin.setRange(2, 8)
        self.tab_size_spin.setValue(4)
        self.tab_size_spin.valueChanged.connect(self._on_tab_size_changed)
        layout.addRow("Tab size:", self.tab_size_spin)
        
        # Insert Spaces
        self.insert_spaces_check = QCheckBox("Insert spaces (not tabs)")
        self.insert_spaces_check.toggled.connect(self._on_insert_spaces_changed)
        layout.addRow(self.insert_spaces_check)
        
        # Show Minimap
        self.show_minimap_check = QCheckBox("Show minimap")
        self.show_minimap_check.toggled.connect(self._on_minimap_changed)
        layout.addRow(self.show_minimap_check)
        
        # Word Wrap
        self.word_wrap_check = QCheckBox("Enable word wrap")
        self.word_wrap_check.toggled.connect(self._on_word_wrap_changed)
        layout.addRow(self.word_wrap_check)
        
        # Hover Style
        self.hover_style_combo = QComboBox()
        for style in self._hover_styles:
            self.hover_style_combo.addItem(style["name"], style["id"])
        self.hover_style_combo.currentIndexChanged.connect(self._on_hover_style_changed)
        layout.addRow("Hover Style:", self.hover_style_combo)
        
        layout.addRow(QWidget())  # Spacer
        
        return widget
    
    def _create_pip_page(self) -> QWidget:
        """Create pip settings page."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Index URLs
        urls_group = QGroupBox("Package Index URLs")
        urls_layout = QVBoxLayout(urls_group)
        
        self.urls_list = QListWidget()
        urls_layout.addWidget(self.urls_list)
        
        urls_buttons = QHBoxLayout()
        self.add_url_btn = QPushButton("Add URL")
        self.add_url_btn.clicked.connect(self._on_add_url)
        self.remove_url_btn = QPushButton("Remove")
        self.remove_url_btn.clicked.connect(self._on_remove_url)
        self.set_primary_btn = QPushButton("Set as Primary")
        self.set_primary_btn.clicked.connect(self._on_set_primary_url)
        urls_buttons.addWidget(self.add_url_btn)
        urls_buttons.addWidget(self.remove_url_btn)
        urls_buttons.addWidget(self.set_primary_btn)
        urls_layout.addLayout(urls_buttons)
        
        self.use_secondary_check = QCheckBox("Use secondary URLs as extra-index-url")
        urls_layout.addWidget(self.use_secondary_check)
        
        layout.addWidget(urls_group)
        
        # Proxy settings
        proxy_group = QGroupBox("Proxy Settings")
        proxy_layout = QFormLayout(proxy_group)
        
        self.proxy_enabled_check = QCheckBox("Enable Proxy")
        self.proxy_enabled_check.toggled.connect(self._on_proxy_enabled_changed)
        proxy_layout.addRow(self.proxy_enabled_check)
        
        self.proxy_http_input = QLineEdit()
        self.proxy_http_input.setPlaceholderText("http://proxy:port")
        proxy_layout.addRow("HTTP Proxy:", self.proxy_http_input)
        
        self.proxy_https_input = QLineEdit()
        self.proxy_https_input.setPlaceholderText("https://proxy:port")
        proxy_layout.addRow("HTTPS Proxy:", self.proxy_https_input)
        
        layout.addWidget(proxy_group)
        
        # Other settings
        other_group = QGroupBox("Other Settings")
        other_layout = QFormLayout(other_group)
        
        self.retries_spin = QSpinBox()
        self.retries_spin.setRange(0, 10)
        self.retries_spin.setValue(3)
        other_layout.addRow("Retries:", self.retries_spin)
        
        layout.addWidget(other_group)
        layout.addStretch()
        
        return widget
    
    
    def _create_console_page(self) -> QWidget:
        """Create console settings page."""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Max Lines
        self.max_lines_spin = QSpinBox()
        self.max_lines_spin.setRange(100, 100000)
        self.max_lines_spin.setValue(10000)
        layout.addRow("Max lines:", self.max_lines_spin)
        
        # Clear on Run
        self.clear_on_run_check = QCheckBox("Clear console on run")
        layout.addRow(self.clear_on_run_check)
        
        # Output Level
        self.output_level_label = QLabel("Output Level:")
        self.output_level_combo = QComboBox()
        self.output_level_combo.addItems(["SIMPLE", "DETAILED", "COMPLETE"])
        self.output_level_combo.setCurrentText("SIMPLE")  # Default
        self.output_level_combo.currentIndexChanged.connect(self._on_console_output_level_changed)
        layout.addRow(self.output_level_label, self.output_level_combo)
        
        # Show IDE Output Only
        self.only_ide_check = QCheckBox("Show IDE output only")
        self.only_ide_check.toggled.connect(self._on_console_only_ide_changed)
        layout.addRow(self.only_ide_check)
        
        layout.addRow(QWidget())  # Spacer
        
        return widget
    
    def _create_pip_api_page(self) -> QWidget:
        """Create pip API mappings settings page."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Index URL to API Mappings
        api_group = QGroupBox("Index URL to API Mappings")
        api_layout = QVBoxLayout(api_group)
        
        self.pip_api_table = QTableWidget()
        self.pip_api_table.setColumnCount(2)
        self.pip_api_table.setHorizontalHeaderLabels(["Index URL", "API Pattern"])
        
        # Column widths
        header = self.pip_api_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        self.pip_api_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.pip_api_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        api_layout.addWidget(self.pip_api_table)
        
        # Buttons
        api_buttons = QHBoxLayout()
        self.add_api_btn = QPushButton("Add")
        self.add_api_btn.clicked.connect(self._on_add_pip_api)
        self.edit_api_btn = QPushButton("Edit")
        self.edit_api_btn.clicked.connect(self._on_edit_pip_api)
        self.remove_api_btn = QPushButton("Remove")
        self.remove_api_btn.clicked.connect(self._on_remove_pip_api)
        api_buttons.addWidget(self.add_api_btn)
        api_buttons.addWidget(self.edit_api_btn)
        api_buttons.addWidget(self.remove_api_btn)
        api_buttons.addStretch()
        api_layout.addLayout(api_buttons)
        
        layout.addWidget(api_group)
        layout.addStretch()
        
        return widget
    
    def _on_ide_theme_changed(self, index: int):
        """Handle IDE theme selection change - apply immediately."""
        theme = self.ide_theme_combo.currentData()
        if theme:
            # Emit signal for main_window connection (primary mechanism)
            self.theme_changed.emit(theme)
    
    def _on_editor_theme_changed(self, index: int):
        """Handle editor theme selection change - apply immediately."""
        editor_theme = self.editor_theme_combo.currentData()
        if editor_theme:
            # Emit signal for main_window connection (primary mechanism)
            self.editor_theme_changed.emit(editor_theme)
    
    def _on_minimap_changed(self, checked: bool):
        """Handle minimap checkbox change - apply immediately."""
        # Emit signal for main_window connection (primary mechanism)
        self.minimap_changed.emit(checked)
    
    def _on_word_wrap_changed(self, checked: bool):
        """Handle word wrap checkbox change - apply immediately."""
        # Emit signal for main_window connection (primary mechanism)
        self.word_wrap_changed.emit(checked)
    
    def _on_font_size_changed(self, value: int):
        """Handle font size change - apply immediately."""
        # Emit signal for main_window connection (primary mechanism)
        self.font_size_changed.emit(value)
    
    def _on_insert_spaces_changed(self, checked: bool):
        """Handle insert spaces checkbox change - apply immediately."""
        # Emit signal for main_window connection (primary mechanism)
        self.insert_spaces_changed.emit(checked)
    
    def _on_tab_size_changed(self, value: int):
        """Handle tab size change - apply immediately."""
        # Emit signal for main_window connection (primary mechanism)
        self.tab_size_changed.emit(value)
    
    def _on_hover_style_changed(self, index: int):
        """Handle hover style selection change - apply immediately."""
        hover_style = self.hover_style_combo.currentData()
        if hover_style:
            self.hover_style_changed.emit(hover_style)
    
    def _on_console_only_ide_changed(self, checked: bool):
        """Handle console only IDE checkbox change - apply immediately."""
        self.console_only_ide_changed.emit(checked)
    
    def _on_console_output_level_changed(self, index: int):
        """Handle console output level change."""
        level= self.output_level_combo.currentText()
        if level:
            self.console_output_level_changed.emit(level)

    def _on_tree_selection(self, current, previous):
        """Handle tree selection change."""
        if current:
            path = current.data(0, Qt.ItemDataRole.UserRole)
            if path == "view.themes":
                self.stack.setCurrentIndex(1)  # Themes page
            elif path == "editor":
                self.stack.setCurrentIndex(2)  # Editor page
            elif path == "package_management.pip":
                self.stack.setCurrentIndex(3)  # Pip page
            elif path == "console":
                self.stack.setCurrentIndex(4)  # Console page
            elif path == "package_management.pip_api":
                self.stack.setCurrentIndex(5)  # API Mappings page
            else:
                # Parent nodes (view, package_management) show empty page
                self.stack.setCurrentIndex(0)  # Empty placeholder
    
    def _on_proxy_enabled_changed(self, checked: bool):
        """Handle proxy enabled checkbox state change."""
        self.proxy_http_input.setEnabled(checked)
        self.proxy_https_input.setEnabled(checked)
    
    def _on_add_url(self):
        """Handle add URL button click."""
        from PySide6.QtWidgets import QInputDialog
        url, ok = QInputDialog.getText(self, "Add Index URL", "Enter URL:")
        if ok and url:
            item = QListWidgetItem(url)
            self.urls_list.addItem(item)
    
    def _on_remove_url(self):
        """Handle remove URL button click."""
        current = self.urls_list.currentRow()
        if current >= 0:
            # Check if this is the only URL remaining
            if self.urls_list.count() == 1:
                from PySide6.QtWidgets import QMessageBox
                QMessageBox.warning(
                    self,
                    "Cannot Remove URL",
                    "Cannot remove the last URL. At least one URL must be configured."
                )
                return
            
            # Get the item to be removed
            item = self.urls_list.item(current)
            text = item.text()
            is_primary = text.startswith("★ ")
            
            # Remove the item
            self.urls_list.takeItem(current)
            
            # If we removed the primary URL, set the first remaining URL as primary
            if is_primary and self.urls_list.count() > 0:
                first_item = self.urls_list.item(0)
                if first_item and not first_item.text().startswith("★ "):
                    first_item.setText(f"★ {first_item.text()}")
    
    
    def _on_set_primary_url(self):
        """Handle set as primary URL button click."""
        current_row = self.urls_list.currentRow()
        if current_row >= 0:
            # Clear all star markers
            for i in range(self.urls_list.count()):
                item = self.urls_list.item(i)
                text = item.text()
                if text.startswith("★ "):
                    item.setText(text[2:])
            
            # Add star to selected item
            item = self.urls_list.item(current_row)
            if not item.text().startswith("★ "):
                item.setText(f"★ {item.text()}")
    
    def _on_add_pip_api(self):
        """Handle add pip API mapping button click."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add API Mapping")
        dialog.resize(500, 150)
        
        layout = QFormLayout()
        
        index_url_input = QLineEdit()
        index_url_input.setPlaceholderText("https://pypi.org/simple")
        layout.addRow("Index URL:", index_url_input)
        
        api_pattern_input = QLineEdit()
        api_pattern_input.setPlaceholderText("https://pypi.org/pypi/{package_name}/{version}/json")
        layout.addRow("API Pattern:", api_pattern_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            index_url = index_url_input.text().strip()
            api_pattern = api_pattern_input.text().strip()
            
            if index_url and api_pattern:
                row = self.pip_api_table.rowCount()
                self.pip_api_table.insertRow(row)
                self.pip_api_table.setItem(row, 0, QTableWidgetItem(index_url))
                self.pip_api_table.setItem(row, 1, QTableWidgetItem(api_pattern))
    
    def _on_edit_pip_api(self):
        """Handle edit pip API mapping button click."""
        current_row = self.pip_api_table.currentRow()
        if current_row < 0:
            return
        
        index_url_item = self.pip_api_table.item(current_row, 0)
        api_pattern_item = self.pip_api_table.item(current_row, 1)
        
        if not index_url_item or not api_pattern_item:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle("Edit API Mapping")
        dialog.resize(500, 150)
        
        layout = QFormLayout()
        
        index_url_input = QLineEdit()
        index_url_input.setText(index_url_item.text())
        layout.addRow("Index URL:", index_url_input)
        
        api_pattern_input = QLineEdit()
        api_pattern_input.setText(api_pattern_item.text())
        layout.addRow("API Pattern:", api_pattern_input)
        
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addRow(buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            index_url = index_url_input.text().strip()
            api_pattern = api_pattern_input.text().strip()
            
            if index_url and api_pattern:
                index_url_item.setText(index_url)
                api_pattern_item.setText(api_pattern)
    
    def _on_remove_pip_api(self):
        """Handle remove pip API mapping button click."""
        current_row = self.pip_api_table.currentRow()
        if current_row >= 0:
            self.pip_api_table.removeRow(current_row)
    
    def load_settings(self, settings: dict):
        """Load settings into UI."""
        self._settings = settings
        
        # Themes - use findData to find the index by value
        view = settings.get("view", {})
        theme_value = view.get("theme", "xpy-dark")
        theme_index = self.ide_theme_combo.findData(theme_value)
        if theme_index >= 0:
            self.ide_theme_combo.setCurrentIndex(theme_index)
        
        editor_theme_value = view.get("editor_theme", "vs-dark")
        editor_theme_index = self.editor_theme_combo.findData(editor_theme_value)
        if editor_theme_index >= 0:
            self.editor_theme_combo.setCurrentIndex(editor_theme_index)
        
        self.font_size_spin.setValue(view.get("font_size", 14))
        
        # Editor - now includes minimap and word wrap
        editor = settings.get("editor", {})
        self.tab_size_spin.setValue(editor.get("tab_size", 4))
        self.insert_spaces_check.setChecked(editor.get("insert_spaces", True))
        # Check both new (editor) and old (view) locations for backward compatibility
        self.show_minimap_check.setChecked(editor.get("show_minimap", view.get("show_minimap", True)))
        self.word_wrap_check.setChecked(editor.get("word_wrap", view.get("word_wrap", False)))
        
        # Hover style
        hover_style_value = editor.get("hover_style", "compact")
        hover_style_index = self.hover_style_combo.findData(hover_style_value)
        if hover_style_index >= 0:
            self.hover_style_combo.setCurrentIndex(hover_style_index)
        else:
            # Fallback to first item (Compact) if value not found
            self.hover_style_combo.setCurrentIndex(0)
        
        # Pip
        pip = settings.get("package_management", {}).get("pip", {})
        self.urls_list.clear()
        for url_entry in pip.get("index_urls", []):
            item = QListWidgetItem(url_entry["url"])
            if url_entry.get("primary"):
                item.setText(f"★ {url_entry['url']}")
            self.urls_list.addItem(item)
        
        self.use_secondary_check.setChecked(pip.get("use_secondary_urls", False))
        
        proxy = pip.get("proxy", {})
        proxy_enabled = proxy.get("enabled", False)
        self.proxy_enabled_check.setChecked(proxy_enabled)
        self.proxy_http_input.setText(proxy.get("http", ""))
        self.proxy_https_input.setText(proxy.get("https", ""))
        
        # Update enabled state of proxy fields
        self._on_proxy_enabled_changed(proxy_enabled)
        
        self.retries_spin.setValue(pip.get("retries", 3))
        
        # Pip API mappings
        pip_api = settings.get("package_management", {}).get("pip_api", [])
        self.pip_api_table.setRowCount(0)
        for entry in pip_api:
            row = self.pip_api_table.rowCount()
            self.pip_api_table.insertRow(row)
            self.pip_api_table.setItem(row, 0, QTableWidgetItem(entry.get("index_url", "")))
            self.pip_api_table.setItem(row, 1, QTableWidgetItem(entry.get("api_pattern", "")))
        
        # Console
        console = settings.get("console", {})
        self.max_lines_spin.setValue(console.get("max_lines", 10000))
        self.clear_on_run_check.setChecked(console.get("clear_on_run", False))
        output_level = console.get("output_level", "SIMPLE")
        self.output_level_combo.setCurrentText(output_level)
        self.only_ide_check.setChecked(console.get("only_ide", False))
    
    def get_settings(self) -> dict:
        """Get settings from UI."""
        # Parse index URLs
        index_urls = []
        for i in range(self.urls_list.count()):
            item = self.urls_list.item(i)
            text = item.text()
            is_primary = text.startswith("★ ")
            url = text[2:] if is_primary else text
            index_urls.append({
                "url": url,
                "primary": is_primary
            })
        
        return {
            "view": {
                "theme": self.ide_theme_combo.currentData(),
                "editor_theme": self.editor_theme_combo.currentData(),
                "font_size": self.font_size_spin.value()
            },
            "package_management": {
                "pip": {
                    "index_urls": index_urls,
                    "use_secondary_urls": self.use_secondary_check.isChecked(),
                    "proxy": {
                        "enabled": self.proxy_enabled_check.isChecked(),
                        "http": self.proxy_http_input.text(),
                        "https": self.proxy_https_input.text()
                    },
                    "retries": self.retries_spin.value()
                },
                "pip_api": [
                    {
                        "index_url": self.pip_api_table.item(row, 0).text(),
                        "api_pattern": self.pip_api_table.item(row, 1).text()
                    }
                    for row in range(self.pip_api_table.rowCount())
                ]
            },
            "editor": {
                "tab_size": self.tab_size_spin.value(),
                "insert_spaces": self.insert_spaces_check.isChecked(),
                "show_minimap": self.show_minimap_check.isChecked(),
                "word_wrap": self.word_wrap_check.isChecked(),
                "hover_style": self.hover_style_combo.currentData()
            },
            "console": {
                "max_lines": self.max_lines_spin.value(),
                "clear_on_run": self.clear_on_run_check.isChecked(),
                "output_level": self.output_level_combo.currentText(),
                "only_ide": self.only_ide_check.isChecked()
            }
        }
