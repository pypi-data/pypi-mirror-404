# Manifest Tracking and Automatic Cache Clearing Implementation

## Overview

This document describes the implementation of automatic manifest tracking and cache clearing functionality for the XPyCode Office add-in.

## Problem Statement

When switching between local and external add-in modes, or when configuration changes (port, version, etc.), Office's add-in cache needs to be cleared for changes to take effect. Previously, users had to manually clear the cache, which was error-prone and not well-documented.

## Solution

Automatically track manifest configuration and clear the Office add-in cache when settings change.

## Implementation Details

### 1. Manifest Info Tracking

**File**: `~/.xpycode/manifest_info.json`

Stores current manifest configuration:

```json
{
  "mode": "local",
  "addin_port": 49171,
  "external_url": null,
  "version": "0.1.2",
  "manifest_path": "/Users/username/.xpycode/manifest/xpycode_manifest.xml",
  "last_updated": "2026-01-30T14:30:00Z"
}
```

### 2. New Functions in `launcher.py`

#### Tracking Functions

- **`get_manifest_info_path()`** - Returns path to manifest info file
- **`load_manifest_info()`** - Loads existing manifest info (returns None if not found)
- **`save_manifest_info()`** - Saves current configuration with error handling

#### Cache Management Functions

- **`should_clear_cache()`** - Determines if cache clearing is needed
- **`get_wef_cache_folder()`** - Gets platform-specific cache folder path
- **`clear_office_addin_cache()`** - Clears Office add-in cache safely

### 3. Integration

Modified `register_manifest_with_excel()` to:

1. Load previous manifest info
2. Determine if cache should be cleared
3. Clear cache if needed (with user notification)
4. Register manifest
5. Save new manifest info

### 4. Cache Clearing Logic

Cache is cleared when:

| Condition | Example | Cache Cleared? |
|-----------|---------|----------------|
| First time setup | No previous info exists | No |
| Mode change | local ↔ external | Yes |
| Port change (local mode) | 49171 → 49172 | Yes |
| External URL change (external mode) | URL updated | Yes |
| Version change (external mode) | 0.1.2 → 0.1.3 | Yes |

### 5. Platform Support

| Platform | Cache Location |
|----------|----------------|
| Windows | `%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\` |
| macOS | `~/Library/Containers/com.microsoft.Excel/Data/Documents/wef/` |
| Linux | Not supported (no standard location) |

### 6. User Notification

When cache is cleared:

```
==================================================
INFO:   Office add-in cache cleared
INFO:   Please restart Excel if it's running
==================================================
```

### 7. Error Handling

- File I/O errors are caught and logged (warnings)
- Manifest registration continues even if info saving fails
- Cache clearing handles:
  - Non-existent folders (returns True)
  - Permission errors (logged as warnings)
  - Symlinks (removed without following)

## Testing

### Unit Tests (`test_manifest_tracking.py`)

9 tests covering:
- Manifest info path creation
- Save/load operations
- Cache clearing decision logic
- Platform-specific cache folder detection
- Cache clearing functionality

### Integration Tests (`test_manifest_integration.py`)

3 tests covering:
- First time registration
- Re-registration with same settings
- Mode change scenarios

### All Tests Pass

```
RESULTS: 9 passed, 0 failed (unit tests)
RESULTS: 3 passed, 0 failed (integration tests)
```

## Security

- **CodeQL Scan**: 0 alerts
- Symlinks handled safely (not followed)
- Error handling prevents information leakage
- File operations use proper encoding

## Code Review Feedback Addressed

1. ✓ Added error handling to `save_manifest_info()`
2. ✓ Fixed spacing inconsistency in comparison operator
3. ✓ Added explicit `return None` for clarity
4. ✓ Improved comment clarity on version changes
5. ✓ Added symlink handling to prevent following links

## Example Usage

```python
from xpycode_master.launcher import register_manifest_with_excel

# First time - cache will be cleared
register_manifest_with_excel(manifest_path, 49171)

# Second time with same settings - cache NOT cleared
register_manifest_with_excel(manifest_path, 49171)

# Change to external mode - cache will be cleared
register_manifest_with_excel(manifest_path, -1)
```

## Files Modified

- `xpycode_master/launcher.py` - Added 6 functions, integrated into registration flow

## Files Created

- `test_manifest_tracking.py` - Unit tests
- `test_manifest_integration.py` - Integration tests
- `demo_manifest_tracking.py` - Demonstration script
- `MANIFEST_TRACKING_IMPLEMENTATION.md` - This document

## Benefits

1. **Automatic**: No manual cache clearing needed
2. **Smart**: Only clears when necessary
3. **Transparent**: Logs and notifies user
4. **Robust**: Error handling prevents failures
5. **Secure**: Safe file operations, symlink handling
6. **Tested**: Comprehensive test coverage

## Backward Compatibility

- Existing code paths unchanged
- First run treats as new installation (clears cache)
- No breaking changes to API or behavior
