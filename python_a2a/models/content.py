"""
Content types for A2A messages.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import datetime

from .base import BaseModel


class ContentType(str, Enum):
    """Types of A2A message content"""
    TEXT = "text"
    FUNCTION_CALL = "function_call"
    FUNCTION_RESPONSE = "function_response"
    ERROR = "error"


@dataclass
class TextContent(BaseModel):
    """Simple text message content"""
    text: str
    type: str = ContentType.TEXT
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TextContent':
        """Create a TextContent object from a dictionary"""
        return cls(
            text=data.get("text", ""),
            type=data.get("type", ContentType.TEXT)
        )


@dataclass
class FunctionParameter(BaseModel):
    """Parameter for a function call"""
    name: str
    value: Any
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FunctionParameter':
        """Create a FunctionParameter from a dictionary"""
        return cls(
            name=data.get("name", ""),
            value=data.get("value")
        )


@dataclass
class FunctionCallContent(BaseModel):
    """Function call message content"""
    name: str
    parameters: List[FunctionParameter] = field(default_factory=list)
    type: str = ContentType.FUNCTION_CALL
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FunctionCallContent':
        """Create a FunctionCallContent from a dictionary"""
        parameters = [
            FunctionParameter.from_dict(param) 
            for param in data.get("parameters", [])
        ]
        
        return cls(
            name=data.get("name", ""),
            parameters=parameters,
            type=data.get("type", ContentType.FUNCTION_CALL)
        )


@dataclass
class FunctionResponseContent(BaseModel):
    """Function response message content"""
    name: str
    response: Any
    type: str = ContentType.FUNCTION_RESPONSE
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FunctionResponseContent':
        """Create a FunctionResponseContent from a dictionary"""
        return cls(
            name=data.get("name", ""),
            response=data.get("response"),
            type=data.get("type", ContentType.FUNCTION_RESPONSE)
        )


@dataclass
class ErrorContent(BaseModel):
    """Error message content"""
    message: str
    type: str = ContentType.ERROR
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ErrorContent':
        """Create an ErrorContent from a dictionary"""
        return cls(
            message=data.get("message", ""),
            type=data.get("type", ContentType.ERROR)
        )


@dataclass
class Metadata(BaseModel):
    """Custom metadata that can be attached to a message"""
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Metadata':
        """Create a Metadata from a dictionary"""
        return cls(
            created_at=data.get("created_at", datetime.datetime.now().isoformat()),
            custom_fields=data.get("custom_fields", {})
        )