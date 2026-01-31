"""
XPyCode IDE - Advanced Actions Configuration

Dynamic configuration system for advanced actions.
Each "tab" becomes a submenu under the Advanced menu.
Each action becomes a menu item with tooltip.
"""

from typing import Callable, List, Dict
from dataclasses import dataclass


@dataclass
class AdvancedAction:
    """Represents a single advanced action."""
    short_name: str
    description: str
    action_function: Callable


# Configuration storage
ADVANCED_ACTIONS_CONFIG: Dict[str, List[AdvancedAction]] = {}


def register_action(tab_name: str, action: AdvancedAction):
    """Register an action under a tab."""
    if tab_name not in ADVANCED_ACTIONS_CONFIG:
        ADVANCED_ACTIONS_CONFIG[tab_name] = []
    ADVANCED_ACTIONS_CONFIG[tab_name].append(action)


def get_tabs() -> List[str]:
    """Get list of tab names."""
    return list(ADVANCED_ACTIONS_CONFIG.keys())


def get_actions(tab_name: str) -> List[AdvancedAction]:
    """Get actions for a tab."""
    return ADVANCED_ACTIONS_CONFIG.get(tab_name, [])


def clear_actions():
    """Clear all registered actions."""
    ADVANCED_ACTIONS_CONFIG.clear()
