"""
XPyCode IDE - Icon Utilities

This module provides utilities for working with emoji icons in the IDE.
"""

from typing import Optional

# Icon mapping for different object types
OBJECT_TYPE_ICONS = {
    'Workbook': '📗',
    'Worksheet': '📋',
    'Table': '⊞',
    'Chart': '📊',
    'Shape': '⬡',
    'Binding': '🔗',
    'SettingCollection': '⚙️',
    'CommentCollection': '💬',
    'LinkedEntityDataDomainCollection': '🌐',
    # Collections - use folder icon
    'WorksheetCollection': '📁',
    'TableCollection': '📁',
    'ChartCollection': '📁',
}

# All possible icons used in the IDE
ALL_ICONS = ['📗', '🐍', '📋', '📁', '⊞', '📊', '⬡', '🔗', '⚙️', '💬', '🌐', 'Ƒ', '⚡', '🧩', '📦', '▶️']


def get_icon_for_type(object_type: str) -> str:
    """
    Get icon for an object type. Collections use folder icon.
    
    Args:
        object_type: The type of the object (e.g., 'Workbook', 'Worksheet', etc.)
    
    Returns:
        The emoji icon for the object type, or empty string if no icon is defined
    """
    if object_type in OBJECT_TYPE_ICONS:
        return OBJECT_TYPE_ICONS[object_type]
    # All *Collection types use folder icon
    if object_type.endswith('Collection'):
        return '📁'
    return ''  # No icon for unknown types


def strip_icon_prefix(text: str) -> str:
    """
    Strip emoji icon prefix from text if present.
    
    Args:
        text: The text that may have an icon prefix
    
    Returns:
        The text with the icon prefix removed
    """
    for icon in ALL_ICONS:
        if text.startswith(icon + ' '):
            return text[len(icon) + 1:]
        if text.startswith(icon):
            return text[len(icon):]
    return text


def format_display_name(icon: str, name: str, count: Optional[int] = None) -> str:
    """
    Format a display name with optional icon and event count.
    
    Args:
        icon: The emoji icon (can be empty string)
        name: The object/item name
        count: Optional event count to display in parentheses
    
    Returns:
        Formatted display name string
    """
    if count is not None and count > 0:
        if icon:
            return f"{icon} {name} ({count})"
        else:
            return f"{name} ({count})"
    else:
        if icon:
            return f"{icon} {name}"
        else:
            return name
