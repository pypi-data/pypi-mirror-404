# xpycode_master/addin_launcher/__init__.py

"""
XPyCode Excel Add-in Server Launcher

A Python package to start/stop the Node.js Excel Add-in server.

Usage:
    # As a module
    from xpycode_master.addin_launcher import AddinServerManager
    
    with AddinServerManager(use_compiled=False) as server:
        print(f"Server running at {server.url}")
    
    # From command line
    python -m xpycode_master.addin_launcher start --dev
"""

from .server_manager import AddinServerManager
from .certificate_manager import CertificateManager, CertificatePaths
from .exceptions import (
    AddinServerError,
    ServerStartError,
    ServerStopError,
    ServerNotRunningError,
    BinaryNotFoundError
)

from .. import __version__

__all__ = [
    'AddinServerManager',
    'CertificateManager',
    'CertificatePaths',
    'AddinServerError',
    'ServerStartError',
    'ServerStopError',
    'ServerNotRunningError',
    'BinaryNotFoundError',
]

from ..logging_config import setup_logging_subprocess, get_logger
setup_logging_subprocess()
logger = get_logger(__name__)


# Convenience functions
def start_server(use_compiled: bool = False, port: int = 3000) -> AddinServerManager:
    """
    Quick start function. Returns the manager for later stopping.
    
    Args:
        use_compiled: Use compiled binary (True) or Node.js (False).
        port: Server port (default: 3000).
    
    Returns:
        AddinServerManager instance (call .stop() when done).
    """
    manager = AddinServerManager(use_compiled=use_compiled, port=port)
    manager.start()
    return manager
