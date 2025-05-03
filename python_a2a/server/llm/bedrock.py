"""
AWS Bedrock-based server implementation for the A2A protocol.
"""

import json
import asyncio
import re
import uuid
from typing import Optional, Dict, Any, List, Union, AsyncGenerator
from pathlib import Path

try:
    import boto3
    import aioboto3
except ImportError:
    boto3 = None
    aioboto3 = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent, FunctionParameter
from ...models.conversation import Conversation
from ...models.task import Task, TaskStatus, TaskState
from ..base import BaseA2AServer
from ...exceptions import A2AImportError, A2AConnectionError, A2AStreamingError


class BedrockA2AServer(BaseA2AServer):
    """
    An A2A server that uses AWS Bedrock's API to process messages.

    This server converts incoming A2A messages to Bedrock's format, processes them
    using AWS Bedrock's API, and converts the responses back to A2A format.
    """

    def __init__(
        self,
        model_id: str = "anthropic.claude-v2",
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        functions: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize the AWS Bedrock A2A server

        Args:
            model_id: Bedrock model ID (default: "anthropic.claude-v2")
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_region: AWS region (default: "us-east-1")
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum number of tokens to generate (default: 1000)
            system_prompt: Optional system prompt to use for all conversations
            tools: Optional list of tool definitions for tool use
            functions: Optional list of function definitions for function calling
                       (alias for tools, for compatibility with OpenAI interface)

        Raises:
            A2AImportError: If the boto3 package is not installed
            A2AConnectionError: If AWS credentials cannot be loaded
        """
        if boto3 is None:
            raise A2AImportError(
                "boto3 package is not installed. "
                "Install it with 'pip install boto3'"
            )
            
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region

        # Verify credentials
        if not aws_access_key_id or not aws_secret_access_key:
            # Try to use credentials from environment or IAM role
            try:
                session = boto3.Session(region_name=aws_region)
                credentials = session.get_credentials()
                if not credentials:
                    raise ValueError("No AWS credentials found")
            except Exception as e:
                raise A2AConnectionError(
                    f"AWS credentials not found: {str(e)}. "
                    "Provide credentials or ensure IAM role is properly configured."
                )

        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Store tools/functions for function calling
        self.tools = tools
        self.functions = functions if functions is not None else tools
        
        # Store system prompt
        self.system_prompt = system_prompt
        
        # Initialize the Bedrock runtime client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
        
        # Initialize async client if available
        if aioboto3 is not None:
            self.async_session = aioboto3.Session(
                region_name=self.aws_region,
                aws_access_key_id=self.aws_access_key_id,
                aws_secret_access_key=self.aws_secret_access_key
            )
            self.async_client = None  # Will be created when needed
        else:
            self.async_session = None
            self.async_client = None
        
        # For tracking conversation state
        self._conversation_state = {}  # conversation_id -> list of messages
    
    def handle_message(self, message: Message) -> Message:
        """
        Process an incoming A2A message using AWS Bedrock's API
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to AWS Bedrock fails
        """
        try:
            conversation_id = message.conversation_id
            
            # Create a generic message list for different model providers
            bedrock_messages = []
            
            # If this is part of an existing conversation, retrieve history
            if conversation_id and conversation_id in self._conversation_state:
                # Use the existing conversation history
                bedrock_messages = self._conversation_state[conversation_id].copy()
            
            # Add the incoming message
            if message.content.type == "text":
                msg_role = "user" if message.role == MessageRole.USER else "assistant"
                bedrock_messages.append({
                    "role": msg_role,
                    "content": message.content.text
                })
            elif message.content.type == "function_call":
                # Format function call as text
                params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
                text = f"Call function {message.content.name}({params_str})"
                bedrock_messages.append({"role": "user", "content": text})
            elif message.content.type == "function_response":
                # Format function response based on model provider
                if "anthropic" in self.model_id.lower():
                    # For Claude models in Bedrock
                    bedrock_messages.append({
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
                elif "amazon" in self.model_id.lower():
                    # For Amazon Titan models
                    bedrock_messages.append({
                        "role": "user",
                        "content": f"Function {message.content.name} returned: {json.dumps(message.content.response)}"
                    })
                elif "ai21" in self.model_id.lower():
                    # For AI21 models
                    bedrock_messages.append({
                        "role": "user",
                        "content": f"Function {message.content.name} returned: {json.dumps(message.content.response)}"
                    })
                elif "cohere" in self.model_id.lower():
                    # For Cohere models
                    bedrock_messages.append({
                        "role": "user",
                        "content": f"Function {message.content.name} returned: {json.dumps(message.content.response)}"
                    })
                else:
                    # Generic fallback
                    bedrock_messages.append({
                        "role": "user",
                        "content": f"Function {message.content.name} returned: {json.dumps(message.content.response)}"
                    })
            else:
                # Handle other message types or errors
                text = f"Message of type {message.content.type}"
                if hasattr(message.content, "message"):
                    text = message.content.message
                bedrock_messages.append({"role": "user", "content": text})
            
            # Check if running on a Claude model
            is_claude = "anthropic" in self.model_id.lower()
            
            # Prepare the request body based on the model provider
            request_body = {}
            
            if is_claude:
                # For Anthropic Claude models in Bedrock
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "messages": bedrock_messages
                }
                
                # Add system prompt if available
                if self.system_prompt:
                    request_body["system"] = self.system_prompt
                
                # Add temperature if specified
                if self.temperature is not None:
                    request_body["temperature"] = self.temperature
                
                # Add tools if available
                if self.tools:
                    request_body["tools"] = self.tools
            else:
                # Generic format for other providers
                # Note: This is simplified and would need to be adapted for 
                # specific model providers like Amazon Titan, AI21, Cohere, etc.
                request_body = {
                    "inputText": "\n".join([
                        f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                        for msg in bedrock_messages
                    ]),
                    "textGenerationConfig": {
                        "maxTokenCount": self.max_tokens,
                        "temperature": self.temperature,
                    }
                }
                
                # Add system prompt for models that support it
                if self.system_prompt:
                    request_body["systemPrompt"] = self.system_prompt
            
            # Convert to JSON string
            request_json = json.dumps(request_body)
            
            # Call Bedrock synchronously
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=request_json
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            # If we have a conversation ID, update the conversation state
            if conversation_id:
                if conversation_id not in self._conversation_state:
                    self._conversation_state[conversation_id] = []
                
                # Add the incoming message to state
                if message.content.type == "text":
                    msg_role = "user" if message.role == MessageRole.USER else "assistant"
                    self._conversation_state[conversation_id].append({
                        "role": msg_role,
                        "content": message.content.text
                    })
                elif message.content.type == "function_response":
                    if is_claude:
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
                    else:
                        self._conversation_state[conversation_id].append({
                            "role": "user",
                            "content": f"Function {message.content.name} returned: {json.dumps(message.content.response)}"
                        })
            
            # Handle response based on model provider
            if is_claude:
                # For Claude models
                # Extract text content
                text_content = ""
                
                # Check if this is the new Claude response format
                if "content" in response_body and isinstance(response_body["content"], list):
                    for content_item in response_body["content"]:
                        if content_item.get("type") == "text":
                            text_content += content_item.get("text", "")
                        elif content_item.get("type") == "tool_use":
                            # Handle Claude tool use
                            tool_use = content_item
                            try:
                                # Parse tool input as JSON
                                input_data = json.loads(tool_use.get("input", "{}"))
                                parameters = [
                                    FunctionParameter(name=key, value=value)
                                    for key, value in input_data.items()
                                ]
                            except (json.JSONDecodeError, TypeError):
                                # Handle non-JSON input
                                parameters = [FunctionParameter(name="input", value=tool_use.get("input", ""))]
                            
                            # Add to conversation state if tracking
                            if conversation_id:
                                self._conversation_state[conversation_id].append({
                                    "role": "assistant",
                                    "content": [
                                        {
                                            "type": "tool_use",
                                            "id": tool_use.get("id", str(uuid.uuid4())),
                                            "name": tool_use.get("name", ""),
                                            "input": tool_use.get("input", "")
                                        }
                                    ]
                                })
                            
                            # Return function call
                            return Message(
                                content=FunctionCallContent(
                                    name=tool_use.get("name", ""),
                                    parameters=parameters
                                ),
                                role=MessageRole.AGENT,
                                parent_message_id=message.message_id,
                                conversation_id=message.conversation_id
                            )
                elif "completion" in response_body:
                    # Handle older Claude response format
                    text_content = response_body.get("completion", "")
                
                # Add to conversation state if tracking
                if conversation_id and text_content:
                    self._conversation_state[conversation_id].append({
                        "role": "assistant",
                        "content": text_content
                    })
                
                # Check if the text contains a function/tool call
                tool_call = self._extract_tool_call_from_text(text_content)
                if tool_call:
                    # Return function call
                    return Message(
                        content=FunctionCallContent(
                            name=tool_call["name"],
                            parameters=tool_call["parameters"]
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                # Return text response
                return Message(
                    content=TextContent(text=text_content),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            else:
                # Generic handling for other model providers
                # This would need to be customized for each model type
                output_text = ""
                
                # Try to extract text from different response formats
                if "results" in response_body and len(response_body["results"]) > 0:
                    output_text = response_body["results"][0].get("outputText", "")
                elif "generated_text" in response_body:
                    output_text = response_body["generated_text"]
                elif "generations" in response_body and len(response_body["generations"]) > 0:
                    output_text = response_body["generations"][0].get("text", "")
                elif "output" in response_body:
                    output_text = response_body["output"]
                else:
                    # Fallback to JSON string
                    output_text = json.dumps(response_body)
                
                # Add to conversation state if tracking
                if conversation_id:
                    self._conversation_state[conversation_id].append({
                        "role": "assistant",
                        "content": output_text
                    })
                
                # Return text response
                return Message(
                    content=TextContent(text=output_text),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with AWS Bedrock: {str(e)}")
    
    def handle_task(self, task: Task) -> Task:
        """
        Process an incoming A2A task using AWS Bedrock's API
        
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
                    "message": f"Error in Bedrock server: {str(e)}"
                }]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
            return task
    
    def _extract_tool_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Extract tool/function call information from Claude's text response
        
        Args:
            text: Text response to analyze
            
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
        Process an incoming A2A conversation using AWS Bedrock's API
        
        This method overrides the default implementation to send the entire
        conversation history to Bedrock instead of just the last message.
        
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
            
            # Check if running on a Claude model
            is_claude = "anthropic" in self.model_id.lower()
            
            # Convert each message to the appropriate format based on model provider
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
                    # Format function response based on model provider
                    if is_claude:
                        # For Claude models in Bedrock
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
                    else:
                        # For other models
                        self._conversation_state[conversation_id].append({
                            "role": "user",
                            "content": f"Function {msg.content.name} returned: {json.dumps(msg.content.response)}"
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
            error_msg = f"Failed to communicate with AWS Bedrock: {str(e)}"
            conversation.create_error_message(
                error_msg, parent_message_id=conversation.messages[-1].message_id)
            return conversation
    
    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """
        Stream a response from AWS Bedrock for the given message.
        
        Args:
            message: The A2A message to respond to
            
        Yields:
            Chunks of the response as they arrive
            
        Raises:
            A2AStreamingError: If streaming is not supported or fails
            A2AConnectionError: If connection to AWS Bedrock fails
        """
        # Check if streaming is supported
        if aioboto3 is None:
            raise A2AStreamingError(
                "aioboto3 is not available. Install it with 'pip install aioboto3'."
            )
        
        try:
            # Create async client if needed
            if self.async_client is None:
                self.async_client = self.async_session.client('bedrock-runtime')
            
            # Extract message content
            query = ""
            if hasattr(message.content, "type") and message.content.type == "text":
                query = message.content.text
            elif hasattr(message.content, "text"):
                query = message.content.text
            
            # Prepare messages based on model provider
            # Check if running on a Claude model
            is_claude = "anthropic" in self.model_id.lower()
            
            # Prepare message history
            bedrock_messages = []
            conversation_id = message.conversation_id
            
            # If this is part of an existing conversation, retrieve history
            if conversation_id and conversation_id in self._conversation_state:
                # Use the existing conversation history
                bedrock_messages = self._conversation_state[conversation_id].copy()
            
            # Add the user message if not already in the history
            if is_claude:
                msg_role = "user" if message.role == MessageRole.USER else "assistant"
                if not bedrock_messages or not any(msg.get("role") == msg_role and msg.get("content") == query 
                       for msg in bedrock_messages if isinstance(msg, dict) and "role" in msg and "content" in msg):
                    bedrock_messages.append({
                        "role": msg_role,
                        "content": query
                    })
            else:
                # For non-Claude models, prepare a simple concatenated message
                bedrock_messages.append({
                    "role": "user" if message.role == MessageRole.USER else "assistant",
                    "content": query
                })
            
            # Prepare request body based on the model provider
            if is_claude:
                # For Anthropic Claude models
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "messages": bedrock_messages,
                    "stream": True  # Enable streaming
                }
                
                # Add system prompt if available
                if self.system_prompt:
                    request_body["system"] = self.system_prompt
                
                # Add temperature if specified
                if self.temperature is not None:
                    request_body["temperature"] = self.temperature
                
                # Add tools if available
                if self.tools:
                    request_body["tools"] = self.tools
            else:
                # Generic format for other providers
                input_text = "\n".join([
                    f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                    for msg in bedrock_messages
                ])
                
                # Customize for specific providers
                if "amazon" in self.model_id.lower():
                    # For Amazon Titan models
                    request_body = {
                        "inputText": input_text,
                        "textGenerationConfig": {
                            "maxTokenCount": self.max_tokens,
                            "temperature": self.temperature,
                        }
                    }
                elif "ai21" in self.model_id.lower():
                    # For AI21 models
                    request_body = {
                        "prompt": input_text,
                        "maxTokens": self.max_tokens,
                        "temperature": self.temperature,
                    }
                elif "cohere" in self.model_id.lower():
                    # For Cohere models
                    request_body = {
                        "prompt": input_text,
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    }
                else:
                    # Default format - may not work for all models
                    request_body = {
                        "prompt": input_text,
                        "max_tokens": self.max_tokens,
                        "temperature": self.temperature,
                    }
                    
                # Add system prompt for models that support it
                if self.system_prompt:
                    request_body["systemPrompt"] = self.system_prompt
            
            # Convert to JSON string
            request_json = json.dumps(request_body)
            
            # Create streaming response
            async with self.async_client as client:
                response = await client.invoke_model_with_response_stream(
                    modelId=self.model_id,
                    contentType="application/json",
                    accept="application/json",
                    body=request_json
                )
                
                # Process the streaming response
                stream = response.get('body')
                
                if is_claude:
                    # Claude streaming response handling
                    async for event in stream:
                        chunk = event.get('chunk')
                        if not chunk:
                            continue
                        
                        # Parse chunk data
                        chunk_data = json.loads(chunk.get('bytes').decode('utf-8'))
                        
                        # Extract text content from various Claude response formats
                        if 'completion' in chunk_data:
                            # Claude v1/v2 format
                            yield chunk_data['completion']
                        elif 'type' in chunk_data and chunk_data['type'] == 'content_block_delta':
                            # Claude 3 format - content_block_delta
                            if chunk_data.get('delta', {}).get('type') == 'text':
                                yield chunk_data['delta']['text']
                        elif 'type' in chunk_data and chunk_data['type'] == 'message_delta':
                            # Claude 3 format - message_delta
                            if 'delta' in chunk_data and 'content' in chunk_data['delta']:
                                for content_item in chunk_data['delta']['content']:
                                    if content_item.get('type') == 'text':
                                        yield content_item.get('text', '')
                else:
                    # Generic streaming response handling
                    async for event in stream:
                        chunk = event.get('chunk')
                        if not chunk:
                            continue
                        
                        # Parse chunk data
                        chunk_data = json.loads(chunk.get('bytes').decode('utf-8'))
                        
                        # Different models have different response formats
                        if 'completion' in chunk_data:
                            yield chunk_data['completion']
                        elif 'outputText' in chunk_data:
                            yield chunk_data['outputText']
                        elif 'generated_text' in chunk_data:
                            yield chunk_data['generated_text']
                        elif 'text' in chunk_data:
                            yield chunk_data['text']
                        elif 'results' in chunk_data and len(chunk_data['results']) > 0:
                            output = chunk_data['results'][0].get('outputText', '')
                            yield output
                        elif 'generations' in chunk_data and len(chunk_data['generations']) > 0:
                            output = chunk_data['generations'][0].get('text', '')
                            yield output
            
            # Update conversation state after streaming is complete
            if conversation_id:
                if conversation_id not in self._conversation_state:
                    self._conversation_state[conversation_id] = []
                
                # Add the user message if not already there
                msg_role = "user" if message.role == MessageRole.USER else "assistant"
                if not any(msg.get("role") == msg_role and msg.get("content") == query 
                       for msg in self._conversation_state[conversation_id] if "role" in msg and "content" in msg):
                    self._conversation_state[conversation_id].append({
                        "role": msg_role,
                        "content": query
                    })
                
                # Add placeholder for the assistant's response
                self._conversation_state[conversation_id].append({
                    "role": "assistant",
                    "content": "[Streamed response]"  # Placeholder for now
                })
                
        except Exception as e:
            # Convert exceptions to A2A-specific exceptions
            if isinstance(e, A2AStreamingError):
                raise
            raise A2AConnectionError(f"Failed to stream from AWS Bedrock: {str(e)}")
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this agent server
        
        Returns:
            A dictionary of metadata about this agent
        """
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "BedrockA2AServer",
            "model": self.model_id,
        })
        
        if self.functions or self.tools:
            metadata["capabilities"].append("function_calling")
            if self.functions:
                metadata["functions"] = [f["name"] for f in self.functions if "name" in f]
            elif self.tools:
                metadata["tools"] = [t["name"] for t in self.tools if "name" in t]
        
        # Mark streaming capability based on aioboto3 availability
        if self.async_session is not None:
            metadata["capabilities"].append("streaming")
            
        return metadata