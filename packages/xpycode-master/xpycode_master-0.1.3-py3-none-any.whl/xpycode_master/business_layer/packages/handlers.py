"""
Package Handlers - Message handlers for package management operations.

This module provides:
- Message handlers for IDE package management requests
- Integration with PackageManager for pip operations
- Integration with ConnectionManager for message routing
"""

import asyncio
from typing import Optional

from ...logging_config import get_logger

logger = get_logger(__name__)


# These handlers will be initialized with manager and package_manager
_manager = None
_package_manager = None
_handle_workbook_packages_install = None


def init_handlers(manager, package_manager, handle_workbook_packages_install_func):
    """
    Initialize handlers with manager and package_manager instances.
    
    Args:
        manager: ConnectionManager instance for routing messages.
        package_manager: PackageManager instance for package operations.
        handle_workbook_packages_install_func: Function for installing workbook packages.
    """
    global _manager, _package_manager, _handle_workbook_packages_install
    _manager = manager
    _package_manager = package_manager
    _handle_workbook_packages_install = handle_workbook_packages_install_func


async def handle_package_install_request(client_id: str, message: dict):
    """Handle package installation request from IDE."""
    workbook_id = message.get("workbook_id")
    package_spec = message.get("package")
    if workbook_id and package_spec:
        asyncio.create_task(
            handle_package_install(client_id, workbook_id, package_spec)
        )


async def handle_get_package_versions_request(client_id: str, message: dict):
    """Handle package versions query from IDE."""
    package_name = message.get("package_name")
    request_id = message.get("request_id")
    if package_name and request_id:
        asyncio.create_task(
            handle_get_package_versions(client_id, package_name, request_id)
        )
    else:
        logger.warning("Received get_package_versions_request without package_name or request_id")


async def handle_get_package_extras_request(client_id: str, message: dict):
    """Handle package extras query from IDE."""
    package_name = message.get("package_name")
    version = message.get("version")
    request_id = message.get("request_id")
    if package_name and request_id:
        asyncio.create_task(
            handle_get_package_extras(client_id, package_name, version, request_id)
        )
    else:
        logger.warning("Received get_package_extras_request without package_name or request_id")


async def handle_get_package_info_request(client_id: str, message: dict):
    """Handle package info query from IDE."""
    package_name = message.get("package_name")
    request_id = message.get("request_id")
    if package_name and request_id:
        asyncio.create_task(
            handle_get_package_info(client_id, package_name, request_id)
        )
    else:
        logger.warning("Received get_package_info_request without package_name or request_id")


async def handle_add_workbook_package(client_id: str, message: dict):
    """Handle add package to workbook's list request from IDE."""
    target_workbook = message.get("workbook_id")
    package_name = message.get("package_name")
    version = message.get("version")
    extras = message.get("extras", [])
    
    if target_workbook and package_name and version:
        # Initialize workbook package list if needed
        if target_workbook not in _manager.workbook_packages:
            _manager.workbook_packages[target_workbook] = []
        
        # Add package to list with pending status
        package_entry = {
            "name": package_name,
            "version": version,
            "extras": extras,
            "status": "pending"
        }
        _manager.workbook_packages[target_workbook].append(package_entry)
        
        # Send update to all IDEs
        await _manager.send_to_ide({
            "type": "workbook_packages_update",
            "workbook_id": target_workbook,
            "packages": _manager.workbook_packages[target_workbook]
        })
        logger.info(f"Added package {package_name}=={version} to workbook {target_workbook}")
    else:
        logger.warning("Received add_workbook_package without required parameters")


async def handle_remove_workbook_package(client_id: str, message: dict):
    """Handle remove package from workbook's list request from IDE."""
    target_workbook = message.get("workbook_id")
    package_name = message.get("package_name")
    
    if target_workbook and package_name:
        if target_workbook in _manager.workbook_packages:
            # Remove package from list
            _manager.workbook_packages[target_workbook] = [
                pkg for pkg in _manager.workbook_packages[target_workbook]
                if pkg["name"] != package_name
            ]
            
            # Send update to all IDEs
            await _manager.send_to_ide({
                "type": "workbook_packages_update",
                "workbook_id": target_workbook,
                "packages": _manager.workbook_packages[target_workbook]
            })
            logger.info(f"Removed package {package_name} from workbook {target_workbook}")
    else:
        logger.warning("Received remove_workbook_package without required parameters")


async def handle_update_workbook_package(client_id: str, message: dict):
    """Handle update package in workbook's list request from IDE."""
    target_workbook = message.get("workbook_id")
    package_name = message.get("package_name")
    version = message.get("version")
    extras = message.get("extras", [])
    
    if target_workbook and package_name and version:
        if target_workbook in _manager.workbook_packages:
            # Find and update the package
            for pkg in _manager.workbook_packages[target_workbook]:
                if pkg["name"] == package_name:
                    pkg["version"] = version
                    pkg["extras"] = extras
                    pkg["status"] = "pending_update"
                    break
            
            # Send update to all IDEs
            await _manager.send_to_ide({
                "type": "workbook_packages_update",
                "workbook_id": target_workbook,
                "packages": _manager.workbook_packages[target_workbook]
            })
            logger.info(f"Updated package {package_name}=={version} in workbook {target_workbook}")
    else:
        logger.warning("Received update_workbook_package without required parameters")


async def handle_restore_workbook_packages(client_id: str, message: dict):
    """Handle restore packages request from IDE."""

    target_workbook = message.get("workbook_id")
    if not target_workbook:
        return
    _manager.workbook_packages[target_workbook]=_manager.workbook_installed_packages.get(target_workbook,[])
    _manager._push_packages_and_python_paths(target_workbook)


async def handle_update_package_status(client_id: str, message: dict):
    """Handle update package status request from IDE."""
    target_workbook = message.get("workbook_id")
    package_name = message.get("package_name")
    status = message.get("status")
    
    if target_workbook and package_name and status:
        if target_workbook in _manager.workbook_packages:
            # Find and update the package status
            for pkg in _manager.workbook_packages[target_workbook]:
                if pkg["name"] == package_name:
                    pkg["status"] = status
                    break
            
            # Send update to all IDEs
            await _manager.send_to_ide({
                "type": "workbook_packages_update",
                "workbook_id": target_workbook,
                "packages": _manager.workbook_packages[target_workbook],
                "python_paths": _manager.workbook_python_paths.get(target_workbook, []),
                "package_errors": _manager.package_errors.get(target_workbook, {})
            })
            logger.info(f"Updated status for package {package_name} to {status} in workbook {target_workbook}")
    else:
        logger.warning("Received update_package_status without required parameters")


async def handle_update_python_paths(client_id: str, message: dict):
    """Handle update python paths request from IDE."""
    # Import here to avoid circular dependency
    from ..bl_master import normalize_python_paths
    
    target_workbook = message.get("workbook_id")
    python_paths = message.get("python_paths", [])
    
    if target_workbook:
        # Normalize python_paths to strings (handles old dict format)
        python_paths = normalize_python_paths(python_paths)
        
        # Store python paths
        old_python_paths = _manager.workbook_python_paths.get(target_workbook, [])
        _manager.workbook_python_paths[target_workbook] = python_paths
        
        # Send python paths to kernel for sys.path update
        # python_paths are now already strings
        if python_paths or old_python_paths:
            await _manager.send_message("kernel", target_workbook, {
                "type": "set_python_paths",
                "old_paths": old_python_paths,
                "new_paths": python_paths
            })
            logger.info(f"Sent {len(python_paths)} python paths to kernel for workbook {target_workbook}")
        
        # Send save_workbook_packages message to addin to persist python_paths
        addin_ws = _manager.get_connection("addin", target_workbook)
        if addin_ws:
            # Get current packages for this workbook
            packages = _manager.workbook_packages.get(target_workbook, [])
            
            await addin_ws.send_json({
                "type": "save_workbook_packages",
                "packages": packages,
                "python_paths": python_paths
            })
            logger.info(f"Sent python paths to addin for storage: {len(python_paths)} paths")
        else:
            logger.warning(f"Cannot save python paths: addin not connected for {target_workbook}")
        
        # Send update to all IDEs
        await _manager.send_to_ide({
            "type": "workbook_packages_update",
            "workbook_id": target_workbook,
            "packages": _manager.workbook_packages.get(target_workbook, []),
            "python_paths": python_paths,
            "package_errors": _manager.package_errors.get(target_workbook, {})
        })
        logger.info(f"Updated python paths for workbook {target_workbook}: {len(python_paths)} paths")
    else:
        logger.warning("Received update_python_paths without workbook_id")


async def handle_reorder_workbook_packages(client_id: str, message: dict):
    """Handle reorder packages request from IDE."""
    target_workbook = message.get("workbook_id")
    package_names = message.get("package_names", [])
    
    if target_workbook and package_names:
        if target_workbook in _manager.workbook_packages:
            # Create new ordered list
            current_packages = {pkg["name"]: pkg for pkg in _manager.workbook_packages[target_workbook]}
            new_order = []
            for name in package_names:
                if name in current_packages:
                    new_order.append(current_packages[name])
            
            _manager.workbook_packages[target_workbook] = new_order
            
            # Send update to all IDEs
            await _manager.send_to_ide({
                "type": "workbook_packages_update",
                "workbook_id": target_workbook,
                "packages": _manager.workbook_packages[target_workbook]
            })
            logger.info(f"Reordered packages for workbook {target_workbook}")
    else:
        logger.warning("Received reorder_workbook_packages without required parameters")


async def handle_install_workbook_packages(client_id: str, message: dict):
    """Handle install all packages request from IDE."""
    target_workbook = message.get("workbook_id")
    
    if target_workbook:
        asyncio.create_task(
            _handle_workbook_packages_install(target_workbook)
        )
        logger.info(f"Starting package installation for workbook {target_workbook}")
    else:
        logger.warning("Received install_workbook_packages without workbook_id")


async def handle_get_workbook_packages(client_id: str, message: dict):
    """Handle get workbook packages request from IDE."""
    target_workbook = message.get("workbook_id")
    
    if target_workbook:
        packages = _manager.workbook_packages.get(target_workbook, [])
        python_paths = _manager.workbook_python_paths.get(target_workbook, [])
        # Send to requesting IDE
        await _manager.send_to_ide({
            "type": "workbook_packages_update",
            "workbook_id": target_workbook,
            "packages": packages,
            "package_errors": _manager.package_errors.get(target_workbook, {}),
            "python_paths": python_paths
        })
    else:
        logger.warning("Received get_workbook_packages without workbook_id")


async def handle_get_resolved_deps(client_id: str, message: dict):
    """Handle get resolved dependencies request from IDE."""
    target_workbook = message.get("workbook_id")
    
    if target_workbook:
        deps = _manager.workbook_resolved_deps.get(target_workbook, [])
        # Send to requesting IDE
        await _manager.send_to_ide({
            "type": "resolved_deps_response",
            "workbook_id": target_workbook,
            "deps": deps
        })
    else:
        logger.warning("Received get_resolved_deps without workbook_id")


# Implementation functions called by the request handlers

async def handle_package_install(ide_client_id: str, workbook_id: str, package_spec: str):
    """
    Handle package installation and stream output to IDE.

    Args:
        ide_client_id: The IDE client ID to send output to.
        workbook_id: The workbook ID for the kernel to update sys.path.
        package_spec: The package specification to install.
    """
    installation_path = None

    try:
        async for output_type, content in _package_manager.install_package(package_spec):
            if output_type in ("stdout", "stderr"):
                # Stream pip output to IDE
                await _manager.send_message(
                    "ide",
                    ide_client_id,
                    {
                        "type": "pip_output",
                        "workbook_id": workbook_id,
                        "output_type": output_type,
                        "content": content,
                    },
                )
            elif output_type == "path":
                # Store the installation path
                installation_path = content
            elif output_type == "success":
                # Send success message to IDE
                await _manager.send_message(
                    "ide",
                    ide_client_id,
                    {
                        "type": "pip_output",
                        "workbook_id": workbook_id,
                        "output_type": "success",
                        "content": content,
                    },
                )
                # Send add_path to the kernel if we have an installation path
                if installation_path:
                    await _manager.send_message(
                        "kernel",
                        workbook_id,
                        {
                            "type": "add_path",
                            "path": installation_path,
                        },
                    )
            elif output_type == "error":
                # Send error message to IDE
                await _manager.send_message(
                    "ide",
                    ide_client_id,
                    {
                        "type": "pip_output",
                        "workbook_id": workbook_id,
                        "output_type": "error",
                        "content": content,
                    },
                )
    except Exception as e:
        logger.error(f"Error during package installation: {e}")
        await _manager.send_message(
            "ide",
            ide_client_id,
            {
                "type": "pip_output",
                "workbook_id": workbook_id,
                "output_type": "error",
                "content": f"Installation error: {str(e)}",
            },
        )


async def handle_get_package_versions(ide_client_id: str, package_name: str, request_id: str):
    """
    Handle package versions query and send response to IDE.
    
    Args:
        ide_client_id: The IDE client ID to send response to.
        package_name: The package name to query.
        request_id: The request ID for matching response.
    """
    try:
        versions = await _package_manager.get_available_versions(package_name)
        
        # Send response back to IDE
        await _manager.send_message(
            "ide",
            ide_client_id,
            {
                "type": "get_package_versions_response",
                "package_name": package_name,
                "versions": versions,
                "request_id": request_id,
            },
        )
    except Exception as e:
        logger.error(f"Error querying package versions for {package_name}: {e}")
        
        # Also send the standard response with error
        await _manager.send_message(
            "ide",
            ide_client_id,
            {
                "type": "get_package_versions_response",
                "package_name": package_name,
                "versions": [],
                "error": str(e),
                "request_id": request_id,
            },
        )


async def handle_get_package_extras(
    ide_client_id: str, package_name: str, version: Optional[str], request_id: str
):
    """
    Handle package extras query and send response to IDE.
    
    Args:
        ide_client_id: The IDE client ID to send response to.
        package_name: The package name to query.
        version: Optional specific version to query.
        request_id: The request ID for matching response.
    """
    try:
        extras = await _package_manager.get_package_extras(package_name, version)
        
        # If version wasn't provided, get the latest version from package info
        if not version:
            info = await _package_manager.get_package_info(package_name)
            version = info.get("latest_version", "")
        
        # Send response back to IDE
        await _manager.send_message(
            "ide",
            ide_client_id,
            {
                "type": "get_package_extras_response",
                "package_name": package_name,
                "version": version,
                "extras": extras,
                "request_id": request_id,
            },
        )
    except Exception as e:
        logger.error(f"Error querying package extras for {package_name}: {e}")
        await _manager.send_message(
            "ide",
            ide_client_id,
            {
                "type": "get_package_extras_response",
                "package_name": package_name,
                "version": version or "",
                "extras": [],
                "error": str(e),
                "request_id": request_id,
            },
        )


async def handle_get_package_info(ide_client_id: str, package_name: str, request_id: str):
    """
    Handle package info query and send response to IDE.
    
    Args:
        ide_client_id: The IDE client ID to send response to.
        package_name: The package name to query.
        request_id: The request ID for matching response.
    """
    try:
        info = await _package_manager.get_package_info(package_name)
        
        # Send response back to IDE
        response = {
            "type": "get_package_info_response",
            "package_name": package_name,
            "request_id": request_id,
        }
        
        # Add info fields or error
        if "error" in info:
            response["error"] = info["error"]
        else:
            response.update({
                "name": info.get("name", package_name),
                "latest_version": info.get("latest_version", ""),
                "summary": info.get("summary", ""),
            })
        
        await _manager.send_message("ide", ide_client_id, response)
        
    except Exception as e:
        logger.error(f"Error querying package info for {package_name}: {e}")
        await _manager.send_message(
            "ide",
            ide_client_id,
            {
                "type": "get_package_info_response",
                "package_name": package_name,
                "error": str(e),
                "request_id": request_id,
            },
        )
