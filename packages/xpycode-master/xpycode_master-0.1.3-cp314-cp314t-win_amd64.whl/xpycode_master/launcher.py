"""
XPyCode Master Launcher

Main launcher module that orchestrates all components:
- Addin server launcher
- Excel manifest installation
- Business layer server

Note: Single instance lock is now managed by the watchdog process.

Usage:
    python -m xpycode_master.launcher [options]
"""

import argparse
import atexit
import json
import os
import uuid
import shutil
import signal
import subprocess
import sys
import io
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime

# Import port configuration
from .config import ADDIN_PORTS, SERVER_PORTS, DOCS_PORTS, find_available_port
from .addin_launcher.server_manager import AddinServerManager
from .docs_launcher.server_manager import DocsServerManager
from .logging_config import setup_logging_master, get_logger, DEFAULT_LOG_FORMAT, fix_windows_console_encoding

# Fix Windows console encoding for Unicode characters
fix_windows_console_encoding()

# Module-level logger (will be properly configured when main() is called)
# For manifest functions that may be called during setup, we use print as fallback
_manifest_logger = None

def _get_manifest_logger():
    """Get logger for manifest operations, with fallback to print."""
    global _manifest_logger
    if _manifest_logger is None:
        try:
            _manifest_logger = get_logger(__name__)
        except Exception:
            # If logging not yet configured, return a dummy logger
            import logging
            _manifest_logger = logging.getLogger(__name__)
    return _manifest_logger


def get_manifest_info_path() -> Path:
    """Get the path to the manifest info file."""
    xpycode_dir = Path.home() / ".xpycode"
    xpycode_dir.mkdir(parents=True, exist_ok=True)
    return xpycode_dir / MANIFEST_INFO_FILENAME


def load_manifest_info() -> Optional[dict]:
    """Load existing manifest info if it exists."""
    info_path = get_manifest_info_path()
    if info_path.exists():
        try:
            with open(info_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            _get_manifest_logger().warning(f"Could not read manifest info: {e}")
    return None


def save_manifest_info(mode: str, addin_port: Optional[int], external_url: Optional[str], 
                       version: str, manifest_path: Path) -> None:
    """Save current manifest configuration."""
    info = {
        "mode": mode,
        "addin_port": addin_port,
        "external_url": external_url,
        "version": version,
        "manifest_path": str(manifest_path),
        "last_updated": datetime.now().isoformat()
    }
    info_path = get_manifest_info_path()
    try:
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(info, f, indent=2)
        _get_manifest_logger().info(f"Saved manifest info to: {info_path}")
    except (IOError, OSError) as e:
        _get_manifest_logger().warning(f"Could not save manifest info: {e}")


def should_clear_cache(old_info: Optional[dict], new_mode: str, new_port: Optional[int], 
                       new_external_url: Optional[str], new_version: str) -> bool:
    """
    Determine if the Office add-in cache should be cleared.
    
    Returns True if:
    - Mode changed (local <-> external)
    - Port changed (in local mode)
    - External URL changed (in external mode)
    - Version changed (in external mode only)
    
    Returns False if:
    - First time (no previous info) - don't flush cache for new users
    - No changes detected
    """
    if old_info is None:
        return False  # First time setup - don't flush cache
    
    # Mode changed
    if old_info.get("mode") != new_mode:
        return True
    
    # In local mode, port changed
    if new_mode == "local" and old_info.get("addin_port") != new_port:
        return True
    
    # In external mode, URL changed (includes version in URL)
    if new_mode == "external" and old_info.get("external_url") != new_external_url:
        return True
    
    # Version changed (relevant for external mode where version is in the URL)
    if new_mode == "external" and old_info.get("version") != new_version:
        return True
    
    return False


def get_wef_cache_folder() -> Optional[Path]:
    """
    Get the Office add-in cache folder (Wef) based on platform.
    
    Returns:
        Path to Wef folder, or None if not applicable/found
    """
    if sys.platform == 'win32':
        # Windows: %LOCALAPPDATA%\Microsoft\Office\16.0\Wef\
        appdata = os.environ.get('LOCALAPPDATA', '')
        if appdata:
            return Path(appdata) / "Microsoft" / "Office" / "16.0" / "Wef"
        return None
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Containers/com.microsoft.Excel/Data/Documents/wef/
        return Path.home() / "Library" / "Containers" / "com.microsoft.Excel" / "Data" / "Documents" / "wef"
    # Linux: No standard location
    return None


def clear_office_addin_cache() -> bool:
    """
    Clear the Office add-in cache (Wef folder).
    
    Warning: This clears cache for ALL add-ins, not just XPyCode.
    
    This function is called when:
    - Mode changes (local <-> external)
    - Port changes (in local mode)
    - External URL or version changes (in external mode)
    
    NOT called on first-time setup to avoid disrupting existing users.
    
    Returns:
        True if cache was cleared successfully, False otherwise
    """
    logger = _get_manifest_logger()
    wef_folder = get_wef_cache_folder()
    
    if wef_folder is None:
        logger.info("No Wef cache folder location for this platform")
        return False
    
    if not wef_folder.exists():
        logger.info(f"Wef cache folder does not exist: {wef_folder}")
        return True  # Nothing to clear
    
    logger.info(f"Clearing Office add-in cache: {wef_folder}")
    logger.warning("Note: This clears cache for ALL Office add-ins, not just XPyCode")
    
    try:
        # Clear contents of the folder, but keep the folder itself
        for item in wef_folder.iterdir():
            try:
                if item.is_symlink():
                    # Remove symlink itself, don't follow it
                    item.unlink()
                elif item.is_file():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
            except Exception as e:
                logger.warning(f"Could not delete {item}: {e}")
        
        logger.info("Office add-in cache cleared successfully")
        print("=" * 50)
        print("INFO:\tOffice add-in cache cleared")
        print("INFO:\tPlease restart Excel if it's running")
        print("=" * 50)
        return True
    except Exception as e:
        logger.error(f"Failed to clear Office add-in cache: {e}")
        return False

# Constants
MANIFEST_FILENAME = "xpycode_manifest.xml"
MANIFEST_INFO_FILENAME = "manifest_info.json"
OFFICE_VERSION = "16.0"
REGISTRY_BASE = fr"Software\Microsoft\Office\{OFFICE_VERSION}\WEF"
REGISTRY_TRUSTED_CATALOGS = fr"{REGISTRY_BASE}\TrustedCatalogs"
REGISTRY_DEVELOPER = fr"{REGISTRY_BASE}\Developer"


def start_addin_server(use_compiled: bool = True, addin_port: int = 3000, server_port: int = 8000, 
                       watchdog_port: int = 0, auth_token: str = "") -> subprocess.Popen:
    """
    Start the addin server in a subprocess.
    
    Args:
        use_compiled: If True, use compiled binary. If False, use Node.js.
        addin_port: Port for the addin HTTPS server
        server_port: Port for the business layer server
        watchdog_port: Port for the watchdog HTTP API
        auth_token: Auth token for watchdog API
    
    Returns:
        Popen object for process management
    """
    cmd = [
        sys.executable, "-m", "xpycode_master.addin_launcher",
        "start",
        "--port", str(addin_port),
        "--server-port", str(server_port),
        "--foreground",
    ]
    
    if use_compiled:
        cmd.append("--prod")
    else:
        cmd.append("--dev")
    
    # Add watchdog info
    if watchdog_port:
        cmd.extend(["--watchdog-port", str(watchdog_port)])
    if auth_token:
        cmd.extend(["--auth-token", auth_token])
    
    add_params={}
    if sys.platform=='win32':
        add_params['creationflags']=subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        add_params['preexec_fn']=os.setsid
    
    
    return subprocess.Popen(cmd,**add_params)


def get_excel_addin_folder() -> Path:
    """
    Get the Excel add-ins folder based on the platform.
    """
    if sys.platform == 'win32':
        # Windows: %LOCALAPPDATA%\Microsoft\Office\16.0\Wef\
        appdata = os.environ.get('LOCALAPPDATA', '')
        return Path(appdata) / "Microsoft" / "Office" / "16.0" / "Wef"
    elif sys.platform == 'darwin':
        # macOS: ~/Library/Containers/com.microsoft.Excel/Data/Documents/wef
        return Path.home() / "Library" / "Containers" / "com.microsoft.Excel" / "Data" / "Documents" / "wef"
    else:
        # Linux: Not officially supported by Excel, but provide a path
        return Path.home() / ".config" / "microsoft-office" / "wef"


def get_source_manifest_path() -> Path:
    """
    Get the path to the source manifest file.
    
    Returns:
        Path to manifest.xml in the addin_launcher/bin/manifest folder
    
    Raises:
        FileNotFoundError: If manifest file doesn't exist
    """
    package_dir = Path(__file__).parent
    source_manifest = package_dir / "addin_launcher" / "bin" / "manifest" / "manifest.xml"
    
    if not source_manifest.exists():
        raise FileNotFoundError(f"Manifest not found: {source_manifest}")
    
    return source_manifest


def install_manifest(source_manifest: Optional[Path] = None) -> Path:
    """
    Copy the manifest to Excel's add-in folder.
    
    Args:
        source_manifest: Path to manifest. If None, uses addin_launcher/bin/manifest/manifest.xml
    
    Returns:
        Path to installed manifest
    """
    if source_manifest is None:
        source_manifest = get_source_manifest_path()
    
    # Get destination folder
    dest_folder = get_excel_addin_folder()
    dest_folder.mkdir(parents=True, exist_ok=True)
    
    # Copy with a recognizable name
    dest_manifest = dest_folder / MANIFEST_FILENAME
    shutil.copy2(source_manifest, dest_manifest)
    
    _get_manifest_logger().info(f"Manifest installed to: {dest_manifest}")
    return dest_manifest


def get_xpycode_manifest_folder() -> Path:
    """Get the XPyCode manifest folder in user profile."""
    manifest_folder = Path.home() / ".xpycode" / "manifest"
    manifest_folder.mkdir(parents=True, exist_ok=True)
    return manifest_folder


def local_path_to_unc(local_path: Path) -> str:
    """
    Convert a local path to UNC style for TrustedCatalogs.
    
    Example:
        C:\\Users\\john\\.xpycode\\manifest
        becomes
        \\\\localhost\\c$\\Users\\john\\.xpycode\\manifest
    """
    path_str = str(local_path.resolve())
    
    # Check if it's a drive letter path (e.g., C:\...)
    if len(path_str) >= 2 and path_str[1] == ':':
        drive_letter = path_str[0].lower()
        rest_of_path = path_str[2:]  # Everything after "C:"
        # Convert to UNC: \\localhost\c$\...
        unc_path = f"\\\\localhost\\{drive_letter}${rest_of_path}"
        return unc_path
    
    # Already UNC or other format, return as-is
    return path_str


def find_existing_trusted_catalog() -> Optional[Tuple[str, str]]:
    """
    Find an existing TrustedCatalog with Flags=1.
    
    Returns:
        Tuple of (catalog_key_name, url) if found, None otherwise.
    """
    if sys.platform != 'win32':
        return None
    
    import winreg
    
    try:
        catalogs_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, REGISTRY_TRUSTED_CATALOGS)
    except OSError:
        # Registry key doesn't exist - no catalogs registered
        return None
    
    try:
        index = 0
        while True:
            try:
                subkey_name = winreg.EnumKey(catalogs_key, index)
                subkey_path = f"{REGISTRY_TRUSTED_CATALOGS}\\{subkey_name}"
                
                try:
                    subkey = winreg.OpenKey(winreg.HKEY_CURRENT_USER, subkey_path)
                    
                    # Check Flags value
                    try:
                        flags, _ = winreg.QueryValueEx(subkey, "Flags")
                        if flags == 1:
                            # Found a catalog with Flags=1, get the URL
                            try:
                                url, _ = winreg.QueryValueEx(subkey, "Url")
                                winreg.CloseKey(subkey)
                                winreg.CloseKey(catalogs_key)
                                return (subkey_name, url)
                            except OSError:
                                # Url value doesn't exist, skip this catalog
                                pass
                    except OSError:
                        # Flags value doesn't exist, skip this catalog
                        pass
                    
                    winreg.CloseKey(subkey)
                except OSError:
                    # Can't open this subkey, skip it
                    pass
                
                index += 1
            except OSError:
                # No more subkeys to enumerate
                break
    finally:
        winreg.CloseKey(catalogs_key)
    
    return None


def unc_to_local_path(unc_path: str) -> Optional[Path]:
    """
    Convert UNC path back to local path for file operations.
    
    Example:
        \\\\localhost\\c$\\Users\\john\\.xpycode\\manifest
        or
        //localhost/c$/Users/john/.xpycode/manifest
        becomes
        C:\\Users\\john\\.xpycode\\manifest
    """
    # Handle \\localhost\X$\... or //localhost/X$/... format
    if unc_path.startswith("\\\\localhost\\") or unc_path.startswith("//localhost/"):
        # Normalize slashes
        normalized = unc_path.replace("/", "\\")
        # Remove \\localhost\ prefix
        rest = normalized[len("\\\\localhost\\"):]
        
        # Check for drive$ format (e.g., c$\...)
        if len(rest) >= 2 and rest[1] == '$':
            drive_letter = rest[0].upper()
            path_rest = rest[2:]  # Skip "c$"
            return Path(f"{drive_letter}:{path_rest}")
    
    # Try as regular path
    try:
        return Path(unc_path)
    except (ValueError, OSError):
        # Invalid path format
        return None


def copy_manifest_to_catalog(source_manifest: Path, catalog_url: str) -> bool:
    """
    Try to copy manifest to an existing catalog folder.
    
    Returns:
        True if successful, False otherwise.
    """
    try:
        catalog_path = unc_to_local_path(catalog_url)
        if catalog_path is None:
            return False
        
        if not catalog_path.exists():
            return False
        
        dest_manifest = catalog_path / MANIFEST_FILENAME
        shutil.copy2(source_manifest, dest_manifest)
        _get_manifest_logger().info(f"Manifest copied to existing catalog: {dest_manifest}")
        return True
    except Exception as e:
        _get_manifest_logger().warning(f"Failed to copy to existing catalog: {e}")
        return False


def register_in_developer_fallback(manifest_path: Path):
    r"""
    Fallback: Register manifest in WEF\Developer.
    This is less persistent but works without admin.
    """
    import winreg
    
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_DEVELOPER)
        winreg.SetValueEx(key, "xpycode", 0, winreg.REG_SZ, str(manifest_path))
        winreg.CloseKey(key)
        _get_manifest_logger().info(f"Manifest registered in Developer path (fallback): {manifest_path}")
    except Exception as e:
        _get_manifest_logger().warning(f"Could not register in Developer path: {e}")

def unregister_in_developer_fallback():
    r"""
    Fallback: Register manifest in WEF\Developer.
    This is less persistent but works without admin.
    """
    import winreg
    
    try:
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_DEVELOPER)
        winreg.DeleteValue(key, "xpycode")
        _get_manifest_logger().info(f"Manifest unregistered in Developer path (fallback)")
    except Exception as e:
        _get_manifest_logger().warning(f"Could not unregister in Developer path: {e}")


def create_trusted_catalog(manifest_folder: Path):
    """
    Create a new TrustedCatalog entry for the manifest folder.
    """
    import uuid
    import winreg
    
    # Generate a new GUID for the catalog
    catalog_id = str(uuid.uuid4())
    catalog_key_path = f"{REGISTRY_TRUSTED_CATALOGS}\\{catalog_id}"
    
    # Convert local path to UNC style
    unc_url = local_path_to_unc(manifest_folder)
    
    logger = _get_manifest_logger()
    
    try:
        # Create the TrustedCatalogs key if it doesn't exist
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, REGISTRY_TRUSTED_CATALOGS)
        
        # Create the catalog subkey
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, catalog_key_path)
        
        # Set values
        winreg.SetValueEx(key, "Id", 0, winreg.REG_SZ, catalog_id)
        winreg.SetValueEx(key, "Url", 0, winreg.REG_SZ, unc_url)
        winreg.SetValueEx(key, "Flags", 0, winreg.REG_DWORD, 1)
        
        winreg.CloseKey(key)
        
        logger.info(f"Created TrustedCatalog:")
        logger.info(f"  Id: {catalog_id}")
        logger.info(f"  Url: {unc_url}")
        logger.info(f"  Flags: 1")
        
    except Exception as e:
        logger.warning(f"Could not create TrustedCatalog: {e}")
        raise


def copy_manifest_to_folder(source_manifest: Path, dest_folder: Path, filename: str = MANIFEST_FILENAME) -> Path:
    """
    Copy manifest to a destination folder.
    
    Args:
        source_manifest: Source manifest file path
        dest_folder: Destination folder path
        filename: Target filename (default: xpycode_manifest.xml)
    
    Returns:
        Path to the copied manifest
    """
    dest_manifest = dest_folder / filename
    shutil.copy2(source_manifest, dest_manifest)
    return dest_manifest


def prepare_manifest(source_manifest: Path, dest_manifest: Path, addin_port: int) -> None:
    """
    Process manifest template and replace port placeholders.
    
    Args:
        source_manifest: Path to the source manifest template
        dest_manifest: Path where the processed manifest will be saved
        addin_port: Port number for the addin server
    """
    # Read the manifest template
    content = source_manifest.read_text(encoding='utf-8')
    
    # Replace the port placeholder
    from . import __version__ as xpycode_version
    content = content.replace('{{ADDIN_PORT}}', str(addin_port)).replace('{{XPYCODE_VERSION}}', xpycode_version)
    
    # Write the processed manifest
    dest_manifest.write_text(content, encoding='utf-8')
    
    # Print manifest path for user reference
    print('='*50)
    print(f"PATHS:\tManifest file: {dest_manifest}")
    print('='*50)


def prepare_external_manifest(source_manifest: Path, dest_manifest: Path) -> None:
    """
    Process manifest template for external addin hosting.
    Replaces https://localhost:{{ADDIN_PORT}} with the external addin URL.
    
    Args:
        source_manifest: Path to the source manifest template
        dest_manifest: Path where the processed manifest will be saved
    """
    from .config import get_external_addin_url
    from . import __version__ as xpycode_version
    
    # Read the manifest template
    content = source_manifest.read_text(encoding='utf-8')
    
    # Get the external URL
    external_url = get_external_addin_url()
    
    # Replace localhost URLs with external URL
    # Pattern: https://localhost:{{ADDIN_PORT}}
    content = content.replace('https://localhost:{{ADDIN_PORT}}', external_url)
    
    # Also replace version placeholder if present
    content = content.replace('{{XPYCODE_VERSION}}', xpycode_version)
    
    # Write the processed manifest
    dest_manifest.write_text(content, encoding='utf-8')
    
    # Print manifest path for user reference
    print('='*50)
    print(f"PATHS:\tExternal manifest file: {dest_manifest}")
    print(f"PATHS:\tUsing external addin URL: {external_url}")
    print('='*50)


def register_manifest_with_excel(source_manifest: Path, addin_port: int):
    """
    Register the manifest with Excel using the best available method.
    
    Processes the manifest template by replacing port placeholders, then registers it.
    
    Args:
        source_manifest: Path to the manifest template file
        addin_port: Port number for the addin server (or -1 for external mode)
    
    Strategy:
    1. Check for existing TrustedCatalog with Flags=1
    2. If found: try copying manifest there
       - If copy fails: fallback to Developer path
    3. If not found: create new TrustedCatalog
    """
    logger = _get_manifest_logger()
    
    # Import version
    from . import __version__
    from .config import get_external_addin_url
    
    # Determine mode and settings
    is_external = (addin_port == -1)
    mode = "external" if is_external else "local"
    external_url = get_external_addin_url() if is_external else None
    port_for_info = None if is_external else addin_port
    
    # Check if we need to clear cache
    old_info = load_manifest_info()
    if should_clear_cache(old_info, mode, port_for_info, external_url, __version__):
        reason = "first time setup" if old_info is None else "configuration changed"
        logger.info(f"Cache clear needed: {reason}")
        if old_info:
            logger.info(f"  Previous: mode={old_info.get('mode')}, port={old_info.get('addin_port')}, url={old_info.get('external_url')}, version={old_info.get('version')}")
        logger.info(f"  Current: mode={mode}, port={port_for_info}, url={external_url}, version={__version__}")
        clear_office_addin_cache()
    
    # Get the xpycode manifest folder
    xpycode_folder = get_xpycode_manifest_folder()
    dest_manifest = xpycode_folder / MANIFEST_FILENAME
    
    # Process the manifest template and write to destination
    if addin_port == -1:
        # External addin mode
        prepare_external_manifest(source_manifest, dest_manifest)
        logger.info("Manifest processed for external addin mode")
    else:
        # Local addin mode
        prepare_manifest(source_manifest, dest_manifest, addin_port)
        logger.info(f"Manifest processed with addin port: {addin_port}")

    if sys.platform != 'win32':
        logger.info("Automatic Excel registration only supported on Windows.")
        logger.info(f"Please manually sideload the manifest: {dest_manifest}")
        # Save manifest info before returning
        save_manifest_info(mode, port_for_info, external_url, __version__, dest_manifest)
        return
    
    import winreg


    # Step 1: Check for existing TrustedCatalog with Flags=1
    existing_catalog = find_existing_trusted_catalog()
    
    if existing_catalog:
        catalog_name, catalog_url = existing_catalog
        logger.info(f"Found existing TrustedCatalog: {catalog_url}")
        
        # Step 2.1: Try copying processed manifest to existing catalog
        catalog_path = unc_to_local_path(catalog_url)
        if catalog_path and catalog_path.exists():
            try:
                catalog_manifest = catalog_path / MANIFEST_FILENAME
                if catalog_manifest != dest_manifest:
                    shutil.copy2(dest_manifest, catalog_manifest)
                    logger.info(f"Manifest copied to existing catalog: {catalog_manifest}")
                logger.info("Add-in registered successfully using existing catalog.")
                unregister_in_developer_fallback()
                # Save manifest info before returning
                save_manifest_info(mode, port_for_info, external_url, __version__, dest_manifest)
                return
            except Exception as e:
                logger.warning(f"Failed to copy to existing catalog: {e}")
        
        # Step 2.2: Fallback to Developer path
        logger.info("Could not use existing catalog, falling back to Developer path...")
        register_in_developer_fallback(dest_manifest)
        # Save manifest info before returning
        save_manifest_info(mode, port_for_info, external_url, __version__, dest_manifest)
        return
    
    # Step 3: No existing catalog - create new TrustedCatalog
    logger.info("No existing TrustedCatalog found, creating new one...")
    logger.info(f"Manifest copied to: {dest_manifest}")
    
    try:
        create_trusted_catalog(xpycode_folder)
        logger.info("Add-in registered successfully with new TrustedCatalog.")
        logger.info("Please restart Excel for changes to take effect.")
    except Exception:
        # If TrustedCatalog creation fails, fall back to Developer
        logger.info("TrustedCatalog creation failed, falling back to Developer path...")
        register_in_developer_fallback(dest_manifest)
    
    # Save manifest info after registration
    save_manifest_info(mode, port_for_info, external_url, __version__, dest_manifest)


def main():
    """
    Main entry point for XPyCode Master Launcher.
    
    Launches all components:
    1. Starts addin server (subprocess)
    2. Installs/updates Excel manifest
    3. Runs business layer server (main process)
    
    Note: Single instance lock is handled by watchdog process.
    """
    parser = argparse.ArgumentParser(description="XPyCode Master Launcher")
    parser.add_argument("--addin-port", type=int, default=0,
                        help="Port for addin server (auto-selected if not specified or 0)")
    parser.add_argument("--server-port", type=int, default=0,
                        help="Port for business layer server (auto-selected if not specified or 0)")
    parser.add_argument("--docs-port", type=int, default=0,
                        help="Port for documentation server (auto-selected if not specified or 0)")
    parser.add_argument("--watchdog-port", type=int, default=0,
                        help="Watchdog HTTP API port")
    parser.add_argument("--auth-token", type=str, default="",
                        help="Watchdog auth token")
    parser.add_argument("--dev", action="store_true", 
                        help="Use development mode (node server.js), default is compiled binary")
    parser.add_argument("--prod", action="store_true",
                        help="Use production mode (compiled binary)")
    parser.add_argument("--skip-manifest", action="store_true",
                        help="Skip manifest installation")
    
    # Logging arguments
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)"
    )
    parser.add_argument(
        "--log-format",
        type=str,
        default=None,
        help="Logging format string (default: see DEFAULT_LOG_FORMAT in logging_config.py)"
    )
    parser.add_argument(
        "--no-log-file",
        action="store_true",
        help="Disable logging to file (console only)"
    )
    parser.add_argument(
        "--log-to-console",
        action="store_true",
        help="Enable console logging output"
    )
    
    args = parser.parse_args()
    
    # Setup logging FIRST, before any other operations
    log_file = setup_logging_master(
        level=args.log_level,
        format_str=args.log_format,
        enable_file=not args.no_log_file,
        enable_console=args.log_to_console
    )
    
    # Get logger for this module
    logger = get_logger(__name__)
    
    logger.info("=" * 60)
    logger.info("XPyCode Master Launcher starting")
    logger.info(f"Log level: {args.log_level}")
    if log_file:
        logger.info(f"Log file: {log_file}")
    else:
        logger.info("File logging disabled")
    logger.info("=" * 60)
    
    # Default to compiled binary unless --dev is specified
    use_compiled = args.prod or not args.dev
    
    # Select addin port
    if args.addin_port == -1:
        # External addin mode - no local addin server
        addin_port = -1
        logger.info("External addin mode: using addin.xpycode.com")
    elif args.addin_port:
        addin_port = args.addin_port
        logger.info(f"Using specified addin port: {addin_port}")
    else:
        addin_port = find_available_port(ADDIN_PORTS)
        if addin_port is None:
            logger.error("No available ports for addin server")
            logger.error(f"Tried ports: {ADDIN_PORTS}")
            sys.exit(1)
        logger.info(f"Auto-selected addin port: {addin_port}")
    
    # Select server port
    if args.server_port:
        server_port = args.server_port
        logger.info(f"Using specified server port: {server_port}")
    else:
        server_port = find_available_port(SERVER_PORTS)
        if server_port is None:
            logger.error("No available ports for business layer server")
            logger.error(f"Tried ports: {SERVER_PORTS}")
            sys.exit(1)
        logger.info(f"Auto-selected server port: {server_port}")
    
    # Select docs port
    if args.docs_port:
        docs_port = args.docs_port
        logger.info(f"Using specified docs port: {docs_port}")
    else:
        docs_port = find_available_port(DOCS_PORTS)
        if docs_port is None:
            logger.error("No available ports for documentation server")
            logger.error(f"Tried ports: {DOCS_PORTS}")
            sys.exit(1)
        logger.info(f"Auto-selected docs port: {docs_port}")
    
    # Print discovered ports for watchdog to parse
    print('='*18+'PORT SELECTION'+'='*18)
    print(f"XPYCODE_PORTS:{json.dumps({'addin_port': addin_port, 'server_port': server_port, 'docs_port': docs_port})}")
    print('='*50)
    sys.stdout.flush()
    
    manager = None
    docs_manager = None
    hard_kill = lambda: None
    
    try:
        # 1. Start addin server (skip if external addin mode)
        if addin_port != -1:
            manager=AddinServerManager(
                use_compiled=use_compiled, 
                port=addin_port,
                server_port=server_port,
                watchdog_port=args.watchdog_port,
                auth_token=args.auth_token,
                docs_port=docs_port
            )
            manager.start()
            logger.info(f"Starting addin server on port {addin_port}...")
            logger.info(f"Addin server started (PID: {manager.pid})")
        else:
            logger.info("Skipping local addin server (external addin mode)")
        
        # 1b. Start documentation server
        if docs_port>-1: #docs will use external urls if docs_port==-1
            docs_manager = DocsServerManager(port=docs_port)
            try:
                docs_manager.start()
                logger.info(f"Documentation server started on port {docs_port} (PID: {docs_manager.pid})")
            except RuntimeError as e:
                logger.warning(f"Could not start documentation server: {e}")
                docs_manager = None
            except Exception as e:
                logger.error(f"Unexpected error starting documentation server: {e}", exc_info=True)
                docs_manager = None
        
        # 2. Install manifest (unless skipped)
        if not args.skip_manifest:
            try:
                # Get source manifest path
                source_manifest = get_source_manifest_path()
                
                # Register with Excel (handles processing and copying internally)
                register_manifest_with_excel(source_manifest, addin_port)
                logger.info(f"Manifest updated with ports: addin={addin_port}, server={server_port}")
            except Exception as e:
                logger.warning(f"Could not install manifest: {e}")
        
        # 3. Run business layer server in main process
        logger.info(f"Starting business layer server on port {server_port}...")
        try:
            from .business_layer import server
        except ImportError as e:
            logger.error(f"Failed to import business layer server: {e}")
            logger.error("Please install required dependencies: pip install fastapi uvicorn")
            raise
        
        def hard_kill():
            try:
                if manager:
                    manager.stop()
            except:
                pass
            try:
                if docs_manager:
                    docs_manager.stop()
            except:
                pass

        
        # Setup signal handlers for graceful shutdown
        def signal_handler(signum, frame):
            logger.info("Shutting down...")
            if manager:
                hard_kill()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        atexit.register(hard_kill)
        
        # Start the business layer server (blocking call)
        # Pass watchdog info and docs_port to business layer
        server.run_server(
            port=server_port,
            watchdog_port=args.watchdog_port,
            auth_token=args.auth_token,
            docs_port=docs_port
        )
        
    except Exception as e:
        logger.error(f"Error: {e}")
        raise
    finally:
        # Cleanup
        if hard_kill:
            hard_kill()


if __name__ == "__main__":
    main()
