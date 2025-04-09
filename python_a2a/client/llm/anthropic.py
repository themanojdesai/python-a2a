"""
Anthropic client implementation for the A2A protocol.
"""

import uuid
from typing import List, Dict, Any, Optional, Union

try:
    import anthropic
except ImportError:
    anthropic = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, FunctionParameter
from ...models.conversation import Conversation
from ..base import BaseA2AClient
from ...exceptions import A2AImportError, A2AConnectionError


class AnthropicA2AClient(BaseA2AClient):
    """
    A2A client that uses Anthropic's Claude API to process messages.
    
    This client converts A2A messages to Anthropic's format, sends them to the Anthropic API,
    and converts the responses back to A2A format.
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-opus-20240229", temperature: float = 0.7, max_tokens: int = 1000):
        """
        Initialize the Anthropic A2A client
        
        Args:
            api_key: Anthropic API key
            model: Anthropic model to use (default: "claude-3-opus-20240229")
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum number of tokens to generate (default: 1000)
        
        Raises:
            A2AImportError: If the anthropic package is not installed
        """
        if anthropic is None:
            raise A2AImportError(
                "Anthropic package is not installed. "
                "Install it with 'pip install anthropic'"
            )
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.client = anthropic.Anthropic(api_key=api_key)
        
    def send_message(self, message: Message) -> Message:
        """
        Send a message to Anthropic and convert the response to A2A format
        
        Args:
            message: The A2A message to send
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to Anthropic fails
        """
        try:
            # Convert A2A message to Anthropic format
            if message.content.type == "text":
                # For text messages, use the text directly
                user_message = message.content.text
            elif message.content.type == "function_call":
                # For function calls, format as text
                params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
                user_message = f"Call function {message.content.name}({params_str})"
            elif message.content.type == "function_response":
                # For function responses, format as text
                user_message = f"Function {message.content.name} returned: {message.content.response}"
            else:
                # For error messages or unknown types
                user_message = f"Error: {getattr(message.content, 'message', 'Unknown message type')}"
            
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=[
                    {"role": "user", "content": user_message}
                ]
            )
            
            # Convert response back to A2A format
            return Message(
                content=TextContent(text=response.content[0].text),
                role=MessageRole.AGENT,
                message_id=str(uuid.uuid4()),
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with Anthropic: {str(e)}")
    
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to Anthropic and update with the response
        
        Args:
            conversation: The A2A conversation to send
            
        Returns:
            The updated conversation with Anthropic's response
        
        Raises:
            A2AConnectionError: If connection to Anthropic fails
        """
        if not conversation.messages:
            return conversation
        
        try:
            # Convert A2A conversation to Anthropic messages
            anthropic_messages = []
            
            for msg in conversation.messages:
                # Map A2A roles to Anthropic roles
                if msg.role == MessageRole.USER:
                    role = "user"
                elif msg.role == MessageRole.AGENT:
                    role = "assistant"
                elif msg.role == MessageRole.SYSTEM:
                    role = "user"  # Anthropic doesn't have system role, use user
                else:
                    role = "user"  # Default to user
                
                # Convert content to text
                if msg.content.type == "text":
                    content = msg.content.text
                elif msg.content.type == "function_call":
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    content = f"Call function {msg.content.name}({params_str})"
                elif msg.content.type == "function_response":
                    content = f"Function {msg.content.name} returned: {msg.content.response}"
                else:
                    content = f"Error: {getattr(msg.content, 'message', 'Unknown message type')}"
                
                anthropic_messages.append({"role": role, "content": content})
            
            # Call Anthropic API
            response = self.client.messages.create(
                model=self.model,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                messages=anthropic_messages
            )
            
            # Get the last message ID to use as parent
            parent_id = conversation.messages[-1].message_id
            
            # Convert response to A2A format and add to conversation
            a2a_response = Message(
                content=TextContent(text=response.content[0].text),
                role=MessageRole.AGENT,
                message_id=str(uuid.uuid4()),
                parent_message_id=parent_id,
                conversation_id=conversation.conversation_id
            )
            
            conversation.add_message(a2a_response)
            return conversation
        
        except Exception as e:
            # Add an error message to the conversation
            error_msg = f"Failed to communicate with Anthropic: {str(e)}"
            conversation.create_error_message(error_msg)
            return conversation