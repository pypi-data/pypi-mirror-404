"""
XPyCode Master Configuration

Port configuration and availability checking for dynamic port selection.
"""

import socket
from typing import List, Optional


# Ports for addin server (HTTPS, for Excel add-in)
# Using non-standard ports to avoid conflicts
ADDIN_PORTS = [49171, 49172, 49173, 49174, 49175, 49176, 49177, 49178, 49179]

# Ports for business layer server (HTTP, Python backend)
SERVER_PORTS = [50171, 50172, 50173, 50174, 50175, 50176, 50177, 50178, 50179]

# Ports for watchdog HTTP API
# IMPORTANT: Keep in sync with WATCHDOG_PORTS in addin/utils/config-utils.js
WATCHDOG_PORTS = [51171, 51172, 51173, 51174, 51175, 51176, 51177, 51178, 51179]

# Ports for documentation server
DOCS_PORTS = [52171, 52172, 52173, 52174, 52175, 52176, 52177, 52178, 52179]

# External addin URL - lazy evaluation to avoid circular import
_external_addin_url = None

def get_external_addin_url() -> str:
    """Get the external addin URL with version."""
    global _external_addin_url
    if _external_addin_url is None:
        from . import __version__
        version = '.'.join((__version__.split('.')+['0']*3)[:3])
        _external_addin_url = f'https://addin.xpycode.com/v1'
    return _external_addin_url

# For backward compatibility, provide EXTERNAL_ADDIN_URL as a module-level function
@property
def EXTERNAL_ADDIN_URL():
    return get_external_addin_url()

# Also provide it directly for simple imports
EXTERNAL_ADDIN_URL = get_external_addin_url


def is_port_available(port: int, host: str = 'localhost') -> bool:
    """
    Check if a port is available for binding.
    
    Args:
        port: Port number to check
        host: Host address (default: 'localhost')
    
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            return True
    except OSError:
        return False


def find_available_port(port_list: List[int], host: str = 'localhost') -> Optional[int]:
    """
    Find the first available port from the list.
    
    Args:
        port_list: List of ports to check
        host: Host address (default: 'localhost')
    
    Returns:
        First available port number, or None if no ports are available
    """
    for port in port_list:
        if is_port_available(port, host):
            return port
    return None
