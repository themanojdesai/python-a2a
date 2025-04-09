"""
Python A2A - Agent-to-Agent Protocol

A Python library for implementing Google's Agent-to-Agent (A2A) protocol.
"""

__version__ = "0.1.0"

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

# Make everything available at the package level
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