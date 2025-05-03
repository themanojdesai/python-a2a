#!/usr/bin/env python
"""
basic_streaming.py - Minimal A2A Streaming Example

This example demonstrates the simplest implementation of A2A streaming.
It creates a minimal streaming server and client to show the bare essentials
needed to implement streaming in the A2A protocol.

Key concepts demonstrated:
- Setting up a streaming-capable A2A server
- Implementing the stream_response protocol method
- Using StreamingClient to consume streamed responses
- Handling both string and dictionary chunk formats

Usage:
    python basic_streaming.py [--port PORT] [--query "Your question"]
"""

import asyncio
import time
import random
import threading
import argparse
from typing import AsyncGenerator

# Import python_a2a components
from python_a2a import (
    BaseA2AServer, AgentCard, Message, TextContent, MessageRole, run_server
)
from python_a2a.client.streaming import StreamingClient

# ANSI colors for prettier output
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RED = "\033[31m"
RESET = "\033[0m"

# Default configuration
DEFAULT_QUERY = "Tell me about streaming in A2A"
DEFAULT_PORT = 8000


class MinimalStreamingServer(BaseA2AServer):
    """
    Minimal streaming server implementation.
    
    This server demonstrates the bare minimum needed to support
    streaming in an A2A-compatible agent.
    """
    
    def __init__(self, url: str = "http://localhost:8000"):
        """
        Initialize the streaming server.
        
        Args:
            url: The server URL
        """
        # Create an agent card with streaming capability
        self.agent_card = AgentCard(
            name="Minimal A2A Streaming Demo",
            description="A minimal example of streaming in the A2A protocol",
            url=url,
            version="1.0.0",
            capabilities={"streaming": True}  # Mark as streaming-capable
        )
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle standard (non-streaming) message requests.
        
        Args:
            message: The incoming message
            
        Returns:
            The response message
        """
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Generate complete response
        response_text = (
            f"This is a non-streaming response. For streaming, use the /stream endpoint. "
            f"Your query was: '{query}'"
        )
        
        print(f"[Server] Non-streaming response generated ({len(response_text)} chars)")
        
        # Return as a complete message
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """
        Stream a response chunk by chunk.
        
        This is the key protocol method for streaming support.
        It yields chunks of the response with simulated delays.
        
        Args:
            message: The incoming message
            
        Yields:
            Chunks of the response text
        """
        print(f"[Server] Streaming request received")
        
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        print(f"[Server] Query: {query}")
        
        # Create a simple response in sections
        sections = [
            "A2A streaming enables real-time content delivery as it's generated. ",
            "This creates a more natural conversational experience. ",
            "You're seeing this right now - each section appears with a small delay. ",
            "Implementation requires two key components: ",
            "1. Server-side: Implement stream_response async generator method ",
            "2. Client-side: Use StreamingClient to process chunks as they arrive. ",
            "That's all you need for basic streaming!"
        ]
        
        # Stream each section with a delay
        for i, section in enumerate(sections):
            # Add a thinking delay
            await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Log the chunk (for demonstration)
            print(f"[Server] Streaming chunk {i+1}/{len(sections)} ({len(section)} chars)")
            
            # Yield the section as a chunk
            yield section
        
        print(f"[Server] Streaming complete: {len(sections)} chunks sent")


async def run_streaming_client(server_url: str, query: str):
    """
    Demonstrate a streaming client.
    
    Args:
        server_url: URL of the A2A server
        query: The query to send
    """
    print(f"\n{BLUE}Query: \"{query}\"{RESET}")
    print(f"\n{BLUE}Streaming response:{RESET}")
    print("-" * 60)
    
    # Create message with required role
    message = Message(
        content=TextContent(text=query),
        role=MessageRole.USER
    )
    
    # Create streaming client
    streaming_client = StreamingClient(server_url)
    
    # Process streaming response
    start_time = time.time()
    total_chunks = 0
    total_chars = 0
    
    try:
        # Stream the response
        async for chunk in streaming_client.stream_response(message):
            total_chunks += 1
            
            # Handle various chunk formats (important for different A2A implementations)
            if isinstance(chunk, dict):
                if "content" in chunk:
                    text = chunk["content"]
                elif "text" in chunk:
                    text = chunk["text"]
                else:
                    # Try to convert dict to string
                    try:
                        import json
                        text = json.dumps(chunk)
                    except:
                        text = str(chunk)
            else:
                text = str(chunk)
            
            # Update total chars
            total_chars += len(text)
            
            # Print the chunk
            print(text, end="", flush=True)
        
        # Calculate time
        elapsed = time.time() - start_time
        
        print("\n" + "-" * 60)
        print(f"{GREEN}Received {total_chunks} chunks ({total_chars} characters) in {elapsed:.2f} seconds{RESET}")
        
    except Exception as e:
        print(f"\n\n{RED}Error during streaming: {str(e)}{RESET}")


def find_free_port():
    """Find an available port on localhost."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


async def main_async(args):
    """
    Main async function.
    
    Args:
        args: Command line arguments
    """
    # Get port
    port = args.port or find_free_port()
    server_url = f"http://localhost:{port}"
    
    # Create server
    server = MinimalStreamingServer(server_url)
    
    # Start server in background thread
    print(f"{BLUE}Starting streaming server on port {port}...{RESET}")
    server_thread = threading.Thread(
        target=lambda: run_server(server, host="localhost", port=port),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    # Run the streaming client
    await run_streaming_client(server_url, args.query)


def main():
    """Parse arguments and run the example."""
    parser = argparse.ArgumentParser(description="Minimal A2A Streaming Example")
    parser.add_argument("--query", default=DEFAULT_QUERY,
                       help="Query to send to the agent")
    parser.add_argument("--port", type=int, default=None,
                       help="Port to run the server on (will find a free port if not specified)")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print(f"\n{BLUE}Exiting{RESET}")


if __name__ == "__main__":
    main()