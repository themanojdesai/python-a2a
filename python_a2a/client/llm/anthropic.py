"""
Anthropic-based client implementation for the A2A protocol.
"""

import json
import re
from typing import Optional, Dict, Any, List, Union

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
    """A2A client that uses Anthropic's Claude API to process messages."""
    
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
        Initialize the Anthropic A2A client
        
        Args:
            api_key: Anthropic API key
            model: Anthropic model to use (default: "claude-3-opus-20240229")
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 1000)
            system_prompt: Optional system prompt for all conversations
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
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.tools = tools
        
        # Initialize Anthropic client
        self.client = anthropic.Anthropic(api_key=api_key)
        
        # Store message history for conversations
        self._conversation_histories = {}
    
    def send_message(self, message: Message) -> Message:
        """
        Send a message to Anthropic's API and return the response as an A2A message
        
        Args:
            message: The A2A message to send
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to Anthropic fails
        """
        try:
            # Create Anthropic message format
            anthropic_messages = []
            
            # If this is part of a conversation, retrieve history
            conversation_id = message.conversation_id
            if conversation_id and conversation_id in self._conversation_histories:
                anthropic_messages = self._conversation_histories[conversation_id].copy()
            
            # Add the current message
            if message.content.type == "text":
                anthropic_messages.append({
                    "role": "user" if message.role == MessageRole.USER else "assistant",
                    "content": message.content.text
                })
            elif message.content.type == "function_call":
                # Convert function call to string representation
                params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
                text = f"Call function {message.content.name}({params_str})"
                anthropic_messages.append({"role": "user", "content": text})
            elif message.content.type == "function_response":
                # Format function response as tool result for Claude
                anthropic_messages.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": message.message_id or "tool_call_id",
                            "tool_name": message.content.name,
                            "content": json.dumps(message.content.response)
                        }
                    ]
                })
            elif message.content.type == "error":
                # Convert error to text
                anthropic_messages.append({
                    "role": "user", 
                    "content": f"Error: {message.content.message}"
                })
            else:
                # Default case for unknown content types
                anthropic_messages.append({
                    "role": "user", 
                    "content": str(message.content)
                })
            
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
            
            # Update conversation history if we have a conversation ID
            if conversation_id:
                if conversation_id not in self._conversation_histories:
                    # Initialize history
                    self._conversation_histories[conversation_id] = []
                
                # Add the user message to history
                if message.content.type == "text":
                    self._conversation_histories[conversation_id].append({
                        "role": "user" if message.role == MessageRole.USER else "assistant",
                        "content": message.content.text
                    })
                elif message.content.type == "function_response":
                    self._conversation_histories[conversation_id].append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": message.message_id or "tool_call_id",
                                "tool_name": message.content.name,
                                "content": json.dumps(message.content.response)
                            }
                        ]
                    })
            
            # Process the response
            # Check for tool use first
            for content_item in response.content:
                if content_item.type == "tool_use":
                    # It's a tool call
                    tool_use = content_item
                    
                    # Add to conversation history if tracking
                    if conversation_id:
                        self._conversation_histories[conversation_id].append({
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": tool_use.id,
                                    "name": tool_use.name,
                                    "input": tool_use.input
                                }
                            ]
                        })
                    
                    try:
                        # Parse input as JSON
                        input_data = json.loads(tool_use.input)
                        parameters = [
                            FunctionParameter(name=key, value=value)
                            for key, value in input_data.items()
                        ]
                    except (json.JSONDecodeError, TypeError):
                        # Fallback for non-JSON input
                        parameters = [
                            FunctionParameter(name="input", value=tool_use.input)
                        ]
                    
                    # Create function call message
                    return Message(
                        content=FunctionCallContent(
                            name=tool_use.name,
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
            
            # If no tool use, get text content
            text_content = ""
            for content_item in response.content:
                if content_item.type == "text":
                    text_content += content_item.text
            
            # Add to conversation history
            if conversation_id:
                self._conversation_histories[conversation_id].append({
                    "role": "assistant",
                    "content": text_content
                })
            
            # Check for tool use in the text content (for older Claude versions)
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
            
            # Standard text response
            return Message(
                content=TextContent(text=text_content),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
            
        except Exception as e:
            # Create error message
            return Message(
                content=TextContent(text=f"Error from Anthropic API: {str(e)}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a full conversation to Anthropic's API and get an updated conversation
        
        Args:
            conversation: The A2A conversation to send
            
        Returns:
            The updated conversation with the response
            
        Raises:
            A2AConnectionError: If connection to Anthropic fails
        """
        if not conversation.messages:
            # Empty conversation, return as is
            return conversation
        
        try:
            # Initialize Anthropic message format
            anthropic_messages = []
            
            # Add all messages from the conversation
            for msg in conversation.messages:
                if msg.content.type == "text":
                    anthropic_messages.append({
                        "role": "user" if msg.role == MessageRole.USER else "assistant",
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Convert function call to string
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    
                    role = "user" if msg.role == MessageRole.USER else "assistant"
                    anthropic_messages.append({"role": role, "content": text})
                elif msg.content.type == "function_response":
                    # Format function response as tool result for Claude
                    anthropic_messages.append({
                        "role": "user",
                        "content": [
                            {
                                "type": "tool_result",
                                "tool_use_id": msg.message_id or "tool_call_id",
                                "tool_name": msg.content.name,
                                "content": json.dumps(msg.content.response)
                            }
                        ]
                    })
            
            # Get conversation ID for tracking history
            conversation_id = conversation.conversation_id
            
            # Store the conversation in history
            if conversation_id:
                self._conversation_histories[conversation_id] = anthropic_messages.copy()
            
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
            
            # Get the last message in the conversation as parent
            last_message = conversation.messages[-1]
            
            # Process the response
            # Check for tool use first
            for content_item in response.content:
                if content_item.type == "tool_use":
                    # It's a tool call
                    tool_use = content_item
                    
                    # Add to conversation history if tracking
                    if conversation_id:
                        self._conversation_histories[conversation_id].append({
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": tool_use.id,
                                    "name": tool_use.name,
                                    "input": tool_use.input
                                }
                            ]
                        })
                    
                    try:
                        # Parse input as JSON
                        input_data = json.loads(tool_use.input)
                        parameters = [
                            FunctionParameter(name=key, value=value)
                            for key, value in input_data.items()
                        ]
                    except (json.JSONDecodeError, TypeError):
                        # Fallback for non-JSON input
                        parameters = [
                            FunctionParameter(name="input", value=tool_use.input)
                        ]
                    
                    # Add function call message to conversation
                    a2a_message = Message(
                        content=FunctionCallContent(
                            name=tool_use.name,
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=last_message.message_id,
                        conversation_id=conversation_id
                    )
                    conversation.add_message(a2a_message)
                    return conversation
            
            # If no tool use, get text content
            text_content = ""
            for content_item in response.content:
                if content_item.type == "text":
                    text_content += content_item.text
            
            # Add to conversation history
            if conversation_id:
                self._conversation_histories[conversation_id].append({
                    "role": "assistant",
                    "content": text_content
                })
            
            # Check for tool use in the text content (for older Claude versions)
            tool_call = self._extract_tool_call_from_text(text_content)
            if tool_call:
                a2a_message = Message(
                    content=FunctionCallContent(
                        name=tool_call["name"],
                        parameters=tool_call["parameters"]
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=last_message.message_id,
                    conversation_id=conversation_id
                )
                conversation.add_message(a2a_message)
                return conversation
            
            # Add text response to conversation
            a2a_message = Message(
                content=TextContent(text=text_content),
                role=MessageRole.AGENT,
                parent_message_id=last_message.message_id,
                conversation_id=conversation_id
            )
            conversation.add_message(a2a_message)
            
            return conversation
            
        except Exception as e:
            # Add error message to conversation
            error_msg = f"Error from Anthropic API: {str(e)}"
            
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
    
    def _extract_tool_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract tool call information from text response
        
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
                    # If not valid JSON, try to extract parameters as key-value pairs
                    param_matches = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|[\d.]+|true|false|null)', 
                                             input_match.group(1))
                    for key, value in param_matches:
                        # Process value based on type
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]  # Remove quotes
                        elif value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        elif value.lower() == "null":
                            value = None
                        elif value.replace('.', '', 1).isdigit():
                            value = float(value) if '.' in value else int(value)
                            
                        params.append(FunctionParameter(name=key, value=value))
            
            return {
                "name": tool_name,
                "parameters": params
            }
        
        # Alternative pattern: check for "I'll use the tool/function" format
        function_intent_match = re.search(r"I('ll| will) use the (tool|function) ['\"]([^'\"]+)['\"]", text)
        if function_intent_match:
            func_name = function_intent_match.group(3)
            
            # Look for parameters
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
                    # If not valid JSON, try to extract parameters manually
                    param_matches = re.findall(r'"([^"]+)"\s*:\s*("[^"]*"|[\d.]+|true|false|null)', 
                                             param_match.group(1))
                    for key, value in param_matches:
                        # Process value based on type
                        if value.startswith('"') and value.endswith('"'):
                            value = value[1:-1]  # Remove quotes
                        elif value.lower() == "true":
                            value = True
                        elif value.lower() == "false":
                            value = False
                        elif value.lower() == "null":
                            value = None
                        elif value.replace('.', '', 1).isdigit():
                            value = float(value) if '.' in value else int(value)
                            
                        params.append(FunctionParameter(name=key, value=value))
            
            # If no JSON-like section, look for parameter assignments
            if not params:
                param_matches = re.findall(r'([a-zA-Z0-9_]+)\s*=\s*([^,\n]+)', param_section)
                for key, value in param_matches:
                    # Process the value
                    value = value.strip()
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]  # Remove quotes
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]  # Remove quotes
                    elif value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.lower() in ("none", "null"):
                        value = None
                    elif value.replace('.', '', 1).isdigit():
                        value = float(value) if '.' in value else int(value)
                        
                    params.append(FunctionParameter(name=key, value=value))
            
            return {
                "name": func_name,
                "parameters": params
            }
        
        return None
    
    def clear_conversation_history(self, conversation_id: str = None):
        """
        Clear conversation history for a specific conversation or all conversations
        
        Args:
            conversation_id: ID of conversation to clear, or None to clear all
        """
        if conversation_id:
            if conversation_id in self._conversation_histories:
                # Reset history for the specific conversation
                self._conversation_histories[conversation_id] = []
        else:
            # Clear all conversation histories
            self._conversation_histories = {}