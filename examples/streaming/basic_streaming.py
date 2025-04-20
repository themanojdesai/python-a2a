#!/usr/bin/env python
"""
Basic Streaming Example

This example demonstrates how to use streaming capabilities to receive
real-time responses from A2A agents that support streaming.

The example:
- Sets up a streaming-capable agent on a local server
- Uses a streaming client to process streamed chunks as they arrive
- Displays real-time progress with a visual indicator

To run:
    python basic_streaming.py [--query QUESTION]

Requirements:
    pip install "python-a2a[all]"
"""

import sys
import argparse
import asyncio
import threading
import time
import socket
import random
from flask import Flask, request, jsonify, Response
import json

from python_a2a import (
    A2AServer, A2AClient, AgentCard, AgentSkill,
    Message, TextContent, MessageRole,
    Task, TaskStatus, TaskState
)

# Import necessary components - using A2AClient instead of abstract StreamingClient
try:
    # Try to use aiohttp if available (needed for true streaming)
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False
    print("Warning: aiohttp not installed. Streaming visualization will be simulated.")
    print("Install aiohttp with: pip install aiohttp")


class StreamingAgent(A2AServer):
    """
    A simple agent that supports streaming responses.
    
    This agent simulates a streaming response by sending text
    chunks with deliberate delays to create a realistic streaming effect.
    """
    
    def __init__(self):
        """Initialize the streaming agent with appropriate capabilities."""
        agent_card = AgentCard(
            name="Streaming Agent",
            description="An agent that supports streaming responses",
            url="http://localhost:0",  # Will be updated later
            version="1.0.0",
            capabilities={"streaming": True},  # Mark as streaming-capable
            skills=[
                AgentSkill(
                    name="Streaming Response",
                    description="Generate responses with streaming output",
                    tags=["streaming"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message):
        """Handle a message request with a complete response."""
        # Extract the query from the message
        query = ""
        if hasattr(message.content, "text"):
            query = message.content.text
        
        # Generate a complete response
        response_text = self._generate_response(query)
        
        # Create response message
        response = Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            message_id=f"response-{time.time()}",
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
        
        return response
    
    def handle_task(self, task):
        """Handle a task by providing a non-streaming response."""
        # Extract query from task
        query = self._extract_query(task)
        
        # Generate complete response
        response_text = self._generate_response(query)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": response_text}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_query(self, task):
        """Extract the query text from a task."""
        if task.message:
            if isinstance(task.message, dict):
                content = task.message.get("content", {})
                if isinstance(content, dict):
                    return content.get("text", "")
        return ""
    
    def _generate_response(self, query):
        """Generate a complete response to the query."""
        query = query.lower()
        
        if "hello" in query or "hi" in query:
            return "Hello! I'm a streaming-capable agent. I can respond to your questions in real-time, sending each part of my response as soon as it's ready."
            
        elif "weather" in query:
            return "The weather today is sunny with some scattered clouds. Temperature is around 22°C (72°F) with a light breeze from the west. There's a small chance of rain in the evening, but overall it should be a pleasant day."
            
        elif "help" in query:
            return "I'm a streaming-capable agent that demonstrates how the A2A streaming protocol works. You can ask me various questions and I'll respond in a streaming fashion, sending my response chunk by chunk. Try asking about the weather, streaming capabilities, or any general knowledge question!"
            
        elif "stream" in query or "streaming" in query:
            return "Streaming in the A2A protocol allows agents to send responses incrementally as they're generated, rather than waiting for the complete response to be ready. This provides a more interactive experience, especially for longer responses or when the response generation takes time. The streaming capabilities in Python A2A make it easy to consume these streaming responses."
            
        else:
            # Default response for any other query
            return (
                "I received your query and I'm responding with a streaming response. "
                "This means my answer is being sent to you piece by piece, as soon as each fragment is ready. "
                "Streaming is particularly useful for long-form content, allowing you to start reading "
                "the beginning of the response while I'm still generating the rest. "
                "This creates a more interactive and responsive experience. "
                "The Python A2A library handles all the complexity of managing the streaming connection, "
                "so developers can focus on creating great agent experiences. "
                "In this example, you'll see chunks arriving with deliberate delays to simulate "
                "the streaming experience. In a real application with actual language models, "
                "the chunks would arrive as the model generates them."
            )


def start_streaming_server(agent, port, ready_event=None):
    """Start a server that supports streaming on a specific port."""
    app = Flask(__name__)
    
    # Update the agent's URL to include the actual port
    agent.agent_card.url = f"http://localhost:{port}"
    
    @app.route('/agent.json', methods=['GET'])
    def get_agent_card():
        """Return the agent card information."""
        return jsonify(agent.agent_card.to_dict())
    
    @app.route('/a2a/agent.json', methods=['GET'])
    def get_a2a_agent_card():
        """Return the agent card at the alternate endpoint."""
        return jsonify(agent.agent_card.to_dict())
    
    @app.route('/', methods=['POST'])
    def handle_message():
        """Handle standard message requests."""
        try:
            # Extract the request data
            data = request.json
            
            # Check what type of request this is
            if isinstance(data, dict) and "message" in data:
                # This is a message request
                message = Message.from_dict(data["message"])
                
                # Process the message
                response = agent.handle_message(message)
                
                # Return the response
                return jsonify(response.to_dict())
                
            elif isinstance(data, dict) and "id" in data:
                # This is a Task request
                task = Task.from_dict(data)
                
                # Process the task
                result = agent.handle_task(task)
                
                # Return the result
                return jsonify(result.to_dict())
                
            else:
                # Create a message from the raw data
                if isinstance(data, dict):
                    content = data.get("content", {})
                    if isinstance(content, dict):
                        text = content.get("text", "")
                    else:
                        text = str(content)
                else:
                    text = str(data)
                
                message = Message(
                    content=TextContent(text=text),
                    role=MessageRole.USER
                )
                
                # Process the message
                response = agent.handle_message(message)
                
                # Return the response
                return jsonify(response.to_dict())
        
        except Exception as e:
            # If there's an error, return it
            return jsonify({"error": str(e)}), 400
    
    @app.route('/stream', methods=['POST'])
    def handle_streaming():
        """Handle streaming requests."""
        try:
            # Extract the request data
            data = request.json
            
            # Get the message
            if "message" in data:
                if isinstance(data["message"], dict):
                    message = Message.from_dict(data["message"])
                else:
                    message = Message(
                        content=TextContent(text=str(data["message"])),
                        role=MessageRole.USER
                    )
            else:
                # Create a default message
                message = Message(
                    content=TextContent(text="Default query"),
                    role=MessageRole.USER
                )
            
            # Get the query text
            query = ""
            if hasattr(message.content, "text"):
                query = message.content.text
            
            # Generate a full response
            full_response = agent._generate_response(query)
            
            # Simulate streaming by breaking it into chunks with delays
            def generate():
                # Break the response into words
                words = full_response.split()
                current_chunk = []
                
                # Send words in small chunks with random delays
                for word in words:
                    current_chunk.append(word)
                    
                    # Every 3-7 words (randomized for realism), send a chunk
                    if len(current_chunk) >= random.randint(3, 7):
                        chunk_text = " ".join(current_chunk)
                        
                        # Format as server-sent event
                        data_obj = {"text": chunk_text}
                        yield f"data: {json.dumps(data_obj)}\n\n"
                        
                        # Reset for next chunk
                        current_chunk = []
                        
                        # Add a small delay to simulate typing or thinking
                        time.sleep(random.uniform(0.2, 0.5))
                
                # Send any remaining words
                if current_chunk:
                    chunk_text = " ".join(current_chunk)
                    data_obj = {"text": chunk_text}
                    yield f"data: {json.dumps(data_obj)}\n\n"
            
            # Return streaming response
            return Response(generate(), content_type='text/event-stream')
            
        except Exception as e:
            # If there's an error, return it
            return jsonify({"error": str(e)}), 400
    
    # Signal that we're ready to start
    if ready_event:
        ready_event.set()
    
    # Start the server
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


class EnhancedClient(A2AClient):
    """
    Enhanced client with streaming capabilities.
    
    This extends the standard A2AClient with basic streaming support
    without requiring the abstract StreamingClient.
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    async def check_streaming_support(self):
        """Check if the agent supports streaming capabilities."""
        # If aiohttp is not available, we can't do true streaming
        if not HAS_AIOHTTP:
            return False
            
        try:
            # Try to fetch the agent card to check capabilities
            async with aiohttp.ClientSession() as session:
                # Try the primary endpoint
                async with session.get(f"{self.url}/agent.json") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check capabilities
                        return (
                            isinstance(data, dict) and
                            isinstance(data.get("capabilities"), dict) and
                            data.get("capabilities", {}).get("streaming", False)
                        )
                
                # Try the alternate endpoint
                async with session.get(f"{self.url}/a2a/agent.json") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check capabilities
                        return (
                            isinstance(data, dict) and
                            isinstance(data.get("capabilities"), dict) and
                            data.get("capabilities", {}).get("streaming", False)
                        )
            
            return False
        except Exception:
            return False
    
    async def stream_response(self, message, chunk_callback=None):
        """
        Stream a response from the agent.
        
        Args:
            message: Message to send
            chunk_callback: Function to call for each chunk
            
        Yields:
            Response chunks as they arrive
        """
        if not HAS_AIOHTTP:
            # If aiohttp is not available, simulate streaming with the full response
            async for chunk in self._simulate_streaming(message, chunk_callback):
                yield chunk
            return
        
        # Check if streaming is supported
        supports_streaming = await self.check_streaming_support()
        
        if not supports_streaming:
            # Fall back to non-streaming for non-streaming agents
            async for chunk in self._simulate_streaming(message, chunk_callback):
                yield chunk
            return
        
        try:
            # Set up headers for streaming
            headers = {"Content-Type": "application/json", "Accept": "text/event-stream"}
            
            # Create a session and send the request
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.url}/stream",
                    json={"message": message.to_dict()},
                    headers=headers
                ) as response:
                    # Handle errors
                    if response.status >= 400:
                        raise Exception(f"HTTP error {response.status}")
                    
                    # Process the streaming response
                    buffer = ""
                    async for chunk in response.content.iter_chunked(1024):
                        if not chunk:
                            continue
                            
                        # Decode chunk and add to buffer
                        chunk_text = chunk.decode('utf-8')
                        buffer += chunk_text
                        
                        # Process complete events
                        while "\n\n" in buffer:
                            event, buffer = buffer.split("\n\n", 1)
                            
                            # Extract data field
                            for line in event.split("\n"):
                                if line.startswith("data:"):
                                    data = line[5:].strip()
                                    
                                    try:
                                        # Try to parse as JSON
                                        data_obj = json.loads(data)
                                        if "text" in data_obj:
                                            # Extract text and process
                                            text = data_obj["text"]
                                            if chunk_callback:
                                                chunk_callback(text)
                                            yield text
                                    except json.JSONDecodeError:
                                        # Not JSON, yield raw data
                                        if chunk_callback:
                                            chunk_callback(data)
                                        yield data
        
        except Exception as e:
            # Fall back to simulated streaming on error
            error_msg = f"Streaming error (falling back to non-streaming): {str(e)}"
            if chunk_callback:
                chunk_callback(error_msg)
            async for chunk in self._simulate_streaming(message, chunk_callback):
                yield chunk
    
    async def _simulate_streaming(self, message, chunk_callback=None):
        """Simulate streaming using the full response."""
        # Get the full response
        response = self.send_message(message)
        
        # Extract text
        if hasattr(response.content, "text"):
            full_text = response.content.text
        else:
            full_text = str(response.content)
        
        # Break into words to simulate chunks
        words = full_text.split()
        
        # Create chunks of 5-10 words
        current_chunk = []
        for word in words:
            current_chunk.append(word)
            if len(current_chunk) >= random.randint(5, 10):
                # Join words into a chunk
                chunk_text = " ".join(current_chunk)
                
                # Process the chunk
                if chunk_callback:
                    chunk_callback(chunk_text)
                
                # Add a small delay to simulate network latency
                await asyncio.sleep(random.uniform(0.1, 0.3))
                
                # Yield the chunk
                yield chunk_text
                
                # Reset for next chunk
                current_chunk = []
        
        # Process any remaining words
        if current_chunk:
            chunk_text = " ".join(current_chunk)
            if chunk_callback:
                chunk_callback(chunk_text)
            yield chunk_text


def create_progress_bar(total_width=50):
    """Create a progress bar visualization function."""
    
    def display_progress(current, total):
        if total == 0:
            progress = 0
        else:
            progress = current / total
        
        filled_width = int(total_width * progress)
        empty_width = total_width - filled_width
        
        bar = "█" * filled_width + "░" * empty_width
        percent = int(progress * 100)
        
        return f"[{bar}] {percent}% ({current}/{total})"
    
    return display_progress


async def stream_with_progress(client, message):
    """Stream a response with a progress visualization."""
    total_chars = 0
    chunk_count = 0
    start_time = time.time()
    full_response = ""
    
    print("\nStreaming response:\n" + "-" * 60)
    
    # Create progress bar function
    progress_bar = create_progress_bar(40)
    
    # Function to handle each chunk
    def handle_chunk(chunk):
        nonlocal total_chars, chunk_count, full_response
        
        # Update counters
        total_chars += len(chunk)
        chunk_count += 1
        full_response += chunk
        
        # Calculate metrics
        elapsed = time.time() - start_time
        chars_per_sec = total_chars / elapsed if elapsed > 0 else 0
        
        # Print the new chunk
        print(chunk, end="", flush=True)
        
        # We don't know the total in advance, so we just show the current progress
        elapsed_str = f"{elapsed:.1f}s"
        rate_str = f"{chars_per_sec:.1f} chars/sec"
        
        # Clear the current line and print status on the second line
        # We store cursor position after content but before status line
        
    # Process the streaming response
    try:
        async for _ in client.stream_response(message, chunk_callback=handle_chunk):
            # Just process with the callback
            pass
        
        # Calculate final stats
        elapsed = time.time() - start_time
        chars_per_sec = total_chars / elapsed if elapsed > 0 else 0
        
        # Print final stats
        print("\n" + "-" * 60)
        print(f"Streaming complete:")
        print(f"- Total characters: {total_chars}")
        print(f"- Chunks received: {chunk_count}")
        print(f"- Time elapsed: {elapsed:.2f} seconds")
        print(f"- Average speed: {chars_per_sec:.1f} characters/second")
        
        return full_response
        
    except Exception as e:
        print(f"\nError during streaming: {e}")
        return None


async def visualize_streaming(client, message):
    """Stream a response with visual chunk indicators."""
    chunk_count = 0
    total_chars = 0
    received_chunks = []
    start_time = time.time()
    
    print("\nStreaming response with chunk visualization:")
    print("-" * 60)
    
    # Function to handle each chunk with visual indicators
    def handle_chunk(chunk):
        nonlocal chunk_count, total_chars
        chunk_count += 1
        total_chars += len(chunk)
        received_chunks.append(chunk)
        
        # Print chunk with a visual indicator
        print(f"\n[Chunk {chunk_count}] ", end="")
        print(chunk, end="")
        
        # Print chunk size and timing information
        elapsed = time.time() - start_time
        print(f" ({len(chunk)} chars, +{elapsed:.2f}s)", end="", flush=True)
    
    # Process the streaming response
    try:
        async for _ in client.stream_response(message, chunk_callback=handle_chunk):
            # Just process with the callback
            pass
        
        # Calculate final stats
        elapsed = time.time() - start_time
        chars_per_sec = total_chars / elapsed if elapsed > 0 else 0
        
        # Combine all chunks into the full response
        full_response = "".join(received_chunks)
        
        # Print final stats
        print("\n" + "-" * 60)
        print(f"Streaming complete:")
        print(f"- Total characters: {total_chars}")
        print(f"- Chunks received: {chunk_count}")
        print(f"- Time elapsed: {elapsed:.2f} seconds")
        print(f"- Average speed: {chars_per_sec:.1f} characters/second")
        
        return full_response
        
    except Exception as e:
        print(f"\nError during streaming: {e}")
        return None


def main():
    """Run the streaming example."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Basic Streaming Example")
    parser.add_argument("--query", type=str, default="Tell me about streaming in the A2A protocol.",
                      help="Query to send to the streaming agent")
    parser.add_argument("--mode", choices=["simple", "visualize"], default="simple",
                      help="Streaming display mode: simple (continuous) or visualize (chunk by chunk)")
    args = parser.parse_args()
    
    print("=== Basic Streaming Example ===\n")
    print("This example demonstrates:")
    print("1. Setting up a streaming-capable agent")
    print("2. Using a streaming client to receive incremental responses")
    print("3. Processing streaming responses in real-time\n")
    
    # Find available port
    port = find_free_port()
    
    # Create streaming agent
    agent = StreamingAgent()
    agent.agent_card.url = f"http://localhost:{port}"
    
    # Event to signal when server is ready
    ready_event = threading.Event()
    
    # Start agent server in background thread
    print(f"Starting streaming agent server on port {port}...")
    server_thread = threading.Thread(
        target=start_streaming_server,
        args=(agent, port, ready_event),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to be ready
    ready_event.wait(timeout=5.0)
    print(f"✓ Streaming agent ready at http://localhost:{port}")
    
    # Create enhanced client with streaming capabilities instead of StreamingClient
    client = EnhancedClient(f"http://localhost:{port}")
    
    # Create message with query
    message = Message(
        content=TextContent(text=args.query),
        role=MessageRole.USER
    )
    
    print(f"\nSending query: '{args.query}'")
    
    # Run the streaming request using asyncio
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        # No event loop in thread, create one
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # Check if streaming is supported
        supports_streaming = loop.run_until_complete(client.check_streaming_support())
        
        if supports_streaming:
            print("✓ Agent supports streaming responses")
            
            # Choose streaming mode based on argument
            if args.mode == "visualize":
                loop.run_until_complete(visualize_streaming(client, message))
            else:
                loop.run_until_complete(stream_with_progress(client, message))
            
        else:
            print("✓ Agent supports simulated streaming")
            print("Falling back to simulated streaming mode...")
            
            # Use simulated streaming
            if args.mode == "visualize":
                loop.run_until_complete(visualize_streaming(client, message))
            else:
                loop.run_until_complete(stream_with_progress(client, message))
    
    except KeyboardInterrupt:
        print("\nStreaming interrupted by user")
    except Exception as e:
        print(f"\nError during streaming: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())