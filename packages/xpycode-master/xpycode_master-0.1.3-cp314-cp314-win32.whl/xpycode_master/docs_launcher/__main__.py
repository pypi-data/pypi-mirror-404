"""
Command-line interface entry point for documentation server launcher.
"""

import argparse
import sys
import time
from .server_manager import DocsServerManager
from ..logging_config import setup_logging_subprocess, get_logger


def main():
    # Setup logging first - reads from environment variables set by master process
    setup_logging_subprocess()
    logger = get_logger(__name__)
    
    parser = argparse.ArgumentParser(
        prog='xpycode_master.docs_launcher',
        description='XPyCode Documentation Server Launcher'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the documentation server')
    start_parser.add_argument(
        '--port', type=int, default=8100,
        help='Port number for documentation server (default: 8100)'
    )
    start_parser.add_argument(
        '--foreground', '-f', action='store_true',
        help='Run in foreground (Ctrl+C to stop)'
    )
    
    # Status command
    subparsers.add_parser('status', help='Check server status')
    
    # Stop command
    subparsers.add_parser('stop', help='Stop the server')
    
    args = parser.parse_args()
    
    if args.command == 'start':
        manager = DocsServerManager(port=args.port)
        
        try:
            manager.start()
            logger.info(f"Documentation server subprocess starting")
            # Keep user-facing messages as print for CLI output
            print(f"✅ Documentation server started")
            print(f"   URL: {manager.url}")
            print(f"   PID: {manager.pid}")
            
            if args.foreground:
                print("\nPress Ctrl+C to stop...")
                try:
                    while manager.is_running:
                        time.sleep(1)
                except KeyboardInterrupt:
                    print("\nStopping server...")
                    manager.stop()
                    print("✅ Server stopped")
        except Exception as e:
            logger.error(f"Documentation server error: {e}")
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'status':
        # Simple port check - use default DOCS_PORTS from config
        import socket
        from ..config import DOCS_PORTS
        port = DOCS_PORTS[0]  # Use first port from the range
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect(('127.0.0.1', port))
                print(f"✅ Documentation server is running on port {port}")
            except (socket.timeout, ConnectionRefusedError, OSError):
                print(f"❌ Documentation server is not running on port {port}")
    
    elif args.command == 'stop':
        print("Note: 'stop' command requires the PID. Use Ctrl+C if running in foreground.")
        print("Or use Task Manager / kill command to stop the process.")
    
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
