"""
XPyCode IDE - Settings Manager

This module provides settings management with secure credential storage.
Uses QSettings for regular preferences and keyring for API keys.
"""

import base64
import json
import logging
import os
from typing import Any, Dict, List, Optional

from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)


class SettingsManager:
    """
    Manager for IDE settings with secure credential storage.
    
    Uses QSettings for regular preferences (stored in OS-native location)
    and keyring library for secure API key storage (with base64 fallback).
    """
    
    SERVICE_NAME = "XPyCode_IDE"
    
    def __init__(self):
        """Initialize the settings manager."""
        # Use QSettings with organization and application name for OS-native storage
        self.settings = QSettings("XPyCode", "XPyCode_IDE")
        
        # Try to import keyring for secure credential storage
        self._keyring_available = False
        try:
            import keyring
            self._keyring = keyring
            self._keyring_available = True
            logger.info("Keyring library available for secure credential storage")
        except ImportError:
            logger.warning("Keyring library not available, falling back to base64 encoding")
            self._keyring = None
        
        # Load AI providers configuration
        self._providers_config = self._load_providers_config()
    
    def _load_providers_config(self) -> Dict[str, Any]:
        """Load AI providers configuration from JSON file."""
        config_path = os.path.join(
            os.path.dirname(__file__),
            "ai_providers.json"
        )
        
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"AI providers config file not found: {config_path}")
            return {"providers": []}
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in AI providers config: {e}")
            return {"providers": []}
        except Exception as e:
            logger.error(f"Failed to load AI providers config: {e}")
            return {"providers": []}
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if key not found
            
        Returns:
            Setting value or default
        """
        return self.settings.value(key, default)
    
    def set_setting(self, key: str, value: Any) -> None:
        """
        Set a setting value.
        
        Args:
            key: Setting key
            value: Setting value
        """
        self.settings.setValue(key, value)
        self.settings.sync()
    
    def get_api_key(self, provider: str) -> Optional[str]:
        """
        Get API key for a provider from secure storage.
        
        Args:
            provider: Provider name (e.g., "OpenAI", "Anthropic")
            
        Returns:
            API key or None if not set
        """
        key_name = f"api_key_{provider}"
        
        if self._keyring_available:
            try:
                api_key = self._keyring.get_password(self.SERVICE_NAME, key_name)
                return api_key
            except Exception as e:
                logger.error(f"Failed to retrieve API key from keyring: {e}")
                return None
        else:
            # Fallback to base64-encoded storage in QSettings
            encoded = self.settings.value(key_name)
            if encoded:
                try:
                    return base64.b64decode(encoded.encode()).decode('utf-8')
                except Exception as e:
                    logger.error(f"Failed to decode API key: {e}")
                    return None
            return None
    
    def set_api_key(self, provider: str, api_key: str) -> None:
        """
        Store API key for a provider in secure storage.
        
        Args:
            provider: Provider name (e.g., "OpenAI", "Anthropic")
            api_key: API key to store
        """
        key_name = f"api_key_{provider}"
        
        if self._keyring_available:
            try:
                self._keyring.set_password(self.SERVICE_NAME, key_name, api_key)
                logger.info(f"API key stored securely for {provider}")
            except Exception as e:
                logger.error(f"Failed to store API key in keyring: {e}")
        else:
            # Fallback to base64-encoded storage in QSettings
            encoded = base64.b64encode(api_key.encode()).decode('utf-8')
            self.settings.setValue(key_name, encoded)
            self.settings.sync()
            logger.info(f"API key stored (base64) for {provider}")
    
    def delete_api_key(self, provider: str) -> None:
        """
        Delete API key for a provider.
        
        Args:
            provider: Provider name (e.g., "OpenAI", "Anthropic")
        """
        key_name = f"api_key_{provider}"
        
        if self._keyring_available:
            try:
                self._keyring.delete_password(self.SERVICE_NAME, key_name)
                logger.info(f"API key deleted for {provider}")
            except Exception as e:
                logger.warning(f"Failed to delete API key from keyring: {e}")
        else:
            # Remove from QSettings
            self.settings.remove(key_name)
            self.settings.sync()
            logger.info(f"API key removed for {provider}")
    
    def get_providers(self) -> List[Dict[str, Any]]:
        """
        Get list of available AI providers.
        
        Returns:
            List of provider configurations
        """
        return self._providers_config.get("providers", [])
    
    def get_provider_config(self, provider_name: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific provider.
        
        Args:
            provider_name: Name of the provider
            
        Returns:
            Provider configuration or None if not found
        """
        for provider in self.get_providers():
            if provider["name"] == provider_name:
                return provider
        return None
    
    def get_current_provider(self) -> Optional[str]:
        """Get currently selected provider name."""
        return self.get_setting("ai_provider")
    
    def set_current_provider(self, provider: str) -> None:
        """Set currently selected provider name."""
        self.set_setting("ai_provider", provider)
    
    def get_current_model(self) -> Optional[str]:
        """Get currently selected model."""
        return self.get_setting("ai_model")
    
    def set_current_model(self, model: str) -> None:
        """Set currently selected model."""
        self.set_setting("ai_model", model)
    
    def get_azure_endpoint(self) -> Optional[str]:
        """Get Azure OpenAI endpoint URL."""
        return self.get_setting("azure_endpoint")
    
    def set_azure_endpoint(self, endpoint: str) -> None:
        """Set Azure OpenAI endpoint URL."""
        self.set_setting("azure_endpoint", endpoint)
    
    def get_azure_deployment(self) -> Optional[str]:
        """Get Azure OpenAI deployment name."""
        return self.get_setting("azure_deployment")
    
    def set_azure_deployment(self, deployment: str) -> None:
        """Set Azure OpenAI deployment name."""
        self.set_setting("azure_deployment", deployment)
