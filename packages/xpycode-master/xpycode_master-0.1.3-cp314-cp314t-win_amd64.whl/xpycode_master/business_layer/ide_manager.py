"""
IDE Process Manager - Manages the IDE subprocess lifecycle.

This module provides functionality to:
- Launch the IDE as a subprocess
- Check if the IDE is running
- Send messages to the IDE
- Terminate the IDE process
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Optional

from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class IDEProcessManager:
    """Manages the IDE subprocess lifecycle."""
    
    # Timeout constants (in seconds)
    GRACEFUL_SHUTDOWN_TIMEOUT = 5  # Time to wait for graceful termination
    FORCEFUL_SHUTDOWN_TIMEOUT = 2  # Time to wait after forceful kill
    
    def __init__(self, server_port: int, watchdog_port: int = 0, auth_token: str = "", docs_port: int = 0):
        """
        Initialize the IDE process manager.
        
        Args:
            server_port: The business layer server port
            watchdog_port: The watchdog HTTP API port
            auth_token: The watchdog auth token
            docs_port: The documentation server port
        """
        self.server_port = server_port
        self.watchdog_port = watchdog_port
        self.auth_token = auth_token
        self.docs_port = docs_port
        self.ide_process: Optional[subprocess.Popen] = None
    
    def is_running(self) -> bool:
        """
        Check if IDE process is alive.
        
        Returns:
            True if IDE is running, False otherwise
        """
        return self.ide_process is not None and self.ide_process.poll() is None
    
    def ensure_running(self) -> bool:
        """
        Ensure IDE is running. Launch if not running or dead.
        
        Returns:
            True if IDE is running after this call, False otherwise
        """
        if not self.is_running():
            return self._launch_ide()
        return True
    
    def _launch_ide(self) -> bool:
        """
        Launch the IDE subprocess.
        
        Returns:
            True if launch successful, False otherwise
        """
        try:
            cmd = [
                sys.executable, "-m", "xpycode_master.ide",
                "--port", str(self.server_port)
            ]
            
            # Add watchdog info if provided
            if self.watchdog_port:
                cmd.extend(["--watchdog-port", str(self.watchdog_port)])
            if self.auth_token:
                cmd.extend(["--auth-token", self.auth_token])
            if self.docs_port:
                cmd.extend(["--docs-port", str(self.docs_port)])
            
            logger.info(f"Launching IDE with command: {' '.join(cmd)}")
            
            self.ide_process = subprocess.Popen(
                cmd,
                # Don't capture stdout/stderr to allow IDE to show its own console if needed
                stdout=None,
                stderr=None,
            )
            logger.info(f"IDE launched successfully (PID: {self.ide_process.pid})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to launch IDE: {e}", exc_info=True)
            return False
    
    def kill_and_restart(self) -> bool:
        """
        Kill the IDE process if running and restart it.
        
        Returns:
            True if restart successful, False otherwise
        """
        logger.info("[IDEProcessManager] Kill and restart requested")
        
        # Kill existing process if running
        if self.is_running():
            logger.info(f"[IDEProcessManager] Killing IDE process (PID: {self.ide_process.pid})")
            try:
                self.ide_process.terminate()  # Graceful termination first
                self.ide_process.wait(timeout=self.GRACEFUL_SHUTDOWN_TIMEOUT)
            except subprocess.TimeoutExpired:
                logger.warning("[IDEProcessManager] IDE process did not terminate gracefully, killing forcefully")
                self.ide_process.kill()
                try:
                    self.ide_process.wait(timeout=self.FORCEFUL_SHUTDOWN_TIMEOUT)
                except subprocess.TimeoutExpired:
                    logger.error("[IDEProcessManager] IDE process did not respond to kill signal")
            except Exception as e:
                logger.error(f"[IDEProcessManager] Error killing IDE: {e}")
            finally:
                self.ide_process = None
        
        # Launch new IDE
        return self._launch_ide()
    
    def terminate(self):
        """Terminate the IDE process if running."""
        if self.is_running():
            logger.info(f"Terminating IDE process (PID: {self.ide_process.pid})")
            self.ide_process.terminate()
            try:
                self.ide_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                logger.warning("IDE process did not terminate gracefully, killing...")
                self.ide_process.kill()
            self.ide_process = None
