"""
Conversation models for the A2A protocol.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, ClassVar

from .base import BaseModel
from .message import Message, MessageRole
from .content import (
    TextContent, FunctionCallContent, FunctionResponseContent, 
    ErrorContent, FunctionParameter
)


@dataclass
class Conversation(BaseModel):
    """Represents an A2A conversation"""
    conversation_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[Message] = field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None
    
    # Add a class variable to track protocol compatibility mode
    _GOOGLE_A2A_COMPATIBILITY: ClassVar[bool] = False

    def add_message(self, message: Message) -> Message:
        """
        Add a message to the conversation
        
        Args:
            message: The message to add
            
        Returns:
            The added message
        """
        # Set the conversation ID if not already set
        if not message.conversation_id:
            message.conversation_id = self.conversation_id
        
        self.messages.append(message)
        return message

    def create_text_message(self, text: str, role: MessageRole, 
                           parent_message_id: Optional[str] = None) -> Message:
        """
        Create and add a text message to the conversation
        
        Args:
            text: The text content of the message
            role: The role of the sender
            parent_message_id: Optional ID of the parent message
            
        Returns:
            The created message
        """
        content = TextContent(text=text)
        message = Message(
            content=content,
            role=role,
            conversation_id=self.conversation_id,
            parent_message_id=parent_message_id
        )
        return self.add_message(message)

    def create_function_call(self, name: str, parameters: List[Dict[str, Any]], 
                            role: MessageRole = MessageRole.AGENT,
                            parent_message_id: Optional[str] = None) -> Message:
        """
        Create and add a function call message to the conversation
        
        Args:
            name: The name of the function to call
            parameters: List of parameter dictionaries with 'name' and 'value' keys
            role: The role of the sender
            parent_message_id: Optional ID of the parent message
            
        Returns:
            The created message
        """
        function_params = [FunctionParameter(name=p["name"], value=p["value"]) for p in parameters]
        content = FunctionCallContent(name=name, parameters=function_params)
        message = Message(
            content=content,
            role=role,
            conversation_id=self.conversation_id,
            parent_message_id=parent_message_id
        )
        return self.add_message(message)

    def create_function_response(self, name: str, response: Any, 
                               role: MessageRole = MessageRole.AGENT,
                               parent_message_id: Optional[str] = None) -> Message:
        """
        Create and add a function response message to the conversation
        
        Args:
            name: The name of the function that was called
            response: The response data
            role: The role of the sender
            parent_message_id: Optional ID of the parent message
            
        Returns:
            The created message
        """
        content = FunctionResponseContent(name=name, response=response)
        message = Message(
            content=content,
            role=role,
            conversation_id=self.conversation_id,
            parent_message_id=parent_message_id
        )
        return self.add_message(message)

    def create_error_message(self, error_message: str, 
                           role: MessageRole = MessageRole.SYSTEM,
                           parent_message_id: Optional[str] = None) -> Message:
        """
        Create and add an error message to the conversation
        
        Args:
            error_message: The error message text
            role: The role of the sender
            parent_message_id: Optional ID of the parent message
            
        Returns:
            The created message
        """
        content = ErrorContent(message=error_message)
        message = Message(
            content=content,
            role=role,
            conversation_id=self.conversation_id,
            parent_message_id=parent_message_id
        )
        return self.add_message(message)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a Conversation from a dictionary"""
        # Check if this is Google A2A format with careful detection
        if ("messages" in data and isinstance(data.get("messages"), list) and 
            data["messages"] and "parts" in data["messages"][0] and 
            isinstance(data["messages"][0].get("parts"), list) and
            "role" in data["messages"][0] and not "content" in data["messages"][0]):
            return cls.from_google_a2a(data)
        
        # Standard python_a2a format
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            conversation_id=data.get("conversation_id", str(uuid.uuid4())),
            messages=messages,
            metadata=data.get("metadata")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert Conversation to dictionary representation"""
        # Use google format if compatibility mode is enabled
        if self._GOOGLE_A2A_COMPATIBILITY:
            return self.to_google_a2a()
        
        # Standard python_a2a format
        result = {
            "conversation_id": self.conversation_id,
            "messages": [message.to_dict() for message in self.messages]
        }
        
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def from_google_a2a(cls, data: Dict[str, Any]) -> 'Conversation':
        """Create a Conversation from a Google A2A format dictionary
        
        Args:
            data: A dictionary in Google A2A format
            
        Returns:
            A Conversation object
        """
        if not ("messages" in data and isinstance(data.get("messages"), list)):
            raise ValueError("Not a valid Google A2A format conversation")
            
        conversation_id = data.get("conversation_id", str(uuid.uuid4()))
        
        # Process messages
        messages = []
        for msg_data in data.get("messages", []):
            # Skip invalid messages
            if not isinstance(msg_data, dict):
                continue
                
            # Try to convert from Google A2A format
            if "parts" in msg_data and "role" in msg_data and not "content" in msg_data:
                try:
                    # Convert message from Google A2A format
                    message = Message.from_google_a2a(msg_data)
                    
                    # Set conversation_id if not already set
                    if not message.conversation_id:
                        message.conversation_id = conversation_id
                        
                    messages.append(message)
                except Exception:
                    # If conversion fails, skip this message
                    continue
            else:
                # Try standard format as fallback
                try:
                    message = Message.from_dict(msg_data)
                    
                    # Set conversation_id if not already set
                    if not message.conversation_id:
                        message.conversation_id = conversation_id
                        
                    messages.append(message)
                except Exception:
                    # If parsing fails, skip this message
                    continue
        
        return cls(
            conversation_id=conversation_id,
            messages=messages,
            metadata=data.get("metadata")
        )
    
    def to_google_a2a(self) -> Dict[str, Any]:
        """Convert to Google A2A format dictionary
        
        Returns:
            A dictionary in Google A2A format
        """
        # Convert messages to Google A2A format
        google_messages = []
        for message in self.messages:
            # Convert message to Google A2A format
            try:
                google_messages.append(message.to_google_a2a())
            except Exception:
                # Skip any messages that can't be converted
                continue
        
        # Create the Google A2A conversation dict
        result = {
            "conversation_id": self.conversation_id,
            "messages": google_messages
        }
        
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result
    
    @classmethod
    def enable_google_a2a_compatibility(cls, enable: bool = True) -> None:
        """Enable or disable Google A2A compatibility mode
        
        When enabled, to_dict() will output Google A2A format
        
        Args:
            enable: Whether to enable compatibility mode
        """
        cls._GOOGLE_A2A_COMPATIBILITY = enable
        # Also update Message class compatibility
        from .message import Message
        Message.enable_google_a2a_compatibility(enable)

    @classmethod
    def is_google_a2a_compatibility_enabled(cls) -> bool:
        """Check if Google A2A compatibility mode is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return cls._GOOGLE_A2A_COMPATIBILITY