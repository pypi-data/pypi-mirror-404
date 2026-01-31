# xpycode_master/addin_launcher/server_manager.py

from math import e
import subprocess
import sys
import os
import atexit
import time
import signal
import socket
from pathlib import Path
from typing import Optional
from .config import Config
from .certificate_manager import CertificateManager
from .exceptions import ServerStartError, ServerStopError, ServerNotRunningError

import logging
from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class AddinServerManager:
    """
    Manages the lifecycle of the XPyCode Excel Add-in HTTPS server.
    
    Supports two modes:
    - Development (use_compiled=False): Uses system Node.js to run server.js
    - Production (use_compiled=True): Uses pre-compiled standalone binary
    """
    
    def __init__(
        self,
        use_compiled: bool = False,
        port: int = 3000,
        server_port: int = 8000,
        watchdog_port: int = 0,
        docs_port: int = 0,
        auth_token: str = "",
        addin_path: Optional[str] = None,
        timeout: float = 30.0,
        capture_output: bool = False
    ):
        """
        Initialize the server manager.
        
        Args:
            use_compiled: If True, use pre-compiled binary. If False, use Node.js.
            port: Port number for the HTTPS server (default: 3000).
            server_port: Port number for the business layer server (default: 8000).
            watchdog_port: Port number for the watchdog HTTP API (default: 0).
            docs_port: Port number for the documentation server (default: 0).
            auth_token: Auth token for watchdog API (default: "").
            addin_path: Path to addin directory. Auto-detected if None.
            timeout: Maximum seconds to wait for server startup.
            capture_output: If True, capture stdout/stderr for programmatic access.
        """
        self.use_compiled = use_compiled
        self.port = port
        self.server_port = server_port
        self.watchdog_port = watchdog_port
        self.docs_port = docs_port
        self.auth_token = auth_token
        self.timeout = timeout
        self.capture_output = capture_output
        self._process: Optional[subprocess.Popen] = None
        self._config = Config(addin_path)
        self._cert_manager = CertificateManager()
    
    @property
    def url(self) -> str:
        """Get the server URL."""
        return f"https://localhost:{self.port}"
    
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
        Start the addin server.
        
        Raises:
            ServerStartError: If the server fails to start within timeout.
        """
        if self.is_running:
            raise ServerStartError("Server is already running")
        
        cmd = self._build_command()
        
        # Start the process
        self._process = subprocess.Popen(
            cmd,
            cwd=self._config.addin_path,
            stdout=subprocess.PIPE if self.capture_output else None,
            stderr=subprocess.PIPE if self.capture_output else None,
            # Platform-specific process group handling
            **self._get_platform_popen_args()
        )
        atexit.register(self._terminate_process)
        # Wait for server to be ready
        if not self._wait_for_ready():
            self.stop()
            raise ServerStartError(
                f"Server failed to start within {self.timeout} seconds"
            )
    
    def stop(self) -> None:
        """
        Stop the addin server gracefully.
        
        Raises:
            ServerNotRunningError: If no server is running.
        """
        if self._process is None:
            raise ServerNotRunningError("No server process to stop")
        
        try:
            self._terminate_process()
        finally:
            self._process = None
    
    def __enter__(self) -> 'AddinServerManager':
        """Context manager entry - starts the server."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit - stops the server."""
        if self.is_running:
            self.stop()
    
    def _build_command(self) -> list:
        """Build the command to start the server."""
        # Ensure certificates exist and are trusted
        cert_paths = self._cert_manager.ensure_certificates()
        
        # Print certificate paths for user reference
        print('='*50)
        print(f"PATHS:\tCA Certificate: {cert_paths.ca_cert}")
        print(f"PATHS:\tServer Certificate: {cert_paths.server_cert}")
        print(f"PATHS:\tServer Key: {cert_paths.server_key}")
        print('='*50)
        
        if self.use_compiled:
            binary = self._config.get_binary_path()
            cmd = [str(binary)]
        else:
            if self._config.addin_path is None:
                raise self.addin_path_error
            cmd = ["node", str(self._config.addin_path / "server.js") ]
        
        # Add certificate arguments
        cmd.extend([
            "--cert", str(cert_paths.server_cert),
            "--key", str(cert_paths.server_key),
            "--port", str(self.port),
            "--server-port", str(self.server_port),
            "--logging-level", str(logging.getLevelName(logger.getEffectiveLevel()))
        ])
        
        # Add watchdog info if provided
        if self.watchdog_port:
            cmd.extend(["--watchdog-port", str(self.watchdog_port)])
        if self.auth_token:
            cmd.extend(["--auth-token", self.auth_token])
        if self.docs_port:
            cmd.extend(["--docs-port", str(self.docs_port)])
        
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
                s.connect(('localhost', self.port))
                return True
            except (socket.timeout, ConnectionRefusedError, OSError):
                return False
    
    def _terminate_process(self) -> None:
        if not self._process:
            return
        """Terminate the server process (platform-aware)."""
        if sys.platform == 'win32':
            # Windows: use taskkill to ensure child processes are killed    
            subprocess.run(
                    ['taskkill', '/F', '/T', '/PID', str(self._process.pid)],
                    capture_output=True
                    )
        else:
            # Unix: send SIGTERM to process group
            os.killpg(os.getpgid(self._process.pid), signal.SIGTERM)
            try:
                self._process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                os.killpg(os.getpgid(self._process.pid), signal.SIGKILL)
    
    def _get_platform_popen_args(self) -> dict:
        """Get platform-specific Popen arguments."""
        if sys.platform == 'win32':
            return {'creationflags': subprocess.CREATE_NEW_PROCESS_GROUP}
        else:
            return {'preexec_fn': os.setsid}
