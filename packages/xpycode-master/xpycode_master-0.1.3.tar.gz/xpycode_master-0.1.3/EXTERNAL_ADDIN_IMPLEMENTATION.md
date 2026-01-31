# External Addin Hosting Implementation Summary

## Overview
This implementation adds support for running XPyCode with the addin hosted externally at `https://addin.xpycode.com/{version}` while the business layer runs locally.

## Architecture

### Mode Selection
- **Local Mode (default)**: Addin served from localhost on a dynamically assigned port
- **External Mode**: Addin served from `https://addin.xpycode.com/{version}`, business layer runs locally

### Key Components

#### 1. Watchdog Process (`watchdog_xpc.py`)
**Purpose**: Manages lifecycle and configuration

**Changes**:
- New arguments: `--use-local-addin` and `--use-external-addin` (mutually exclusive)
- Validation: `--use-external-addin` cannot be combined with `--addin-port`
- When external mode is enabled, sets `addin_port = -1`
- Fixed routing bug: `/ports` endpoint now correctly calls `_handle_ports()`
- Enhanced `/health` endpoint with `app: "xpycode_watchdog"` identifier

**Usage**:
```bash
# Local mode (default)
python -m xpycode_master.watchdog_xpc

# External mode
python -m xpycode_master.watchdog_xpc --use-external-addin
```

#### 2. Launcher Process (`launcher.py`)
**Purpose**: Orchestrates component startup

**Changes**:
- Handles `addin_port == -1` as external mode signal
- Skips local addin server launch when in external mode
- Skips certificate generation (not needed for external hosting)
- New function: `prepare_external_manifest()` - replaces localhost URLs with external URL
- Enhanced: `register_manifest_with_excel()` - handles both modes

**Behavior in External Mode**:
1. Does NOT start AddinServerManager
2. Does NOT generate self-signed certificates
3. DOES generate manifest with external URLs
4. DOES register manifest with Excel
5. DOES start business layer server normally

#### 3. Configuration Module (`config.py`)
**Purpose**: Centralized configuration

**Changes**:
- Added synchronization comment for `WATCHDOG_PORTS`
- Implemented lazy evaluation: `get_external_addin_url()`
- Avoids circular imports by deferring version import

**Version Handling**:
```python
# Takes version like "0.1.0.dev5" and normalizes to "0.1.0"
version = '.'.join((__version__.split('.')+['0']*3)[:3])
EXTERNAL_ADDIN_URL = f'https://addin.xpycode.com/{version}'
```

#### 4. Client-Side Discovery (`addin/utils/config-utils.js`)
**Purpose**: Discover and connect to local watchdog

**Changes**:
- Complete rewrite of `reloadConfig()` function
- Detects external mode via `watchdogPort === -1` in config.json
- Implements port scanning to discover local watchdog
- Caches discovered port in localStorage
- Validates watchdog via `/health` endpoint
- Fetches configuration from `/ports` endpoint

**Discovery Flow**:
```
1. Fetch /config.json from addin server
2. If watchdogPort === -1 (external mode):
   a. Try cached port from localStorage
   b. If cache miss, scan WATCHDOG_PORTS sequentially
   c. Validate each port via /health endpoint
   d. Fetch config from /ports endpoint
   e. Cache successful port
3. Update window.XPYCODE_CONFIG
```

**Port Synchronization**:
- `WATCHDOG_PORTS` must be kept in sync between:
  - `xpycode_master/config.py` (Python)
  - `addin/utils/config-utils.js` (JavaScript)
- Currently: `[51171, 51172, 51173, 51174, 51175, 51176, 51177, 51178, 51179]`

#### 5. Static Configuration (`addin/config.json`)
**Purpose**: Initial config for external addin hosting

**Content**:
```json
{
    "serverPort": -1,
    "watchdogPort": -1,
    "authToken": "",
    "loggingLevel": "INFO",
    "docsPort": -1
}
```

**Meaning**: All `-1` values signal to the client that it needs to discover the local watchdog.

## Security Considerations

### 1. Watchdog Discovery
- Uses localhost-only connections for discovery
- Validates watchdog identity via `/health` endpoint
- Requires `status: "ok"` and `watchdog_port` field
- 2-second timeout per port attempt

### 2. Authentication
- Auth token still transmitted from watchdog to client
- All watchdog API calls (except /health and /ports) require auth
- CORS enabled for Office Add-in development

### 3. HTTPS
- External addin served over HTTPS (managed externally)
- Local business layer uses HTTP (localhost only)
- Certificate management not needed in external mode

## Testing

### Automated Tests (`test_external_addin.py`)
All tests passing:
1. ✓ Mockingargs dataclass fields
2. ✓ External URL generation
3. ✓ External manifest preparation
4. ✓ Local manifest preparation (backward compatibility)
5. ✓ Argument validation

### Security Scan
- CodeQL analysis: **0 alerts** (JavaScript and Python)
- No vulnerabilities detected

## Backward Compatibility

All changes are **fully backward compatible**:
- Running without `--use-external-addin` works exactly as before
- Existing code paths unchanged for local mode
- No breaking changes to APIs or interfaces

## Usage Examples

### Starting in External Mode
```bash
# From command line
python -m xpycode_master.watchdog_xpc --use-external-addin

# From Python code
from xpycode_master import start_master
start_master(use_external_addin=True)
```

### Starting in Local Mode (Default)
```bash
# From command line
python -m xpycode_master.watchdog_xpc

# Or explicitly
python -m xpycode_master.watchdog_xpc --use-local-addin

# From Python code
from xpycode_master import start_master
start_master()  # or start_master(use_local_addin=True)
```

## Files Modified

### Python Files
- `xpycode_master/watchdog_xpc.py` - Argument parsing, validation, spawning
- `xpycode_master/launcher.py` - External mode handling, manifest generation
- `xpycode_master/config.py` - External URL configuration

### JavaScript Files
- `addin/utils/config-utils.js` - Watchdog discovery, config loading

### Configuration Files
- `addin/config.json` - Static config for external mode

### Test Files
- `test_external_addin.py` - Comprehensive test suite (new)

## Future Considerations

1. **Port Range Exhaustion**: If all watchdog ports are in use, discovery will fail. Consider:
   - Expanding port range
   - Better error messaging to user

2. **Network Latency**: Port scanning with 2-second timeouts could be slow. Consider:
   - Parallel port scanning
   - Adaptive timeout based on first successful connection

3. **Cache Invalidation**: localStorage cache might become stale if:
   - Multiple instances running on different ports
   - Watchdog restarts on different port
   - Currently handled by validation on cached port before use

4. **External Hosting**: The external URL `https://addin.xpycode.com/{version}` must:
   - Serve the compiled addin files
   - Include proper CORS headers
   - Be version-specific (allows multiple versions)

## Deployment Checklist

When deploying external addin hosting:
- [ ] Build and deploy addin to `https://addin.xpycode.com/{version}/`
- [ ] Ensure all static assets are accessible
- [ ] Verify CORS headers allow Office Add-in origins
- [ ] Test manifest loading from external URL
- [ ] Verify watchdog discovery works from external addin
- [ ] Test with multiple simultaneous users
