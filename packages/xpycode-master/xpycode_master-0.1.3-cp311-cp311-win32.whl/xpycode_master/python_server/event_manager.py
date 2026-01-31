"""
Event Manager - Handles Excel event utilities for XPyCode.

This module provides:
- Event discovery from the xpycode.office_objects module
- Registry management for event handlers (legacy support)
- Handler scaffolding for generating stub functions
- Handler validation

Note: With the new event system architecture, the Add-in is the source of truth
for object structure and event metadata, and the Business Layer centralizes state.
This module now serves primarily as a utility library for event-related operations.
"""

import importlib
import inspect
import logging
import os
import re
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


# Mapping of event name prefixes to their parent object types
# Used when the event name clearly indicates the parent object
PARENT_OBJECT_MAPPING = {
    "Workbook": "Workbook",
    "Worksheet": "Worksheet",
    "Table": "Table",
    "Chart": "Chart",
    "Comment": "Comment",
    "Shape": "Shape",
    "Binding": "Binding",
    "Selection": "Workbook",  # General selection events belong to Workbook
    "Settings": "Settings",
    "LinkedEntityDataDomain": "LinkedEntityDataDomain",
}


class EventManager:
    """
    Manages Excel event utilities.

    Provides event discovery, registry management (legacy support), 
    handler scaffolding, and handler validation.
    
    Note: In the new event system architecture, event registration and 
    dispatching is handled by the Add-in and Business Layer.
    """

    def __init__(self):
        """Initialize the EventManager."""
        # Registry structure: {workbook_id: {(object_type, object_name, event_type): handler_name}}
        self._registry: Dict[str, Dict[Tuple[str, str, str], str]] = {}
        # Cache for discovered events
        self._event_cache: Optional[Dict[str, List[str]]] = None

    def discover_available_events(self) -> Dict[str, List[str]]:
        """
        Discover all available events from the xpycode.office_objects module.

        Inspects the office_objects module to identify all classes ending in
        'EventArgs' and constructs a mapping of parent objects to their events.

        Returns:
            Dict mapping parent object names to lists of event type names.
            e.g., {"Worksheet": ["WorksheetSelectionChangedEventArgs", ...], ...}
        """
        if self._event_cache is not None:
            return self._event_cache

        events_by_parent: Dict[str, List[str]] = {}

        try:
            # Import the office_objects module
            try:
                from .xpycode import office_objects
            except ImportError:
                from xpycode import office_objects

            # Get the Excel class which contains most Excel-related EventArgs
            excel_class = getattr(office_objects, "Excel", None)
            if excel_class:
                self._discover_events_in_class(excel_class, events_by_parent)

            # Also check other top-level classes for EventArgs
            for name in dir(office_objects):
                if name.startswith("_"):
                    continue
                obj = getattr(office_objects, name)
                if inspect.isclass(obj) and name != "Excel":
                    self._discover_events_in_class(obj, events_by_parent)

        except ImportError as e:
            logger.error(f"Failed to import office_objects module: {e}")
        except Exception as e:
            logger.error(f"Error discovering events: {e}")

        # Explicitly ensure Workbook and Shape are included as event sources
        # These are important object types that should always be available
        if "Workbook" not in events_by_parent:
            events_by_parent["Workbook"] = []
        if "Shape" not in events_by_parent:
            events_by_parent["Shape"] = []

        self._event_cache = events_by_parent
        return events_by_parent

    def _discover_events_in_class(
        self, cls: type, events_by_parent: Dict[str, List[str]]
    ) -> None:
        """
        Recursively discover EventArgs classes within a class.

        Args:
            cls: The class to inspect.
            events_by_parent: Dict to populate with discovered events.
        """
        for name in dir(cls):
            if name.startswith("_"):
                continue

            obj = getattr(cls, name, None)
            if obj is None:
                continue

            if inspect.isclass(obj):
                if name.endswith("EventArgs"):
                    # Infer parent object from the event name
                    parent = self._infer_parent_from_event_name(name)
                    if parent not in events_by_parent:
                        events_by_parent[parent] = []
                    if name not in events_by_parent[parent]:
                        events_by_parent[parent].append(name)
                else:
                    # Recursively check nested classes
                    self._discover_events_in_class(obj, events_by_parent)

    def _infer_parent_from_event_name(self, event_name: str) -> str:
        """
        Infer the parent object type from an event name.

        Args:
            event_name: The EventArgs class name (e.g., "WorksheetSelectionChangedEventArgs").

        Returns:
            The inferred parent object type (e.g., "Worksheet").
        """
        # Check each known prefix in order of length (longest first)
        sorted_prefixes = sorted(
            PARENT_OBJECT_MAPPING.keys(), key=len, reverse=True
        )
        for prefix in sorted_prefixes:
            if event_name.startswith(prefix):
                return PARENT_OBJECT_MAPPING[prefix]

        # If no known prefix, try to extract the first capitalized word
        match = re.match(r"([A-Z][a-z]+)", event_name)
        if match:
            return match.group(1)

        return "Unknown"

    def register_event(
        self,
        workbook_id: str,
        object_type: str,
        object_id: str,
        event_type: str,
        handler_name: str,
    ) -> None:
        """
        Register an event handler for a specific Excel object's event.

        Args:
            workbook_id: The workbook identifier.
            object_type: The type of Excel object (e.g., "Worksheet", "Workbook").
            object_id: The ID of the specific object (e.g., sheet ID, table ID).
            event_type: The event type class name (e.g., "WorksheetSelectionChangedEventArgs").
            handler_name: The Python function name as a string (e.g., "ExcelEvents.on_selection_change").
        """
        if workbook_id not in self._registry:
            self._registry[workbook_id] = {}

        key = (object_type, object_id, event_type)
        self._registry[workbook_id][key] = handler_name
        logger.debug(
            f"Registered event handler: {workbook_id}/{object_type}/{object_id}/{event_type} -> {handler_name}"
        )

    def unregister_event(
        self,
        workbook_id: str,
        object_type: str,
        object_id: str,
        event_type: str,
    ) -> bool:
        """
        Unregister an event handler.

        Args:
            workbook_id: The workbook identifier.
            object_type: The type of Excel object.
            object_id: The ID of the specific object.
            event_type: The event type class name.

        Returns:
            True if the handler was found and removed, False otherwise.
        """
        if workbook_id not in self._registry:
            return False

        key = (object_type, object_id, event_type)
        if key in self._registry[workbook_id]:
            del self._registry[workbook_id][key]
            logger.debug(
                f"Unregistered event handler: {workbook_id}/{object_type}/{object_id}/{event_type}"
            )
            return True
        return False

    def get_handler(
        self,
        workbook_id: str,
        object_type: str,
        object_id: str,
        event_type: str,
    ) -> Optional[str]:
        """
        Retrieve the registered handler name for a given event.

        Args:
            workbook_id: The workbook identifier.
            object_type: The type of Excel object.
            object_id: The ID of the specific object.
            event_type: The event type class name.

        Returns:
            The handler name string if found, None otherwise.
        """
        if workbook_id not in self._registry:
            return None

        key = (object_type, object_id, event_type)
        return self._registry[workbook_id].get(key)

    def get_all_handlers(
        self, workbook_id: str
    ) -> Dict[Tuple[str, str, str], str]:
        """
        Get all registered handlers for a workbook.

        Args:
            workbook_id: The workbook identifier.

        Returns:
            Dict mapping (object_type, object_id, event_type) tuples to handler names.
        """
        return self._registry.get(workbook_id, {}).copy()

    def create_handler_stub(
        self,
        handler_name: str,
        event_type: str,
        base_path: Optional[str] = None,
    ) -> bool:
        """
        Create a handler function stub in the ExcelEvents module.

        Args:
            handler_name: The handler name (e.g., "ExcelEvents.on_selection_change").
            event_type: The event type class name (e.g., "WorksheetSelectionChangedEventArgs").
            base_path: Optional base path for the Python files. Defaults to python_server directory.

        Returns:
            True if the stub was created successfully, False otherwise.
        """
        # Parse the handler name to get module and function
        parts = handler_name.split(".")
        if len(parts) != 2:
            logger.error(
                f"Invalid handler name format: {handler_name}. Expected 'ModuleName.function_name'"
            )
            return False

        module_name, function_name = parts

        # Determine the base path
        if base_path is None:
            base_path = os.path.dirname(os.path.abspath(__file__))

        module_path = os.path.join(base_path, f"{module_name}.py")

        try:
            # Check if the module file exists
            if not os.path.exists(module_path):
                # Create the module with necessary imports
                self._create_module_file(module_path, event_type)

            # Read the existing file content
            with open(module_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check if the function already exists
            if self._function_exists_in_content(content, function_name):
                logger.info(
                    f"Function {function_name} already exists in {module_path}"
                )
                return True

            # Ensure the import for the EventType is present
            content = self._ensure_import(content, event_type)

            # Append the new function stub
            stub = self._generate_function_stub(function_name, event_type)
            content = content.rstrip() + "\n\n" + stub + "\n"

            # Write the updated content
            with open(module_path, "w", encoding="utf-8") as f:
                f.write(content)

            logger.info(
                f"Created handler stub: {function_name} in {module_path}"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to create handler stub: {e}")
            return False

    def _create_module_file(self, module_path: str, event_type: str) -> None:
        """
        Create a new module file with necessary imports.

        Args:
            module_path: Path to the module file.
            event_type: The event type to import.
        """
        content = '''"""
Excel event handlers module.

This module contains handler functions for Excel events.
"""

from xpycode.office_objects import Excel

'''
        with open(module_path, "w", encoding="utf-8") as f:
            f.write(content)

    def _function_exists_in_content(
        self, content: str, function_name: str
    ) -> bool:
        """
        Check if a function definition exists in the content.

        Args:
            content: The file content.
            function_name: The function name to search for.

        Returns:
            True if the function is defined, False otherwise.
        """
        pattern = rf"^def\s+{re.escape(function_name)}\s*\("
        return bool(re.search(pattern, content, re.MULTILINE))

    def _ensure_import(self, content: str, event_type: str) -> str:
        """
        Ensure that the import for the EventType is present in the content.

        Args:
            content: The current file content.
            event_type: The event type class name.

        Returns:
            The updated content with the import if it was missing.
        """
        # Check if Excel is imported from office_objects
        if "from xpycode.office_objects import Excel" in content:
            # The EventArgs classes are nested in Excel, so this import is sufficient
            return content

        # Add the import at the top of the file, after any existing imports
        import_line = "from xpycode.office_objects import Excel\n"

        # Find the last import statement
        lines = content.split("\n")
        last_import_idx = -1
        for i, line in enumerate(lines):
            stripped = line.strip()
            if stripped.startswith("import ") or stripped.startswith("from "):
                last_import_idx = i

        if last_import_idx >= 0:
            lines.insert(last_import_idx + 1, import_line.rstrip())
        else:
            # No imports found, add after any docstrings (handles both """ and ''')
            insert_idx = 0
            first_line = lines[0] if lines else ""
            if first_line.startswith('"""') or first_line.startswith("'''"):
                docstring_marker = '"""' if first_line.startswith('"""') else "'''"
                for i, line in enumerate(lines):
                    if i > 0 and docstring_marker in line:
                        insert_idx = i + 1
                        break
            lines.insert(insert_idx, import_line.rstrip())

        return "\n".join(lines)

    def _generate_function_stub(
        self, function_name: str, event_type: str
    ) -> str:
        """
        Generate a function stub for the event handler.

        Args:
            function_name: The name of the function.
            event_type: The event type class name.

        Returns:
            The function stub as a string.
        """
        return f'''def {function_name}(event: Excel.{event_type}):
    """
    Handle {event_type} event.

    Args:
        event: The event arguments containing event details.
    """
    raise NotImplementedError("Handler not implemented")'''

    def validate_handler(
        self, handler_name: str, modules: Optional[Dict[str, str]] = None
    ) -> Union[bool, Callable[..., Any]]:
        """
        Validate that a handler function exists and can be found.

        Args:
            handler_name: The handler name (e.g., "ExcelEvents.on_selection_change").
            modules: Optional dict of in-memory modules {name: source_code}.

        Returns:
            The function object if found and valid, False otherwise.
        """
        parts = handler_name.split(".")
        if len(parts) != 2:
            logger.warning(
                f"Invalid handler name format: {handler_name}. Expected 'ModuleName.function_name'"
            )
            return False

        module_name, function_name = parts

        try:
            # First, try to import from in-memory modules if provided
            if modules and module_name in modules:
                # The module might be in sys.modules if already imported
                import sys

                if module_name in sys.modules:
                    module = sys.modules[module_name]
                else:
                    # Create a temporary module from the source
                    import types

                    module = types.ModuleType(module_name)
                    exec(modules[module_name], module.__dict__)

                func = getattr(module, function_name, None)
                if callable(func):
                    return func
                return False

            # Try to import the module from the file system
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                # Try importing relative to current package
                # Infer package name from this module's name
                current_package = __name__.rsplit(".", 1)[0] if "." in __name__ else None
                if current_package:
                    try:
                        module = importlib.import_module(f".{module_name}", package=current_package)
                    except (ModuleNotFoundError, ImportError):
                        logger.debug(f"Module not found: {module_name}")
                        return False
                else:
                    logger.debug(f"Module not found: {module_name}")
                    return False

            func = getattr(module, function_name, None)
            if callable(func):
                return func

            logger.debug(
                f"Function {function_name} not found or not callable in module {module_name}"
            )
            return False

        except Exception as e:
            logger.debug(f"Error validating handler {handler_name}: {e}")
            return False

    def get_callable(
        self, handler_name: str, modules: Optional[Dict[str, str]] = None
    ) -> Callable[..., Any]:
        """
        Get the callable function object for a handler name.

        Takes a full function path (e.g., "ExcelEvents.on_selection_change"),
        dynamically imports the module, and returns the actual Python function object.

        Args:
            handler_name: The handler name (e.g., "ExcelEvents.on_selection_change").
            modules: Optional dict of in-memory modules {name: source_code}.

        Returns:
            The callable function object.

        Raises:
            ValueError: If the handler name format is invalid.
            ImportError: If the module cannot be imported.
            AttributeError: If the function is not found in the module.
        """
        parts = handler_name.split(".")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid handler name format: {handler_name}. "
                "Expected 'ModuleName.function_name'"
            )

        module_name, function_name = parts

        try:
            # First, try to import from in-memory modules if provided
            if modules and module_name in modules:
                import sys
                import types

                if module_name in sys.modules:
                    module = sys.modules[module_name]
                else:
                    # Create a temporary module from the source
                    module = types.ModuleType(module_name)
                    exec(modules[module_name], module.__dict__)

                func = getattr(module, function_name, None)
                if func is None:
                    raise AttributeError(
                        f"Function '{function_name}' not found in module '{module_name}'"
                    )
                if not callable(func):
                    raise AttributeError(
                        f"'{function_name}' in module '{module_name}' is not callable"
                    )
                return func

            # Try to import the module from the file system
            try:
                module = importlib.import_module(module_name)
            except ModuleNotFoundError:
                # Try importing relative to current package
                current_package = (
                    __name__.rsplit(".", 1)[0] if "." in __name__ else None
                )
                if current_package:
                    try:
                        module = importlib.import_module(
                            f".{module_name}", package=current_package
                        )
                    except (ModuleNotFoundError, ImportError) as e:
                        raise ImportError(
                            f"Module '{module_name}' not found"
                        ) from e
                else:
                    raise ImportError(f"Module '{module_name}' not found")

            func = getattr(module, function_name, None)
            if func is None:
                raise AttributeError(
                    f"Function '{function_name}' not found in module '{module_name}'"
                )
            if not callable(func):
                raise AttributeError(
                    f"'{function_name}' in module '{module_name}' is not callable"
                )
            return func

        except (ValueError, ImportError, AttributeError):
            # Re-raise these specific exceptions as they are the expected error types
            raise
        except SyntaxError as e:
            # Handle syntax errors in the module source code
            raise ImportError(
                f"Syntax error in module '{module_name}': {e}"
            ) from e
        except Exception as e:
            # Other exceptions (e.g., from exec, getattr, or module initialization)
            # are wrapped in ImportError to provide a consistent error interface
            raise ImportError(
                f"Failed to get callable for handler '{handler_name}': {e}"
            ) from e

    def clear_workbook_registry(self, workbook_id: str) -> None:
        """
        Clear all registered handlers for a workbook.

        Args:
            workbook_id: The workbook identifier.
        """
        if workbook_id in self._registry:
            del self._registry[workbook_id]
            logger.debug(f"Cleared event registry for workbook: {workbook_id}")

    def clear_event_cache(self) -> None:
        """Clear the cached event discovery results."""
        self._event_cache = None
