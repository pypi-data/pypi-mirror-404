# Kill Kernel Action Implementation Summary

## Overview
This implementation adds a new "Kill Kernel" advanced action to both the Excel Add-in and the IDE, allowing users to forcefully terminate and restart a Python kernel for a specific workbook.

## Files Modified

### 1. Add-in: `addin/advanced-actions/actions-config.js`
**Changes:**
- Added `killKernelAction()` function (lines 113-120)
  - Gets workbook ID from `window._xpycode_workbookId` or defaults to empty string
  - Sends `kill_kernel` message with `workbook_id` payload to business layer
  - Logs action for debugging

- Registered action in `ADVANCED_ACTIONS_CONFIG` Master tab (lines 160-165)
  - Short name: "Kill Kernel"
  - Description: "Stop and restart the Python Kernel for this workbook"
  - No input required (hasInput: false)

### 2. Business Layer: `xpycode_master/business_layer/server.py`
**Changes:**
- Added `signal` import (line 18) for Unix process management

- Added `kill_and_restart_kernel()` method (lines 658-727)
  - Checks if kernel exists for workbook
  - Platform-specific hard kill:
    - Windows: Uses `taskkill /F /T /PID` to force kill process tree
    - Unix: Uses SIGTERM with timeout, then SIGKILL if needed
    - Improved process checking with `os.kill(pid, 0)` instead of process group check
  - Removes from `kernel_processes` tracking
  - Removes from `active_connections['kernel']` if exists
  - Waits 0.5 seconds for cleanup
  - Spawns new kernel
  - Returns True on success, False on failure

- Added `handle_kill_kernel()` async handler (lines 2542-2570)
  - Gets `workbook_id` from message, falls back to `client_id` if not provided
  - Calls `kill_and_restart_kernel()`
  - Sends `kill_kernel_response` to both add-in and IDE
  - Response includes `workbook_id` and `success` status

- Updated `MESSAGE_HANDLERS` dictionary
  - Added to "addin" section (line 2591)
  - Added to "ide" section (line 2660)

### 3. IDE: `xpycode_master/ide/gui/advanced_actions.py` (NEW FILE)
**Purpose:** Dynamic configuration system for advanced actions

**Contents:**
- `AdvancedAction` dataclass with short_name, description, and action_function
- `ADVANCED_ACTIONS_CONFIG` dictionary storing actions by tab name
- `register_action()` - Register an action under a tab
- `get_tabs()` - Get list of tab names
- `get_actions()` - Get actions for a specific tab
- `clear_actions()` - Clear all registered actions

### 4. IDE: `xpycode_master/ide/gui/main_window.py`
**Changes:**
- Added import (line 52): `from .advanced_actions import ...`

- Added `_setup_advanced_menu()` method (lines 576-594)
  - Clears and registers actions
  - Creates Advanced menu in menu bar
  - Dynamically creates submenus for each tab
  - Adds actions with tooltips and connections

- Added `_register_advanced_actions()` method (lines 596-603)
  - Registers "Kill Kernel" action under "Master" tab
  - Connects to `_advanced_kill_kernel_dialog()`

- Added `_advanced_kill_kernel_dialog()` method (lines 605-636)
  - Shows warning if no workbooks connected
  - Builds list of workbook names from `_workbook_names` dict
  - Shows `QInputDialog.getItem()` for workbook selection
  - Calls `_send_kill_kernel()` with selected workbook ID

- Added `_send_kill_kernel()` method (lines 638-651)
  - Creates JSON message with type "kill_kernel" and workbook_id
  - Sends via WebSocket
  - Logs to console and logger

- Updated `_setup_menu_bar()` method (line 560)
  - Added call to `_setup_advanced_menu(menu_bar)` before Help menu

### 5. Tests: `test_kill_kernel.py` (NEW FILE)
**Test Coverage:**
- `test_kill_and_restart_kernel_no_kernel()` - Returns False when kernel doesn't exist
- `test_kill_and_restart_kernel_windows()` - Tests Windows taskkill method
- `test_kill_and_restart_kernel_unix()` - Tests Unix SIGTERM/SIGKILL method
- `test_kill_and_restart_kernel_cleans_up_connections()` - Verifies cleanup
- `test_handle_kill_kernel_async()` - Tests async handler with mocks
- `test_handle_kill_kernel_fallback_async()` - Tests client_id fallback

## Implementation Details

### Message Flow
1. **Add-in → Business Layer:**
   - User clicks "Kill Kernel" in Add-in Advanced Actions
   - Add-in sends `{type: "kill_kernel", workbook_id: "..."}` message
   - Business layer receives via "addin" handler

2. **IDE → Business Layer:**
   - User selects "Advanced > Master > Kill Kernel" in IDE menu
   - Dialog shows workbook names, user selects one
   - IDE sends `{type: "kill_kernel", workbook_id: "..."}` message
   - Business layer receives via "ide" handler

3. **Business Layer Processing:**
   - Handler gets workbook_id (falls back to client_id if empty)
   - Calls `kill_and_restart_kernel(workbook_id)`
   - Sends response to both add-in and IDE

4. **Response:**
   - `{type: "kill_kernel_response", workbook_id: "...", success: true/false}`

### Platform-Specific Kill Logic

**Windows:**
```bash
taskkill /F /T /PID <pid>
```
- `/F` = Force termination
- `/T` = Terminate process tree (child processes too)
- `/PID` = Specify process ID

**Unix/Linux:**
```python
os.killpg(os.getpgid(pid), signal.SIGTERM)  # Try graceful shutdown
time.sleep(0.2)
os.kill(pid, 0)  # Check if still alive
os.killpg(os.getpgid(pid), signal.SIGKILL)  # Force kill if needed
```

### Key Design Decisions

1. **workbook_id takes precedence:** The message payload's `workbook_id` is used first, allowing IDE to kill kernels for any workbook, not just the one that sent the message.

2. **Hard kill with restart:** Unlike the existing `terminate_kernel()` which uses `.terminate()`, this uses platform-specific force kill to ensure the process is really stopped, then spawns a fresh kernel.

3. **Comprehensive cleanup:** Removes from both `kernel_processes` tracking and `active_connections['kernel']` to ensure clean state.

4. **Dynamic menu system:** The IDE uses a configuration-based system that makes it easy to add more advanced actions in the future.

5. **User-friendly dialog:** IDE shows workbook names (not IDs) in the selection dialog for better UX.

## Testing

### Unit Tests
- 6 test cases covering various scenarios
- Platform-specific mocking for Windows and Unix
- Async handler testing with AsyncMock

### Code Review
- ✅ All review comments addressed
- ✅ Improved process checking (using `os.kill(pid, 0)` instead of process group check)
- ✅ Removed unused imports
- ✅ Added timeout verification before SIGKILL

### Security Scan
- ✅ CodeQL found 0 alerts
- ✅ No security vulnerabilities introduced

### Syntax Validation
- ✅ All Python files compile successfully
- ✅ JavaScript file passes Node.js syntax check

## Usage

### From Add-in
1. Open Advanced Actions panel
2. Navigate to "Master" tab
3. Click "Kill Kernel"
4. Kernel for current workbook will be killed and restarted

### From IDE
1. Click "Advanced" menu
2. Navigate to "Master" submenu
3. Click "Kill Kernel"
4. Select workbook from dialog
5. Kernel for selected workbook will be killed and restarted

## Benefits

1. **Recovery from hangs:** Users can recover from kernel deadlocks without restarting Master
2. **Clean slate:** Fresh kernel without accumulated state issues
3. **Multi-workbook support:** IDE can kill kernel for any connected workbook
4. **Safe operation:** Proper cleanup ensures no zombie processes or connection leaks
5. **Extensible:** New advanced actions can be easily added using the configuration system

## Statistics

- **5 files changed**
- **411 lines added**
- **0 security vulnerabilities**
- **0 compilation errors**
- **6 unit tests**
