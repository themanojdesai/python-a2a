"""
HTTP server implementation for the A2A protocol.
"""

import json
import traceback
from typing import Type, Optional, Dict, Any, Callable, Union

try:
    from flask import Flask, request, jsonify, Response, render_template_string, make_response
except ImportError:
    Flask = None

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent, ErrorContent
from .base import BaseA2AServer
from ..exceptions import A2AImportError, A2ARequestError
from .ui_templates import AGENT_INDEX_HTML, JSON_HTML_TEMPLATE


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
    
    # Define a function to render beautiful HTML UI
    def get_agent_data():
        """Get basic agent data for rendering"""
        if hasattr(agent, 'agent_card'):
            return agent.agent_card.to_dict() 
        else:
            # Fallback for agents without agent_card
            return {
                "name": "A2A Agent",
                "description": "Agent details not available",
                "version": "1.0.0",
                "skills": []
            }
    
    # IMPORTANT: Register our enhanced routes FIRST to ensure they take precedence
    # Enhanced routes for beautiful UI
    @app.route("/a2a", methods=["GET"])
    def enhanced_a2a_index():
        """A2A index with beautiful UI"""
        # Check if this is a browser request by looking at headers
        user_agent = request.headers.get('User-Agent', '')
        accept_header = request.headers.get('Accept', '')
        
        # Force JSON if explicitly requested
        format_param = request.args.get('format', '')
        
        # Return JSON if explicitly requested or doesn't look like a browser
        if format_param == 'json' or (
            'application/json' in accept_header and 
            not any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari', 'edge'])
        ):
            return jsonify({
                "name": agent.agent_card.name if hasattr(agent, 'agent_card') else "A2A Agent",
                "description": agent.agent_card.description if hasattr(agent, 'agent_card') else "",
                "agent_card_url": "/a2a/agent.json",
                "protocol": "a2a"
            })
        
        # Otherwise serve HTML by default
        response = make_response(render_template_string(
            AGENT_INDEX_HTML,
            agent=agent,
            request=request
        ))
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    
    @app.route("/", methods=["GET"])
    def enhanced_root_index():
        """Root endpoint with beautiful UI"""
        return enhanced_a2a_index()
    
    @app.route("/agent", methods=["GET"])
    def enhanced_agent_index():
        """Agent endpoint with beautiful UI"""
        return enhanced_a2a_index()
    
    @app.route("/a2a/agent.json", methods=["GET"])
    def enhanced_a2a_agent_json():
        """Agent card JSON with beautiful UI"""
        # Get agent data
        agent_data = get_agent_data()
        
        # Check request format preferences
        user_agent = request.headers.get('User-Agent', '')
        accept_header = request.headers.get('Accept', '')
        format_param = request.args.get('format', '')
        
        # Return JSON if explicitly requested or doesn't look like a browser
        if format_param == 'json' or (
            'application/json' in accept_header and 
            not any(browser in user_agent.lower() for browser in ['mozilla', 'chrome', 'safari', 'edge'])
        ):
            return jsonify(agent_data)
        
        # Otherwise serve HTML with pretty JSON visualization
        formatted_json = json.dumps(agent_data, indent=2)
        response = make_response(render_template_string(
            JSON_HTML_TEMPLATE,
            title=agent_data.get('name', 'A2A Agent'),
            description="Agent Card JSON Data",
            json_data=formatted_json
        ))
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response
    
    @app.route("/agent.json", methods=["GET"])
    def enhanced_root_agent_json():
        """Root agent.json endpoint"""
        return enhanced_a2a_agent_json()
    
    # Only AFTER registering our enhanced routes, set up the agent's routes
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
    @app.route('/<path:path>')
    def catch_all(path):
        # Only for GET requests that didn't match other routes
        if request.method == 'GET':
            # Redirect to the A2A index
            return enhanced_a2a_index()
    
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