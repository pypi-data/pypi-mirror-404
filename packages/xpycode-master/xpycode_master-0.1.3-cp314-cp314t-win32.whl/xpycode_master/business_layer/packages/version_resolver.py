"""
Version Resolver - Multi-index version search.

This module provides:
- VersionResolver class for querying package versions across multiple indexes
- Delegates to PackageIndexClient for actual querying
"""

from typing import List

from .package_index_client import PackageIndexClient
from ...logging_config import get_logger

logger = get_logger(__name__)


class VersionResolver:
    """
    Resolves package versions across multiple package indexes.
    
    Delegates to PackageIndexClient for querying.
    """
    
    def __init__(self, settings_manager):
        """
        Initialize the VersionResolver.
        
        Args:
            settings_manager: Settings manager instance for configuration.
        """
        self.settings_manager = settings_manager
        self.client = PackageIndexClient(settings_manager)
    
    async def get_available_versions(self, package_name: str) -> List[str]:
        """
        Query available versions for a package across configured indexes.
        
        Args:
            package_name: The package name to query.
            
        Returns:
            List of version strings sorted descending (latest first), 
            or empty list if not found.
        """
        return await self.client.get_versions(package_name)
