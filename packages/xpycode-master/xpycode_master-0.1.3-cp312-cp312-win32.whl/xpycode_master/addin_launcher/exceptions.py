# xpycode_master/addin_launcher/exceptions.py

class AddinServerError(Exception):
    """Base exception for addin server errors."""
    pass

class ServerStartError(AddinServerError):
    """Raised when the server fails to start."""
    pass

class ServerStopError(AddinServerError):
    """Raised when the server fails to stop."""
    pass

class ServerNotRunningError(AddinServerError):
    """Raised when an operation requires a running server but none exists."""
    pass

class BinaryNotFoundError(AddinServerError):
    """Raised when the compiled binary is not found."""
    pass
