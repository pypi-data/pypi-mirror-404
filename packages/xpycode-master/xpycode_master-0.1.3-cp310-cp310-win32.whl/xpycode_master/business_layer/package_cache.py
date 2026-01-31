"""
Package Cache - SQLite database for tracking cached packages.

This module provides:
- SQLite database schema for package cache
- PackageCache class for CRUD operations
- Platform and Python version detection
- Package name normalization
"""

import logging
import os
import platform
import re
import sqlite3
import sys
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Tuple

# Configure logging
from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


class PackageCache:
    """
    Manages SQLite database for tracking cached packages.
    
    The cache stores packages installed to isolated folders with metadata
    about their platform, Python version, and extras.
    """
    
    # Default database path relative to cache directory
    DEFAULT_DB_NAME = "cache.db"
    
    def __init__(self, db_path: Optional[str] = None, cache_dir: Optional[str] = None):
        """
        Initialize the PackageCache.
        
        Args:
            db_path: Path to SQLite database file. If None, defaults to
                    .xpycode_packages/cache.db in the current directory.
            cache_dir: Base directory for package cache. Used to determine
                      default db_path if db_path is None.
        """
        if db_path is None:
            # Use cache_dir if provided, otherwise use current directory
            base_dir = cache_dir or os.getcwd()
            cache_folder = os.path.join(base_dir, ".xpycode_packages")
            db_path = os.path.join(cache_folder, self.DEFAULT_DB_NAME)
        
        self.db_path = os.path.abspath(db_path)
        
        # Ensure database directory exists
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._init_database()
    
    def _init_database(self):
        """Initialize the database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            
            # Check if packages table exists and has uuid column
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='packages'")
            table_exists = cursor.fetchone() is not None
            
            if table_exists:
                # Check if uuid column exists
                cursor.execute("PRAGMA table_info(packages)")
                columns = [row[1] for row in cursor.fetchall()]
                if 'uuid' not in columns:
                    logger.info("Migrating database schema to add uuid column")
                    # Add uuid column to existing table
                    cursor.execute("ALTER TABLE packages ADD COLUMN uuid TEXT")
                    # Generate unique UUIDs for each existing entry
                    cursor.execute("SELECT id FROM packages WHERE uuid IS NULL")
                    rows = cursor.fetchall()
                    for row in rows:
                        pkg_id = row[0]
                        cursor.execute("UPDATE packages SET uuid = ? WHERE id = ?", (str(uuid.uuid4()), pkg_id))
                    conn.commit()
            
            # Create table with uuid column
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS packages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    uuid TEXT NOT NULL UNIQUE,
                    name TEXT NOT NULL,
                    version TEXT NOT NULL,
                    extras TEXT,
                    platform TEXT NOT NULL,
                    python_version TEXT NOT NULL,
                    path TEXT NOT NULL,
                    installed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(name, version, extras, platform, python_version)
                )
            """)
            conn.commit()
            logger.info(f"Initialized package cache database at {self.db_path}")
        except sqlite3.Error as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
        finally:
            conn.close()
    
    def normalize_package_name(self, name: str) -> str:
        """
        Normalize package name according to PEP 503.
        
        Converts to lowercase and replaces [-_.] with hyphens.
        
        Args:
            name: Package name to normalize.
            
        Returns:
            Normalized package name.
        """
        # Convert to lowercase and replace separators with hyphens per PEP 503
        normalized = re.sub(r"[-_.]+", "-", name.lower())
        return normalized
    
    def get_current_platform(self) -> str:
        """
        Detect the current platform.
        
        Returns:
            Platform string (e.g., "win_amd64", "linux_x86_64", "macosx_11_0_arm64").
        """
        system = platform.system().lower()
        machine = platform.machine().lower()
        
        if system == "windows":
            # Map common Windows architectures
            if machine in ("amd64", "x86_64"):
                return "win_amd64"
            elif machine in ("i386", "i686", "x86"):
                return "win32"
            else:
                return f"win_{machine}"
        elif system == "linux":
            # Map common Linux architectures
            if machine in ("x86_64", "amd64"):
                return "linux_x86_64"
            elif machine in ("i386", "i686"):
                return "linux_i686"
            elif machine.startswith("arm") or machine.startswith("aarch"):
                return f"linux_{machine}"
            else:
                return f"linux_{machine}"
        elif system == "darwin":
            # macOS
            mac_ver = platform.mac_ver()[0]
            if mac_ver:
                parts = mac_ver.split(".")
                major = parts[0] if len(parts) > 0 else "11"
                minor = parts[1] if len(parts) > 1 else "0"
            else:
                major, minor = "11", "0"
            
            if machine == "arm64":
                return f"macosx_{major}_{minor}_arm64"
            else:
                return f"macosx_{major}_{minor}_x86_64"
        else:
            # Fallback for other systems
            return f"{system}_{machine}"
    
    def get_python_version(self) -> str:
        """
        Get the current Python version (major.minor).
        
        Returns:
            Python version string (e.g., "3.11", "3.12").
        """
        return f"{sys.version_info.major}.{sys.version_info.minor}"
    
    def generate_install_path(self) -> Tuple[str, str]:
        """
        Generate a new UUID and return the full path for installation.
        
        Returns:
            Tuple of (uuid, full_path) where:
            - uuid is a new UUID string for the installation folder
            - full_path is the complete path: <cache_base>/<uuid>
        """
        install_uuid = str(uuid.uuid4())
        cache_base = os.path.dirname(self.db_path)
        path = os.path.join(cache_base, install_uuid)
        return install_uuid, path
    
    def get_cached_package(
        self,
        name: str,
        version: str,
        extras: Optional[str] = None,
        platform: Optional[str] = None,
        python_version: Optional[str] = None
    ) -> Optional[str]:
        """
        Check if a package is cached and return its path.
        
        Args:
            name: Package name (will be normalized).
            version: Package version.
            extras: Comma-separated extras or None/empty string.
            platform: Platform string. If None, uses current platform.
            python_version: Python version. If None, uses current version.
            
        Returns:
            Absolute path to the cached package, or None if not found.
        """
        normalized_name = self.normalize_package_name(name)
        extras = extras or ""
        platform = platform or self.get_current_platform()
        python_version = python_version or self.get_python_version()
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT path FROM packages
                WHERE name = ? AND version = ? AND extras = ? 
                      AND platform = ? AND python_version = ?
                """,
                (normalized_name, version, extras, platform, python_version)
            )
            row = cursor.fetchone()
            if row:
                path = row[0]
                # Verify path still exists
                if os.path.exists(path):
                    return path
                else:
                    # Path no longer exists, remove from cache
                    logger.warning(f"Cached package path no longer exists: {path}")
                    self.remove_cached_package(
                        name, version, extras, platform, python_version
                    )
            return None
        except sqlite3.Error as e:
            logger.error(f"Database error when querying package: {e}")
            return None
        finally:
            conn.close()
    
    def add_cached_package(
        self,
        install_uuid: str,
        name: str,
        version: str,
        extras: Optional[str],
        platform: Optional[str],
        python_version: Optional[str],
        path: str
    ):
        """
        Add a package to the cache.
        
        Args:
            install_uuid: UUID for this installation folder.
            name: Package name (will be normalized).
            version: Package version.
            extras: Comma-separated extras or None/empty string.
            platform: Platform string. If None, uses current platform.
            python_version: Python version. If None, uses current version.
            path: Absolute path to the installed package folder.
        """
        normalized_name = self.normalize_package_name(name)
        extras = extras or ""
        platform = platform or self.get_current_platform()
        python_version = python_version or self.get_python_version()
        path = os.path.abspath(path)
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO packages
                (uuid, name, version, extras, platform, python_version, path, installed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    install_uuid,
                    normalized_name,
                    version,
                    extras,
                    platform,
                    python_version,
                    path,
                    datetime.now().isoformat()
                )
            )
            conn.commit()
            logger.info(
                f"Added package to cache: {normalized_name}=={version} "
                f"(extras={extras}, platform={platform}, py={python_version})"
            )
        except sqlite3.Error as e:
            logger.error(f"Failed to add package to cache: {e}")
            raise
        finally:
            conn.close()
    
    def remove_cached_package(
        self,
        name: str,
        version: str,
        extras: Optional[str] = None,
        platform: Optional[str] = None,
        python_version: Optional[str] = None
    ):
        """
        Remove a package from the cache.
        
        Args:
            name: Package name (will be normalized).
            version: Package version.
            extras: Comma-separated extras or None/empty string.
            platform: Platform string. If None, uses current platform.
            python_version: Python version. If None, uses current version.
        """
        normalized_name = self.normalize_package_name(name)
        extras = extras or ""
        platform = platform or self.get_current_platform()
        python_version = python_version or self.get_python_version()
        
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM packages
                WHERE name = ? AND version = ? AND extras = ?
                      AND platform = ? AND python_version = ?
                """,
                (normalized_name, version, extras, platform, python_version)
            )
            conn.commit()
            if cursor.rowcount > 0:
                logger.info(
                    f"Removed package from cache: {normalized_name}=={version}"
                )
        except sqlite3.Error as e:
            logger.error(f"Failed to remove package from cache: {e}")
            raise
        finally:
            conn.close()
    
    def list_cached_packages(self) -> List[Dict]:
        """
        List all cached packages.
        
        Returns:
            List of dictionaries with package information:
            [
                {
                    "id": 1,
                    "uuid": "b6e7e26e-b3c7-43f2-88fb-1de61ad51cc1",
                    "name": "requests",
                    "version": "2.31.0",
                    "extras": "",
                    "platform": "win_amd64",
                    "python_version": "3.11",
                    "path": "/path/to/package",
                    "installed_at": "2024-01-01T12:00:00"
                },
                ...
            ]
        """
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, uuid, name, version, extras, platform, python_version, 
                       path, installed_at
                FROM packages
                ORDER BY installed_at DESC
                """
            )
            rows = cursor.fetchall()
            packages = []
            for row in rows:
                packages.append({
                    "id": row[0],
                    "uuid": row[1],
                    "name": row[2],
                    "version": row[3],
                    "extras": row[4],
                    "platform": row[5],
                    "python_version": row[6],
                    "path": row[7],
                    "installed_at": row[8]
                })
            return packages
        except sqlite3.Error as e:
            logger.error(f"Failed to list cached packages: {e}")
            return []
        finally:
            conn.close()
