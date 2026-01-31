"""
Breakpoint Manager - Manage breakpoints per workbook/module.

This module provides a centralized manager for breakpoints in the IDE.
"""

import logging
from typing import Dict, Set, List

from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)



class BreakpointManager:
    """
    Manages breakpoints for all workbooks and modules.
    
    Breakpoints are stored per workbook and module.
    """
    
    def __init__(self):
        """Initialize the breakpoint manager."""
        # Structure: {workbook_id: {module_name: set(line_numbers)}}
        self.breakpoints: Dict[str, Dict[str, Set[int]]] = {}
    
    def toggle_breakpoint(self, workbook_id: str, module_name: str, line: int) -> bool:
        """
        Toggle a breakpoint at the specified location.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
            line: The line number
            
        Returns:
            True if breakpoint was added, False if it was removed
        """
        if workbook_id not in self.breakpoints:
            self.breakpoints[workbook_id] = {}
        
        if module_name not in self.breakpoints[workbook_id]:
            self.breakpoints[workbook_id][module_name] = set()
        
        if line in self.breakpoints[workbook_id][module_name]:
            # Remove breakpoint
            self.breakpoints[workbook_id][module_name].remove(line)
            logger.info(f"[BreakpointManager] Removed breakpoint: {workbook_id}/{module_name}:{line}")
            return False
        else:
            # Add breakpoint
            self.breakpoints[workbook_id][module_name].add(line)
            logger.info(f"[BreakpointManager] Added breakpoint: {workbook_id}/{module_name}:{line}")
            return True
    
    def has_breakpoint(self, workbook_id: str, module_name: str, line: int) -> bool:
        """
        Check if a breakpoint exists at the specified location.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
            line: The line number
            
        Returns:
            True if breakpoint exists, False otherwise
        """
        return (workbook_id in self.breakpoints and
                module_name in self.breakpoints[workbook_id] and
                line in self.breakpoints[workbook_id][module_name])
    
    def get_breakpoints(self, workbook_id: str) -> List[Dict[str, any]]:
        """
        Get all breakpoints for a workbook.
        
        Args:
            workbook_id: The workbook ID
            
        Returns:
            List of breakpoint dicts with 'module' and 'line' keys
        """
        result = []
        
        if workbook_id in self.breakpoints:
            for module_name, lines in self.breakpoints[workbook_id].items():
                for line in lines:
                    result.append({
                        "module": module_name,
                        "line": line,
                    })
        
        return result
    
    def get_module_breakpoints(self, workbook_id: str, module_name: str) -> Set[int]:
        """
        Get all breakpoint line numbers for a specific module.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
            
        Returns:
            Set of line numbers with breakpoints
        """
        if (workbook_id in self.breakpoints and
            module_name in self.breakpoints[workbook_id]):
            return self.breakpoints[workbook_id][module_name].copy()
        return set()
    
    def clear_module_breakpoints(self, workbook_id: str, module_name: str):
        """
        Clear all breakpoints for a specific module.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
        """
        if workbook_id in self.breakpoints and module_name in self.breakpoints[workbook_id]:
            self.breakpoints[workbook_id][module_name].clear()
            logger.info(f"[BreakpointManager] Cleared breakpoints for {workbook_id}/{module_name}")
    
    def clear_workbook_breakpoints(self, workbook_id: str):
        """
        Clear all breakpoints for a workbook.
        
        Args:
            workbook_id: The workbook ID
        """
        if workbook_id in self.breakpoints:
            self.breakpoints[workbook_id].clear()
            logger.info(f"[BreakpointManager] Cleared breakpoints for workbook {workbook_id}")
    
    def clear_all_breakpoints(self):
        """Clear all breakpoints."""
        self.breakpoints.clear()
        logger.info("[BreakpointManager] Cleared all breakpoints")
    
    def move_breakpoint(self, workbook_id: str, module_name: str, old_line: int, new_line: int):
        """
        Move a breakpoint from old_line to new_line.
        
        Args:
            workbook_id: The workbook ID
            module_name: The module name
            old_line: The old line number
            new_line: The new line number
        """
        if (workbook_id in self.breakpoints and 
            module_name in self.breakpoints[workbook_id] and
            old_line in self.breakpoints[workbook_id][module_name]):
            self.breakpoints[workbook_id][module_name].discard(old_line)
            self.breakpoints[workbook_id][module_name].add(new_line)
            logger.debug(f"[BreakpointManager] Moved breakpoint {module_name}:{old_line} -> {new_line}")
