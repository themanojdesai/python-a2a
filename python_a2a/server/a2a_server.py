"""
Enhanced A2A server with protocol support.
"""

from flask import request, jsonify, Response
import uuid
from typing import Optional, Dict, Any, List, Union

from ..models.agent import AgentCard, AgentSkill
from ..models.task import Task, TaskStatus, TaskState
from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent, ErrorContent
from .base import BaseA2AServer
from ..exceptions import A2AConfigurationError


class A2AServer(BaseA2AServer):
    """
    Enhanced A2A server with protocol support
    """
    
    def __init__(self, agent_card=None, message_handler=None, **kwargs):
        """Initialize with optional agent card and message handler"""
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
    
    def _create_default_agent_card(self, **kwargs):
        """Create a default agent card from attributes"""
        name = kwargs.get("name", getattr(self.__class__, "name", "A2A Agent"))
        description = kwargs.get("description", getattr(self.__class__, "description", "A2A-compatible agent"))
        url = kwargs.get("url", None)
        version = kwargs.get("version", getattr(self.__class__, "version", "1.0.0"))
        
        return AgentCard(
            name=name,
            description=description,
            url=url,
            version=version,
            authentication=kwargs.get("authentication", getattr(self.__class__, "authentication", None)),
            capabilities=kwargs.get("capabilities", {
                "streaming": False,
                "pushNotifications": False,
                "stateTransitionHistory": False
            }),
            default_input_modes=kwargs.get("input_modes", ["text/plain"]),
            default_output_modes=kwargs.get("output_modes", ["text/plain"])
        )
    
    def handle_message(self, message):
        """
        Legacy method for backward compatibility
        """
        # Use message handler if provided in constructor
        if hasattr(self, 'message_handler') and self.message_handler:
            return self.message_handler(message)
            
        # Convert message to task
        task = Task(message=message.to_dict())
        
        # Process task
        processed_task = self.handle_task(task)
        
        # Extract response message
        if processed_task.status.message:
            return Message(
                content=TextContent(text=processed_task.get_text()),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        # Create a response from artifacts if available
        if processed_task.artifacts:
            # Look for text parts and use the first one
            for part in processed_task.artifacts[0].get("parts", []):
                if part.get("type") == "text":
                    return Message(
                        content=TextContent(text=part.get("text", "")),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
        
        # Default response
        return Message(
            content=TextContent(text="Task processed"),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task):
        """
        Process an A2A task
        
        Override this in your custom server implementation.
        """
        # Default implementation calls legacy handle_message if exists
        message_data = task.message or {}
        
        # For backward compatibility with tests
        if hasattr(self, "_handle_message_impl") and self._handle_message_impl:
            try:
                # Convert to Message object if it's a dict
                if isinstance(message_data, dict):
                    from ..models import Message
                    message = Message.from_dict(message_data)
                else:
                    message = message_data
                    
                response = self._handle_message_impl(message)
                
                # Create artifact from response
                if hasattr(response, "content") and hasattr(response.content, "text"):
                    task.artifacts = [{
                        "parts": [{
                            "type": "text",
                            "text": response.content.text
                        }]
                    }]
            except Exception as e:
                # Handle errors in legacy handler
                task.artifacts = [{
                    "parts": [{
                        "type": "text", 
                        "text": f"Error in message handler: {str(e)}"
                    }]
                }]
        else:
            # Echo the message for test compatibility
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Create echo response for test compatibility
            task.artifacts = [{
                "parts": [{
                    "type": "text",
                    "text": f"Echo: {text}"
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
                "agent_card_url": "/.well-known/agent.json",
                "protocol": "a2a"
            })
            
        @app.route("/", methods=["POST"])
        def a2a_root_post():
            """Root endpoint for A2A (POST) - handle legacy message format"""
            try:
                data = request.json
                
                # Check if this is a single message or a conversation
                if "messages" in data:
                    # This is a conversation
                    conversation = Conversation.from_dict(data)
                    response = self.handle_conversation(conversation)
                    return jsonify(response.to_dict())
                else:
                    # This is a single message
                    message = Message.from_dict(data)
                    response = self.handle_message(message)
                    return jsonify(response.to_dict())
                    
            except Exception as e:
                # Return an error response for any exceptions
                error_dict = {
                    "content": {
                        "type": "error",
                        "message": f"Error processing request: {str(e)}"
                    },
                    "role": "system"
                }
                return jsonify(error_dict), 500
        
        # Root endpoint for A2A
        @app.route("/a2a", methods=["GET"])
        def a2a_index():
            """Root endpoint for A2A, redirects to agent card"""
            return jsonify({
                "name": self.agent_card.name,
                "description": self.agent_card.description,
                "agent_card_url": "/a2a/agent.json",
                "protocol": "a2a"
            })
        
        # Agent card endpoint
        @app.route("/a2a/agent.json", methods=["GET"])
        def a2a_agent_card():
            """Return the agent card as JSON"""
            return jsonify(self.agent_card.to_dict())
            
        # Also support the standard agent.json at the root
        @app.route("/.well-known/agent.json", methods=["GET"])
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
                    
                    # Extract task details
                    task_id = params.get("id", str(uuid.uuid4()))
                    session_id = params.get("sessionId")
                    message_data = params.get("message")
                    
                    # Create or update task
                    task = Task(
                        id=task_id,
                        session_id=session_id,
                        message=message_data
                    )
                    
                    # Process the task
                    result = self.handle_task(task)
                    
                    # Store the task
                    self.tasks[task_id] = result
                    
                    # Return JSON-RPC response
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": result.to_dict()
                    })
                else:
                    # Handle as direct task submission
                    task = Task.from_dict(request_data)
                    
                    # Process the task
                    result = self.handle_task(task)
                    
                    # Store the task
                    self.tasks[result.id] = result
                    
                    # Return the task
                    return jsonify(result.to_dict())
                    
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
                    
                    # Convert task to dict
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
                    
                    # Return the task
                    return jsonify(task.to_dict())
                    
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
                    
                    # Return the task
                    return jsonify({
                        "jsonrpc": "2.0",
                        "id": rpc_id,
                        "result": task.to_dict()
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
                    
                    # Return the task
                    return jsonify(task.to_dict())
                    
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
            "agent_version": self.agent_card.version
        })
        return metadata