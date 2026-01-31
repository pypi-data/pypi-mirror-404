"""
Pip Runner - Build pip commands with settings integration.

This module provides:
- PipCommandBuilder class for constructing pip commands with settings
- Integration with settings manager for index URLs, proxy, and retries
"""

import sys
from typing import List, Optional, Dict, Any

from ...logging_config import get_logger

logger = get_logger(__name__)


class PipCommandBuilder:
    """
    Builds pip commands with settings integration.
    
    Uses settings manager to configure:
    - --index-url (primary URL from settings)
    - --extra-index-url (secondary URLs if use_secondary_urls is True)
    - --proxy (if proxy enabled in settings)
    - --retries (from settings, default 3)
    """
    
    def __init__(self, settings_manager: Optional[Any] = None):
        """
        Initialize the PipCommandBuilder.
        
        Args:
            settings_manager: Settings manager instance to read pip configuration.
        """
        self.settings_manager = settings_manager
    
    def _get_pip_settings(self) -> Dict[str, Any]:
        """
        Get pip settings from settings manager.
        
        Returns:
            Dict with pip settings (index_urls, use_secondary_urls, proxy, retries).
        """
        if not self.settings_manager:
            return {
                "index_urls": [{"url": "https://pypi.org/simple/", "primary": True}],
                "use_secondary_urls": False,
                "proxy": {"enabled": False, "http": "", "https": ""},
                "retries": 3
            }
        
        return {
            "index_urls": self.settings_manager.get("package_management.pip.index_urls", 
                                                     [{"url": "https://pypi.org/simple/", "primary": True}]),
            "use_secondary_urls": self.settings_manager.get("package_management.pip.use_secondary_urls", False),
            "proxy": self.settings_manager.get("package_management.pip.proxy", 
                                               {"enabled": False, "http": "", "https": ""}),
            "retries": self.settings_manager.get("package_management.pip.retries", 3)
        }
    
    def build_install_command(
        self,
        package_spec: str,
        target_dir: str,
        no_deps: bool = False,
        prefer_binary: bool = False
    ) -> List[str]:
        """
        Build a pip install command with settings.
        
        Args:
            package_spec: Package specification (e.g., "requests", "numpy>=1.20")
            target_dir: Target directory for installation
            no_deps: Whether to use --no-deps flag
            prefer_binary: Whether to use --prefer-binary flag
            
        Returns:
            List of command arguments for subprocess execution.
        """
        settings = self._get_pip_settings()
        
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--target",
            target_dir,
        ]
        
        # Add index URLs
        primary_url = None
        secondary_urls = []
        for index in settings["index_urls"]:
            if index.get("primary", False):
                primary_url = index["url"]
            else:
                secondary_urls.append(index["url"])
        
        if primary_url:
            cmd.extend(["--index-url", primary_url])
        
        # Add secondary URLs if enabled
        if settings["use_secondary_urls"]:
            for url in secondary_urls:
                cmd.extend(["--extra-index-url", url])
        
        # Add proxy if enabled
        proxy = settings["proxy"]
        if proxy.get("enabled", False):
            proxy_url = proxy.get("https") or proxy.get("http")
            if proxy_url:
                cmd.extend(["--proxy", proxy_url])
        
        # Add retries
        retries = settings.get("retries", 3)
        cmd.extend(["--retries", str(retries)])
        
        # Add optional flags
        if no_deps:
            cmd.append("--no-deps")
        if prefer_binary:
            cmd.append("--prefer-binary")
        
        # Add package spec
        cmd.append(package_spec)
        
        logger.debug(f"Built pip install command: {' '.join(cmd)}")
        return cmd
    
    def build_index_versions_command(
        self,
        package_name: str,
        index_url: Optional[str] = None
    ) -> List[str]:
        """
        Build a pip index versions command.
        
        Args:
            package_name: Package name to query versions for
            index_url: Optional specific index URL to query
            
        Returns:
            List of command arguments for subprocess execution.
        """
        settings = self._get_pip_settings()
        
        cmd = [
            sys.executable,
            "-m",
            "pip",
            "index",
            "versions",
            package_name,
        ]
        
        # Add index URL if provided, otherwise use primary from settings
        if index_url:
            cmd.extend(["--index-url", index_url])
        else:
            # Find primary URL
            for index in settings["index_urls"]:
                if index.get("primary", False):
                    cmd.extend(["--index-url", index["url"]])
                    break
        
        # Add proxy if enabled
        proxy = settings["proxy"]
        if proxy.get("enabled", False):
            proxy_url = proxy.get("https") or proxy.get("http")
            if proxy_url:
                cmd.extend(["--proxy", proxy_url])
        
        # Add retries
        retries = settings.get("retries", 3)
        cmd.extend(["--retries", str(retries)])
        
        logger.debug(f"Built pip index versions command: {' '.join(cmd)}")
        return cmd
