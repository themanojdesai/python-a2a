"""
MCP Transport Implementations - stdio, HTTP and WebSocket transports.

This module provides transport implementations for MCP following the 
2025-03-26 specification. Supports both local and remote MCP servers:

- StdioTransport: For local MCP servers via subprocess (primary)
- HttpMCPTransport: For remote MCP servers via HTTP/HTTPS
- WebSocketMCPTransport: For real-time remote MCP servers via WebSocket
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path
from urllib.parse import urljoin

from .protocol import MCPConnectionError, MCPProtocolError

# Optional HTTP dependencies
try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

logger = logging.getLogger(__name__)


class StdioTransport:
    """
    Standard stdio transport for MCP clients.
    
    Communicates with MCP servers via stdin/stdout of a subprocess,
    following the MCP specification's stdio transport requirements.
    """
    
    def __init__(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ):
        """
        Initialize stdio transport.
        
        Args:
            command: Command and arguments to start MCP server
            cwd: Working directory for server process
            env: Environment variables for server process
            timeout: Process startup timeout
        """
        self.command = command
        self.cwd = cwd
        self.env = env or {}
        self.timeout = timeout
        
        # Process management
        self.process: Optional[asyncio.subprocess.Process] = None
        self._connected = False
        self._receive_queue = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
        
        logger.info(f"Created stdio transport for command: {' '.join(command)}")
    
    async def connect(self) -> None:
        """Start the MCP server process and establish communication."""
        if self._connected:
            raise MCPConnectionError("Transport already connected")
        
        try:
            # Prepare environment
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            # Validate command
            if not self.command:
                raise MCPConnectionError("Command cannot be empty")
            
            # Check if command exists
            command_path = self.command[0]
            if not self._command_exists(command_path):
                raise MCPConnectionError(f"Command not found: {command_path}")
            
            logger.info(f"Starting MCP server: {' '.join(self.command)}")
            
            # Start process
            self.process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *self.command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.cwd,
                    env=full_env,
                    # Ensure clean process group for proper cleanup
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                ),
                timeout=self.timeout
            )
            
            # Start reading stdout
            self._reader_task = asyncio.create_task(self._read_stdout())
            
            # Verify process is running
            if self.process.returncode is not None:
                raise MCPConnectionError(f"Process exited immediately with code {self.process.returncode}")
            
            self._connected = True
            logger.info(f"MCP server started with PID {self.process.pid}")
            
        except asyncio.TimeoutError:
            raise MCPConnectionError(f"Process startup timed out after {self.timeout}s")
        except Exception as e:
            await self._cleanup_process()
            raise MCPConnectionError(f"Failed to start process: {e}") from e
    
    async def disconnect(self) -> None:
        """Stop the MCP server process and clean up resources."""
        if not self._connected:
            return
        
        logger.info("Stopping MCP server process")
        
        self._connected = False
        
        # Stop reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        
        # Clean up process
        await self._cleanup_process()
        
        logger.info("MCP server process stopped")
    
    async def send(self, message: bytes) -> None:
        """Send message to MCP server via stdin."""
        if not self._connected or not self.process:
            raise MCPConnectionError("Transport not connected")
        
        if self.process.returncode is not None:
            raise MCPConnectionError(f"Process has exited with code {self.process.returncode}")
        
        try:
            # MCP stdio protocol: each message is a line
            message_line = message + b'\n'
            
            self.process.stdin.write(message_line)
            await self.process.stdin.drain()
            
            logger.debug(f"Sent {len(message)} bytes to MCP server")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise MCPConnectionError(f"Send failed: {e}") from e
    
    async def receive(self) -> bytes:
        """Receive message from MCP server via stdout."""
        if not self._connected:
            raise MCPConnectionError("Transport not connected")
        
        try:
            # Get message from queue (populated by reader task)
            message = await self._receive_queue.get()
            
            # Check for special error marker
            if isinstance(message, Exception):
                raise message
            
            logger.debug(f"Received {len(message)} bytes from MCP server")
            return message
            
        except Exception as e:
            if isinstance(e, MCPConnectionError):
                raise
            logger.error(f"Failed to receive message: {e}")
            raise MCPConnectionError(f"Receive failed: {e}") from e
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return (
            self._connected and 
            self.process is not None and 
            self.process.returncode is None
        )
    
    async def _read_stdout(self) -> None:
        """Read messages from process stdout with proper handling of large JSON responses."""
        logger.debug("Started stdout reader task")
        
        try:
            buffer = b''
            max_message_size = 50 * 1024 * 1024  # 50MB limit for large responses like screenshots
            
            while self._connected and self.process:
                try:
                    # Read data in chunks
                    chunk = await self.process.stdout.read(65536)  # 64KB chunks
                    if not chunk:
                        logger.info("MCP server closed stdout")
                        break
                    
                    buffer += chunk
                    
                    # Process complete JSON-RPC messages from buffer
                    while True:
                        newline_pos = buffer.find(b'\n')
                        if newline_pos == -1:
                            break
                        
                        # Extract complete message
                        message_bytes = buffer[:newline_pos].rstrip(b'\r')
                        buffer = buffer[newline_pos + 1:]
                        
                        # Validate message size
                        if len(message_bytes) > max_message_size:
                            logger.error(f"Message too large: {len(message_bytes)} bytes, skipping")
                            continue
                        
                        # Decode and validate as JSON
                        if message_bytes:
                            try:
                                message_text = message_bytes.decode('utf-8')
                                # Validate it's proper JSON-RPC
                                import json
                                json.loads(message_text)  # Validate JSON structure
                                await self._receive_queue.put(message_bytes)
                            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                                logger.warning(f"Invalid message from MCP server: {e}")
                                continue
                    
                    # Check if buffer is getting too large
                    if len(buffer) > max_message_size:
                        logger.error("Buffer overflow, clearing incomplete message")
                        buffer = b''
                        
                except Exception as e:
                    logger.error(f"Error reading stdout: {e}")
                    break
                
        except Exception as e:
            logger.error(f"Stdout reader error: {e}")
            await self._receive_queue.put(MCPConnectionError(f"Reader failed: {e}"))
        
        logger.debug("Stdout reader task ended")
    
    async def _cleanup_process(self) -> None:
        """Clean up the server process."""
        if not self.process:
            return
        
        try:
            # Try graceful termination first
            if self.process.returncode is None:
                self.process.terminate()
                
                try:
                    # Wait for graceful exit
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if graceful termination fails
                    logger.warning("Process did not terminate gracefully, killing")
                    self.process.kill()
                    await self.process.wait()
            
            # Read any remaining stderr for debugging
            if self.process.stderr:
                stderr_data = await self.process.stderr.read()
                if stderr_data:
                    stderr_text = stderr_data.decode('utf-8', errors='replace')
                    logger.debug(f"MCP server stderr: {stderr_text}")
            
            exit_code = self.process.returncode
            if exit_code != 0:
                logger.warning(f"MCP server exited with code {exit_code}")
            else:
                logger.info("MCP server exited normally")
                
        except Exception as e:
            logger.error(f"Error cleaning up process: {e}")
        finally:
            self.process = None
    
    def _command_exists(self, command: str) -> bool:
        """Check if command exists in PATH or as absolute path."""
        # If absolute path, check directly
        if os.path.isabs(command):
            return os.path.isfile(command) and os.access(command, os.X_OK)
        
        # Check in PATH
        path_env = os.environ.get('PATH', '')
        for path_dir in path_env.split(os.pathsep):
            if not path_dir:
                continue
            
            full_path = os.path.join(path_dir, command)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return True
        
        return False
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get information about the server process."""
        if not self.process:
            return {"status": "not_started"}
        
        return {
            "pid": self.process.pid,
            "returncode": self.process.returncode,
            "command": self.command,
            "cwd": self.cwd,
            "connected": self._connected
        }


class ServerStdioTransport:
    """
    Server-side stdio transport for MCP servers.
    
    Handles communication via stdin/stdout when the MCP server
    is being run as a subprocess by a client.
    """
    
    def __init__(self):
        """Initialize server stdio transport."""
        self._connected = False
        self._stdin_reader: Optional[asyncio.Task] = None
        self._receive_queue = asyncio.Queue()
        
        logger.info("Created server stdio transport")
    
    async def connect(self) -> None:
        """Start reading from stdin."""
        if self._connected:
            raise MCPConnectionError("Transport already connected")
        
        # Start stdin reader
        self._stdin_reader = asyncio.create_task(self._read_stdin())
        self._connected = True
        
        logger.info("Server stdio transport connected")
    
    async def disconnect(self) -> None:
        """Stop reading from stdin."""
        if not self._connected:
            return
        
        self._connected = False
        
        if self._stdin_reader and not self._stdin_reader.done():
            self._stdin_reader.cancel()
            try:
                await self._stdin_reader
            except asyncio.CancelledError:
                pass
        
        logger.info("Server stdio transport disconnected")
    
    async def send(self, message: bytes) -> None:
        """Send message via stdout."""
        if not self._connected:
            raise MCPConnectionError("Transport not connected")
        
        try:
            # Write to stdout with newline
            message_line = message + b'\n'
            sys.stdout.buffer.write(message_line)
            sys.stdout.buffer.flush()
            
            logger.debug(f"Sent {len(message)} bytes via stdout")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise MCPConnectionError(f"Send failed: {e}") from e
    
    async def receive(self) -> bytes:
        """Receive message from stdin."""
        if not self._connected:
            raise MCPConnectionError("Transport not connected")
        
        try:
            message = await self._receive_queue.get()
            
            if isinstance(message, Exception):
                raise message
            
            logger.debug(f"Received {len(message)} bytes from stdin")
            return message
            
        except Exception as e:
            if isinstance(e, MCPConnectionError):
                raise
            logger.error(f"Failed to receive message: {e}")
            raise MCPConnectionError(f"Receive failed: {e}") from e
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected
    
    async def _read_stdin(self) -> None:
        """Read messages from stdin."""
        logger.debug("Started stdin reader task")
        
        try:
            # Use asyncio subprocess communication approach
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            
            # Connect to stdin properly
            loop = asyncio.get_event_loop()
            transport, _ = await loop.connect_read_pipe(
                lambda: protocol, sys.stdin
            )
            
            try:
                while self._connected:
                    # Read line from stdin with timeout
                    try:
                        line = await asyncio.wait_for(reader.readline(), timeout=1.0)
                        
                        if not line:
                            # EOF - but only break if we're sure stdin is closed
                            logger.debug("Received EOF from stdin")
                            # Small delay to ensure we're not just hitting a temporary EOF
                            await asyncio.sleep(0.1)
                            continue
                        
                        # Remove newline and decode
                        try:
                            message_text = line.rstrip(b'\n\r').decode('utf-8')
                            if message_text:  # Skip empty lines
                                message_bytes = message_text.encode('utf-8')
                                await self._receive_queue.put(message_bytes)
                        except UnicodeDecodeError as e:
                            logger.warning(f"Invalid UTF-8 from stdin: {e}")
                            continue
                            
                    except asyncio.TimeoutError:
                        # Normal timeout, continue loop
                        continue
                        
            finally:
                transport.close()
                
        except Exception as e:
            logger.error(f"Stdin reader error: {e}")
            await self._receive_queue.put(MCPConnectionError(f"Reader failed: {e}"))
        
        logger.debug("Stdin reader task ended")


# Factory functions
def create_stdio_transport(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> StdioTransport:
    """
    Create stdio transport for MCP client.
    
    Args:
        command: Command to start MCP server
        cwd: Working directory
        env: Environment variables
        timeout: Startup timeout
        
    Returns:
        Configured stdio transport
    """
    return StdioTransport(command, cwd, env, timeout)


def create_server_stdio_transport() -> ServerStdioTransport:
    """
    Create stdio transport for MCP server.
    
    Returns:
        Configured server stdio transport
    """
    return ServerStdioTransport()


# HTTP and WebSocket Transport Classes for Remote MCP Servers

class HttpMCPTransport:
    """
    HTTP transport implementation for remote MCP servers.
    
    Connects to remote MCP servers via HTTP/HTTPS protocols.
    Supports authentication, custom headers, and request/response handling.
    """
    
    def __init__(self, 
                 base_url: str,
                 headers: Optional[Dict[str, str]] = None,
                 auth_token: Optional[str] = None,
                 api_key: Optional[str] = None,
                 timeout: float = 30.0,
                 verify_ssl: bool = True):
        """
        Initialize HTTP MCP transport.
        
        Args:
            base_url: Base URL of the MCP server (e.g., "https://api.example.com/mcp")
            headers: Additional HTTP headers to send with requests
            auth_token: Bearer token for authentication
            api_key: API key for authentication (added as X-API-Key header)
            timeout: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
        """
        if not HAS_AIOHTTP:
            raise ImportError(
                "aiohttp is required for HTTP transport. Install with: pip install aiohttp"
            )
        
        self.base_url = base_url.rstrip('/')
        self.headers = headers or {}
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.verify_ssl = verify_ssl
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._response_queue = asyncio.Queue()
        
        # Set up authentication headers
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
        if api_key:
            self.headers['X-API-Key'] = api_key
        
        # Ensure content type for JSON-RPC
        self.headers.setdefault('Content-Type', 'application/json')
        self.headers.setdefault('Accept', 'application/json')
    
    async def connect(self) -> None:
        """Establish HTTP connection session."""
        if self._connected:
            return
        
        connector = aiohttp.TCPConnector(verify_ssl=self.verify_ssl)
        self._session = aiohttp.ClientSession(
            headers=self.headers,
            timeout=self.timeout,
            connector=connector
        )
        
        # Test connection with a health check if available
        try:
            await self._health_check()
            self._connected = True
            logger.info(f"Connected to remote MCP server at {self.base_url}")
        except Exception as e:
            await self.disconnect()
            raise MCPConnectionError(f"Failed to connect to remote MCP server: {e}") from e
    
    async def disconnect(self) -> None:
        """Close HTTP connection session."""
        if self._session:
            await self._session.close()
            self._session = None
        self._connected = False
        logger.info("Disconnected from HTTP MCP server")
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected and self._session is not None
    
    async def send(self, message: bytes) -> None:
        """
        Send JSON-RPC message via HTTP POST.
        
        Args:
            message: JSON-RPC message as bytes
        """
        if not self._session:
            raise MCPConnectionError("Not connected to MCP server")
        
        try:
            # Parse the message to ensure it's valid JSON-RPC
            message_data = json.loads(message.decode('utf-8'))
            
            # Determine endpoint based on JSON-RPC method
            endpoint = self._get_endpoint_for_method(message_data.get('method', ''))
            
            # Send HTTP POST request
            async with self._session.post(
                urljoin(self.base_url, endpoint),
                json=message_data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise MCPConnectionError(f"HTTP {response.status}: {error_text}")
                
                # Store response for receive() call
                response_data = await response.json()
                response_bytes = json.dumps(response_data).encode('utf-8')
                await self._response_queue.put(response_bytes)
                
        except Exception as e:
            logger.error(f"Failed to send HTTP message: {e}")
            raise MCPConnectionError(f"Send failed: {e}") from e
    
    async def receive(self) -> bytes:
        """
        Receive JSON-RPC response.
        
        Returns:
            Response message as bytes
        """
        try:
            response = await asyncio.wait_for(
                self._response_queue.get(),
                timeout=self.timeout.total if self.timeout else 30.0
            )
            return response
        except asyncio.TimeoutError:
            raise MCPConnectionError("Receive timeout")
    
    def _get_endpoint_for_method(self, method: str) -> str:
        """Get appropriate endpoint for JSON-RPC method."""
        # Map MCP methods to appropriate endpoints
        if method in ['initialize', 'initialized']:
            return '/mcp/init'
        elif method.startswith('tools/'):
            return '/mcp/tools'
        elif method.startswith('resources/'):
            return '/mcp/resources'
        elif method.startswith('prompts/'):
            return '/mcp/prompts'
        else:
            return '/mcp/rpc'  # Default endpoint
    
    async def _health_check(self) -> None:
        """Perform health check on the MCP server."""
        try:
            # Try a simple OPTIONS or GET request to check server availability
            async with self._session.options(self.base_url) as response:
                if response.status >= 400:
                    # If OPTIONS fails, try GET to root
                    async with self._session.get(self.base_url) as get_response:
                        if get_response.status >= 500:
                            raise MCPConnectionError(f"Server error: {get_response.status}")
        except aiohttp.ClientConnectorError as e:
            raise MCPConnectionError(f"Cannot reach server: {e}")
        except Exception as e:
            logger.warning(f"Health check failed, proceeding anyway: {e}")
            # Don't fail on health check issues, server might not support it


class WebSocketMCPTransport:
    """
    WebSocket transport implementation for remote MCP servers.
    
    Provides real-time bidirectional communication for MCP servers
    that support WebSocket connections.
    """
    
    def __init__(self,
                 ws_url: str,
                 headers: Optional[Dict[str, str]] = None,
                 auth_token: Optional[str] = None,
                 api_key: Optional[str] = None,
                 timeout: float = 30.0,
                 heartbeat: Optional[float] = None):
        """
        Initialize WebSocket MCP transport.
        
        Args:
            ws_url: WebSocket URL (e.g., "wss://api.example.com/mcp/ws")
            headers: Additional headers for WebSocket handshake
            auth_token: Bearer token for authentication
            api_key: API key for authentication
            timeout: Connection timeout in seconds
            heartbeat: Heartbeat interval in seconds (None to disable)
        """
        if not HAS_AIOHTTP:
            raise ImportError(
                "aiohttp is required for WebSocket transport. Install with: pip install aiohttp"
            )
        
        self.ws_url = ws_url
        self.headers = headers or {}
        self.timeout = timeout
        self.heartbeat = heartbeat
        self._websocket: Optional[aiohttp.ClientWebSocketResponse] = None
        self._session: Optional[aiohttp.ClientSession] = None
        self._connected = False
        self._message_queue = asyncio.Queue()
        self._receive_task: Optional[asyncio.Task] = None
        
        # Set up authentication headers
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
        if api_key:
            self.headers['X-API-Key'] = api_key
    
    async def connect(self) -> None:
        """Establish WebSocket connection."""
        if self._connected:
            return
        
        try:
            self._session = aiohttp.ClientSession()
            
            self._websocket = await self._session.ws_connect(
                self.ws_url,
                headers=self.headers,
                timeout=self.timeout,
                heartbeat=self.heartbeat
            )
            
            # Start message receiving task
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            self._connected = True
            logger.info(f"Connected to WebSocket MCP server at {self.ws_url}")
            
        except Exception as e:
            await self.disconnect()
            raise MCPConnectionError(f"Failed to connect to WebSocket MCP server: {e}") from e
    
    async def disconnect(self) -> None:
        """Close WebSocket connection."""
        self._connected = False
        
        # Cancel receive task
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None
        
        # Close WebSocket
        if self._websocket:
            await self._websocket.close()
            self._websocket = None
        
        # Close session
        if self._session:
            await self._session.close()
            self._session = None
        
        logger.info("Disconnected from WebSocket MCP server")
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return (self._connected and 
                self._websocket is not None and 
                not self._websocket.closed)
    
    async def send(self, message: bytes) -> None:
        """
        Send message via WebSocket.
        
        Args:
            message: JSON-RPC message as bytes
        """
        if not self._websocket or self._websocket.closed:
            raise MCPConnectionError("WebSocket not connected")
        
        try:
            await self._websocket.send_str(message.decode('utf-8'))
        except Exception as e:
            logger.error(f"Failed to send WebSocket message: {e}")
            raise MCPConnectionError(f"Send failed: {e}") from e
    
    async def receive(self) -> bytes:
        """
        Receive message from WebSocket.
        
        Returns:
            Message as bytes
        """
        try:
            message = await asyncio.wait_for(
                self._message_queue.get(), 
                timeout=self.timeout
            )
            
            if isinstance(message, Exception):
                raise message
            
            return message
        except asyncio.TimeoutError:
            raise MCPConnectionError("Receive timeout")
    
    async def _receive_loop(self) -> None:
        """Background task to receive WebSocket messages."""
        try:
            async for msg in self._websocket:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    message_bytes = msg.data.encode('utf-8')
                    await self._message_queue.put(message_bytes)
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self._websocket.exception()}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSE:
                    logger.info("WebSocket closed by server")
                    break
        except Exception as e:
            logger.error(f"WebSocket receive loop failed: {e}")
            await self._message_queue.put(MCPConnectionError(f"WebSocket receive failed: {e}"))
        finally:
            self._connected = False


# Additional factory functions for remote transports

def create_http_transport(base_url: str, **kwargs) -> HttpMCPTransport:
    """
    Create HTTP MCP transport for remote servers.
    
    Args:
        base_url: Base URL of the remote MCP server
        **kwargs: Additional arguments for HttpMCPTransport
        
    Returns:
        Configured HTTP transport
    """
    return HttpMCPTransport(base_url, **kwargs)


def create_websocket_transport(ws_url: str, **kwargs) -> WebSocketMCPTransport:
    """
    Create WebSocket MCP transport for remote servers.
    
    Args:
        ws_url: WebSocket URL of the remote MCP server
        **kwargs: Additional arguments for WebSocketMCPTransport
        
    Returns:
        Configured WebSocket transport
    """
    return WebSocketMCPTransport(ws_url, **kwargs)