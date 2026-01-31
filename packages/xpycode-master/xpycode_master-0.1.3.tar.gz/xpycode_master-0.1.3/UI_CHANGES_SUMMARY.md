# UI Changes Summary - Pip API Mappings Feature

## Overview
This document summarizes the UI changes made to support the pip API mappings feature.

## Part 1: Settings Dialog - API Mappings Page

### Location
`xpycode_master/ide/gui/settings_dialog.py`

### Changes Made

1. **New Tree Item**: Added "API Mappings" under "Package Management" in the settings tree
   - Path: `package_management.pip_api`
   - Located between "Pip" and console settings

2. **New Page**: Created `_create_pip_api_page()` method (Stack Index 5)
   - **Components**:
     - QTableWidget with 2 columns: "Index URL" and "API Pattern"
     - Both columns use stretch mode for responsive width
     - 3 buttons: "Add", "Edit", "Remove"

3. **Dialog Handlers**:
   - `_on_add_pip_api()`: Shows dialog to add new API mapping
     - 2 input fields: Index URL, API Pattern
     - Pre-filled placeholders showing example values
   - `_on_edit_pip_api()`: Shows dialog to edit selected mapping
     - Pre-fills with existing values
   - `_on_remove_pip_api()`: Removes selected row from table

4. **Settings Integration**:
   - `load_settings()`: Populates table from `package_management.pip_api` list
   - `get_settings()`: Exports table data as list of dicts with `index_url` and `api_pattern` keys

### Example Settings Structure
```json
{
  "package_management": {
    "pip_api": [
      {
        "index_url": "https://pypi.org/simple",
        "api_pattern": "https://pypi.org/pypi/{package_name}/{version}/json"
      },
      {
        "index_url": "https://custom.org/simple",
        "api_pattern": "https://custom.org/api/{package_name}/{version}"
      }
    ]
  }
}
```

### Visual Layout
```
Settings Dialog
├── View
│   └── Themes & Appearance
├── Editor
├── Package Management
│   ├── Pip
│   └── API Mappings ← NEW
│       ├── Table (Index URL | API Pattern)
│       └── Buttons [Add] [Edit] [Remove]
└── Console
```

## Part 2: Package Manager - Manual Extras Input

### Location
`xpycode_master/ide/gui/package_manager.py`

### Changes Made

1. **New Input Section**: Added after the extras list, before "Add to List" button
   - **Components**:
     - QLineEdit: Text input for custom extra name
     - QPushButton: "Add Extra" button
     - Placeholder text: "Enter custom extra (e.g., dev, test)"

2. **Handler**: `_on_add_manual_extra_clicked()`
   - Validates extra name (alphanumeric, hyphens, underscores only)
   - Checks for duplicates
   - Adds to extras_list with checked state
   - Clears input field after adding
   - Logs action to pip console

### Visual Layout
```
Add Package Group
├── Package Name Input
├── Version Dropdown
├── Extras List (checkboxes)
├── Manual Extra Input ← NEW
│   ├── [Text Input: "Enter custom extra"]
│   └── [Add Extra Button]
└── [Add to List Button]
```

### User Workflow
1. User searches for a package
2. Selects a version
3. Auto-detected extras appear in list (if API pattern configured)
4. User can type custom extra names (e.g., "dev", "testing")
5. Click "Add Extra" to add to the checkbox list
6. Both auto-detected and manually-added extras are included when clicking "Add to List"

### Validation Rules
- Only alphanumeric characters, hyphens, and underscores allowed
- Duplicate extras are rejected with a message
- Empty names are ignored

## Backend Integration

### Settings Manager
**File**: `xpycode_master/business_layer/settings_manager.py`

Added default `pip_api` configuration:
```python
"package_management": {
    "pip": { ... },
    "pip_api": [
        {
            "index_url": "https://pypi.org/simple",
            "api_pattern": "https://pypi.org/pypi/{package_name}/{version}/json"
        }
    ]
}
```

### Extras Resolver
**File**: `xpycode_master/business_layer/packages/extras_resolver.py`

Added methods:
- `_normalize_url(url)`: Strips trailing slashes/backslashes
- `_get_api_pattern_for_index(index_url, pip_api_list)`: Finds matching API pattern
- Updated `_query_index_for_extras()`: Uses API patterns instead of HTML parsing

## Testing

### Test Coverage
1. **API Pattern Tests** (`test_extras_resolver_api_pattern.py`):
   - URL normalization
   - API pattern matching
   - JSON API extras extraction
   - Version placeholder handling
   - 404 handling

2. **Updated Tests** (`test_extras_resolver.py`):
   - All existing tests updated to reflect new behavior
   - Tests now verify empty set returned without API pattern

3. **UI Component Tests** (`test_ui_components.py`):
   - Verifies UI components exist and are properly initialized
   - Tests load_settings and get_settings integration

### All Tests Pass ✓
- 6 new API pattern tests
- 7 updated existing tests
- 2 UI component tests (when PySide6 available)

## Summary

The implementation successfully adds:
1. Configurable API pattern mappings in settings UI
2. Manual extras input in package manager
3. API-based extras resolution in backend
4. Comprehensive test coverage

All changes are minimal, focused, and follow existing code patterns.
