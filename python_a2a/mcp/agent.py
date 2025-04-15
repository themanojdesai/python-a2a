"""
Adds MCP capabilities to A2A agents.
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Set
from concurrent.futures import ThreadPoolExecutor

from ..models import Message, MessageRole, FunctionCallContent, FunctionResponseContent, TextContent
from .client import MCPClient, MCPError, MCPConnectionError, MCPTimeoutError, MCPToolError

logger = logging.getLogger(__name__)

class MCPEnabledAgent:
    """
    Mixin class that adds MCP capabilities to A2A agents.
    """
    
    def __init__(
        self, 
        mcp_servers: Optional[Dict[str, Union[str, Dict[str, Any]]]] = None,
        tool_discovery: bool = True,
        max_concurrent_calls: int = 5,
        executor: Optional[ThreadPoolExecutor] = None
    ):
        """
        Initialize MCP integration
        
        Args:
            mcp_servers: Dictionary mapping server names to URLs or config dicts
            tool_discovery: Whether to automatically discover tools on initialization
            max_concurrent_calls: Maximum number of concurrent MCP tool calls
            executor: Optional thread pool executor for blocking operations
        """
        self.mcp_servers = {}
        self.mcp_clients = {}
        self._tool_capabilities = {}  # Map of tool names to server names
        self._initialized = False
        self._executor = executor
        self._tool_discovery = tool_discovery
        self._semaphore = asyncio.Semaphore(max_concurrent_calls)
        
        if mcp_servers:
            for name, config in mcp_servers.items():
                # Handle both string URLs and config dictionaries
                if isinstance(config, str):
                    self.add_mcp_server(name, config)
                elif isinstance(config, dict):
                    url = config.pop("url", None)
                    if url:
                        self.add_mcp_server(name, url, **config)
    
    def add_mcp_server(self, name: str, url: str, **config) -> None:
        """
        Add an MCP server connection
        
        Args:
            name: Name to identify the server
            url: URL of the MCP server
            **config: Additional configuration for the client
        """
        self.mcp_servers[name] = url
        self.mcp_clients[name] = MCPClient(url, **config)
    
    async def initialize_mcp_servers(self) -> None:
        """
        Initialize all MCP server connections
        
        This fetches available tools from each server and builds
        a mapping of tool capabilities.
        """
        if self._initialized:
            return
            
        # Create tasks for initializing each server
        tasks = []
        for name, client in self.mcp_clients.items():
            if self._tool_discovery:
                tasks.append(self._init_server(name, client))
            
        # Run all initialization tasks concurrently
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check for errors
            for i, (name, _) in enumerate(self.mcp_clients.items()):
                result = results[i]
                if isinstance(result, Exception):
                    logger.warning(f"Failed to initialize MCP server '{name}': {result}")
        
        self._initialized = True
    
    async def _init_server(self, name: str, client: MCPClient) -> None:
        """Initialize a single MCP server"""
        try:
            tools = await client.get_tools()
            logger.info(f"Initialized MCP server '{name}' with {len(tools)} tools")
            
            # Update tool capabilities mapping
            for tool in tools:
                tool_name = tool["name"]
                if tool_name not in self._tool_capabilities:
                    self._tool_capabilities[tool_name] = set()
                self._tool_capabilities[tool_name].add(name)
                
        except Exception as e:
            logger.warning(f"Failed to initialize MCP server '{name}': {e}")
            raise
    
    async def close_mcp_connections(self) -> None:
        """Close all MCP client connections"""
        tasks = []
        for name, client in self.mcp_clients.items():
            tasks.append(self._close_client(name, client))
            
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _close_client(self, name: str, client: MCPClient) -> None:
        """Close a single MCP client connection"""
        try:
            await client.close()
            logger.debug(f"Closed MCP client '{name}'")
        except Exception as e:
            logger.warning(f"Error closing MCP client '{name}': {e}")
    
    async def call_mcp_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        stream: bool = False,
        **params
    ) -> Any:
        """
        Call a tool on a specific MCP server
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            stream: Whether to stream the response
            **params: Parameters for the tool
            
        Returns:
            Result from the tool
            
        Raises:
            ValueError: If the server is not found
            MCPError: For errors communicating with the MCP server
        """
        if not self._initialized:
            await self.initialize_mcp_servers()
            
        if server_name not in self.mcp_clients:
            raise ValueError(f"MCP server '{server_name}' not found")
        
        client = self.mcp_clients[server_name]
        
        # Use semaphore to limit concurrent calls
        async with self._semaphore:
            return await client.call_tool(tool_name, stream=stream, **params)
    
    async def process_function_call(self, function_call: FunctionCallContent) -> Any:
        """
        Process a function call, routing to appropriate MCP server
        
        Args:
            function_call: Function call content
            
        Returns:
            Result from the function call
            
        Raises:
            ValueError: If the function or server is not found
            MCPError: For errors communicating with the MCP server
        """
        if not self._initialized:
            await self.initialize_mcp_servers()
            
        function_name = function_call.name
        
        # Check if this is an MCP function call (server_name_tool_name format)
        if "_" in function_name:
            parts = function_name.split("_", 1)
            if len(parts) == 2 and parts[0] in self.mcp_clients:
                server_name, tool_name = parts
                
                # Convert parameters to a dictionary
                params = {p.name: p.value for p in function_call.parameters}
                
                # Call the MCP tool
                return await self.call_mcp_tool(server_name, tool_name, **params)
        
        # Check if we have this tool in our capabilities map
        if function_name in self._tool_capabilities:
            # Get the first server that can handle this tool
            server_name = next(iter(self._tool_capabilities[function_name]))
            
            # Convert parameters to a dictionary
            params = {p.name: p.value for p in function_call.parameters}
            
            # Call the MCP tool
            return await self.call_mcp_tool(server_name, function_name, **params)
        
        # Not an MCP function call
        raise ValueError(f"Unknown function: {function_name}")
    
    def get_servers_for_tool(self, tool_name: str) -> Set[str]:
        """
        Get all server names that provide a specific tool
        
        Args:
            tool_name: The name of the tool
            
        Returns:
            Set of server names
        """
        return self._tool_capabilities.get(tool_name, set())
    
    def get_all_mcp_function_specs(self) -> List[Dict[str, Any]]:
        """
        Get all function specifications from all MCP servers
        
        Returns:
            List of function specifications for LLM function calling
        """
        all_specs = []
        
        # Add server-prefixed specs
        for name, client in self.mcp_clients.items():
            specs = client.get_function_specs()
            
            # Add server name prefix to avoid name collisions
            for spec in specs:
                prefixed_spec = spec.copy()
                prefixed_spec["name"] = f"{name}_{spec['name']}"
                prefixed_spec["description"] = f"[From {name}] {spec['description']}"
                all_specs.append(prefixed_spec)
                
        return all_specs
    
    def get_all_mcp_tools(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get all available tools from all MCP servers
        
        Returns:
            Dictionary mapping server names to tool lists
        """
        return {
            name: (client._tools_cache.tools if client._tools_cache else [])
            for name, client in self.mcp_clients.items()
        }