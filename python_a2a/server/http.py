"""
HTTP server implementation for the A2A protocol.
"""

import json
import traceback
import time
import threading
import asyncio
from queue import Queue, Empty
from typing import Type, Optional, Dict, Any, Callable, Union

try:
    from flask import Flask, request, jsonify, Response, render_template_string, make_response
except ImportError:
    Flask = None

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent, ErrorContent
from .base import BaseA2AServer
from ..exceptions import A2AImportError, A2ARequestError, A2AStreamingError
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
            # Include Google A2A compatibility flag if available
            capabilities = {}
            if hasattr(agent, 'agent_card') and hasattr(agent.agent_card, 'capabilities'):
                capabilities = agent.agent_card.capabilities
            elif hasattr(agent, '_use_google_a2a'):
                capabilities = {
                    "google_a2a_compatible": getattr(agent, '_use_google_a2a', False),
                    "parts_array_format": getattr(agent, '_use_google_a2a', False)
                }
                
            return jsonify({
                "name": agent.agent_card.name if hasattr(agent, 'agent_card') else "A2A Agent",
                "description": agent.agent_card.description if hasattr(agent, 'agent_card') else "",
                "agent_card_url": "/a2a/agent.json",
                "protocol": "a2a",
                "capabilities": capabilities
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
        
        # Add Google A2A compatibility flag if available
        if hasattr(agent, '_use_google_a2a'):
            if "capabilities" not in agent_data:
                agent_data["capabilities"] = {}
            agent_data["capabilities"]["google_a2a_compatible"] = getattr(agent, '_use_google_a2a', False)
            agent_data["capabilities"]["parts_array_format"] = getattr(agent, '_use_google_a2a', False)
        
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
    
    # Critical: Register the streaming route if the agent supports streaming
    @app.route("/stream", methods=["POST"])
    def handle_streaming_request():
        """
        Handle streaming requests.
        
        This endpoint enables Server-Sent Events (SSE) streaming from the agent.
        It uses the agent's stream_response method if it implements it.
        """
        try:
            # CORS for streaming - important for browser compatibility
            if request.method == 'OPTIONS':
                response = Response()
                response.headers['Access-Control-Allow-Origin'] = '*'
                response.headers['Access-Control-Allow-Methods'] = 'POST'
                response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
                return response
            
            # Check accept header for streaming support
            accept_header = request.headers.get('Accept', '')
            supports_sse = 'text/event-stream' in accept_header
            
            # Debug logging
            print(f"Streaming request received with Accept: {accept_header}")
            print(f"Request supports SSE: {supports_sse}")
            
            # Extract the message from the request
            data = request.json
            
            # Debug logging for request data
            print(f"Streaming request data: {json.dumps(data)[:500]}")
            
            # Check if this is a direct message or wrapped
            if "message" in data and isinstance(data["message"], dict):
                message = Message.from_dict(data["message"])
            else:
                # Try parsing the entire request as a message
                message = Message.from_dict(data)
            
            # Debug logging for message
            print(f"Extracted message: {message.content}")
            
            # Check if the agent supports streaming
            if not hasattr(agent, 'stream_response'):
                error_msg = "This agent does not support streaming"
                print(f"Error: {error_msg}")
                return jsonify({"error": error_msg}), 405
            
            # Check if stream_response is implemented (not just inherited)
            if agent.stream_response == BaseA2AServer.stream_response:
                error_msg = "This agent inherits but does not implement stream_response"
                print(f"Error: {error_msg}")
                return jsonify({"error": error_msg}), 501
            
            # Set up SSE streaming response
            def generate():
                """Generator for streaming server-sent events."""
                # Create a thread and asyncio event loop for streaming
                queue = Queue()
                done_event = threading.Event()
                
                def run_async_stream():
                    """Run the async stream in a dedicated thread with its own event loop."""
                    async def process_stream():
                        """Process the streaming response."""
                        try:
                            print("Starting streaming process")
                            # Get the stream generator from the agent
                            # Note: stream_response returns an async generator, not an awaitable
                            stream_gen = agent.stream_response(message)
                            
                            # First heartbeat is sent from outside this function
                            
                            # Process each chunk
                            index = 0
                            async for chunk in stream_gen:
                                print(f"Received chunk from agent: {chunk}")
                                
                                # Create chunk object with metadata
                                chunk_data = {
                                    "content": chunk,
                                    "index": index,
                                    "append": True
                                }
                                
                                # Put in queue
                                queue.put(chunk_data)
                                print(f"Put chunk {index} in queue")
                                index += 1
                            
                            # Signal completion
                            queue.put({
                                "content": "",
                                "index": index,
                                "append": True,
                                "lastChunk": True
                            })
                            print(f"Streaming complete, signaling with lastChunk")
                            
                        except Exception as e:
                            # Log the error
                            print(f"Error in streaming process: {str(e)}")
                            traceback.print_exc()
                            
                            # Put error in queue
                            queue.put({"error": str(e)})
                            
                        finally:
                            # Signal we're done
                            done_event.set()
                            print("Set done_event")
                    
                    # Create a new event loop for this thread
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    
                    # Run the streaming process
                    try:
                        print("Starting async streaming thread")
                        loop.run_until_complete(process_stream())
                    except Exception as e:
                        print(f"Exception in async thread: {e}")
                        traceback.print_exc()
                    finally:
                        loop.close()
                        print("Closed async loop")
                
                # Start the streaming thread
                thread = threading.Thread(target=run_async_stream)
                thread.daemon = True
                thread.start()
                print("Started streaming thread")
                
                # Yield initial SSE comment to establish connection
                yield f": SSE stream established\n\n"
                
                # Process queue items until done
                timeout = time.time() + 60  # 60-second timeout
                
                total_chunks = 0
                
                while not done_event.is_set() and time.time() < timeout:
                    try:
                        # Check if we have a chunk in the queue
                        if not queue.empty():
                            chunk = queue.get(block=False)
                            total_chunks += 1
                            
                            # Check if it's an error
                            if "error" in chunk:
                                error_event = f"event: error\ndata: {json.dumps(chunk)}\n\n"
                                print(f"Yielding error event: {error_event}")
                                yield error_event
                                break
                            
                            # Format as SSE event with proper newlines
                            data_event = f"data: {json.dumps(chunk)}\n\n"
                            print(f"Yielding data event #{total_chunks}")
                            yield data_event
                            
                            # Check if it's the last chunk
                            if chunk.get("lastChunk", False):
                                print("Last chunk detected, ending stream")
                                break
                        else:
                            # No data yet, sleep briefly
                            time.sleep(0.01)
                    except Empty:
                        # Queue was empty
                        time.sleep(0.01)
                    except Exception as e:
                        # Other error
                        print(f"Error in queue processing: {e}")
                        error_event = f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"
                        yield error_event
                        break
                
                # If timed out, send timeout error
                if time.time() >= timeout and not done_event.is_set():
                    error_event = f"event: error\ndata: {json.dumps({'error': 'Streaming timed out'})}\n\n"
                    print("Stream timed out")
                    yield error_event
                
                print(f"Stream complete - yielded {total_chunks} chunks")
            
            # Create the streaming response
            response = Response(generate(), mimetype="text/event-stream")
            response.headers["Cache-Control"] = "no-cache"
            response.headers["Connection"] = "keep-alive"
            response.headers["X-Accel-Buffering"] = "no"  # Important for Nginx
            return response
            
        except Exception as e:
            # Log the exception
            print(f"Exception in streaming request handler: {str(e)}")
            traceback.print_exc()
            
            # Return error response for any other exception
            return jsonify({"error": str(e)}), 500
    
    # Only AFTER registering our enhanced routes, set up the agent's routes
    if hasattr(agent, 'setup_routes'):
        agent.setup_routes(app)
    
    # Legacy routes for backward compatibility
    @app.route("/a2a", methods=["POST"])
    def handle_a2a_request() -> Union[Response, tuple]:
        """Handle A2A protocol requests"""
        try:
            data = request.json
            
            # Detect if this is Google A2A format
            is_google_format = False
            if "parts" in data and "role" in data and not "content" in data:
                is_google_format = True
            elif "messages" in data and data["messages"] and "parts" in data["messages"][0] and "role" in data["messages"][0]:
                is_google_format = True
            
            # Check if this is a single message or a conversation
            if "messages" in data:
                # This is a conversation
                if is_google_format:
                    conversation = Conversation.from_google_a2a(data)
                else:
                    conversation = Conversation.from_dict(data)
                
                response = agent.handle_conversation(conversation)
                
                # Format response based on request format or agent preference
                use_google_format = is_google_format
                if hasattr(agent, '_use_google_a2a'):
                    use_google_format = use_google_format or agent._use_google_a2a
                
                if use_google_format:
                    return jsonify(response.to_google_a2a())
                else:
                    return jsonify(response.to_dict())
            else:
                # This is a single message
                if is_google_format:
                    message = Message.from_google_a2a(data)
                else:
                    message = Message.from_dict(data)
                
                response = agent.handle_message(message)
                
                # Format response based on request format or agent preference
                use_google_format = is_google_format
                if hasattr(agent, '_use_google_a2a'):
                    use_google_format = use_google_format or agent._use_google_a2a
                
                if use_google_format:
                    return jsonify(response.to_google_a2a())
                else:
                    return jsonify(response.to_dict())
                
        except Exception as e:
            # Determine response format based on request
            is_google_format = False
            if 'data' in locals():
                if isinstance(data, dict):
                    if "parts" in data and "role" in data and not "content" in data:
                        is_google_format = True
                    elif "messages" in data and data["messages"] and "parts" in data["messages"][0] and "role" in data["messages"][0]:
                        is_google_format = True
            
            # Also consider agent preference
            if hasattr(agent, '_use_google_a2a'):
                is_google_format = is_google_format or agent._use_google_a2a
            
            # Return error in appropriate format
            error_msg = f"Error processing request: {str(e)}"
            if is_google_format:
                # Google A2A format
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
                # python_a2a format
                return jsonify({
                    "content": {
                        "type": "error",
                        "message": error_msg
                    },
                    "role": "system"
                }), 500
    
    @app.route("/a2a/metadata", methods=["GET"])
    def get_agent_metadata() -> Response:
        """Return metadata about the agent"""
        metadata = agent.get_metadata()
        
        # Add Google A2A compatibility flag if available
        if hasattr(agent, '_use_google_a2a'):
            metadata["google_a2a_compatible"] = getattr(agent, '_use_google_a2a', False)
            metadata["parts_array_format"] = getattr(agent, '_use_google_a2a', False)
            
        return jsonify(metadata)
    
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
    
    # Add info about Google A2A compatibility if available
    if hasattr(agent, '_use_google_a2a'):
        google_compat = getattr(agent, '_use_google_a2a', False)
        print(f"Google A2A compatibility: {'Enabled' if google_compat else 'Disabled'}")
        
    app.run(host=host, port=port, debug=debug)