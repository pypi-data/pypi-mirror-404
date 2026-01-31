"""
XPyCode Master Package Entry Point

Starts the watchdog process which manages the xpycode_master lifecycle.
"""

from .watchdog_xpc import main

if __name__ == "__main__":
    main()
