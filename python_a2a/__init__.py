"""
Python A2A - Agent-to-Agent Protocol

A Python library for implementing Google's Agent-to-Agent (A2A) protocol.
"""

__version__ = "0.2.0"

# Import core models
from .models import (
    Message,
    MessageRole,
    Conversation,
    TextContent,
    FunctionParameter,
    FunctionCallContent,
    FunctionResponseContent,
    ErrorContent,
    Metadata,
    ContentType
)

# Import clients
from .client import (
    BaseA2AClient,
    A2AClient,
    OpenAIA2AClient,
    AnthropicA2AClient
)

# Import servers
from .server import (
    BaseA2AServer,
    A2AServer,
    run_server,
    OpenAIA2AServer,
    AnthropicA2AServer
)

# Import utility functions
from .utils import (
    # Formatting utilities
    format_message_as_text,
    format_conversation_as_text,
    pretty_print_message,
    pretty_print_conversation,
    
    # Validation utilities
    validate_message,
    validate_conversation,
    is_valid_message,
    is_valid_conversation,
    
    # Conversion utilities
    create_text_message,
    create_function_call,
    create_function_response,
    create_error_message,
    format_function_params,
    conversation_to_messages
)

# Import exceptions
from .exceptions import (
    A2AError,
    A2AImportError,
    A2AConnectionError,
    A2AResponseError,
    A2ARequestError,
    A2AValidationError,
    A2AAuthenticationError,
    A2AConfigurationError
)

# Expose command-line interface
from .cli import main as cli_main

# Import MCP integration with improved error handling
try:
    # MCP client
    from .mcp.client import (
        MCPClient, 
        MCPError, 
        MCPConnectionError, 
        MCPTimeoutError, 
        MCPToolError,
        MCPTools
    )
    
    # MCP agent integration
    from .mcp.agent import MCPEnabledAgent
    
    # FastMCP implementation
    from .mcp.fastmcp import (
        FastMCP,
        MCPResponse,
        text_response,
        error_response,
        image_response,
        multi_content_response,
        ContentType as MCPContentType
    )
    
    # Improved agent integration
    from .mcp.integration import (
        FastMCPAgent,
        A2AMCPAgent
    )
    
    # Proxy functionality
    from .mcp.proxy import create_proxy_server
    
    # Transport for easy imports
    from .mcp.transport import create_fastapi_app
    
    HAS_MCP = True
except ImportError as e:
    # Print more detailed error information to help diagnose import issues
    import sys
    print(f"Warning: MCP module could not be imported: {e}", file=sys.stderr)
    HAS_MCP = False

# Base package exports
__all__ = [
    # Version
    '__version__',
    
    # Models
    'Message',
    'MessageRole',
    'Conversation',
    'TextContent',
    'FunctionParameter',
    'FunctionCallContent',
    'FunctionResponseContent',
    'ErrorContent',
    'Metadata',
    'ContentType',
    
    # Clients
    'BaseA2AClient',
    'A2AClient',
    'OpenAIA2AClient',
    'AnthropicA2AClient',
    
    # Servers
    'BaseA2AServer',
    'A2AServer',
    'run_server',
    'OpenAIA2AServer',
    'AnthropicA2AServer',
    
    # Utilities
    'format_message_as_text',
    'format_conversation_as_text',
    'pretty_print_message',
    'pretty_print_conversation',
    'validate_message',
    'validate_conversation',
    'is_valid_message',
    'is_valid_conversation',
    'create_text_message',
    'create_function_call',
    'create_function_response',
    'create_error_message',
    'format_function_params',
    'conversation_to_messages',
    
    # Exceptions
    'A2AError',
    'A2AImportError',
    'A2AConnectionError',
    'A2AResponseError',
    'A2ARequestError',
    'A2AValidationError',
    'A2AAuthenticationError',
    'A2AConfigurationError',
    
    # CLI
    'cli_main',
]

# Add MCP classes if available
if HAS_MCP:
    # Add to __all__ list
    __all__.extend([
        # MCP client
        'MCPClient',
        'MCPError',
        'MCPConnectionError',
        'MCPTimeoutError',
        'MCPToolError',
        'MCPTools',
        
        # MCP agent integration
        'MCPEnabledAgent',
        
        # FastMCP implementation
        'FastMCP',
        'MCPResponse',
        'text_response',
        'error_response',
        'image_response',
        'multi_content_response',
        'MCPContentType',
        
        # Improved agent integration
        'FastMCPAgent',
        'A2AMCPAgent',
        
        # Proxy functionality
        'create_proxy_server',
        
        # Transport
        'create_fastapi_app'
    ])