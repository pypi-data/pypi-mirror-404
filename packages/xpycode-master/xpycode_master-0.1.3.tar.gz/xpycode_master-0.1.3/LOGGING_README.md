# Centralized Logging Configuration

## Overview

XPyCode Master now includes centralized logging configuration that works seamlessly across the main process and all subprocesses, with output to both console and a shared log file.

## Features

- **Centralized Configuration**: Single point of configuration for all logging
- **Shared Log File**: All processes write to the same timestamped log file
- **Environment-based Sharing**: Subprocesses inherit configuration via environment variables
- **Flexible Levels**: Support for DEBUG, INFO, WARNING, ERROR, CRITICAL levels
- **Console + File Output**: Dual output to both console and file (file is optional)
- **Custom Formatting**: Configurable log message format

## Quick Start

### Command Line Usage

```bash
# Default logging (INFO level, file enabled)
python -m xpycode_master

# Debug level logging
python -m xpycode_master --log-level DEBUG

# Custom format
python -m xpycode_master --log-format "%(asctime)s [%(levelname)s] %(message)s"

# Console only (no log file)
python -m xpycode_master --no-log-file

# Combined options
python -m xpycode_master --log-level DEBUG --no-log-file
```

### Programmatic Usage

#### Main Process

```python
from xpycode_master.logging_config import setup_logging_master, get_logger

# Setup logging (returns log file path)
log_file = setup_logging_master(
    level="INFO",           # Log level
    format_str=None,        # Use default format
    enable_file=True        # Enable file logging
)

# Get a logger
logger = get_logger(__name__)

# Log messages
logger.info("Application started")
logger.warning("This is a warning")
logger.error("This is an error")
```

#### Subprocess

```python
from xpycode_master.logging_config import setup_logging_subprocess, get_logger

# Setup subprocess logging (reads from environment variables)
setup_logging_subprocess()

# Get a logger
logger = get_logger(__name__)

# Log messages (will go to the same file as main process)
logger.info("Subprocess started")
```

## Log File Location

Log files are stored in:

- **Windows**: `C:\Users\<username>\.xpycode\logs\xpycode_2026-01-06_143052.log`
- **macOS**: `/Users/<username>/.xpycode/logs/xpycode_2026-01-06_143052.log`
- **Linux**: `/home/<username>/.xpycode/logs/xpycode_2026-01-06_143052.log`

Files are named with timestamps: `xpycode_YYYY-MM-DD_HHMMSS.log`

## How It Works

```
┌────────────────────────────────────────────────────────────────┐
│  xpycode_master (main process)                                  │
│                                                                │
│  1. Parse --log-level, --log-format, --no-log-file args        │
│  2. Generate log filename: xpycode_2026-01-06_143052.log       │
│  3. Set environment variables:                                  │
│     • XPYCODE_LOG_LEVEL=DEBUG                                  │
│     • XPYCODE_LOG_FORMAT=...                                   │
│     • XPYCODE_LOG_FILE=~/.xpycode/logs/xpycode_...log          │
│  4. Configure logging (console + file handlers)                │
│  5. Launch subprocesses (inherit env vars automatically)       │
└────────────────────────────────────────────────────────────────┘
         │
         ├──► addin_launcher subprocess
         │    └── Calls setup_logging_subprocess()
         │    └── Reads env vars → same log file
         │
         └──► ide subprocess
              └── Calls setup_logging_subprocess()
              └── Reads env vars → same log file
```

## API Reference

### `setup_logging_master(level, format_str, enable_file)`

Setup logging for the master process.

**Parameters:**
- `level` (str, optional): Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL). Default: "INFO"
- `format_str` (str, optional): Log format string. Default: `"%(asctime)s - %(name)s - %(levelname)s - %(message)s"`
- `enable_file` (bool, optional): Enable file logging. Default: True

**Returns:**
- `Path` or `None`: Path to log file if enabled, None otherwise

### `setup_logging_subprocess()`

Setup logging for a subprocess. Reads configuration from environment variables set by the master process.

**Parameters:** None

**Returns:** None

### `get_logger(name)`

Get a logger instance.

**Parameters:**
- `name` (str): Logger name (typically `__name__`)

**Returns:**
- `logging.Logger`: Logger instance

### `get_log_directory()`

Get the log directory path, creating it if needed.

**Returns:**
- `Path`: Path to log directory (`~/.xpycode/logs`)

### `generate_log_filename()`

Generate a timestamped log filename.

**Returns:**
- `Path`: Full path to log file with timestamp

## Environment Variables

The following environment variables are used to share configuration:

- `XPYCODE_LOG_LEVEL`: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `XPYCODE_LOG_FORMAT`: Log message format string
- `XPYCODE_LOG_FILE`: Path to shared log file

These are automatically set by `setup_logging_master()` and read by `setup_logging_subprocess()`.

## Examples

### Example 1: Basic Usage

```python
from xpycode_master.logging_config import setup_logging_master, get_logger

# Setup
log_file = setup_logging_master(level="INFO")
logger = get_logger("myapp")

# Log
logger.info("Application started")
logger.warning("Configuration loaded")
logger.error("Failed to connect to database")
```

**Output (console and file):**
```
2026-01-06 14:30:52,123 - myapp - INFO - Application started
2026-01-06 14:30:52,124 - myapp - WARNING - Configuration loaded
2026-01-06 14:30:52,125 - myapp - ERROR - Failed to connect to database
```

### Example 2: Debug Mode

```python
log_file = setup_logging_master(level="DEBUG")
logger = get_logger("myapp")

logger.debug("Debug info: config={'key': 'value'}")
logger.info("Processing started")
```

**Output:**
```
2026-01-06 14:30:52,123 - myapp - DEBUG - Debug info: config={'key': 'value'}
2026-01-06 14:30:52,124 - myapp - INFO - Processing started
```

### Example 3: Console Only

```python
log_file = setup_logging_master(level="INFO", enable_file=False)
# log_file will be None

logger = get_logger("myapp")
logger.info("This only goes to console")
```

### Example 4: Custom Format

```python
log_file = setup_logging_master(
    level="INFO",
    format_str="%(levelname)s - %(message)s"
)
logger = get_logger("myapp")
logger.info("Simple format")
```

**Output:**
```
INFO - Simple format
```

## Testing

Run the test suites:

```bash
# Unit tests
python test_logging_config.py

# Integration tests
python test_logging_integration.py

# Demonstration
python demo_logging.py
```

## Components Updated

The following components have been updated to use centralized logging:

1. **xpycode_master/launcher.py**: Main launcher with CLI arguments
2. **xpycode_master/addin_launcher/cli.py**: Addin launcher subprocess
3. **xpycode_master/ide/main.py**: IDE subprocess
4. **xpycode_master/business_layer/server.py**: Business layer server
5. **xpycode_master/__init__.py**: Package exports

## Migration Notes

### Converting from print() to logging

Before:
```python
print(f"Starting server on port {port}...")
print(f"Error: {e}")
```

After:
```python
from xpycode_master.logging_config import get_logger
logger = get_logger(__name__)

logger.info(f"Starting server on port {port}...")
logger.error(f"Error: {e}")
```

### Best Practices

1. **Use appropriate log levels**:
   - `DEBUG`: Detailed diagnostic information
   - `INFO`: General informational messages
   - `WARNING`: Warning messages (something unexpected but not an error)
   - `ERROR`: Error messages (something failed)
   - `CRITICAL`: Critical errors (application may not continue)

2. **Include context in messages**:
   ```python
   logger.info(f"Processing file: {filename}")
   logger.error(f"Failed to load config from {path}: {error}")
   ```

3. **Use structured logging for complex data**:
   ```python
   logger.debug(f"Config loaded: {config}")
   ```

4. **Keep user-facing messages as print()** for CLI tools:
   ```python
   print("✅ Server started successfully")  # User output
   logger.info(f"Server started on port {port}")  # Logging
   ```

## Troubleshooting

### Log file not created

- Check that `~/.xpycode/logs` directory exists and is writable
- Verify `--no-log-file` is not being used
- Check for error messages in console output

### Subprocess logs not appearing

- Ensure subprocess calls `setup_logging_subprocess()` at startup
- Verify environment variables are set (check `XPYCODE_LOG_FILE`)
- Make sure subprocess has file write permissions

### Log level not respected

- Check the level passed to `setup_logging_master()`
- Verify environment variable `XPYCODE_LOG_LEVEL` is set correctly
- Ensure no other code is calling `logging.basicConfig()` after setup

## Future Enhancements

Potential future improvements:

- Log rotation (size-based or time-based)
- Separate log files per component
- Remote logging support
- Structured logging (JSON format)
- Performance metrics logging
- Integration with logging aggregation services
