"""
Python A2A - Agent-to-Agent Protocol

A Python library for implementing Google's Agent-to-Agent (A2A) protocol.
"""

__version__ = "0.4.2"

# Import basic exceptions first as they're used everywhere
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

# Import core models
try:
    from .models.base import BaseModel
    from .models.message import Message, MessageRole
    from .models.conversation import Conversation
    from .models.content import (
        ContentType,
        TextContent,
        FunctionParameter,
        FunctionCallContent,
        FunctionResponseContent,
        ErrorContent,
        Metadata
    )
    
    # Try to import newer models
    try:
        from .models.agent import AgentCard, AgentSkill
        from .models.task import Task, TaskStatus, TaskState
        HAS_ADVANCED_MODELS = True
    except ImportError:
        HAS_ADVANCED_MODELS = False

    HAS_MODELS = True
except ImportError as e:
    # Handle missing models gracefully
    import sys
    print(f"Warning: Basic A2A models not fully available: {e}", file=sys.stderr)
    HAS_MODELS = False
    HAS_ADVANCED_MODELS = False

# Import basic client functionality
try:
    from .client.base import BaseA2AClient
    HAS_CLIENT_BASE = True
    
    # Try to import more advanced client components
    try:
        from .client.http import A2AClient
        HAS_HTTP_CLIENT = True
    except ImportError:
        HAS_HTTP_CLIENT = False
        
    # Try to import LLM clients
    try:
        from .client.llm import OpenAIA2AClient, AnthropicA2AClient
        HAS_LLM_CLIENTS = True
    except ImportError:
        HAS_LLM_CLIENTS = False
        
    # Try to import enhanced components
    try:
        from .client.network import AgentNetwork
        from .client.router import AIAgentRouter
        from .client.streaming import StreamingClient
        HAS_ADVANCED_CLIENTS = True
    except ImportError:
        HAS_ADVANCED_CLIENTS = False
except ImportError:
    HAS_CLIENT_BASE = False
    HAS_HTTP_CLIENT = False
    HAS_LLM_CLIENTS = False
    HAS_ADVANCED_CLIENTS = False

# Import server functionality
try:
    from .server.base import BaseA2AServer
    HAS_SERVER_BASE = True
    
    try:
        from .server.http import run_server
        from .server.a2a_server import A2AServer
        HAS_SERVER = True
    except ImportError:
        HAS_SERVER = False
    
    # Try to import LLM servers
    try:
        from .server.llm import (
            OpenAIA2AServer,
            AnthropicA2AServer,
            BedrockA2AServer
        )
        HAS_LLM_SERVERS = True
    except ImportError:
        HAS_LLM_SERVERS = False
except ImportError:
    HAS_SERVER_BASE = False
    HAS_SERVER = False
    HAS_LLM_SERVERS = False

# Import utility functions conditionally
try:
    from .utils.formatting import (
        format_message_as_text,
        format_conversation_as_text,
        pretty_print_message,
        pretty_print_conversation
    )
    from .utils.validation import (
        validate_message,
        validate_conversation,
        is_valid_message,
        is_valid_conversation
    )
    from .utils.conversion import (
        create_text_message,
        create_function_call,
        create_function_response,
        create_error_message,
        format_function_params,
        conversation_to_messages
    )
    
    # Try to import decorators
    try:
        from .utils.decorators import (
            skill,
            agent
        )
        HAS_DECORATORS = True
    except ImportError:
        HAS_DECORATORS = False
        
    HAS_UTILS = True
except ImportError:
    HAS_UTILS = False
    HAS_DECORATORS = False

# Try to import workflow system
try:
    from .workflow import (
        Flow,
        WorkflowContext,
        WorkflowStep,
        QueryStep,
        AutoRouteStep,
        FunctionStep,
        ConditionalBranch,
        ConditionStep,
        ParallelStep,
        ParallelBuilder,
        StepType
    )
    HAS_WORKFLOW = True
except ImportError:
    HAS_WORKFLOW = False

# Import documentation utilities conditionally
try:
    from .docs import (
        generate_a2a_docs,
        generate_html_docs
    )
    HAS_DOCS = True
except ImportError:
    HAS_DOCS = False

# Try to import CLI
try:
    from .cli import main as cli_main
    HAS_CLI = True
except ImportError:
    HAS_CLI = False

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

# Define __all__ based on what was successfully imported
__all__ = [
    # Version
    '__version__',

    # Exceptions - always available
    'A2AError',
    'A2AImportError',
    'A2AConnectionError',
    'A2AResponseError',
    'A2ARequestError',
    'A2AValidationError',
    'A2AAuthenticationError',
    'A2AConfigurationError',
]

# Add models if available
if HAS_MODELS:
    __all__.extend([
        # Basic models
        'BaseModel',
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
    ])

# Add advanced models if available
if HAS_ADVANCED_MODELS:
    __all__.extend([
        # Advanced models
        'AgentCard',
        'AgentSkill',
        'Task',
        'TaskStatus',
        'TaskState',
    ])

# Add client functionality if available
if HAS_CLIENT_BASE:
    __all__.append('BaseA2AClient')

if HAS_HTTP_CLIENT:
    __all__.append('A2AClient')

if HAS_LLM_CLIENTS:
    __all__.extend([
        'OpenAIA2AClient',
        'AnthropicA2AClient',
    ])

if HAS_ADVANCED_CLIENTS:
    __all__.extend([
        'AgentNetwork',
        'AIAgentRouter',
        'StreamingClient',
    ])

# Add server functionality if available
if HAS_SERVER_BASE:
    __all__.append('BaseA2AServer')

if HAS_SERVER:
    __all__.extend([
        'A2AServer',
        'run_server',
    ])

if HAS_LLM_SERVERS:
    __all__.extend([
        'OpenAIA2AServer',
        'AnthropicA2AServer',
        'BedrockA2AServer',
    ])

# Add workflow components if available
if HAS_WORKFLOW:
    __all__.extend([
        'Flow',
        'WorkflowContext',
        'WorkflowStep',
        'QueryStep',
        'AutoRouteStep',
        'FunctionStep',
        'ConditionalBranch',
        'ConditionStep',
        'ParallelStep',
        'ParallelBuilder',
        'StepType',
    ])

# Add utilities if available
if HAS_UTILS:
    __all__.extend([
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
    ])

if HAS_DECORATORS:
    __all__.extend([
        'skill',
        'agent',
    ])

# Add documentation utilities if available
if HAS_DOCS:
    __all__.extend([
        'generate_a2a_docs',
        'generate_html_docs',
    ])

# Add CLI if available
if HAS_CLI:
    __all__.append('cli_main')

# Add MCP components if available
if HAS_MCP:
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