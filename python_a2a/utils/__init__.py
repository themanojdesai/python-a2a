"""
Utility functions for the A2A protocol.
"""

# Import and re-export utility functions for easy access
from .formatting import (
    format_message_as_text,
    format_conversation_as_text,
    pretty_print_message,
    pretty_print_conversation
)

from .validation import (
    validate_message,
    validate_conversation,
    is_valid_message,
    is_valid_conversation
)

from .conversion import (
    create_text_message,
    create_function_call,
    create_function_response,
    create_error_message,
    format_function_params,
    conversation_to_messages
)

# Import decorators
from .decorators import (
    skill,
    agent
)

# Make everything available at the utils level
__all__ = [
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
    'agent'
]