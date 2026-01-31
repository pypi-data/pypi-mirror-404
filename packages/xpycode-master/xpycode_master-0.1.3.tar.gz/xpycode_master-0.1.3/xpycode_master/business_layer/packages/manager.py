"""
Package Manager - Backend logic for managing Python packages in XPyCode V3.

This module provides:
- PackageManager class for handling pip install commands
- Integration with settings manager for pip configuration
- Subprocess execution with output capture
- Centralized hidden cache directory for package installations
- PyPI version and extras queries via JSON API
- SQLite-based package cache tracking
"""

import asyncio
import logging
import os
import re
import sys
import uuid
from typing import AsyncGenerator, Optional, Tuple, List, Dict

try:
    import aiohttp
except ImportError:
    aiohttp = None

from ..package_cache import PackageCache
from .pip_runner import PipCommandBuilder
from .version_resolver import VersionResolver
from .extras_resolver import ExtrasResolver

# Configure logging
from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


# Default hidden cache directory for packages
DEFAULT_CACHE_DIR = ".xpycode_packages"

# Valid package spec pattern (alphanumeric, hyphens, underscores, dots, brackets, comparison operators)
# Allows: package_name, package-name, package[extra], package>=1.0.0, etc.
VALID_PACKAGE_PATTERN = re.compile(
    r"^[a-zA-Z0-9][a-zA-Z0-9._-]*(\[[a-zA-Z0-9,._-]+\])?(==|>=|<=|>|<|!=|~=)?[a-zA-Z0-9._-]*$"
)


def validate_package_spec(package_spec: str) -> Tuple[bool, str]:
    """
    Validate package spec to prevent injection attacks.

    Returns (is_valid, error_message).
    """
    if not package_spec:
        return False, "Package spec cannot be empty"
    if len(package_spec) > 256:
        return False, "Package spec too long (max 256 characters)"
    # Check for shell metacharacters that could be used for injection
    dangerous_chars = [";", "|", "&", "$", "`", "(", ")", "{", "}", "<", ">", "\n", "\r"]
    for char in dangerous_chars:
        if char in package_spec:
            return False, f"Package spec contains invalid character: {char}"
    if not VALID_PACKAGE_PATTERN.match(package_spec):
        return False, "Package spec contains invalid format"
    return True, ""


class PackageManager:
    """
    Manages Python package installations for workbooks.

    Handles pip install commands targeting a centralized hidden cache directory,
    queries PyPI for package versions and extras, and maintains an SQLite cache.
    Integrates with settings manager for pip configuration.
    """

    def __init__(self, base_dir: Optional[str] = None, settings_manager: Optional[any] = None):
        """
        Initialize the PackageManager.

        Args:
            base_dir: Base directory for package installations.
                      If None, uses current working directory.
            settings_manager: Settings manager instance for pip configuration.
        """
        self.base_dir = base_dir or os.getcwd()
        self.cache_dir = os.path.join(self.base_dir, DEFAULT_CACHE_DIR)
        self.settings_manager = settings_manager
        
        # Initialize package cache
        self.package_cache = PackageCache(cache_dir=self.base_dir)
        
        # Initialize pip command builder, version resolver, and extras resolver
        self.pip_command_builder = PipCommandBuilder(settings_manager)
        self.version_resolver = VersionResolver(settings_manager)
        self.extras_resolver = ExtrasResolver(settings_manager)

    def get_target_dir(self) -> str:
        """
        Get the target directory for package installations.

        Returns:
            The absolute path to the package cache directory.
        """
        return os.path.abspath(self.cache_dir)

    def ensure_cache_dir(self) -> str:
        """
        Ensure the cache directory exists.

        Returns:
            The absolute path to the cache directory.
        """
        target_dir = self.get_target_dir()
        os.makedirs(target_dir, exist_ok=True)
        return target_dir

    async def install_package(
        self, package_spec: str, target_dir: Optional[str] = None
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Install a package using pip and stream output.

        Args:
            package_spec: The package specification (e.g., "requests", "numpy>=1.20")
            target_dir: Target directory for installation. If None, uses cache_dir.

        Yields:
            Tuples of (output_type, content) where output_type is 'stdout', 'stderr',
            'success', or 'error'.
        """
        # Validate package spec
        is_valid, error = validate_package_spec(package_spec)
        if not is_valid:
            yield ("error", f"Invalid package spec: {error}")
            return

        # Determine target directory
        if target_dir is None:
            target_dir = self.ensure_cache_dir()
        else:
            target_dir = os.path.abspath(target_dir)
            os.makedirs(target_dir, exist_ok=True)

        # Build pip command using pip_command_builder
        cmd = self.pip_command_builder.build_install_command(
            package_spec, target_dir
        )

        logger.info(f"Running pip install: {' '.join(cmd)}")

        try:
            # Run pip as subprocess with async streaming
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            # Queue to collect output from both streams concurrently
            output_queue: asyncio.Queue = asyncio.Queue()

            async def read_stream(stream, stream_type):
                """Read lines from a stream and put them in the output queue."""
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    await output_queue.put(
                        (stream_type, line.decode("utf-8", errors="replace").rstrip())
                    )

            # Start reading both streams concurrently
            stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout"))
            stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr"))

            # Yield output as it becomes available
            async def yield_from_queue():
                """Yield items from the queue until both streams are done."""
                while not (stdout_task.done() and stderr_task.done()) or not output_queue.empty():
                    try:
                        item = await asyncio.wait_for(output_queue.get(), timeout=0.1)
                        yield item
                    except asyncio.TimeoutError:
                        continue

            async for stream_type, line in yield_from_queue():
                yield (stream_type, line)

            # Ensure both tasks are complete
            await asyncio.gather(stdout_task, stderr_task)

            # Wait for process to complete
            await process.wait()

            if process.returncode == 0:
                yield ("success", f"Successfully installed {package_spec}")
                yield ("path", target_dir)
            else:
                yield (
                    "error",
                    f"pip install failed with return code {process.returncode}",
                )

        except FileNotFoundError:
            yield ("error", "Python executable not found")
        except PermissionError:
            yield ("error", f"Permission denied when installing to {target_dir}")
        except Exception as e:
            logger.error(f"Failed to install package {package_spec}: {e}")
            yield ("error", f"Installation failed: {str(e)}")

    def get_installation_path(self) -> str:
        """
        Get the installation path for packages.

        Returns:
            The absolute path to the package installation directory.
        """
        return self.get_target_dir()

    async def get_available_versions(self, package_name: str) -> List[str]:
        """
        Query for available versions of a package using multi-index search.
        
        Delegates to VersionResolver which searches primary first,
        then secondaries one by one until results found.
        
        Args:
            package_name: The package name to query.
            
        Returns:
            List of version strings sorted descending, or empty list on error.
        """
        return await self.version_resolver.get_available_versions(package_name)

    async def get_package_extras(
        self, package_name: str, version: Optional[str] = None
    ) -> List[str]:
        """
        Query for available extras of a package using multi-index search.
        
        Delegates to ExtrasResolver which searches primary first,
        then secondaries one by one until results found.
        
        Args:
            package_name: The package name to query.
            version: Specific version to query. If None, uses latest version.
            
        Returns:
            List of extra names, or empty list if none or on error.
        """
        return await self.extras_resolver.get_package_extras(package_name, version)

    async def get_package_info(self, package_name: str) -> Dict[str, str]:
        """
        Get package info including latest version and description.
        
        Uses PyPI JSON API: https://pypi.org/pypi/<package>/json
        
        Args:
            package_name: The package name to query.
            
        Returns:
            Dictionary with keys: "name", "latest_version", "summary"
            Returns dict with error key if request fails.
        """
        if aiohttp is None:
            logger.error("aiohttp not installed, cannot query PyPI API")
            return {"error": "aiohttp not installed"}
        
        try:
            url = f"https://pypi.org/pypi/{package_name}/json"
            
            logger.info(f"Querying package info for {package_name} from PyPI")
            
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as response:
                    if response.status == 404:
                        return {"error": f"Package '{package_name}' not found on PyPI"}
                    elif response.status != 200:
                        return {"error": f"PyPI API returned status {response.status}"}
                    
                    data = await response.json()
                    info = data.get("info", {})
                    
                    return {
                        "name": info.get("name", package_name),
                        "latest_version": info.get("version", ""),
                        "summary": info.get("summary", "")
                    }
                    
        except asyncio.TimeoutError:
            logger.error(f"Timeout querying PyPI for {package_name}")
            return {"error": "Request timed out"}
        except Exception as e:
            logger.error(f"Failed to query package info for {package_name}: {e}")
            return {"error": str(e)}

    async def install_package_to_cache(
        self,
        package_name: str,
        version: str,
        extras: Optional[List[str]] = None,
        env: Optional[Dict[str, str]] = None
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Install a specific package version with extras to the cache.
        
        Installs to isolated UUID folder: .xpycode_packages/<uuid>/
        Uses --no-deps and --prefer-binary flags.
        Adds entry to SQLite cache on success.
        
        Args:
            package_name: The package name to install.
            version: The specific version to install.
            extras: Optional list of extras to install.
            env: Optional custom environment variables for subprocess.
            
        Yields:
            Tuples of (output_type, content) where output_type is 'stdout', 'stderr',
            'success', 'error', or 'path'.
        """
        # Build package spec with version and extras
        extras_str = ""
        if extras:
            extras_str = f"[{','.join(extras)}]"
        package_spec = f"{package_name}{extras_str}=={version}"
        
        # Validate package spec
        is_valid, error = validate_package_spec(package_spec)
        if not is_valid:
            yield ("error", f"Invalid package spec: {error}")
            return
        
        # Check if already cached FIRST
        extras_cache_key = ",".join(sorted(extras)) if extras else ""
        cached_path = self.package_cache.get_cached_package(
            package_name, version, extras_cache_key
        )
        if cached_path:
            yield ("stdout", f"Package already cached at {cached_path}")
            yield ("success", f"Using cached {package_spec}")
            yield ("cached", cached_path)
            return
        
        # Generate UUID for this installation using cache method
        install_uuid, target_dir = self.package_cache.generate_install_path()
        os.makedirs(target_dir, exist_ok=True)
        
        # Build pip command with --no-deps and --prefer-binary using pip_command_builder
        cmd = self.pip_command_builder.build_install_command(
            package_spec, target_dir, no_deps=True, prefer_binary=True
        )
        
        logger.info(f"Installing to cache: {' '.join(cmd)}")
        
        try:
            # Run pip as subprocess with async streaming
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=env,
            )
            
            # Queue to collect output from both streams concurrently
            output_queue: asyncio.Queue = asyncio.Queue()
            
            async def read_stream(stream, stream_type):
                """Read lines from a stream and put them in the output queue."""
                while True:
                    line = await stream.readline()
                    if not line:
                        break
                    await output_queue.put(
                        (stream_type, line.decode("utf-8", errors="replace").rstrip())
                    )
            
            # Start reading both streams concurrently
            stdout_task = asyncio.create_task(read_stream(process.stdout, "stdout"))
            stderr_task = asyncio.create_task(read_stream(process.stderr, "stderr"))
            
            # Yield output as it becomes available
            async def yield_from_queue():
                """Yield items from the queue until both streams are done."""
                while not (stdout_task.done() and stderr_task.done()) or not output_queue.empty():
                    try:
                        item = await asyncio.wait_for(output_queue.get(), timeout=0.1)
                        yield item
                    except asyncio.TimeoutError:
                        continue
            
            async for stream_type, line in yield_from_queue():
                yield (stream_type, line)
            
            # Ensure both tasks are complete
            await asyncio.gather(stdout_task, stderr_task)
            
            # Wait for process to complete
            await process.wait()
            
            if process.returncode == 0:
                # Add to cache database with UUID
                self.package_cache.add_cached_package(
                    install_uuid,  # NEW: pass UUID as first parameter
                    package_name,
                    version,
                    extras_cache_key,
                    self.package_cache.get_current_platform(),
                    self.package_cache.get_python_version(),
                    target_dir  # This is now the UUID-based path
                )
                yield ("success", f"Successfully installed {package_spec} to cache")
                yield ("path", target_dir)
            else:
                yield (
                    "error",
                    f"pip install failed with return code {process.returncode}",
                )
                
        except FileNotFoundError:
            yield ("error", "Python executable not found")
        except PermissionError:
            yield ("error", f"Permission denied when installing to {target_dir}")
        except Exception as e:
            logger.error(f"Failed to install package {package_spec}: {e}")
            yield ("error", f"Installation failed: {str(e)}")

    async def install_package_no_deps(
        self,
        package_name: str,
        version: str,
        extras: Optional[List[str]] = None
    ) -> AsyncGenerator[Tuple[str, str], None]:
        """
        Install a package without dependencies to versioned cache folder.
        
        Uses: pip install --no-deps --prefer-binary --target <cache>/<name>/<version>
        This is essentially an alias for install_package_to_cache, which already
        uses --no-deps flag.
        
        Args:
            package_name: The package name to install.
            version: The specific version to install.
            extras: Optional list of extras to install.
            
        Yields:
            Tuples of (output_type, content) where output_type is 'stdout', 'stderr',
            'success', 'error', or 'path'. Final yield is ('path', install_path) on success.
        """
        # Delegate to install_package_to_cache which already implements --no-deps
        async for output_type, content in self.install_package_to_cache(
            package_name, version, extras
        ):
            yield (output_type, content)
