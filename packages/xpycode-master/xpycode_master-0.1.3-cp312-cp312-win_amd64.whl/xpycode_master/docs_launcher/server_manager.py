"""
Documentation Server Manager

Manages the lifecycle of the MkDocs documentation server.
"""

import subprocess
import sys
import os
import atexit
import time
import signal
import socket
from pathlib import Path
from typing import Optional

from ..logging_config import get_logger

logger = get_logger(__name__)


class DocsServerManager:
    """
    Manages the lifecycle of the MkDocs documentation server.
    
    Starts mkdocs serve to provide live documentation viewing.
    """
    
    def __init__(
        self,
        port: int = 8100,
        timeout: float = 30.0,
        capture_output: bool = False
    ):
        """
        Initialize the documentation server manager.
        
        Args:
            port: Port number for the documentation server (default: 8100).
            timeout: Maximum seconds to wait for server startup.
            capture_output: If True, capture stdout/stderr for programmatic access.
        """
        self.port = port
        self.timeout = timeout
        self.capture_output = capture_output
        self._process: Optional[subprocess.Popen] = None
        self._mkdocs_dir = self._find_mkdocs_dir()
    
    @property
    def url(self) -> str:
        """Get the documentation server URL."""
        return f"http://127.0.0.1:{self.port}"
    
    @property
    def pid(self) -> Optional[int]:
        """Get the server process ID, or None if not running."""
        return self._process.pid if self._process else None
    
    @property
    def is_running(self) -> bool:
        """Check if the server is currently running."""
        if self._process is None:
            return False
        return self._process.poll() is None and self._is_port_in_use()
    
    def start(self) -> None:
        """
        Start the documentation server.
        
        Raises:
            RuntimeError: If the server fails to start within timeout.
        """
        if self.is_running:
            logger.warning("Documentation server is already running")
            return
        
        if not self._mkdocs_dir:
            raise RuntimeError("Could not find mkdocs.yml configuration file")
        
        cmd = self._build_command()
        
        # Create a clean environment without the parent package in the path
        # This prevents mkdocs from importing our local watchdog.py instead of the watchdog package
        env = os.environ.copy()
        
        # Start the process
        logger.info(f"Starting documentation server on port {self.port}")
        self._process = subprocess.Popen(
            cmd,
            cwd=str(self._mkdocs_dir.parent),
            env=env,
            stdout=subprocess.PIPE if self.capture_output else subprocess.DEVNULL,
            stderr=subprocess.PIPE if self.capture_output else subprocess.DEVNULL,
            # Platform-specific process group handling
            **self._get_platform_popen_args()
        )

        atexit.register(self._terminate_process)
        
        # Wait for server to be ready
        if not self._wait_for_ready():
            self.stop()
            raise RuntimeError(
                f"Documentation server failed to start within {self.timeout} seconds"
            )
        
        logger.info(f"Documentation server started successfully at {self.url}")
    
    def stop(self) -> None:
        """
        Stop the documentation server gracefully.
        
        Raises:
            RuntimeError: If no server is running.
        """
        if self._process is None:
            raise RuntimeError("No documentation server process to stop")
        
        try:
            logger.info("Stopping documentation server")
            self._terminate_process()
        finally:
            self._process = None
    
    def __enter__(self) -> 'DocsServerManager':
        """Context manager entry - starts the server."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stops the server."""
        if self.is_running:
            self.stop()
    
    def _find_mkdocs_dir(self) -> Optional[Path]:
        """Find the directory containing mkdocs.yml."""
        # Start from the package directory
        current = Path(__file__).parent.parent  # xpycode_master directory
        
        # Check if mkdocs.yml exists in xpycode_master
        if (current / "mkdocs.yml").exists():
            return current
        
        # Check parent directory (project root)
        parent = current.parent
        if (parent / "mkdocs.yml").exists():
            return parent
        
        # Return None if not found
        return None
    
    def _build_command(self) -> list:
        """Build the command to start the documentation server."""
        # Use mkdocs executable directly to avoid import conflicts with our watchdog.py
        # When using 'python -m mkdocs' from xpycode_master directory, it would
        # import our local watchdog.py instead of the watchdog package
        import shutil
        
        mkdocs_exe = shutil.which('mkdocs')
        if mkdocs_exe:
            # Use mkdocs executable directly
            cmd = [mkdocs_exe, "serve", "--dev-addr", f"127.0.0.1:{self.port}",
                        "-f", str(self._mkdocs_dir/"mkdocs.yml")
                        ]
        else:
            # Fallback to python -m mkdocs (may have import conflicts)
            logger.warning("mkdocs executable not found, using python -m mkdocs (may have issues)")
            cmd = [
                sys.executable, "-m", "mkdocs", "serve",
                "-a", f"127.0.0.1:{self.port}",
                "-f",str(self._mkdocs_dir/"mkdocs.yml")
            ]
        
        return cmd
    
    def _wait_for_ready(self) -> bool:
        """Wait for the server to be ready (port accepting connections)."""
        start_time = time.time()
        while time.time() - start_time < self.timeout:
            if self._is_port_in_use():
                return True
            if self._process.poll() is not None:
                # Process exited unexpectedly
                return False
            time.sleep(0.1)
        return False
    
    def _is_port_in_use(self) -> bool:
        """Check if the port is accepting connections."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect(('127.0.0.1', self.port))
                return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                return False
    
    def _terminate_process(self) -> None:
        """Terminate the server process (platform-aware)."""
        if not self._process:
            return
        
        if sys.platform == 'win32':
            # Windows: use taskkill to ensure child processes are killed
            subprocess.run(
                ['taskkill', '/F', '/T', '/PID', str(self._process.pid)],
                capture_output=True
            )
        else:
            # Unix: send SIGTERM to process group
            try:
                os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
            except (ProcessLookupError, OSError):
                # Process already terminated
                pass
    
    def _get_platform_popen_args(self) -> dict:
        """Get platform-specific Popen arguments."""
        if sys.platform == 'win32':
            return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            return {'preexec_fn': os.setsid}
