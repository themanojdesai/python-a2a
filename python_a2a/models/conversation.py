"""
Conversation models for the A2A protocol.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

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
        messages = [Message.from_dict(m) for m in data.get("messages", [])]
        return cls(
            conversation_id=data.get("conversation_id", str(uuid.uuid4())),
            messages=messages,
            metadata=data.get("metadata")
        )