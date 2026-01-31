# ExtrasResolver Implementation

## Overview

This document describes the implementation of the `ExtrasResolver` module, which provides multi-index extras resolution for Python packages.

## Problem Statement

Previously, the `get_package_extras` function in `manager.py` used hardcoded PyPI URL patterns to fetch metadata about package extras. This approach had several limitations:
- No support for multiple package repositories
- No modularity or extensibility
- Tight coupling to PyPI JSON API

## Solution

A new `ExtrasResolver` module was created following the same architectural pattern as `VersionResolver`, providing:
- Multi-index orchestration with settings integration
- PEP 503 simple index HTML parsing for standard package indexes
- Deactivated PyPI JSON API fallback (available but not used by default)
- Proper priority handling (primary URLs first, then secondaries)

## Architecture

### Components

1. **ExtrasResolver** (`extras_resolver.py`)
   - Main class for orchestrating extras resolution
   - Queries primary index first, then secondaries if enabled
   - Parses PEP 503 HTML for extras information
   - Normalizes package names per PEP 503 standards

2. **SimpleIndexParser** (`extras_resolver.py`)
   - HTML parser for PEP 503 simple index format
   - Extracts package file metadata from anchor tags

3. **PackageManager** (updated in `manager.py`)
   - Initializes and uses ExtrasResolver
   - Delegates all extras queries to the resolver

### Multi-Index Strategy

The resolver follows this strategy:
1. Query primary index first
2. If no results AND `use_secondary_urls` is True, query secondaries one by one
3. Stop at first index with results (don't cumulate)

This mirrors the behavior of `VersionResolver` for consistency.

## Key Features

### PEP 503 Compliance

- **Package Name Normalization**: Converts package names to lowercase with hyphens
  ```python
  normalized_name = package_name.lower().replace('_', '-')
  ```

- **Simple Index Parsing**: Parses HTML to extract package file links
  ```
  https://index.example.com/simple/package-name/
  ```

### Version Filtering

Precise regex-based version matching:
```python
version_pattern = rf'-{escaped_version}[-\.]'
```

Matches patterns like:
- `package-1.0.0-py3-none-any.whl`
- `package-1.0.0.tar.gz`

### Settings Integration

Respects settings from `settings_manager`:
- `package_management.pip.index_urls`: List of index URLs with primary flag
- `package_management.pip.use_secondary_urls`: Enable/disable secondary fallback
- `package_management.pip.proxy`: Proxy configuration
- `package_management.pip.retries`: Number of retries

### Deactivated PyPI JSON API

The PyPI JSON API fallback is available via `get_package_extras_pypi_json()` but not used by default:
- Kept as a separate method for future use
- Can be activated by modifying settings
- Useful for PyPI-specific queries

## Known Limitations

### PEP 503 Simple Index

The PEP 503 simple index specification has inherent limitations:
- Does not expose extras metadata directly
- Extras are not typically encoded in wheel filenames (per PEP 427)
- This implementation looks for non-standard bracket notation that may exist in custom indexes

### Alternative Approaches

For comprehensive extras detection, consider:
1. **PyPI JSON API**: Use `get_package_extras_pypi_json()` for PyPI packages
2. **Core Metadata**: Download and parse wheel file metadata
3. **Custom APIs**: Use index-specific metadata APIs if available

## Usage Examples

### Basic Usage

```python
from xpycode_master.business_layer.packages.manager import PackageManager

# Initialize with settings
manager = PackageManager(settings_manager=settings)

# Query extras
extras = await manager.get_package_extras("requests", "2.28.0")
# Returns: ['security', 'socks', 'use_chardet_on_py3']
```

### With Custom Index URLs

```python
# Configure settings
settings.set("package_management.pip.index_urls", [
    {"url": "https://pypi.org/simple/", "primary": True},
    {"url": "https://custom.repo.com/simple/", "primary": False}
])
settings.set("package_management.pip.use_secondary_urls", True)

# Query will try primary first, then custom repo if needed
extras = await manager.get_package_extras("internal-package")
```

### Using PyPI JSON Fallback

```python
# Direct call to PyPI JSON API (not used by default)
from xpycode_master.business_layer.packages.extras_resolver import ExtrasResolver

resolver = ExtrasResolver(pip_command_builder)
extras = await resolver.get_package_extras_pypi_json("requests", "2.28.0")
```

## Testing

### Test Coverage

The implementation includes comprehensive test coverage:

**Unit Tests** (`test_extras_resolver.py`):
1. SimpleIndexParser HTML parsing
2. Primary index query
3. Secondary index fallback
4. Respects use_secondary_urls setting
5. Handles packages with no extras
6. PyPI JSON API fallback method
7. Version filtering

**Integration Tests** (`test_manager_extras_integration.py`):
1. PackageManager uses ExtrasResolver
2. Handles packages with no extras
3. Respects settings
4. Handles errors gracefully

All tests use mocked aiohttp responses to simulate various scenarios without network calls.

### Running Tests

```bash
# Run unit tests
python test_extras_resolver.py

# Run integration tests
python test_manager_extras_integration.py

# Run all tests
python test_extras_resolver.py && python test_manager_extras_integration.py
```

## File Changes Summary

| File | Changes | Lines |
|------|---------|-------|
| `extras_resolver.py` | New module | +304 |
| `manager.py` | Refactored to use resolver | -48, +7 |
| `test_extras_resolver.py` | Unit tests | +396 |
| `test_manager_extras_integration.py` | Integration tests | +214 |

**Total**: +921 lines, -48 lines

## Migration Notes

### Backward Compatibility

The changes maintain full backward compatibility:
- `PackageManager.get_package_extras()` signature unchanged
- Return type remains `List[str]`
- Error handling behavior preserved
- All existing tests still pass

### No Breaking Changes

- Existing code using `get_package_extras()` will work without modification
- Default behavior uses PEP 503 parsing instead of PyPI JSON
- PyPI JSON fallback available for future activation

## Future Enhancements

Potential improvements:
1. Add support for downloading and parsing wheel core metadata
2. Implement caching for extras queries
3. Support index-specific metadata APIs
4. Add configurable fallback to PyPI JSON API
5. Support for custom HTML parsing strategies

## References

- [PEP 503 - Simple Repository API](https://peps.python.org/pep-0503/)
- [PEP 427 - The Wheel Binary Package Format](https://peps.python.org/pep-0427/)
- [PyPI JSON API Documentation](https://warehouse.pypa.io/api-reference/json.html)
