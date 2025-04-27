"""
Message models for the A2A protocol.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Any, Union, List, ClassVar
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
    
    # Add a class variable to track protocol compatibility mode
    _GOOGLE_A2A_COMPATIBILITY: ClassVar[bool] = False

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create a Message from a dictionary"""
        # First try to detect if this is Google A2A format
        # IMPORTANT: Very strict detection to avoid breaking existing code
        if ("parts" in data and isinstance(data.get("parts"), list) and 
            "role" in data and not "content" in data):
            try:
                return cls.from_google_a2a(data)
            except Exception:
                # If conversion fails, fall back to standard format
                # This ensures existing code is never broken by format detection
                pass
        
        # Standard python_a2a format (unchanged from original implementation)
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
        metadata_dict = data.get("metadata")
        metadata = Metadata.from_dict(metadata_dict) if metadata_dict is not None else None
        
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
    
    @classmethod
    def from_google_a2a(cls, data: Dict[str, Any]) -> 'Message':
        """Create a Message from a Google A2A format dictionary
        
        Args:
            data: A dictionary in Google A2A format
            
        Returns:
            A Message object
        """
        # Strict validation to ensure this is truly Google A2A format
        if not ("parts" in data and isinstance(data.get("parts"), list) and "role" in data):
            raise ValueError("Not a valid Google A2A format message")
        
        # Extract metadata
        metadata_dict = data.get("metadata", {}) or {}
        
        # Extract core fields from metadata if present
        message_id = metadata_dict.pop("message_id", str(uuid.uuid4())) if isinstance(metadata_dict, dict) else str(uuid.uuid4())
        parent_message_id = metadata_dict.pop("parent_message_id", None) if isinstance(metadata_dict, dict) else None
        conversation_id = metadata_dict.pop("conversation_id", None) if isinstance(metadata_dict, dict) else None
        
        # Create metadata if needed
        metadata = None
        if metadata_dict and isinstance(metadata_dict, dict):
            created_at = metadata_dict.pop("created_at", None)
            metadata = Metadata(
                created_at=created_at or "",
                custom_fields=metadata_dict
            )
        
        # Extract role
        role_str = data.get("role", "user")
        if role_str.lower() == "user":
            role = MessageRole.USER
        elif role_str.lower() == "agent":
            role = MessageRole.AGENT
        else:
            role = MessageRole.SYSTEM
        
        # Process parts
        parts = data.get("parts", [])
        content = None
        
        for part in parts:
            part_type = part.get("type")
            
            if part_type == "text":
                content = TextContent(text=part.get("text", ""))
                break
                
            elif part_type == "data":
                data_content = part.get("data", {})
                
                # Check for function call
                if "function_call" in data_content:
                    func_data = data_content["function_call"]
                    from .content import FunctionParameter
                    parameters = []
                    
                    for param in func_data.get("parameters", []):
                        parameters.append(FunctionParameter(
                            name=param.get("name", ""),
                            value=param.get("value")
                        ))
                    
                    content = FunctionCallContent(
                        name=func_data.get("name", ""),
                        parameters=parameters
                    )
                    break
                
                # Check for function response
                if "function_response" in data_content:
                    func_data = data_content["function_response"]
                    content = FunctionResponseContent(
                        name=func_data.get("name", ""),
                        response=func_data.get("response")
                    )
                    break
                
                # Check for error
                if "error" in data_content:
                    content = ErrorContent(message=data_content["error"])
                    break
        
        # Default to empty text if no content found
        if content is None:
            content = TextContent(text="")
        
        return cls(
            content=content,
            role=role,
            message_id=message_id,
            parent_message_id=parent_message_id,
            conversation_id=conversation_id,
            metadata=metadata
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Message to dictionary representation"""
        # Use google format if compatibility mode is enabled
        if self._GOOGLE_A2A_COMPATIBILITY:
            return self.to_google_a2a()
        
        # Standard python_a2a format (unchanged from original)
        result = {
            "content": self.content.to_dict(),
            "role": self.role.value
        }
        
        if self.message_id:
            result["message_id"] = self.message_id
            
        if self.parent_message_id:
            result["parent_message_id"] = self.parent_message_id
            
        if self.conversation_id:
            result["conversation_id"] = self.conversation_id
            
        if self.metadata:
            result["metadata"] = self.metadata.to_dict()
            
        return result
    
    def to_google_a2a(self) -> Dict[str, Any]:
        """Convert to Google A2A format dictionary
        
        Returns:
            A dictionary in Google A2A format
        """
        # Convert role to string
        role = self.role.value
        
        # Convert content to parts
        parts = []
        
        if self.content.type == "text":
            parts.append({
                "type": "text",
                "text": self.content.text
            })
        
        elif self.content.type == "function_call":
            # Convert function call to a data part
            function_data = {
                "name": self.content.name,
                "parameters": [{
                    "name": param.name,
                    "value": param.value
                } for param in self.content.parameters]
            }
            parts.append({
                "type": "data",
                "data": {"function_call": function_data}
            })
        
        elif self.content.type == "function_response":
            # Convert function response to a data part
            function_data = {
                "name": self.content.name,
                "response": self.content.response
            }
            parts.append({
                "type": "data",
                "data": {"function_response": function_data}
            })
        
        elif self.content.type == "error":
            # Convert error to a data part
            parts.append({
                "type": "data",
                "data": {"error": self.content.message}
            })
        
        # Create metadata dict
        metadata = {}
        if self.metadata:
            if hasattr(self.metadata, 'custom_fields'):
                metadata.update(self.metadata.custom_fields)
            if hasattr(self.metadata, 'created_at') and self.metadata.created_at:
                metadata["created_at"] = self.metadata.created_at
        
        # Add python_a2a specific fields as metadata
        if self.message_id:
            metadata["message_id"] = self.message_id
        if self.parent_message_id:
            metadata["parent_message_id"] = self.parent_message_id
        if self.conversation_id:
            metadata["conversation_id"] = self.conversation_id
        
        # Create Google A2A message dict
        return {
            "role": role,
            "parts": parts,
            "metadata": metadata
        }
    
    @classmethod
    def enable_google_a2a_compatibility(cls, enable: bool = True) -> None:
        """Enable or disable Google A2A compatibility mode
        
        When enabled, to_dict() will output Google A2A format
        
        Args:
            enable: Whether to enable compatibility mode
        """
        cls._GOOGLE_A2A_COMPATIBILITY = enable

    @classmethod
    def is_google_a2a_compatibility_enabled(cls) -> bool:
        """Check if Google A2A compatibility mode is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return cls._GOOGLE_A2A_COMPATIBILITY