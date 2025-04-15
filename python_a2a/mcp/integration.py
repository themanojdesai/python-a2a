"""
Integration between FastMCP and A2A agents.

This module provides classes and functions to integrate FastMCP with A2A agents.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union, Callable

from ..models import Message, MessageRole, FunctionCallContent, FunctionResponseContent, TextContent
from .client import MCPClient
from .fastmcp import FastMCP, MCPResponse

# Configure logging
logger = logging.getLogger("python_a2a.mcp.integration")

class FastMCPAgent:
    """
    Mixin class that adds FastMCP capabilities to A2A agents.
    
    This class provides a more streamlined way to use FastMCP with A2A agents
    compared to the original MCPEnabledAgent.
    """
    
    def __init__(
        self, 
        mcp_servers: Optional[Dict[str, Union[str, FastMCP, MCPClient]]] = None,
        max_concurrent_calls: int = 5
    ):
        """
        Initialize FastMCP integration.
        
        Args:
            mcp_servers: Dictionary mapping server names to URLs, FastMCP instances, or MCPClient instances
            max_concurrent_calls: Maximum number of concurrent MCP tool calls
        """
        self.mcp_servers = {}
        self.mcp_clients = {}
        self._semaphore = asyncio.Semaphore(max_concurrent_calls)
        
        if mcp_servers:
            for name, server in mcp_servers.items():
                self.add_mcp_server(name, server)
    
    def add_mcp_server(
        self, 
        name: str, 
        server: Union[str, FastMCP, MCPClient],
        **client_kwargs
    ) -> None:
        """
        Add an MCP server connection.
        
        Args:
            name: Name to identify the server
            server: URL, FastMCP instance, or MCPClient instance
            **client_kwargs: Additional arguments for MCPClient if server is a URL
        """
        self.mcp_servers[name] = server
        
        # Create or use appropriate client
        if isinstance(server, str):
            # URL, create a client
            self.mcp_clients[name] = MCPClient(server, **client_kwargs)
        elif isinstance(server, FastMCP):
            # FastMCP instance, use directly
            self.mcp_clients[name] = None  # No client needed
        elif isinstance(server, MCPClient):
            # Already a client, use as is
            self.mcp_clients[name] = server
        else:
            raise ValueError(f"Unsupported server type: {type(server)}")
        
        logger.info(f"Added MCP server '{name}' of type {type(server).__name__}")
    
    async def call_mcp_tool(
        self, 
        server_name: str, 
        tool_name: str, 
        **params
    ) -> Any:
        """
        Call a tool on a specific MCP server.
        
        Args:
            server_name: Name of the server
            tool_name: Name of the tool
            **params: Parameters for the tool
            
        Returns:
            Result from the tool
            
        Raises:
            ValueError: If the server is not found
        """
        if server_name not in self.mcp_servers:
            raise ValueError(f"MCP server '{server_name}' not found")
        
        server = self.mcp_servers[server_name]
        client = self.mcp_clients[server_name]
        
        # Use semaphore to limit concurrent calls
        async with self._semaphore:
            # Call the tool differently based on server type
            if isinstance(server, FastMCP):
                # Direct call to FastMCP instance
                response = await server.call_tool(tool_name, params)
                
                # Extract text content
                content = response.content
                for item in content:
                    if item.get("type") == "text":
                        return item.get("text", "")
                
                # Return the whole response if no text content
                return response
            else:
                # Call via client
                return await client.call_tool(tool_name, **params)
    
    async def get_mcp_resource(
        self, 
        server_name: str, 
        resource_uri: str
    ) -> Any:
        """
        Get a resource from a specific MCP server.
        
        Args:
            server_name: Name of the server
            resource_uri: URI of the resource
            
        Returns:
            Resource content
            
        Raises:
            ValueError: If the server is not found
        """
        if server_name not in self.mcp_servers:
            raise ValueError(f"MCP server '{server_name}' not found")
        
        server = self.mcp_servers[server_name]
        client = self.mcp_clients[server_name]
        
        # Get the resource differently based on server type
        if isinstance(server, FastMCP):
            # Direct call to FastMCP instance
            response = await server.get_resource(resource_uri)
            
            # Extract text content
            content = response.content
            for item in content:
                if item.get("type") == "text":
                    return item.get("text", "")
            
            # Return the whole response if no text content
            return response
        else:
            # Call via client
            return await client.get_resource(resource_uri)
    
    async def handle_function_call(self, function_call: FunctionCallContent) -> Any:
        """
        Handle a function call by routing it to the appropriate MCP server.
        
        This method is intended to be called from an A2A agent's message handler.
        
        Args:
            function_call: Function call content
            
        Returns:
            Function call result
            
        Raises:
            ValueError: If the function cannot be routed to any server
        """
        function_name = function_call.name
        
        # Check if this is a server-prefixed function (server_name:tool_name)
        if ":" in function_name:
            server_name, tool_name = function_name.split(":", 1)
            if server_name in self.mcp_servers:
                # Convert parameters to a dictionary
                params = {p.name: p.value for p in function_call.parameters}
                
                # Call the tool
                return await self.call_mcp_tool(server_name, tool_name, **params)
        
        # If no server prefix, try each server
        for server_name in self.mcp_servers:
            try:
                # Convert parameters to a dictionary
                params = {p.name: p.value for p in function_call.parameters}
                
                # Try to call the tool on this server
                return await self.call_mcp_tool(server_name, function_name, **params)
            except ValueError:
                # Tool not found on this server, try the next one
                continue
        
        # If we get here, the function couldn't be handled
        raise ValueError(f"No server found that can handle function: {function_name}")
    
    async def close_mcp_connections(self) -> None:
        """Close all MCP client connections."""
        for name, client in self.mcp_clients.items():
            if client is not None:
                try:
                    await client.close()
                    logger.debug(f"Closed MCP client '{name}'")
                except Exception as e:
                    logger.warning(f"Error closing MCP client '{name}': {e}")

class A2AMCPAgent(FastMCPAgent):
    """
    A ready-to-use A2A agent with FastMCP capabilities.
    
    This class provides a complete A2A agent implementation that includes
    FastMCP capabilities, making it easy to create agents that can use MCP tools.
    """
    
    def __init__(
        self, 
        name: str,
        description: str = "",
        mcp_servers: Optional[Dict[str, Union[str, FastMCP, MCPClient]]] = None,
        message_handler: Optional[Callable[[Message], Message]] = None
    ):
        """
        Initialize A2A agent with FastMCP capabilities.
        
        Args:
            name: Agent name
            description: Agent description
            mcp_servers: Dictionary mapping server names to URLs, FastMCP instances, or MCPClient instances
            message_handler: Optional custom message handler function
        """
        # Initialize FastMCPAgent
        super().__init__(mcp_servers=mcp_servers)
        
        # Store agent information
        self.name = name
        self.description = description
        self.custom_message_handler = message_handler
    
    async def handle_message_async(self, message: Message) -> Message:
        """
        Process incoming A2A messages asynchronously.
        
        This method handles text messages by default and automatically routes
        function calls to the appropriate MCP server.
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The agent's response message
        """
        # Use custom handler if provided
        if self.custom_message_handler:
            return self.custom_message_handler(message)
        
        # Handle based on content type
        if message.content.type == "text":
            # Default text message handler
            return Message(
                content=TextContent(
                    text=f"I'm {self.name}, an A2A agent with MCP capabilities. "
                         f"You can call my functions or send me text messages."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        elif message.content.type == "function_call":
            # Route function calls to MCP servers
            try:
                result = await self.handle_function_call(message.content)
                
                # Convert result to a response message
                return Message(
                    content=FunctionResponseContent(
                        name=message.content.name,
                        response={"result": result}
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            except Exception as e:
                # Return error response
                return Message(
                    content=FunctionResponseContent(
                        name=message.content.name,
                        response={"error": str(e)}
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        else:
            # Unsupported content type
            return Message(
                content=TextContent(
                    text=f"I cannot process messages of type {message.content.type}."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_message(self, message: Message) -> Message:
        """
        Process incoming A2A messages.
        
        This method delegates to the async handler.
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The agent's response message
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.handle_message_async(message))
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this agent.
        
        Returns:
            A dictionary of metadata about this agent
        """
        return {
            "agent_type": "A2AMCPAgent",
            "name": self.name,
            "description": self.description,
            "capabilities": ["text", "function_calling"],
            "mcp_servers": list(self.mcp_servers.keys()),
            "version": "1.0.0"
        }