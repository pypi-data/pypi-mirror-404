"""
Python Inspector Launcher

Launches the Python Inspector as a subprocess when the Business Layer starts.
"""

import subprocess
import sys
import os
import logging
import atexit

from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)

_inspector_process = None


def get_inspector_path() -> str:
    """Get the path to the inspector module."""
    return 'xpycode_master.python_inspector'
    #Launch by xpycode_master, a module path ensure full module components relative access
    #Path saved to keep the info
    '''
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "python_inspector",
        "inspector.py"
    )
    '''


def launch_inspector(port:int) -> subprocess.Popen:
    """
    Launch the Python Inspector as a subprocess.
    
    Returns:
        The subprocess.Popen object for the inspector process.
    """
    global _inspector_process
    
    inspector_path = get_inspector_path()
        
    try:
        # Launch inspector with stdout/stderr merged with parent process
        _inspector_process = subprocess.Popen(
            [sys.executable, '-m',inspector_path, str(port)],
            stdout=sys.stdout,
            stderr=sys.stderr,
        )
        logger.info(f"Launched Python Inspector (PID: {_inspector_process.pid})")
        
        # Register cleanup on exit
        atexit.register(terminate_inspector)
        
        return _inspector_process
    except Exception as e:
        logger.error(f"Failed to launch Python Inspector: {e}")
        return None


def terminate_inspector():
    """Terminate the Python Inspector subprocess."""
    global _inspector_process
    
    if _inspector_process is not None:
        try:
            _inspector_process.terminate()
            _inspector_process.wait(timeout=5)
            logger.info("Python Inspector terminated")
        except Exception as e:
            logger.warning(f"Error terminating Python Inspector: {e}")
            try:
                _inspector_process.kill()
            except:
                pass
        finally:
            _inspector_process = None


def is_inspector_running() -> bool:
    """Check if the inspector process is running."""
    global _inspector_process
    
    if _inspector_process is None:
        return False
    
    return _inspector_process.poll() is None
