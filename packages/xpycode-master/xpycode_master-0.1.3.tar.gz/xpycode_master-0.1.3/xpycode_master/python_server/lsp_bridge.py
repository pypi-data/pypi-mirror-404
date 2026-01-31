"""
LSP Bridge - Language Server Protocol integration for XPyCode.

This module provides LSP-like functionality using python-lsp-server (pylsp)
internals, specifically leveraging jedi_completion for autocompletion.

The bridge wraps pylsp's internal plugins to provide:
- Code completion with detailed logging
- Signature help for function parameters
- Diagnostics (syntax error checking via ast.parse and warnings via pyflakes)
- Future extensibility for hover, definition, and other LSP features

ARCHITECTURE:
- Uses pylsp's jedi_completion plugin directly for robust completion
- Logs all requests and responses for debugging ([LSP] prefix)
- Maps results to Monaco Editor format
- Uses jedi.Project for cross-module resolution when workspace is set
- Filters underscore-prefixed completions unless explicitly triggered
- Supports "dirty files" for cross-module sync (unsaved editor content)
- Uses pyflakes for detecting undefined variables and other warnings
"""

import ast
import importlib.util
import io
import logging
import os
import re
import sys
import tempfile
from typing import Any, Dict, List, Optional

# Import jedi for completion functionality
# pylsp uses jedi internally, but we configure it consistently with pylsp
import jedi

# Import pyflakes for additional diagnostics (undefined variables, etc.)
try:
    from pyflakes import api as pyflakes_api
    from pyflakes import reporter as pyflakes_reporter
    PYFLAKES_AVAILABLE = True
except ImportError:
    PYFLAKES_AVAILABLE = False

# Try to import pylsp components for configuration consistency
try:
    from pylsp import uris
    from pylsp.config.config import Config
    from pylsp.workspace import Workspace, Document
    PYLSP_AVAILABLE = True
except ImportError:
    PYLSP_AVAILABLE = False

from ..logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)


# Mapping from Jedi completion types to Monaco Editor CompletionItemKind values
# Monaco CompletionItemKind enum values:
# Method=0, Function=1, Constructor=2, Field=3, Variable=4, Class=5,
# Interface=6, Module=7, Property=8, Unit=9, Value=10, Enum=11,
# Keyword=13, Snippet=14, Text=15, Color=16, File=17, Reference=18, Folder=19
JEDI_TO_MONACO_KIND = {
    'function': 1,    # CompletionItemKind.Function
    'class': 5,       # CompletionItemKind.Class
    'module': 7,      # CompletionItemKind.Module
    'property': 8,    # CompletionItemKind.Property
    'instance': 4,    # CompletionItemKind.Variable
    'param': 4,       # CompletionItemKind.Variable
    'statement': 4,   # CompletionItemKind.Variable
    'keyword': 13,    # CompletionItemKind.Keyword
    'path': 17,       # CompletionItemKind.File
}

# Monaco MarkerSeverity enum values
MONACO_MARKER_SEVERITY_ERROR = 8
MONACO_MARKER_SEVERITY_WARNING = 4

# Regex pattern for parsing pyflakes messages
# Format: "filename:lineno:colno: message" or "filename:lineno: message"
PYFLAKES_MESSAGE_PATTERN = re.compile(r'^(.+?):(\d+)(?::(\d+))?:\s*(.+)$')

# Regex pattern for detecting import alias context
# Matches: "import xxx as " or "from xxx import yyy as "
# Supports dotted module names like "import numpy.array as "
# Groups:
#   - Simple import: "import <module> as <alias?>"
#   - From import: "from <module> import <name> as <alias?>"
IMPORT_ALIAS_PATTERN = re.compile(
    r'^\s*(import\s+[\w.]+\s+as(\s+\w*)?|from\s+[\w.]+\s+import\s+[\w.]+\s+as(\s+\w*)?)$'
)


class LSPBridge:
    """
    Bridge class for LSP-like functionality.
    
    Provides code completion and other language features using pylsp/jedi.
    All interactions are logged with [LSP] prefix for debugging.
    
    Uses a "Sync-to-Disk" strategy to enable cross-module completion:
    modules are written to a temporary directory so jedi can analyze them.
    """
    
    def __init__(self):
        """Initialize the LSP Bridge with a temporary directory for module sync."""
        self._workspace_path: Optional[str] = None
        self._temp_dir: Optional[tempfile.TemporaryDirectory] = tempfile.TemporaryDirectory()
        # Get absolute path to python_server directory for xpycode module resolution
        self._python_server_path: str = os.path.dirname(os.path.abspath(__file__))
        
        # Path to xpycode-stubs for type stub resolution (PEP 561)
        self._stubs_path: str = os.path.join(self._python_server_path, "stubs")
        
        self._jedi_project: Optional[jedi.Project] = jedi.Project(
            path=self._temp_dir.name,
            added_sys_path=[
                self._stubs_path,           # Stubs first - Jedi will use these exclusively
                #self._python_server_path    # Runtime modules second
            ]
        )
        # Hover mode: "compact" or "detailed"
        self._hover_mode: str = "compact"
        logger.info(
            "[LSP] LSPBridge initialized (pylsp_available=%s, pyflakes_available=%s, temp_dir=%s, python_server=%s, stubs=%s)",
            PYLSP_AVAILABLE, PYFLAKES_AVAILABLE, self._temp_dir.name, self._python_server_path, self._stubs_path
        )
    
    def cleanup(self) -> None:
        """Clean up the temporary directory used for module sync."""
        if self._temp_dir is not None:
            try:
                self._temp_dir.cleanup()
                logger.info("[LSP] Cleaned up temporary directory")
            except Exception as e:
                logger.warning("[LSP] Failed to cleanup temporary directory: %s", e)
            finally:
                self._temp_dir = None
    
    def set_hover_mode(self, mode: str) -> None:
        """
        Set the hover mode for displaying type information.
        
        Args:
            mode: Either "compact" or "detailed"
        """
        if mode in ("compact", "detailed"):
            self._hover_mode = mode
            logger.info(f"[LSP] Hover mode set to: {mode}")
        else:
            logger.warning(f"[LSP] Invalid hover mode '{mode}', keeping current: {self._hover_mode}")
    
    def update_sys_paths(self, new_paths: List[str]) -> None:
        """
        Update LSP's sys.path for import resolution.
        
        This recreates the jedi Project with the updated sys paths from the kernel.
        Called when package paths change (install/uninstall).
        
        Args:
            new_paths: List of paths to use for import resolution (from sys.path)
        """
        try:
            # Recreate jedi Project with updated sys paths
            # Always include stubs path first, then python_server path for xpycode module resolution
            # Avoid duplication if paths are already in new_paths
            added_paths = [self._stubs_path, self._python_server_path]
            for path in new_paths:
                if path not in added_paths:
                    added_paths.append(path)
            
            self._jedi_project = jedi.Project(
                path=self._temp_dir.name if self._temp_dir else None,
                added_sys_path=added_paths
            )
            logger.info("[LSP] Updated jedi project with %d total paths (%d package paths, stubs path: %s)", len(added_paths), len(new_paths), self._stubs_path)
        except Exception as e:
            logger.error("[LSP] Failed to update sys paths: %s", e, exc_info=True)
    
    def _get_word_prefix(self, code: str, line: int, column: int) -> str:
        """
        Extract the word being typed before the cursor position.
        
        Args:
            code: The source code text.
            line: 1-based line number.
            column: 0-based column number.
            
        Returns:
            The word prefix being typed, or empty string if none.
        """
        lines = code.split('\n')
        if line < 1 or line > len(lines):
            return ''
        line_text = lines[line - 1]
        prefix = line_text[:column]
        # Match the identifier being typed (after the last non-identifier character)
        match = re.search(r'[a-zA-Z_][a-zA-Z0-9_]*$', prefix)
        return match.group() if match else ''
    
    def _format_signature(self, signature) -> str:
        """
        Format a Jedi signature object into a clean, human-readable string.
        
        Args:
            signature: A Jedi Signature object.
            
        Returns:
            A clean signature string like '(arg1: str, arg2: int) -> None'.
        """
        try:
            # Use to_string() for a clean representation
            full_sig = signature.to_string()
            # Extract just the parameters part (after the function name)
            # The format is: func_name(params) -> return_type
            # We want: (params) -> return_type
            paren_idx = full_sig.find('(')
            if paren_idx >= 0:
                return full_sig[paren_idx:]
            return full_sig
        except (AttributeError, TypeError):
            # Fallback: build from params manually if to_string() fails
            try:
                param_strs = [p.to_string() for p in signature.params]
                return '(' + ', '.join(param_strs) + ')'
            except (AttributeError, TypeError):
                return ''
    
    def _format_compact_hover(self, definition) -> Optional[str]:
        """
        Format hover information in compact mode: (type) name: signature
        
        Args:
            definition: A Jedi definition object
            
        Returns:
            Compact hover string or None if formatting fails
        """
        try:
            name = definition.name or ""
            def_type = definition.type
            
            if def_type == 'function':
                try:
                    signatures = definition.get_signatures()
                    if signatures:
                        sig_str = self._format_signature(signatures[0])
                        return f"```python\n(function) {name}{sig_str}\n```"
                    else:
                        return f"```python\n(function) {name}\n```"
                except Exception:
                    return f"```python\n(function) {name}\n```"
            elif def_type == 'class':
                return f"```python\n(class) {name}\n```"
            elif def_type == 'module':
                return f"```python\n(module) {name}\n```"
            else:
                # For variables and other types, show the inferred type
                type_desc = self._get_type_description(definition, def_type)
                return f"```python\n({def_type}) {name}: {type_desc}\n```"
        except Exception as e:
            logger.debug(f"[LSP] Error formatting compact hover: {e}")
            return None
    
    def _get_type_description(self, definition, fallback_type: str) -> str:
        """
        Get a type description for a definition, with fallback.
        
        Args:
            definition: A Jedi definition object
            fallback_type: The type to use if description is not available
            
        Returns:
            Type description string
        """
        if hasattr(definition, 'description') and definition.description:
            return definition.description
        return fallback_type
    
    def _is_module_name(self, path: str) -> bool:
        """
        Check if a path looks like a module name (not a file path).
        
        A module name is a valid Python identifier without path separators,
        file extensions, or special characters.
        
        Args:
            path: The path or module name to check.
            
        Returns:
            True if path is a valid module name, False otherwise.
        """
        if not path:
            return False
        # Module names don't contain path separators or special prefixes
        if os.path.sep in path or '/' in path or '\\' in path:
            return False
        if path.startswith('<') or path.startswith('.'):
            return False
        # Check if it's a valid Python identifier (module name)
        return path.isidentifier()
    
    def sync_modules(self, modules: Dict[str, str], dirty_files: Optional[Dict[str, str]] = None) -> None:
        """
        Write in-memory modules to the temporary directory as .py files.
        
        This enables jedi to find and analyze these modules for cross-module
        type inference and completion.
        
        The dirty_files parameter allows overriding saved module content with
        the current editor state, ensuring Jedi sees exactly what the user sees.
        
        Args:
            modules: Dictionary mapping module names to source code strings (saved state).
            dirty_files: Optional dictionary of module names to current editor content.
                        These override the corresponding entries in modules.
        """
        # Merge modules with dirty_files (dirty_files takes precedence)
        merged_modules = dict(modules)
        if dirty_files:
            merged_modules.update(dirty_files)
        
        for module_name, code in merged_modules.items():
            file_path = os.path.join(self._temp_dir.name, f"{module_name}.py")
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(code)
                logger.debug("[LSP] Synced module '%s' to %s", module_name, file_path)
            except Exception as e:
                logger.warning("[LSP] Failed to sync module '%s': %s", module_name, e)
    
    def delete_module(self, module_name: str):
        """
        Delete a module file from the temporary directory.
        
        This removes the .py file so Jedi no longer sees the deleted module.
        
        Args:
            module_name: The name of the module to delete.
        """
        file_path = os.path.join(self._temp_dir.name, f"{module_name}.py")
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.debug("[LSP] Deleted module file '%s'", module_name)
        except Exception as e:
            logger.warning("[LSP] Failed to delete module file '%s': %s", module_name, e)
    
    def get_completions(
        self,
        code: str,
        line: int,
        column: int,
        path: Optional[str] = None,
        modules: Optional[Dict[str, str]] = None,
        dirty_files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get code completions for the given position.
        
        Args:
            code: The source code text.
            line: 1-based line number.
            column: 0-based column number.
            path: Optional file path (used for context).
            modules: Optional dictionary of module names to source code.
                     If provided, these are synced to disk before completion.
            dirty_files: Optional dictionary of module names to current editor content.
                        These override the corresponding entries in modules.
            
        Returns:
            Dict with:
                - completions: List of completion items in Monaco format
                - error: Optional error message if completion failed
        """
        # Log the request
        request_info = {
            "line": line,
            "column": column,
            "path": path,
            "code_length": len(code) if code else 0,
            "code_preview": code[:100] if code and len(code) > 100 else code
        }
        logger.debug("[LSP] Request: get_completions %s", request_info)
        
        try:
            # Validate inputs
            if not isinstance(code, str):
                raise ValueError("code must be a string")
            if not isinstance(line, int) or line < 1:
                raise ValueError("line must be a positive integer (1-based)")
            if not isinstance(column, int) or column < 0:
                raise ValueError("column must be a non-negative integer (0-based)")
            
            # Check if we're in an import alias context - no completions needed
            lines = code.split('\n')
            if line >= 1 and line <= len(lines):
                current_line = lines[line - 1]
                line_before_cursor = current_line[:column]
                
                # Check if cursor is after "import xxx as" or "from xxx import yyy as"
                if IMPORT_ALIAS_PATTERN.match(line_before_cursor):
                    logger.debug("[LSP] In import alias context, returning empty completions")
                    return {"completions": [], "error": None}
            
            # Sync modules to disk for cross-module resolution
            if modules or dirty_files:
                self.sync_modules(modules or {}, dirty_files)
            
            # Determine if user is explicitly typing an underscore prefix
            word_prefix = self._get_word_prefix(code, line, column)
            show_underscores = word_prefix.startswith('_')
            
            # Use jedi for completions with project support for cross-module resolution
            # Map virtual module names to actual file paths in the temp directory
            if path and self._is_module_name(path):
                script_path = os.path.join(self._temp_dir.name, f"{path}.py")
            else:
                script_path = path or '<editor>'
            script = jedi.Script(
                code=code,
                path=script_path,
                project=self._jedi_project
            )
            completions = script.complete(line=line, column=column)
            
            # Log raw jedi response
            logger.debug("[LSP] Jedi returned %d completions", len(completions))
            
            # Define names to filter out (deprecated aliases from xpycode)
            # These should not appear in suggestions - only 'excel' and 'context' instances should
            _filtered_xpycode_names = {} #{'Excel', 'Context'}
            
            # Map completions to Monaco format with filtering
            completion_items = []
            for completion in completions:
                # Filter out underscore-prefixed items unless user explicitly typed underscore
                if not show_underscores and completion.name.startswith('_'):
                    continue
                
                # Filter out deprecated aliases (Excel, Context) from xpycode module
                # Users should use lowercase 'excel' and 'context' instances instead
                if completion.name in _filtered_xpycode_names:
                    # Check if this is from xpycode module
                    try:
                        full_name = completion.full_name or ''
                        if 'xpycode' in full_name:
                            continue
                    except Exception:
                        pass
                
                kind = JEDI_TO_MONACO_KIND.get(completion.type, 4)  # Default to Variable
                item = {
                    "label": completion.name,
                    "kind": kind,
                    "insertText": completion.name,
                }
                
                # Add detail for functions (signature) using clean formatting
                if completion.type == "function":
                    try:
                        signatures = completion.get_signatures()
                        if signatures:
                            item["detail"] = self._format_signature(signatures[0])
                    except Exception:
                        # Ignore errors getting signature details
                        pass
                
                # Add documentation if available
                try:
                    docstring = completion.docstring()
                    if docstring:
                        item["documentation"] = docstring
                except Exception:
                    # Ignore errors getting documentation
                    pass
                
                completion_items.append(item)
            
            # Log the response
            response = {
                "completions": completion_items,
                "error": None
            }
            logger.debug(
                "[LSP] Response: %d completions returned",
                len(completion_items)
            )
            
            # Log first few completions for debugging
            if completion_items:
                sample = completion_items[:5]
                labels = [item["label"] for item in sample]
                logger.debug("[LSP] Sample completions: %s%s", 
                           labels, 
                           "..." if len(completion_items) > 5 else "")
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error("[LSP] Error in get_completions: %s", error_msg)
            return {
                "completions": [],
                "error": error_msg
            }
    
    def set_workspace(self, workspace_path: str):
        """
        Set the workspace path for LSP operations.
        
        Note: This method is deprecated for the sync-to-disk strategy.
        The temporary directory-based jedi.Project is used instead.
        This method is kept for backward compatibility but logs a warning.
        
        Args:
            workspace_path: The root path of the workspace.
        """
        self._workspace_path = workspace_path
        logger.info(
            "[LSP] Workspace path recorded: %s (using temp_dir for jedi.Project)",
            workspace_path
        )
    
    def get_signature_help(
        self,
        code: str,
        line: int,
        column: int,
        path: Optional[str] = None,
        modules: Optional[Dict[str, str]] = None,
        dirty_files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get signature help for function calls at the given position.
        
        Args:
            code: The source code text.
            line: 1-based line number.
            column: 0-based column number.
            path: Optional file path (used for context).
            modules: Optional dictionary of module names to source code.
            dirty_files: Optional dictionary of module names to current editor content.
            
        Returns:
            Dict with:
                - signatures: List of signature information in Monaco format
                - activeSignature: Index of the active signature (0)
                - activeParameter: Index of the active parameter
                - error: Optional error message if signature help failed
        """
        logger.debug(
            "[LSP] Request: get_signature_help line=%d, column=%d, path=%s",
            line, column, path
        )
        
        try:
            # Validate inputs
            if not isinstance(code, str):
                raise ValueError("code must be a string")
            if not isinstance(line, int) or line < 1:
                raise ValueError("line must be a positive integer (1-based)")
            if not isinstance(column, int) or column < 0:
                raise ValueError("column must be a non-negative integer (0-based)")
            
            # Sync modules to disk for cross-module resolution
            if modules or dirty_files:
                self.sync_modules(modules or {}, dirty_files)
            
            # Map virtual module names to actual file paths in the temp directory
            if path and self._is_module_name(path):
                script_path = os.path.join(self._temp_dir.name, f"{path}.py")
            else:
                script_path = path or '<editor>'
            
            script = jedi.Script(
                code=code,
                path=script_path,
                project=self._jedi_project
            )
            
            signatures = script.get_signatures(line=line, column=column)
            
            if not signatures:
                logger.debug("[LSP] No signatures found")
                return {
                    "signatures": [],
                    "activeSignature": 0,
                    "activeParameter": 0,
                    "error": None
                }
            
            # Use the first signature (most relevant)
            sig = signatures[0]
            
            # Build Monaco-compatible signature information
            # Extract parameter information
            params = []
            for param in sig.params:
                param_info = {
                    "label": param.name,
                }
                # Get parameter description if available
                try:
                    param_desc = param.description
                    if param_desc:
                        param_info["documentation"] = param_desc
                except (AttributeError, TypeError):
                    pass
                params.append(param_info)
            
            # Build the full signature label
            sig_label = self._format_signature(sig)
            
            # Get docstring
            docstring = ""
            try:
                docstring = sig.docstring(raw=True) or ""
            except (AttributeError, TypeError):
                pass
            
            # Safely construct the signature label
            sig_name = sig.name if sig.name else "function"
            monaco_signature = {
                "label": sig_name + sig_label,
                "documentation": docstring,
                "parameters": params
            }
            
            # Get active parameter index
            active_param = sig.index if sig.index is not None else 0
            
            response = {
                "signatures": [monaco_signature],
                "activeSignature": 0,
                "activeParameter": active_param,
                "error": None
            }
            
            logger.debug(
                "[LSP] Signature help: %s, activeParam=%d",
                sig.name, active_param
            )
            
            return response
            
        except Exception as e:
            error_msg = str(e)
            logger.error("[LSP] Error in get_signature_help: %s", error_msg)
            return {
                "signatures": [],
                "activeSignature": 0,
                "activeParameter": 0,
                "error": error_msg
            }
    
    def get_hover(
        self,
        code: str,
        line: int,
        column: int,
        path: Optional[str] = None,
        modules: Optional[Dict[str, str]] = None,
        dirty_files: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Get hover information (type and docstring) for the symbol at the given position.
        
        Args:
            code: The source code text.
            line: 1-based line number.
            column: 0-based column number.
            path: Optional file path (used for context).
            modules: Optional dictionary of module names to source code.
            dirty_files: Optional dictionary of module names to current editor content.
            
        Returns:
            Dict with:
                - contents: Hover content as markdown or plain text
                - error: Optional error message if hover failed
        """
        logger.debug(
            "[LSP] Request: get_hover line=%d, column=%d, path=%s",
            line, column, path
        )
        
        try:
            # Validate inputs
            if not isinstance(code, str):
                raise ValueError("code must be a string")
            if not isinstance(line, int) or line < 1:
                raise ValueError("line must be a positive integer (1-based)")
            if not isinstance(column, int) or column < 0:
                raise ValueError("column must be a non-negative integer (0-based)")
            
            # Sync modules to disk for cross-module resolution
            if modules or dirty_files:
                self.sync_modules(modules or {}, dirty_files)
            
            # Map virtual module names to actual file paths in the temp directory
            if path and self._is_module_name(path):
                script_path = os.path.join(self._temp_dir.name, f"{path}.py")
            else:
                script_path = path or '<editor>'
            
            script = jedi.Script(
                code=code,
                path=script_path,
                project=self._jedi_project
            )
            
            # Use infer() to get type information at the cursor position
            inferred = script.infer(line=line, column=column)
            
            # Fallback: If infer() returns empty, try help() for documentation
            if not inferred:
                logger.debug("[LSP] infer() returned empty, trying help() as fallback")
                try:
                    help_results = script.help(line=line, column=column)
                    if help_results:
                        # Build hover content from help results
                        hover_parts = []
                        for h in help_results:
                            name = h.name or ""
                            desc = h.description if hasattr(h, 'description') else ""
                            # Construct hover text - use signature format for better readability
                            # description is typically the type (e.g., "function", "class")
                            if name and desc:
                                hover_parts.append(f"```python\n({desc}) {name}\n```")
                            elif name:
                                hover_parts.append(f"```python\n{name}\n```")
                            
                            # Add docstring if available
                            try:
                                docstring = h.docstring()
                                if docstring:
                                    hover_parts.append(docstring)
                            except Exception:
                                pass
                        
                        if hover_parts:
                            contents_str = "\n\n---\n\n".join(hover_parts)
                            contents = {'kind': 'markdown', 'value': contents_str}
                            logger.debug("[LSP] Hover (from help()): found %d results", len(help_results))
                            return {
                                "contents": contents,
                                "error": None
                            }
                except Exception as e:
                    logger.debug("[LSP] help() fallback failed: %s", e)
                
                logger.debug("[LSP] No type information found for hover")
                return {
                    "contents": None,
                    "error": None
                }
            
            # Build hover content from inferred types
            hover_parts = []
            for definition in inferred:
                # Use compact or detailed mode based on setting
                if self._hover_mode == "compact":
                    # Compact mode: (type) name: signature, skip docstrings
                    compact_str = self._format_compact_hover(definition)
                    if compact_str:
                        hover_parts.append(compact_str)
                else:
                    # Detailed mode: full information with docstrings
                    # Get the full name and type
                    full_name = definition.full_name or definition.name
                    def_type = definition.type
                    
                    # Build type signature line
                    if def_type == 'function':
                        try:
                            signatures = definition.get_signatures()
                            if signatures:
                                sig_str = self._format_signature(signatures[0])
                                hover_parts.append(f"```python\n{full_name}{sig_str}\n```")
                            else:
                                hover_parts.append(f"```python\n{full_name}\n```")
                        except Exception:
                            hover_parts.append(f"```python\n{full_name}\n```")
                    elif def_type == 'class':
                        hover_parts.append(f"```python\nclass {full_name}\n```")
                    elif def_type == 'module':
                        hover_parts.append(f"```python\nmodule {full_name}\n```")
                    else:
                        # For variables and other types, show the inferred type
                        type_desc = self._get_type_description(definition, def_type)
                        hover_parts.append(f"```python\n{full_name}: {type_desc}\n```")
                    
                    # Add docstring if available (detailed mode only)
                    try:
                        docstring = definition.docstring()
                        if docstring:
                            hover_parts.append(docstring)
                    except Exception:
                        pass
            
            # Combine all parts with newlines
            contents_str = "\n\n---\n\n".join(hover_parts) if hover_parts else None
            
            logger.debug("[LSP] Hover: found %d definitions", len(inferred))
            
            # Return contents in LSP-compatible format: {'kind': 'markdown', 'value': string}
            # This ensures proper rendering in Monaco editor
            if contents_str:
                contents = {'kind': 'markdown', 'value': contents_str}
            else:
                contents = None
            
            return {
                "contents": contents,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error("[LSP] Error in get_hover: %s", error_msg)
            return {
                "contents": None,
                "error": error_msg
            }
    
    def get_diagnostics(self, code: str, module_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Get diagnostics for the given code.
        
        Uses ast.parse() to detect syntax errors and pyflakes to detect
        warnings like undefined variables, unused imports, etc.
        
        Args:
            code: The source code text to check.
            module_name: Optional module name for better error context.
            
        Returns:
            Dict with:
                - diagnostics: List of diagnostic objects with:
                    - startLineNumber: 1-based line number
                    - startColumn: 1-based column number
                    - endLineNumber: 1-based line number
                    - endColumn: 1-based column number
                    - message: Error message
                    - severity: Monaco severity (ERROR or WARNING)
                - error: Optional error message if diagnostic check failed
        """
        logger.debug("[LSP] Request: get_diagnostics, code_length=%d", len(code) if code else 0)
        
        try:
            if not isinstance(code, str):
                raise ValueError("code must be a string")
            
            diagnostics = []
            
            # Use module name as filename for better error context
            filename = f"<{module_name}>" if module_name else "<editor>"
            
            # Step 1: Check for syntax errors with ast.parse
            syntax_ok = True
            try:
                ast.parse(code, filename=filename)
            except SyntaxError as e:
                syntax_ok = False
                # Extract error information
                lineno = e.lineno or 1
                offset = e.offset or 1
                msg = e.msg or "Syntax error"
                
                # Monaco uses 1-based line and column numbers
                # Python's offset is 1-based already
                diagnostic = {
                    "startLineNumber": lineno,
                    "startColumn": offset,
                    "endLineNumber": lineno,
                    "endColumn": offset + 1,  # Highlight at least one character
                    "message": msg,
                    "severity": MONACO_MARKER_SEVERITY_ERROR
                }
                diagnostics.append(diagnostic)
                logger.debug(
                    "[LSP] Syntax error at line %d, col %d: %s",
                    lineno, offset, msg
                )
            
            # Step 2: Run pyflakes for additional warnings (only if syntax is OK)
            if syntax_ok and PYFLAKES_AVAILABLE:
                pyflakes_diagnostics = self._run_pyflakes(code, filename)
                diagnostics.extend(pyflakes_diagnostics)
            
            # Step 3: Check for unresolved imports (only if syntax is OK)
            if syntax_ok:
                import_diagnostics = self._check_unresolved_imports(code, module_name)
                diagnostics.extend(import_diagnostics)
            
            # Step 4: Sort diagnostics by severity (Error=8 first, Warning=4 second)
            # Higher severity values come first (descending order)
            diagnostics.sort(key=lambda d: d.get("severity", 0), reverse=True)
            
            return {
                "diagnostics": diagnostics,
                "error": None
            }
            
        except Exception as e:
            error_msg = str(e)
            logger.error("[LSP] Error in get_diagnostics: %s", error_msg)
            return {
                "diagnostics": [],
                "error": error_msg
            }
    
    def _run_pyflakes(self, code: str, filename: str) -> List[Dict[str, Any]]:
        """
        Run pyflakes on the code and return diagnostics.
        
        Args:
            code: The source code text to check.
            filename: The filename for error reporting.
            
        Returns:
            List of diagnostic objects in Monaco format.
        """
        diagnostics = []
        
        try:
            # Create string buffers to capture pyflakes output
            warning_stream = io.StringIO()
            error_stream = io.StringIO()
            
            # Create a custom reporter that writes to our buffers
            reporter = pyflakes_reporter.Reporter(warning_stream, error_stream)
            
            # Run pyflakes check
            pyflakes_api.check(code, filename, reporter)
            
            # Parse warning output
            warning_stream.seek(0)
            for line in warning_stream:
                diag = self._parse_pyflakes_message(line.strip(), MONACO_MARKER_SEVERITY_WARNING)
                if diag:
                    diagnostics.append(diag)
            
            # Parse error output
            error_stream.seek(0)
            for line in error_stream:
                diag = self._parse_pyflakes_message(line.strip(), MONACO_MARKER_SEVERITY_ERROR)
                if diag:
                    diagnostics.append(diag)
            
            logger.debug("[LSP] Pyflakes returned %d diagnostics", len(diagnostics))
            
        except Exception as e:
            logger.warning("[LSP] Pyflakes check failed: %s", e)
        
        return diagnostics
    
    def _parse_pyflakes_message(self, message: str, severity: int) -> Optional[Dict[str, Any]]:
        """
        Parse a pyflakes message into Monaco diagnostic format.
        
        Pyflakes message format: "filename:lineno:colno message" or "filename:lineno: message"
        
        Args:
            message: The pyflakes message string.
            severity: The Monaco severity level.
            
        Returns:
            Diagnostic dict or None if parsing fails.
        """
        if not message:
            return None
        
        try:
            # Match pattern: filename:lineno:colno: message OR filename:lineno: message
            # Examples:
            #   <editor>:2:1: 'os' imported but unused
            #   <editor>:3: undefined name 'foo'
            match = PYFLAKES_MESSAGE_PATTERN.match(message)
            
            if match:
                lineno = int(match.group(2))
                colno = int(match.group(3)) if match.group(3) else 1
                msg = match.group(4)
                
                # Try to extract a more accurate end column from the message
                # For messages like "'os' imported but unused", extract the token length
                end_col = colno + 1  # Default: highlight at least one character
                token_match = re.match(r"^'([^']+)'", msg)
                if token_match:
                    # Use the length of the token mentioned in the message
                    end_col = colno + len(token_match.group(1))
                
                return {
                    "startLineNumber": lineno,
                    "startColumn": colno,
                    "endLineNumber": lineno,
                    "endColumn": end_col,
                    "message": msg,
                    "severity": severity
                }
        except Exception as e:
            logger.debug("[LSP] Failed to parse pyflakes message '%s': %s", message, e)
        
        return None
    
    def _check_unresolved_imports(self, code: str, module_name: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Check for unresolved import statements in the code.
        
        Uses importlib to verify that imported modules can be resolved.
        Returns diagnostic errors for modules that cannot be found.
        
        Args:
            code: The source code text to check.
            module_name: Optional module name for better error context.
            
        Returns:
            List of diagnostic objects in Monaco format.
        """
        diagnostics = []
        
        try:
            tree = ast.parse(code)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Check each imported module name
                    for alias in node.names:
                        module_to_check = alias.name
                        if not self._can_resolve_import(module_to_check):
                            diagnostics.append({
                                "startLineNumber": node.lineno,
                                "startColumn": node.col_offset + 1,
                                "endLineNumber": node.end_lineno or node.lineno,
                                "endColumn": (node.end_col_offset or node.col_offset) + 1,
                                "message": f"import '{module_to_check}' could not be resolved",
                                "severity": MONACO_MARKER_SEVERITY_ERROR
                            })
                            
                elif isinstance(node, ast.ImportFrom):
                    # Check the module being imported from
                    module_to_check = node.module or ''
                    if module_to_check and not self._can_resolve_import(module_to_check):
                        diagnostics.append({
                            "startLineNumber": node.lineno,
                            "startColumn": node.col_offset + 1,
                            "endLineNumber": node.end_lineno or node.lineno,
                            "endColumn": (node.end_col_offset or node.col_offset) + 1,
                            "message": f"import '{module_to_check}' could not be resolved",
                            "severity": MONACO_MARKER_SEVERITY_ERROR
                        })
            
            logger.debug("[LSP] Import check found %d unresolved imports", len(diagnostics))
            
        except SyntaxError:
            # Syntax errors are already handled by ast.parse in get_diagnostics
            pass
        except Exception as e:
            logger.warning("[LSP] Import check failed: %s", e)
        
        return diagnostics
    
    def _can_resolve_import(self, module_name: str) -> bool:
        """
        Check if a module can be resolved by Python's import system.
        
        Args:
            module_name: The name of the module to check.
            
        Returns:
            True if the module can be resolved, False otherwise.
        """
        try:
            # Check if module is already loaded
            if module_name in sys.modules:
                return True
            
            # Check if the module is in the in-memory loader (virtual modules)
            # Virtual modules are stored in the temp directory
            if self._temp_dir is not None:
                temp_module_path = os.path.join(self._temp_dir.name, f"{module_name}.py")
                if os.path.exists(temp_module_path):
                    return True
            
            # Try to find the module spec without actually importing
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ModuleNotFoundError, ImportError, ValueError, AttributeError):
            return False
