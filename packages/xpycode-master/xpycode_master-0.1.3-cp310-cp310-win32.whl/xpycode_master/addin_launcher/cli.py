# xpycode_master/addin_launcher/cli.py

import argparse
import sys
import time
from .server_manager import AddinServerManager
from .exceptions import AddinServerError
from ..logging_config import setup_logging_subprocess, get_logger

def main():
    # Setup logging first - reads from environment variables set by master process
    setup_logging_subprocess()
    logger = get_logger(__name__)
    
    parser = argparse.ArgumentParser(
        prog='xpycode_master.addin_launcher',
        description='XPyCode Excel Add-in Server Launcher'
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Start command
    start_parser = subparsers.add_parser('start', help='Start the addin server')
    mode_group = start_parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--dev', action='store_true',
        help='Use Node.js (development mode)'
    )
    mode_group.add_argument(
        '--prod', action='store_true',
        help='Use compiled binary (production mode)'
    )
    start_parser.add_argument(
        '--port', type=int, default=3000,
        help='Port number for addin server (default: 3000)'
    )
    start_parser.add_argument(
        '--server-port', type=int, default=8000,
        help='Port number for business layer server (default: 8000)'
    )
    start_parser.add_argument(
        '--watchdog-port', type=int, default=0,
        help='Port number for watchdog HTTP API (default: 0)'
    )
    start_parser.add_argument(
        '--auth-token', type=str, default='',
        help='Auth token for watchdog API'
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
        use_compiled = args.prod  # Default to dev mode if neither specified
        manager = AddinServerManager(
            use_compiled=use_compiled, 
            port=args.port,
            server_port=args.server_port,
            watchdog_port=args.watchdog_port,
            auth_token=args.auth_token
        )
        
        try:
            manager.start()
            mode = "production" if use_compiled else "development"
            logger.info(f"Addin launcher subprocess starting")
            # Keep user-facing messages as print for CLI output
            print(f"✅ Server started in {mode} mode")
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
        except AddinServerError as e:
            logger.error(f"Addin server error: {e}")
            print(f"❌ Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == 'status':
        # Simple port check
        import socket
        port = 3000
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.settimeout(1)
                s.connect(('localhost', port))
                print(f"✅ Server is running on port {port}")
            except (socket.timeout, ConnectionRefusedError, OSError):
                print(f"❌ Server is not running on port {port}")
    
    elif args.command == 'stop':
        print("Note: 'stop' command requires the PID. Use Ctrl+C if running in foreground.")
        print("Or use Task Manager / kill command to stop the process.")
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
