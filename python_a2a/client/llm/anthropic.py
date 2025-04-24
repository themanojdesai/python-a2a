"""
Anthropic client implementation for the A2A protocol.
"""

import uuid
import json
import re
from typing import List, Dict, Any, Optional, Union

try:
    import anthropic
except ImportError:
    anthropic = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, FunctionParameter
from ...models.conversation import Conversation
from ...models.agent import AgentCard, AgentSkill
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
        
        # Create model name for display
        model_display_name = model.replace("-", " ").title()
        # Extract version from model ID if present
        model_version = re.search(r"[0-9]{8}", model)
        if model_version:
            version_date = model_version.group(0)
            # Format as YYYY-MM-DD
            formatted_date = f"{version_date[:4]}-{version_date[4:6]}-{version_date[6:8]}"
            version = f"{model.split('-')[0].title()} {formatted_date}"
        else:
            version = "1.0.0"
        
        # Create a default agent card
        self.agent_card = AgentCard(
            name=f"Claude {model_display_name}",
            description=f"Anthropic's {model_display_name} model accessible via A2A",
            url="https://api.anthropic.com",
            version=version,
            capabilities={
                "streaming": True,
                "pushNotifications": False,
                "stateTransitionHistory": False
            },
            skills=[
                AgentSkill(
                    name="Text Generation",
                    description=f"Generate text using the Claude {model_display_name} model",
                    tags=["anthropic", "claude", "language-model", "text-generation"]
                ),
                AgentSkill(
                    name="Reasoning",
                    description="Perform complex reasoning tasks",
                    tags=["anthropic", "claude", "reasoning"]
                ),
                AgentSkill(
                    name="Tool Use",
                    description="Use tools through structured responses",
                    tags=["anthropic", "claude", "tool-use"]
                )
            ]
        )
        
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
            
            # Extract text from response
            text_content = ""
            for content_item in response.content:
                if content_item.type == "text":
                    text_content += content_item.text
            
            # Check if the text appears to be a function/tool call
            tool_call = self._extract_tool_call_from_text(text_content)
            if tool_call:
                # Create a function call message
                return Message(
                    content=FunctionCallContent(
                        name=tool_call["name"],
                        parameters=tool_call["parameters"]
                    ),
                    role=MessageRole.AGENT,
                    message_id=str(uuid.uuid4()),
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            # Convert response back to A2A format
            return Message(
                content=TextContent(text=text_content),
                role=MessageRole.AGENT,
                message_id=str(uuid.uuid4()),
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with Anthropic: {str(e)}")
    
    def _extract_tool_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract tool/function call information from text response
        
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
            name_match = re.search(r'<name>(.*?)</name>', tool_content, re.DOTALL)
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
            
            # Extract text from response
            text_content = ""
            for content_item in response.content:
                if content_item.type == "text":
                    text_content += content_item.text
            
            # Check if the text appears to be a function/tool call
            tool_call = self._extract_tool_call_from_text(text_content)
            if tool_call:
                # Create a function call message
                a2a_response = Message(
                    content=FunctionCallContent(
                        name=tool_call["name"],
                        parameters=tool_call["parameters"]
                    ),
                    role=MessageRole.AGENT,
                    message_id=str(uuid.uuid4()),
                    parent_message_id=parent_id,
                    conversation_id=conversation.conversation_id
                )
            else:
                # Convert response to A2A format
                a2a_response = Message(
                    content=TextContent(text=text_content),
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
    
    def ask(self, message_text):
        """
        Simple helper for text-based queries
        
        Args:
            message_text: Text message to send
            
        Returns:
            Text response from the agent
        """
        # Check if message is already a Message object
        if isinstance(message_text, str):
            message = Message(
                content=TextContent(text=message_text),
                role=MessageRole.USER
            )
        else:
            message = message_text
        
        # Send message
        response = self.send_message(message)
        
        # Extract text from response
        if response and hasattr(response, "content"):
            if hasattr(response.content, "text"):
                return response.content.text
            elif hasattr(response.content, "message"):
                return response.content.message
            elif response.content is not None:
                return str(response.content)
        
        return "No text response"