# xpycode_master/addin_launcher/config.py

import sys
from pathlib import Path
from typing import Optional
from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)

class Config:
    """Configuration for the addin server launcher."""
    
    # Binary names per platform
    BINARY_NAMES = {
        'win32': 'addin-server-win.exe',
        'darwin': 'addin-server-macos',
        'linux': 'addin-server-linux'
    }
    
    def __init__(self, addin_path: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            addin_path: Explicit path to addin directory, or None to auto-detect.
        """
        if addin_path:
            self.addin_path = Path(addin_path)
        else:
            try:
                self.addin_path = self._detect_addin_path()
                self.addin_path_error= None
            except Exception as e:
                self.addin_path= None
                self.addin_path_error= e

        
        self.bin_path = Path(__file__).parent / 'bin'
    
    def _detect_addin_path(self) -> Path:
        """Auto-detect the addin directory path."""
        # Try relative to this package
        package_root = Path(__file__).parent.parent
        candidates = [
            package_root / 'addin',
            package_root.parent / 'addin',
            Path.cwd() / 'addin'
        ]
        
        for candidate in candidates:
            if (candidate / 'server.js').exists():
                return candidate
        
        raise FileNotFoundError(
            "Could not auto-detect addin path. Please specify addin_path parameter."
        )
    
    def get_binary_path(self) -> Path:
        """Get the path to the compiled binary for the current platform."""
        binary_name = self.BINARY_NAMES.get(sys.platform)
        if not binary_name:
            raise OSError(f"Unsupported platform: {sys.platform}")
        
        binary_path = self.bin_path / binary_name
        if not binary_path.exists():
            raise FileNotFoundError(
                f"Compiled binary not found: {binary_path}\n"
                f"Run the build script first: addin/build_binaries.bat"
            )
        
        return binary_path
