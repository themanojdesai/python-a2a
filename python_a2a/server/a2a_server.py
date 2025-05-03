"""
Enhanced A2A server with protocol support.
"""

from flask import request, jsonify, Response, stream_with_context
import uuid
import json
import time
from datetime import datetime
from typing import Optional, Dict, Any, List, Union, Generator, Iterator, Callable

from ..models.agent import AgentCard, AgentSkill
from ..models.task import Task, TaskStatus, TaskState
from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent, ErrorContent, FunctionResponseContent, FunctionCallContent
from .base import BaseA2AServer
from ..exceptions import A2AConfigurationError, A2AStreamingError


class A2AServer(BaseA2AServer):
    """
    Enhanced A2A server with protocol support
    """
    
    def __init__(self, agent_card=None, message_handler=None, google_a2a_compatible=True, **kwargs):
        """
        Initialize with optional agent card and message handler
        
        Args:
            agent_card: Optional agent card
            message_handler: Optional message handler function
            google_a2a_compatible: Whether to use Google A2A format by default (True by default since this is an A2A protocol implementation)
            **kwargs: Additional keyword arguments
        """
        # Create default agent card if none provided
        if agent_card:
            self.agent_card = agent_card
        else:
            self.agent_card = self._create_default_agent_card(**kwargs)
        
        # Store the message handler for backwards compatibility
        self.message_handler = message_handler
        self._handle_message_impl = message_handler
        
        # Initialize task storage
        self.tasks = {}
        
        # Initialize streaming subscriptions
        self.streaming_subscriptions = {}
        
        # Set Google A2A compatibility mode
        self._use_google_a2a = google_a2a_compatible
        
        # Add Google A2A compatibility to capabilities
        if not hasattr(self.agent_card, 'capabilities'):
            self.agent_card.capabilities = {}
        if isinstance(self.agent_card.capabilities, dict):
            self.agent_card.capabilities["google_a2a_compatible"] = google_a2a_compatible
            self.agent_card.capabilities["parts_array_format"] = google_a2a_compatible
            
            # Add streaming capability
            self.agent_card.capabilities["streaming"] = True
    
    def _create_default_agent_card(self, **kwargs):
        """Create a default agent card from attributes"""
        name = kwargs.get("name", getattr(self.__class__, "name", "A2A Agent"))
        description = kwargs.get("description", getattr(self.__class__, "description", "A2A-compatible agent"))
        url = kwargs.get("url", None)
        version = kwargs.get("version", getattr(self.__class__, "version", "1.0.0"))
        
        # Check for Google A2A compatibility flag - default to True since this is an A2A implementation
        google_a2a_compatible = kwargs.get("google_a2a_compatible", True)
        
        # Create capabilities dict with Google A2A compatibility flag
        capabilities = kwargs.get("capabilities", {
            "streaming": True,  # Enable streaming by default
            "pushNotifications": False,
            "stateTransitionHistory": False,
            "google_a2a_compatible": google_a2a_compatible,
            "parts_array_format": google_a2a_compatible
        })
        
        return AgentCard(
            name=name,
            description=description,
            url=url,
            version=version,
            authentication=kwargs.get("authentication", getattr(self.__class__, "authentication", None)),
            capabilities=capabilities,
            default_input_modes=kwargs.get("input_modes", ["text/plain"]),
            default_output_modes=kwargs.get("output_modes", ["text/plain"])
        )
    
    def handle_message(self, message):
        """
        Legacy method for backward compatibility
        
        This method is automatically called by handle_task when a message is received.
        You can override either this method or handle_task.
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The response message
        """
        # Use message handler if provided in constructor
        if hasattr(self, 'message_handler') and self.message_handler:
            return self.message_handler(message)
            
        # Default implementation just echoes the text content
        if message.content.type == "text":
            return Message(
                content=TextContent(text=message.content.text),  # Simply echo the text
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        elif message.content.type == "function_call":
            # Basic echo for function calls when no handler is defined
            return Message(
                content=TextContent(
                    text=f"Received function call '{message.content.name}' with parameters, but no handler is defined."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        else:
            # Basic handling for non-text content
            return Message(
                content=TextContent(text="Received a non-text message"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_task(self, task):
        """
        Process an A2A task
        
        Override this in your custom server implementation.
        
        Args:
            task: The incoming A2A task
            
        Returns:
            The processed task with response
        """
        # Extract message from task with careful handling to maintain format compatibility
        message_data = task.message or {}
        
        # IMPORTANT: Check if the subclass has overridden handle_message
        has_message_handler = hasattr(self, 'handle_message') and self.handle_message != A2AServer.handle_message
        
        if has_message_handler or hasattr(self, "_handle_message_impl") and self._handle_message_impl:
            try:
                # Convert to Message object if it's a dict
                message = None
                
                if isinstance(message_data, dict):
                    from ..models import Message
                    
                    # First, check for Google A2A format
                    if "parts" in message_data and "role" in message_data and not "content" in message_data:
                        try:
                            message = Message.from_google_a2a(message_data)
                        except Exception:
                            # If conversion fails, fall back to standard format
                            pass
                    
                    # If not Google A2A format or conversion failed, try standard format
                    if message is None:
                        try:
                            message = Message.from_dict(message_data)
                        except Exception:
                            # If standard format fails too, create a basic message
                            # Extract text directly from common formats to maintain compatibility
                            text = ""
                            if "content" in message_data and isinstance(message_data["content"], dict):
                                # python_a2a format
                                content = message_data["content"]
                                if "text" in content:
                                    text = content["text"]
                                elif "message" in content:
                                    text = content["message"]
                            elif "parts" in message_data:
                                # Google A2A format
                                for part in message_data["parts"]:
                                    if isinstance(part, dict) and part.get("type") == "text" and "text" in part:
                                        text = part["text"]
                                        break
                            
                            message = Message(
                                content=TextContent(text=text),
                                role=MessageRole.USER
                            )
                else:
                    # If it's already a Message object, use it directly
                    message = message_data
                    
                # Call the appropriate message handler
                if has_message_handler:
                    response = self.handle_message(message)
                else:
                    response = self._handle_message_impl(message)
                
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
            except Exception as e:
                # Handle errors in message handler
                task.artifacts = [{
                    "parts": [{
                        "type": "error", 
                        "message": f"Error in message handler: {str(e)}"
                    }]
                }]
        else:
            # Basic echo response when no message handler exists
            content = message_data.get("content", {})
            
            # Handle different content types in passthrough mode
            if isinstance(content, dict):
                content_type = content.get("type")
                
                if content_type == "text":
                    # Text content
                    task.artifacts = [{
                        "parts": [{
                            "type": "text", 
                            "text": content.get("text", "")
                        }]
                    }]
                elif content_type == "function_call":
                    # Function call - pass through
                    task.artifacts = [{
                        "parts": [{
                            "type": "text", 
                            "text": f"Received function call '{content.get('name', '')}' without handler"
                        }]
                    }]
                else:
                    # Other content types
                    task.artifacts = [{
                        "parts": [{
                            "type": "text", 
                            "text": f"Received message of type '{content_type}'"
                        }]
                    }]
            else:
                # For Google A2A format or other formats, try to extract text
                text = ""
                if isinstance(message_data, dict):
                    if "parts" in message_data and isinstance(message_data["parts"], list):
                        # Google A2A format
                        for part in message_data["parts"]:
                            if isinstance(part, dict) and part.get("type") == "text" and "text" in part:
                                text = part["text"]
                                break
                    elif "content" in message_data and "text" in message_data["content"]:
                        # Try to extract from nested content
                        text = message_data["content"]["text"]
                
                # Non-dict content or extracted text
                task.artifacts = [{
                    "parts": [{
                        "type": "text", 
                        "text": text or str(content)
                    }]
                }]
        
        # Mark as completed
        from ..models import TaskStatus, TaskState
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def setup_routes(self, app):
        """Setup Flask routes for A2A endpoints"""
        # Root endpoint for both GET and POST
        @app.route("/", methods=["GET"])
        def a2a_root_get():
            """Root endpoint for A2A (GET), redirects to agent card"""
            return jsonify({
                "name": self.agent_card.name,
                "description": self.agent_card.description,
                "agent_card_url": "/agent.json",
                "protocol": "a2a",
                "capabilities": self.agent_card.capabilities
            })
            
        @app.route("/", methods=["POST"])
        def a2a_root_post():
            """Root endpoint for A2A (POST) - handle message in appropriate format"""
            try:
                data = request.json
                
                # First, detect if this is Google A2A format (has 'parts' field)
                is_google_format = False
                if "parts" in data and "role" in data and not "content" in data:
                    is_google_format = True
                
                # Check if it's a task
                if "id" in data and ("message" in data or "status" in data):
                    return self._handle_task_request(data, is_google_format)
                
                # Check if this is a conversation (has 'messages' field)
                if "messages" in data:
                    # Check first message format to determine if Google A2A format
                    if data["messages"] and "parts" in data["messages"][0] and "role" in data["messages"][0]:
                        is_google_format = True
                    return self._handle_conversation_request(data, is_google_format)
                
                # Handle as a single message
                return self._handle_message_request(data, is_google_format)
                
            except Exception as e:
                # Return an error response in appropriate format
                error_msg = f"Error processing request: {str(e)}"
                if self._use_google_a2a:
                    # Return error in Google A2A format
                    return jsonify({
                        "role": "agent",
                        "parts": [
                            {
                                "type": "data",
                                "data": {"error": error_msg}
                            }
                        ]
                    }), 500
                else:
                    # Return error in python_a2a format
                    return jsonify({
                        "content": {
                            "type": "error",
                            "message": error_msg
                        },
                        "role": "system"
                    }), 500
        
        # Root endpoint for A2A
        @app.route("/a2a", methods=["GET"])
        def a2a_index():
            """Root endpoint for A2A, redirects to agent card"""
            return jsonify({
                "name": self.agent_card.name,
                "description": self.agent_card.description,
                "agent_card_url": "/a2a/agent.json",
                "protocol": "a2a",
                "capabilities": self.agent_card.capabilities
            })
        
        # Also support direct POST to /a2a endpoint
        @app.route("/a2a", methods=["POST"])
        def a2a_post():
            """POST endpoint for A2A - mirrors root POST behavior"""
            return a2a_root_post()
        
        # Agent card endpoint
        @app.route("/a2a/agent.json", methods=["GET"])
        def a2a_agent_card():
            """Return the agent card as JSON"""
            return jsonify(self.agent_card.to_dict())
            
        # Also support the standard agent.json at the root
        @app.route("/agent.json", methods=["GET"])
        def agent_card():
            """Return the agent card as JSON (standard location)"""
            return jsonify(self.agent_card.to_dict())
        
        # Task endpoints with proper JSON-RPC
        @app.route("/a2a/tasks/send", methods=["POST"])
        def a2a_tasks_send():
            """Handle POST request to create or update a task"""
            try:
                # Parse JSON data
                request_data = request.json
                
                # Handle as JSON-RPC if it follows that format
                if "jsonrpc" in request_data:
                    rpc_id = request_data.get("id", 1)
                    params = request_data.get("params", {})
                    
                    # Detect format from params
                    is_google_format = False
                    if isinstance(params, dict) and "message" in params:
                        message_data = params.get("message", {})
                        if isinstance(message_data, dict) and "parts" in message_data and "role" in message_data:
                            is_google_format = True
                    
                    # Process the task
                    result = self._handle_task_request(params, is_google_format)
                    
                    # Get the data from the response
                    result_data = result.get_json() if hasattr(result, 'get_json') else result.json
                    
                    # Return JSON-RPC response
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": result_data
                    })
                else:
                    # Direct task submission - detect format
                    is_google_format = False
                    if "message" in request_data:
                        message_data = request_data.get("message", {})
                        if isinstance(message_data, dict) and "parts" in message_data and "role" in message_data:
                            is_google_format = True
                    
                    # Handle the task request
                    return self._handle_task_request(request_data, is_google_format)
                    
            except Exception as e:
                # Handle error based on request format
                if "jsonrpc" in request_data:
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": request_data.get("id", 1),
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }), 500
                else:
                    if self._use_google_a2a:
                        return jsonify({
                            "role": "agent",
                            "parts": [
                                {
                                    "type": "data",
                                    "data": {"error": f"Error: {str(e)}"}
                                }
                            ]
                        }), 500
                    else:
                        return jsonify({
                            "content": {
                                "type": "error",
                                "message": f"Error: {str(e)}"
                            },
                            "role": "system"
                        }), 500
        
        # Also support the standard /tasks/send at the root
        @app.route("/tasks/send", methods=["POST"])
        def tasks_send():
            """Forward to the A2A tasks/send endpoint"""
            return a2a_tasks_send()
        
        @app.route("/a2a/tasks/get", methods=["POST"])
        def a2a_tasks_get():
            """Handle POST request to get a task"""
            try:
                # Parse JSON data
                request_data = request.json
                
                # Handle as JSON-RPC if it follows that format
                if "jsonrpc" in request_data:
                    rpc_id = request_data.get("id", 1)
                    params = request_data.get("params", {})
                    
                    # Extract task ID
                    task_id = params.get("id")
                    history_length = params.get("historyLength", 0)
                    
                    # Get the task
                    task = self.tasks.get(task_id)
                    if not task:
                        return jsonify({
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {
                                "code": -32000,
                                "message": f"Task not found: {task_id}"
                            }
                        }), 404
                    
                    # Convert task to dict in appropriate format
                    if self._use_google_a2a:
                        task_dict = task.to_google_a2a()
                    else:
                        task_dict = task.to_dict()
                    
                    # Return the task
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": task_dict
                    })
                else:
                    # Handle as direct task request
                    task_id = request_data.get("id")
                    
                    # Get the task
                    task = self.tasks.get(task_id)
                    if not task:
                        return jsonify({"error": f"Task not found: {task_id}"}), 404
                    
                    # Convert task to dict in appropriate format
                    if self._use_google_a2a:
                        task_dict = task.to_google_a2a()
                    else:
                        task_dict = task.to_dict()
                    
                    # Return the task
                    return jsonify(task_dict)
                    
            except Exception as e:
                # Handle error
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_data.get("id", 1) if 'request_data' in locals() else 1,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }), 500
        
        # Also support the standard /tasks/get at the root
        @app.route("/tasks/get", methods=["POST"])
        def tasks_get():
            """Forward to the A2A tasks/get endpoint"""
            return a2a_tasks_get()
        
        @app.route("/a2a/tasks/cancel", methods=["POST"])
        def a2a_tasks_cancel():
            """Handle POST request to cancel a task"""
            try:
                # Parse JSON data
                request_data = request.json
                
                # Handle as JSON-RPC if it follows that format
                if "jsonrpc" in request_data:
                    rpc_id = request_data.get("id", 1)
                    params = request_data.get("params", {})
                    
                    # Extract task ID
                    task_id = params.get("id")
                    
                    # Get the task
                    task = self.tasks.get(task_id)
                    if not task:
                        return jsonify({
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {
                                "code": -32000,
                                "message": f"Task not found: {task_id}"
                            }
                        }), 404
                    
                    # Cancel the task
                    task.status = TaskStatus(state=TaskState.CANCELED)
                    
                    # Convert task to dict in appropriate format
                    if self._use_google_a2a:
                        task_dict = task.to_google_a2a()
                    else:
                        task_dict = task.to_dict()
                    
                    # Return the task
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": task_dict
                    })
                else:
                    # Handle as direct task request
                    task_id = request_data.get("id")
                    
                    # Get the task
                    task = self.tasks.get(task_id)
                    if not task:
                        return jsonify({"error": f"Task not found: {task_id}"}), 404
                    
                    # Cancel the task
                    task.status = TaskStatus(state=TaskState.CANCELED)
                    
                    # Convert task to dict in appropriate format
                    if self._use_google_a2a:
                        task_dict = task.to_google_a2a()
                    else:
                        task_dict = task.to_dict()
                    
                    # Return the task
                    return jsonify(task_dict)
                    
            except Exception as e:
                # Handle error
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_data.get("id", 1) if 'request_data' in locals() else 1,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }), 500
        
        # Also support the standard /tasks/cancel at the root
        @app.route("/tasks/cancel", methods=["POST"])
        def tasks_cancel():
            """Forward to the A2A tasks/cancel endpoint"""
            return a2a_tasks_cancel()
            
        # Add streaming endpoints
        @app.route("/a2a/tasks/stream", methods=["POST"])
        def a2a_tasks_stream():
            """
            Streaming endpoint that handles tasks/sendSubscribe and tasks/resubscribe
            """
            try:
                # Parse JSON data
                request_data = request.json
                
                # Check if this is a JSON-RPC request
                if "jsonrpc" in request_data:
                    method = request_data.get("method", "")
                    params = request_data.get("params", {})
                    rpc_id = request_data.get("id", 1)
                    
                    # Handle different streaming methods
                    if method == "tasks/sendSubscribe":
                        # Process tasks/sendSubscribe
                        return self._handle_tasks_send_subscribe(params, rpc_id)
                    elif method == "tasks/resubscribe":
                        # Process tasks/resubscribe
                        return self._handle_tasks_resubscribe(params, rpc_id)
                    else:
                        # Unknown method
                        return jsonify({
                            "jsonrpc": "2.0",
                            "id": rpc_id,
                            "error": {
                                "code": -32601,
                                "message": f"Method '{method}' not found"
                            }
                        }), 404
                else:
                    # Not a JSON-RPC request
                    return jsonify({
                        "error": "Expected JSON-RPC format for streaming requests"
                    }), 400
                    
            except Exception as e:
                # Handle error
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": request_data.get("id", 1) if 'request_data' in locals() else 1,
                    "error": {
                        "code": -32603,
                        "message": f"Internal error: {str(e)}"
                    }
                }), 500
                
        # Also support the standard /tasks/stream at the root
        @app.route("/tasks/stream", methods=["POST"])
        def tasks_stream():
            """Forward to the A2A tasks/stream endpoint"""
            return a2a_tasks_stream()
            
    def _handle_message_request(self, data, is_google_format=False):
        """
        Handle a message request in either format
        
        Args:
            data: Request data
            is_google_format: Whether the request is in Google A2A format
            
        Returns:
            Response with the message in appropriate format
        """
        try:
            # Convert from the appropriate format
            if is_google_format:
                # Google A2A format
                message = Message.from_google_a2a(data)
            else:
                # Standard python_a2a format
                message = Message.from_dict(data)
            
            # Process the message
            response = self.handle_message(message)
            
            # Convert to the appropriate format for response
            if is_google_format or self._use_google_a2a:
                # Use Google A2A format for response
                return jsonify(response.to_google_a2a())
            else:
                # Use standard python_a2a format
                return jsonify(response.to_dict())
        except Exception as e:
            # Return an error in the appropriate format
            error_msg = f"Error processing message: {str(e)}"
            if is_google_format or self._use_google_a2a:
                return jsonify({
                    "role": "agent",
                    "parts": [
                        {
                            "type": "data",
                            "data": {"error": error_msg}
                        }
                    ]
                }), 500
            else:
                return jsonify({
                    "content": {
                        "type": "error",
                        "message": error_msg
                    },
                    "role": "system"
                }), 500
                
    def _handle_conversation_request(self, data, is_google_format=False):
        """
        Handle a conversation request in either format
        
        Args:
            data: Request data
            is_google_format: Whether the request is in Google A2A format
            
        Returns:
            Response with the conversation in appropriate format
        """
        try:
            # Convert from the appropriate format
            if is_google_format:
                # Google A2A format
                conversation = Conversation.from_google_a2a(data)
            else:
                # Standard python_a2a format
                conversation = Conversation.from_dict(data)
            
            # Process the conversation
            response = self.handle_conversation(conversation)
            
            # Convert to the appropriate format for response
            if is_google_format or self._use_google_a2a:
                # Use Google A2A format for response
                return jsonify(response.to_google_a2a())
            else:
                # Use standard python_a2a format
                return jsonify(response.to_dict())
        except Exception as e:
            # Return an error in the appropriate format
            error_msg = f"Error processing conversation: {str(e)}"
            if is_google_format or self._use_google_a2a:
                return jsonify({
                    "conversation_id": data.get("conversation_id", ""),
                    "messages": [
                        {
                            "role": "agent",
                            "parts": [
                                {
                                    "type": "data",
                                    "data": {"error": error_msg}
                                }
                            ]
                        }
                    ]
                }), 500
            else:
                return jsonify({
                    "conversation_id": data.get("conversation_id", ""),
                    "messages": [
                        {
                            "content": {
                                "type": "error",
                                "message": error_msg
                            },
                            "role": "system"
                        }
                    ]
                }), 500
                
    def _handle_task_request(self, data, is_google_format=False):
        """
        Handle a task request in either format
        
        Args:
            data: Request data
            is_google_format: Whether the request is in Google A2A format
            
        Returns:
            Response with the task in appropriate format
        """
        try:
            # Extract task ID and session ID
            task_id = data.get("id", str(uuid.uuid4()))
            session_id = data.get("sessionId")
            
            # Create task based on format
            if is_google_format:
                # Google A2A format - preserve the exact format of message
                task = Task.from_google_a2a(data)
            else:
                # Standard python_a2a format - preserve the exact format of message
                task = Task.from_dict(data)
            
            # Process the task
            result = self.handle_task(task)
            
            # Store the task
            self.tasks[result.id] = result
            
            # Convert to the appropriate format for response
            if is_google_format or self._use_google_a2a:
                # Use Google A2A format for response
                return jsonify(result.to_google_a2a())
            else:
                # Use standard python_a2a format
                return jsonify(result.to_dict())
        except Exception as e:
            # Return an error in the appropriate format
            error_msg = f"Error processing task: {str(e)}"
            error_response = {
                "id": data.get("id", ""),
                "sessionId": data.get("sessionId", ""),
                "status": {
                    "state": "failed",
                    "message": {"error": error_msg},
                    "timestamp": datetime.now().isoformat()
                }
            }
            return jsonify(error_response), 500
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this agent server
        
        Returns:
            A dictionary of metadata about this agent
        """
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "A2AServer",
            "capabilities": ["text"],
            "has_agent_card": True,
            "agent_name": self.agent_card.name,
            "agent_version": self.agent_card.version,
            "google_a2a_compatible": self._use_google_a2a
        })
        return metadata
    
    def use_google_a2a_format(self, use_google_format: bool = True) -> None:
        """
        Set whether to use Google A2A format for responses
        
        Args:
            use_google_format: Whether to use Google A2A format
        """
        self._use_google_a2a = use_google_format
        
        # Update agent card capabilities
        if isinstance(self.agent_card.capabilities, dict):
            self.agent_card.capabilities["google_a2a_compatible"] = use_google_format
            self.agent_card.capabilities["parts_array_format"] = use_google_format
        
    def is_using_google_a2a_format(self) -> bool:
        """
        Check if using Google A2A format
        
        Returns:
            True if using Google A2A format, False otherwise
        """
        return self._use_google_a2a
        
    def _handle_tasks_send_subscribe(self, params, rpc_id):
        """
        Handle the tasks/sendSubscribe method to create and subscribe to a new task
        
        Args:
            params: Task parameters from the request
            rpc_id: JSON-RPC ID for the request
            
        Returns:
            A streaming response for the task execution
        """
        try:
            # Extract task ID and session ID
            task_id = params.get("id", str(uuid.uuid4()))
            session_id = params.get("sessionId")
            
            # Create task from params
            task = Task.from_dict(params)
            
            # Process the task in the background
            # For this implementation, we'll create a generator to simulate real-time updates
            
            def generate_sse_stream():
                """Generate a Server-Sent Events stream for task execution"""
                # Send initial task state
                initial_task = task.to_dict() if not self._use_google_a2a else task.to_google_a2a()
                yield f"event: update\nid: {rpc_id}\ndata: {json.dumps(initial_task)}\n\n"
                
                # Process the task
                result_task = None
                try:
                    result_task = self.handle_task(task)
                except Exception as e:
                    # Handle error
                    task.status = TaskStatus(
                        state=TaskState.FAILED,
                        message={"error": str(e)}
                    )
                    result_task = task
                
                # Store the task
                self.tasks[result_task.id] = result_task
                
                # Send complete event
                complete_task = result_task.to_dict() if not self._use_google_a2a else result_task.to_google_a2a()
                yield f"event: complete\nid: {rpc_id}\ndata: {json.dumps(complete_task)}\n\n"
            
            # Create a streaming response
            return Response(
                stream_with_context(generate_sse_stream()),
                content_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable Nginx buffering
                }
            )
            
        except Exception as e:
            # Return an error response
            return jsonify({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }), 500
    
    def _handle_tasks_resubscribe(self, params, rpc_id):
        """
        Handle the tasks/resubscribe method to resubscribe to an existing task
        
        Args:
            params: Parameters containing task ID and optional session ID
            rpc_id: JSON-RPC ID for the request
            
        Returns:
            A streaming response with the task's current state and updates
        """
        try:
            # Extract task ID and session ID
            task_id = params.get("id")
            session_id = params.get("sessionId")
            
            if not task_id:
                # Task ID is required
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32602,
                        "message": "Missing required parameter: id"
                    }
                }), 400
            
            # Get the task
            task = self.tasks.get(task_id)
            if not task:
                # Task not found
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": rpc_id,
                    "error": {
                        "code": -32000,
                        "message": f"Task not found: {task_id}"
                    }
                }), 404
            
            # Generate a stream for the task's current state
            def generate_sse_stream():
                """Generate a Server-Sent Events stream for the task's current state"""
                # Send the current task state
                current_task = task.to_dict() if not self._use_google_a2a else task.to_google_a2a()
                yield f"event: update\nid: {rpc_id}\ndata: {json.dumps(current_task)}\n\n"
                
                # If the task is not completed, failed, or canceled, we should wait for updates
                if task.status.state not in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
                    # In a real implementation, this would wait for task updates
                    # For this example, we'll just send a completion event after a delay
                    time.sleep(0.5)  # Small delay to simulate processing
                    
                    # Update task status to completed
                    task.status = TaskStatus(state=TaskState.COMPLETED)
                    
                    # Send complete event
                    complete_task = task.to_dict() if not self._use_google_a2a else task.to_google_a2a()
                    yield f"event: complete\nid: {rpc_id}\ndata: {json.dumps(complete_task)}\n\n"
                else:
                    # If the task is already in a final state, send a complete event
                    complete_task = task.to_dict() if not self._use_google_a2a else task.to_google_a2a()
                    yield f"event: complete\nid: {rpc_id}\ndata: {json.dumps(complete_task)}\n\n"
            
            # Create a streaming response
            return Response(
                stream_with_context(generate_sse_stream()),
                content_type="text/event-stream",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable Nginx buffering
                }
            )
            
        except Exception as e:
            # Return an error response
            return jsonify({
                "jsonrpc": "2.0",
                "id": rpc_id,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }), 500