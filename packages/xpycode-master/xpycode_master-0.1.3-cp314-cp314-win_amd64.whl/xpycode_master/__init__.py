"""
XPyCode Master Package

Consolidates all XPyCode Python packages into a single namespace.

This package contains:
- business_layer: Central message broker for XPyCode
- ide: XPyCode IDE application
- python_inspector: Python code inspector
- python_server: Python kernel and server components
- addin_launcher: Excel add-in server launcher
- launcher: Main launcher for the entire XPyCode application
- logging_config: Centralized logging configuration

Usage:
    from xpycode_master.addin_launcher import AddinServerManager
    from xpycode_master.business_layer import *
    from xpycode_master.python_server import *
    from xpycode_master.launcher import main
    from xpycode_master.logging_config import setup_logging_master, get_logger
"""

from .watchdog_xpc import start_master

from importlib.metadata import version, PackageNotFoundError

try:
    __version__ = version("xpycode_master")
except PackageNotFoundError:
    # happens if running from source without installing
    __version__ = "0.1.0"


__all__ = [
    'start_master',
]
