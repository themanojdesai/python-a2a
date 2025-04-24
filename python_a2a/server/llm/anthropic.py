"""
Anthropic-based server implementation for the A2A protocol.
"""

import uuid
import json
import re
from typing import Optional, Dict, Any, List, Union

try:
    import anthropic
except ImportError:
    anthropic = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent, FunctionParameter
from ...models.conversation import Conversation
from ...models.task import Task, TaskStatus, TaskState
from ..base import BaseA2AServer
from ...exceptions import A2AImportError, A2AConnectionError


class AnthropicA2AServer(BaseA2AServer):
    """
    An A2A server that uses Anthropic's Claude API to process messages.
    
    This server converts incoming A2A messages to Anthropic's format, processes them
    using Anthropic's API, and converts the responses back to A2A format.
    """
    
    def __init__(
        self,
        api_key: str,
        model: str = "claude-3-opus-20240229",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize the Anthropic A2A server
        
        Args:
            api_key: Anthropic API key
            model: Anthropic model to use (default: "claude-3-opus-20240229")
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum number of tokens to generate (default: 1000)
            system_prompt: Optional system prompt to use for all conversations
            tools: Optional list of tool definitions for tool use
        
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
        self.tools = tools
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # For tracking conversation state
        self._conversation_state = {}  # conversation_id -> list of messages
    
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
            # Prepare the Anthropic messages
            anthropic_messages = []
            conversation_id = message.conversation_id
            
            # If this is part of an existing conversation, retrieve history
            if conversation_id and conversation_id in self._conversation_state:
                # Use the existing conversation history
                anthropic_messages = self._conversation_state[conversation_id].copy()
            
            # Add the incoming message
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
                # Format function response for Claude
                # Claude accepts tool output in this format
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.message_id or str(uuid.uuid4()),
                            "tool_name": message.content.name,
                            "content": json.dumps(message.content.response)
                        }
                    ]
                })
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
                
            # Add tools if provided
            if self.tools:
                kwargs["tools"] = self.tools
            
            # Call Anthropic API
            response = self.client.messages.create(**kwargs)
            
            # Extract text from response
            text_content = ""
            for content_item in response.content:
                if content_item.type == "text":
                    text_content += content_item.text
            
            # If we have a conversation ID, update the conversation state
            if conversation_id:
                if conversation_id not in self._conversation_state:
                    self._conversation_state[conversation_id] = []
                
                # Add the original message
                if message.content.type == "text":
                    msg_role = "user" if message.role == MessageRole.USER else "assistant"
                    self._conversation_state[conversation_id].append({
                        "role": msg_role,
                        "content": message.content.text
                    })
                elif message.content.type == "function_response":
                    self._conversation_state[conversation_id].append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message.message_id or str(uuid.uuid4()),
                                "tool_name": message.content.name,
                                "content": json.dumps(message.content.response)
                            }
                        ]
                    })
                
                # Add Claude's response
                assistant_msg = {"role": "assistant"}
                
                # Check for tool use in the response
                tool_use = None
                for content_item in response.content:
                    if content_item.type == "tool_use":
                        tool_use = content_item
                        break
                
                if tool_use:
                    assistant_msg["content"] = [
                        {
                            "type": "tool_use",
                            "id": tool_use.id,
                            "name": tool_use.name,
                            "input": tool_use.input
                        }
                    ]
                else:
                    assistant_msg["content"] = text_content
                
                self._conversation_state[conversation_id].append(assistant_msg)
            
            # Check if the response includes a tool call
            for content_item in response.content:
                if content_item.type == "tool_use":
                    try:
                        # Extract parameters from input
                        input_data = json.loads(content_item.input)
                        parameters = [
                            FunctionParameter(name=key, value=value)
                            for key, value in input_data.items()
                        ]
                    except (json.JSONDecodeError, TypeError):
                        # Handle non-JSON input
                        parameters = [FunctionParameter(name="input", value=content_item.input)]
                    
                    # Create a function call message
                    return Message(
                        content=FunctionCallContent(
                            name=content_item.name,
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
            
            # If no tool call, check for tool use in text content
            tool_call = self._extract_tool_call_from_text(text_content)
            if tool_call:
                return Message(
                    content=FunctionCallContent(
                        name=tool_call["name"],
                        parameters=tool_call["parameters"]
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            # Otherwise, return the text response
            return Message(
                content=TextContent(text=text_content),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with Anthropic: {str(e)}")
    
    def handle_task(self, task: Task) -> Task:
        """
        Process an incoming A2A task using Anthropic's API
        
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
                
            # Process the message using handle_message
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
                    "message": f"Error in Anthropic server: {str(e)}"
                }]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
            return task
    
    def _extract_tool_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract tool call information from Claude's text response
        
        Claude often formats tool calls in a structured way that can be parsed
        
        Args:
            text: Response text to analyze
            
        Returns:
            Dictionary with tool name and parameters or None if no tool call detected
        """
        # Look for tool use format with <tool></tool> tags
        tool_match = re.search(r'<tool>(.*?)</tool>', text, re.DOTALL)
        if tool_match:
            tool_content = tool_match.group(1)
            
            # Look for the name
            name_match = re.search(r'<n>(.*?)</n>', tool_content, re.DOTALL)
            if not name_match:
                return None
                
            tool_name = name_match.group(1).strip()
            
            # Look for parameters
            params = []
            input_match = re.search(r'<input>(.*?)</input>', tool_content, re.DOTALL)
            if input_match:
                try:
                    # Try to parse as JSON
                    input_json = json.loads(input_match.group(1).strip())
                    for key, value in input_json.items():
                        params.append(FunctionParameter(name=key, value=value))
                except json.JSONDecodeError:
                    # If not valid JSON, extract key-value pairs using regex
                    param_matches = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|[\d.]+|true|false|null|\{.*?\}|\[.*?\])', 
                                             input_match.group(1))
                    for key, value in param_matches:
                        # Process the value
                        if value.startswith('"') and value.endswith('"'):
                            # String value, remove quotes
                            value = value[1:-1]
                        elif value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        elif value.lower() == "null":
                            value = None
                        elif value.isdigit():
                            value = int(value)
                        elif re.match(r'^-?\d+(\.\d+)?$', value):
                            value = float(value)
                            
                        params.append(FunctionParameter(name=key, value=value))
            
            return {
                "name": tool_name,
                "parameters": params
            }
        
        # Alternative pattern: check for "I'll use the tool/function" format
        function_intent_match = re.search(r"I('ll| will) use the (tool|function) ['\"]([^'\"]+)['\"]", text)
        if function_intent_match:
            func_name = function_intent_match.group(3)
            
            # Look for parameters in a structured format
            params = []
            param_section = text.split(function_intent_match.group(0), 1)[1]
            
            # Look for JSON-like parameter section
            param_match = re.search(r'\{(.*?)\}', param_section, re.DOTALL)
            if param_match:
                try:
                    # Try to parse as JSON
                    param_json = json.loads("{" + param_match.group(1) + "}")
                    for key, value in param_json.items():
                        params.append(FunctionParameter(name=key, value=value))
                except json.JSONDecodeError:
                    # If not valid JSON, extract key-value pairs using regex
                    param_matches = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|[\d.]+|true|false|null)', 
                                             param_match.group(1))
                    for key, value in param_matches:
                        # Process the value
                        if value.startswith('"') and value.endswith('"'):
                            # String value, remove quotes
                            value = value[1:-1]
                        elif value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        elif value.lower() == "null":
                            value = None
                        elif value.isdigit():
                            value = int(value)
                        elif re.match(r'^-?\d+(\.\d+)?$', value):
                            value = float(value)
                            
                        params.append(FunctionParameter(name=key, value=value))
            
            # If no JSON-like section, look for parameter assignments
            if not params:
                param_matches = re.findall(r'([a-zA-Z0-9_]+)\s*=\s*([^,\n]+)', param_section)
                for key, value in param_matches:
                    # Process the value
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        # String value, remove quotes
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        # String value, remove quotes
                        value = value[1:-1]
                    elif value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.lower() == "none" or value.lower() == "null":
                        value = None
                    elif value.isdigit():
                        value = int(value)
                    elif re.match(r'^-?\d+(\.\d+)?$', value):
                        value = float(value)
                        
                    params.append(FunctionParameter(name=key, value=value))
            
            return {
                "name": func_name,
                "parameters": params
            }
        
        return None
    
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
            # Store conversation in state
            conversation_id = conversation.conversation_id
            self._conversation_state[conversation_id] = []
            
            # Convert each message to Anthropic's format and add to state
            for msg in conversation.messages:
                if msg.content.type == "text":
                    msg_role = "user" if msg.role == MessageRole.USER else "assistant"
                    self._conversation_state[conversation_id].append({
                        "role": msg_role,
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Format function call as text
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    
                    msg_role = "user" if msg.role == MessageRole.USER else "assistant"
                    self._conversation_state[conversation_id].append({
                        "role": msg_role,
                        "content": text
                    })
                elif msg.content.type == "function_response":
                    # Format function response as tool result
                    self._conversation_state[conversation_id].append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.message_id or str(uuid.uuid4()),
                                "tool_name": msg.content.name,
                                "content": json.dumps(msg.content.response)
                            }
                        ]
                    })
            
            # Use the handle_message method to process the last message
            last_message = conversation.messages[-1]
            a2a_response = self.handle_message(last_message)
            
            # Add the response to the conversation
            conversation.add_message(a2a_response)
            return conversation
            
        except Exception as e:
            # Add an error message to the conversation
            error_msg = f"Failed to communicate with Anthropic: {str(e)}"
            conversation.create_error_message(error_msg)
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
        if self.tools:
            metadata["capabilities"].append("tool_use")
            metadata["tools"] = [t["name"] for t in self.tools if "name" in t]
        return metadata