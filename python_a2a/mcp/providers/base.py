"""
Base Provider Class

Abstract base class for all MCP providers. Provides common functionality
and enforces a consistent interface across all external MCP server integrations.
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from ..clients import MCPClient
from ..server_config import ServerConfig, MCPServerRunner

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Abstract base class for MCP providers.
    
    A provider is a high-level interface to an external MCP server.
    It handles server lifecycle, connection management, and provides
    typed methods for the server's functionality.
    
    Subclasses must implement:
    - _create_config(): Create server configuration
    - _get_provider_name(): Return provider name for logging
    """
    
    def __init__(self):
        """Initialize the base provider."""
        self.client: Optional[MCPClient] = None
        self.runner: Optional[MCPServerRunner] = None
        self._connected = False
        
        # Get provider configuration
        self.config = self._create_config()
        self.provider_name = self._get_provider_name()
        
        # Create server runner
        self.runner = MCPServerRunner(self.provider_name, self.config)
    
    @abstractmethod
    def _create_config(self) -> ServerConfig:
        """
        Create server configuration for this provider.
        
        Returns:
            ServerConfig with command, args, env, etc.
        """
        pass
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """
        Get the provider name for logging and identification.
        
        Returns:
            Provider name (e.g., "github", "browserbase", "filesystem")
        """
        pass
    
    async def connect(self) -> None:
        """
        Connect to the MCP server.
        
        Raises:
            RuntimeError: If already connected or connection fails
        """
        if self._connected:
            raise RuntimeError(f"{self.provider_name} provider already connected")
        
        logger.info(f"Starting {self.provider_name} MCP server...")
        self.client = await self.runner.start()
        self._connected = True
        logger.info(f"Connected to {self.provider_name} MCP server")
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.runner:
            await self.runner.stop()
        self.client = None
        self._connected = False
        logger.info(f"Disconnected from {self.provider_name} MCP server")
    
    @property
    def is_connected(self) -> bool:
        """Check if provider is connected to the MCP server."""
        return self._connected and self.client is not None
    
    def _ensure_connected(self) -> None:
        """Ensure provider is connected, raise error if not."""
        if not self.is_connected:
            raise RuntimeError(f"{self.provider_name} provider not connected. Call connect() first.")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server.
        
        Returns:
            List of available tools with their descriptions
        """
        self._ensure_connected()
        
        tools_response = await self.client.list_tools()
        
        # Handle different response formats (some servers return {'tools': [...]})
        if isinstance(tools_response, dict) and 'tools' in tools_response:
            return tools_response['tools']
        elif isinstance(tools_response, list):
            return tools_response
        else:
            return tools_response if tools_response else []
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None, timeout: Optional[float] = None) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            timeout: Custom timeout for this operation
            
        Returns:
            Tool result (parsed from MCP content format if needed)
            
        Raises:
            RuntimeError: If not connected
        """
        self._ensure_connected()
        
        # Use the client's built-in timeout support
        result = await self.client.call_tool(tool_name, arguments or {}, timeout=timeout)
        
        # Parse MCP content format if present
        if isinstance(result, dict) and 'content' in result:
            content = result['content']
            if content and len(content) > 0:
                if 'text' in content[0]:
                    import json
                    try:
                        # Try to parse as JSON first
                        return json.loads(content[0]['text'])
                    except json.JSONDecodeError:
                        # If not valid JSON, return the text as-is
                        return content[0]['text']
                elif content[0].get('type') == 'image' and 'data' in content[0]:
                    # For image content (like screenshots), return the raw base64 data
                    return content[0]['data']
        
        return result
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        status = "connected" if self.is_connected else "disconnected"
        return f"{self.__class__.__name__}(status={status})"


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    
    def __init__(self, provider_name: str, message: str):
        self.provider_name = provider_name
        super().__init__(f"{provider_name} provider error: {message}")


class ProviderConnectionError(ProviderError):
    """Raised when provider connection fails."""
    pass


class ProviderToolError(ProviderError):
    """Raised when tool execution fails."""
    
    def __init__(self, provider_name: str, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(provider_name, f"Tool '{tool_name}' failed: {message}")