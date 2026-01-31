"""
Python Inspector - AST-based code analysis service.

This module provides:
- WebSocket connection to Business Layer
- Code inspection using Python's ast module
- Function detection at specific positions
- Function listing
- Syntax validation
"""

import ast
import asyncio
import json
import logging
import sys
from typing import Optional, List, Dict, Any

try:
    import websockets
    from websockets.client import WebSocketClientProtocol
except ImportError:
    print("ERROR: websockets library not installed. Install with: pip install websockets>=12.0")
    sys.exit(1)


# Configure logging
from ..logging_config import setup_logging_subprocess, get_logger
setup_logging_subprocess()
logger = get_logger(__name__)


class PythonInspector:
    """Python code inspector using AST analysis."""
    
    def __init__(self, client_id: str = "main", host:str="localhost", port:str="8000"):
        self.client_id = client_id
        self.ws_url = f"ws://{host}:{port}/ws/inspector/{client_id}"
        self.websocket: Optional[WebSocketClientProtocol] = None
        self.running = False
    
    def get_function_at_position(self, code: str, line: int, column: int = 0) -> Optional[str]:
        """
        Find the function containing the given position.
        
        Args:
            code: Python source code
            line: Line number (1-indexed)
            column: Column number (0-indexed, optional)
        
        Returns:
            Function name if found, None otherwise
        """
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.lineno <= line <= (node.end_lineno or node.lineno):
                        return node.name
            return None
        except SyntaxError as e:
            logger.warning(f"Syntax error in code: {e}")
            # Fallback for invalid syntax
            return None
        except Exception as e:
            logger.error(f"Error analyzing code: {e}")
            return None
    
    def list_functions(self, code: str) -> List[Dict[str, Any]]:
        """
        List all top-level functions in the code.
        
        Args:
            code: Python source code
        
        Returns:
            List of function info dictionaries
        """
        functions = []
        try:
            tree = ast.parse(code)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'end_line': node.end_lineno or node.lineno,
                    })
        except SyntaxError as e:
            logger.warning(f"Syntax error in code: {e}")
        except Exception as e:
            logger.error(f"Error listing functions: {e}")
        
        return functions
    
    def validate_syntax(self, code: str) -> Dict[str, Any]:
        """
        Validate Python syntax.
        
        Args:
            code: Python source code
        
        Returns:
            Dictionary with 'valid' boolean and optional 'error' message
        """
        try:
            ast.parse(code)
            return {'valid': True}
        except SyntaxError as e:
            return {
                'valid': False,
                'error': str(e),
                'line': e.lineno,
                'offset': e.offset,
            }
        except Exception as e:
            return {
                'valid': False,
                'error': str(e),
            }
    
    async def handle_message(self, message: Dict[str, Any]) -> None:
        """
        Handle incoming messages from Business Layer.
        
        Args:
            message: Message dictionary
        """
        msg_type = message.get('type')
        request_id = message.get('request_id')
        
        logger.debug(f"Handling message: {msg_type}")
        
        try:
            if msg_type == 'get_function_at_position':
                code = message.get('code', '')
                line = message.get('line', 1)
                column = message.get('column', 0)
                
                function_name = self.get_function_at_position(code, line, column)
                
                response = {
                    'type': 'function_at_position_result',
                    'request_id': request_id,
                    'function_name': function_name,
                }
                
                if self.websocket:
                    await self.websocket.send(json.dumps(response))
                    logger.debug(f"Sent function_at_position_result: {function_name}")
            
            elif msg_type == 'list_functions':
                code = message.get('code', '')
                functions = self.list_functions(code)
                
                response = {
                    'type': 'list_functions_result',
                    'request_id': request_id,
                    'functions': functions,
                }
                
                if self.websocket:
                    await self.websocket.send(json.dumps(response))
                    logger.debug(f"Sent list_functions_result: {len(functions)} functions")
            
            elif msg_type == 'validate_syntax':
                code = message.get('code', '')
                validation = self.validate_syntax(code)
                
                response = {
                    'type': 'validate_syntax_result',
                    'request_id': request_id,
                    **validation,
                }
                
                if self.websocket:
                    await self.websocket.send(json.dumps(response))
                    logger.debug(f"Sent validate_syntax_result: {validation}")
            
            else:
                logger.warning(f"Unknown message type: {msg_type}")
        
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            # Send error response
            if request_id and self.websocket:
                error_response = {
                    'type': f"{msg_type}_result" if msg_type else "error",
                    'request_id': request_id,
                    'error': str(e),
                }
                await self.websocket.send(json.dumps(error_response))
    
    async def run(self) -> None:
        """Main run loop for the inspector service."""
        self.running = True
        reconnect_delay = 1
        max_reconnect_delay = 30
        
        while self.running:
            try:
                logger.info(f"Connecting to Business Layer at {self.ws_url}")
                async with websockets.connect(self.ws_url) as websocket:
                    self.websocket = websocket
                    logger.info(f"Connected to Business Layer as inspector/{self.client_id}")
                    reconnect_delay = 1  # Reset delay on successful connection
                    
                    # Main message loop
                    async for raw_message in websocket:
                        try:
                            message = json.loads(raw_message)
                            await self.handle_message(message)
                        except json.JSONDecodeError as e:
                            logger.error(f"Invalid JSON received: {e}")
                        except Exception as e:
                            logger.error(f"Error processing message: {e}")
            
            except websockets.exceptions.WebSocketException as e:
                logger.error(f"WebSocket error: {e}")
                self.websocket = None
            except ConnectionRefusedError:
                logger.warning(f"Connection refused. Retrying in {reconnect_delay}s...")
                self.websocket = None
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.websocket = None
            
            # Reconnect logic
            if self.running:
                await asyncio.sleep(reconnect_delay)
                reconnect_delay = min(reconnect_delay * 2, max_reconnect_delay)
    
    def stop(self) -> None:
        """Stop the inspector service."""
        self.running = False
        logger.info("Inspector service stopping...")


async def main(port:str):
    """Main entry point for the inspector service."""
    inspector = PythonInspector(port=port)
    
    try:
        await inspector.run()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        inspector.stop()
