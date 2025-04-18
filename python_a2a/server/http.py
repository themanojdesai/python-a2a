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
    
    # Allow CORS for all routes
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Handle OPTIONS requests for CORS preflight
    @app.route('/', methods=['OPTIONS'])
    @app.route('/<path:path>', methods=['OPTIONS'])
    def options_handler(path=None):
        return '', 200
    
    # Set up the agent's routes if it supports it
    if hasattr(agent, 'setup_routes'):
        agent.setup_routes(app)
    
    # Legacy routes for backward compatibility
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
    
    # If we reach here and no routes matched, set up a catch-all route
    @app.route('/', defaults={'path': ''})
    @app.route('/<path:path>')
    def catch_all(path):
        # Only for GET requests that didn't match other routes
        if request.method == 'GET':
            # Redirect to the A2A index
            return jsonify({
                "message": "A2A Agent API",
                "endpoints": {
                    "agent_card": "/agent.json or /a2a/agent.json",
                    "api": "/a2a",
                    "metadata": "/a2a/metadata",
                    "health": "/a2a/health"
                }
            })
    
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