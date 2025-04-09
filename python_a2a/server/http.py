"""
HTTP server implementation for the A2A protocol.
"""

import json
import traceback
from typing import Type, Optional, Dict, Any, Callable, Union

try:
    from flask import Flask, request, jsonify, Response
except ImportError:
    Flask = None

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent, ErrorContent
from .base import BaseA2AServer
from ..exceptions import A2AImportError, A2ARequestError


class A2AServer(BaseA2AServer):
    """
    A customizable A2A-compatible agent server.
    
    This server can be configured with custom message handlers to create
    specialized agents for different purposes.
    """
    
    def __init__(self, message_handler: Optional[Callable[[Message], Message]] = None):
        """
        Initialize the server with an optional message handler
        
        Args:
            message_handler: Optional function that processes messages
                If provided, this function will be called to handle incoming messages
                instead of the handle_message method
        """
        self.message_handler = message_handler
        
    def handle_message(self, message: Message) -> Message:
        """
        Process an incoming A2A message and generate a response
        
        If a message handler was provided in the constructor, it will be used.
        Otherwise, this method should be overridden by subclasses.
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The agent's response message
        """
        if self.message_handler:
            return self.message_handler(message)
        
        # Default implementation for when no handler is provided
        # Just echo back the input with a prefix
        if message.content.type == "text":
            return Message(
                content=TextContent(text=f"Echo: {message.content.text}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        else:
            return Message(
                content=ErrorContent(message=f"Unsupported message type: {message.content.type}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
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
            "has_custom_handler": self.message_handler is not None
        })
        return metadata


def create_flask_app(agent: BaseA2AServer) -> Flask:
    """
    Create a Flask application that serves an A2A agent
    
    Args:
        agent: The A2A agent server
        
    Returns:
        A Flask application
        
    Raises:
        A2AImportError: If Flask is not installed
    """
    if Flask is None:
        raise A2AImportError(
            "Flask is not installed. "
            "Install it with 'pip install flask'"
        )
    
    app = Flask(__name__)
    
    @app.route("/a2a", methods=["POST"])
    def handle_a2a_request() -> Union[Response, tuple]:
        """Handle A2A protocol requests"""
        try:
            data = request.json
            
            # Check if this is a single message or a conversation
            if "messages" in data:
                # This is a conversation
                conversation = Conversation.from_dict(data)
                response = agent.handle_conversation(conversation)
                return jsonify(response.to_dict())
            else:
                # This is a single message
                message = Message.from_dict(data)
                response = agent.handle_message(message)
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
    
    @app.route("/a2a/metadata", methods=["GET"])
    def get_agent_metadata() -> Response:
        """Return metadata about the agent"""
        return jsonify(agent.get_metadata())
    
    @app.route("/a2a/health", methods=["GET"])
    def health_check() -> Response:
        """Health check endpoint"""
        return jsonify({"status": "ok"})
    
    return app


def run_server(
    agent: BaseA2AServer,
    host: str = "0.0.0.0",
    port: int = 5000,
    debug: bool = False
) -> None:
    """
    Run an A2A agent as a Flask server
    
    Args:
        agent: The A2A agent server
        host: Host to bind to (default: "0.0.0.0")
        port: Port to listen on (default: 5000)
        debug: Enable debug mode (default: False)
        
    Raises:
        A2AImportError: If Flask is not installed
    """
    app = create_flask_app(agent)
    print(f"Starting A2A server on http://{host}:{port}/a2a")
    app.run(host=host, port=port, debug=debug)