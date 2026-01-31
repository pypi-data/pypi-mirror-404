# Cython Compilation Fix - Subprocess Module Entry Points

## Problem
When running `python -m xpycode_master` after installing from a wheel built with Cython compilation, the application failed with:
```
No code object available for xpycode_master.launcher
```

This occurred because modules invoked as subprocesses using `python -m module_name` cannot be Cython-compiled (.pyd files). The `-m` flag doesn't work with compiled extension modules.

## Root Cause
The following modules were called as subprocesses via `sys.executable -m`:
- `xpycode_master.launcher` - called by `watchdog.py`
- `xpycode_master.python_server.kernel` - called by `business_layer/server.py`
- `xpycode_master.python_inspector.inspector` - called by `business_layer/inspector_launcher.py`
- `xpycode_master.ide.main` - called by `business_layer/ide_manager.py`

## Solution Implemented

### 1. Python Server Package (`xpycode_master.python_server`)

**Created:** `xpycode_master/python_server/__main__.py`
- New entry point that imports and calls `kernel.main()`
- Handles command-line arguments
- Can be invoked as `python -m xpycode_master.python_server`

**Modified:** `xpycode_master/python_server/kernel.py`
- Removed `if __name__ == "__main__":` block
- Kept `async def main(workbook_id: str, port: str)` function

**Modified:** `xpycode_master/business_layer/server.py`
- Changed `kernel_path='xpycode_master.python_server.kernel'` to `kernel_path='xpycode_master.python_server'`

### 2. Python Inspector Package (`xpycode_master.python_inspector`)

**Created:** `xpycode_master/python_inspector/__main__.py`
- New entry point that imports and calls `inspector.main()`
- Handles command-line arguments
- Can be invoked as `python -m xpycode_master.python_inspector`

**Modified:** `xpycode_master/python_inspector/inspector.py`
- Removed `if __name__ == "__main__":` block
- Kept `async def main(port: str)` function

**Modified:** `xpycode_master/business_layer/inspector_launcher.py`
- Changed `return 'xpycode_master.python_inspector.inspector'` to `return 'xpycode_master.python_inspector'`

### 3. IDE Package (`xpycode_master.ide`)

**Renamed:** `xpycode_master/ide/main.py` → `xpycode_master/ide/__main__.py`
- The file content remains the same
- Can now be invoked as `python -m xpycode_master.ide`

**Modified:** `xpycode_master/business_layer/ide_manager.py`
- Changed `sys.executable, "-m", "xpycode_master.ide.main"` to `sys.executable, "-m", "xpycode_master.ide"`

### 4. Setup.py Configuration

**Modified:** `setup.py`
- Removed `"xpycode_master/launcher.py"` from `CYTHON_MODULES` list
- `launcher.py` must remain as a .py file since it's called by `watchdog.py` as a subprocess

**Note:** `__main__.py` files are automatically excluded from Cython compilation via the `EXCLUDE_FROM_CYTHON` list in `setup.py`.

## Benefits

1. **Cython Compatibility**: Modules can now be compiled with Cython without breaking subprocess invocation
2. **Standard Python Pattern**: Uses the standard `__main__.py` pattern for package entry points
3. **Backward Compatibility**: Works with both compiled and non-compiled versions
4. **Maintainability**: Clear separation between entry point and implementation

## Testing

Created `test_subprocess_modules.py` to verify:
- Modules can be invoked with `python -m` flag
- Module structure is correct
- `launcher.py` is excluded from Cython compilation
- `__main__.py` files are excluded from Cython compilation

All tests pass successfully.

## Files Modified

1. **Created** `xpycode_master/python_server/__main__.py`
2. **Modified** `xpycode_master/python_server/kernel.py`
3. **Modified** `xpycode_master/business_layer/server.py`
4. **Created** `xpycode_master/python_inspector/__main__.py`
5. **Modified** `xpycode_master/python_inspector/inspector.py`
6. **Modified** `xpycode_master/business_layer/inspector_launcher.py`
7. **Renamed** `xpycode_master/ide/main.py` → `xpycode_master/ide/__main__.py`
8. **Modified** `xpycode_master/business_layer/ide_manager.py`
9. **Modified** `setup.py`
10. **Created** `test_subprocess_modules.py` (test file)

## Acceptance Criteria - All Met ✓

- ✓ `xpycode_master/python_server/__main__.py` created with proper entry point
- ✓ `kernel.py` no longer has `if __name__ == "__main__":` block
- ✓ `server.py` calls `python -m xpycode_master.python_server` 
- ✓ `xpycode_master/python_inspector/__main__.py` created with proper entry point
- ✓ `inspector.py` no longer has `if __name__ == "__main__":` block
- ✓ `inspector_launcher.py` calls `python -m xpycode_master.python_inspector`
- ✓ `xpycode_master/ide/__main__.py` exists (renamed from main.py)
- ✓ `ide_manager.py` calls `python -m xpycode_master.ide`
- ✓ `setup.py` CYTHON_MODULES list does not include `launcher.py`
- ✓ Building a wheel and running the application works without "No code object" errors (verified by test)
