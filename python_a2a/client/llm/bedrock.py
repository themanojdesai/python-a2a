"""
AWS Bedrock-based client implementation for the A2A protocol.
"""

import json
import re
import uuid
from typing import Optional, Dict, Any, List, Union

try:
    import boto3
except ImportError:
    boto3 = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, FunctionParameter
from ...models.conversation import Conversation
from ..base import BaseA2AClient
from ...exceptions import A2AImportError, A2AConnectionError


class BedrockA2AClient(BaseA2AClient):
    """A2A client that uses AWS Bedrock's API to process messages."""
    
    def __init__(
        self, 
        aws_access_key_id: Optional[str] = None,
        aws_secret_access_key: Optional[str] = None,
        aws_region: str = "us-east-1",
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None
    ):
        """
        Initialize the AWS Bedrock A2A client
        
        Args:
            aws_access_key_id: AWS access key ID
            aws_secret_access_key: AWS secret access key
            aws_region: AWS region (default: "us-east-1")
            model_id: Bedrock model ID to use (default: "anthropic.claude-3-sonnet-20240229-v1:0")
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum tokens to generate (default: 1000)
            system_prompt: Optional system prompt for all conversations
            tools: Optional list of tool definitions for tool use
        
        Raises:
            A2AImportError: If the boto3 package is not installed
        """
        if boto3 is None:
            raise A2AImportError(
                "boto3 package is not installed. "
                "Install it with 'pip install boto3'"
            )
        
        # Store AWS credentials
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        self.aws_region = aws_region
        
        # Store model parameters
        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt or "You are a helpful assistant."
        self.tools = tools
        
        # Determine provider based on model ID
        if "anthropic" in model_id.lower():
            self.provider = "anthropic"
        elif "amazon" in model_id.lower():
            self.provider = "amazon"
        elif "ai21" in model_id.lower():
            self.provider = "ai21"
        elif "cohere" in model_id.lower():
            self.provider = "cohere"
        else:
            self.provider = "unknown"
        
        try:
            # Initialize the Bedrock runtime client
            self.client = boto3.client(
                service_name='bedrock-runtime',
                region_name=aws_region,
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key
            )
        except Exception as e:
            raise A2AConnectionError(f"Failed to initialize Bedrock client: {str(e)}")
        
        # Store message history for conversations
        self._conversation_histories = {}
    
    def send_message(self, message: Message) -> Message:
        """
        Send a message to AWS Bedrock and return the response as an A2A message
        
        Args:
            message: The A2A message to send
            
        Returns:
            The response as an A2A message
        
        Raises:
            A2AConnectionError: If connection to AWS Bedrock fails
        """
        try:
            # Get conversation ID for tracking history
            conversation_id = message.conversation_id
            
            # Initialize or retrieve conversation history
            if conversation_id and conversation_id in self._conversation_histories:
                conversation_history = self._conversation_histories[conversation_id].copy()
            else:
                conversation_history = []
            
            # Create Bedrock-compatible message format
            bedrock_messages = list(conversation_history)
            
            # Add the current message
            if message.content.type == "text":
                bedrock_messages.append({
                    "role": "user" if message.role == MessageRole.USER else "assistant",
                    "content": message.content.text
                })
            elif message.content.type == "function_call":
                # Format function call as text
                params_str = ", ".join([f"{p.name}={p.value}" for p in message.content.parameters])
                bedrock_messages.append({
                    "role": "user" if message.role == MessageRole.USER else "assistant",
                    "content": f"Call function {message.content.name}({params_str})"
                })
            elif message.content.type == "function_response":
                # Format function response based on provider
                if self.provider == "anthropic":
                    # Claude-specific tool response format
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
                else:
                    # Generic format for other providers
                    bedrock_messages.append({
                        "role": "user",
                        "content": f"Function {message.content.name} returned: {json.dumps(message.content.response)}"
                    })
            else:
                # Handle other message types (like errors)
                text = f"Message of type {message.content.type}"
                if hasattr(message.content, "message"):
                    text = message.content.message
                bedrock_messages.append({
                    "role": "user",
                    "content": text
                })
            
            # Prepare request body based on model provider
            request_body = {}
            
            if self.provider == "anthropic":
                # Claude-specific format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": bedrock_messages
                }
                
                # Add system prompt if available
                if self.system_prompt:
                    request_body["system"] = self.system_prompt
                    
                # Add tools if available
                if self.tools:
                    request_body["tools"] = self.tools
            else:
                # Generic format for other providers (simplified)
                # Note: Each provider might need specific adjustments
                request_body = {
                    "inputText": "\n".join([
                        f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                        for msg in bedrock_messages
                    ]),
                    "textGenerationConfig": {
                        "maxTokenCount": self.max_tokens,
                        "temperature": self.temperature
                    }
                }
                
                # Add system prompt for models that support it
                if self.system_prompt:
                    request_body["systemPrompt"] = self.system_prompt
            
            # Convert to JSON string
            request_json = json.dumps(request_body)
            
            # Call Bedrock API
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=request_json
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            # Update conversation history
            if conversation_id:
                if conversation_id not in self._conversation_histories:
                    self._conversation_histories[conversation_id] = []
                
                # Add the current message to history
                if message.content.type == "text":
                    self._conversation_histories[conversation_id].append({
                        "role": "user" if message.role == MessageRole.USER else "assistant",
                        "content": message.content.text
                    })
                elif message.content.type == "function_response":
                    if self.provider == "anthropic":
                        self._conversation_histories[conversation_id].append({
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
                        self._conversation_histories[conversation_id].append({
                            "role": "user",
                            "content": f"Function {message.content.name} returned: {json.dumps(message.content.response)}"
                        })
            
            # Extract the response content based on model provider
            if self.provider == "anthropic":
                # Claude-specific response handling
                response_text = ""
                tool_call = None
                
                # Check if this is the new Claude response format
                if "content" in response_body and isinstance(response_body["content"], list):
                    for content_item in response_body["content"]:
                        if content_item.get("type") == "text":
                            response_text += content_item.get("text", "")
                        elif content_item.get("type") == "tool_use":
                            # Handle tool use
                            tool_call = content_item
                elif "completion" in response_body:
                    # Handle older Claude response format
                    response_text = response_body.get("completion", "")
                
                # Update conversation history
                if conversation_id:
                    if tool_call:
                        self._conversation_histories[conversation_id].append({
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": tool_call.get("id", str(uuid.uuid4())),
                                    "name": tool_call.get("name", ""),
                                    "input": tool_call.get("input", "")
                                }
                            ]
                        })
                    else:
                        self._conversation_histories[conversation_id].append({
                            "role": "assistant",
                            "content": response_text
                        })
                
                # Check if we have a tool call
                if tool_call:
                    try:
                        # Extract parameters from tool input
                        input_data = json.loads(tool_call.get("input", "{}"))
                        parameters = [
                            FunctionParameter(name=key, value=value)
                            for key, value in input_data.items()
                        ]
                    except (json.JSONDecodeError, TypeError):
                        # Handle non-JSON input
                        parameters = [FunctionParameter(name="input", value=tool_call.get("input", ""))]
                    
                    # Return function call message
                    return Message(
                        content=FunctionCallContent(
                            name=tool_call.get("name", ""),
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                # Check for tool call in text (for older Claude versions)
                parsed_tool_call = self._extract_tool_call_from_text(response_text)
                if parsed_tool_call:
                    return Message(
                        content=FunctionCallContent(
                            name=parsed_tool_call["name"],
                            parameters=parsed_tool_call["parameters"]
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                # Return text response
                return Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            else:
                # Generic handling for other providers
                response_text = ""
                
                # Try to extract text from different response formats
                if "results" in response_body and len(response_body["results"]) > 0:
                    response_text = response_body["results"][0].get("outputText", "")
                elif "generated_text" in response_body:
                    response_text = response_body["generated_text"]
                elif "generations" in response_body and len(response_body["generations"]) > 0:
                    response_text = response_body["generations"][0].get("text", "")
                elif "output" in response_body:
                    response_text = response_body["output"]
                else:
                    # Fallback to JSON string
                    response_text = json.dumps(response_body)
                
                # Update conversation history
                if conversation_id:
                    self._conversation_histories[conversation_id].append({
                        "role": "assistant",
                        "content": response_text
                    })
                
                # Return text response
                return Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
                
        except Exception as e:
            # Create error message
            return Message(
                content=TextContent(text=f"Error from AWS Bedrock: {str(e)}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a full conversation to AWS Bedrock and get an updated conversation
        
        Args:
            conversation: The A2A conversation to send
            
        Returns:
            The updated conversation with the response
            
        Raises:
            A2AConnectionError: If connection to AWS Bedrock fails
        """
        if not conversation.messages:
            # Empty conversation, return as is
            return conversation
        
        try:
            # Initialize Bedrock message format
            bedrock_messages = []
            
            # Add all messages from the conversation
            for msg in conversation.messages:
                if msg.content.type == "text":
                    bedrock_messages.append({
                        "role": "user" if msg.role == MessageRole.USER else "assistant",
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Convert function call to string
                    params_str = ", ".join([f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    
                    role = "user" if msg.role == MessageRole.USER else "assistant"
                    bedrock_messages.append({"role": role, "content": text})
                elif msg.content.type == "function_response":
                    # Format function response based on provider
                    if self.provider == "anthropic":
                        # Claude-specific tool response format
                        bedrock_messages.append({
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
                        # Generic format for other providers
                        bedrock_messages.append({
                            "role": "user",
                            "content": f"Function {msg.content.name} returned: {json.dumps(msg.content.response)}"
                        })
            
            # Get conversation ID for tracking history
            conversation_id = conversation.conversation_id
            
            # Store the conversation in history
            if conversation_id:
                self._conversation_histories[conversation_id] = bedrock_messages.copy()
            
            # Prepare request body based on model provider
            request_body = {}
            
            if self.provider == "anthropic":
                # Claude-specific format
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature,
                    "messages": bedrock_messages
                }
                
                # Add system prompt if available
                if self.system_prompt:
                    request_body["system"] = self.system_prompt
                    
                # Add tools if available
                if self.tools:
                    request_body["tools"] = self.tools
            else:
                # Generic format for other providers (simplified)
                request_body = {
                    "inputText": "\n".join([
                        f"{msg.get('role', 'user')}: {msg.get('content', '')}" 
                        for msg in bedrock_messages
                    ]),
                    "textGenerationConfig": {
                        "maxTokenCount": self.max_tokens,
                        "temperature": self.temperature
                    }
                }
                
                # Add system prompt for models that support it
                if self.system_prompt:
                    request_body["systemPrompt"] = self.system_prompt
            
            # Convert to JSON string
            request_json = json.dumps(request_body)
            
            # Call Bedrock API
            response = self.client.invoke_model(
                modelId=self.model_id,
                contentType="application/json",
                accept="application/json",
                body=request_json
            )
            
            # Parse the response
            response_body = json.loads(response['body'].read())
            
            # Get the last message in the conversation as parent
            last_message = conversation.messages[-1]
            
            # Process the response based on model provider
            if self.provider == "anthropic":
                # Claude-specific response handling
                response_text = ""
                tool_call = None
                
                # Check if this is the new Claude response format
                if "content" in response_body and isinstance(response_body["content"], list):
                    for content_item in response_body["content"]:
                        if content_item.get("type") == "text":
                            response_text += content_item.get("text", "")
                        elif content_item.get("type") == "tool_use":
                            # Handle tool use
                            tool_call = content_item
                elif "completion" in response_body:
                    # Handle older Claude response format
                    response_text = response_body.get("completion", "")
                
                # Update conversation history
                if conversation_id:
                    if tool_call:
                        self._conversation_histories[conversation_id].append({
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "id": tool_call.get("id", str(uuid.uuid4())),
                                    "name": tool_call.get("name", ""),
                                    "input": tool_call.get("input", "")
                                }
                            ]
                        })
                    else:
                        self._conversation_histories[conversation_id].append({
                            "role": "assistant",
                            "content": response_text
                        })
                
                # Check if we have a tool call
                if tool_call:
                    try:
                        # Extract parameters from tool input
                        input_data = json.loads(tool_call.get("input", "{}"))
                        parameters = [
                            FunctionParameter(name=key, value=value)
                            for key, value in input_data.items()
                        ]
                    except (json.JSONDecodeError, TypeError):
                        # Handle non-JSON input
                        parameters = [FunctionParameter(name="input", value=tool_call.get("input", ""))]
                    
                    # Add function call message to conversation
                    a2a_message = Message(
                        content=FunctionCallContent(
                            name=tool_call.get("name", ""),
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=last_message.message_id,
                        conversation_id=conversation_id
                    )
                    conversation.add_message(a2a_message)
                    return conversation
                
                # Check for tool call in text (for older Claude versions)
                parsed_tool_call = self._extract_tool_call_from_text(response_text)
                if parsed_tool_call:
                    a2a_message = Message(
                        content=FunctionCallContent(
                            name=parsed_tool_call["name"],
                            parameters=parsed_tool_call["parameters"]
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=last_message.message_id,
                        conversation_id=conversation_id
                    )
                    conversation.add_message(a2a_message)
                    return conversation
                
                # Add text response to conversation
                a2a_message = Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=last_message.message_id,
                    conversation_id=conversation_id
                )
                conversation.add_message(a2a_message)
                return conversation
            else:
                # Generic handling for other providers
                response_text = ""
                
                # Try to extract text from different response formats
                if "results" in response_body and len(response_body["results"]) > 0:
                    response_text = response_body["results"][0].get("outputText", "")
                elif "generated_text" in response_body:
                    response_text = response_body["generated_text"]
                elif "generations" in response_body and len(response_body["generations"]) > 0:
                    response_text = response_body["generations"][0].get("text", "")
                elif "output" in response_body:
                    response_text = response_body["output"]
                else:
                    # Fallback to JSON string
                    response_text = json.dumps(response_body)
                
                # Update conversation history
                if conversation_id:
                    self._conversation_histories[conversation_id].append({
                        "role": "assistant",
                        "content": response_text
                    })
                
                # Add text response to conversation
                a2a_message = Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=last_message.message_id,
                    conversation_id=conversation_id
                )
                conversation.add_message(a2a_message)
                return conversation
            
        except Exception as e:
            # Add error message to conversation
            error_msg = f"Error from AWS Bedrock: {str(e)}"
            
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
        
        AWS Bedrock Claude models often format tool calls in a structured way that can be parsed
        
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