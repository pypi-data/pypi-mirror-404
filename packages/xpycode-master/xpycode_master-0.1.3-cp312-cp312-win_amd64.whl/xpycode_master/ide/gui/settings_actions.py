"""
XPyCode IDE - Settings Actions

This module provides a mapping of settings paths to action functions.
Settings can be applied programmatically via the SETTINGS_ACTIONS dictionary.
"""

import logging
from enum import Enum
from typing import Callable

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class OutputLevel(Enum):
    """Output level for console messages."""
    SIMPLE = "SIMPLE"
    DETAILED = "DETAILED"
    COMPLETE = "COMPLETE"
    
    @classmethod
    def from_string(cls, value: str) -> "OutputLevel":
        """Convert string to OutputLevel enum."""
        try:
            return cls(value.upper())
        except (ValueError, AttributeError):
            return cls.SIMPLE  # Default
    
    def allows(self, level: "OutputLevel") -> bool:
        """
        Check if this setting level allows the given message level.
        
        SIMPLE setting: only SIMPLE messages
        DETAILED setting: SIMPLE + DETAILED messages
        COMPLETE setting: all messages (SIMPLE + DETAILED + COMPLETE)
        
        Lower priority number = more important = shown at higher filter levels
        """
        priority = {
            OutputLevel.SIMPLE: 1,
            OutputLevel.DETAILED: 2,
            OutputLevel.COMPLETE: 3,
        }
        return priority[level] <= priority[self]


def do_nothing(value):
    """Placeholder action for settings without direct actions yet."""
    pass


# Action function placeholders
# These placeholder functions are defined here for use in the SETTINGS_ACTIONS dictionary.
# They will be replaced with bound methods from the MainWindow instance at runtime
# via the bind_actions_to_instance() function. This approach allows:
# 1. The SETTINGS_ACTIONS dictionary to be defined at module level
# 2. Settings to be applied before MainWindow is fully initialized
# 3. A clean separation between action definitions and implementations

def apply_theme(value):
    """Apply IDE theme. Bound to main_window._set_app_theme at runtime."""
    pass


def apply_editor_theme(value):
    """Apply editor theme. Bound to main_window._set_theme at runtime."""
    pass


def apply_font_size(value):
    """Apply font size to editors. Bound to main_window._apply_font_size at runtime."""
    pass


def apply_minimap(value):
    """Toggle minimap visibility. Bound to main_window._apply_minimap_setting at runtime."""
    pass


def apply_word_wrap(value):
    """Toggle word wrap. Bound to main_window._apply_word_wrap at runtime."""
    pass


def apply_console_max_lines(value):
    """Apply console max lines setting. Value is read when needed."""
    pass


def apply_clear_console_on_run(value):
    """Apply clear console on run setting. Value is read when needed."""
    pass


def apply_output_level(value):
    """Apply output level setting. Bound to main_window._apply_output_level at runtime."""
    pass


def apply_tab_size(value):
    """Apply tab size to editors. Bound to main_window._apply_tab_size at runtime."""
    pass


def apply_insert_spaces(value):
    """Apply insert spaces setting. Bound to main_window._apply_insert_spaces at runtime."""
    pass


def apply_hover_style(value):
    """Apply hover style. Bound to main_window._set_hover_mode at runtime."""
    pass


def apply_console_only_ide(value):
    """Apply console only IDE filter. Bound to main_window._apply_console_only_ide at runtime."""
    pass


# Dictionary mapping setting paths to action functions
SETTINGS_ACTIONS = {
    "view.theme": apply_theme,
    "view.editor_theme": apply_editor_theme,
    "view.font_size": apply_font_size,
    "editor.show_minimap": apply_minimap,
    "editor.word_wrap": apply_word_wrap,
    "editor.tab_size": apply_tab_size,
    "editor.insert_spaces": apply_insert_spaces,
    "editor.hover_style": apply_hover_style,
    # Settings without direct actions yet - use do_nothing
    "package_management.pip.index_urls": do_nothing,
    "package_management.pip.use_secondary_urls": do_nothing,
    "package_management.pip.proxy.enabled": do_nothing,
    "package_management.pip.proxy.http": do_nothing,
    "package_management.pip.proxy.https": do_nothing,
    "console.max_lines": apply_console_max_lines,
    "console.clear_on_run": apply_clear_console_on_run,
    "console.output_level": apply_output_level,
    "console.only_ide": apply_console_only_ide,
}


def get_settings_action(path: str) -> Callable:
    """
    Get the action function for a setting path.
    Returns do_nothing if no specific action is defined.
    
    Args:
        path: The setting path (e.g., "view.theme")
        
    Returns:
        The action function for this path, or do_nothing if not found
    """
    return SETTINGS_ACTIONS.get(path, do_nothing)


def bind_actions_to_instance(main_window):
    """
    Bind action functions to the main_window instance.
    This allows the action functions to call main_window methods.
    
    Args:
        main_window: The MainWindow instance
    """
    SETTINGS_ACTIONS["view.theme"] = main_window._set_app_theme
    SETTINGS_ACTIONS["view.editor_theme"] = main_window._set_theme
    SETTINGS_ACTIONS["view.font_size"] = main_window._apply_font_size
    SETTINGS_ACTIONS["editor.show_minimap"] = main_window._apply_minimap_setting
    SETTINGS_ACTIONS["editor.word_wrap"] = main_window._apply_word_wrap
    SETTINGS_ACTIONS["editor.tab_size"] = main_window._apply_tab_size
    SETTINGS_ACTIONS["editor.insert_spaces"] = main_window._apply_insert_spaces
    SETTINGS_ACTIONS["editor.hover_style"] = main_window._set_hover_mode
    SETTINGS_ACTIONS["console.output_level"] = main_window._apply_output_level
    SETTINGS_ACTIONS["console.only_ide"] = main_window._apply_console_only_ide
    # Console settings are read when needed, no immediate action required
