"""
XPyCode Master Setup Script

This script handles Cython compilation of core modules for code protection and performance.
"""

import os
import sys
import platform
from pathlib import Path
from setuptools import setup, Extension
from setuptools.command.build_py import build_py
from Cython.Build import cythonize

# Modules to compile with Cython
CYTHON_MODULES = [
    "xpycode_master/python_server/kernel.py",
    "xpycode_master/python_server/xpycode/com_like.py",
    "xpycode_master/python_server/lsp_bridge.py",
    "xpycode_master/business_layer/dependency_resolver.py",
    "xpycode_master/business_layer/bl_master.py",
    "xpycode_master/business_layer/packages/package_index_client.py",
    "xpycode_master/business_layer/packages/handlers.py",
    "xpycode_master/business_layer/packages/manager.py",
    "xpycode_master/addin_launcher/server_manager.py",
    'xpycode_master/ide/gui/websocket_client.py',
]


CYTHON_MODULES_COMPLETE = [
    "xpycode_master/python_server/kernel.py",
    "xpycode_master/python_server/xpycode/com_like.py",
    "xpycode_master/python_server/lsp_bridge.py",
    "xpycode_master/python_server/event_manager.py",
    "xpycode_master/python_server/debugger.py",
    "xpycode_master/business_layer/dependency_resolver.py",
    "xpycode_master/business_layer/bl_master.py",
    "xpycode_master/business_layer/packages/package_index_client.py",
    "xpycode_master/business_layer/packages/handlers.py",
    "xpycode_master/business_layer/packages/manager.py",
    "xpycode_master/addin_launcher/server_manager.py",
    "xpycode_master/watchdog_xpc.py",
    'xpycode_master/ide/gui/advanced_actions.py',
    'xpycode_master/ide/gui/ai_login_widget.py',
    'xpycode_master/ide/gui/breakpoint_manager.py',
    'xpycode_master/ide/gui/debug_panel.py',
    'xpycode_master/ide/gui/editor.py',
    'xpycode_master/ide/gui/event_manager.py',
    'xpycode_master/ide/gui/function_publisher.py',
    'xpycode_master/ide/gui/icon_utils.py',
    'xpycode_master/ide/gui/main_window.py',
    'xpycode_master/ide/gui/monaco_editor.py',
    'xpycode_master/ide/gui/object_inspector.py',
    'xpycode_master/ide/gui/package_manager.py',
    'xpycode_master/ide/gui/project_explorer.py',
    'xpycode_master/ide/gui/settings_actions.py',
    'xpycode_master/ide/gui/settings_dialog.py',
    'xpycode_master/ide/gui/theme_loader.py',
    'xpycode_master/ide/gui/websocket_client.py',
    'xpycode_master/ide/gui/welcome_widget.py',
    'xpycode_master/ide/gui/widgets/edits.py',
    'xpycode_master/ide/gui/widgets/expandable_group_box.py',
]


# Files to explicitly exclude from compilation (must remain as .py)
EXCLUDE_FROM_CYTHON = [
    "__init__.py",
    "__init__.pyi",
    "__main__.py",
    "office_objects.py",  # Type stubs
    "office_objects.pyi",  # Type stubs
    "config.py",
    "exceptions.py",
]


def path_to_module_name(module_path):
    """Convert a file path to a Python module name.
    
    Example: 'xpycode_master/launcher.py' -> 'xpycode_master.launcher'
    """
    module_name = module_path.replace("/", ".").replace("\\", ".")
    if module_name.endswith(".py"):
        module_name = module_name[:-3]
    return module_name


class BuildPyExcludeCythonSources(build_py):
    """
    Custom build_py command that excludes .py source files for modules
    that have been compiled with Cython.
    """
    
    def find_package_modules(self, package, package_dir):
        """Override to exclude .py files for Cython-compiled modules."""
        modules = super().find_package_modules(package, package_dir)
        
        if not should_cythonize():
            # If not cythonizing, return all modules
            return modules
        
        # Build a set of module names that should be compiled
        cython_module_names = set()
        for module_path in CYTHON_MODULES:
            module_name = path_to_module_name(module_path)
            cython_module_names.add(module_name)
        
        # Filter out .py files for Cython modules
        filtered_modules = []
        for package_name, module_name, module_file in modules:
            # Construct full module name
            full_module = f"{package_name}.{module_name}" if package_name else module_name
            
            # Keep module if:
            # 1. It's not in the Cython modules list (not compiled), OR
            # 2. Its basename is in EXCLUDE_FROM_CYTHON (e.g., __init__.py - never compiled)
            # This ensures we exclude .py source for compiled modules but keep .py for non-compiled ones
            basename = os.path.basename(module_file)
            if full_module not in cython_module_names or basename in EXCLUDE_FROM_CYTHON:
                filtered_modules.append((package_name, module_name, module_file))
            else:
                print(f"  Excluding source file for Cython module: {full_module}")
        
        return filtered_modules


def should_cythonize():
    """
    Determine if Cython compilation should be performed.
    Skip Cython compilation if:
    - SKIP_CYTHON environment variable is set
    - Building source distribution (sdist)
    """
    if os.environ.get("SKIP_CYTHON"):
        return False
    if "sdist" in sys.argv:
        return False
    return True


def get_extensions():
    """Build list of Extension objects for Cython compilation."""
    extensions = []
    
    if not should_cythonize():
        print("Skipping Cython compilation")
        return extensions
    
    print("Setting up Cython extensions...")
    
    for module_path in CYTHON_MODULES:
        # Check if file exists
        if not Path(module_path).exists():
            print(f"Warning: Module not found: {module_path}")
            continue
        
        # Convert path to module name
        module_name = path_to_module_name(module_path)
        
        print(f"  Adding Cython extension: {module_name}")
        
        extensions.append(
            Extension(
                module_name,
                [module_path],
                # Optimization settings
                define_macros=[("CYTHON_TRACE", "0")],
            )
        )
    
    return extensions


def get_target_platform():
    """
    Determine the target platform for binary selection.
    
    Returns:
        str: 'win', 'macos', 'linux', or 'all'
    """
    target = os.environ.get("XPYCODE_TARGET_PLATFORM", "").lower().strip()
    
    if target == "all":
        return "all"
    
    # Normalize target platform name
    if target in ("win", "windows"):
        return "win"
    elif target in ("mac", "macos", "darwin"):
        return "macos"
    elif target == "linux":
        return "linux"
    elif target == "":
        # Auto-detect
        system = platform.system().lower()
        if system == "windows":
            return "win"
        elif system == "darwin":
            return "macos"
        elif system == "linux":
            return "linux"
        else:
            print(f"[setup.py] Unknown platform '{system}', keeping all binaries")
            return "all"
    else:
        print(f"[setup.py] Unknown XPYCODE_TARGET_PLATFORM='{target}', keeping all binaries")
        return "all"


def skip_other_platform_binaries():
    """
    Rename Node.js binaries for other platforms by adding .skip extension.
    This excludes them from the wheel while preserving them for sdist.
    
    Returns:
        list: List of (original_path, skip_path) tuples for files that were renamed
    """
    bin_dir = Path(__file__).parent / "xpycode_master" / "addin_launcher" / "bin"
    
    if not bin_dir.exists():
        print(f"[setup.py] Binary directory not found: {bin_dir}")
        return []
    
    platform_binaries = {
        "win": "addin-server-win.exe",
        "macos": "addin-server-macos",
        "linux": "addin-server-linux",
    }
    
    target = get_target_platform()
    
    if target == "all":
        print("[setup.py] Target platform is 'all', keeping all binaries")
        return []
    
    print(f"[setup.py] Target platform: {target}")
    
    renamed_files = []
    
    for plat, binary_name in platform_binaries.items():
        binary_path = bin_dir / binary_name
        skip_path = bin_dir / f"{binary_name}.skip"
        
        if plat != target and binary_path.exists():
            binary_path.rename(skip_path)
            renamed_files.append((binary_path, skip_path))
            print(f"[setup.py] Skipped binary for {plat}: {binary_name} -> {binary_name}.skip")
        elif plat == target and binary_path.exists():
            print(f"[setup.py] Keeping binary for {plat}: {binary_name}")
    
    return renamed_files


def restore_skipped_binaries(renamed_files):
    """
    Restore binaries that were renamed with .skip extension.
    
    Args:
        renamed_files: List of (original_path, skip_path) tuples
    """
    for original_path, skip_path in renamed_files:
        if skip_path.exists():
            skip_path.rename(original_path)
            print(f"[setup.py] Restored binary: {skip_path.name} -> {original_path.name}")


def restore_all_skipped_binaries():
    """
    Restore all .skip binaries in the bin directory.
    Call this at the start to ensure clean state.
    """
    bin_dir = Path(__file__).parent / "xpycode_master" / "addin_launcher" / "bin"
    
    if not bin_dir.exists():
        return
    
    for skip_path in bin_dir.glob("*.skip"):
        # Remove .skip extension by replacing it in the name
        original_name = skip_path.name.replace('.skip', '')
        original_path = skip_path.with_name(original_name)
        if not original_path.exists():
            skip_path.rename(original_path)
            print(f"[setup.py] Restored binary: {skip_path.name} -> {original_path.name}")


def main():
    """Main setup function."""
    # Always restore any previously skipped binaries first (clean state)
    restore_all_skipped_binaries()
    
    # Determine if we should skip binaries for this build
    renamed_files = []
    if "sdist" not in sys.argv:
        # For wheel/install, skip binaries for other platforms
        renamed_files = skip_other_platform_binaries()
    else:
        print("[setup.py] Building sdist, keeping all binaries")
    
    try:
        extensions = get_extensions()
        
        # Cythonize if we have extensions
        if extensions:
            print(f"\nCythonizing {len(extensions)} modules...")
            ext_modules = cythonize(
                extensions,
                compiler_directives={
                    "language_level": "3str",
                    "embedsignature": True,
                    "annotation_typing": True,
                    "binding": False,
                    "boundscheck": False,
                    "wraparound": False,
                    "initializedcheck": False,
                    "nonecheck": False,
                    "overflowcheck": False,
                    "cdivision": True,
                },
                build_dir="build",
                nthreads=os.cpu_count() or 1,
            )
        else:
            ext_modules = []
        
        # Call setup with ext_modules
        setup(
            ext_modules=ext_modules,
            cmdclass={
                'build_py': BuildPyExcludeCythonSources,
            },
        )
    finally:
        # Always restore skipped binaries after build
        if renamed_files:
            restore_skipped_binaries(renamed_files)


if __name__ == "__main__":
    main()
