"""
Validation utilities for A2A messages and conversations.
"""

from typing import Dict, List, Any, Optional, Union
import uuid

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..exceptions import A2AValidationError


def validate_message(message: Message) -> None:
    """
    Validate that a message conforms to the A2A protocol
    
    Args:
        message: The message to validate
        
    Raises:
        A2AValidationError: If the message is invalid
    """
    # Check required fields
    if not hasattr(message, 'content') or message.content is None:
        raise A2AValidationError("Message must have content")
    
    if not hasattr(message, 'role') or message.role is None:
        raise A2AValidationError("Message must have a role")
    
    # Check valid role
    if message.role not in list(MessageRole):
        raise A2AValidationError(f"Invalid role: {message.role}. Must be one of {list(MessageRole)}")
    
    # Validate content based on type
    content_type = message.content.type
    
    if content_type == "text":
        if not hasattr(message.content, "text") or not message.content.text:
            raise A2AValidationError("Text content must have a text field")
    
    elif content_type == "function_call":
        if not hasattr(message.content, "name") or not message.content.name:
            raise A2AValidationError("Function call must have a name")
        
        if not hasattr(message.content, "parameters"):
            raise A2AValidationError("Function call must have a parameters field")
    
    elif content_type == "function_response":
        if not hasattr(message.content, "name") or not message.content.name:
            raise A2AValidationError("Function response must have a name")
        
        if not hasattr(message.content, "response"):
            raise A2AValidationError("Function response must have a response field")
    
    elif content_type == "error":
        if not hasattr(message.content, "message") or not message.content.message:
            raise A2AValidationError("Error content must have a message field")
    
    else:
        raise A2AValidationError(f"Unknown content type: {content_type}")
    
    # Validate IDs
    if message.message_id:
        try:
            uuid.UUID(message.message_id)
        except ValueError:
            # Not raising an error here, as custom ID formats are allowed
            pass
    
    if message.parent_message_id:
        try:
            uuid.UUID(message.parent_message_id)
        except ValueError:
            # Not raising an error here, as custom ID formats are allowed
            pass
    
    if message.conversation_id:
        try:
            uuid.UUID(message.conversation_id)
        except ValueError:
            # Not raising an error here, as custom ID formats are allowed
            pass


def is_valid_message(message: Message) -> bool:
    """
    Check if a message is valid according to the A2A protocol
    
    Args:
        message: The message to check
        
    Returns:
        True if the message is valid, False otherwise
    """
    try:
        validate_message(message)
        return True
    except A2AValidationError:
        return False


def validate_conversation(conversation: Conversation) -> None:
    """
    Validate that a conversation conforms to the A2A protocol
    
    Args:
        conversation: The conversation to validate
        
    Raises:
        A2AValidationError: If the conversation is invalid
    """
    # Check required fields
    if not hasattr(conversation, 'conversation_id') or not conversation.conversation_id:
        raise A2AValidationError("Conversation must have an ID")
    
    if not hasattr(conversation, 'messages'):
        raise A2AValidationError("Conversation must have a messages field")
    
    # Validate all messages in the conversation
    for i, message in enumerate(conversation.messages):
        try:
            validate_message(message)
        except A2AValidationError as e:
            raise A2AValidationError(f"Invalid message at index {i}: {str(e)}")
        
        # Check that the conversation_id matches
        if message.conversation_id and message.conversation_id != conversation.conversation_id:
            raise A2AValidationError(
                f"Message at index {i} has conversation_id {message.conversation_id}, "
                f"which does not match the conversation's ID {conversation.conversation_id}"
            )


def is_valid_conversation(conversation: Conversation) -> bool:
    """
    Check if a conversation is valid according to the A2A protocol
    
    Args:
        conversation: The conversation to check
        
    Returns:
        True if the conversation is valid, False otherwise
    """
    try:
        validate_conversation(conversation)
        return True
    except A2AValidationError:
        return False