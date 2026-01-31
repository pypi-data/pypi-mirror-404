"""
Centralized Logging Configuration for XPyCode Master

This module provides centralized logging configuration that works across
the main process and all subprocesses, with output to both console and
a shared log file.

Environment variables are used to share configuration between processes:
- XPYCODE_LOG_LEVEL: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- XPYCODE_LOG_FORMAT: Format string for log messages
- XPYCODE_LOG_FILE: Path to shared log file

Usage in main process:
    from xpycode_master.logging_config import setup_logging_master, get_logger
    
    log_file = setup_logging_master(level="INFO")
    logger = get_logger(__name__)
    logger.info("Application started")

Usage in subprocess:
    from xpycode_master.logging_config import setup_logging_subprocess, get_logger
    
    setup_logging_subprocess()
    logger = get_logger(__name__)
    logger.info("Subprocess started")
"""

import os
import sys
import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

# Environment variable names for sharing config with subprocesses
ENV_LOG_LEVEL = "XPYCODE_LOG_LEVEL"
ENV_LOG_FORMAT = "XPYCODE_LOG_FORMAT"
ENV_LOG_FILE = "XPYCODE_LOG_FILE"
ENV_LOG_TO_CONSOLE = "XPYCODE_LOG_TO_CONSOLE"

# Default values
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def fix_windows_console_encoding():
    """
    Fix Windows console encoding for Unicode characters.
    
    Wraps sys.stdout and sys.stderr with UTF-8 encoding on Windows to prevent
    UnicodeEncodeError when outputting Unicode characters that are not supported
    by the default Windows console encoding (cp1252).
    
    This should be called at the entry point of the application before any
    output is generated.
    """
    if sys.platform == 'win32':
        try:
            # safest when stdout is a real TextIOWrapper
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return
    if sys.platform == 'win32':
        try:
            # Check encoding case-insensitively (can be 'UTF-8' or 'utf-8')
            if hasattr(sys.stdout, 'buffer') and sys.stdout.encoding.lower() != 'utf-8':
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            if hasattr(sys.stderr, 'buffer') and sys.stderr.encoding.lower() != 'utf-8':
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        except Exception:
            pass  # Ignore if already wrapped or not supported


def get_log_directory() -> Path:
    """Get the log directory, creating if needed."""
    log_dir = Path.home() / ".xpycode" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir


def generate_log_filename() -> Path:
    """Generate a timestamped log filename for this session."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    return get_log_directory() / f"xpycode_{timestamp}.log"


def setup_logging_master(
    level: Optional[str] = None,
    format_str: Optional[str] = None,
    enable_file: bool = True,
    enable_console: bool = True
) -> Optional[Path]:
    """
    Setup logging for the master process.
    Sets environment variables so subprocesses can use the same configuration.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_str: Logging format string
        enable_file: Whether to enable file logging
        enable_console: Whether to enable console logging
    
    Returns:
        Path to log file if file logging is enabled, None otherwise
    """
    # Determine settings (use provided or defaults)
    log_level = (level or DEFAULT_LOG_LEVEL).upper()
    log_format = format_str or DEFAULT_LOG_FORMAT
    log_file = generate_log_filename() if enable_file else None
    
    # Set environment variables for subprocesses to inherit
    os.environ[ENV_LOG_LEVEL] = log_level
    os.environ[ENV_LOG_FORMAT] = log_format
    if log_file:
        os.environ[ENV_LOG_FILE] = str(log_file)
    elif ENV_LOG_FILE in os.environ:
        del os.environ[ENV_LOG_FILE]
    
    # Set console logging preference
    os.environ[ENV_LOG_TO_CONSOLE] = "1" if enable_console else "0"
    
    # Configure logging for this process
    _configure_logging(log_level, log_format, log_file, enable_console)
    
    return log_file


def setup_logging_subprocess():
    """
    Setup logging for a subprocess.
    Reads configuration from environment variables set by the master process.
    This ensures all subprocesses use the same logging settings and log file.
    """
    log_level = os.environ.get(ENV_LOG_LEVEL, DEFAULT_LOG_LEVEL)
    log_format = os.environ.get(ENV_LOG_FORMAT, DEFAULT_LOG_FORMAT)
    log_file_str = os.environ.get(ENV_LOG_FILE)
    log_file = Path(log_file_str) if log_file_str else None
    enable_console = os.environ.get(ENV_LOG_TO_CONSOLE, "1") == "1"
    
    _configure_logging(log_level, log_format, log_file, enable_console)


def _parse_log_level(level: str) -> int:
    """
    Parse log level string to logging level constant.
    
    Args:
        level: Log level string (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Returns:
        Logging level constant, defaults to INFO if invalid
    """
    return getattr(logging, level.upper(), logging.INFO)


def _configure_logging(level: str, format_str: str, log_file: Optional[Path], enable_console: bool = True):
    """
    Configure the Python logging system with console and optional file handlers.
    
    Args:
        level: Logging level string
        format_str: Format string for log messages
        log_file: Path to log file, or None to disable file logging
        enable_console: Whether to enable console logging
    """
    # Get root logger
    root_logger = logging.getLogger()
    log_level = _parse_log_level(level)
    root_logger.setLevel(log_level)
    
    # Clear any existing handlers to avoid duplicates
    root_logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Console handler (stdout) - only add if enabled
    if enable_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        
        # Fix Windows console encoding for Unicode characters
        # Only wrap if stdout hasn't already been wrapped with UTF-8
        # Check encoding case-insensitively (can be 'UTF-8' or 'utf-8')
        '''
        if sys.platform == 'win32' and sys.stdout.encoding.lower() != 'utf-8':
            try:
                console_handler.stream = io.TextIOWrapper(
                    sys.stdout.buffer,
                    encoding='utf-8',
                    errors='replace'
                )
            except Exception:
                pass  # Fallback to default if wrapping fails
        
        '''
            
        root_logger.addHandler(console_handler)
    # File handler (if enabled)
    if log_file:
        try:
            file_handler = logging.FileHandler(log_file, encoding='utf-8',errors='replace')
            file_handler.setLevel(log_level)
            file_handler.setFormatter(formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # If we can't create the file handler, log to console only
            root_logger.warning(f"Could not create log file {log_file}: {e}")


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.
    Convenience function for consistent logger naming.
    
    Args:
        name: Logger name (typically __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
