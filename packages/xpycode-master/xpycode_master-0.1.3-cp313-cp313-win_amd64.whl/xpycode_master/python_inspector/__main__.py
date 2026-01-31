"""
Python Inspector Package Entry Point

Starts the Python Inspector service.
"""
import sys
import asyncio
from .inspector import main

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m xpycode_master.python_inspector <port>", file=sys.stderr)
        sys.exit(1)

    port = sys.argv[1]
    try:
        asyncio.run(main(port))
    except KeyboardInterrupt:
        print("Inspector service terminated")
