# """
# AWS Bedrock-based server implementation for the A2A protocol.
# """

# import json
# import asyncio
# from typing import Optional, Dict, Any, List
# from pathlib import Path
# from ...models.message import Message, MessageRole
# from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent, FunctionParameter
# try:
#     import boto3
# except ImportError:
#     boto3 = None

# from ...models.message import Message, MessageRole
# from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent
# from ...models.conversation import Conversation
# from ..base import BaseA2AServer
# from ...exceptions import A2AImportError, A2AConnectionError

# class BedrockA2AServer(BaseA2AServer):
#     """
#     An A2A server that uses AWS Bedrock's API to process messages.

#     This server converts incoming A2A messages to Bedrock's format, processes them
#     using AWS Bedrock's API, and converts the responses back to A2A format.
#     """

#     def __init__(
#         self,
#         model_id: str = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
#         aws_access_key_id = None,
#         aws_secret_access_key = None,
#         aws_region = None,
#         temperature: float = 0.7,
#         max_tokens: int = 1000,
#         system_prompt: Optional[str] = None,
#         tools: Optional[List[Dict[str, Any]]] = None,
#         functions: Optional[List[Dict[str, Any]]] = None,
#         env_path: Optional[str] = None
#     ):
#         """
#         Initialize the AWS Bedrock A2A server

#         Args:
#             model_id: Bedrock model ID (default: "anthropic.claude-3-sonnet-20240229-v1:0")
#             temperature: Generation temperature (default: 0.7)
#             max_tokens: Maximum number of tokens to generate (default: 1000)
#             system_prompt: Optional system prompt to use for all conversations
#             tools: Optional list of tool definitions for tool use
#             functions: Optional list of function definitions for function calling
#                        (alias for tools, for compatibility with OpenAI interface)
#             env_path: Optional path to .env file (default: searches in current directory)

#         Raises:
#             A2AImportError: If the boto3 package is not installed
#             A2AConnectionError: If AWS credentials cannot be loaded
#         """
#         if boto3 is None:
#             raise A2AImportError(
#                 "boto3 package is not installed. "
#                 "Install it with 'pip install boto3'"
#             )
            
#         self.aws_access_key_id = aws_access_key_id
#         self.aws_secret_access_key = aws_secret_access_key
#         self.aws_region = aws_region

#         # Verify credentials were loaded
#         if not self.aws_access_key_id or not self.aws_secret_access_key:
#             raise A2AConnectionError(
#                 "AWS credentials not found in environment variables. "
#                 "Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set in your .env file."
#             )

#         self.model_id = model_id
#         self.temperature = temperature
#         self.max_tokens = max_tokens
        
#         # Store functions for function calling emulation
#         self.functions = functions if functions is not None else tools
        
#         # Create an enhanced system prompt that includes function definitions
#         if self.functions and system_prompt:
#             self.system_prompt = self._create_function_enhanced_system_prompt(system_prompt)
#         else:
#             self.system_prompt = system_prompt

#         # Initialize the Bedrock runtime client
#         self.client = boto3.client(
#             service_name='bedrock-runtime',
#             region_name=self.aws_region,
#             aws_access_key_id=self.aws_access_key_id,
#             aws_secret_access_key=self.aws_secret_access_key
#         )
    
#     def _create_function_enhanced_system_prompt(self, original_prompt: str) -> str:
#         """
#         Enhances the system prompt with function definitions to emulate function calling

#         Args:
#             original_prompt: The original system prompt

#         Returns:
#             Enhanced system prompt with function definitions
#         """
#         # Create a description of available functions
#         functions_description = "\n\nYou have access to the following functions:\n\n"
        
#         for func in self.functions:
#             functions_description += f"Function: {func.get('name', '')}\n"
#             functions_description += f"Description: {func.get('description', '')}\n"
            
#             # Add parameters information
#             parameters = func.get('parameters', {})
#             if 'properties' in parameters:
#                 functions_description += "Parameters:\n"
#                 required_params = parameters.get('required', [])
#                 for param_name, param_info in parameters.get('properties', {}).items():
#                     required = "required" if param_name in required_params else "optional"
#                     functions_description += f"- {param_name} ({required}): {param_info.get('description', '')}\n"
            
#             functions_description += "\n"
        
#         # Add instructions on how to call functions
#         functions_description += "\nWhen you need to call a function, format your response as follows:\n"
#         functions_description += "I need to call a function to answer this. I'll use the function '{function_name}'.\n"
#         functions_description += "Function call: {function_name}({parameter1}={value1}, {parameter2}={value2}, ...)\n\n"
        
#         # Combine with original prompt
#         enhanced_prompt = original_prompt + functions_description
        
#         print(f"Enhanced system prompt: {enhanced_prompt}")
#         return enhanced_prompt

#     def _call_bedrock_sync(self, bedrock_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """
#         Make a synchronous call to AWS Bedrock API

#         Args:
#             bedrock_messages: List of messages in Bedrock format

#         Returns:
#             The response from Bedrock API

#         Raises:
#             A2AConnectionError: If connection to Bedrock fails
#         """
#         try:
#             # Determine model type - ARN or normal model ID
#             is_arn = self.model_id.startswith("arn:")

#             # Check if this is an Anthropic model
#             is_anthropic = "anthropic" in self.model_id.lower()

#             # Prepare request body
#             request_body = {}

#             if is_anthropic:
#                 # For inference profiles (ARN) and regular Claude models
#                 request_body = {
#                     "anthropic_version": "bedrock-2023-05-31",
#                     "max_tokens": self.max_tokens,
#                     "messages": bedrock_messages
#                 }

#                 # Add system prompt if available
#                 if self.system_prompt:
#                     request_body["system"] = self.system_prompt

#                 # Add temperature
#                 if self.temperature is not None:
#                     request_body["temperature"] = self.temperature
#             else:
#                 # Generic format for other providers
#                 request_body = {
#                     "inputText": "\n".join([msg.get("content", "") for msg in bedrock_messages]),
#                     "textGenerationConfig": {
#                         "maxTokenCount": self.max_tokens,
#                         "temperature": self.temperature,
#                     }
#                 }

#             # Log the entire request payload for debugging
#             print(f"Full request payload: {json.dumps(request_body, indent=2)}")

#             # Convert to JSON string
#             request_json = json.dumps(request_body)

#             # Call Bedrock synchronously
#             response = self.client.invoke_model(
#                 modelId=self.model_id,
#                 contentType="application/json",
#                 accept="application/json",
#                 body=request_json
#             )

#             # Parse the response
#             response_body = json.loads(response['body'].read())
#             return response_body

#         except Exception as e:
#             # Log details about the error and request for debugging
#             error_msg = f"Failed to communicate with AWS Bedrock: {str(e)}"
#             print(f"Error details: {error_msg}")
#             print(f"Model ID: {self.model_id}")
#             print(f"Request body: {request_body}")
#             raise A2AConnectionError(error_msg)

#     async def _call_bedrock(self, bedrock_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
#         """
#         Make an asynchronous call to AWS Bedrock API

#         Args:
#             bedrock_messages: List of messages in Bedrock format

#         Returns:
#             The response from Bedrock API

#         Raises:
#             A2AConnectionError: If connection to Bedrock fails
#         """
#         try:
#             # Create a coroutine to call the model
#             loop = asyncio.get_event_loop()
#             return await loop.run_in_executor(
#                 None,
#                 lambda: self._call_bedrock_sync(bedrock_messages)
#             )

#         except Exception as e:
#             raise A2AConnectionError(
#                 f"Failed to communicate with AWS Bedrock: {str(e)}")
    
#     def _parse_function_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
#         """
#         Parse a function call from text response

#         Args:
#             text: The text response from the model

#         Returns:
#             Dictionary with function name and parameters, or None if no function call is detected
#         """
#         # Look for common function call patterns
#         import re
        
#         # Print full text for debugging
#         print(f"Parsing function call from text: {text}")
        
#         # Pattern 1: Function call: function_name(param1=value1, param2=value2)
#         pattern1 = r"Function call: (\w+)\((.*?)\)"
#         match1 = re.search(pattern1, text)
        
#         # Pattern 2: I'll use the function 'function_name'
#         pattern2 = r"I'll use the function ['\"]([\w]+)['\"]"
#         match2 = re.search(pattern2, text)
        
#         # Pattern 3: Direct pattern function_name(param1=value1, param2=value2)
#         pattern3 = r"(\w+)\((.*?)\)"
#         match3 = re.search(pattern3, text)
        
#         function_name = None
#         parameters = []
        
#         # Try to extract function name
#         if match1:
#             function_name = match1.group(1)
#             params_str = match1.group(2)
            
#             # Parse parameters
#             if params_str:
#                 param_pairs = params_str.split(',')
#                 for pair in param_pairs:
#                     if '=' in pair:
#                         key, value = pair.split('=', 1)
#                         parameters.append({
#                             "name": key.strip(), 
#                             "value": value.strip().strip('"\'')
#                         })
        
#         elif match2:
#             function_name = match2.group(1)
            
#             # Look for parameters in Pattern 3
#             for m in re.finditer(pattern3, text):
#                 if m.group(1) == function_name:
#                     params_str = m.group(2)
#                     if params_str:
#                         param_pairs = params_str.split(',')
#                         for pair in param_pairs:
#                             if '=' in pair:
#                                 key, value = pair.split('=', 1)
#                                 parameters.append({
#                                     "name": key.strip(), 
#                                     "value": value.strip().strip('"\'')
#                                 })
#                     break
        
#         # If no match found with patterns 1 or 2, try pattern 3 directly
#         elif match3 and not function_name:
#             # Check if the function name is one of our defined functions
#             potential_name = match3.group(1)
            
#             # Check if this is a valid function name
#             is_valid = False
#             if self.functions:
#                 for func in self.functions:
#                     if func.get('name') == potential_name:
#                         is_valid = True
#                         break
            
#             if is_valid:
#                 function_name = potential_name
#                 params_str = match3.group(2)
                
#                 # Parse parameters
#                 if params_str:
#                     param_pairs = params_str.split(',')
#                     for pair in param_pairs:
#                         if '=' in pair:
#                             key, value = pair.split('=', 1)
#                             parameters.append({
#                                 "name": key.strip(), 
#                                 "value": value.strip().strip('"\'')
#                             })
        
#         # If a function name was found, return the result
#         if function_name:
#             print(f"Detected function call: {function_name}")
#             print(f"Parameters: {parameters}")
#             return {
#                 "name": function_name,
#                 "parameters": parameters
#             }
        
#         return None
    
#     def handle_message(self, message: Message) -> Message:
#         """
#         Process an incoming A2A message using AWS Bedrock's API
        
#         Args:
#             message: The incoming A2A message
            
#         Returns:
#             The response as an A2A message
        
#         Raises:
#             A2AConnectionError: If connection to AWS Bedrock fails
#         """
#         try:
#             # Create messages array for Bedrock
#             bedrock_messages = []
            
#             # Add the user message
#             if message.content.type == "text":
#                 msg_role = "user" if message.role == MessageRole.USER else "assistant"
#                 bedrock_messages.append({
#                     "role": msg_role,
#                     "content": message.content.text
#                 })
#             elif message.content.type == "function_call":
#                 # Format function call as text
#                 params_str = ", ".join(
#                     [f"{p.name}={p.value}" for p in message.content.parameters])
#                 text = f"Call function {message.content.name}({params_str})"
#                 bedrock_messages.append({"role": "user", "content": text})
#             elif message.content.type == "function_response":
#                 # Format function response as text
#                 text = f"Function {message.content.name} returned: {message.content.response}"
#                 bedrock_messages.append({"role": "user", "content": text})
#             else:
#                 # Handle other message types or errors
#                 text = f"Message of type {message.content.type}"
#                 if hasattr(message.content, "message"):
#                     text = message.content.message
#                 bedrock_messages.append({"role": "user", "content": text})
            
#             # Determine model type - ARN or normal model ID
#             is_arn = self.model_id.startswith("arn:")
            
#             # Check if this is an Anthropic model
#             is_anthropic = "anthropic" in self.model_id.lower()
            
#             # Prepare request body
#             request_body = {}
            
#             if is_anthropic:
#                 # For inference profiles (ARN) and regular Claude models
#                 request_body = {
#                     "anthropic_version": "bedrock-2023-05-31",
#                     "max_tokens": self.max_tokens,
#                     "messages": bedrock_messages
#                 }
                
#                 # Add system prompt if available
#                 if self.system_prompt:
#                     request_body["system"] = self.system_prompt
                
#                 # Add temperature
#                 if self.temperature is not None:
#                     request_body["temperature"] = self.temperature
#             else:
#                 # Generic format for other providers
#                 request_body = {
#                     "inputText": "\n".join([msg.get("content", "") for msg in bedrock_messages]),
#                     "textGenerationConfig": {
#                         "maxTokenCount": self.max_tokens,
#                         "temperature": self.temperature,
#                     }
#                 }
            
#             # Convert to JSON string
#             request_json = json.dumps(request_body)
            
#             # Call Bedrock synchronously
#             response = self.client.invoke_model(
#                 modelId=self.model_id,
#                 contentType="application/json",
#                 accept="application/json",
#                 body=request_json
#             )
            
#             # Parse the response
#             response_body = json.loads(response['body'].read())
            
#             # Process the response based on the model provider
#             if is_anthropic:
#                 # Extract text content
#                 content_items = response_body.get("content", [])
#                 response_text = ""
                
#                 for content in content_items:
#                     if content.get("type") == "text":
#                         response_text += content.get("text", "")
                
#                 # If we didn't get any text from content items but have a completion field
#                 if not response_text and "completion" in response_body:
#                     response_text = response_body.get("completion", "")
                
#                 # Check if the text contains a function call
#                 function_call = self._parse_function_call_from_text(response_text)
                
#                 if function_call:
#                     # Extract parameters from the function call
#                     params_dict_list = function_call.get("parameters", [])
                    
#                     # Convert dictionaries to parameter objects
#                     from ...models.content import FunctionParameter
                    
#                     parameters = []
#                     for param_dict in params_dict_list:
#                         # Create a FunctionParameter object instead of a dictionary
#                         param = FunctionParameter(name=param_dict['name'], value=param_dict['value'])
#                         parameters.append(param)
                    
#                     # Create a function call response
#                     return Message(
#                         content=FunctionCallContent(
#                             name=function_call.get("name", ""),
#                             parameters=parameters
#                         ),
#                         role=MessageRole.AGENT,
#                         parent_message_id=message.message_id,
#                         conversation_id=message.conversation_id
#                     )
#             else:
#                 # Generic handling for other model providers
#                 response_text = response_body.get("results", [{}])[0].get("outputText", "")
#                 if not response_text:
#                     # Fallback to looking for text in other common response formats
#                     response_text = response_body.get("generated_text", "")
            
#             # Convert response to A2A format
#             return Message(
#                 content=TextContent(text=response_text),
#                 role=MessageRole.AGENT,
#                 parent_message_id=message.message_id,
#                 conversation_id=message.conversation_id
#             )
        
#         except Exception as e:
#             raise A2AConnectionError(f"Failed to communicate with AWS Bedrock: {str(e)}")

#     def handle_conversation(self, conversation: Conversation) -> Conversation:
#         """
#         Process an incoming A2A conversation using AWS Bedrock's API
        
#         This method overrides the default implementation to send the entire
#         conversation history to Bedrock instead of just the last message.
        
#         Args:
#             conversation: The incoming A2A conversation
            
#         Returns:
#             The updated conversation with the response
#         """
#         if not conversation.messages:
#             # Empty conversation, create an error
#             conversation.create_error_message("Empty conversation received")
#             return conversation
        
#         try:
#             # Create messages array for Bedrock
#             bedrock_messages = []
            
#             # Add all messages from the conversation
#             for msg in conversation.messages:
#                 role = "user" if msg.role == MessageRole.USER else "assistant"
                
#                 if msg.content.type == "text":
#                     bedrock_messages.append({
#                         "role": role,
#                         "content": msg.content.text
#                     })
#                 elif msg.content.type == "function_call":
#                     # Format function call as text
#                     params_str = ", ".join(
#                         [f"{p.name}={p.value}" for p in msg.content.parameters])
#                     text = f"Call function {msg.content.name}({params_str})"
#                     bedrock_messages.append({"role": role, "content": text})
#                 elif msg.content.type == "function_response":
#                     # Format function response as text
#                     text = f"Function {msg.content.name} returned: {msg.content.response}"
#                     bedrock_messages.append({"role": role, "content": text})
#                 else:
#                     # Handle other message types or errors
#                     text = f"Message of type {msg.content.type}"
#                     if hasattr(msg.content, "message"):
#                         text = msg.content.message
#                     bedrock_messages.append({"role": role, "content": text})
            
#             # Determine model type and prepare request
#             is_anthropic = "anthropic" in self.model_id.lower()
            
#             # Prepare request body
#             request_body = {}
            
#             if is_anthropic:
#                 # For Anthropic Claude models
#                 request_body = {
#                     "anthropic_version": "bedrock-2023-05-31",
#                     "max_tokens": self.max_tokens,
#                     "messages": bedrock_messages
#                 }
                
#                 # Add system prompt if available
#                 if self.system_prompt:
#                     request_body["system"] = self.system_prompt
                
#                 # Add temperature
#                 if self.temperature is not None:
#                     request_body["temperature"] = self.temperature
#             else:
#                 # Generic format for other providers
#                 request_body = {
#                     "inputText": "\n".join([msg.get("content", "") for msg in bedrock_messages]),
#                     "textGenerationConfig": {
#                         "maxTokenCount": self.max_tokens,
#                         "temperature": self.temperature,
#                     }
#                 }
            
#             # Convert to JSON string
#             request_json = json.dumps(request_body)
            
#             # Call Bedrock synchronously
#             response = self.client.invoke_model(
#                 modelId=self.model_id,
#                 contentType="application/json",
#                 accept="application/json",
#                 body=request_json
#             )
            
#             # Parse the response
#             response_body = json.loads(response['body'].read())
            
#             # Get the last message ID to use as parent
#             parent_id = conversation.messages[-1].message_id
            
#             # Process the response based on the model provider
#             if is_anthropic:
#                 # Extract text content
#                 content_items = response_body.get("content", [])
#                 response_text = ""
                
#                 for content in content_items:
#                     if content.get("type") == "text":
#                         response_text += content.get("text", "")
                
#                 # If we didn't get any text from content items but have a completion field
#                 if not response_text and "completion" in response_body:
#                     response_text = response_body.get("completion", "")
                
#                 # Check if the text contains a function call
#                 function_call = self._parse_function_call_from_text(response_text)
                
#                 if function_call:
#                     # Extract parameters from the function call
#                     params_dict_list = function_call.get("parameters", [])
                    
#                     from ...models.content import FunctionParameter
                    
#                     parameters = []
#                     for param_dict in params_dict_list:
#                         # Create a FunctionParameter object
#                         param = FunctionParameter(name=param_dict['name'], value=param_dict['value'])
#                         parameters.append(param)
                    
#                     # Create a function call response
#                     a2a_response = Message(
#                         content=FunctionCallContent(
#                             name=function_call.get("name", ""),
#                             parameters=parameters
#                         ),
#                         role=MessageRole.AGENT,
#                         parent_message_id=parent_id,
#                         conversation_id=conversation.conversation_id
#                     )
                    
#                     conversation.add_message(a2a_response)
#                     return conversation
#             else:
#                 # Generic handling for other model providers
#                 response_text = response_body.get("results", [{}])[0].get("outputText", "")
#                 if not response_text:
#                     # Fallback to looking for text in other common response formats
#                     response_text = response_body.get("generated_text", "")
            
#             # Convert response to A2A format and add to conversation
#             a2a_response = Message(
#                 content=TextContent(text=response_text),
#                 role=MessageRole.AGENT,
#                 parent_message_id=parent_id,
#                 conversation_id=conversation.conversation_id
#             )
            
#             conversation.add_message(a2a_response)
#             return conversation
        
#         except Exception as e:
#             # Add an error message to the conversation
#             error_msg = f"Failed to communicate with AWS Bedrock: {str(e)}"
#             conversation.create_error_message(
#                 error_msg, parent_message_id=conversation.messages[-1].message_id)
#             return conversation
    
#     def get_metadata(self) -> Dict[str, Any]:
#         """
#         Get metadata about this agent server

#         Returns:
#             A dictionary of metadata about this agent
#         """
#         metadata = super().get_metadata()
#         metadata.update({
#             "agent_type": "BedrockA2AServer",
#             "model": self.model_id,
#             "capabilities": ["text"]
#         })

#         if self.functions:
#             metadata["capabilities"].append("function_calling")
#             metadata["functions"] = [f["name"] for f in self.functions if "name" in f]

#         return metadata



"""
AWS Bedrock-based server implementation for the A2A protocol.
"""

import json
import asyncio
from typing import Optional, Dict, Any, List
from pathlib import Path
from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent, FunctionParameter
try:
    import boto3
except ImportError:
    boto3 = None

from ...models.message import Message, MessageRole
from ...models.content import TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent
from ...models.conversation import Conversation
from ..base import BaseA2AServer
from ...exceptions import A2AImportError, A2AConnectionError

class BedrockA2AServer(BaseA2AServer):
    """
    An A2A server that uses AWS Bedrock's API to process messages.

    This server converts incoming A2A messages to Bedrock's format, processes them
    using AWS Bedrock's API, and converts the responses back to A2A format.
    """

    def __init__(
        self,
        model_id: str = "apac.anthropic.claude-3-5-sonnet-20241022-v2:0",
        aws_access_key_id = None,
        aws_secret_access_key = None,
        aws_region = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        system_prompt: Optional[str] = None,
        tools: Optional[List[Dict[str, Any]]] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
        env_path: Optional[str] = None
    ):
        """
        Initialize the AWS Bedrock A2A server

        Args:
            model_id: Bedrock model ID (default: "anthropic.claude-3-sonnet-20240229-v1:0")
            temperature: Generation temperature (default: 0.7)
            max_tokens: Maximum number of tokens to generate (default: 1000)
            system_prompt: Optional system prompt to use for all conversations
            tools: Optional list of tool definitions for tool use
            functions: Optional list of function definitions for function calling
                       (alias for tools, for compatibility with OpenAI interface)
            env_path: Optional path to .env file (default: searches in current directory)

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

        # Verify credentials were loaded
        if not self.aws_access_key_id or not self.aws_secret_access_key:
            raise A2AConnectionError(
                "AWS credentials not found in environment variables. "
                "Make sure AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY are set in your .env file."
            )

        self.model_id = model_id
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Store functions for function calling emulation
        self.functions = functions if functions is not None else tools
        
        # Create an enhanced system prompt that includes function definitions
        if self.functions and system_prompt:
            self.system_prompt = self._create_function_enhanced_system_prompt(system_prompt)
        else:
            self.system_prompt = system_prompt

        # Initialize the Bedrock runtime client
        self.client = boto3.client(
            service_name='bedrock-runtime',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_access_key
        )
    
    def _create_function_enhanced_system_prompt(self, original_prompt: str) -> str:
        """
        Enhances the system prompt with function definitions to emulate function calling

        Args:
            original_prompt: The original system prompt

        Returns:
            Enhanced system prompt with function definitions
        """
        # Create a description of available functions
        functions_description = "\n\nYou have access to the following functions:\n\n"
        
        for func in self.functions:
            functions_description += f"Function: {func.get('name', '')}\n"
            functions_description += f"Description: {func.get('description', '')}\n"
            
            # Add parameters information
            parameters = func.get('parameters', {})
            if 'properties' in parameters:
                functions_description += "Parameters:\n"
                required_params = parameters.get('required', [])
                for param_name, param_info in parameters.get('properties', {}).items():
                    required = "required" if param_name in required_params else "optional"
                    functions_description += f"- {param_name} ({required}): {param_info.get('description', '')}\n"
            
            functions_description += "\n"
        
        # Add instructions on how to call functions
        functions_description += "\nWhen you need to call a function, format your response as follows:\n"
        functions_description += "I need to call a function to answer this. I'll use the function '{function_name}'.\n"
        functions_description += "Function call: {function_name}({parameter1}={value1}, {parameter2}={value2}, ...)\n\n"
        
        # Combine with original prompt
        enhanced_prompt = original_prompt + functions_description
        
        print(f"Enhanced system prompt: {enhanced_prompt}")
        return enhanced_prompt

    def _call_bedrock(self, bedrock_messages: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Make a call to AWS Bedrock API

        Args:
            bedrock_messages: List of messages in Bedrock format

        Returns:
            The response from Bedrock API

        Raises:
            A2AConnectionError: If connection to Bedrock fails
        """
        try:
            # Determine model type - ARN or normal model ID
            is_arn = self.model_id.startswith("arn:")

            # Check if this is an Anthropic model
            is_anthropic = "anthropic" in self.model_id.lower()

            # Prepare request body
            request_body = {}

            if is_anthropic:
                # For inference profiles (ARN) and regular Claude models
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "messages": bedrock_messages
                }

                # Add system prompt if available
                if self.system_prompt:
                    request_body["system"] = self.system_prompt

                # Add temperature
                if self.temperature is not None:
                    request_body["temperature"] = self.temperature
            else:
                # Generic format for other providers
                request_body = {
                    "inputText": "\n".join([msg.get("content", "") for msg in bedrock_messages]),
                    "textGenerationConfig": {
                        "maxTokenCount": self.max_tokens,
                        "temperature": self.temperature,
                    }
                }

            # Log the entire request payload for debugging
            print(f"Full request payload: {json.dumps(request_body, indent=2)}")

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
            return response_body

        except Exception as e:
            # Log details about the error and request for debugging
            error_msg = f"Failed to communicate with AWS Bedrock: {str(e)}"
            print(f"Error details: {error_msg}")
            print(f"Model ID: {self.model_id}")
            print(f"Request body: {request_body}")
            raise A2AConnectionError(error_msg)
    
    def _parse_function_call_from_text(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Parse a function call from text response

        Args:
            text: The text response from the model

        Returns:
            Dictionary with function name and parameters, or None if no function call is detected
        """
        # Look for common function call patterns
        import re
        
        # Print full text for debugging
        print(f"Parsing function call from text: {text}")
        
        # Pattern 1: Function call: function_name(param1=value1, param2=value2)
        pattern1 = r"Function call: (\w+)\((.*?)\)"
        match1 = re.search(pattern1, text)
        
        # Pattern 2: I'll use the function 'function_name'
        pattern2 = r"I'll use the function ['\"]([\w]+)['\"]"
        match2 = re.search(pattern2, text)
        
        # Pattern 3: Direct pattern function_name(param1=value1, param2=value2)
        pattern3 = r"(\w+)\((.*?)\)"
        match3 = re.search(pattern3, text)
        
        function_name = None
        parameters = []
        
        # Try to extract function name
        if match1:
            function_name = match1.group(1)
            params_str = match1.group(2)
            
            # Parse parameters
            if params_str:
                param_pairs = params_str.split(',')
                for pair in param_pairs:
                    if '=' in pair:
                        key, value = pair.split('=', 1)
                        parameters.append({
                            "name": key.strip(), 
                            "value": value.strip().strip('"\'')
                        })
        
        elif match2:
            function_name = match2.group(1)
            
            # Look for parameters in Pattern 3
            for m in re.finditer(pattern3, text):
                if m.group(1) == function_name:
                    params_str = m.group(2)
                    if params_str:
                        param_pairs = params_str.split(',')
                        for pair in param_pairs:
                            if '=' in pair:
                                key, value = pair.split('=', 1)
                                parameters.append({
                                    "name": key.strip(), 
                                    "value": value.strip().strip('"\'')
                                })
                    break
        
        # If no match found with patterns 1 or 2, try pattern 3 directly
        elif match3 and not function_name:
            # Check if the function name is one of our defined functions
            potential_name = match3.group(1)
            
            # Check if this is a valid function name
            is_valid = False
            if self.functions:
                for func in self.functions:
                    if func.get('name') == potential_name:
                        is_valid = True
                        break
            
            if is_valid:
                function_name = potential_name
                params_str = match3.group(2)
                
                # Parse parameters
                if params_str:
                    param_pairs = params_str.split(',')
                    for pair in param_pairs:
                        if '=' in pair:
                            key, value = pair.split('=', 1)
                            parameters.append({
                                "name": key.strip(), 
                                "value": value.strip().strip('"\'')
                            })
        
        # If a function name was found, return the result
        if function_name:
            print(f"Detected function call: {function_name}")
            print(f"Parameters: {parameters}")
            return {
                "name": function_name,
                "parameters": parameters
            }
        
        return None
    
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
            # Create messages array for Bedrock
            bedrock_messages = []
            
            # Add the user message
            if message.content.type == "text":
                msg_role = "user" if message.role == MessageRole.USER else "assistant"
                bedrock_messages.append({
                    "role": msg_role,
                    "content": message.content.text
                })
            elif message.content.type == "function_call":
                # Format function call as text
                params_str = ", ".join(
                    [f"{p.name}={p.value}" for p in message.content.parameters])
                text = f"Call function {message.content.name}({params_str})"
                bedrock_messages.append({"role": "user", "content": text})
            elif message.content.type == "function_response":
                # Format function response as text
                text = f"Function {message.content.name} returned: {message.content.response}"
                bedrock_messages.append({"role": "user", "content": text})
            else:
                # Handle other message types or errors
                text = f"Message of type {message.content.type}"
                if hasattr(message.content, "message"):
                    text = message.content.message
                bedrock_messages.append({"role": "user", "content": text})
            
            # Determine model type - ARN or normal model ID
            is_arn = self.model_id.startswith("arn:")
            
            # Check if this is an Anthropic model
            is_anthropic = "anthropic" in self.model_id.lower()
            
            # Prepare request body
            request_body = {}
            
            if is_anthropic:
                # For inference profiles (ARN) and regular Claude models
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "messages": bedrock_messages
                }
                
                # Add system prompt if available
                if self.system_prompt:
                    request_body["system"] = self.system_prompt
                
                # Add temperature
                if self.temperature is not None:
                    request_body["temperature"] = self.temperature
            else:
                # Generic format for other providers
                request_body = {
                    "inputText": "\n".join([msg.get("content", "") for msg in bedrock_messages]),
                    "textGenerationConfig": {
                        "maxTokenCount": self.max_tokens,
                        "temperature": self.temperature,
                    }
                }
            
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
            
            # Process the response based on the model provider
            if is_anthropic:
                # Extract text content
                content_items = response_body.get("content", [])
                response_text = ""
                
                for content in content_items:
                    if content.get("type") == "text":
                        response_text += content.get("text", "")
                
                # If we didn't get any text from content items but have a completion field
                if not response_text and "completion" in response_body:
                    response_text = response_body.get("completion", "")
                
                # Check if the text contains a function call
                function_call = self._parse_function_call_from_text(response_text)
                
                if function_call:
                    # Extract parameters from the function call
                    params_dict_list = function_call.get("parameters", [])
                    
                    # Convert dictionaries to parameter objects
                    from ...models.content import FunctionParameter
                    
                    parameters = []
                    for param_dict in params_dict_list:
                        # Create a FunctionParameter object instead of a dictionary
                        param = FunctionParameter(name=param_dict['name'], value=param_dict['value'])
                        parameters.append(param)
                    
                    # Create a function call response
                    return Message(
                        content=FunctionCallContent(
                            name=function_call.get("name", ""),
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
            else:
                # Generic handling for other model providers
                response_text = response_body.get("results", [{}])[0].get("outputText", "")
                if not response_text:
                    # Fallback to looking for text in other common response formats
                    response_text = response_body.get("generated_text", "")
            
            # Convert response to A2A format
            return Message(
                content=TextContent(text=response_text),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        except Exception as e:
            raise A2AConnectionError(f"Failed to communicate with AWS Bedrock: {str(e)}")

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
            # Create messages array for Bedrock
            bedrock_messages = []
            
            # Add all messages from the conversation
            for msg in conversation.messages:
                role = "user" if msg.role == MessageRole.USER else "assistant"
                
                if msg.content.type == "text":
                    bedrock_messages.append({
                        "role": role,
                        "content": msg.content.text
                    })
                elif msg.content.type == "function_call":
                    # Format function call as text
                    params_str = ", ".join(
                        [f"{p.name}={p.value}" for p in msg.content.parameters])
                    text = f"Call function {msg.content.name}({params_str})"
                    bedrock_messages.append({"role": role, "content": text})
                elif msg.content.type == "function_response":
                    # Format function response as text
                    text = f"Function {msg.content.name} returned: {msg.content.response}"
                    bedrock_messages.append({"role": role, "content": text})
                else:
                    # Handle other message types or errors
                    text = f"Message of type {msg.content.type}"
                    if hasattr(msg.content, "message"):
                        text = msg.content.message
                    bedrock_messages.append({"role": role, "content": text})
            
            # Determine model type and prepare request
            is_anthropic = "anthropic" in self.model_id.lower()
            
            # Prepare request body
            request_body = {}
            
            if is_anthropic:
                # For Anthropic Claude models
                request_body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": self.max_tokens,
                    "messages": bedrock_messages
                }
                
                # Add system prompt if available
                if self.system_prompt:
                    request_body["system"] = self.system_prompt
                
                # Add temperature
                if self.temperature is not None:
                    request_body["temperature"] = self.temperature
            else:
                # Generic format for other providers
                request_body = {
                    "inputText": "\n".join([msg.get("content", "") for msg in bedrock_messages]),
                    "textGenerationConfig": {
                        "maxTokenCount": self.max_tokens,
                        "temperature": self.temperature,
                    }
                }
            
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
            
            # Get the last message ID to use as parent
            parent_id = conversation.messages[-1].message_id
            
            # Process the response based on the model provider
            if is_anthropic:
                # Extract text content
                content_items = response_body.get("content", [])
                response_text = ""
                
                for content in content_items:
                    if content.get("type") == "text":
                        response_text += content.get("text", "")
                
                # If we didn't get any text from content items but have a completion field
                if not response_text and "completion" in response_body:
                    response_text = response_body.get("completion", "")
                
                # Check if the text contains a function call
                function_call = self._parse_function_call_from_text(response_text)
                
                if function_call:
                    # Extract parameters from the function call
                    params_dict_list = function_call.get("parameters", [])
                    
                    from ...models.content import FunctionParameter
                    
                    parameters = []
                    for param_dict in params_dict_list:
                        # Create a FunctionParameter object
                        param = FunctionParameter(name=param_dict['name'], value=param_dict['value'])
                        parameters.append(param)
                    
                    # Create a function call response
                    a2a_response = Message(
                        content=FunctionCallContent(
                            name=function_call.get("name", ""),
                            parameters=parameters
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=parent_id,
                        conversation_id=conversation.conversation_id
                    )
                    
                    conversation.add_message(a2a_response)
                    return conversation
            else:
                # Generic handling for other model providers
                response_text = response_body.get("results", [{}])[0].get("outputText", "")
                if not response_text:
                    # Fallback to looking for text in other common response formats
                    response_text = response_body.get("generated_text", "")
            
            # Convert response to A2A format and add to conversation
            a2a_response = Message(
                content=TextContent(text=response_text),
                role=MessageRole.AGENT,
                parent_message_id=parent_id,
                conversation_id=conversation.conversation_id
            )
            
            conversation.add_message(a2a_response)
            return conversation
        
        except Exception as e:
            # Add an error message to the conversation
            error_msg = f"Failed to communicate with AWS Bedrock: {str(e)}"
            conversation.create_error_message(
                error_msg, parent_message_id=conversation.messages[-1].message_id)
            return conversation
    
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
            "capabilities": ["text"]
        })

        if self.functions:
            metadata["capabilities"].append("function_calling")
            metadata["functions"] = [f["name"] for f in self.functions if "name" in f]

        return metadata