"""
Example 06: Distributed Streaming

This example demonstrates how to implement A2A streaming in a distributed 
environment, including:
1. Multiple streaming servers with load balancing
2. Stream aggregation from multiple sources
3. Fault tolerance and error handling
4. Metrics collection and monitoring

Key concepts:
- Distributed streaming architecture
- Stream composition and aggregation
- Fault tolerance strategies
- Performance monitoring and metrics
- Backpressure handling

Prerequisites:
- Install additional requirements: pip install aiohttp tqdm
"""

import asyncio
import json
import os
import random
import signal
import time
from asyncio import Queue
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Tuple, Union

import aiohttp
from tqdm import tqdm

# Import from the A2A library
from python_a2a.client import A2AClient
from python_a2a.client.streaming import StreamingClient
from python_a2a.models.message import Message, MessageRole
from python_a2a.models.content import TextContent
from python_a2a.models.agent import AgentCard
from python_a2a.server.base import BaseA2AServer
from python_a2a.server.http import run_server
from python_a2a.exceptions import A2AStreamingError


class DistributedStreamingServer(BaseA2AServer):
    """A server that simulates being part of a distributed streaming cluster."""
    
    def __init__(self, 
                 name: str = "Distributed Server",
                 node_id: str = None,
                 failure_rate: float = 0.0, 
                 lag_factor: float = 1.0):
        """Initialize the server with distributed parameters.
        
        Args:
            name: The server name
            node_id: Unique identifier for this node
            failure_rate: Probability of simulating a failure (0.0-1.0)
            lag_factor: Multiplier for response lag (1.0 = normal, higher = more lag)
        """
        # BaseA2AServer doesn't have a defined __init__, so no need to call super().__init__()
        self.name = name
        self.agent_card = AgentCard(
            name=f"{name} ({node_id or 'unknown'})",
            description="Distributed streaming A2A agent",
            url="http://localhost:8000",  # Default, will be updated
            version="1.0.0",
            capabilities={"streaming": True}
        )
        self.node_id = node_id or f"node-{random.randint(1000, 9999)}"
        self.failure_rate = min(max(failure_rate, 0.0), 1.0)  # Clamp to 0.0-1.0
        self.lag_factor = max(lag_factor, 0.1)  # Ensure some positive value
        
        # Metrics collection
        self.metrics = {
            "requests_processed": 0,
            "chunks_generated": 0,
            "failures_simulated": 0,
            "avg_chunk_processing_time": 0,
            "peak_memory_usage": 0,
        }
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle standard (non-streaming) message requests.
        This is required since BaseA2AServer is an abstract class.
        
        Args:
            message: The incoming message
            
        Returns:
            Response message
        """
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Randomly simulate a failure based on failure_rate
        if random.random() < self.failure_rate:
            self.metrics["failures_simulated"] += 1
            return Message(
                content=TextContent(text=f"Error: Simulated failure in node {self.node_id}"),
                role=MessageRole.SYSTEM,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
        
        # Determine the response style for this node
        response_style = random.choice(["technical", "creative", "analytical", "concise"])
        
        # Generate a response
        chunks = self._generate_response_chunks(query, 3, response_style)
        
        # Track metrics
        self.metrics["requests_processed"] += 1
        
        return Message(
            content=TextContent(text=f"[Node {self.node_id}] " + " ".join(chunks)),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """Stream a response with simulated distributed characteristics."""
        # Track metrics
        self.metrics["requests_processed"] += 1
        chunk_count = 0
        start_time = time.time()
        
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Randomly simulate a failure based on failure_rate
        if random.random() < self.failure_rate:
            self.metrics["failures_simulated"] += 1
            await asyncio.sleep(0.5)  # Brief delay before failure
            raise A2AStreamingError(f"Simulated failure in node {self.node_id}")
        
        # Determine the response style for this node
        response_style = random.choice(["technical", "creative", "analytical", "concise"])
        
        # Generate a relatively small response (3-7 chunks)
        num_chunks = random.randint(3, 7)
        chunks = self._generate_response_chunks(query, num_chunks, response_style)
        
        # Add node metadata to first chunk
        metadata = {
            "node_id": self.node_id,
            "timestamp": datetime.now().isoformat(),
            "response_style": response_style,
        }
        
        # Stream with simulated processing time variations
        for i, chunk in enumerate(chunks):
            # Simulated processing/network delay based on lag factor
            processing_time = random.uniform(0.2, 0.6) * self.lag_factor
            await asyncio.sleep(processing_time)
            
            # For first chunk, add node identifying information
            if i == 0:
                chunk = f"[Node {self.node_id}] {chunk}"
            
            # Metrics tracking
            chunk_count += 1
            
            # Simulate occasional backpressure for larger lag factors
            if self.lag_factor > 1.5 and random.random() < 0.2:
                await asyncio.sleep(random.uniform(0.5, 1.0))
            
            # Yield the chunk
            yield chunk
        
        # Update final metrics
        self.metrics["chunks_generated"] += chunk_count
        processing_time = time.time() - start_time
        self.metrics["avg_chunk_processing_time"] = (
            (self.metrics["avg_chunk_processing_time"] * (self.metrics["requests_processed"] - 1))
            + processing_time
        ) / self.metrics["requests_processed"]
        
        # Simulate memory usage statistics
        self.metrics["peak_memory_usage"] = max(
            self.metrics["peak_memory_usage"],
            random.randint(50, 200) * self.metrics["requests_processed"]
        )
    
    def _generate_response_chunks(self, query: str, num_chunks: int, style: str) -> List[str]:
        """Generate response chunks in a particular style."""
        chunks = []
        
        # Define content based on style
        technical_content = [
            "The distributed system architecture leverages asynchronous message passing.",
            "Each node implements a consistent hashing algorithm for load distribution.",
            "Fault tolerance is achieved through redundancy and state replication.",
            "Response latency is optimized using predictive prefetching techniques.",
            "The consensus protocol ensures eventual consistency across all nodes.",
            "Data sharding improves throughput by parallelizing query processing.",
            "Circuit breakers prevent cascading failures in the node network.",
        ]
        
        creative_content = [
            "Imagine your data flowing like a river across multiple streams and tributaries.",
            "Each node in our system is like a musician in an orchestra, playing its part.",
            "The magic happens when all these distributed pieces harmonize together.",
            "Like a puzzle coming together, each stream adds to the complete picture.",
            "Think of our system as a neural network, with each node contributing its insight.",
            "The beauty of distributed systems is in their resilience and adaptability.",
            "Every stream tells part of the story, creating a tapestry of information.",
        ]
        
        analytical_content = [
            "Analysis of query patterns indicates a 37% improvement in response time.",
            "The efficiency coefficient of distributed processing is logarithmic to node count.",
            "Statistical models show that stream aggregation reduces variance by 42%.",
            "Comparative benchmarks demonstrate 3.5x throughput versus monolithic systems.",
            "Quantitative assessment reveals optimal node distribution at N+2 redundancy.",
            "Time-series analysis confirms streaming's superiority for real-time applications.",
            "Load distribution matrices indicate asymptotic improvement with scale.",
        ]
        
        concise_content = [
            "Distributed processing active.",
            "Stream data flowing normally.",
            "Node network stable.",
            "Processing complete.",
            "Results aggregated successfully.",
            "System operating within parameters.",
            "Response optimization applied.",
        ]
        
        # Select content based on style
        if style == "technical":
            content = technical_content
        elif style == "creative":
            content = creative_content
        elif style == "analytical":
            content = analytical_content
        else:  # concise
            content = concise_content
        
        # Generate the chunks
        for _ in range(num_chunks):
            chunk = random.choice(content)
            chunks.append(chunk)
        
        return chunks


class LoadBalancer:
    """A load balancer that distributes requests across multiple streaming servers."""
    
    def __init__(self, server_urls: List[str], strategy: str = "round_robin"):
        """Initialize with server URLs and a distribution strategy.
        
        Args:
            server_urls: List of server URLs to balance across
            strategy: Distribution strategy: 'round_robin', 'random', or 'least_busy'
        """
        self.server_urls = server_urls
        self.strategy = strategy
        self.current_index = 0
        self.server_metrics = {url: {"requests": 0, "errors": 0, "last_latency": 0} 
                              for url in server_urls}
    
    def get_server_url(self) -> str:
        """Get the next server URL based on the selected strategy."""
        if not self.server_urls:
            raise ValueError("No server URLs available")
        
        if self.strategy == "round_robin":
            url = self.server_urls[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.server_urls)
            return url
        
        elif self.strategy == "random":
            return random.choice(self.server_urls)
        
        elif self.strategy == "least_busy":
            return min(self.server_metrics.items(), 
                      key=lambda x: x[1]["requests"] / (1 + x[1]["last_latency"]))[0]
        
        else:
            # Default to round robin
            url = self.server_urls[self.current_index]
            self.current_index = (self.current_index + 1) % len(self.server_urls)
            return url
    
    def update_metrics(self, url: str, success: bool, latency: float):
        """Update metrics for a server after a request."""
        if url in self.server_metrics:
            self.server_metrics[url]["requests"] += 1
            if not success:
                self.server_metrics[url]["errors"] += 1
            self.server_metrics[url]["last_latency"] = latency


class DistributedStreamingClient:
    """A client that can aggregate streams from multiple sources."""
    
    def __init__(self, load_balancer: LoadBalancer = None, server_urls: List[str] = None):
        """Initialize with either a load balancer or direct server URLs."""
        if load_balancer:
            self.load_balancer = load_balancer
        elif server_urls:
            self.load_balancer = LoadBalancer(server_urls)
        else:
            raise ValueError("Either load_balancer or server_urls must be provided")
        
        self.clients = {}  # Cache for clients
    
    def _get_client(self, url: str) -> StreamingClient:
        """Get or create a client for the given URL."""
        if url not in self.clients:
            self.clients[url] = StreamingClient(url)
        return self.clients[url]
    
    async def stream_from_single_source(self, message: Message) -> AsyncGenerator[str, None]:
        """Stream a response from a single source selected by the load balancer."""
        server_url = self.load_balancer.get_server_url()
        client = self._get_client(server_url)
        
        start_time = time.time()
        success = True
        
        try:
            async for chunk in client.stream_response(message):
                yield chunk
        except Exception as e:
            success = False
            yield f"Error from {server_url}: {str(e)}"
        finally:
            # Update metrics
            latency = time.time() - start_time
            self.load_balancer.update_metrics(server_url, success, latency)
    
    async def stream_with_fallback(self, message: Message, 
                                  max_retries: int = 2) -> AsyncGenerator[str, None]:
        """Stream with automatic retry and fallback if a source fails."""
        retries = 0
        tried_urls = set()
        
        while retries <= max_retries:
            server_url = self.load_balancer.get_server_url()
            
            # Skip already tried URLs if possible
            if server_url in tried_urls and len(tried_urls) < len(self.load_balancer.server_urls):
                continue
            
            tried_urls.add(server_url)
            client = self._get_client(server_url)
            
            start_time = time.time()
            success = True
            chunks_received = 0
            
            try:
                # Indicate which server we're using for this attempt
                yield f"[Attempt {retries+1}] Using server: {server_url}\n"
                
                async for chunk in client.stream_response(message):
                    chunks_received += 1
                    yield chunk
                
                # If we get here, streaming completed successfully
                break
                
            except Exception as e:
                success = False
                yield f"\n[Error] Server {server_url} failed: {str(e)}\n"
                
                if retries < max_retries:
                    yield f"[Retrying] Switching to another server...\n"
                else:
                    yield f"[Failed] Maximum retries reached. Could not complete request.\n"
                
                retries += 1
                
            finally:
                # Update metrics
                latency = time.time() - start_time
                self.load_balancer.update_metrics(server_url, success, latency)
    
    async def stream_aggregated(self, message: Message, 
                               num_sources: int = 3) -> AsyncGenerator[Dict, None]:
        """Stream from multiple sources in parallel and aggregate results.
        
        Unlike other streaming methods, this returns structured chunks with source info.
        """
        # Get URLs for all sources we'll use
        source_urls = []
        for _ in range(min(num_sources, len(self.load_balancer.server_urls))):
            url = self.load_balancer.get_server_url()
            while url in source_urls and len(source_urls) < len(self.load_balancer.server_urls):
                url = self.load_balancer.get_server_url()
            source_urls.append(url)
        
        # Create tasks for all sources
        tasks = []
        for url in source_urls:
            client = self._get_client(url)
            tasks.append(asyncio.create_task(self._stream_from_source(client, message, url)))
        
        # Process all chunks as they arrive
        pending = set(tasks)
        source_status = {url: {"active": True, "chunks": 0} for url in source_urls}
        
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            
            for task in done:
                try:
                    result = task.result()
                    
                    if result["type"] == "chunk":
                        # Update source status
                        source_status[result["source"]]["chunks"] += 1
                        
                        # Yield the chunk
                        yield result
                        
                        # Continue streaming from this source if not complete
                        if source_status[result["source"]]["active"]:
                            client = self._get_client(result["source"])
                            
                            # Create new task to get next chunk
                            new_task = asyncio.create_task(
                                self._stream_from_source(
                                    client, message, result["source"], 
                                    result["chunk_index"] + 1
                                )
                            )
                            pending.add(new_task)
                    
                    elif result["type"] == "complete":
                        # Mark source as complete
                        source_status[result["source"]]["active"] = False
                        yield result
                    
                    elif result["type"] == "error":
                        # Mark source as inactive due to error
                        source_status[result["source"]]["active"] = False
                        yield result
                
                except Exception as e:
                    # Handle unexpected task failures
                    for url in source_urls:
                        if source_status[url]["active"]:
                            yield {
                                "type": "error",
                                "source": url,
                                "error": f"Unexpected error: {str(e)}"
                            }
                            source_status[url]["active"] = False
        
        # Final aggregated completion
        total_chunks = sum(source["chunks"] for source in source_status.values())
        active_sources = sum(1 for source in source_status.values() if source["active"])
        
        yield {
            "type": "aggregate_complete",
            "total_chunks": total_chunks,
            "successful_sources": len(source_urls) - active_sources,
            "total_sources": len(source_urls)
        }
    
    async def _stream_from_source(self, client: StreamingClient, message: Message, 
                                 source_url: str, chunk_index: int = 0) -> Dict:
        """Stream a single chunk from a source and return it with metadata."""
        try:
            # Start streaming
            stream_iterator = client.stream_response(message).__aiter__()
            
            # Skip chunks we've already processed
            for _ in range(chunk_index):
                try:
                    await asyncio.wait_for(stream_iterator.__anext__(), timeout=1.0)
                except StopAsyncIteration:
                    # Stream ended prematurely
                    return {
                        "type": "complete",
                        "source": source_url,
                        "chunk_index": chunk_index
                    }
                except asyncio.TimeoutError:
                    # Timeout waiting for chunk
                    return {
                        "type": "error",
                        "source": source_url,
                        "error": "Timeout waiting for chunk"
                    }
            
            # Get the next chunk
            try:
                chunk = await asyncio.wait_for(stream_iterator.__anext__(), timeout=5.0)
                return {
                    "type": "chunk",
                    "source": source_url,
                    "content": chunk,
                    "chunk_index": chunk_index,
                    "timestamp": datetime.now().isoformat()
                }
            except StopAsyncIteration:
                # Stream is complete
                return {
                    "type": "complete",
                    "source": source_url,
                    "chunk_index": chunk_index
                }
            except asyncio.TimeoutError:
                # Timeout waiting for chunk
                return {
                    "type": "error",
                    "source": source_url,
                    "error": "Timeout waiting for chunk"
                }
                
        except Exception as e:
            # Any other error
            return {
                "type": "error",
                "source": source_url,
                "error": str(e)
            }


async def run_distributed_demo():
    """Run a demo of distributed streaming."""
    print("\n=== A2A Distributed Streaming Demo ===")
    print("This demo simulates a distributed streaming environment with multiple nodes.\n")
    
    # Set up servers with different characteristics
    servers = [
        # A reliable, fast server
        DistributedStreamingServer(
            name="Primary Node", 
            node_id="primary-1", 
            failure_rate=0.0,
            lag_factor=0.8
        ),
        # A mostly reliable server with some lag
        DistributedStreamingServer(
            name="Secondary Node", 
            node_id="secondary-1", 
            failure_rate=0.1,
            lag_factor=1.2
        ),
        # An unreliable server
        DistributedStreamingServer(
            name="Backup Node", 
            node_id="backup-1", 
            failure_rate=0.3,
            lag_factor=1.5
        ),
        # Another reliable but slow server
        DistributedStreamingServer(
            name="Analytics Node", 
            node_id="analytics-1", 
            failure_rate=0.05,
            lag_factor=2.0
        ),
    ]
    
    # Start each server on a different port
    server_ports = []
    server_futures = []
    executor = ThreadPoolExecutor(max_workers=len(servers))
    
    base_port = 8000
    for i, server in enumerate(servers):
        port = base_port + i
        server_ports.append(port)
        
        # Start the server in its own thread
        future = executor.submit(
            run_server, server, "localhost", port, debug=False
        )
        server_futures.append(future)
    
    # Wait for servers to start
    await asyncio.sleep(1)
    
    # Create server URLs
    server_urls = [f"http://localhost:{port}" for port in server_ports]
    
    # Create a load balancer
    load_balancer = LoadBalancer(server_urls, strategy="round_robin")
    
    # Create a distributed client
    client = DistributedStreamingClient(load_balancer)
    
    # Sample query
    query = "Explain the advantages of distributed streaming architectures"
    message = Message(content=TextContent(text=query), role=MessageRole.USER)
    
    # Menu of demo options
    print("Select a demonstration mode:")
    print("1. Single-source streaming (simple, one server)")
    print("2. Streaming with fallback (automatic retry on failure)")
    print("3. Aggregated multi-source streaming (parallel from all servers)")
    
    choice = input("\nEnter choice (1-3): ")
    
    if choice == "2":
        # Demo 2: Streaming with fallback
        print("\n=== Streaming with Automatic Fallback ===")
        print(f"Query: '{query}'")
        print("\nStreaming (with retry on failure)...")
        
        async for chunk in client.stream_with_fallback(message, max_retries=3):
            # Handle dictionary chunks by extracting content
            if isinstance(chunk, dict):
                if "content" in chunk:
                    # Extract content from dict
                    chunk_text = chunk["content"]
                else:
                    # Try to convert the dict to a string
                    try:
                        chunk_text = json.dumps(chunk)
                    except:
                        chunk_text = str(chunk)
            else:
                # Use the chunk as is
                chunk_text = str(chunk)
                
            print(chunk_text, end="", flush=True)
        
    elif choice == "3":
        # Demo 3: Aggregated streaming
        print("\n=== Aggregated Multi-Source Streaming ===")
        print(f"Query: '{query}'")
        print("\nStreaming from multiple sources in parallel...\n")
        
        source_buffers = {url: [] for url in server_urls}
        active_sources = set(server_urls)
        
        # Process the aggregated stream
        async for item in client.stream_aggregated(message, num_sources=len(servers)):
            if item["type"] == "chunk":
                source = item["source"]
                content = item["content"]
                
                # Extract text from content if it's a dictionary
                if isinstance(content, dict):
                    if "content" in content:
                        content_text = content["content"]
                    else:
                        # Try to convert dict to string
                        try:
                            content_text = json.dumps(content)
                        except:
                            content_text = str(content)
                else:
                    content_text = str(content)
                
                # Add to the source's buffer
                source_buffers[source].append(content_text)
                
                # Clear the screen and redisplay all buffers
                os.system('cls' if os.name == 'nt' else 'clear')
                
                print(f"=== Streaming from {len(active_sources)} sources ===\n")
                
                # Display source status
                for url in server_urls:
                    source_name = url.split(":")[-1]
                    chunks = len(source_buffers[url])
                    
                    if url in active_sources:
                        status = "✅ ACTIVE"
                    else:
                        status = "❌ INACTIVE"
                    
                    print(f"Node {source_name} | Status: {status} | Chunks: {chunks}")
                
                print("\n=== Content Streams ===\n")
                
                # Display content from each source
                for url in server_urls:
                    source_name = url.split(":")[-1]
                    content = "".join(source_buffers[url])
                    
                    print(f"--- Node {source_name} ---")
                    print(f"{content}\n")
            
            elif item["type"] == "error":
                source = item["source"]
                active_sources.discard(source)
                
                print(f"\nError from {source}: {item['error']}")
            
            elif item["type"] == "complete":
                source = item["source"]
                active_sources.discard(source)
                
                print(f"\nSource {source} completed streaming")
            
            elif item["type"] == "aggregate_complete":
                print("\n=== Streaming Complete ===")
                print(f"Total chunks received: {item['total_chunks']}")
                print(f"Successful sources: {item['successful_sources']}/{item['total_sources']}")
        
    else:
        # Default Demo 1: Single-source streaming
        print("\n=== Single-Source Streaming ===")
        print(f"Query: '{query}'")
        print("\nStreaming from a single source...")
        
        async for chunk in client.stream_from_single_source(message):
            # Handle dictionary chunks by extracting content
            if isinstance(chunk, dict):
                if "content" in chunk:
                    # Extract content from dict
                    chunk_text = chunk["content"]
                else:
                    # Try to convert the dict to a string
                    try:
                        chunk_text = json.dumps(chunk)
                    except:
                        chunk_text = str(chunk)
            else:
                # Use the chunk as is
                chunk_text = str(chunk)
                
            print(chunk_text, end="", flush=True)
    
    # Clean up
    print("\n\nDemo complete. Shutting down servers...")
    for future in server_futures:
        future.cancel()
    executor.shutdown(wait=False)


if __name__ == "__main__":
    try:
        # Run the demo
        asyncio.run(run_distributed_demo())
    except KeyboardInterrupt:
        print("\nDemo interrupted. Shutting down...")
    except Exception as e:
        print(f"\nError in demo: {str(e)}")
        import traceback
        traceback.print_exc()
    # Note: No need for the finally block with task cancellation here -
    # asyncio.run() handles the event loop cleanup automatically