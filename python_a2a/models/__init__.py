"""
Models for the A2A protocol.
"""

# Import and re-export all models for easy access
from .base import BaseModel
from .message import Message, MessageRole
from .conversation import Conversation
from .content import (
    ContentType,
    TextContent,
    FunctionParameter,
    FunctionCallContent,
    FunctionResponseContent,
    ErrorContent,
    Metadata
)

# Make everything available at the models level
__all__ = [
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
]