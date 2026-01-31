"""
Dependency Resolver - Resolves package dependencies from configured indexes.

This module provides:
- Dependency tree building from package metadata
- Version compatibility resolution
- Conflict detection with first-wins strategy
- Ordered installation list generation
"""

import asyncio
import logging
import re
from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple

from .packages.package_index_client import PackageIndexClient

try:
    from packaging.specifiers import SpecifierSet, InvalidSpecifier
    from packaging.version import Version, InvalidVersion
    PACKAGING_AVAILABLE = True
except ImportError:
    SpecifierSet = None
    InvalidSpecifier = None
    Version = None
    InvalidVersion = None
    PACKAGING_AVAILABLE = False

# Configure logging
from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


@dataclass
class PackageSpec:
    """Specification for a package with version and extras."""
    name: str
    version: str
    extras: List[str] = field(default_factory=list)
    from_dist: bool = False  # True if version came from current distribution
    
    def __hash__(self):
        """Make PackageSpec hashable for use in sets/dicts."""
        return hash((self.name.lower(), self.version, tuple(sorted(self.extras))))
    
    def __eq__(self, other):
        """Compare PackageSpecs by normalized name, version, and extras."""
        if not isinstance(other, PackageSpec):
            return False
        return (
            self.name.lower() == other.name.lower() and
            self.version == other.version and
            sorted(self.extras) == sorted(other.extras)
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "version": self.version,
            "extras": self.extras,
            "from_dist": self.from_dist
        }


class ResolvedPackage:
    """A resolved package with its spec and metadata."""
    spec: PackageSpec
    path: Optional[str] = None  # Path from cache, if available
    is_direct: bool = False  # True if directly requested, False if dependency
    source:set = set()
    is_error=False

    def __init__(self, spec: PackageSpec, path: Optional[str] = None, is_direct: bool = False, source: Set[str] = None):
        self.spec = spec
        self.path = path
        self.is_direct = is_direct
        self.source = source if source is not None else set()

    
    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "spec": self.spec.to_dict(),
            "path": self.path,
            "is_direct": self.is_direct,
            "from_dist": self.spec.from_dist
        }




@dataclass
class ResolutionResult:
    """Result of dependency resolution."""
    success: bool
    packages: List[ResolvedPackage] = field(default_factory=list)
    conflicts: List[Dict[str, str]] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "packages": [pkg.to_dict() for pkg in self.packages],
            "conflicts": self.conflicts,
            "errors": self.errors
        }


class DependencyResolver:
    """
    Resolves package dependencies using configured package indexes.
    
    Uses a first-wins strategy for conflict resolution:
    - The first version encountered for a package is kept
    - Later conflicting versions generate warnings but are skipped
    
    **Limitations:**
    - Only handles exact version specifications (==) for dependencies
    - Dependencies with version ranges (>=, <=, ~=, etc.) are currently skipped
    - This is acceptable for Phase 2 usage with --no-deps installation
    - Future versions should implement proper version range resolution
    
    **Requirements:**
    - Requires aiohttp for API access
    - Will return errors if aiohttp is not available
    """
    
    def __init__(self, settings_manager, package_cache=None):
        """
        Initialize the DependencyResolver.
        
        Args:
            settings_manager: Settings manager instance for configuration
            package_cache: Optional PackageCache instance to check for cached packages
        """
        self.settings_manager = settings_manager
        self.package_cache = package_cache
        self.client = PackageIndexClient(settings_manager)
    
    async def resolve(
        self,
        package_specs: List[PackageSpec]
    ) -> ResolutionResult:
        """
        Resolve dependencies for a list of package specifications.
        
        Args:
            package_specs: List of PackageSpec objects to resolve
            
        Returns:
            ResolutionResult with resolved packages, conflicts, and errors
        """
        result = ResolutionResult(success=True)
        
        # Track resolved packages by normalized name
        resolved: Dict[str, ResolvedPackage] = {}
        
        # Queue for BFS traversal: (spec, is_direct, parent_name)
        queue: List[Tuple[PackageSpec, bool, Optional[str]]] = [
            (spec, True, None) for spec in package_specs
        ]
        
        # Track visited to avoid infinite loops
        visited: Set[Tuple[str, str]] = set()
        
        while queue:
            spec, is_direct, parent = queue.pop(0)
            normalized_name = self._normalize_name(spec.name)
            
            # Check if already visited this version
            visit_key = (normalized_name, spec.version)
            if visit_key in visited:
                continue
            visited.add(visit_key)
            
            # Check for conflicts (different version already resolved)
            if normalized_name in resolved:
                existing = resolved[normalized_name]
                existing.source.add(parent or spec.name)
                if existing.spec.version != spec.version:
                    conflict = {
                        "package": spec.name,
                        "existing_version": existing.spec.version,
                        "requested_version": spec.version,
                        "requested_by": parent or "direct"
                    }
                    result.conflicts.append(conflict)
                    logger.warning(
                        f"Conflict: {spec.name} version {spec.version} requested by "
                        f"{parent or 'direct'}, but version {existing.spec.version} "
                        f"already resolved. Using {existing.spec.version}."
                    )
                continue
            
            # Check if package is in cache
            path = None
            if self.package_cache:
                extras_key = ",".join(sorted(spec.extras)) if spec.extras else ""
                cached_path = self.package_cache.get_cached_package(
                    spec.name,
                    spec.version,
                    extras_key
                )
                if cached_path:
                    path = cached_path
            
            # Add to resolved packages
            resolved_pkg = ResolvedPackage(
                spec=spec,
                path=path,
                is_direct=is_direct,
                source={parent or spec.name}
            )
            resolved[normalized_name] = resolved_pkg
            
            # Fetch and queue dependencies
            try:
                deps = await self.get_package_dependencies(
                    spec.name, 
                    spec.version, 
                    spec.extras,
                    from_dist=spec.from_dist
                )
                for dep_spec in deps:
                    queue.append((dep_spec, False, parent or spec.name))
            except Exception as e:
                error = f"Failed to fetch dependencies for {spec.name}=={spec.version}: {e}"
                result.errors.append(error)
                logger.error(error)
                result.success = False
        
        # Convert to ordered list (direct packages first, then dependencies)
        direct_packages = [pkg for pkg in resolved.values() if pkg.is_direct]
        indirect_packages = [pkg for pkg in resolved.values() if not pkg.is_direct]
        result.packages = direct_packages + indirect_packages
        
        logger.info(
            f"Resolved {len(result.packages)} packages "
            f"({len(direct_packages)} direct, {len(indirect_packages)} dependencies)"
        )
        if result.conflicts:
            logger.warning(f"Found {len(result.conflicts)} version conflicts")
        
        return result
    
    async def get_package_dependencies(
        self,
        package_name: str,
        version: str,
        extras: List[str] = None,
        from_dist: bool = False
    ) -> List[PackageSpec]:
        """
        Fetch package dependencies from configured indexes.
        
        Args:
            package_name: Package name
            version: Package version
            extras: Optional list of extras to include
            from_dist: If True, skip fetching dependencies (package from current dist)
            
        Returns:
            List of PackageSpec objects for dependencies
        """
        # If package is from current distribution, don't resolve its dependencies
        # Rationale: Packages installed in the current environment already have
        # their dependencies satisfied by the environment's dependency tree.
        # Re-resolving them would be redundant and could lead to conflicts.
        if from_dist:
            logger.debug(f"Skipping dependency resolution for {package_name} (from current dist)")
            return []
        
        # Get dependencies from client
        deps_data = await self.client.get_dependencies(package_name, version)
        
        if not deps_data:
            return []
        
        dependencies = []
        extras_set = set(extras or [])
        
        for dep in deps_data:
            # Check if dependency is for a specific extra we don't have
            markers = dep.get("markers", "")
            if markers and "extra ==" in markers:
                match = re.search(r"extra\s*==\s*['\"]([^'\"]+)['\"]", markers)
                if match:
                    required_extra = match.group(1)
                    if required_extra not in extras_set:
                        # This dependency is only for an extra we don't want
                        continue
            
            # Resolve the best version for this requirement
            name = dep["name"]
            version_spec = dep["version_spec"]
            pkg_extras = dep.get("extras", [])
            
            resolved_version, from_dist = await self._resolve_best_version(name, version_spec, pkg_extras)
            if resolved_version:
                dependencies.append(PackageSpec(
                    name=name, 
                    version=resolved_version, 
                    extras=pkg_extras,
                    from_dist=from_dist
                ))
            else:
                logger.debug(f"Could not resolve version for {name} with spec {version_spec}")
        
        logger.debug(f"Found {len(dependencies)} dependencies for {package_name}=={version}")
        return dependencies
    
    async def _resolve_best_version(
        self, package_name: str, version_spec: str, extras: List[str] = None
    ) -> Tuple[Optional[str], bool]:
        """
        Resolve the best version for a package given a version specifier.
        
        First checks current Python distribution, then falls back to package index.
        
        Uses packaging library for proper version constraint handling.
        Supports: ==, >=, <=, >, <, !=, ~=, and compound specifiers.
        
        Args:
            package_name: Package name to query
            version_spec: Version specifier (e.g., ">=1.0.0,<2.0.0")
            extras: Optional list of extras to check. Used when checking current
                    environment to verify extras are available. Not used for
                    package index lookups as those don't validate extras.
            
        Returns:
            Tuple of (version_string, from_dist) where from_dist is True if version
            came from current distribution, False if from package index.
            Returns (None, False) if no match found.
        """
        # First, check if current distribution satisfies the specifier
        dist_version = self.client.check_specifier_in_dist(
            package_name, version_spec, extras
        )
        if dist_version:
            logger.info(f"Package {package_name} satisfied by current distribution: {dist_version}")
            return (dist_version, True)
        
        # Fallback to existing logic for package index resolution
        if not version_spec or not version_spec.strip():
            # No constraint - get latest version
            latest = await self._get_latest_version(package_name)
            return (latest, False)
        
        # Check if packaging library is available
        if not PACKAGING_AVAILABLE:
            logger.warning("packaging library not available, falling back to exact version matching")
            # Fallback to exact version matching
            match = re.match(r"^\s*==\s*([0-9][0-9a-zA-Z._-]*)", version_spec)
            if match:
                return (match.group(1), False)
            else:
                logger.debug(f"Non-exact version spec '{version_spec}' for {package_name}, using latest")
                latest = await self._get_latest_version(package_name)
                return (latest, False)
        
        try:
            specifier = SpecifierSet(version_spec)
        except (InvalidSpecifier, Exception) as e:
            logger.warning(f"Invalid version specifier '{version_spec}' for {package_name}: {e}")
            latest = await self._get_latest_version(package_name)
            return (latest, False)
        
        # Get all available versions
        versions = await self._get_all_versions(package_name)
        if not versions:
            return (None, False)
        
        # Filter versions that match the specifier
        matching_versions = []
        for v_str in versions:
            try:
                v = Version(v_str)
                if v in specifier:
                    matching_versions.append((v, v_str))
            except (InvalidVersion, Exception):
                continue
        
        if not matching_versions:
            logger.warning(f"No versions of {package_name} match specifier {version_spec}")
            return (None, False)
        
        # Return the highest matching version
        matching_versions.sort(key=lambda x: x[0], reverse=True)
        return (matching_versions[0][1], False)
    
    async def _get_latest_version(self, package_name: str) -> Optional[str]:
        """Get the latest version of a package."""
        versions = await self._get_all_versions(package_name)
        if versions:
            return versions[0]  # Assuming sorted descending
        return None
    
    async def _get_all_versions(self, package_name: str) -> List[str]:
        """Get all available versions of a package."""
        return await self.client.get_versions(package_name)
    
    def _normalize_name(self, name: str) -> str:
        """
        Normalize package name according to PEP 503.
        
        Args:
            name: Package name
            
        Returns:
            Normalized package name (lowercase, [-_.] replaced with hyphens)
        """
        return re.sub(r"[-_.]+", "-", name.lower())
