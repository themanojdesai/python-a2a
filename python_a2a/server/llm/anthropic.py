"""
Anthropic-based server implementation for the A2A protocol.
"""

import uuid
from typing import Optional, Dict, Any, List

try:
    import anthropic
except ImportError:
    anthropic = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent
from ...models.conversation import Conversation
from ..base import BaseA2AServer
from ...exceptions import A2AImportError, A2AConnectionError


class AnthropicA2AServer(BaseA2AServer):
    """
    An A2A server that uses Anthropic's API to process messages.
    
    This server converts incoming A2A messages to Anthropic's format, processes them
    using Anthropic's API, and converts the responses back to A2A format.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None
    ):
        """
        Initialize the Anthropic A2A server
        
        Args:
            api_key: Anthropic API key
            model: Anthropic model to use (default: "claude-3-opus-20240229")
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum number of tokens to generate (default: 1000)
            system_prompt: Optional system prompt to use for all conversations
        
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
        self.system_prompt = system_prompt
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def handle_message(self, message: Message) -> Message:
        """
        Process an incoming A2A message using Anthropic's API
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to Anthropic fails
        """
        try:
            # Create messages array for Anthropic
            anthropic_messages = []
            
            # Add the user message
            if message.content.type == "text":
                msg_role = "user" if message.role == MessageRole.USER else "assistant"
                anthropic_messages.append({
                    "role": msg_role,
                    "content": message.content.text
                })
            elif message.content.type == "function_call":
                # Format function call as text
                params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
                text = f"Call function {message.content.name}({params_str})"
                anthropic_messages.append({"role": "user", "content": text})
            elif message.content.type == "function_response":
                # Format function response as text
                text = f"Function {message.content.name} returned: {message.content.response}"
                anthropic_messages.append({"role": "user", "content": text})
            else:
                # Handle other message types or errors
                text = f"Message of type {message.content.type}"
                if hasattr(message.content, "message"):
                    text = message.content.message
                anthropic_messages.append({"role": "user", "content": text})
            
            # Prepare API call parameters
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": anthropic_messages
            }
            
            # Add system prompt if provided
            if self.system_prompt:
                kwargs["system"] = self.system_prompt
            
            # Call Anthropic API
            response = self.client.messages.create(**kwargs)
            
            # Convert response to A2A format
            return Message(
                content=TextContent(text=response.content[0].text),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with Anthropic: {str(e)}")
    
    def handle_conversation(self, conversation: Conversation) -> Conversation:
        """
        Process an incoming A2A conversation using Anthropic's API
        
        This method overrides the default implementation to send the entire
        conversation history to Anthropic instead of just the last message.
        
        Args:
            conversation: The incoming A2A conversation
            
        Returns:
            The updated conversation with the response
        """
        if not conversation.messages:
            # Empty conversation, create an error
            conversation.create_error_message("Empty conversation received")
            return conversation
        
        try:
            # Create messages array for Anthropic
            anthropic_messages = []
            
            # Add all messages from the conversation
            for msg in conversation.messages:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                
                if msg.content.type == "text":
                    anthropic_messages.append({
                        "role": role,
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Format function call as text
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    anthropic_messages.append({"role": role, "content": text})
                elif msg.content.type == "function_response":
                    # Format function response as text
                    text = f"Function {msg.content.name} returned: {msg.content.response}"
                    anthropic_messages.append({"role": role, "content": text})
                else:
                    # Handle other message types or errors
                    text = f"Message of type {msg.content.type}"
                    if hasattr(msg.content, "message"):
                        text = msg.content.message
                    anthropic_messages.append({"role": role, "content": text})
            
            # Prepare API call parameters
            kwargs = {
                "model": self.model,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "messages": anthropic_messages
            }
            
            # Add system prompt if provided
            if self.system_prompt:
                kwargs["system"] = self.system_prompt
            
            # Call Anthropic API
            response = self.client.messages.create(**kwargs)
            
            # Get the last message ID to use as parent
            parent_id = conversation.messages[-1].message_id
            
            # Convert response to A2A format and add to conversation
            a2a_response = Message(
                content=TextContent(text=response.content[0].text),
                role=MessageRole.AGENT,
                parent_message_id=parent_id,
                conversation_id=conversation.conversation_id
            )
            
            conversation.add_message(a2a_response)
            return conversation
        
        except Exception as e:
            # Add an error message to the conversation
            error_msg = f"Failed to communicate with Anthropic: {str(e)}"
            conversation.create_error_message(error_msg, parent_message_id=conversation.messages[-1].message_id)
            return conversation
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this agent server
        
        Returns:
            A dictionary of metadata about this agent
        """
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "AnthropicA2AServer",
            "model": self.model,
            "capabilities": ["text"]
        })
        return metadata