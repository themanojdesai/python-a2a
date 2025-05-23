"""
Client for communicating with MCP servers.

This implementation follows the Model Context Protocol specification,
using JSON-RPC 2.0 as the wire protocol with support for stdio and SSE transports.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass

from .client_transport import Transport, create_transport

logger = logging.getLogger(__name__)


class MCPError(Exception):
    """Base error for MCP-related issues"""
    pass


class MCPConnectionError(MCPError):
    """Error connecting to MCP server"""
    pass


class MCPTimeoutError(MCPError):
    """Timeout during MCP request"""
    pass


class MCPToolError(MCPError):
    """Error executing an MCP tool"""
    pass


class JSONRPCError(MCPError):
    """JSON-RPC protocol error"""
    def __init__(self, code: int, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(f"JSON-RPC Error {code}: {message}")


@dataclass
class ServerInfo:
    """MCP server information"""
    name: str
    version: str
    protocol_version: str
    capabilities: Dict[str, Any]


class MCPClient:
    """
    Client for interacting with MCP servers.
    
    This client implements the Model Context Protocol using JSON-RPC 2.0
    with support for both stdio and SSE transports.
    """
    
    def __init__(
        self, 
        server_url: Optional[str] = None,
        command: Optional[List[str]] = None,
        timeout: int = 30,
        headers: Optional[Dict[str, str]] = None,
        # Legacy parameters for backward compatibility
        max_retries: int = 3,
        retry_delay: float = 1.0,
        auth: Optional[Dict[str, Any]] = None,
        tools_ttl: int = 3600
    ):
        """
        Initialize an MCP client.
        
        Args:
            server_url: URL for SSE transport (mutually exclusive with command)
            command: Command for stdio transport (mutually exclusive with server_url)
            timeout: Request timeout in seconds
            headers: Optional HTTP headers for SSE transport
            max_retries: Maximum number of retry attempts (legacy, not used)
            retry_delay: Initial delay between retries (legacy, not used)
            auth: Optional authentication configuration (legacy, applied to headers)
            tools_ttl: Time-to-live for tools cache in seconds
        """
        # Handle legacy auth parameter
        if auth and headers is None:
            headers = {}
        if auth:
            headers = self._apply_auth(auth, headers or {})
        
        # Create transport
        self.transport = create_transport(
            url=server_url,
            command=command,
            headers=headers
        )
        
        # State
        self.initialized = False
        self.server_info = None
        self._request_id = 0
        self._tools_cache = None
        self._tools_cache_time = None
        self.tools_ttl = tools_ttl
        
        # Store original parameters for legacy compatibility
        self.server_url = server_url
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = headers or {}
        self.auth = auth
        
        # For async context manager
        self._connected = False
    
    def _apply_auth(self, auth: Dict[str, Any], headers: Dict[str, str]) -> Dict[str, str]:
        """Apply legacy auth configuration to headers."""
        auth_type = auth.get("type", "").lower()
        
        if auth_type == "bearer":
            token = auth.get("token", "")
            headers["Authorization"] = f"Bearer {token}"
        elif auth_type == "api_key":
            key = auth.get("key", "")
            key_name = auth.get("key_name", "X-API-Key")
            location = auth.get("location", "header")
            if location == "header":
                headers[key_name] = key
        
        return headers
    
    def _next_id(self) -> int:
        """Generate next request ID."""
        self._request_id += 1
        return self._request_id
    
    async def _ensure_connected(self):
        """Ensure client is connected and initialized."""
        if not self._connected:
            await self.connect()
        if not self.initialized:
            await self._initialize()
    
    async def connect(self):
        """Connect to the MCP server."""
        if not self._connected:
            await self.transport.connect()
            self._connected = True
            logger.info("Connected to MCP server")
    
    async def _initialize(self):
        """Perform MCP initialization handshake."""
        # Send initialize request
        response = await self._send_request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {},
                "resources": {},
                "prompts": {}
            },
            "clientInfo": {
                "name": "python-a2a",
                "version": "1.0.0"
            }
        })
        
        # Extract server info
        if "error" in response:
            raise JSONRPCError(
                response["error"]["code"],
                response["error"]["message"],
                response["error"].get("data")
            )
        
        result = response.get("result", {})
        self.server_info = ServerInfo(
            name=result.get("serverInfo", {}).get("name", "Unknown"),
            version=result.get("serverInfo", {}).get("version", "Unknown"),
            protocol_version=result.get("protocolVersion", "Unknown"),
            capabilities=result.get("capabilities", {})
        )
        
        # Send initialized notification
        await self._send_notification("initialized", {})
        
        self.initialized = True
        logger.info(f"Initialized connection to MCP server: {self.server_info.name}")
    
    async def _send_request(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Send a JSON-RPC request and wait for response."""
        request = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": method,
            "params": params
        }
        
        try:
            response = await self.transport.send_request(request)
            return response
        except Exception as e:
            logger.error(f"Error sending request {method}: {e}")
            raise MCPConnectionError(f"Failed to send request: {str(e)}")
    
    async def _send_notification(self, method: str, params: Dict[str, Any]):
        """Send a JSON-RPC notification (no response expected)."""
        notification = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params
        }
        
        try:
            await self.transport.send_notification(notification)
        except Exception as e:
            logger.error(f"Error sending notification {method}: {e}")
            raise MCPConnectionError(f"Failed to send notification: {str(e)}")
    
    async def close(self):
        """Close the connection to the MCP server."""
        if self._connected:
            await self.transport.disconnect()
            self._connected = False
            self.initialized = False
            logger.info("Closed connection to MCP server")
    
    async def get_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get available tools from the MCP server.
        
        Args:
            force_refresh: Force a refresh of the tools cache
            
        Returns:
            List of available tools with their metadata
        """
        # Ensure connected
        await self._ensure_connected()
        
        # Check cache
        if not force_refresh and self._tools_cache is not None:
            cache_age = (datetime.now() - self._tools_cache_time).total_seconds()
            if cache_age < self.tools_ttl:
                return self._tools_cache
        
        # Request tools
        response = await self._send_request("tools/list", {})
        
        if "error" in response:
            raise JSONRPCError(
                response["error"]["code"],
                response["error"]["message"],
                response["error"].get("data")
            )
        
        tools = response.get("result", {}).get("tools", [])
        
        # Cache tools
        self._tools_cache = tools
        self._tools_cache_time = datetime.now()
        
        return tools
    
    async def call_tool(
        self, 
        tool_name: str, 
        stream: bool = False,
        callback: Optional[Callable[[str], None]] = None,
        **params
    ) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            stream: Whether to stream the response (not implemented)
            callback: Callback function for streaming responses (not implemented)
            **params: Parameters to pass to the tool
            
        Returns:
            Result from the tool
        """
        # Ensure connected
        await self._ensure_connected()
        
        # Note: Streaming is not yet implemented in this version
        if stream:
            logger.warning("Streaming is not yet implemented, using regular call")
        
        # Send tool call request
        response = await self._send_request("tools/call", {
            "name": tool_name,
            "arguments": params
        })
        
        if "error" in response:
            raise JSONRPCError(
                response["error"]["code"],
                response["error"]["message"],
                response["error"].get("data")
            )
        
        # Extract content from response
        result = response.get("result", {})
        content = result.get("content", [])
        
        # If single text content, return just the text
        if len(content) == 1 and content[0].get("type") == "text":
            return content[0].get("text", "")
        
        # Otherwise return the full content array
        return content
    
    async def list_resources(self) -> List[Dict[str, Any]]:
        """List available resources from the MCP server."""
        await self._ensure_connected()
        
        response = await self._send_request("resources/list", {})
        
        if "error" in response:
            raise JSONRPCError(
                response["error"]["code"],
                response["error"]["message"],
                response["error"].get("data")
            )
        
        return response.get("result", {}).get("resources", [])
    
    async def read_resource(self, uri: str) -> Any:
        """Read a resource from the MCP server."""
        await self._ensure_connected()
        
        response = await self._send_request("resources/read", {
            "uri": uri
        })
        
        if "error" in response:
            raise JSONRPCError(
                response["error"]["code"],
                response["error"]["message"],
                response["error"].get("data")
            )
        
        # Extract content
        result = response.get("result", {})
        contents = result.get("contents", [])
        
        if contents:
            # Get the first resource's content
            resource_content = contents[0].get("content", [])
            if len(resource_content) == 1 and resource_content[0].get("type") == "text":
                return resource_content[0].get("text", "")
        
        return contents
    
    async def get_prompt(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get a prompt from the MCP server."""
        await self._ensure_connected()
        
        response = await self._send_request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        
        if "error" in response:
            raise JSONRPCError(
                response["error"]["code"],
                response["error"]["message"],
                response["error"].get("data")
            )
        
        return response.get("result", {}).get("messages", [])
    
    # Legacy sync methods for backward compatibility
    def call_tool_sync(self, tool_name: str, **params) -> Any:
        """Call a tool synchronously (legacy method)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.call_tool(tool_name, **params))
    
    def get_tools_sync(self) -> List[Dict[str, Any]]:
        """Get available tools synchronously (legacy method)."""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_tools())
    
    def get_function_specs(self) -> List[Dict[str, Any]]:
        """
        Get tool specifications in function-calling format (legacy method).
        
        Returns:
            List of specifications suitable for function calling
        """
        tools = self.get_tools_sync()
        function_specs = []
        
        for tool in tools:
            # Convert MCP tool spec to function spec format
            spec = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("inputSchema", {
                    "type": "object",
                    "properties": {},
                    "required": []
                })
            }
            function_specs.append(spec)
        
        return function_specs
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    # Legacy method for backward compatibility
    async def _stream_tool_call(self, tool_name: str, callback: Callable[[str], None], **params) -> str:
        """Legacy streaming method - not implemented."""
        logger.warning("Streaming is not implemented in the new MCP client")
        result = await self.call_tool(tool_name, **params)
        if isinstance(result, str):
            callback(result)
            return result
        return str(result)