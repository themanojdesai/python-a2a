"""
MCP Client Implementation following 2025-03-26 specification.

This module provides a complete MCP client implementation with proper
JSON-RPC 2.0 compliance, lifecycle management, and transport support.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable

from .protocol import (
    MCPProtocolHandler,
    MCPProtocolError,
    MCPConnectionError,
    MCPTimeoutError,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCErrorCode,
    MCPImplementationInfo,
    MCPCapabilities
)
from .connection import MCPConnection, MCPMessageHandler
from .transports import StdioTransport, create_stdio_transport

logger = logging.getLogger(__name__)


class MCPClientHandler(MCPMessageHandler):
    """
    MCP client message handler.
    
    Processes server-initiated requests and notifications
    according to MCP client capabilities.
    """
    
    def __init__(self, client_capabilities: MCPCapabilities):
        """
        Initialize client handler.
        
        Args:
            client_capabilities: Client capabilities
        """
        self.capabilities = client_capabilities
        self._notification_handlers: Dict[str, List[Callable]] = {}
        
    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle server request."""
        method = request.method
        request_id = request.id
        
        # Handle sampling requests if capability is enabled
        if method.startswith("sampling/") and self.capabilities.sampling:
            return await self._handle_sampling_request(request)
        
        # Handle roots requests if capability is enabled  
        elif method.startswith("roots/") and self.capabilities.roots:
            return await self._handle_roots_request(request)
        
        # Unknown method
        else:
            protocol = MCPProtocolHandler(
                MCPImplementationInfo("client", "1.0"),
                self.capabilities
            )
            return protocol.create_error_response(
                request_id,
                JSONRPCErrorCode.METHOD_NOT_FOUND,
                f"Method not supported: {method}"
            )
    
    async def handle_notification(self, notification: JSONRPCRequest) -> None:
        """Handle server notification."""
        method = notification.method
        params = notification.params or {}
        
        # Call registered handlers
        if method in self._notification_handlers:
            for handler in self._notification_handlers[method]:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(params)
                    else:
                        handler(params)
                except Exception as e:
                    logger.error(f"Notification handler error for {method}: {e}")
    
    async def _handle_sampling_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle sampling request from server."""
        # Sampling capability implementation would go here
        protocol = MCPProtocolHandler(
            MCPImplementationInfo("client", "1.0"),
            self.capabilities
        )
        return protocol.create_error_response(
            request.id,
            JSONRPCErrorCode.METHOD_NOT_FOUND,
            "Sampling not implemented"
        )
    
    async def _handle_roots_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle roots request from server."""
        # Roots capability implementation would go here
        protocol = MCPProtocolHandler(
            MCPImplementationInfo("client", "1.0"),
            self.capabilities
        )
        return protocol.create_response(request.id, result={"roots": []})
    
    def add_notification_handler(self, method: str, handler: Callable) -> None:
        """Add handler for server notifications."""
        if method not in self._notification_handlers:
            self._notification_handlers[method] = []
        self._notification_handlers[method].append(handler)


class MCPClient:
    """
    Complete MCP client implementation following 2025-03-26 specification.
    
    Provides a high-level interface for connecting to MCP servers
    and calling tools, reading resources, and getting prompts.
    """
    
    def __init__(
        self,
        name: str = "python-a2a-client",
        version: str = "2.0.0",
        # Client capabilities
        enable_sampling: bool = False,
        enable_roots: bool = False,
        # Connection settings
        timeout: float = 30.0
    ):
        """
        Initialize MCP client.
        
        Args:
            name: Client name
            version: Client version
            enable_sampling: Enable sampling capability
            enable_roots: Enable roots capability
            timeout: Request timeout
        """
        self.name = name
        self.version = version
        self.timeout = timeout
        
        # Build client capabilities
        capabilities = MCPCapabilities()
        if enable_sampling:
            capabilities.sampling = {}
        if enable_roots:
            capabilities.roots = {"listChanged": True}
        
        # Implementation info
        implementation_info = MCPImplementationInfo(name, version)
        
        # Create handler
        self.handler = MCPClientHandler(capabilities)
        
        # Connection will be set when connecting
        self.connection: Optional[MCPConnection] = None
        
        logger.info(f"Created MCP client: {name} v{version}")
    
    async def connect_stdio(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None
    ) -> None:
        """
        Connect to MCP server via stdio transport.
        
        Args:
            command: Command to start server
            cwd: Working directory
            env: Environment variables
        """
        # Create stdio transport
        transport = create_stdio_transport(command, cwd, env, self.timeout)
        
        # Create connection
        implementation_info = MCPImplementationInfo(self.name, self.version)
        self.connection = MCPConnection(
            transport=transport,
            handler=self.handler,
            implementation_info=implementation_info,
            capabilities=self.handler.capabilities,
            timeout=self.timeout
        )
        
        # Connect and initialize as client
        await self.connection.connect()
        await self.connection.initialize_client()
        
        logger.info(f"Connected to MCP server via stdio: {' '.join(command)}")
    
    async def connect_http(self, url: str, headers: Optional[Dict[str, str]] = None) -> None:
        """
        Connect to MCP server via HTTP transport.
        
        Args:
            url: Server URL
            headers: HTTP headers
        """
        # HTTP transport implementation would go here
        raise NotImplementedError("HTTP transport not yet implemented")
    
    async def disconnect(self) -> None:
        """Disconnect from MCP server."""
        if self.connection:
            await self.connection.disconnect()
            self.connection = None
            logger.info("Disconnected from MCP server")
    
    def _ensure_connected(self) -> None:
        """Ensure client is connected."""
        if not self.connection or not self.connection.is_initialized:
            raise MCPConnectionError("Client not connected to server")
    
    async def list_tools(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List available tools from server.
        
        Args:
            cursor: Pagination cursor
            
        Returns:
            Tools list response
        """
        self._ensure_connected()
        
        request = self.connection.protocol.create_request("tools/list", {
            "cursor": cursor
        } if cursor else {})
        
        response = await self.connection.send_request(request)
        
        if response.error:
            raise MCPProtocolError(f"tools/list failed: {response.error.message}")
        
        return response.result
    
    async def call_tool(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None,
        timeout: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Call a tool on the server with optional custom timeout.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            timeout: Custom timeout for this operation
            
        Returns:
            Tool result
        """
        self._ensure_connected()
        
        request = self.connection.protocol.create_request("tools/call", {
            "name": name,
            "arguments": arguments or {}
        })
        
        response = await self.connection.send_request(request, timeout=timeout)
        
        if response.error:
            raise MCPProtocolError(f"tools/call failed: {response.error.message}")
        
        return response.result
    
    async def list_resources(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List available resources from server.
        
        Args:
            cursor: Pagination cursor
            
        Returns:
            Resources list response
        """
        self._ensure_connected()
        
        request = self.connection.protocol.create_request("resources/list", {
            "cursor": cursor
        } if cursor else {})
        
        response = await self.connection.send_request(request)
        
        if response.error:
            raise MCPProtocolError(f"resources/list failed: {response.error.message}")
        
        return response.result
    
    async def read_resource(self, uri: str) -> Dict[str, Any]:
        """
        Read a resource from the server.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource content
        """
        self._ensure_connected()
        
        request = self.connection.protocol.create_request("resources/read", {
            "uri": uri
        })
        
        response = await self.connection.send_request(request)
        
        if response.error:
            raise MCPProtocolError(f"resources/read failed: {response.error.message}")
        
        return response.result
    
    async def list_prompts(self, cursor: Optional[str] = None) -> Dict[str, Any]:
        """
        List available prompts from server.
        
        Args:
            cursor: Pagination cursor
            
        Returns:
            Prompts list response
        """
        self._ensure_connected()
        
        request = self.connection.protocol.create_request("prompts/list", {
            "cursor": cursor
        } if cursor else {})
        
        response = await self.connection.send_request(request)
        
        if response.error:
            raise MCPProtocolError(f"prompts/list failed: {response.error.message}")
        
        return response.result
    
    async def get_prompt(
        self,
        name: str,
        arguments: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Get a prompt from the server.
        
        Args:
            name: Prompt name
            arguments: Prompt arguments
            
        Returns:
            Prompt result
        """
        self._ensure_connected()
        
        request = self.connection.protocol.create_request("prompts/get", {
            "name": name,
            "arguments": arguments or {}
        })
        
        response = await self.connection.send_request(request)
        
        if response.error:
            raise MCPProtocolError(f"prompts/get failed: {response.error.message}")
        
        return response.result
    
    async def ping(self) -> Dict[str, Any]:
        """
        Ping the server.
        
        Returns:
            Ping response
        """
        self._ensure_connected()
        
        request = self.connection.protocol.create_request("ping", {})
        response = await self.connection.send_request(request)
        
        if response.error:
            raise MCPProtocolError(f"ping failed: {response.error.message}")
        
        return response.result
    
    def add_notification_handler(self, method: str, handler: Callable) -> None:
        """
        Add handler for server notifications.
        
        Args:
            method: Notification method
            handler: Handler function
        """
        self.handler.add_notification_handler(method, handler)
    
    @property
    def server_info(self) -> Optional[MCPImplementationInfo]:
        """Get server implementation info."""
        return self.connection.peer_info if self.connection else None
    
    @property
    def server_capabilities(self) -> Optional[MCPCapabilities]:
        """Get server capabilities."""
        return self.connection.peer_capabilities if self.connection else None
    
    @property
    def is_connected(self) -> bool:
        """Check if client is connected and initialized."""
        return (
            self.connection is not None and 
            self.connection.is_initialized
        )
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get connection statistics."""
        if self.connection:
            return self.connection.get_stats()
        return {}


# Convenience functions
async def create_stdio_client(
    command: List[str],
    name: str = "python-a2a-client",
    version: str = "2.0.0",
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> MCPClient:
    """
    Create and connect MCP client via stdio.
    
    Args:
        command: Command to start server
        name: Client name
        version: Client version
        cwd: Working directory
        env: Environment variables
        timeout: Timeout
        
    Returns:
        Connected MCP client
    """
    client = MCPClient(name=name, version=version, timeout=timeout)
    await client.connect_stdio(command, cwd, env)
    return client