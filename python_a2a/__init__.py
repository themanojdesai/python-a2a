"""
Python A2A - Agent-to-Agent Protocol

A Python library for implementing Google's Agent-to-Agent (A2A) protocol.
"""

__version__ = "0.5.5"

# Setup feature flags
import sys
import importlib.util
import warnings

# Import basic exceptions first as they're used everywhere
from .exceptions import (
    A2AError,
    A2AImportError,
    A2AConnectionError,
    A2AResponseError,
    A2ARequestError,
    A2AValidationError,
    A2AAuthenticationError,
    A2AConfigurationError,
    A2AStreamingError
)

# All core models - these should be available with basic install
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
from .models.agent import AgentCard, AgentSkill
from .models.task import Task, TaskStatus, TaskState

# Core client functionality
from .client.base import BaseA2AClient
from .client.http import A2AClient
from .client.network import AgentNetwork
from .client.router import AIAgentRouter
from .client.streaming import StreamingClient

# Core server functionality
from .server.base import BaseA2AServer
from .server.a2a_server import A2AServer
from .server.http import run_server

# Agent discovery functionality
from .discovery import (
    AgentRegistry,
    run_registry,
    DiscoveryClient,
    enable_discovery,
    RegistryAgent
)

# Utility functions
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
from .utils.decorators import skill, agent

# Workflow components
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

# MCP integration
from .mcp.client import (
    MCPClient,
    MCPError,
    MCPConnectionError,
    MCPTimeoutError,
    MCPToolError,
    MCPTools
)
from .mcp.agent import MCPEnabledAgent
from .mcp.fastmcp import (
    FastMCP,
    MCPResponse,
    text_response,
    error_response,
    image_response,
    multi_content_response,
    ContentType as MCPContentType
)
from .mcp.integration import (
    FastMCPAgent,
    A2AMCPAgent
)
from .mcp.proxy import create_proxy_server
from .mcp.transport import create_fastapi_app

# LangChain integration - Always import the core functions regardless of LangChain availability
from .langchain import (
    to_a2a_server,
    to_langchain_agent,
    to_mcp_server,
    to_langchain_tool
)
from .langchain.exceptions import (
    LangChainIntegrationError,
    LangChainNotInstalledError,
    LangChainToolConversionError,
    MCPToolConversionError,
    LangChainAgentConversionError,
    A2AAgentConversionError
)
HAS_LANGCHAIN = importlib.util.find_spec("langchain") is not None or importlib.util.find_spec("langchain_core") is not None

# Optional integration with LLM providers
# These might not be available if the specific provider packages are not installed
try:
    from .client.llm import OpenAIA2AClient, AnthropicA2AClient
    from .server.llm import OpenAIA2AServer, AnthropicA2AServer, BedrockA2AServer
    HAS_LLM_CLIENTS = True
    HAS_LLM_SERVERS = True
except ImportError:
    HAS_LLM_CLIENTS = False
    HAS_LLM_SERVERS = False

# Optional doc generation
try:
    from .docs import generate_a2a_docs, generate_html_docs
    HAS_DOCS = True
except ImportError:
    HAS_DOCS = False

# Optional CLI
try:
    from .cli import main as cli_main
    HAS_CLI = True
except ImportError:
    HAS_CLI = False

# Agent Flow import - optional but integrated by default
try:
    from .agent_flow import models, engine, server, storage
    HAS_AGENT_FLOW_IMPORT = True
except ImportError:
    HAS_AGENT_FLOW_IMPORT = False

# Set feature flags (all core features should be True)
HAS_MODELS = True
HAS_ADVANCED_MODELS = True
HAS_CLIENT_BASE = True
HAS_HTTP_CLIENT = True
HAS_ADVANCED_CLIENTS = True
HAS_SERVER_BASE = True
HAS_SERVER = True
HAS_UTILS = True
HAS_DECORATORS = True
HAS_WORKFLOW = True
HAS_MCP = True
HAS_DISCOVERY = True  # Agent discovery
HAS_LANGCHAIN_INTEGRATION = True  # Always True since we provide the interface
HAS_AGENT_FLOW = True  # Agent Flow UI and workflow editor

# Define __all__ for explicit exports
__all__ = [
    # Version
    '__version__',

    # Exceptions
    'A2AError',
    'A2AImportError',
    'A2AConnectionError',
    'A2AResponseError',
    'A2ARequestError',
    'A2AValidationError',
    'A2AAuthenticationError',
    'A2AConfigurationError',
    'A2AStreamingError',
    
    # Models
    'BaseModel',
    'Message',
    'MessageRole',
    'Conversation',
    'ContentType',
    'TextContent',
    'FunctionParameter',
    'FunctionCallContent',
    'FunctionResponseContent',
    'ErrorContent',
    'Metadata',
    'AgentCard',
    'AgentSkill',
    'Task',
    'TaskStatus',
    'TaskState',
    
    # Client
    'BaseA2AClient',
    'A2AClient',
    'AgentNetwork',
    'AIAgentRouter',
    'StreamingClient',
    
    # Server
    'BaseA2AServer',
    'A2AServer',
    'run_server',
    
    # Discovery
    'AgentRegistry',
    'run_registry',
    'DiscoveryClient',
    'enable_discovery',
    'RegistryAgent',
    
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
    'skill',
    'agent',
    
    # Workflow
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
    
    # MCP
    'MCPClient',
    'MCPError', 
    'MCPConnectionError',
    'MCPTimeoutError',
    'MCPToolError',
    'MCPTools',
    'MCPEnabledAgent',
    'FastMCP',
    'MCPResponse',
    'text_response',
    'error_response',
    'image_response',
    'multi_content_response',
    'MCPContentType',
    'FastMCPAgent',
    'A2AMCPAgent',
    'create_proxy_server',
    'create_fastapi_app',
    
    # LangChain Integration (always included)
    'to_a2a_server',
    'to_langchain_agent',
    'to_mcp_server',
    'to_langchain_tool',
    'LangChainIntegrationError',
    'LangChainNotInstalledError',
    'LangChainToolConversionError',
    'MCPToolConversionError',
    'LangChainAgentConversionError',
    'A2AAgentConversionError',
]

# Conditionally add LLM clients/servers
if HAS_LLM_CLIENTS:
    __all__.extend(['OpenAIA2AClient', 'AnthropicA2AClient'])
if HAS_LLM_SERVERS:
    __all__.extend(['OpenAIA2AServer', 'AnthropicA2AServer', 'BedrockA2AServer'])

# Conditionally add docs
if HAS_DOCS:
    __all__.extend(['generate_a2a_docs', 'generate_html_docs'])

# Conditionally add CLI
if HAS_CLI:
    __all__.append('cli_main')