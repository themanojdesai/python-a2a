"""
Python A2A - Agent-to-Agent Protocol

A Python library for implementing Google's Agent-to-Agent (A2A) protocol.
"""

__version__ = "0.4.3"

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

# Setup feature flags and import tracking
import sys
import importlib.util
import warnings

# Initialize feature flags
HAS_MODELS = True
HAS_ADVANCED_MODELS = True
HAS_CLIENT_BASE = True
HAS_HTTP_CLIENT = True
HAS_LLM_CLIENTS = True
HAS_ADVANCED_CLIENTS = True
HAS_SERVER_BASE = True
HAS_SERVER = True
HAS_LLM_SERVERS = True
HAS_UTILS = True
HAS_DECORATORS = True
HAS_WORKFLOW = True
HAS_DOCS = True
HAS_CLI = True
HAS_MCP = True

# Define a helper function to check if a module exists
def _check_module(module_name):
    """Check if a module exists without importing it"""
    return importlib.util.find_spec(module_name) is not None

# Define a function to import a module and handle import errors
def _safe_import(import_statement, error_message, feature_flag=None):
    """Execute an import statement safely and set a feature flag if provided"""
    try:
        exec(import_statement)
        return True
    except ImportError as e:
        # Only show warnings in verbose mode
        if "--verbose" in sys.argv or "--debug" in sys.argv:
            warnings.warn(f"{error_message}: {e}", ImportWarning)
        if feature_flag:
            globals()[feature_flag] = False
        return False
    except Exception as e:
        # Only show warnings in verbose mode
        if "--verbose" in sys.argv or "--debug" in sys.argv:
            warnings.warn(f"Unexpected error importing {import_statement}: {e}", ImportWarning)
        if feature_flag:
            globals()[feature_flag] = False
        return False

# Import all modules - we expect all dependencies to be installed now
_safe_import("""
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
""", "Failed to import basic models", "HAS_MODELS")

_safe_import("""
from .models.agent import AgentCard, AgentSkill
from .models.task import Task, TaskStatus, TaskState
""", "Failed to import advanced models", "HAS_ADVANCED_MODELS")

_safe_import("""
from .client.base import BaseA2AClient
""", "Failed to import client base", "HAS_CLIENT_BASE")

_safe_import("""
from .client.http import A2AClient
""", "Failed to import HTTP client", "HAS_HTTP_CLIENT")

_safe_import("""
from .client.llm import OpenAIA2AClient, AnthropicA2AClient
""", "Failed to import LLM clients", "HAS_LLM_CLIENTS")

_safe_import("""
from .client.network import AgentNetwork
from .client.router import AIAgentRouter
from .client.streaming import StreamingClient
""", "Failed to import advanced client features", "HAS_ADVANCED_CLIENTS")

_safe_import("""
from .server.base import BaseA2AServer
""", "Failed to import server base", "HAS_SERVER_BASE")

_safe_import("""
from .server.http import run_server
from .server.a2a_server import A2AServer
""", "Failed to import server", "HAS_SERVER")

_safe_import("""
from .server.llm import (
    OpenAIA2AServer,
    AnthropicA2AServer,
    BedrockA2AServer
)
""", "Failed to import LLM servers", "HAS_LLM_SERVERS")

_safe_import("""
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
""", "Failed to import utilities", "HAS_UTILS")

_safe_import("""
from .utils.decorators import (
    skill,
    agent
)
""", "Failed to import decorators", "HAS_DECORATORS")

_safe_import("""
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
""", "Failed to import workflow system", "HAS_WORKFLOW")

_safe_import("""
from .docs import (
    generate_a2a_docs,
    generate_html_docs
)
""", "Failed to import documentation utilities", "HAS_DOCS")

_safe_import("""
from .cli import main as cli_main
""", "Failed to import CLI", "HAS_CLI")

_safe_import("""
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
""", "Failed to import MCP module", "HAS_MCP")

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

# Add a single informational message about potential missing dependencies
def check_and_report_issues():
    """Check for any potential issues and report if necessary"""
    # Only show this in verbose or debug mode
    if "--verbose" not in sys.argv and "--debug" not in sys.argv:
        return
    
    issues = []
    
    # Check for critical missing features
    if not HAS_MODELS:
        issues.append("Basic models not available - check package installation")
    if not HAS_CLIENT_BASE:
        issues.append("Client functionality not available - check package installation")
    if not HAS_SERVER_BASE:
        issues.append("Server functionality not available - check package installation")
    if not HAS_MCP:
        issues.append("MCP functionality not available - check package installation")
    
    if issues:
        print("\nWarning: Python A2A detected issues:")
        for issue in issues:
            print(f"  - {issue}")
        print("\nReinstall the package with: pip install --force-reinstall python-a2a\n")

# Only check in verbose mode
if "--verbose" in sys.argv or "--debug" in sys.argv:
    check_and_report_issues()