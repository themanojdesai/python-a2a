"""
Model Context Protocol (MCP) integration for python-a2a.

This module provides both the original MCP implementation and a new 
specification-compliant implementation following the 2025-03-26 specification.

BACKWARD COMPATIBILITY:
All existing imports continue to work unchanged:
- MCPClient (original implementation)
- MCPEnabledAgent, FastMCP, etc.

NEW MCP 2025-03-26 API (Official Specification Terms):
For new projects or when upgrading, use:
- Client (official MCP client implementation)
- Server (official MCP server implementation)  
- create_stdio_client() (convenience function)

Key Features of New Implementation:
- Full MCP 2025-03-26 specification compliance
- Proper JSON-RPC 2.0 implementation
- Standard stdio transport (as recommended by spec)
- Complete server with tools/resources/prompts
- Robust lifecycle management
- Production-ready for millions of users
- No monkey patching or proxy patterns

Migration Path:
Existing code: from python_a2a.mcp import MCPClient  # Still works
New code:     from python_a2a.mcp import Client, Server  # Official MCP terms
"""

# Core MCP protocol implementation (new, spec-compliant)
from .protocol import (
    MCPProtocolHandler,
    MCPProtocolError,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    JSONRPCErrorCode,
    MCPImplementationInfo,
    MCPCapabilities,
    MCPContent,
    create_text_content,
    create_image_content,
    create_blob_content
)

# MCP Server implementation (new, spec-compliant)
from .server import (
    MCPServer,
    MCPServerHandler,
    MCPTool,
    MCPResource,
    MCPPrompt
)

# MCP Connection and lifecycle management (new, spec-compliant)
from .connection import (
    MCPConnection,
    MCPConnectionState,
    MCPMessageHandler
)

# Standard stdio transport (new, spec-compliant)
from .transports import (
    StdioTransport,
    ServerStdioTransport,
    create_stdio_transport,
    create_server_stdio_transport
)

# Backward compatibility: Keep original MCPClient as default
from .client import (
    MCPClient,  # Original client - maintains backward compatibility
    MCPError, 
    MCPConnectionError, 
    MCPTimeoutError, 
    MCPToolError
)

# New implementation following MCP specification terminology
from .clients import (
    MCPClient as Client,
    MCPClientHandler,
    create_stdio_client
)
from .server import (
    MCPServer as Server,
    MCPServerHandler
)

# Backward compatibility: Legacy agent
from .agent import MCPEnabledAgent

# Backward compatibility: FastMCP implementation
from .fastmcp import (
    FastMCP,
    MCPResponse,
    text_response,
    error_response,
    image_response,
    multi_content_response
)

# Server configuration and management
from .server_config import (
    ServerConfig,
    MCPServerRunner, 
    MCPServerManager,
    create_github_config,
    create_filesystem_config
)

# MCP providers for external servers (local only)
from .providers import (
    GitHubMCPServer, BrowserbaseMCPServer, FilesystemMCPServer, 
    PuppeteerMCPServer, PlaywrightMCPServer
)

# Backward compatibility: Legacy integrations (DEPRECATED)
try:
    from .integration import (
        FastMCPAgent,
        A2AMCPAgent
    )
except ImportError:
    # Integration module may not exist in all environments
    FastMCPAgent = None
    A2AMCPAgent = None

# Backward compatibility: Proxy functionality (DEPRECATED)
try:
    from .proxy import create_proxy_server
except ImportError:
    create_proxy_server = None

# Backward compatibility: Transport
try:
    from .transport import create_fastapi_app
except ImportError:
    create_fastapi_app = None

# Main API - use these for new code
# MCPClient is the primary client interface (from clients.py)

__all__ = [
    # Backward compatibility (existing imports continue to work)
    "MCPClient",  # Original client implementation
    "MCPEnabledAgent",
    "FastMCP",
    "MCPResponse",
    "text_response",
    "error_response", 
    "image_response",
    "multi_content_response",
    
    # Common error classes
    "MCPError",
    "MCPConnectionError",
    "MCPTimeoutError", 
    "MCPToolError",
    
    # New MCP 2025-03-26 API (Official Specification Terms)
    "Server",   # Official MCP server
    "Client",   # Official MCP client
    "MCPConnection",
    "StdioTransport",
    "create_stdio_transport",
    "create_server_stdio_transport",
    "create_stdio_client",
    
    # Core protocol classes
    "MCPProtocolHandler",
    "MCPImplementationInfo",
    "MCPCapabilities",
    "MCPContent",
    "MCPConnectionState",
    
    # Server components
    "MCPServerHandler",
    "MCPTool",
    "MCPResource", 
    "MCPPrompt",
    "MCPMessageHandler",
    
    # Client components
    "MCPClientHandler",
    
    # Content creation helpers
    "create_text_content",
    "create_image_content", 
    "create_blob_content",
    
    # Core errors and protocols
    "MCPProtocolError",
    "JSONRPCRequest",
    "JSONRPCResponse", 
    "JSONRPCError",
    "JSONRPCErrorCode",
    
    # Server configuration and management
    "ServerConfig",
    "MCPServerRunner",
    "MCPServerManager", 
    "create_github_config",
    "create_filesystem_config",
    
    # High-level MCP providers (local)
    "GitHubMCPServer",
    "BrowserbaseMCPServer",
    "FilesystemMCPServer",
    "PuppeteerMCPServer",
    "PlaywrightMCPServer",
]

# Add conditional exports for backward compatibility
if FastMCPAgent is not None:
    __all__.extend(["FastMCPAgent", "A2AMCPAgent"])

if create_proxy_server is not None:
    __all__.append("create_proxy_server")

if create_fastapi_app is not None:
    __all__.append("create_fastapi_app")

# Version info
__version__ = "2.0.0"  # Major version bump for spec compliance