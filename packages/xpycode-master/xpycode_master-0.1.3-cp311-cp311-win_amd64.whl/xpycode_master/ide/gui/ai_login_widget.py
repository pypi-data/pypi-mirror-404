"""
XPyCode IDE - AI Login Widget

This module provides the AI login widget for the toolbar with settings dialog.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QLabel,
    QToolButton,
    QMenu,
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class AISettingsDialog(QDialog):
    """Dialog for configuring AI provider settings."""
    
    def __init__(self, settings_manager, parent=None):
        """
        Initialize the AI settings dialog.
        
        Args:
            settings_manager: SettingsManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        self.setWindowTitle("AI Settings")
        self.setMinimumWidth(500)
        
        self._setup_ui()
        self._load_settings()
    
    def _setup_ui(self):
        """Setup the dialog UI."""
        layout = QVBoxLayout()
        form_layout = QFormLayout()
        
        # Provider selection
        self.provider_combo = QComboBox()
        providers = self.settings_manager.get_providers()
        for provider in providers:
            self.provider_combo.addItem(provider["name"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        form_layout.addRow("Provider:", self.provider_combo)
        
        # Model selection
        self.model_combo = QComboBox()
        form_layout.addRow("Model:", self.model_combo)
        
        # API Key field with show/hide toggle
        api_key_layout = QHBoxLayout()
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.api_key_input.setPlaceholderText("Enter your API key")
        api_key_layout.addWidget(self.api_key_input)
        
        self.show_hide_button = QPushButton("Show")
        self.show_hide_button.setMaximumWidth(60)
        self.show_hide_button.clicked.connect(self._toggle_api_key_visibility)
        api_key_layout.addWidget(self.show_hide_button)
        
        api_key_widget = QWidget()
        api_key_widget.setLayout(api_key_layout)
        form_layout.addRow("API Key:", api_key_widget)
        
        # Azure-specific fields (initially hidden)
        self.azure_endpoint_label = QLabel("Azure Endpoint:")
        self.azure_endpoint_input = QLineEdit()
        self.azure_endpoint_input.setPlaceholderText("https://your-resource.openai.azure.com")
        form_layout.addRow(self.azure_endpoint_label, self.azure_endpoint_input)
        
        self.azure_deployment_label = QLabel("Azure Deployment:")
        self.azure_deployment_input = QLineEdit()
        self.azure_deployment_input.setPlaceholderText("your-deployment-name")
        form_layout.addRow(self.azure_deployment_label, self.azure_deployment_input)
        
        layout.addLayout(form_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._save_settings)
        button_layout.addWidget(self.save_button)
        
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.cancel_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def _toggle_api_key_visibility(self):
        """Toggle API key visibility."""
        if self.api_key_input.echoMode() == QLineEdit.EchoMode.Password:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Normal)
            self.show_hide_button.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.EchoMode.Password)
            self.show_hide_button.setText("Show")
    
    def _on_provider_changed(self, provider_name: str):
        """Handle provider selection change."""
        # Update model list
        provider_config = self.settings_manager.get_provider_config(provider_name)
        
        # Clear model combo first
        self.model_combo.clear()
        
        if provider_config:
            for model in provider_config["models"]:
                self.model_combo.addItem(model)
            
            # Set default model
            default_model = provider_config.get("default_model")
            if default_model:
                index = self.model_combo.findText(default_model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)
        else:
            logger.warning(f"No configuration found for provider: {provider_name}")
        
        # Show/hide Azure-specific fields
        is_azure = provider_name == "Azure OpenAI"
        self.azure_endpoint_label.setVisible(is_azure)
        self.azure_endpoint_input.setVisible(is_azure)
        self.azure_deployment_label.setVisible(is_azure)
        self.azure_deployment_input.setVisible(is_azure)
    
    def _load_settings(self):
        """Load current settings into the dialog."""
        # Load current provider
        current_provider = self.settings_manager.get_current_provider()
        if current_provider:
            index = self.provider_combo.findText(current_provider)
            if index >= 0:
                self.provider_combo.setCurrentIndex(index)
        else:
            # Trigger initial provider change to populate models
            if self.provider_combo.count() > 0:
                self._on_provider_changed(self.provider_combo.currentText())
        
        # Load current model
        current_model = self.settings_manager.get_current_model()
        if current_model:
            index = self.model_combo.findText(current_model)
            if index >= 0:
                self.model_combo.setCurrentIndex(index)
        
        # Load API key
        if current_provider:
            api_key = self.settings_manager.get_api_key(current_provider)
            if api_key:
                self.api_key_input.setText(api_key)
        
        # Load Azure settings
        azure_endpoint = self.settings_manager.get_azure_endpoint()
        if azure_endpoint:
            self.azure_endpoint_input.setText(azure_endpoint)
        
        azure_deployment = self.settings_manager.get_azure_deployment()
        if azure_deployment:
            self.azure_deployment_input.setText(azure_deployment)
    
    def _save_settings(self):
        """Save settings and close dialog."""
        provider = self.provider_combo.currentText()
        model = self.model_combo.currentText()
        api_key = self.api_key_input.text().strip()
        
        # Save provider and model
        self.settings_manager.set_current_provider(provider)
        self.settings_manager.set_current_model(model)
        
        # Save API key if provided
        if api_key:
            self.settings_manager.set_api_key(provider, api_key)
        
        # Save Azure-specific settings
        if provider == "Azure OpenAI":
            azure_endpoint = self.azure_endpoint_input.text().strip()
            azure_deployment = self.azure_deployment_input.text().strip()
            if azure_endpoint:
                self.settings_manager.set_azure_endpoint(azure_endpoint)
            if azure_deployment:
                self.settings_manager.set_azure_deployment(azure_deployment)
        
        logger.info(f"AI settings saved: provider={provider}, model={model}")
        self.accept()


class AILoginWidget(QWidget):
    """Compact toolbar widget for AI provider login and selection."""
    
    # Signal emitted when provider or model changes
    provider_changed = Signal(str, str)  # provider, model
    
    def __init__(self, settings_manager, parent=None):
        """
        Initialize the AI login widget.
        
        Args:
            settings_manager: SettingsManager instance
            parent: Parent widget
        """
        super().__init__(parent)
        self.settings_manager = settings_manager
        
        self._setup_ui()
        self._update_display()
    
    def _setup_ui(self):
        """Setup the widget UI."""
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create a tool button with dropdown menu
        self.button = QToolButton()
        self.button.setText("🤖 Login")
        self.button.setPopupMode(QToolButton.ToolButtonPopupMode.InstantPopup)
        self.button.setToolTip("AI Provider Settings")
        
        # Create menu
        self.menu = QMenu()
        
        # Provider submenu
        self.provider_menu = QMenu("Provider")
        self.menu.addMenu(self.provider_menu)
        
        # Model submenu
        self.model_menu = QMenu("Model")
        self.menu.addMenu(self.model_menu)
        
        self.menu.addSeparator()
        
        # Settings action
        settings_action = QAction("Settings...", self)
        settings_action.triggered.connect(self._open_settings)
        self.menu.addAction(settings_action)
        
        # Clear API key action
        self.clear_action = QAction("Clear API Key", self)
        self.clear_action.triggered.connect(self._clear_api_key)
        self.menu.addAction(self.clear_action)
        
        self.button.setMenu(self.menu)
        layout.addWidget(self.button)
        
        self.setLayout(layout)
        
        # Populate provider and model menus
        self._populate_provider_menu()
    
    def _populate_provider_menu(self):
        """Populate the provider submenu."""
        self.provider_menu.clear()
        
        current_provider = self.settings_manager.get_current_provider()
        providers = self.settings_manager.get_providers()
        
        for provider in providers:
            action = QAction(provider["name"], self)
            action.setCheckable(True)
            if provider["name"] == current_provider:
                action.setChecked(True)
            action.triggered.connect(
                lambda checked, p=provider["name"]: self._on_provider_selected(p)
            )
            self.provider_menu.addAction(action)
    
    def _populate_model_menu(self):
        """Populate the model submenu based on current provider."""
        self.model_menu.clear()
        
        current_provider = self.settings_manager.get_current_provider()
        current_model = self.settings_manager.get_current_model()
        
        if current_provider:
            provider_config = self.settings_manager.get_provider_config(current_provider)
            if provider_config:
                for model in provider_config["models"]:
                    action = QAction(model, self)
                    action.setCheckable(True)
                    if model == current_model:
                        action.setChecked(True)
                    action.triggered.connect(
                        lambda checked, m=model: self._on_model_selected(m)
                    )
                    self.model_menu.addAction(action)
    
    def _on_provider_selected(self, provider: str):
        """Handle provider selection from menu."""
        # Get provider config and set default model
        provider_config = self.settings_manager.get_provider_config(provider)
        if provider_config:
            default_model = provider_config.get("default_model", provider_config["models"][0])
            
            # Save settings
            self.settings_manager.set_current_provider(provider)
            self.settings_manager.set_current_model(default_model)
            
            # Update UI
            self._update_display()
            self._populate_provider_menu()
            self._populate_model_menu()
            
            # Emit signal
            self.provider_changed.emit(provider, default_model)
            logger.info(f"Provider changed to: {provider} with model: {default_model}")
    
    def _on_model_selected(self, model: str):
        """Handle model selection from menu."""
        current_provider = self.settings_manager.get_current_provider()
        
        # Save settings
        self.settings_manager.set_current_model(model)
        
        # Update UI
        self._update_display()
        self._populate_model_menu()
        
        # Emit signal
        if current_provider:
            self.provider_changed.emit(current_provider, model)
            logger.info(f"Model changed to: {model}")
    
    def _update_display(self):
        """Update the button text based on current settings."""
        current_provider = self.settings_manager.get_current_provider()
        current_model = self.settings_manager.get_current_model()
        
        if current_provider and current_model:
            # Check if API key is configured
            api_key = self.settings_manager.get_api_key(current_provider)
            if api_key:
                # Show model name when configured
                self.button.setText(f"🤖 {current_model}")
                self.clear_action.setEnabled(True)
            else:
                # Show Login if no API key
                self.button.setText("🤖 Login")
                self.clear_action.setEnabled(False)
        else:
            self.button.setText("🤖 Login")
            self.clear_action.setEnabled(False)
        
        # Update model menu
        self._populate_model_menu()
    
    def _open_settings(self):
        """Open the AI settings dialog."""
        dialog = AISettingsDialog(self.settings_manager, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Settings were saved, update display
            self._update_display()
            self._populate_provider_menu()
            self._populate_model_menu()
            
            # Emit signal
            provider = self.settings_manager.get_current_provider()
            model = self.settings_manager.get_current_model()
            if provider and model:
                self.provider_changed.emit(provider, model)
    
    def _clear_api_key(self):
        """Clear the API key for the current provider."""
        current_provider = self.settings_manager.get_current_provider()
        if current_provider:
            self.settings_manager.delete_api_key(current_provider)
            self._update_display()
            logger.info(f"API key cleared for {current_provider}")
