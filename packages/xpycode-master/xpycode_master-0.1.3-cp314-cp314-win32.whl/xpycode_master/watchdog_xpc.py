"""
XPyCode Watchdog Process

Manages the xpycode_master lifecycle with HTTP API for kill/restart.
"""

import argparse
from dataclasses import dataclass
import json
import os
import secrets
import signal
import subprocess
import sys
import io
import threading
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Optional, Dict, Any

# Platform-specific imports
if sys.platform == 'win32':
    import msvcrt
else:
    import fcntl

from .config import ADDIN_PORTS, DOCS_PORTS, SERVER_PORTS, WATCHDOG_PORTS, find_available_port
from .logging_config import setup_logging_master, get_logger, fix_windows_console_encoding

# Fix Windows console encoding for Unicode characters
fix_windows_console_encoding()

# Constants
PORT_DISCOVERY_PREFIX = "XPYCODE_PORTS:"


class SingleInstanceLock:
    """Cross-platform file lock for single instance."""
    
    def __init__(self):
        xpycode_dir = Path.home() / ".xpycode"
        xpycode_dir.mkdir(parents=True, exist_ok=True)
        self.lock_file_path = xpycode_dir / "xpycode_master.lock"
        self.lock_file = None
    
    def acquire(self) -> bool:
        try:
            self.lock_file = open(self.lock_file_path, 'w')
            if sys.platform == 'win32':
                msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.lock_file.write(str(os.getpid()))
            self.lock_file.flush()
            return True
        except (IOError, OSError):
            if self.lock_file:
                self.lock_file.close()
            return False
    
    def release(self):
        if self.lock_file:
            try:
                if sys.platform == 'win32':
                    msvcrt.locking(self.lock_file.fileno(), msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(self.lock_file.fileno(), fcntl.LOCK_UN)
                self.lock_file.close()
                self.lock_file_path.unlink(missing_ok=True)
            except Exception:
                pass


class WatchdogState:
    """Shared state for watchdog."""
    
    def __init__(self):
        self.launcher_process: Optional[subprocess.Popen] = None
        self.saved_args: Dict[str, Any] = {}
        self.auth_token: str = ""
        self.watchdog_port: int = 0
        self.start_time: float = time.time()
        self.should_exit: bool = False
        self.lock = threading.Lock()


# Global state
state = WatchdogState()
logger = None


class WatchdogAPIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for watchdog API."""
    
    def log_message(self, format, *args):
        if logger:
            logger.debug(f"[WatchdogAPI] {format % args}")
    
    def _send_json_response(self, status_code: int, data: dict):
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())
    
    def _check_auth(self) -> bool:
        auth_header = self.headers.get('Authorization', '')
        expected = f"Bearer {state.auth_token}"
        return auth_header == expected
    
    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Authorization, Content-Type')
        self.end_headers()
    
    def do_GET(self):
        if self.path == '/health':
            self._handle_health()
        elif self.path == '/ports':
            self._handle_ports()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def do_POST(self):
        if self.path == '/kill':
            self._handle_kill()
        elif self.path == '/restart':
            self._handle_restart()
        else:
            self._send_json_response(404, {"error": "Not found"})
    
    def _handle_health(self):
        """GET /health - No auth required."""
        from . import __version__
        
        #with state.lock:
        #    pid = state.launcher_process.pid if state.launcher_process else None
        #    running = state.launcher_process is not None and state.launcher_process.poll() is None
        
        self._send_json_response(200, {
            "status": "ok",
            "app": "xpycode_watchdog",
            "python_version": __version__,
            "version": __version__ if state.saved_args.get("addin_port", 0)==-1 else 'last', #if the addin is local always use 'last'
            #"launcher_pid": pid,
            #"launcher_running": running,
            "uptime": int(time.time() - state.start_time),
            "watchdog_port": state.watchdog_port,
            "logging_level": state.saved_args.get("log_level", "INFO"),
        })

    def _handle_ports(self):
        """GET /ports - No auth required."""
        args=state.saved_args.copy()
        
        self._send_json_response(200, {
            "uptime": int(time.time() - state.start_time),
            "server_port": args.get("server_port", 0),
            "addin_port": args.get("addin_port", 0),
            "docs_port": args.get("docs_port", 0),
            "watchdog_port": state.watchdog_port,
            "auth_token": state.auth_token,
        })

    
    def _handle_kill(self):
        """POST /kill - Auth required."""
        if not self._check_auth():
            self._send_json_response(401, {"error": "Unauthorized"})
            return
        
        logger.info("[Watchdog] Kill requested")
        self._send_json_response(200, {"status": "killing"})
        
        # Kill in separate thread to allow response to be sent
        def do_kill():
            time.sleep(0.1)
            _kill_launcher()
            state.should_exit = True
        
        threading.Thread(target=do_kill, daemon=True).start()
    
    def _handle_restart(self):
        """POST /restart - Auth required."""
        if not self._check_auth():
            self._send_json_response(401, {"error": "Unauthorized"})
            return
        
        logger.info("[Watchdog] Restart requested")
        self._send_json_response(200, {"status": "restarting"})
        
        # Restart in separate thread to allow response to be sent
        def do_restart():
            time.sleep(0.1)
            _kill_launcher()
            time.sleep(0.5)  # Brief pause before restart
            _spawn_launcher()
        
        threading.Thread(target=do_restart, daemon=True).start()


def _kill_launcher():
    """Kill the launcher subprocess."""
    with state.lock:
        if state.launcher_process and state.launcher_process.poll() is None:
            logger.info(f"[Watchdog] Killing launcher (PID: {state.launcher_process.pid})")
            pid = state.launcher_process.pid
            
            try:
                if sys.platform == 'win32':
                    subprocess.run(
                        ['taskkill', '/F', '/T', '/PID', str(state.launcher_process.pid)],
                        capture_output=True
                    )
                    #state.launcher_process.kill()
                else:
                    # Get process group ID before attempting to kill
                    try:
                        pgid = os.getpgid(pid)
                        os.killpg(pgid, signal.SIGKILL)
                    except (ProcessLookupError, OSError) as e:
                        # Process already terminated or no process group
                        logger.debug(f"[Watchdog] Process already terminated: {e}")
                        state.launcher_process = None
                        return
                
            except Exception as e:
                logger.error(f"[Watchdog] Error killing launcher: {e}")
            finally:
                state.launcher_process = None


def _spawn_launcher():
    """Spawn the launcher subprocess with saved args."""
    global logger
    
    cmd = [sys.executable, "-m", "xpycode_master.launcher"]
    
    # Add saved args
    args = state.saved_args
    
    if args.get("log_level"):
        cmd.extend(["--log-level", args["log_level"]])
    if args.get("log_format"):
        cmd.extend(["--log-format", args["log_format"]])
    if args.get("no_log_file"):
        cmd.append("--no-log-file")
    if args.get("log_to_console"):
        cmd.append("--log-to-console")
    if args.get("dev_mode"):
        cmd.append("--dev")
    else:
        cmd.append("--prod")
    
    # Add watchdog info
    cmd.extend(["--watchdog-port", str(state.watchdog_port)])
    cmd.extend(["--auth-token", state.auth_token])
    
    # Add discovered ports if available (for restart)
    # Note: addin_port can be -1 for external addin mode
    if args.get("addin_port") is not None:
        cmd.extend(["--addin-port", str(args["addin_port"])])
    if args.get("server_port"):
        cmd.extend(["--server-port", str(args["server_port"])])
    if args.get("docs_port"):
        cmd.extend(["--docs-port", str(args["docs_port"])])

    if args.get("skip_manifest"):
        cmd.append("--skip-manifest")

    logger.info(f"[Watchdog] Spawning launcher: {' '.join(cmd)}")
    
    # Create subprocess with stdout pipe for port discovery
    kwargs = {
        #"stdout": subprocess.PIPE,
        "stderr": subprocess.STDOUT,
        "bufsize": 1,
        "encoding": "utf-8",           # CHANGED: explicit UTF-8
        "errors": "replace", 
    }
    
    if sys.platform != 'win32':
        kwargs["preexec_fn"] = os.setsid
    else:
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    
    with state.lock:
        state.launcher_process = subprocess.Popen(cmd, **kwargs)
    
    # Start thread to read stdout and look for port discovery
    threading.Thread(target=_read_launcher_output, daemon=True).start()


def _read_launcher_output():
    """Read launcher stdout, parse port discovery, forward to logger."""
    global logger
    
    proc = state.launcher_process
    if not proc or not proc.stdout:
        return
    
    try:
        for line in proc.stdout:
            line = line.rstrip()
            
            # Check for port discovery
            if line.startswith(PORT_DISCOVERY_PREFIX):
                try:
                    json_str = line[len(PORT_DISCOVERY_PREFIX):].strip()
                    ports = json.loads(json_str)
                    with state.lock:
                        if "addin_port" in ports:
                            state.saved_args["addin_port"] = ports["addin_port"]
                        if "server_port" in ports:
                            state.saved_args["server_port"] = ports["server_port"]
                        if "docs_port" in ports:
                            state.saved_args["docs_port"] = ports["docs_port"]
                    logger.info(f"[Watchdog] Discovered ports: {ports}")
                except json.JSONDecodeError as e:
                    logger.error(f"[Watchdog] Failed to parse ports: {e}")
            else:
                # Forward to logger
                #print(line)
                pass
    except OSError as e: 
        # Process terminated or stdout closed - this is expected
        logger.debug(f"[Watchdog] Launcher output stream closed: {e}")
    except Exception as e: 
        # Unexpected error - log but don't crash
        logger.warning(f"[Watchdog] Error reading launcher output: {e}")

@dataclass
class Mockingargs:
    log_level: str="INFO"
    log_format: Optional[str]=None
    no_log_file: bool=False
    dev: bool=False
    prod: bool=True
    addin_port=0
    server_port=0
    docs_port=0
    skip_manifest: bool=False
    log_to_console: bool=False
    use_local_addin: bool=False
    use_external_addin: bool=False


def clear_certificates():
    """Clear XPyCode certificates by running platform-specific script."""
    utils_dir = Path(__file__).parent / "utils"
    
    if sys.platform == 'win32':
        script = utils_dir / "delete_certs.bat"
        if script.exists():
            subprocess.run([str(script)], shell=True)
        else:
            print(f"Script not found: {script}")
    else:
        script = utils_dir / "delete_certs.sh"
        if script.exists():
            subprocess.run(["bash", str(script)])
        else:
            print(f"Script not found: {script}")


def clear_python_cache():
    """Clear the XPyCode Python package cache."""
    import shutil
    
    cache_dir = Path.home() / ".xpycode" / ".xpycode_packages"
    
    if cache_dir.exists():
        try:
            shutil.rmtree(cache_dir)
            print(f"Successfully deleted Python cache: {cache_dir}")
        except Exception as e:
            print(f"Error deleting Python cache: {e}")
    else:
        print(f"Python cache directory not found: {cache_dir}")


def main():
    
    # Parse arguments
    parser = argparse.ArgumentParser(description='XPyCode Watchdog')
    
    # Standalone arguments (mutually exclusive with everything else)
    standalone_group = parser.add_mutually_exclusive_group()
    standalone_group.add_argument('--clear-certificate', action='store_true',
                                   help='Clear all XPyCode certificates and exit')
    standalone_group.add_argument('--clear-python-cache', action='store_true',
                                   help='Clear Python package cache and exit')
    standalone_group.add_argument('--version', action='store_true', help='Show version and exit')
    
    parser.add_argument("--addin-port", type=int, default=0,
                        help="Port for addin server (auto-selected if not specified or 0)")
    
    # Addin mode arguments (mutually exclusive)
    addin_mode_group = parser.add_mutually_exclusive_group()
    addin_mode_group.add_argument('--use-local-addin', action='store_true',
                                  help='Use local addin server (default behavior, for future use)')
    addin_mode_group.add_argument('--use-external-addin', action='store_true',
                                  help='Use external addin at addin.xpycode.com (sets addin_port to -1)')
    
    parser.add_argument("--server-port", type=int, default=0,
                        help="Port for business layer server (auto-selected if not specified or 0)")
    parser.add_argument("--docs-port", type=int, default=0,
                        help="Port for documentation server (auto-selected if not specified or 0)")
    parser.add_argument("--skip-manifest", action="store_true",
                        help="Skip manifest installation")

    parser.add_argument('--local-docs', action='store_true', help='Launch local docs server')


    parser.add_argument('--log-level', default='INFO', help='Log level')
    parser.add_argument('--log-format', default=None, help='Log format')
    parser.add_argument('--no-log-file', action='store_true', help='Disable log file')
    parser.add_argument('--log-to-console', action='store_true', help='Enable console logging output')
    parser.add_argument('--dev', action='store_true', help='Development mode')
    parser.add_argument('--prod', action='store_true', help='Production mode (default)')
    args = parser.parse_args()
    
    # Validate external addin mode
    if args.use_external_addin:
        if args.addin_port != 0:
            parser.error("--use-external-addin cannot be combined with --addin-port")
        # Set addin_port to -1 for external mode
        args.addin_port = -1
    
    # Handle standalone commands first - check they are used alone
    if args.clear_certificate:
        # Check if any non-default arguments were provided
        if (args.log_level != 'INFO' or args.log_format is not None or 
            args.no_log_file or args.log_to_console or args.dev or args.prod):
            parser.error("--clear-certificate cannot be combined with other arguments")
        clear_certificates()
        sys.exit(0)
    
    if args.clear_python_cache:
        # Check if any non-default arguments were provided
        if (args.log_level != 'INFO' or args.log_format is not None or 
            args.no_log_file or args.log_to_console or args.dev or args.prod):
            parser.error("--clear-python-cache cannot be combined with other arguments")
        clear_python_cache()
        sys.exit(0)
    
    # Handle version request
    if args.version:
        from . import __version__
        print(f"xpycode_master {__version__}")
        sys.exit(0)
    
    _main(args)

def start_master(log_level: str="INFO", log_format: Optional[str]=None, no_log_file: bool=False, dev: bool=False, prod: bool=True,
                 addin_port:int=0,
                 server_port:int=0,
                    docs_port:int=0,
                    skip_manifest: bool=False,
                    use_local_addin: bool=False,
                    use_external_addin: bool=False,
                 ):
    # Validate external addin mode
    if use_external_addin:
        if addin_port != 0:
            raise ValueError("use_external_addin cannot be combined with addin_port != 0")
        addin_port = -1
    
    args = Mockingargs(
        log_level=log_level,
        log_format=log_format,
        no_log_file=no_log_file,
        dev=dev,
        prod=prod,
        addin_port=addin_port,
        server_port=server_port,
        docs_port=docs_port,
        skip_manifest=skip_manifest,
        use_local_addin=use_local_addin,
        use_external_addin=use_external_addin,
    )
    _main(args)


def _main(args):    
    global logger
    # Setup logging
    setup_logging_master(
        level=args.log_level,
        format_str=args.log_format,
        enable_file=not args.no_log_file,
        enable_console=args.log_to_console
    )
    logger = get_logger(__name__)
    
    # Acquire single instance lock
    lock = SingleInstanceLock()
    if not lock.acquire():
        print("ERROR: Another instance of xpycode_master is already running.")
        sys.exit(1)
    
    logger.info("[Watchdog] Starting...")
    
    try:
        # Find available watchdog port
        state.watchdog_port = find_available_port(WATCHDOG_PORTS)
        if not state.watchdog_port:
            logger.error("[Watchdog] No available watchdog port")
            sys.exit(1)
        
        logger.info(f"[Watchdog] Using port {state.watchdog_port}")
        
        # Generate auth token
        state.auth_token = secrets.token_hex(16)
        logger.info(f"[Watchdog] Auth token generated")
        
        # Save initial args
        state.saved_args = {
            "log_level": args.log_level,
            "log_format": args.log_format,
            "no_log_file": args.no_log_file,
            "log_to_console": args.log_to_console,
            "dev_mode": args.dev,
            "addin_port":args.addin_port if args.addin_port else find_available_port(ADDIN_PORTS),
            "server_port":args.server_port if args.server_port else find_available_port(SERVER_PORTS),
            "docs_port":(args.docs_port if args.docs_port else  find_available_port(DOCS_PORTS)) if args.local_docs else -1,
            "skip_manifest":args.skip_manifest,
        }
        
        # Start HTTP server in background thread
        server = HTTPServer(('127.0.0.1', state.watchdog_port), WatchdogAPIHandler)
        server_thread = threading.Thread(target=server.serve_forever, daemon=True)
        server_thread.start()
        logger.info(f"[Watchdog] HTTP API listening on http://127.0.0.1:{state.watchdog_port}")
        
        # Spawn launcher
        _spawn_launcher()
        
        # Main loop - wait for launcher to exit or kill signal
        while not state.should_exit:
            with state.lock:
                proc = state.launcher_process
            
            if proc and proc.poll() is not None:
                exit_code = proc.returncode
                logger.info(f"[Watchdog] Launcher exited with code {exit_code}")
                
                if exit_code == 0:
                    # Normal exit
                    break
                else:
                    # Unexpected exit - don't auto-restart on crash
                    logger.error(f"[Watchdog] Launcher crashed, exiting")
                    break
            
            time.sleep(0.5)
        sys.exit(0)
        # Cleanup
        server.shutdown()
    finally:
        try:
            _kill_launcher()
        except:
            pass
        lock.release()
        logger.info("[Watchdog] Exiting")


if __name__ == "__main__":
    main()
