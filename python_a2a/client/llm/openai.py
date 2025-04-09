"""
OpenAI client implementation for the A2A protocol.
"""

import uuid
from typing import List, Dict, Any, Optional, Union

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, FunctionParameter
from ...models.conversation import Conversation
from ..base import BaseA2AClient
from ...exceptions import A2AImportError, A2AConnectionError


class OpenAIA2AClient(BaseA2AClient):
    """
    A2A client that uses OpenAI API to process messages.
    
    This client converts A2A messages to OpenAI's format, sends them to the OpenAI API,
    and converts the responses back to A2A format.
    """
    
    def __init__(self, api_key: str, model: str = "gpt-4", temperature: float = 0.7):
        """
        Initialize the OpenAI A2A client
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (default: "gpt-4")
            temperature: Generation temperature (default: 0.7)
        
        Raises:
            A2AImportError: If the OpenAI package is not installed
        """
        if OpenAI is None:
            raise A2AImportError(
                "OpenAI package is not installed. "
                "Install it with 'pip install openai'"
            )
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.client = OpenAI(api_key=api_key)
        
    def send_message(self, message: Message) -> Message:
        """
        Send a message to OpenAI and convert the response to A2A format
        
        Args:
            message: The A2A message to send
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to OpenAI fails
        """
        # Convert A2A message to OpenAI format
        openai_messages = self._convert_messages_to_openai_format([message])
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
            )
            
            # Convert response back to A2A format
            return self._convert_openai_response_to_a2a(response, message.message_id, message.conversation_id)
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with OpenAI: {str(e)}")
    
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to OpenAI and update with the response
        
        Args:
            conversation: The A2A conversation to send
            
        Returns:
            The updated conversation with OpenAI's response
        
        Raises:
            A2AConnectionError: If connection to OpenAI fails
        """
        if not conversation.messages:
            return conversation
        
        # Convert A2A conversation to OpenAI format
        openai_messages = self._convert_messages_to_openai_format(conversation.messages)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=openai_messages,
                temperature=self.temperature,
            )
            
            # Get the last message ID to use as parent
            parent_id = conversation.messages[-1].message_id
            
            # Convert response to A2A format and add to conversation
            a2a_response = self._convert_openai_response_to_a2a(
                response, 
                parent_id, 
                conversation.conversation_id
            )
            
            conversation.add_message(a2a_response)
            return conversation
        
        except Exception as e:
            # Add an error message to the conversation
            error_msg = f"Failed to communicate with OpenAI: {str(e)}"
            conversation.create_error_message(error_msg)
            return conversation
    
    def _convert_messages_to_openai_format(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        Convert A2A messages to OpenAI format
        
        Args:
            messages: List of A2A messages
            
        Returns:
            List of OpenAI-formatted messages
        """
        result = []
        
        for msg in messages:
            # Map A2A roles to OpenAI roles
            if msg.role == MessageRole.USER:
                role = "user"
            elif msg.role == MessageRole.AGENT:
                role = "assistant"
            elif msg.role == MessageRole.SYSTEM:
                role = "system"
            else:
                # Default to user if role is unknown
                role = "user"
            
            # Convert based on content type
            if msg.content.type == "text":
                result.append({
                    "role": role,
                    "content": msg.content.text
                })
            elif msg.content.type == "function_call":
                # OpenAI doesn't have a direct equivalent for incoming function calls,
                # so we convert it to a user message describing the function call
                params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                result.append({
                    "role": "user",
                    "content": f"Call function {msg.content.name}({params_str})"
                })
            elif msg.content.type == "function_response":
                # Convert function response to a text message
                result.append({
                    "role": role,
                    "content": f"Function {msg.content.name} returned: {msg.content.response}"
                })
            # Ignore error messages as they don't have a direct equivalent in OpenAI
        
        return result
    
    def _convert_openai_response_to_a2a(
        self, 
        response: Any, 
        parent_id: Optional[str] = None,
        conversation_id: Optional[str] = None
    ) -> Message:
        """
        Convert OpenAI response to A2A format
        
        Args:
            response: OpenAI API response
            parent_id: ID of the parent message
            conversation_id: ID of the conversation
            
        Returns:
            A2A-formatted message
        """
        # Extract the completion
        choice = response.choices[0]
        content = choice.message.content
        
        # Create an A2A message
        return Message(
            content=TextContent(text=content),
            role=MessageRole.AGENT,
            message_id=str(uuid.uuid4()),
            parent_message_id=parent_id,
            conversation_id=conversation_id
        )