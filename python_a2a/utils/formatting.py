"""
Formatting utilities for A2A messages and conversations.
"""

import json
from typing import Dict, List, Any, Optional

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation


def format_message_as_text(message: Message) -> str:
    """
    Format a message as a human-readable text string
    
    Args:
        message: The message to format
        
    Returns:
        A formatted string representation of the message
    """
    role = message.role.value.capitalize()
    content_type = message.content.type
    
    if content_type == "text":
        return f"{role}: {message.content.text}"
    
    elif content_type == "function_call":
        params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
        return f"{role} calls function: {message.content.name}({params_str})"
    
    elif content_type == "function_response":
        response_str = json.dumps(message.content.response, indent=2)
        return f"{role} function response: {message.content.name} -> {response_str}"
    
    elif content_type == "error":
        return f"{role} error: {message.content.message}"
    
    else:
        return f"{role}: [Unknown message type: {content_type}]"


def format_conversation_as_text(conversation: Conversation) -> str:
    """
    Format a conversation as a human-readable text string
    
    Args:
        conversation: The conversation to format
        
    Returns:
        A formatted string representation of the conversation
    """
    result = f"Conversation: {conversation.conversation_id}\n"
    result += "=" * 40 + "\n"
    
    for message in conversation.messages:
        result += format_message_as_text(message) + "\n"
    
    return result


def pretty_print_message(message: Message) -> None:
    """
    Print a message in a readable format to the console
    
    Args:
        message: The message to print
    """
    content_type = message.content.type
    role = message.role.value
    
    print(f"[{role.upper()}] | Message ID: {message.message_id}")
    
    if content_type == "text":
        print(f"Text: {message.content.text}")
    elif content_type == "function_call":
        print(f"Function Call: {message.content.name}")
        print("Parameters:")
        for param in message.content.parameters:
            print(f"  - {param.name}: {param.value}")
    elif content_type == "function_response":
        print(f"Function Response: {message.content.name}")
        print(f"Response: {json.dumps(message.content.response, indent=2)}")
    elif content_type == "error":
        print(f"Error: {message.content.message}")
    
    if message.parent_message_id:
        print(f"Parent Message: {message.parent_message_id}")
    if message.conversation_id:
        print(f"Conversation: {message.conversation_id}")
    print("-" * 50)


def pretty_print_conversation(conversation: Conversation) -> None:
    """
    Print a conversation in a readable format to the console
    
    Args:
        conversation: The conversation to print
    """
    print(f"Conversation: {conversation.conversation_id}")
    print("=" * 50)
    
    if not conversation.messages:
        print("(Empty conversation)")
        return
    
    for message in conversation.messages:
        pretty_print_message(message)