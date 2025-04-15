"""
Model Context Protocol (MCP) integration for python-a2a.

This module provides classes and utilities for integrating with MCP servers,
allowing A2A agents to securely access data sources and tools using the
Model Context Protocol (MCP).
"""

# Original MCP client
from .client import (
    MCPClient, 
    MCPError, 
    MCPConnectionError, 
    MCPTimeoutError, 
    MCPToolError
)

# Original MCP-enabled agent
from .agent import MCPEnabledAgent

# FastMCP implementation
from .fastmcp import (
    FastMCP,
    MCPResponse,
    text_response,
    error_response,
    image_response,
    multi_content_response
)

# Improved agent integration
from .integration import (
    FastMCPAgent,
    A2AMCPAgent
)

# Proxy functionality
from .proxy import create_proxy_server

# Transport for easy imports
from .transport import create_fastapi_app

__all__ = [
    # Client classes
    "MCPClient",
    
    # Agent classes
    "MCPEnabledAgent",
    "FastMCPAgent",
    "A2AMCPAgent",
    
    # Error classes
    "MCPError",
    "MCPConnectionError", 
    "MCPTimeoutError", 
    "MCPToolError",
    
    # FastMCP classes
    "FastMCP",
    "MCPResponse",
    "text_response",
    "error_response",
    "image_response",
    "multi_content_response",
    
    # Proxy functionality
    "create_proxy_server",
    
    # Transport
    "create_fastapi_app"
]