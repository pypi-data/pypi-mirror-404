"""
Packages Module - Dedicated module for package management.

This module provides:
- PackageManager class for managing Python packages
- PipCommandBuilder for building pip commands with settings
- VersionResolver for multi-index version search
- Message handlers for package management operations
"""

from .manager import PackageManager, validate_package_spec
from .pip_runner import PipCommandBuilder
from .version_resolver import VersionResolver
from .handlers import (
    init_handlers,
    handle_package_install_request,
    handle_get_package_versions_request,
    handle_get_package_extras_request,
    handle_get_package_info_request,
    handle_add_workbook_package,
    handle_remove_workbook_package,
    handle_update_workbook_package,
    handle_restore_workbook_packages,
    handle_update_package_status,
    handle_reorder_workbook_packages,
    handle_install_workbook_packages,
    handle_get_workbook_packages,
    handle_get_resolved_deps,
    handle_update_python_paths,
)

__all__ = [
    "PackageManager",
    "validate_package_spec",
    "PipCommandBuilder",
    "VersionResolver",
    "init_handlers",
    "handle_package_install_request",
    "handle_get_package_versions_request",
    "handle_get_package_extras_request",
    "handle_get_package_info_request",
    "handle_add_workbook_package",
    "handle_remove_workbook_package",
    "handle_update_workbook_package",
    "handle_restore_workbook_packages",
    "handle_update_package_status",
    "handle_reorder_workbook_packages",
    "handle_install_workbook_packages",
    "handle_get_workbook_packages",
    "handle_get_resolved_deps",
    "handle_update_python_paths",
]
