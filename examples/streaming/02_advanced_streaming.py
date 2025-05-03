#!/usr/bin/env python
"""
02_advanced_streaming.py - Advanced A2A Streaming Example

This example demonstrates more advanced streaming capabilities in the
A2A protocol, including metrics tracking, progress visualization,
chunking strategies, and error handling during streaming.

Key concepts demonstrated:
- Advanced streaming with metrics and visualization
- Different chunking strategies for natural streaming
- Real-time stream progress tracking
- Error handling in streaming contexts

Usage:
    python 02_advanced_streaming.py [options]
    
Options:
    --port PORT       Set the server port (default: auto-selected)
    --query QUERY     Initial query to send
    --delay DELAY     Simulated thinking delay (default: medium)
    --style STYLE     Chunking style: word|sentence|paragraph (default: sentence)
    -i, --interactive Enable interactive mode
"""

import asyncio
import sys
import time
import random
import threading
import argparse
import json
from typing import AsyncGenerator, Dict, Any, List, Optional

# Import python_a2a components
from python_a2a import (
    BaseA2AServer, AgentCard, Message, TextContent, MessageRole, run_server
)
from python_a2a.client.streaming import StreamingClient, StreamingChunk

# ANSI colors and styles for prettier output
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Default configuration
DEFAULT_QUERY = "Explain how streaming improves user experience in AI applications"
DEFAULT_CHUNK_STYLE = "sentence"


class AdvancedStreamingServer(BaseA2AServer):
    """
    An advanced server demonstrating sophisticated streaming capabilities.
    
    This server supports multiple chunking strategies, simulated thinking,
    and advanced streaming features.
    """
    
    def __init__(
        self, 
        url: str = "http://localhost:8000", 
        chunk_style: str = "sentence",
        thinking_delay: str = "medium"
    ):
        """
        Initialize the streaming server.
        
        Args:
            url: The server URL
            chunk_style: Chunking style: word, sentence, or paragraph
            thinking_delay: Delay between chunks: fast, medium, or slow
        """
        # Create an agent card with streaming capability
        self.agent_card = AgentCard(
            name="Advanced A2A Streaming Demo",
            description="Demonstrates advanced streaming capabilities in the A2A protocol",
            url=url,
            version="1.0.0",
            capabilities={
                "streaming": True,
                "chunking_styles": ["word", "sentence", "paragraph"],
                "advanced_metrics": True
            }
        )
        
        # Store configuration
        self.chunk_style = chunk_style
        
        # Set up thinking delays based on selected speed
        if thinking_delay == "fast":
            self.min_delay, self.max_delay = 0.1, 0.3
        elif thinking_delay == "slow":
            self.min_delay, self.max_delay = 0.7, 1.5
        else:  # medium is default
            self.min_delay, self.max_delay = 0.3, 0.8
            
        # Track metrics for the server
        self.total_streams = 0
        self.total_chunks = 0
        self.total_chars = 0
    
    def handle_message(self, message: Message) -> Message:
        """Handle standard (non-streaming) message."""
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        response_text = self._generate_response(query)
        
        print(f"[Server] Sending non-streaming response ({len(response_text)} chars)")
        
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """
        Stream a response with advanced chunking strategies.
        
        Args:
            message: The incoming message
            
        Yields:
            Chunks of the response based on selected chunking strategy
        """
        # Extract query and get full response text
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Track stream count
        self.total_streams += 1
        stream_id = self.total_streams
        
        print(f"[Server] Stream #{stream_id} started - query: {query[:50]}...")
        print(f"[Server] Using {self.chunk_style} chunking with {self.min_delay}-{self.max_delay}s delays")
        
        # Check for simulated error condition
        if "error" in query.lower() and "simulate" in query.lower():
            print(f"[Server] Simulating streaming error")
            # Stream a bit before error
            yield "Starting to process your query about error simulation. "
            await asyncio.sleep(1.0)
            yield "This stream will encounter an error shortly... "
            await asyncio.sleep(0.5)
            # Raise exception - will be caught and handled by client
            raise ValueError("Simulated streaming error as requested")
        
        # Generate full response
        full_response = self._generate_response(query)
        
        # Prepare chunks based on selected style
        chunks = self._create_chunks(full_response, self.chunk_style)
        print(f"[Server] Ready to stream {len(chunks)} chunks ({len(full_response)} chars total)")
        
        # Stream each chunk with appropriate delay
        chunk_count = 0
        for chunk in chunks:
            # Skip empty chunks
            if not chunk.strip():
                continue
                
            # Add thinking delay based on chunk length
            delay = min(
                self.max_delay,
                self.min_delay + (len(chunk) / 100) * (self.max_delay - self.min_delay)
            )
            await asyncio.sleep(delay)
            
            # Update metrics
            chunk_count += 1
            self.total_chunks += 1
            self.total_chars += len(chunk)
            
            # Log chunk info for demonstration
            print(f"[Server] Streaming chunk {chunk_count}/{len(chunks)} ({len(chunk)} chars)")
            
            # Yield the chunk
            yield chunk
        
        # Log completion
        print(f"[Server] Stream #{stream_id} complete: {chunk_count} chunks, {len(full_response)} chars")
        print(f"[Server] Total metrics: {self.total_streams} streams, {self.total_chunks} chunks, {self.total_chars} chars")
    
    def _create_chunks(self, text: str, style: str) -> List[str]:
        """
        Create chunks based on the specified chunking style.
        
        Args:
            text: Full text to chunk
            style: Chunking style: word, sentence, or paragraph
            
        Returns:
            List of chunks
        """
        if style == "word":
            # Group words into chunks of varying sizes
            words = text.split()
            chunks = []
            current_chunk = []
            
            for word in words:
                current_chunk.append(word)
                # Randomly decide if we should end this chunk
                # More words in chunk = higher chance of ending
                if random.random() < 0.1 * len(current_chunk):
                    chunks.append(" ".join(current_chunk) + " ")
                    current_chunk = []
            
            # Add any remaining words
            if current_chunk:
                chunks.append(" ".join(current_chunk) + " ")
                
            return chunks
            
        elif style == "paragraph":
            # Split by double newlines and ensure each ends with double newline
            paragraphs = text.split("\n\n")
            return [p.strip() + "\n\n" for p in paragraphs if p.strip()]
            
        else:  # Default to sentence chunking
            # Split by sentence boundaries
            sentences = []
            for part in text.replace(". ", ".|").replace("? ", "?|").replace("! ", "!|").split("|"):
                if part:
                    sentences.append(part + (" " if not part.endswith((".", "?", "!")) else ""))
            return sentences
    
    def _generate_response(self, query: str) -> str:
        """Generate a comprehensive response based on the query."""
        # Process query for content selection
        query = query.lower()
        
        if "user experience" in query or "ux" in query:
            return (
                "Streaming significantly enhances user experience in AI applications in several key ways.\n\n"
                
                "First, streaming creates an immediate connection between the user and the AI. When a user sends a query, "
                "seeing an immediate response start to appear creates a sense of acknowledgment and responsiveness. This "
                "drastically reduces the perceived latency, even if the total response time is unchanged.\n\n"
                
                "Second, streaming enables a more natural conversation flow. Human conversations don't happen in complete, "
                "fully-formed paragraphs - we think and speak incrementally. Streaming mimics this natural cadence, making "
                "AI interactions feel more human and less mechanical.\n\n"
                
                "Third, streaming provides continuous feedback. Users can begin processing information immediately rather than "
                "waiting for a complete response. This is especially valuable for longer responses where the user might want to "
                "interrupt or redirect the AI before it completes its full response.\n\n"
                
                "Fourth, streaming improves user trust. The visibility into the AI's thinking process creates transparency "
                "and builds confidence in the system. Users can see that the AI is actively working on their request.\n\n"
                
                "Finally, streaming enables better error recovery. If there's an issue with the response, both the user and "
                "the system can detect it earlier in the process, reducing wasted time and computational resources.\n\n"
                
                "All these factors combine to create a more engaging, efficient, and natural user experience that better "
                "matches how humans naturally communicate and process information."
            )
        elif "technical" in query or "implement" in query:
            return (
                "From a technical perspective, streaming in AI applications involves several key components and considerations.\n\n"
                
                "At its core, streaming leverages Server-Sent Events (SSE) or WebSockets to establish a persistent connection "
                "between the server and client. With SSE, which is commonly used in A2A protocol implementations, the server "
                "keeps the connection open and sends new chunks as they become available, with each chunk properly formatted "
                "according to the SSE specification.\n\n"
                
                "In the A2A protocol specifically, the server implements an AsyncGenerator that yields chunks of content. Each "
                "yielded chunk is immediately sent to the client, with appropriate metadata like sequence numbers and append "
                "flags that tell the client how to process each chunk.\n\n"
                
                "On the client side, a StreamingClient connects to the /stream endpoint and processes the incoming chunks. "
                "The client needs to handle various aspects including:\n\n"
                "1. Proper content negotiation with Accept: text/event-stream header\n"
                "2. Buffering and processing chunks as they arrive\n"
                "3. Handling connection issues and implementing reconnection strategies\n"
                "4. Providing progress indicators to the user interface\n"
                "5. Dealing with errors that might occur mid-stream\n\n"
                
                "One challenge in implementing streaming is dealing with the asynchronous nature of the process. In many web "
                "frameworks, this requires bridging between synchronous request handling and asynchronous response generation, "
                "often using techniques like background threads with dedicated event loops.\n\n"
                
                "Another consideration is error handling - errors that occur during streaming must be properly propagated to "
                "the client, which requires specialized error event types in the SSE protocol.\n\n"
                
                "Security is also important, as long-lived connections can consume server resources, making proper timeout "
                "and resource management essential for production systems."
            )
        else:
            return (
                "Streaming is a communication technique that fundamentally changes how AI systems deliver information to users.\n\n"
                
                "In traditional request-response patterns, a user sends a query, then waits while the AI generates the entire "
                "response. Only when the complete response is ready does the user see anything. This creates a frustrating "
                "waiting period, especially for complex or lengthy responses.\n\n"
                
                "Streaming takes a different approach. Instead of waiting for the complete response, the system sends small "
                "chunks of the response as soon as they're generated. This creates several advantages:\n\n"
                
                "1. Reduced perceived latency - users see something happening immediately\n"
                "2. More natural interaction - mimics human conversation patterns\n"
                "3. Better user engagement - maintains attention through continuous updates\n"
                "4. Opportunity for early feedback - users can start processing information sooner\n"
                "5. Improved resource utilization - better distribution of processing and network load\n\n"
                
                "The A2A protocol implements streaming through Server-Sent Events (SSE), where each chunk is delivered with "
                "metadata that tells the client how to handle it. The server yields chunks from an async generator function, "
                "and the client assembles these chunks into a coherent response.\n\n"
                
                "Different chunking strategies can be employed depending on the content type. For conversational text, "
                "sentence-by-sentence chunking often feels most natural. For code or technical content, logical blocks "
                "might make more sense. For some applications, word-by-word streaming can create a very engaging 'typing' "
                "effect.\n\n"
                
                "Advanced streaming implementations also handle errors gracefully, provide progress indicators, and manage "
                "connection issues transparently to the user."
            )


class StreamingVisualizer:
    """
    Advanced streaming visualization with metrics and progress tracking.
    
    This class provides real-time visualization of streaming responses
    with detailed metrics and formatting.
    """
    
    def __init__(
        self,
        show_metrics: bool = True,
        show_timing: bool = True,
        show_chunk_numbers: bool = True,
        width: int = 80
    ):
        """
        Initialize the streaming visualizer.
        
        Args:
            show_metrics: Whether to show real-time metrics
            show_timing: Whether to show timing information
            show_chunk_numbers: Whether to show chunk numbers
            width: Width for progress indicators
        """
        self.show_metrics = show_metrics
        self.show_timing = show_timing
        self.show_chunk_numbers = show_chunk_numbers
        self.width = width
        
        # Initialize metrics
        self.start_time = time.time()
        self.chunk_count = 0
        self.total_chars = 0
        self.chunk_times = []
        self.chunk_sizes = []
        self.full_text = ""
        
        # Print header
        if self.show_metrics:
            self._print_header()
    
    def _print_header(self):
        """Print the header for the streaming visualization."""
        print(f"\n{BLUE}Streaming Response:{RESET}")
        print("-" * self.width)
    
    def _update_progress(self):
        """Update and display streaming progress metrics."""
        if not self.show_metrics:
            return
            
        elapsed = time.time() - self.start_time
        
        if elapsed > 0:
            chars_per_sec = self.total_chars / elapsed
            chunks_per_sec = self.chunk_count / elapsed
            
            # Only update occasionally to avoid flickering
            if self.chunk_count % 3 == 0 or elapsed > 5.0:
                sys.stdout.write("\r" + " " * self.width + "\r")
                sys.stdout.write(
                    f"{CYAN}[{self.chunk_count} chunks | {self.total_chars} chars | "
                    f"{elapsed:.1f}s | {chars_per_sec:.1f} c/s]{RESET}"
                )
                sys.stdout.flush()
    
    async def process_chunk(self, chunk: Any):
        """
        Process and display a streaming chunk.
        
        Args:
            chunk: The chunk to process
        """
        chunk_start = time.time()
        self.chunk_count += 1
        
        # Extract text from chunk (various formats)
        if isinstance(chunk, dict):
            if "content" in chunk:
                text = chunk["content"]
            elif "text" in chunk:
                text = chunk["text"]
            else:
                text = json.dumps(chunk)
        else:
            text = str(chunk)
        
        # Update metrics
        self.total_chars += len(text)
        self.chunk_sizes.append(len(text))
        self.full_text += text
        
        # Record timing
        chunk_time = time.time() - chunk_start
        self.chunk_times.append(chunk_time)
        
        # Show chunk number if requested
        if self.show_chunk_numbers:
            print(f"{YELLOW}[{self.chunk_count}]{RESET} ", end="", flush=True)
        
        # Display the chunk
        print(text, end="", flush=True)
        
        # Update progress metrics
        self._update_progress()
        
        # Small delay to allow for UI updates
        await asyncio.sleep(0)
    
    def print_final_stats(self):
        """Print final statistics after streaming completes."""
        # Clear progress line
        if self.show_metrics:
            sys.stdout.write("\r" + " " * self.width + "\r")
            sys.stdout.flush()
        
        # Calculate final metrics
        elapsed = time.time() - self.start_time
        if elapsed > 0:
            chars_per_sec = self.total_chars / elapsed
            chunks_per_sec = self.chunk_count / elapsed
        else:
            chars_per_sec = 0
            chunks_per_sec = 0
            
        avg_chunk_size = sum(self.chunk_sizes) / len(self.chunk_sizes) if self.chunk_sizes else 0
        
        # Print summary
        print("\n" + "-" * self.width)
        print(f"{GREEN}{BOLD}Streaming Complete{RESET}")
        print(f"{GREEN}✓ Received {self.chunk_count} chunks in {elapsed:.2f} seconds{RESET}")
        print(f"{GREEN}✓ Total text length: {self.total_chars} characters{RESET}")
        
        if self.show_timing:
            print(f"{GREEN}✓ Average chunk size: {avg_chunk_size:.1f} characters{RESET}")
            print(f"{GREEN}✓ Speed: {chars_per_sec:.1f} characters/second ({chunks_per_sec:.1f} chunks/second){RESET}")
            
            # Only show detailed chunk analysis for larger responses
            if self.chunk_count > 5:
                print(f"{GREEN}✓ Chunk size range: {min(self.chunk_sizes)} to {max(self.chunk_sizes)} characters{RESET}")


async def run_advanced_streaming_client(url: str, query: str, show_metrics: bool = True):
    """
    Run the advanced streaming client demonstration.
    
    Args:
        url: Server URL
        query: Query to send
        show_metrics: Whether to show detailed metrics
    """
    # Create message
    message = Message(
        content=TextContent(text=query),
        role=MessageRole.USER
    )
    
    # Create streaming client
    client = StreamingClient(url)
    
    # Set up visualization
    visualizer = StreamingVisualizer(
        show_metrics=show_metrics,
        show_timing=True,
        show_chunk_numbers=True
    )
    
    try:
        # Stream the response
        async for chunk in client.stream_response(message):
            await visualizer.process_chunk(chunk)
        
        # Print final stats
        visualizer.print_final_stats()
        
        return visualizer.full_text
        
    except Exception as e:
        # Handle streaming errors more gracefully
        print(f"\n\n{RED}Error during streaming: {str(e)}{RESET}")
        print(f"{YELLOW}Partial response received ({visualizer.total_chars} characters):{RESET}")
        if visualizer.total_chars > 0:
            print(f"{YELLOW}{visualizer.full_text}{RESET}")
        return None


async def main_async(args):
    """
    Main async function.
    
    Args:
        args: Command line arguments
    """
    # Get port
    port = args.port or find_free_port()
    server_url = f"http://localhost:{port}"
    
    # Create server with specified options
    server = AdvancedStreamingServer(
        url=server_url,
        chunk_style=args.style,
        thinking_delay=args.delay
    )
    
    # Start server in background thread
    print(f"{BLUE}Starting advanced streaming server on port {port}...{RESET}")
    print(f"{BLUE}Chunk style: {args.style}, Thinking delay: {args.delay}{RESET}")
    
    server_thread = threading.Thread(
        target=lambda: run_server(server, host="localhost", port=port),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    # Run initial streaming request
    print(f"{BLUE}Sending query: {args.query}{RESET}")
    await run_advanced_streaming_client(server_url, args.query)
    
    # Interactive mode if requested
    if args.interactive:
        try:
            while True:
                print(f"\n{BLUE}Enter a query (or Ctrl+C to exit):{RESET}")
                next_query = input("> ")
                if next_query.strip():
                    await run_advanced_streaming_client(server_url, next_query)
                else:
                    print(f"{YELLOW}Query cannot be empty{RESET}")
        except KeyboardInterrupt:
            print(f"\n{BLUE}Exiting interactive mode{RESET}")


def find_free_port():
    """Find an available port on localhost."""
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('localhost', 0))
        return s.getsockname()[1]


def main():
    """Parse arguments and run the example."""
    parser = argparse.ArgumentParser(description="Advanced A2A Streaming Example")
    parser.add_argument("--query", default=DEFAULT_QUERY,
                       help="Query to send to the agent")
    parser.add_argument("--port", type=int, default=None,
                       help="Port to run the server on (will find a free port if not specified)")
    parser.add_argument("--style", choices=["word", "sentence", "paragraph"], 
                       default=DEFAULT_CHUNK_STYLE,
                       help="Chunking style to use")
    parser.add_argument("--delay", choices=["fast", "medium", "slow"], 
                       default="medium",
                       help="Simulated thinking delay")
    parser.add_argument("-i", "--interactive", action="store_true",
                       help="Enable interactive mode after initial query")
    
    args = parser.parse_args()
    
    try:
        asyncio.run(main_async(args))
    except KeyboardInterrupt:
        print(f"\n{BLUE}Exiting{RESET}")


if __name__ == "__main__":
    main()