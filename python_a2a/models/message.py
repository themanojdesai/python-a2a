"""
Message models for the A2A protocol.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, Union
from enum import Enum

from .base import BaseModel
from .content import (
    TextContent, FunctionCallContent, FunctionResponseContent, 
    ErrorContent, Metadata, ContentType
)


class MessageRole(str, Enum):
    """Roles in A2A conversations"""
    USER = "user"
    AGENT = "agent"
    SYSTEM = "system"


@dataclass
class Message(BaseModel):
    """Represents an A2A message"""
    content: Union[TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent]
    role: MessageRole
    message_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_message_id: Optional[str] = None
    conversation_id: Optional[str] = None
    metadata: Optional[Metadata] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a Message from a dictionary"""
        content_data = data.get("content", {})
        content_type = content_data.get("type")
        
        if content_type == ContentType.TEXT:
            content = TextContent.from_dict(content_data)
        elif content_type == ContentType.FUNCTION_CALL:
            content = FunctionCallContent.from_dict(content_data)
        elif content_type == ContentType.FUNCTION_RESPONSE:
            content = FunctionResponseContent.from_dict(content_data)
        elif content_type == ContentType.ERROR:
            content = ErrorContent.from_dict(content_data)
        else:
            raise ValueError(f"Unknown content type: {content_type}")
        
        metadata = None
        if "metadata" in data:
            metadata = Metadata.from_dict(data["metadata"])
        
        # Get the role as a string, then convert to enum
        role_str = data.get("role", MessageRole.USER)
        role = MessageRole(role_str) if isinstance(role_str, str) else role_str
        
        return cls(
            content=content,
            role=role,
            message_id=data.get("message_id", str(uuid.uuid4())),
            parent_message_id=data.get("parent_message_id"),
            conversation_id=data.get("conversation_id"),
            metadata=metadata
        )