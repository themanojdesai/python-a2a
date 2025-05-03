"""
OpenAI-based server implementation for the A2A protocol.
"""

import uuid
import json
import asyncio
from typing import Optional, Dict, Any, List, Union, AsyncGenerator

try:
    from openai import OpenAI
    from openai import AsyncOpenAI
except ImportError:
    OpenAI = None
    AsyncOpenAI = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent
from ...models.conversation import Conversation
from ...models.task import Task, TaskStatus, TaskState
from ..base import BaseA2AServer
from ...exceptions import A2AImportError, A2AConnectionError, A2AStreamingError


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
        functions: Optional[List[Dict[str, Any]]] = None
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
        self.tools = self._convert_functions_to_tools() if functions else None
        self.client = OpenAI(api_key=api_key)
        
        # Create an async client for streaming
        if AsyncOpenAI is not None:
            self.async_client = AsyncOpenAI(api_key=api_key)
        else:
            self.async_client = None
            
        # For tracking conversation state
        self._conversation_state = {}  # conversation_id -> list of messages
        
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
            conversation_id = message.conversation_id
            
            # If this is part of an existing conversation, retrieve history
            if conversation_id and conversation_id in self._conversation_state:
                # Use the existing conversation history
                openai_messages = self._conversation_state[conversation_id].copy()
            
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
            elif message.content.type == "function_response":
                # Format function response in OpenAI's expected format
                # This is critical for function calling to work properly
                openai_messages.append({
                    "role": "function",
                    "name": message.content.name,
                    "content": json.dumps(message.content.response)
                })
            else:
                # Handle other message types or errors
                text = f"Message of type {message.content.type}"
                if hasattr(message.content, "message"):
                    text = message.content.message
                openai_messages.append({"role": "user", "content": text})
            
            # Call OpenAI API with appropriate parameters
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
            }
            
            # Add tools or functions based on model and availability
            if self.tools:
                # Newer models use tools
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"
            elif self.functions:
                # Older models use functions
                kwargs["functions"] = self.functions
                kwargs["function_call"] = "auto"
            
            response = self.client.chat.completions.create(**kwargs)
            
            # Process the response
            choice = response.choices[0]
            response_message = choice.message
            
            # If we have a conversation ID, update the conversation state
            if conversation_id:
                if conversation_id not in self._conversation_state:
                    self._conversation_state[conversation_id] = [{"role": "system", "content": self.system_prompt}]
                
                # Add the original user message to state
                if message.content.type == "text":
                    self._conversation_state[conversation_id].append({
                        "role": "user" if message.role == MessageRole.USER else "assistant",
                        "content": message.content.text
                    })
                elif message.content.type == "function_response":
                    self._conversation_state[conversation_id].append({
                        "role": "function",
                        "name": message.content.name,
                        "content": json.dumps(message.content.response)
                    })
                
                # Add the assistant's response to state
                if hasattr(response_message, "content") and response_message.content:
                    self._conversation_state[conversation_id].append({
                        "role": "assistant",
                        "content": response_message.content
                    })
                
                # If it's a tool/function call, add that to state too
                tool_calls = getattr(response_message, "tool_calls", None)
                if tool_calls:
                    for tool_call in tool_calls:
                        if tool_call.type == "function":
                            self._conversation_state[conversation_id].append({
                                "role": "assistant",
                                "tool_calls": [
                                    {
                                        "id": tool_call.id,
                                        "type": "function",
                                        "function": {
                                            "name": tool_call.function.name,
                                            "arguments": tool_call.function.arguments
                                        }
                                    }
                                ]
                            })
                            break
                elif hasattr(response_message, "function_call") and response_message.function_call:
                    func_call = response_message.function_call
                    self._conversation_state[conversation_id].append({
                        "role": "assistant",
                        "function_call": {
                            "name": func_call.name,
                            "arguments": func_call.arguments
                        }
                    })
            
            # Convert the response to A2A format
            # Check for function calls via newer tool_calls interface first
            tool_calls = getattr(response_message, "tool_calls", None)
            if tool_calls:
                for tool_call in tool_calls:
                    if tool_call.type == "function":
                        # Process function call
                        try:
                            # Parse arguments as JSON
                            args = json.loads(tool_call.function.arguments)
                            parameters = [
                                {"name": name, "value": value}
                                for name, value in args.items()
                            ]
                        except:
                            # Fallback parsing for non-JSON arguments
                            parameters = [{"name": "arguments", "value": tool_call.function.arguments}]
                        
                        return Message(
                            content=FunctionCallContent(
                                name=tool_call.function.name,
                                parameters=parameters
                            ),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
            # Then check older function_call interface
            elif hasattr(response_message, "function_call") and response_message.function_call:
                function_call = response_message.function_call
                try:
                    # Parse arguments as JSON
                    args = json.loads(function_call.arguments)
                    parameters = [
                        {"name": name, "value": value}
                        for name, value in args.items()
                    ]
                except:
                    # Fallback parsing for non-JSON arguments
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
            
            # Regular text response
            return Message(
                content=TextContent(text=response_message.content or ""),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with OpenAI: {str(e)}")
    
    def handle_task(self, task: Task) -> Task:
        """
        Process an incoming A2A task using OpenAI's API
        
        Args:
            task: The incoming A2A task
            
        Returns:
            The updated task with the response
        """
        try:
            # Extract the message from the task
            message_data = task.message or {}
            
            # Convert to Message object if it's a dict
            if isinstance(message_data, dict):
                from ...models import Message
                message = Message.from_dict(message_data)
            else:
                message = message_data
                
            # Process the message
            response = self.handle_message(message)
            
            # Create artifact based on response content type
            if hasattr(response, "content"):
                content_type = getattr(response.content, "type", None)
                
                if content_type == "text":
                    # Handle TextContent
                    task.artifacts = [{
                        "parts": [{
                            "type": "text", 
                            "text": response.content.text
                        }]
                    }]
                elif content_type == "function_response":
                    # Handle FunctionResponseContent
                    task.artifacts = [{
                        "parts": [{
                            "type": "function_response",
                            "name": response.content.name,
                            "response": response.content.response
                        }]
                    }]
                elif content_type == "function_call":
                    # Handle FunctionCallContent
                    params = []
                    for param in response.content.parameters:
                        params.append({
                            "name": param.name,
                            "value": param.value
                        })
                    
                    task.artifacts = [{
                        "parts": [{
                            "type": "function_call",
                            "name": response.content.name,
                            "parameters": params
                        }]
                    }]
                elif content_type == "error":
                    # Handle ErrorContent
                    task.artifacts = [{
                        "parts": [{
                            "type": "error",
                            "message": response.content.message
                        }]
                    }]
                else:
                    # Handle other content types
                    task.artifacts = [{
                        "parts": [{
                            "type": "text", 
                            "text": str(response.content)
                        }]
                    }]
            else:
                # Handle responses without content
                task.artifacts = [{
                    "parts": [{
                        "type": "text", 
                        "text": str(response)
                    }]
                }]
            
            # Mark as completed
            task.status = TaskStatus(state=TaskState.COMPLETED)
            return task
        except Exception as e:
            # Handle errors
            task.artifacts = [{
                "parts": [{
                    "type": "error", 
                    "message": f"Error in OpenAI server: {str(e)}"
                }]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
            return task
    
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
            # Store conversation in state
            conversation_id = conversation.conversation_id
            self._conversation_state[conversation_id] = [{"role": "system", "content": self.system_prompt}]
            
            # Convert all messages to OpenAI format
            for msg in conversation.messages:
                if msg.content.type == "text":
                    self._conversation_state[conversation_id].append({
                        "role": "user" if msg.role == MessageRole.USER else "assistant",
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Format function call for OpenAI
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    self._conversation_state[conversation_id].append({
                        "role": "user" if msg.role == MessageRole.USER else "assistant", 
                        "content": text
                    })
                elif msg.content.type == "function_response":
                    # Format function response for OpenAI
                    self._conversation_state[conversation_id].append({
                        "role": "function",
                        "name": msg.content.name,
                        "content": json.dumps(msg.content.response)
                    })
            
            # Get the last message to process
            last_message = conversation.messages[-1]
            
            # Call the handle_message method to process the last message
            a2a_response = self.handle_message(last_message)
            
            # Add the response to the conversation
            conversation.add_message(a2a_response)
            return conversation
        
        except Exception as e:
            # Add an error message to the conversation
            error_msg = f"Failed to communicate with OpenAI: {str(e)}"
            conversation.create_error_message(error_msg, parent_message_id=conversation.messages[-1].message_id)
            return conversation
    
    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """
        Stream a response from OpenAI for the given message.
        
        Args:
            message: The A2A message to respond to
            
        Yields:
            Chunks of the response as they arrive
            
        Raises:
            A2AStreamingError: If streaming is not supported or fails
            A2AConnectionError: If connection to OpenAI fails
        """
        # Check if streaming is supported
        if self.async_client is None:
            raise A2AStreamingError(
                "AsyncOpenAI is not available. Ensure you have the latest "
                "openai package installed with 'pip install -U openai'."
            )
            
        try:
            # Extract message content
            query = ""
            if hasattr(message.content, "type") and message.content.type == "text":
                query = message.content.text
            elif hasattr(message.content, "text"):
                query = message.content.text
            
            # Prepare message history (similar logic to handle_message)
            openai_messages = [{"role": "system", "content": self.system_prompt}]
            conversation_id = message.conversation_id
            
            # If this is part of an existing conversation, retrieve history
            if conversation_id and conversation_id in self._conversation_state:
                # Use the existing conversation history
                openai_messages = self._conversation_state[conversation_id].copy()
            
            # Add the user message if not already in the history
            if not any(msg.get("role") == "user" and msg.get("content") == query 
                    for msg in openai_messages if "role" in msg and "content" in msg):
                openai_messages.append({
                    "role": "user" if message.role == MessageRole.USER else "assistant",
                    "content": query
                })
            
            # Prepare request arguments
            kwargs = {
                "model": self.model,
                "messages": openai_messages,
                "temperature": self.temperature,
                "stream": True  # Enable streaming
            }
            
            # Add tools or functions based on model and availability
            if self.tools:
                # Newer models use tools
                kwargs["tools"] = self.tools
                kwargs["tool_choice"] = "auto"
            elif self.functions:
                # Older models use functions
                kwargs["functions"] = self.functions
                kwargs["function_call"] = "auto"
            
            # Call OpenAI API with streaming
            async for chunk in await self.async_client.chat.completions.create(**kwargs):
                if hasattr(chunk.choices[0].delta, 'content') and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
                
                # Handle function/tool calls in streaming (if needed in the future)
                # This is a placeholder for future implementation
                # if hasattr(chunk.choices[0].delta, 'tool_calls') and chunk.choices[0].delta.tool_calls:
                #     # Process tool calls here if needed
                #     pass
            
            # Update conversation state after streaming is complete
            if conversation_id:
                if conversation_id not in self._conversation_state:
                    self._conversation_state[conversation_id] = [{"role": "system", "content": self.system_prompt}]
                
                # Add the user message
                if not any(msg.get("role") == "user" and msg.get("content") == query 
                        for msg in self._conversation_state[conversation_id] if "role" in msg and "content" in msg):
                    self._conversation_state[conversation_id].append({
                        "role": "user",
                        "content": query
                    })
                
                # Add the assistant's response (aggregate from streaming)
                # Future enhancement: This could be improved to capture the full streamed response
                self._conversation_state[conversation_id].append({
                    "role": "assistant",
                    "content": "[Streamed response]"  # Placeholder for now
                })
                
        except Exception as e:
            # Convert exceptions to A2A-specific exceptions
            if isinstance(e, A2AStreamingError):
                raise
            raise A2AConnectionError(f"Failed to stream from OpenAI: {str(e)}")
            
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
        })
        
        if self.functions:
            metadata["capabilities"].append("function_calling")
            metadata["functions"] = [f["name"] for f in self.functions]
        
        # Mark streaming capability based on AsyncOpenAI availability
        if self.async_client is not None:
            metadata["capabilities"].append("streaming")
        
        return metadata