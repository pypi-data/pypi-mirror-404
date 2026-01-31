"""
Extras Resolver - Multi-index extras search.

This module provides:
- ExtrasResolver class for querying package extras across multiple indexes
- Delegates to PackageIndexClient for actual querying
"""

from typing import List, Optional

from .package_index_client import PackageIndexClient
from ...logging_config import get_logger

logger = get_logger(__name__)


class ExtrasResolver:
    """
    Resolves package extras across multiple package indexes.
    
    Delegates to PackageIndexClient for querying.
    """
    
    def __init__(self, settings_manager):
        """
        Initialize the ExtrasResolver.
        
        Args:
            settings_manager: Settings manager instance for configuration.
        """
        self.settings_manager = settings_manager
        self.client = PackageIndexClient(settings_manager)
    
    async def get_package_extras(
        self, package_name: str, version: Optional[str] = None
    ) -> List[str]:
        """
        Query extras for a package across configured indexes.
        
        Args:
            package_name: The package name to query.
            version: Optional specific version to query.
            
        Returns:
            List of extra names sorted alphabetically, or empty list if not found.
        """
        if not version:
            # If no version specified, get latest version first
            versions = await self.client.get_versions(package_name)
            if not versions:
                logger.warning(f"No versions found for {package_name}")
                return []
            version = versions[0]  # Use latest version
            logger.info(f"Using latest version {version} for {package_name}")
        
        return await self.client.get_extras(package_name, version)
