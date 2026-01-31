"""
Theme loader module for Qt stylesheets.

This module loads theme definitions from themes.json and generates
Qt stylesheets with proper variable resolution.
"""

import json
import os
from typing import Dict
from ...logging_config import setup_logging_subprocess, get_logger
logger = get_logger(__name__)

class ThemeLoader:
    """Loads and manages Qt themes from JSON configuration."""
    
    def __init__(self):
        """Initialize the theme loader and load themes.json."""
        self._themes_data = None
        self._formatings_cache={}
        self._load_themes()
    
    def _load_themes(self):
        """Load the themes.json file."""
        themes_path = os.path.join(
            os.path.dirname(__file__),
            "resources",
            "themes.json"
        )
        
        with open(themes_path, 'r', encoding='utf-8') as f:
            self._themes_data = json.load(f)

        self._formatings_cache={}
        for theme_id in self.get_theme_names().keys():
            self._formatings_cache[theme_id]=self._get_formatings(theme_id)

    def get_theme_names(self) -> Dict[str, str]:
        """
        Get the mapping of theme IDs to display names.
        
        Returns:
            Dictionary mapping theme_id -> display_name
        """
        return self._themes_data.get("themes", {})
    

    def _get_variables_for_theme(self,theme_id:str) -> Dict[str,str]:
        """
        Get all variable values for a specific theme.
        
        Args:
            theme_id: The theme ID to get variables for
        """
        rep={}
        theme_vars=self._themes_data.get("theme_variables",{})
        for var_name,var_values in theme_vars.items():
            rep[var_name]=var_values.get(theme_id,var_values.get("default",""))
        return rep

    def _get_formatings(self,theme_id:str) -> Dict[str,str]:
        """
        Get all formatting styles for a specific theme.
        
        Args:
            theme_id: The theme ID to get styles for
        """
        rep={}
        rep.update(self._themes_data.get("styles",{}))
        rep.update(self._themes_data.get("colors",{}))

        variables=self._get_variables_for_theme(theme_id)
        for var_name,var_value in variables.items():
            rep[var_name]=rep.get(var_value,"")
        
        return rep

    def _resolve_variable(self, value: str, theme_id: str) -> str:
        """
        Resolve a variable reference to its actual value.
        
        Handles nested variable references like:
        {bg-main} -> {dark-gray-1} -> #1e1e1e
        
        Args:
            value: The value potentially containing {variable} references
            theme_id: The theme ID to resolve variables for
            
        Returns:
            The resolved value with all variables replaced
        """
        # Keep resolving until no more variables are found
        
        formating=self._formatings_cache[theme_id]
        value=str(value).format(**formating)

        return value
    
    def _resolve_variable_old(self, value: str, theme_id: str) -> str:
        """
        Resolve a variable reference to its actual value.
        
        Handles nested variable references like:
        {bg-main} -> {dark-gray-1} -> #1e1e1e
        
        Args:
            value: The value potentially containing {variable} references
            theme_id: The theme ID to resolve variables for
            
        Returns:
            The resolved value with all variables replaced
        """
        # Keep resolving until no more variables are found
        max_iterations = 10  # Prevent infinite loops
        iteration = 0
        
        while '{' in value and iteration < max_iterations:
            iteration += 1
            original_value = value
            
            # Find all {variable} patterns
            import re
            pattern = r'\{([^}]+)\}'
            
            def replace_var(match):
                var_name = match.group(1)
                
                # Check if it's a theme variable
                if var_name in self._themes_data.get("theme_variables", {}):
                    theme_vars = self._themes_data["theme_variables"][var_name]
                    # Get value for this theme, or default
                    resolved = theme_vars.get(theme_id, theme_vars.get("default", var_name))
                    # Wrap in braces if it looks like another variable (not starting with #)
                    if resolved and not resolved.startswith('#') and not resolved.startswith('rgba'):
                        # Check if it's a known color/style variable
                        if resolved in self._themes_data.get("colors", {}) or resolved in self._themes_data.get("styles", {}):
                            return '{' + resolved + '}'
                    return resolved
                
                # Check if it's a color
                elif var_name in self._themes_data.get("colors", {}):
                    return self._themes_data["colors"][var_name]
                
                # Check if it's a style
                elif var_name in self._themes_data.get("styles", {}):
                    return self._themes_data["styles"][var_name]
                
                # Unknown variable, leave as-is
                return match.group(0)
            
            value = re.sub(pattern, replace_var, value)
            
            # If nothing changed, break to avoid infinite loop
            if value == original_value:
                break
        
        return value


    def _resolve_property_value(self, prop_value, theme_id: str) -> str:
        """
        Resolve a property value which can be a string or a dict with theme-specific values.
        
        Args:
            prop_value: Either a string or dict with theme-specific values
            theme_id: The theme ID to resolve for
            
        Returns:
            The resolved property value as a string
        """
        if isinstance(prop_value, dict):
            # Property has theme-specific values
            value = prop_value.get(theme_id, prop_value.get("default", ""))
            if value:
                return self._resolve_variable(value, theme_id)
            return ""
        else:
            # Property is a simple string
            return self._resolve_variable(prop_value, theme_id)
    
    def generate_stylesheet(self, theme_id: str) -> str:
        """
        Generate a Qt stylesheet for the given theme.
        
        Args:
            theme_id: The theme identifier (e.g., 'xpy-dark', 'xpy-light')
            
        Returns:
            The complete Qt stylesheet as a string
        """
        # Fallback to default if theme not found
        if theme_id not in self._themes_data.get("themes", {}):
            theme_id = "xpy-dark"
        
        selectors = self._themes_data.get("selectors", {})
        stylesheet_parts = []
        
        for selector, properties in selectors.items():
            # Build the CSS rules for this selector
            rules = []
            
            for prop_name, prop_value in properties.items():
                resolved_value = self._resolve_property_value(prop_value, theme_id)
                
                # Only add the rule if there's a resolved value
                if resolved_value:
                    rules.append(f"    {prop_name}: {resolved_value};")
            
            # Only add selector if it has rules
            if rules:
                stylesheet_parts.append(f"{selector} {{")
                stylesheet_parts.extend(rules)
                stylesheet_parts.append("}")
        
        return "\n".join(stylesheet_parts)
