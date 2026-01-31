"""
Business Layer Settings Manager

Manages user-level settings stored in JSON file.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from typing import Optional

from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)



class SettingsManager:
    """Manages user-level settings stored in JSON file."""
    
    def __init__(self, base_dir:Optional[Path]=None):
        base_dir=base_dir or Path.home() / ".xpycode"
        self._settings_file = base_dir / "settings.json"
        self._settings: Dict[str, Any] = {}
        self._load_settings()
    
    def _merge_settings(self, saved: dict, defaults: dict) -> dict:
        """
        Deep merge saved settings with defaults.
        Saved values take precedence, defaults fill in missing values.
        
        Args:
            saved: Saved settings from file
            defaults: Default settings
            
        Returns:
            Merged settings dictionary
        """
        result = defaults.copy()
        
        for key, value in saved.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_settings(value, result[key])
            else:
                result[key] = value
        
        return result
    
    def _load_settings(self):
        """Load settings from file, merging with defaults."""
        defaults = self._get_defaults()
        
        if self._settings_file.exists():
            try:
                with open(self._settings_file, 'r') as f:
                    saved_settings = json.load(f)
                # Merge saved settings with defaults
                self._settings = self._merge_settings(saved_settings, defaults)
                logger.info(f"Loaded settings from {self._settings_file}")
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse settings file: {e}")
                self._settings = defaults
                self._save_settings()
        else:
            self._settings = defaults
            self._save_settings()
    
    def _save_settings(self):
        """Save settings to file."""
        try:
            self._settings_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self._settings_file, 'w') as f:
                json.dump(self._settings, f, indent=2)
            logger.debug(f"Saved settings to {self._settings_file}")
        except Exception as e:
            logger.error(f"Failed to save settings: {e}")
    
    def _get_defaults(self) -> Dict[str, Any]:
        """Return default settings."""
        return {
            "view": {
                "theme": "xpy-dark",
                "editor_theme": "vs-dark",
                "font_size": 14
            },
            "package_management": {
                "pip": {
                    "index_urls": [
                        {"url": "https://pypi.org/simple/", "primary": True}
                    ],
                    "use_secondary_urls": False,
                    "proxy": {
                        "enabled": False,
                        "http": "",
                        "https": ""
                    },
                    "retries": 3
                },
                "pip_api": [
                    {
                        "index_url": "https://pypi.org/simple",
                        "api_pattern": "https://pypi.org/pypi/{package_name}/{version}/json"
                    }
                ]
            },
            "editor": {
                "tab_size": 4,
                "insert_spaces": True,
                "show_minimap": True,
                "word_wrap": False
            },
            "console": {
                "max_lines": 10000,
                "clear_on_run": False,
                "output_level": "SIMPLE"
            }
        }
    
    def get(self, path: str, default: Any = None) -> Any:
        """Get setting by dot-notation path (e.g., 'view.theme')."""
        keys = path.split('.')
        value = self._settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, path: str, value: Any):
        """Set setting by dot-notation path."""
        keys = path.split('.')
        target = self._settings
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
        self._save_settings()
    
    def get_all(self) -> Dict[str, Any]:
        """Get all settings."""
        return self._settings.copy()
