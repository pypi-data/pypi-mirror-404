"""
Package Index Client - Centralized package index querying.

This module provides:
- PackageIndexClient class for querying package information from configured repositories
- Multi-index search: query primary first, then secondaries one by one
- API-first approach: prefer API calls over pip commands
- Shared aiohttp session for performance
"""

import asyncio
import re
import sys
import importlib.metadata
from typing import List, Optional, Set, Dict, Any, Tuple, final
from html.parser import HTMLParser

try:
    import aiohttp
except ImportError:
    aiohttp = None

try:
    from unearth import PackageFinder
    UNEARTH_AVAILABLE = True
except ImportError:
    PackageFinder = None
    UNEARTH_AVAILABLE = False

try:
    from packaging.specifiers import SpecifierSet
    from packaging.version import Version
    PACKAGING_AVAILABLE = True
except ImportError:
    SpecifierSet = None
    Version = None
    PACKAGING_AVAILABLE = False

from ...logging_config import get_logger

logger = get_logger(__name__)

class _dummy_metadata(dict):
    def get_all(self, *args, **kwargs):
        return []

class _dummy_dist():
    metadata: Dict[str, str]
    def __init__(self,name,version):
        self.metadata=_dummy_metadata()
        self.metadata["Name"]=name
        self.metadata["Version"]=version


class PackageIndexClient:
    """
    Centralized client for querying package indexes.
    
    Multi-index search strategy:
    1. Query primary index first
    2. If empty AND use_secondary_urls is True, query secondaries one by one
    3. Stop at first index with results (don't cumulate)
    
    API-first approach:
    - Use pip_api patterns when available
    - Fall back to pip commands when API not available
    """
    
    def __init__(self, settings_manager):
        """
        Initialize the PackageIndexClient.
        
        Args:
            settings_manager: Settings manager instance for configuration.
        """
        self.settings_manager = settings_manager
        self._session = None
        self._metadata_cache: Dict[Tuple[str, str], dict] = {}
        self._distributions_cache: Optional[Dict[str, importlib.metadata.Distribution]] = None
    
    async def _get_session(self):
        """Get or create aiohttp session."""
        if aiohttp is None:
            raise RuntimeError("aiohttp not installed, cannot query package indexes")
        
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self):
        """Close HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize package name per PEP 503.
        
        Args:
            name: Package name to normalize.
            
        Returns:
            Normalized package name (lowercase with [-_.] replaced by hyphens).
        """
        return re.sub(r"[-_.]+", "-", name.lower())
    
    def _get_current_distributions(self) -> Dict[str, importlib.metadata.Distribution]:
        """
        Get cached current Python environment distributions.
        
        Returns:
            Dict mapping normalized package name to Distribution object.
        """

        if self._distributions_cache is None:
            self._distributions_cache = {}
            for dist in importlib.metadata.distributions():
                name = self._normalize_name(dist.metadata["Name"])
                self._distributions_cache[name] = dist

            stdlib=getattr(sys,'stdlib_module_names', [])
            sys_version=sys.version.split()[0]
            for mod in stdlib:
                norm_name=self._normalize_name(mod)
                if norm_name not in self._distributions_cache:
                    self._distributions_cache[norm_name]=_dummy_dist(mod, sys_version)

        return self._distributions_cache
    
    def clear_distributions_cache(self):
        """Clear the distributions cache to force refresh."""
        self._distributions_cache = None
    
    def check_specifier_in_dist(
        self, 
        package_name: str, 
        version_spec: str,
        extras: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Check if a package specifier is satisfied by the current Python environment.
        
        Logic:
        1. Check if package is in current distributions
        2. If yes, check if its version matches the specification
        3. If yes and extras are specified, check if the distribution fulfills the extras requirements
        4. If all checks pass, return the version; otherwise return None
        
        Args:
            package_name: The package name to check.
            version_spec: Version specifier (e.g., ">=1.0.0,<2.0.0" or "==1.5.0" or "").
            extras: Optional list of extras that must be satisfied.
            
        Returns:
            The version string if satisfied by current distribution, None otherwise.
        """
        try:
            dist_version_str = None
            if not PACKAGING_AVAILABLE:
                logger.debug("packaging library not available, cannot check distributions")
                return None
        
            distributions = self._get_current_distributions()
            normalized_name = self._normalize_name(package_name)
        
            # Step 1: Check if package is in current distributions
            dist = distributions.get(normalized_name)
            if dist is None:
                return None
        
            dist_version_str = dist.metadata.get("Version")
            if not dist_version_str:
                return None
        
            # Step 2: Check if version matches the specification
            if version_spec and version_spec.strip():
                try:
                    specifier = SpecifierSet(version_spec)
                    dist_version = Version(dist_version_str)
                    if dist_version not in specifier:
                        return None
                except Exception as e:
                    logger.debug(f"Error checking version spec for {package_name}: {e}")
                    return None
        
            # Step 3: Check if extras are specified
            if extras:
                # Step 4: Check if distribution fulfills extras requirements
                # Get the distribution's requires (dependencies for extras)
                requires = dist.metadata.get_all("Requires-Dist") or []
            
                # Build set of available extras from the distribution
                # Note: This uses a regex pattern to match standard PEP 508 extra markers
                # in the form: extra == 'name' or extra == "name"
                # Most packages follow this format, but edge cases may exist.
                available_extras = set()
                for req in requires:
                    if "extra ==" in req:
                        # Match patterns like: extra == 'name' or extra == "name"
                        match = re.search(r'extra\s*==\s*["\']([^"\']+)["\']', req)
                        if match:
                            available_extras.add(match.group(1).lower())
            
                # Check if all requested extras are available
                for extra in extras:
                    if extra.lower() not in available_extras:
                        # Extra not available in distribution
                        return None
        
            # All checks passed
            return dist_version_str
        finally:
            pass

    
    def _get_pip_settings(self) -> Dict[str, Any]:
        """
        Get pip settings from settings manager.
        
        Returns:
            Dict with pip settings (index_urls, use_secondary_urls, etc.).
        """
        if not self.settings_manager:
            return {
                "index_urls": [{"url": "https://pypi.org/simple/", "primary": True}],
                "use_secondary_urls": False,
                "retries": 3
            }
        
        return {
            "index_urls": self.settings_manager.get(
                "package_management.pip.index_urls",
                [{"url": "https://pypi.org/simple/", "primary": True}]
            ),
            "use_secondary_urls": self.settings_manager.get(
                "package_management.pip.use_secondary_urls", False
            ),
            "retries": self.settings_manager.get("package_management.pip.retries", 3)
        }
    
    def _get_pip_api_list(self) -> List[Dict[str, str]]:
        """
        Get pip_api list from settings.
        
        Returns:
            List of pip_api mappings.
        """
        if not self.settings_manager:
            return [
                {
                    "index_url": "https://pypi.org/simple",
                    "api_pattern": "https://pypi.org/pypi/{package_name}/{version}/json"
                }
            ]
        
        return self.settings_manager.get(
            "package_management.pip_api",
            [
                {
                    "index_url": "https://pypi.org/simple",
                    "api_pattern": "https://pypi.org/pypi/{package_name}/{version}/json"
                }
            ]
        )
    
    def _normalize_url(self, url: str) -> str:
        """
        Normalize URL by stripping trailing slashes and backslashes.
        
        Args:
            url: URL to normalize.
            
        Returns:
            Normalized URL.
        """
        return url.rstrip('/\\')
    
    def _get_api_pattern_for_index(self, index_url: str) -> Optional[str]:
        """
        Get API pattern for a given index URL.
        
        Args:
            index_url: The index URL to match.
            
        Returns:
            API pattern if found, None otherwise.
        """
        pip_api_list = self._get_pip_api_list()
        normalized_index = self._normalize_url(index_url)
        
        for entry in pip_api_list:
            entry_index = self._normalize_url(entry.get("index_url", ""))
            if normalized_index == entry_index:
                return entry.get("api_pattern")
        
        return None
    
    async def find_repo_for_package(self, package_name: str) -> Optional[str]:
        """
        Find the first repository URL where package exists.
        
        Args:
            package_name: The package name to search for.
            
        Returns:
            Repository URL where package exists, or None if not found.
        """
        settings = self._get_pip_settings()
        
        # Get primary and secondary URLs
        primary_url = None
        secondary_urls = []
        for index in settings["index_urls"]:
            if index.get("primary", False):
                primary_url = index["url"]
            else:
                secondary_urls.append(index["url"])
        
        # Check primary index first
        if primary_url:
            if await self._package_exists_in_index(package_name, primary_url):
                return primary_url
        
        # Check secondary indexes if enabled
        if settings["use_secondary_urls"] and secondary_urls:
            for url in secondary_urls:
                if await self._package_exists_in_index(package_name, url):
                    return url
        
        return None
    
    async def find_repo_for_package_version(
        self, package_name: str, version: str
    ) -> Optional[str]:
        """
        Find the first repository URL with specific package version.
        
        Args:
            package_name: The package name to search for.
            version: The specific version to find.
            
        Returns:
            Repository URL where package version exists, or None if not found.
        """
        settings = self._get_pip_settings()
        
        # Get primary and secondary URLs
        primary_url = None
        secondary_urls = []
        for index in settings["index_urls"]:
            if index.get("primary", False):
                primary_url = index["url"]
            else:
                secondary_urls.append(index["url"])
        
        # Check primary index first
        if primary_url:
            if await self._package_version_exists_in_index(package_name, version, primary_url):
                return primary_url
        
        # Check secondary indexes if enabled
        if settings["use_secondary_urls"] and secondary_urls:
            for url in secondary_urls:
                if await self._package_version_exists_in_index(package_name, version, url):
                    return url
        
        return None
    
    async def _package_exists_in_index(
        self, package_name: str, index_url: str
    ) -> bool:
        """
        Check if package exists in an index.
        
        Args:
            package_name: The package name to check.
            index_url: The index URL to query.
            
        Returns:
            True if package exists, False otherwise.
        """
        # Try API first
        api_pattern = self._get_api_pattern_for_index(index_url)
        if api_pattern:
            try:
                api_url = api_pattern.replace("{package_name}", package_name)
                # Remove /{version} part if present
                api_url = re.sub(r'/\{version\}', '', api_url)
                
                session = await self._get_session()
                async with session.get(
                    api_url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
            except Exception as e:
                logger.debug(f"API check failed for {package_name} at {index_url}: {e}")
                return False
        
        # Fallback to unearth if available
        if not UNEARTH_AVAILABLE:
            logger.debug(f"No API pattern and unearth not available for {index_url}")
            return False
        
        # Use unearth to check if package exists
        try:
            finder = PackageFinder(index_urls=[index_url])
            packages = finder.find_all_packages(package_name)
            # Use any() to check efficiently without consuming entire iterator
            return any(True for _ in packages)
        except Exception as e:
            logger.debug(f"Unearth check failed for {package_name} at {index_url}: {e}")
            return False
    
    async def _package_version_exists_in_index(
        self, package_name: str, version: str, index_url: str
    ) -> bool:
        """
        Check if specific package version exists in an index.
        
        Args:
            package_name: The package name to check.
            version: The version to check.
            index_url: The index URL to query.
            
        Returns:
            True if package version exists, False otherwise.
        """
        # Try API first
        api_pattern = self._get_api_pattern_for_index(index_url)
        if api_pattern:
            try:
                api_url = api_pattern.replace("{package_name}", package_name)
                api_url = api_url.replace("{version}", version)
                
                session = await self._get_session()
                async with session.get(
                    api_url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    return response.status == 200
            except Exception as e:
                logger.debug(f"API check failed for {package_name}=={version} at {index_url}: {e}")
                return False
        
        # Fallback to unearth if available
        if not UNEARTH_AVAILABLE:
            return False
        
        try:
            loop = asyncio.get_event_loop()
            exists = await loop.run_in_executor(
                None,
                self._package_version_exists_via_unearth,
                package_name,
                version,
                index_url
            )
            return exists
        except Exception:
            return False
    
    def _package_version_exists_via_unearth(
        self, package_name: str, version: str, index_url: str
    ) -> bool:
        """Check if package version exists using unearth."""
        try:
            finder = PackageFinder(index_urls=[index_url])
            result = finder.find_best_match(f"{package_name}=={version}")
            return result is not None and result.best is not None
        except Exception:
            return False
    
    async def get_versions(
        self, package_name: str, index_url: Optional[str] = None
    ) -> List[str]:
        """
        Get all versions for a package from first available repo or specific index.
        
        Args:
            package_name: The package name to query.
            index_url: Optional specific index URL to query.
            
        Returns:
            List of version strings sorted descending (latest first), 
            or empty list if not found.
        """
        if index_url:
            # Query specific index
            return await self._get_versions_from_index(package_name, index_url)
        
        settings = self._get_pip_settings()
        
        # Get primary and secondary URLs
        primary_url = None
        secondary_urls = []
        for index in settings["index_urls"]:
            if index.get("primary", False):
                primary_url = index["url"]
            else:
                secondary_urls.append(index["url"])
        
        # Query primary index first
        if primary_url:
            logger.info(f"Querying primary index for {package_name} versions")
            versions = await self._get_versions_from_index(package_name, primary_url)
            if versions:
                logger.info(f"Found {len(versions)} versions in primary index")
                return versions
        
        # If no results and secondary URLs are enabled, try them one by one
        if settings["use_secondary_urls"] and secondary_urls:
            logger.info(f"No results in primary, trying {len(secondary_urls)} secondary indexes")
            for url in secondary_urls:
                logger.info(f"Querying secondary index: {url}")
                versions = await self._get_versions_from_index(package_name, url)
                if versions:
                    logger.info(f"Found {len(versions)} versions in secondary index")
                    return versions
        
        logger.warning(f"No versions found for {package_name} in any index")
        return []
    
    async def _get_versions_from_index(
        self, package_name: str, index_url: str
    ) -> List[str]:
        """
        Get versions from a specific index.
        
        Args:
            package_name: The package name to query.
            index_url: The index URL to query.
            
        Returns:
            List of version strings, or empty list on error.
        """
        # Try API first
        api_pattern = self._get_api_pattern_for_index(index_url)
        if api_pattern:
            try:
                api_url = api_pattern.replace("{package_name}", package_name)
                # Remove /{version} part if present
                api_url = re.sub(r'/\{version\}', '', api_url)
                
                session = await self._get_session()
                async with session.get(
                    api_url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 404:
                        logger.debug(f"Package {package_name} not found at {index_url}")
                        return []
                    elif response.status != 200:
                        logger.error(f"API returned status {response.status} for {api_url}")
                        return []
                    
                    data = await response.json()
                    releases = data.get("releases", {})
                    versions = list(releases.keys())
                    
                    # Sort versions descending (latest first)
                    # Simple string sort - could use packaging.version for better sorting
                    versions.sort(reverse=True)
                    
                    logger.debug(f"Found {len(versions)} versions via API for {package_name}")
                    return versions
            except asyncio.TimeoutError:
                logger.error(f"Timeout querying {index_url} for {package_name}")
                return []
            except Exception as e:
                logger.error(f"Failed to query {index_url} for {package_name}: {e}")
                return []
        
        # Fallback to unearth if available
        if not UNEARTH_AVAILABLE:
            logger.debug(f"No API pattern and unearth not available for {index_url}")
            return []
        
        try:
            # Run unearth in thread pool since it's synchronous
            loop = asyncio.get_event_loop()
            versions = await loop.run_in_executor(
                None,
                self._get_versions_via_unearth,
                package_name,
                index_url
            )
            return versions
        except Exception as e:
            logger.error(f"Unearth failed for {package_name} at {index_url}: {e}")
            return []
    
    def _get_versions_via_unearth(self, package_name: str, index_url: str) -> List[str]:
        """Get versions using unearth library (synchronous)."""
        try:
            finder = PackageFinder(index_urls=[index_url])
            packages = list(finder.find_all_packages(package_name))
            
            # Extract unique versions
            versions = list(set(str(pkg.version) for pkg in packages))
            
            # Sort versions descending (latest first)
            try:
                from packaging.version import Version, InvalidVersion
                valid_versions = []
                for v in versions:
                    try:
                        valid_versions.append((Version(v), v))
                    except InvalidVersion:
                        pass
                valid_versions.sort(key=lambda x: x[0], reverse=True)
                return [v[1] for v in valid_versions]
            except ImportError:
                # Fallback to simple string sort
                versions.sort(reverse=True)
                return versions
        except Exception as e:
            logger.error(f"Unearth _get_versions failed: {e}")
            return []
    
    async def get_extras(
        self, package_name: str, version: str, index_url: Optional[str] = None
    ) -> List[str]:
        """
        Get extras for a package/version from first available repo or specific index.
        
        Args:
            package_name: The package name to query.
            version: The specific version to query.
            index_url: Optional specific index URL to query.
            
        Returns:
            List of extra names sorted alphabetically, or empty list if not found.
        """
        if index_url:
            # Query specific index
            extras = await self._get_extras_from_index(package_name, version, index_url)
            return sorted(list(extras))
        
        settings = self._get_pip_settings()
        
        # Get primary and secondary URLs
        primary_url = None
        secondary_urls = []
        for index in settings["index_urls"]:
            if index.get("primary", False):
                primary_url = index["url"]
            else:
                secondary_urls.append(index["url"])
        
        # Query primary index first
        if primary_url:
            logger.info(f"Querying primary index for extras: {package_name}")
            extras = await self._get_extras_from_index(package_name, version, primary_url)
            if extras:
                logger.info(f"Found {len(extras)} extras in primary index")
                return sorted(list(extras))
        
        # If no results and secondary URLs are enabled, try them one by one
        if settings["use_secondary_urls"] and secondary_urls:
            logger.info(
                f"No extras in primary, trying {len(secondary_urls)} secondary indexes"
            )
            for url in secondary_urls:
                logger.info(f"Querying secondary index: {url}")
                extras = await self._get_extras_from_index(package_name, version, url)
                if extras:
                    logger.info(f"Found {len(extras)} extras in secondary index")
                    return sorted(list(extras))
        
        logger.info(f"No extras found for {package_name} in any index")
        return []
    
    async def _get_extras_from_index(
        self, package_name: str, version: str, index_url: str
    ) -> Set[str]:
        """
        Get extras from a specific index.
        
        Args:
            package_name: The package name to query.
            version: The specific version to query.
            index_url: The index URL to query.
            
        Returns:
            Set of extra names, or empty set on error.
        """
        # Try API first
        api_pattern = self._get_api_pattern_for_index(index_url)
        if api_pattern:
            try:
                api_url = api_pattern.replace("{package_name}", package_name)
                api_url = api_url.replace("{version}", version)
                
                session = await self._get_session()
                async with session.get(
                    api_url, timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 404:
                        logger.debug(f"Package {package_name} not found at {index_url}")
                        return set()
                    elif response.status != 200:
                        logger.error(f"API returned status {response.status} for {api_url}")
                        return set()
                    
                    data = await response.json()
                    
                    # Extract extras from requires_dist field
                    info = data.get("info", {})
                    requires_dist = info.get("requires_dist", [])
                    extras = set()
                    
                    if requires_dist:
                        for req in requires_dist:
                            # Parse requirements like: "package ; extra == 'extra_name'"
                            if "extra ==" in req:
                                match = re.search(
                                    r"extra\s*==\s*['\"]([^'\"]+)['\"]", req
                                )
                                if match:
                                    extras.add(match.group(1))
                    
                    logger.debug(
                        f"Found {len(extras)} extras via API for {package_name}"
                    )
                    return extras
            except asyncio.TimeoutError:
                logger.error(f"Timeout querying {index_url} for {package_name}")
                return set()
            except Exception as e:
                logger.error(f"Failed to query {index_url} for {package_name}: {e}")
                return set()
        
        # Fallback to unearth if available
        if not UNEARTH_AVAILABLE:
            logger.debug(f"No API pattern and unearth not available for {index_url}")
            return set()
        
        try:
            loop = asyncio.get_event_loop()
            extras = await loop.run_in_executor(
                None,
                self._get_extras_via_unearth,
                package_name,
                version,
                index_url
            )
            return extras
        except Exception as e:
            logger.error(f"Unearth failed for extras {package_name}=={version}: {e}")
            return set()
    
    def _get_extras_via_unearth(
        self, package_name: str, version: str, index_url: str
    ) -> Set[str]:
        """Get extras using unearth library by fetching wheel metadata."""
        try:
            finder = PackageFinder(index_urls=[index_url])
            
            # Find the specific version
            result = finder.find_best_match(f"{package_name}=={version}")
            if not result or not result.best:
                return set()
            
            # Get metadata from the package link
            link = result.best.link
            if not link:
                return set()
            
            # Try to get metadata from wheel
            metadata = finder.get_metadata(link)
            if not metadata:
                return set()
            
            # Parse requires_dist from metadata
            requires_dist = metadata.get_all("Requires-Dist") or []
            extras = set()
            
            for req_str in requires_dist:
                if "extra ==" in req_str:
                    match = re.search(r"extra\s*==\s*['\"]([^'\"]+)['\"]", req_str)
                    if match:
                        extras.add(match.group(1))
            
            return extras
        except Exception as e:
            logger.debug(f"Unearth get_extras failed: {e}")
            return set()
    
    async def get_dependencies(
        self, package_name: str, version: str, index_url: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Get dependencies for a package/version from first available repo or specific index.
        
        Args:
            package_name: The package name to query.
            version: The specific version to query.
            index_url: Optional specific index URL to query.
            
        Returns:
            List of dependency dicts with 'name', 'version_spec', and 'extras' keys,
            or empty list if not found.
        """
        if index_url:
            # Query specific index
            return await self._get_dependencies_from_index(package_name, version, index_url)
        
        settings = self._get_pip_settings()
        
        # Get primary and secondary URLs
        primary_url = None
        secondary_urls = []
        for index in settings["index_urls"]:
            if index.get("primary", False):
                primary_url = index["url"]
            else:
                secondary_urls.append(index["url"])
        
        # Query primary index first
        if primary_url:
            logger.info(f"Querying primary index for dependencies: {package_name}")
            deps = await self._get_dependencies_from_index(package_name, version, primary_url)
            if deps:
                logger.info(f"Found {len(deps)} dependencies in primary index")
                return deps
        
        # If no results and secondary URLs are enabled, try them one by one
        if settings["use_secondary_urls"] and secondary_urls:
            logger.info(
                f"No dependencies in primary, trying {len(secondary_urls)} secondary indexes"
            )
            for url in secondary_urls:
                logger.info(f"Querying secondary index: {url}")
                deps = await self._get_dependencies_from_index(package_name, version, url)
                if deps:
                    logger.info(f"Found {len(deps)} dependencies in secondary index")
                    return deps
        
        logger.debug(f"No dependencies found for {package_name} in any index")
        return []
    
    async def _get_dependencies_from_index(
        self, package_name: str, version: str, index_url: str
    ) -> List[Dict[str, Any]]:
        """
        Get dependencies from a specific index.
        
        Args:
            package_name: The package name to query.
            version: The specific version to query.
            index_url: The index URL to query.
            
        Returns:
            List of dependency dicts, or empty list on error.
        """
        # Check cache first
        cache_key = (package_name.lower(), version)
        if cache_key in self._metadata_cache:
            metadata = self._metadata_cache[cache_key]
        else:
            # Try API first
            api_pattern = self._get_api_pattern_for_index(index_url)
            if api_pattern:
                try:
                    api_url = api_pattern.replace("{package_name}", package_name)
                    api_url = api_url.replace("{version}", version)
                    
                    session = await self._get_session()
                    async with session.get(
                        api_url, timeout=aiohttp.ClientTimeout(total=10)
                    ) as response:
                        if response.status == 404:
                            logger.debug(f"Package {package_name} not found at {index_url}")
                            return []
                        elif response.status != 200:
                            logger.error(f"API returned status {response.status} for {api_url}")
                            return []
                        
                        metadata = await response.json()
                        self._metadata_cache[cache_key] = metadata
                except asyncio.TimeoutError:
                    logger.error(f"Timeout querying {index_url} for {package_name}")
                    return []
                except Exception as e:
                    logger.error(f"Failed to query {index_url} for {package_name}: {e}")
                    return []
            else:
                # Fallback to unearth if available
                if not UNEARTH_AVAILABLE:
                    logger.debug(f"No API pattern and unearth not available for {index_url}")
                    return []
                
                try:
                    loop = asyncio.get_event_loop()
                    deps = await loop.run_in_executor(
                        None,
                        self._get_dependencies_via_unearth,
                        package_name,
                        version,
                        index_url
                    )
                    return deps
                except Exception as e:
                    logger.error(f"Unearth failed for dependencies {package_name}=={version}: {e}")
                    return []
        
        # Parse dependencies from requires_dist
        info = metadata.get("info", {})
        requires_dist = info.get("requires_dist", [])
        
        if not requires_dist:
            return []
        
        dependencies = []
        for req in requires_dist:
            # Parse requirement string (e.g., "package>=1.0.0; extra == 'dev'")
            dep = self._parse_requirement(req)
            if dep:
                dependencies.append(dep)
        
        logger.debug(f"Found {len(dependencies)} dependencies for {package_name}=={version}")
        return dependencies
    
    def _get_dependencies_via_unearth(
        self, package_name: str, version: str, index_url: str
    ) -> List[Dict[str, Any]]:
        """Get dependencies using unearth library by fetching wheel metadata."""
        try:
            finder = PackageFinder(index_urls=[index_url])
            
            # Find the specific version
            result = finder.find_best_match(f"{package_name}=={version}")
            if not result or not result.best:
                return []
            
            # Get metadata from the package link
            link = result.best.link
            if not link:
                return []
            
            # Try to get metadata from wheel
            metadata = finder.get_metadata(link)
            if not metadata:
                return []
            
            # Parse requires_dist from metadata
            requires_dist = metadata.get_all("Requires-Dist") or []
            dependencies = []
            
            for req_str in requires_dist:
                dep = self._parse_requirement(req_str)
                if dep:
                    dependencies.append(dep)
            
            return dependencies
        except Exception as e:
            logger.debug(f"Unearth get_dependencies failed: {e}")
            return []
    
    def _parse_requirement(self, req: str) -> Optional[Dict[str, Any]]:
        """
        Parse a requirement string into components.
        
        Args:
            req: Requirement string (e.g., "package>=1.0.0; extra == 'dev'")
            
        Returns:
            Dict with 'name', 'version_spec', 'extras', and 'markers' keys, or None on error.
        """
        # Split on semicolon to separate package spec from markers
        parts = req.split(";", 1)
        pkg_part = parts[0].strip()
        marker_part = parts[1].strip() if len(parts) > 1 else ""
        
        # Parse package name and version specifier
        # Handle formats like: package, package>=1.0.0, package==1.0.0, package[extra]>=1.0.0
        match = re.match(r"^([a-zA-Z0-9._-]+)(\[[^\]]+\])?(.*)", pkg_part)
        if not match:
            logger.warning(f"Could not parse requirement: {req}")
            return None
        
        name = match.group(1)
        extras_str = match.group(2) or ""
        version_spec = match.group(3).strip()
        
        # Extract extras from brackets
        pkg_extras = []
        if extras_str:
            extras_str = extras_str.strip("[]")
            pkg_extras = [e.strip() for e in extras_str.split(",")]
        
        return {
            "name": name,
            "version_spec": version_spec,
            "extras": pkg_extras,
            "markers": marker_part
        }
    