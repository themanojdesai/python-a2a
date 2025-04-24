"""
OpenAI-based client implementation for the A2A protocol.
"""

import json
from typing import Optional, Dict, Any, List, Union

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
    """A2A client that uses OpenAI's API to process messages."""
    
    def __init__(
        self,
        api_key: str,
        model: str = "gpt-3.5-turbo",
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        functions: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize the OpenAI A2A client
        
        Args:
            api_key: OpenAI API key
            model: OpenAI model to use (default: "gpt-3.5-turbo")
            temperature: Generation temperature (default: 0.7)
            system_prompt: Optional system prompt for all conversations
            functions: Optional list of function definitions for function calling
        
        Raises:
            A2AImportError: If the openai package is not installed
        """
        if OpenAI is None:
            raise A2AImportError(
                "OpenAI package is not installed. "
                "Install it with 'pip install openai'"
            )
        
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.functions = functions
        self.tools = self._convert_functions_to_tools() if functions else None
        
        # Initialize OpenAI client
        self.client = OpenAI(api_key=api_key)
        
        # Store message history for conversations
        self._conversation_histories = {}
    
    def _convert_functions_to_tools(self):
        """Convert functions to the tools format used by newer OpenAI models"""
        if not self.functions:
            return None
            
        tools = []
        for func in self.functions:
            tools.append({
                "type": "function",
                "function": func
            })
        return tools
    
    def send_message(self, message: Message) -> Message:
        """
        Send a message to OpenAI's API and return the response as an A2A message
        
        Args:
            message: The A2A message to send
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to OpenAI fails
        """
        try:
            # Create OpenAI message format
            openai_messages = [{"role": "system", "content": self.system_prompt}]
            
            # If this is part of a conversation, retrieve history
            conversation_id = message.conversation_id
            if conversation_id and conversation_id in self._conversation_histories:
                openai_messages = self._conversation_histories[conversation_id].copy()
            
            # Add the current message
            if message.content.type == "text":
                openai_messages.append({
                    "role": "user" if message.role == MessageRole.USER else "assistant",
                    "content": message.content.text
                })
            elif message.content.type == "function_call":
                # Convert function call to string representation
                params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
                text = f"Call function {message.content.name}({params_str})"
                openai_messages.append({"role": "user", "content": text})
            elif message.content.type == "function_response":
                # Format function response in OpenAI's expected format
                openai_messages.append({
                    "role": "function",
                    "name": message.content.name,
                    "content": json.dumps(message.content.response)
                })
            elif message.content.type == "error":
                # Convert error to text
                openai_messages.append({
                    "role": "user", 
                    "content": f"Error: {message.content.message}"
                })
            else:
                # Default case for unknown content types
                openai_messages.append({
                    "role": "user", 
                    "content": str(message.content)
                })
            
            # Prepare API call parameters
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
            }
            
            # Add functions or tools if provided
            if self.tools:
                # Newer models use tools
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"
            elif self.functions:
                # Older models use functions
                kwargs["functions"] = self.functions
                kwargs["function_call"] = "auto"
            
            # Call OpenAI API
            response = self.client.chat.completions.create(**kwargs)
            
            # Parse response
            choice = response.choices[0]
            response_message = choice.message
            
            # Update conversation history if we have a conversation ID
            if conversation_id:
                if conversation_id not in self._conversation_histories:
                    # Initialize with system prompt
                    self._conversation_histories[conversation_id] = [
                        {"role": "system", "content": self.system_prompt}
                    ]
                
                # Add the user message to history
                if message.content.type == "text":
                    self._conversation_histories[conversation_id].append({
                        "role": "user" if message.role == MessageRole.USER else "assistant",
                        "content": message.content.text
                    })
                elif message.content.type == "function_response":
                    self._conversation_histories[conversation_id].append({
                        "role": "function",
                        "name": message.content.name,
                        "content": json.dumps(message.content.response)
                    })
                
                # Add the assistant's response to history
                if hasattr(response_message, "content") and response_message.content:
                    self._conversation_histories[conversation_id].append({
                        "role": "assistant",
                        "content": response_message.content
                    })
                elif hasattr(response_message, "function_call") and response_message.function_call:
                    # Add function call to history
                    self._conversation_histories[conversation_id].append({
                        "role": "assistant",
                        "function_call": {
                            "name": response_message.function_call.name,
                            "arguments": response_message.function_call.arguments
                        }
                    })
            
            # Convert to A2A message format
            if hasattr(response_message, "function_call") and response_message.function_call:
                # Handle function call response
                function_call = response_message.function_call
                
                try:
                    # Parse arguments as JSON
                    args = json.loads(function_call.arguments)
                    parameters = [
                        FunctionParameter(name=name, value=value)
                        for name, value in args.items()
                    ]
                except:
                    # Fallback for non-JSON arguments
                    parameters = [
                        FunctionParameter(name="arguments", value=function_call.arguments)
                    ]
                
                # Create function call message
                return Message(
                    content=FunctionCallContent(
                        name=function_call.name,
                        parameters=parameters
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            # Handle tool calls in newer models
            tool_calls = getattr(response_message, "tool_calls", None)
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.type == "function":
                        try:
                            # Parse arguments as JSON
                            args = json.loads(tool_call.function.arguments)
                            parameters = [
                                FunctionParameter(name=name, value=value)
                                for name, value in args.items()
                            ]
                        except:
                            # Fallback for non-JSON arguments
                            parameters = [
                                FunctionParameter(name="arguments", value=tool_call.function.arguments)
                            ]
                        
                        # Create function call message
                        return Message(
                            content=FunctionCallContent(
                                name=tool_call.function.name,
                                parameters=parameters
                            ),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
            
            # Regular text response
            return Message(
                content=TextContent(text=response_message.content or ""),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
            
        except Exception as e:
            # Create error message
            return Message(
                content=TextContent(text=f"Error from OpenAI API: {str(e)}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a full conversation to OpenAI's API and get an updated conversation
        
        Args:
            conversation: The A2A conversation to send
            
        Returns:
            The updated conversation with the response
            
        Raises:
            A2AConnectionError: If connection to OpenAI fails
        """
        if not conversation.messages:
            # Empty conversation, return as is
            return conversation
        
        try:
            # Initialize OpenAI message format with system prompt
            openai_messages = [{"role": "system", "content": self.system_prompt}]
            
            # Add all messages from the conversation
            for msg in conversation.messages:
                if msg.content.type == "text":
                    openai_messages.append({
                        "role": "user" if msg.role == MessageRole.USER else "assistant",
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Convert function call to string
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    
                    role = "user" if msg.role == MessageRole.USER else "assistant"
                    openai_messages.append({"role": role, "content": text})
                elif msg.content.type == "function_response":
                    # Format function response for OpenAI
                    openai_messages.append({
                        "role": "function",
                        "name": msg.content.name,
                        "content": json.dumps(msg.content.response)
                    })
            
            # Get conversation ID for tracking history
            conversation_id = conversation.conversation_id
            
            # Store the conversation in history
            if conversation_id:
                self._conversation_histories[conversation_id] = openai_messages.copy()
            
            # Prepare API call parameters
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
            }
            
            # Add functions or tools if provided
            if self.tools:
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"
            elif self.functions:
                kwargs["functions"] = self.functions
                kwargs["function_call"] = "auto"
            
            # Call OpenAI API
            response = self.client.chat.completions.create(**kwargs)
            
            # Parse response
            choice = response.choices[0]
            response_message = choice.message
            
            # Add to conversation history
            if conversation_id and hasattr(response_message, "content") and response_message.content:
                self._conversation_histories[conversation_id].append({
                    "role": "assistant",
                    "content": response_message.content
                })
            
            # Get the last message in the conversation as parent
            last_message = conversation.messages[-1]
            
            # Create a new message based on the response
            if hasattr(response_message, "function_call") and response_message.function_call:
                function_call = response_message.function_call
                
                # Parse arguments as JSON
                try:
                    args = json.loads(function_call.arguments)
                    parameters = [
                        FunctionParameter(name=name, value=value)
                        for name, value in args.items()
                    ]
                except:
                    # Fallback for non-JSON arguments
                    parameters = [
                        FunctionParameter(name="arguments", value=function_call.arguments)
                    ]
                
                # Add function call message to conversation
                a2a_message = Message(
                    content=FunctionCallContent(
                        name=function_call.name,
                        parameters=parameters
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=last_message.message_id,
                    conversation_id=conversation_id
                )
                conversation.add_message(a2a_message)
                
            elif hasattr(response_message, "tool_calls") and response_message.tool_calls:
                # Handle tool calls
                tool_call = response_message.tool_calls[0]
                if tool_call.type == "function":
                    try:
                        # Parse arguments as JSON
                        args = json.loads(tool_call.function.arguments)
                        parameters = [
                            FunctionParameter(name=name, value=value)
                            for name, value in args.items()
                        ]
                    except:
                        # Fallback for non-JSON arguments
                        parameters = [
                            FunctionParameter(name="arguments", value=tool_call.function.arguments)
                        ]
                    
                    # Add function call message to conversation
                    a2a_message = Message(
                        content=FunctionCallContent(
                            name=tool_call.function.name,
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=last_message.message_id,
                        conversation_id=conversation_id
                    )
                    conversation.add_message(a2a_message)
            else:
                # Regular text response
                a2a_message = Message(
                    content=TextContent(text=response_message.content or ""),
                    role=MessageRole.AGENT,
                    parent_message_id=last_message.message_id,
                    conversation_id=conversation_id
                )
                conversation.add_message(a2a_message)
            
            return conversation
            
        except Exception as e:
            # Add error message to conversation
            error_msg = f"Error from OpenAI API: {str(e)}"
            
            # Use the last message as parent if available
            parent_id = conversation.messages[-1].message_id if conversation.messages else None
            
            conversation.create_error_message(error_msg, parent_message_id=parent_id)
            return conversation
    
    def ask(self, query: str) -> str:
        """
        Simple helper for text-based queries
        
        Args:
            query: Text query to send
            
        Returns:
            Text response from the model
        """
        # Create message
        message = Message(
            content=TextContent(text=query),
            role=MessageRole.USER
        )
        
        # Send message and get response
        response = self.send_message(message)
        
        # Extract text from response
        if response.content.type == "text":
            return response.content.text
        elif response.content.type == "function_call":
            # Format function call as text
            params_str = ", ".join([f"{p.name}={p.value}" for p in response.content.parameters])
            return f"Function call: {response.content.name}({params_str})"
        else:
            # Default case for other content types
            return str(response.content)
    
    def clear_conversation_history(self, conversation_id: str = None):
        """
        Clear conversation history for a specific conversation or all conversations
        
        Args:
            conversation_id: ID of conversation to clear, or None to clear all
        """
        if conversation_id:
            if conversation_id in self._conversation_histories:
                # Reset to just the system prompt
                self._conversation_histories[conversation_id] = [
                    {"role": "system", "content": self.system_prompt}
                ]
        else:
            # Clear all conversation histories
            self._conversation_histories = {}