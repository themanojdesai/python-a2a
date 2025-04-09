"""
Conversion utilities for working with A2A messages and conversations.
"""

import uuid
from typing import Dict, List, Any, Optional, Union

from ..models.message import Message, MessageRole
from ..models.content import (
    TextContent, FunctionCallContent, FunctionResponseContent, 
    ErrorContent, FunctionParameter
)
from ..models.conversation import Conversation


def create_text_message(
    text: str, 
    role: MessageRole = MessageRole.USER,
    conversation_id: Optional[str] = None,
    parent_message_id: Optional[str] = None,
    message_id: Optional[str] = None
) -> Message:
    """
    Create a simple text message
    
    Args:
        text: The text content of the message
        role: The role of the sender (default: USER)
        conversation_id: Optional conversation ID
        parent_message_id: Optional parent message ID
        message_id: Optional message ID (will be generated if not provided)
        
    Returns:
        A new Message object
    """
    content = TextContent(text=text)
    return Message(
        content=content,
        role=role,
        message_id=message_id or str(uuid.uuid4()),
        conversation_id=conversation_id,
        parent_message_id=parent_message_id
    )


def create_function_call(
    function_name: str, 
    parameters: List[Dict[str, Any]],
    role: MessageRole = MessageRole.USER,
    conversation_id: Optional[str] = None,
    parent_message_id: Optional[str] = None,
    message_id: Optional[str] = None
) -> Message:
    """
    Create a function call message
    
    Args:
        function_name: The name of the function to call
        parameters: List of parameter dictionaries with 'name' and 'value' keys
        role: The role of the sender (default: USER)
        conversation_id: Optional conversation ID
        parent_message_id: Optional parent message ID
        message_id: Optional message ID (will be generated if not provided)
        
    Returns:
        A new Message object
    """
    function_params = [
        FunctionParameter(name=param["name"], value=param["value"])
        for param in parameters
    ]
    
    content = FunctionCallContent(
        name=function_name,
        parameters=function_params
    )
    
    return Message(
        content=content,
        role=role,
        message_id=message_id or str(uuid.uuid4()),
        conversation_id=conversation_id,
        parent_message_id=parent_message_id
    )


def create_function_response(
    function_name: str, 
    response: Any,
    role: MessageRole = MessageRole.AGENT,
    conversation_id: Optional[str] = None,
    parent_message_id: Optional[str] = None,
    message_id: Optional[str] = None
) -> Message:
    """
    Create a function response message
    
    Args:
        function_name: The name of the function that was called
        response: The response data
        role: The role of the sender (default: AGENT)
        conversation_id: Optional conversation ID
        parent_message_id: Optional parent message ID
        message_id: Optional message ID (will be generated if not provided)
        
    Returns:
        A new Message object
    """
    content = FunctionResponseContent(
        name=function_name,
        response=response
    )
    
    return Message(
        content=content,
        role=role,
        message_id=message_id or str(uuid.uuid4()),
        conversation_id=conversation_id,
        parent_message_id=parent_message_id
    )


def create_error_message(
    error_message: str,
    role: MessageRole = MessageRole.SYSTEM,
    conversation_id: Optional[str] = None,
    parent_message_id: Optional[str] = None,
    message_id: Optional[str] = None
) -> Message:
    """
    Create an error message
    
    Args:
        error_message: The error message text
        role: The role of the sender (default: SYSTEM)
        conversation_id: Optional conversation ID
        parent_message_id: Optional parent message ID
        message_id: Optional message ID (will be generated if not provided)
        
    Returns:
        A new Message object
    """
    content = ErrorContent(message=error_message)
    
    return Message(
        content=content,
        role=role,
        message_id=message_id or str(uuid.uuid4()),
        conversation_id=conversation_id,
        parent_message_id=parent_message_id
    )


def format_function_params(params: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Convert a dictionary of parameters to the format expected by function calls
    
    Args:
        params: Dictionary of parameter name-value pairs
        
    Returns:
        List of parameter dictionaries with 'name' and 'value' keys
    """
    return [{"name": key, "value": value} for key, value in params.items()]


def conversation_to_messages(conversation: Conversation) -> List[Message]:
    """
    Extract messages from a conversation
    
    Args:
        conversation: The conversation to extract messages from
        
    Returns:
        List of messages from the conversation
    """
    return conversation.messages