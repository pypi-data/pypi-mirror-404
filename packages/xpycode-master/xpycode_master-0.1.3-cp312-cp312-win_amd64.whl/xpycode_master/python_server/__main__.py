"""
Python Server Package Entry Point

Starts the Python Kernel for a workbook.
"""
import sys
import asyncio
from .kernel import main

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python -m xpycode_master.python_server <workbook_id> <port>", file=sys.stderr)
        sys.exit(1)

    workbook_id = sys.argv[1]
    port = sys.argv[2]
    #print(f"Starting Python Kernel for workbook: {workbook_id} port:{port}")
    asyncio.run(main(workbook_id, port))
