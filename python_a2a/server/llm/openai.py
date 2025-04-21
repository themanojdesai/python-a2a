"""
OpenAI-based server implementation for the A2A protocol.
"""

import uuid
from typing import Optional, Dict, Any, List, Union, Mapping
import httpx

try:
    from openai import OpenAI, DEFAULT_MAX_RETRIES
    from openai._types import (
        NOT_GIVEN,
        Omit,
        Timeout,
        NotGiven,
        Transport,
        ProxiesTypes,
        RequestOptions,
    )
except ImportError:
    OpenAI = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent
from ...models.conversation import Conversation
from ..base import BaseA2AServer
from ...exceptions import A2AImportError, A2AConnectionError


class OpenAIA2AServer(BaseA2AServer):
    """
    An A2A server that uses OpenAI's API to process messages.
    
    This server converts incoming A2A messages to OpenAI's format, processes them
    using OpenAI's API, and converts the responses back to A2A format.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-4",
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        base_url: str | httpx.URL | None = None,
        timeout: Union[float, Timeout, None, NotGiven] = NOT_GIVEN,
        max_retries: int = DEFAULT_MAX_RETRIES,
        default_headers: Mapping[str, str] | None = None,
        http_client: httpx.Client | None = None,
    ):
        """
        Initialize the OpenAI A2A server
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (default: "gpt-4")
            temperature: Generation temperature (default: 0.7)
            system_prompt: Optional system prompt to use for all conversations
            functions: Optional list of function definitions for function calling
        
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
        self.system_prompt = system_prompt or "You are a helpful AI assistant."
        self.functions = functions
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout, max_retries=max_retries,
                             default_headers=default_headers, http_client=http_client)
    
    def handle_message(self, message: Message) -> Message:
        """
        Process an incoming A2A message using OpenAI's API
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to OpenAI fails
        """
        try:
            # Prepare the OpenAI messages
            openai_messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add the user message
            if message.content.type == "text":
                openai_messages.append({
                    "role": "user" if message.role == MessageRole.USER else "assistant",
                    "content": message.content.text
                })
            elif message.content.type == "function_call":
                # Format function call as text for OpenAI
                params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
                text = f"Call function {message.content.name}({params_str})"
                openai_messages.append({"role": "user", "content": text})
            else:
                # Handle other message types or errors
                text = f"Message of type {message.content.type}"
                if hasattr(message.content, "message"):
                    text = message.content.message
                openai_messages.append({"role": "user", "content": text})
            
            # Call OpenAI API
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
            }
            
            # Add functions if provided
            if self.functions:
                kwargs["functions"] = self.functions
                kwargs["function_call"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Process the response
            choice = response.choices[0]
            message_obj = choice.message
            
            # Check if it's a function call or a regular message
            if hasattr(message_obj, "function_call") and message_obj.function_call:
                # Convert function call to A2A format
                function_call = message_obj.function_call
                try:
                    # Parse arguments as JSON
                    import json
                    args = json.loads(function_call.arguments)
                    parameters = [
                        {"name": name, "value": value}
                        for name, value in args.items()
                    ]
                except:
                    # Fallback: parse arguments as simple string
                    parameters = [{"name": "arguments", "value": function_call.arguments}]
                
                return Message(
                    content=FunctionCallContent(
                        name=function_call.name,
                        parameters=parameters
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            else:
                # Regular text response
                return Message(
                    content=TextContent(text=message_obj.content),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with OpenAI: {str(e)}")
    
    def handle_conversation(self, conversation: Conversation) -> Conversation:
        """
        Process an incoming A2A conversation using OpenAI's API
        
        This method overrides the default implementation to send the entire
        conversation history to OpenAI instead of just the last message.
        
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
            # Prepare the OpenAI messages
            openai_messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add all messages from the conversation
            for msg in conversation.messages:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                
                if msg.content.type == "text":
                    openai_messages.append({
                        "role": role,
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Format function call as text
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    openai_messages.append({"role": role, "content": text})
                elif msg.content.type == "function_response":
                    # Format function response as text
                    text = f"Function {msg.content.name} returned: {msg.content.response}"
                    openai_messages.append({"role": role, "content": text})
                else:
                    # Handle other message types or errors
                    text = f"Message of type {msg.content.type}"
                    if hasattr(msg.content, "message"):
                        text = msg.content.message
                    openai_messages.append({"role": role, "content": text})
            
            # Call OpenAI API
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
            }
            
            # Add functions if provided
            if self.functions:
                kwargs["functions"] = self.functions
                kwargs["function_call"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Process the response
            choice = response.choices[0]
            message_obj = choice.message
            
            # Get the last message ID to use as parent
            parent_id = conversation.messages[-1].message_id
            
            # Check if it's a function call or a regular message
            if hasattr(message_obj, "function_call") and message_obj.function_call:
                # Convert function call to A2A format
                function_call = message_obj.function_call
                try:
                    # Parse arguments as JSON
                    import json
                    args = json.loads(function_call.arguments)
                    parameters = [
                        {"name": name, "value": value}
                        for name, value in args.items()
                    ]
                except:
                    # Fallback: parse arguments as simple string
                    parameters = [{"name": "arguments", "value": function_call.arguments}]
                
                a2a_response = Message(
                    content=FunctionCallContent(
                        name=function_call.name,
                        parameters=parameters
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=parent_id,
                    conversation_id=conversation.conversation_id
                )
            else:
                # Regular text response
                a2a_response = Message(
                    content=TextContent(text=message_obj.content),
                    role=MessageRole.AGENT,
                    parent_message_id=parent_id,
                    conversation_id=conversation.conversation_id
                )
            
            # Add the response to the conversation
            conversation.add_message(a2a_response)
            return conversation
        
        except Exception as e:
            # Add an error message to the conversation
            error_msg = f"Failed to communicate with OpenAI: {str(e)}"
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
            "agent_type": "OpenAIA2AServer",
            "model": self.model,
            "capabilities": ["text"]
        })
        
        if self.functions:
            metadata["capabilities"].append("function_calling")
            metadata["functions"] = [f["name"] for f in self.functions]
        
        return metadata