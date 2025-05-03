#!/usr/bin/env python
"""
01_basic_streaming.py - Basic A2A Streaming Example

This example demonstrates the fundamentals of streaming in the A2A protocol.
It creates a simple streaming server and client that communicate in real-time,
showing the key concepts of streaming with minimal complexity.

Key concepts demonstrated:
- Creating a streaming-capable A2A server
- Implementing the stream_response protocol method
- Using StreamingClient to receive streamed responses
- Comparing streamed vs. non-streamed responses

Usage:
    python 01_basic_streaming.py [--port PORT] [--query "Your question"]
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
from python_a2a.client.http import A2AClient

# ANSI colors for prettier output
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RED = "\033[31m"
RESET = "\033[0m"

# Default configuration
DEFAULT_QUERY = "Tell me about streaming in the A2A protocol"


class BasicStreamingServer(BaseA2AServer):
    """
    A simple server that implements streaming capabilities.
    
    This server demonstrates the minimum requirements for supporting
    streaming in an A2A-compatible agent: implementing the stream_response
    protocol method.
    """
    
    def __init__(self, url: str = "http://localhost:8000"):
        """
        Initialize the streaming server.
        
        Args:
            url: The server URL
        """
        # Create an agent card with streaming capability
        self.agent_card = AgentCard(
            name="Basic A2A Streaming Demo",
            description="A simple example of streaming in the A2A protocol",
            url=url,
            version="1.0.0",
            capabilities={"streaming": True}  # Mark as streaming-capable
        )
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle standard (non-streaming) message requests.
        
        This method is called for regular (non-streaming) requests.
        It returns the entire response as a single message.
        
        Args:
            message: The incoming message
            
        Returns:
            The response message
        """
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Generate complete response
        response_text = self._generate_response(query)
        
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
        
        This is the key protocol method for streaming support. It yields
        chunks of the response with simulated thinking delays, allowing
        for real-time delivery of content.
        
        Args:
            message: The incoming message
            
        Yields:
            Chunks of the response text
        """
        print(f"[Server] Streaming request received: {message.content.text[:50]}...")
        
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Generate the complete response
        full_response = self._generate_response(query)
        
        # Split into sentences for more natural chunking
        sentences = []
        for part in full_response.replace(". ", ".|").replace("? ", "?|").replace("! ", "!|").split("|"):
            if part:
                sentences.append(part + (" " if not part.endswith((".", "?", "!")) else ""))
        
        print(f"[Server] Ready to stream {len(sentences)} chunks")
        
        # Yield each sentence with a simulated thinking delay
        for i, sentence in enumerate(sentences):
            # Add a thinking delay
            await asyncio.sleep(random.uniform(0.3, 0.7))
            
            # Log the chunk (for demonstration)
            print(f"[Server] Streaming chunk {i+1}/{len(sentences)} ({len(sentence)} chars)")
            
            # Yield the sentence as a chunk
            yield sentence
        
        print(f"[Server] Streaming complete: {len(sentences)} chunks sent")
    
    def _generate_response(self, query: str) -> str:
        """
        Generate a response based on the query.
        
        Args:
            query: The query text
            
        Returns:
            The response text
        """
        # Simple keyword-based responses
        query = query.lower()
        
        if "streaming" in query and ("a2a" in query or "protocol" in query):
            return (
                "Streaming in the A2A protocol allows for real-time delivery of content as it's generated. "
                "Instead of waiting for the entire response to be ready, the server sends chunks as soon as they're available. "
                "This creates a more natural and interactive experience, similar to how humans communicate. "
                "The protocol uses Server-Sent Events (SSE) to deliver chunks with metadata like append flags and completion indicators. "
                "This improves the perceived responsiveness of AI systems, especially for longer outputs. "
                "Implementation requires adding a stream_response method to your server and using StreamingClient on the client side."
            )
        elif "streaming" in query:
            return (
                "Streaming allows content to be sent incrementally as it's generated, rather than all at once. "
                "This creates a more natural user experience, especially for longer responses. "
                "You're seeing this right now - I'm sending this response sentence by sentence with small delays between each one. "
                "Notice how the text appears gradually, as if someone were typing it out in real-time. "
                "This approach feels more interactive and reduces perceived latency, making the interaction feel more conversational. "
                "Streaming is particularly valuable for AI-generated content, where generation can take time."
            )
        else:
            return (
                "This is a basic demonstration of streaming in the A2A protocol. "
                "As you can see, the response is being delivered in chunks rather than all at once. "
                "Each sentence appears after a short delay, simulating real-time generation. "
                "This creates a more dynamic and engaging experience compared to waiting for the entire response. "
                "Try asking specifically about 'streaming in the A2A protocol' to learn more about how it works. "
                "You can also compare streaming to non-streaming responses to see the difference in user experience."
            )


def find_free_port():
    """Find an available port on localhost."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


async def run_streaming_demo(server_url: str, query: str):
    """
    Demonstrate both streaming and non-streaming requests to the same server.
    
    Args:
        server_url: URL of the A2A server
        query: The query to send
    """
    print(f"\n{BLUE}Query: \"{query}\"{RESET}")
    
    # Create message
    message = Message(
        content=TextContent(text=query),
        role=MessageRole.USER
    )
    
    # First demonstrate standard (non-streaming) request
    print(f"\n{BLUE}Standard (non-streaming) request:{RESET}")
    print("-" * 60)
    
    start_time = time.time()
    
    # Create standard client
    standard_client = A2AClient(server_url)
    
    # Send non-streaming request
    response = standard_client.send_message(message)
    
    # Calculate time
    elapsed = time.time() - start_time
    
    # Display response
    if hasattr(response.content, "text"):
        print(response.content.text)
    else:
        print(str(response.content))
    
    print("-" * 60)
    print(f"{BLUE}Non-streaming response received in {elapsed:.2f} seconds{RESET}")
    
    # Now demonstrate streaming request
    print(f"\n{BLUE}Streaming request:{RESET}")
    print("-" * 60)
    
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
            
            # Extract text content (could be string or dict)
            if isinstance(chunk, dict):
                if "content" in chunk:
                    text = chunk["content"]
                elif "text" in chunk:
                    text = chunk["text"]
                else:
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
        
        # Calculate approximate typing speed
        if elapsed > 0:
            chars_per_sec = total_chars / elapsed
            print(f"{GREEN}Effective typing speed: {chars_per_sec:.1f} characters/second{RESET}")
        
    except Exception as e:
        print(f"\n\n{RED}Error during streaming: {str(e)}{RESET}")


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
    server = BasicStreamingServer(server_url)
    
    # Start server in background thread
    print(f"{BLUE}Starting streaming server on port {port}...{RESET}")
    server_thread = threading.Thread(
        target=lambda: run_server(server, host="localhost", port=port),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    # Run the streaming demo
    await run_streaming_demo(server_url, args.query)
    
    # Interactive mode if requested
    if args.interactive:
        try:
            while True:
                print(f"\n{BLUE}Enter a query (or Ctrl+C to exit):{RESET}")
                next_query = input("> ")
                if next_query.strip():
                    await run_streaming_demo(server_url, next_query)
                else:
                    print(f"{YELLOW}Query cannot be empty{RESET}")
        except KeyboardInterrupt:
            print(f"\n{BLUE}Exiting interactive mode{RESET}")


def main():
    """Parse arguments and run the example."""
    parser = argparse.ArgumentParser(description="Basic A2A Streaming Example")
    parser.add_argument("--query", default=DEFAULT_QUERY,
                       help="Query to send to the agent")
    parser.add_argument("--port", type=int, default=None,
                       help="Port to run the server on (will find a free port if not specified)")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Enable interactive mode after initial query")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print(f"\n{BLUE}Exiting{RESET}")


if __name__ == "__main__":
    main()