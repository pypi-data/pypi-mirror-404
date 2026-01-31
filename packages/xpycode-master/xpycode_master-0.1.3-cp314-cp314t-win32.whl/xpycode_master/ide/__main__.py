"""
XPyCode IDE - Entry Point

This module provides the entry point for the XPyCode IDE application.
It initializes the Qt application and launches the main window.
"""

import argparse
import logging
import os
import sys
import ctypes
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtCore import Qt

from .gui.main_window import MainWindow
from .gui.websocket_client import WebSocketClient
from .gui.utils.decorators_pyside6_threadsafe import InitializeThreadSafe
from ..logging_config import setup_logging_subprocess, get_logger


def get_splash_pixmap(app: QApplication) -> QPixmap:
    """Get splash screen pixmap, scaled for high-DPI if needed."""
    pixmap = _get_initial_splash_pixmap()
    screen = app.primaryScreen()
    if screen is not None:
        dpi_scale = screen.devicePixelRatio()
        if dpi_scale != 1.0:
            pixmap.setDevicePixelRatio(dpi_scale)

        screensize = screen.size()
        pixmap = pixmap.scaledToWidth(int(screensize.width() * 0.3), Qt.TransformationMode.SmoothTransformation)

    return pixmap

def _get_initial_splash_pixmap() -> QPixmap:
    """Load splash screen image."""
    paths = [
        os.path.join(os.path.dirname(__file__), "gui", "resources", "XpyCodeSplash.png"),
        os.path.join(os.path.dirname(__file__), "resources", "XpyCodeSplash.png"),
    ]
    for path in paths:
        if os.path.exists(path):
            return QPixmap(path)
    # Return empty pixmap if logo not found
    return QPixmap(400, 300)


def main():
    """Main entry point for the XPyCode IDE."""
    # Setup logging first - reads from environment variables if available
    # If not available (IDE started independently), uses defaults
    try:
        setup_logging_subprocess()
    except Exception:
        # Fallback to basic config if logging not configured
        logging.basicConfig(
            level=logging.WARNING,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    logger = get_logger(__name__)
    logger.info("IDE subprocess starting")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='XPyCode IDE')
    parser.add_argument('--port', type=int, default=8000, help='Business Layer WebSocket port')
    parser.add_argument('--watchdog-port', type=int, default=0, help='Watchdog HTTP API port')
    parser.add_argument('--auth-token', type=str, default='', help='Watchdog auth token')
    parser.add_argument('--docs-port', type=int, default=0, help='Documentation server port')
    args = parser.parse_args()
    
    print("Starting XPyCode IDE...")
    
    icon_path = os.path.join(os.path.dirname(__file__), "gui", "resources", "icons", "XPY.png")

    
    # Create the Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("XPyCode Editor")
    app.setOrganizationName("BGE Advisory")
    app.setApplicationVersion("3.0.0")
    app.setWindowIcon(QIcon(icon_path))
    
    if sys.platform=='win32':
        myappid = u'bgeadvisory.xpycode' # arbitrary string
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    #Ensure the basic object is created in the Qt app Thread
    InitializeThreadSafe()
    
    # Show splash screen
    splash_pixmap = get_splash_pixmap(app)
    splash = QSplashScreen(splash_pixmap, Qt.WindowType.WindowStaysOnTopHint)
    splash.show()
    splash.showMessage("Initializing...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
    app.processEvents()
    
    # Create MainWindow (but don't show yet)
    splash.showMessage("Creating interface...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
    app.processEvents()
    main_window = MainWindow()
    
    # Store watchdog info in main_window
    main_window.watchdog_port = args.watchdog_port
    main_window.auth_token = args.auth_token
    main_window.docs_port = args.docs_port
    
    # Create WebSocket client with MainWindow reference
    splash.showMessage("Connecting to Business Layer...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
    app.processEvents()
    ws_client = WebSocketClient(main_window, port=args.port)
    main_window.set_websocket_client(ws_client)
    
    # Start WebSocket client
    ws_client.start()
    while not ws_client.connected:
        pass
    
    # Apply initial settings
    splash.showMessage("Applying settings...", Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignCenter, Qt.GlobalColor.white)
    app.processEvents()
    main_window.apply_startup_settings()
    
    # Close splash and show main window
    splash.finish(main_window)
    main_window.show_and_focus()
    
    # Run the application event loop
    result=app.exec()
    ws_client.stop()
    sys.exit(result)


if __name__ == "__main__":
    main()
