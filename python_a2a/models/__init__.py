"""
Models for the A2A protocol.
"""

# Import base models first (they have no dependencies)
from .base import BaseModel

# Import content types which most other models depend on
from .content import (
    ContentType,
    TextContent,
    FunctionParameter,
    FunctionCallContent,
    FunctionResponseContent,
    ErrorContent,
    Metadata
)

# Import core communication models
from .message import Message, MessageRole
from .conversation import Conversation

# Import newer models with defensive imports
try:
    from .agent import AgentCard, AgentSkill
except ImportError:
    # These may not be available yet
    pass

try:
    from .task import Task, TaskStatus, TaskState
except ImportError:
    # These may not be available yet
    pass

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

# Conditionally add newer models to __all__ if they're available
try:
    AgentCard
    AgentSkill
    __all__.extend(['AgentCard', 'AgentSkill'])
except NameError:
    pass

try:
    Task
    TaskStatus
    TaskState
    __all__.extend(['Task', 'TaskStatus', 'TaskState'])
except NameError:
    pass