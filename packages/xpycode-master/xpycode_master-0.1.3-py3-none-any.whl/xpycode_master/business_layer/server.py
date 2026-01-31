"""
Business Layer Server - FastAPI Routes and Server Management.

This module provides:
- FastAPI application initialization
- All route decorators (@app.websocket, @app.get, etc.)
- Server lifecycle management (startup, shutdown)
- uvicorn server runner

The actual business logic resides in bl_master.py which is Cython-compiled.
This separation ensures FastAPI can properly inspect function signatures.
"""

from fastapi import FastAPI, WebSocket
import uvicorn

# Import all business logic from bl_master
from . import bl_master
from .. import __version__

# Create FastAPI app
app = FastAPI(title="XPyCode Business Layer", version=__version__)


@app.on_event("startup")
async def startup_event():
    """Launch Python Inspector on server startup."""
    await bl_master.startup_event()


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    await bl_master.shutdown_event()


@app.websocket("/ws/{client_type}/{client_id}")
async def websocket_endpoint(
    websocket: WebSocket, client_type: str, client_id: str
):
    """
    WebSocket endpoint for client connections.

    client_type: 'addin', 'ide', 'kernel', or 'inspector'
    client_id: Unique identifier for the client (e.g., workbook_id)
    Query parameter 'name': Optional display name for the client (default: 'Untitled')
    """
    await bl_master.websocket_endpoint(websocket, client_type, client_id)


@app.get("/")
async def root():
    """Health check endpoint."""
    return await bl_master.root()


@app.get("/connections")
async def get_connections():
    """Get current connection status."""
    return await bl_master.get_connections()


def run_server(host: str = "127.0.0.1", port: int = 8000, watchdog_port: int = 0, auth_token: str = "", docs_port: int = 0):
    """Run the Business Layer server."""
    # Initialize global state in bl_master
    bl_master.set_port(port)
    bl_master.initialize_ide_manager(port, watchdog_port, auth_token, docs_port)
    
    uvicorn.run(
        app, 
        host=host, 
        port=port,
        ws_ping_interval=20,  # Send ping every 20 seconds
        ws_ping_timeout=30   # Wait up to 30 seconds 
    )


if __name__ == "__main__":
    run_server()
