#!/usr/bin/env python
"""
03_streaming_llm_integration.py - LLM Streaming Integration

This example demonstrates how to integrate LLM API streaming with the A2A protocol.
It shows how to bridge between LLM streaming APIs and A2A streaming, enabling
real-time delivery of LLM-generated content.

Key concepts demonstrated:
- Integrating A2A streaming with LLM provider APIs
- Bridging LLM streaming to A2A streaming
- Provider-agnostic LLM streaming wrapper
- Handling provider-specific token/chunk formats

Note: This example uses mock LLM providers to demonstrate concepts without requiring
actual API keys. In a real application, you would replace these with actual LLM APIs.

Usage:
    python 03_streaming_llm_integration.py [--provider provider] [--query query]
    
Options:
    --provider {mock_openai,mock_anthropic,mock_bedrock}  LLM provider to use
    --query QUERY                                         Query to send to the LLM
    --port PORT                                           Port for the server
    -i, --interactive                                     Enable interactive mode
"""

import asyncio
import sys
import time
import random
import threading
import argparse
from typing import AsyncGenerator, Dict, Any, List, Optional, Callable, Union

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
CYAN = "\033[36m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Default configuration
DEFAULT_QUERY = "Explain how LLMs generate text in a streaming fashion"
DEFAULT_PROVIDER = "mock_openai"


# ===============================================================
# Mock LLM Provider Implementations
# In a real application, these would be replaced with actual API clients
# ===============================================================

class MockOpenAIStream:
    """
    Mock OpenAI compatible streaming API client.
    
    This mimics OpenAI's streaming API pattern without requiring an actual API key.
    In a real application, you would replace this with the actual OpenAI client.
    """
    
    def __init__(self, system_prompt: str = "You are a helpful assistant"):
        """Initialize with a system prompt."""
        self.system_prompt = system_prompt
    
    async def generate(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming response mimicking OpenAI's API.
        
        This method yields completion chunks in OpenAI format.
        
        Args:
            prompt: User prompt
            
        Yields:
            Chunks mimicking OpenAI's stream format
        """
        # Log operation
        print(f"[OpenAI] Generating streaming response for: {prompt[:50]}...")
        
        # Generate a response based on the prompt
        response = self._mock_generate_response(prompt)
        
        # Split into "tokens" (here we just fake token-by-token streaming)
        tokens = []
        for word in response.split():
            # Split longer words into subtokens
            if len(word) > 5 and random.random() < 0.3:
                split_point = random.randint(2, len(word) - 2)
                tokens.append(word[:split_point])
                tokens.append(word[split_point:])
            else:
                tokens.append(word)
        
        # Stream the response token by token
        token_id = 0
        for token in tokens:
            # Simulate thinking
            await asyncio.sleep(random.uniform(0.05, 0.15))
            
            # Format in OpenAI-like chunk format
            chunk = {
                "choices": [{
                    "delta": {"content": token + " "},
                    "finish_reason": None,
                    "index": 0
                }],
                "created": int(time.time()),
                "id": f"mock-completion-{int(time.time())}-{token_id}",
                "model": "mock-gpt-3.5-turbo",
                "object": "chat.completion.chunk"
            }
            
            # Log for diagnostic purposes
            print(f"[OpenAI] Yielding token: '{token}'")
            
            # Yield the token
            yield chunk
            token_id += 1
        
        # Send the final completion message
        yield {
            "choices": [{
                "delta": {},
                "finish_reason": "stop",
                "index": 0
            }],
            "created": int(time.time()),
            "id": f"mock-completion-{int(time.time())}-{token_id}",
            "model": "mock-gpt-3.5-turbo",
            "object": "chat.completion.chunk"
        }
    
    def _mock_generate_response(self, prompt: str) -> str:
        """Generate a mock response based on the prompt."""
        prompt_lower = prompt.lower()
        
        if "llm" in prompt_lower and "stream" in prompt_lower:
            return (
                "LLMs generate text in a streaming fashion by producing tokens one at a time. "
                "Each token represents a small piece of text, often part of a word. "
                "When streaming is enabled, these tokens are sent to the client as soon as they're generated, "
                "rather than waiting for the entire response to be complete. "
                "This creates a real-time experience where text appears progressively. "
                "The OpenAI API implements this using server-sent events (SSE), "
                "where each token is delivered as a JSON object containing the delta of new text. "
                "The client receives these chunks and appends them to build the complete response. "
                "Streaming significantly improves perceived latency and user experience, "
                "as users can begin reading the response immediately rather than waiting for the full generation."
            )
        else:
            return (
                "I'm a mock OpenAI API demo that simulates streaming text generation. "
                "In a real application, this would connect to the actual OpenAI API using your API key. "
                "The pattern would be the same - the API generates tokens one by one, "
                "and they're delivered to the client as soon as they're available. "
                "This creates a smooth, real-time experience for the user. "
                "Try asking about 'how LLMs generate text in a streaming fashion' for a more specific response."
            )


class MockAnthropicStream:
    """
    Mock Anthropic Claude streaming API client.
    
    This mimics Anthropic's streaming API pattern without requiring an actual API key.
    In a real application, you would replace this with the actual Anthropic client.
    """
    
    def __init__(self, system_prompt: str = ""):
        """Initialize with a system prompt."""
        self.system_prompt = system_prompt
    
    async def generate(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming response mimicking Anthropic's API.
        
        This method yields completion events in Anthropic's format.
        
        Args:
            prompt: User prompt
            
        Yields:
            Chunks mimicking Anthropic's stream format
        """
        # Log operation
        print(f"[Anthropic] Generating streaming response for: {prompt[:50]}...")
        
        # Generate a response based on the prompt
        response = self._mock_generate_response(prompt)
        
        # Split into "token" chunks (simulating Claude's token chunking)
        chunks = []
        current_chunk = ""
        
        for word in response.split():
            current_chunk += word + " "
            # Claude typically yields multi-word chunks
            if len(current_chunk) > 15 or random.random() < 0.2:
                chunks.append(current_chunk)
                current_chunk = ""
        
        # Add any remaining text
        if current_chunk:
            chunks.append(current_chunk)
        
        # Stream the response chunk by chunk
        for i, chunk in enumerate(chunks):
            # Simulate thinking
            await asyncio.sleep(random.uniform(0.1, 0.25))
            
            # Format in Anthropic-like event format
            event = {
                "type": "content_block_delta",
                "delta": {
                    "type": "text_delta",
                    "text": chunk
                },
                "index": 0
            }
            
            # Log for diagnostic purposes
            print(f"[Anthropic] Yielding chunk {i+1}/{len(chunks)}: '{chunk}'")
            
            # Yield the chunk
            yield event
        
        # Send the completion event
        yield {
            "type": "message_stop",
            "message": {"id": f"msg_{int(time.time())}_{random.randint(1000, 9999)}"}
        }
    
    def _mock_generate_response(self, prompt: str) -> str:
        """Generate a mock response based on the prompt."""
        prompt_lower = prompt.lower()
        
        if "llm" in prompt_lower and "stream" in prompt_lower:
            return (
                "Language models like Claude generate text through a token-by-token prediction process. "
                "When streaming is enabled, each small group of tokens is sent to the client immediately after generation, "
                "rather than waiting for the full response to be complete. "
                "In Anthropic's API specifically, we send these tokens in chunks as they become available. "
                "Our streaming implementation uses a Server-Sent Events (SSE) approach, with each chunk "
                "containing the new text to be appended to the existing response. "
                "The client-side library receives these chunks and builds up the complete response incrementally. "
                "This approach creates a more interactive user experience, as the human can start reading "
                "the response as it's being generated, rather than waiting for potentially several seconds. "
                "It also enables applications to implement features like interruptions or redirections mid-stream."
            )
        else:
            return (
                "I'm simulating Anthropic Claude's streaming response pattern. "
                "In a real application, this would connect to Anthropic's API with your API key. "
                "Claude's streaming API yields text in chunks, usually containing multiple tokens, "
                "which creates a smooth reading experience for users. "
                "The pattern is similar across most modern LLM providers, though the exact format "
                "of the chunks varies. Try asking about 'how LLMs generate text in a streaming fashion' "
                "for a more detailed explanation of streaming text generation."
            )


class MockBedrockStream:
    """
    Mock AWS Bedrock streaming API client.
    
    This mimics AWS Bedrock's streaming API pattern without requiring actual AWS credentials.
    In a real application, you would replace this with the actual Bedrock client.
    """
    
    def __init__(self, model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"):
        """Initialize with a model ID."""
        self.model_id = model_id
    
    async def generate(self, prompt: str) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Generate a streaming response mimicking AWS Bedrock's API.
        
        This method yields completion chunks in Bedrock's format.
        
        Args:
            prompt: User prompt
            
        Yields:
            Chunks mimicking Bedrock's stream format
        """
        # Log operation
        print(f"[Bedrock] Generating streaming response with model {self.model_id}")
        print(f"[Bedrock] Prompt: {prompt[:50]}...")
        
        # Generate a response based on the prompt
        response = self._mock_generate_response(prompt)
        
        # Split into chunks (Bedrock typically yields larger chunks)
        chunks = []
        words = response.split()
        chunk_size = random.randint(5, 15)  # Random chunk size for variety
        
        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i+chunk_size])
            chunks.append(chunk)
        
        # Stream the response chunk by chunk
        for i, chunk in enumerate(chunks):
            # Simulate thinking
            await asyncio.sleep(random.uniform(0.15, 0.4))
            
            # Create chunk IDs and completion ID
            chunk_id = f"chunk-{i+1}-{int(time.time())}"
            completion_id = f"completion-{int(time.time())}"
            
            # Format in Bedrock-like event format (provider-specific format)
            if "anthropic" in self.model_id:
                # Anthropic-type format
                event = {
                    "chunk": {
                        "bytes": chunk.encode()
                    },
                    "completionReason": None,
                    "amazon-bedrock-invocationId": completion_id,
                    "amazon-bedrock-outputType": "chunk"
                }
            else:
                # Generic format for other models
                event = {
                    "chunk": {
                        "bytes": chunk.encode()
                    },
                    "completionReason": None
                }
            
            # Log for diagnostic purposes
            print(f"[Bedrock] Yielding chunk {i+1}/{len(chunks)} ({len(chunk)} chars)")
            
            # Yield the chunk
            yield event
        
        # Send the completion event
        yield {
            "completionReason": "COMPLETE",
            "amazon-bedrock-invocationId": f"completion-{int(time.time())}",
            "amazon-bedrock-outputType": "completion"
        }
    
    def _mock_generate_response(self, prompt: str) -> str:
        """Generate a mock response based on the prompt."""
        prompt_lower = prompt.lower()
        
        if "llm" in prompt_lower and "stream" in prompt_lower:
            return (
                "AWS Bedrock provides streaming capabilities for supported foundation models, including those from Anthropic, "
                "AI21 Labs, Cohere, and others. Each model provider implements streaming slightly differently, but the general "
                "concept is consistent: tokens are generated one by one and sent to the client immediately rather than waiting "
                "for the full response. In Bedrock specifically, streaming works through the InvokeModelWithResponseStream API. "
                "This returns a stream of chunks, with each chunk containing a portion of the generated text. The chunks are "
                "delivered as they become available, enabling real-time display of the model's output. This is particularly "
                "valuable for longer responses, as it significantly reduces the perceived latency. The exact format of the "
                "stream depends on the underlying model provider. For example, Claude models return chunks that include "
                "both the generated text and metadata about the generation process. The AWS SDK provides utilities to "
                "handle this streaming pattern, making it relatively straightforward to implement in applications."
            )
        else:
            return (
                "I'm demonstrating AWS Bedrock's streaming pattern. In a real application, this would connect "
                "to AWS Bedrock using your AWS credentials and the boto3 SDK. Bedrock can stream responses from "
                "various foundation models like Claude, AI21, and Cohere, with each having slightly different "
                "chunk formats. Generally, you would invoke the model with streaming enabled, and then process "
                "the chunks as they arrive. This creates a responsive experience for users, especially with "
                "longer generations. Try asking about 'how LLMs generate text in a streaming fashion' for "
                "a more specific explanation of how streaming works in AWS Bedrock."
            )


# ===============================================================
# LLM Server with A2A Streaming
# ===============================================================

class LLMStreamingServer(BaseA2AServer):
    """
    A2A streaming server that integrates with LLM providers.
    
    This server bridges LLM streaming APIs to the A2A streaming protocol,
    enabling real-time streaming of LLM-generated content.
    """
    
    def __init__(
        self, 
        url: str = "http://localhost:8000",
        provider: str = "mock_openai",
        system_prompt: str = "You are a helpful AI assistant"
    ):
        """
        Initialize the LLM streaming server.
        
        Args:
            url: Server URL
            provider: LLM provider to use
            system_prompt: System prompt for the LLM
        """
        # Create an agent card with streaming and LLM capabilities
        self.agent_card = AgentCard(
            name=f"LLM Streaming Demo ({provider})",
            description="Demonstrates integration of LLM streaming APIs with A2A protocol",
            url=url,
            version="1.0.0",
            capabilities={
                "streaming": True,
                "llm_provider": provider,
                "supports_system_prompt": True
            }
        )
        
        # Store configuration
        self.provider = provider
        self.system_prompt = system_prompt
        
        # Initialize the appropriate LLM client based on provider
        self._initialize_llm_client()
        
        # Metrics tracking
        self.request_count = 0
        self.total_tokens = 0
    
    def _initialize_llm_client(self):
        """Initialize the LLM client based on the selected provider."""
        if self.provider == "mock_openai":
            self.llm_client = MockOpenAIStream(system_prompt=self.system_prompt)
        elif self.provider == "mock_anthropic":
            self.llm_client = MockAnthropicStream(system_prompt=self.system_prompt)
        elif self.provider == "mock_bedrock":
            self.llm_client = MockBedrockStream()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
        
        print(f"[Server] Initialized {self.provider} LLM client")
    
    def handle_message(self, message: Message) -> Message:
        """
        Handle non-streaming messages by generating a complete response.
        
        Args:
            message: The incoming message
            
        Returns:
            Response message with LLM-generated content
        """
        # Extract query
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # For non-streaming, we'll generate a placeholder
        response_text = (
            f"This is a non-streaming response from the {self.provider} LLM integration. "
            f"In a real application, this would call the LLM synchronously. "
            f"For best results, use streaming with this server - the response will be "
            f"delivered incrementally as the LLM generates it."
        )
        
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """
        Stream a response from the LLM provider.
        
        This method bridges between the LLM's streaming API and the A2A protocol.
        
        Args:
            message: The incoming message
            
        Yields:
            Chunks of the LLM-generated response
        """
        # Track request count
        self.request_count += 1
        request_id = self.request_count
        
        # Extract query
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        print(f"[Server] Request #{request_id}: Streaming response from {self.provider}")
        print(f"[Server] Query: {query[:50]}...")
        
        # Get the LLM stream
        token_count = 0
        try:
            # Stream from the LLM provider
            async for chunk in self.llm_client.generate(query):
                # Extract text based on provider format
                text = self._extract_text_from_provider_chunk(chunk)
                
                # Skip empty chunks
                if not text:
                    continue
                
                # Update metrics
                token_count += 1
                self.total_tokens += 1
                
                # Log the chunk (for demonstration)
                if token_count % 10 == 0 or token_count <= 3:
                    print(f"[Server] Request #{request_id}: Token {token_count}, text: '{text}'")
                
                # Yield to A2A streaming client - yield string, not dict
                yield text
                
            print(f"[Server] Request #{request_id}: Complete - {token_count} tokens generated")
            print(f"[Server] Total requests: {self.request_count}, total tokens: {self.total_tokens}")
            
        except Exception as e:
            # Log errors but don't crash
            print(f"[Server] Error in LLM streaming: {e}")
            # We could yield an error message here if desired
            yield f"Error during LLM response generation: {str(e)}"
    
    def _extract_text_from_provider_chunk(self, chunk: Dict[str, Any]) -> str:
        """
        Extract text from a provider-specific chunk format.
        
        Args:
            chunk: Provider-specific chunk object
            
        Returns:
            Extracted text content
        """
        # Handle provider-specific formats
        if self.provider == "mock_openai":
            # OpenAI format: {"choices": [{"delta": {"content": "text"}}]}
            try:
                if "choices" in chunk and chunk["choices"]:
                    delta = chunk["choices"][0].get("delta", {})
                    if "content" in delta:
                        return delta["content"]
            except (KeyError, IndexError):
                pass
                
        elif self.provider == "mock_anthropic":
            # Anthropic format: {"type": "content_block_delta", "delta": {"text": "text"}}
            try:
                if chunk.get("type") == "content_block_delta":
                    delta = chunk.get("delta", {})
                    if delta.get("type") == "text_delta" and "text" in delta:
                        return delta["text"]
            except (KeyError, AttributeError):
                pass
                
        elif self.provider == "mock_bedrock":
            # Bedrock format: {"chunk": {"bytes": b"text"}}
            try:
                if "chunk" in chunk and "bytes" in chunk["chunk"]:
                    # Handle both byte and string formats
                    content = chunk["chunk"]["bytes"]
                    if isinstance(content, bytes):
                        return content.decode("utf-8")
                    return str(content)
            except (KeyError, AttributeError, UnicodeDecodeError):
                pass
        
        # If we can't extract text in a provider-specific way, try a generic approach
        if isinstance(chunk, dict):
            # Look for common text fields
            for key in ["text", "content", "message", "value", "data"]:
                if key in chunk and isinstance(chunk[key], str):
                    return chunk[key]
            
            # If it's JSON, convert to string
            return ""
        
        # If it's already a string
        if isinstance(chunk, str):
            return chunk
            
        # Last resort - try string conversion
        try:
            return str(chunk)
        except:
            return ""


# ===============================================================
# Client and Demo Functions
# ===============================================================

class StreamingVisualizer:
    """
    Visualize streaming responses with real-time metrics.
    """
    
    def __init__(self, show_tokens: bool = True, show_timing: bool = True):
        """Initialize visualizer with display options."""
        self.show_tokens = show_tokens
        self.show_timing = show_timing
        
        # Metrics
        self.start_time = time.time()
        self.token_count = 0
        self.total_chars = 0
        self.tokens = []
        self.full_text = ""
        
        # Display state
        self.last_update = 0
        self.update_interval = 0.2  # seconds
    
    def update_display(self):
        """Update the streaming metrics display."""
        current_time = time.time()
        elapsed = current_time - self.start_time
        
        # Only update occasionally to prevent flicker
        if current_time - self.last_update < self.update_interval:
            return
            
        self.last_update = current_time
        
        # Calculate metrics
        tokens_per_sec = self.token_count / elapsed if elapsed > 0 else 0
        chars_per_sec = self.total_chars / elapsed if elapsed > 0 else 0
        
        # Clear line and update
        sys.stdout.write("\r" + " " * 80 + "\r")
        sys.stdout.write(
            f"{CYAN}[{self.token_count} tokens | {self.total_chars} chars | "
            f"{elapsed:.1f}s | {tokens_per_sec:.1f} t/s | {chars_per_sec:.1f} c/s]{RESET}"
        )
        sys.stdout.flush()
    
    async def process_chunk(self, chunk: Union[str, Dict]):
        """
        Process a streaming chunk and update display.
        
        Args:
            chunk: Text chunk from the stream (string or dict)
        """
        # Extract text if it's a dictionary
        if isinstance(chunk, dict):
            if "content" in chunk:
                text = chunk["content"]
            elif "text" in chunk:
                text = chunk["text"]
            else:
                # Last resort, convert to string
                text = str(chunk)
        else:
            text = str(chunk)
        
        # Update metrics
        self.token_count += 1
        self.total_chars += len(text)
        self.tokens.append(text)
        self.full_text += text
        
        # Display the token if enabled
        if self.show_tokens:
            # Highlight tokens for visibility
            if self.token_count % 10 == 0:
                print(f"{YELLOW}{text}{RESET}", end="", flush=True)
            else:
                print(text, end="", flush=True)
        
        # Update metrics display
        if self.show_timing:
            self.update_display()
        
        # Small delay to allow UI updates
        await asyncio.sleep(0)
    
    def print_final_stats(self):
        """Print final statistics after streaming completes."""
        # Clear metrics line
        if self.show_timing:
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
        
        # Calculate final metrics
        elapsed = time.time() - self.start_time
        tokens_per_sec = self.token_count / elapsed if elapsed > 0 else 0
        chars_per_sec = self.total_chars / elapsed if elapsed > 0 else 0
        avg_token_size = self.total_chars / self.token_count if self.token_count else 0
        
        # Print summary
        print("\n" + "-" * 60)
        print(f"{GREEN}{BOLD}LLM Response Complete{RESET}")
        print(f"{GREEN}✓ Generated {self.token_count} tokens ({self.total_chars} characters){RESET}")
        print(f"{GREEN}✓ Time: {elapsed:.2f} seconds ({tokens_per_sec:.1f} tokens/sec){RESET}")
        if self.token_count > 0:
            print(f"{GREEN}✓ Average token size: {avg_token_size:.1f} characters{RESET}")


async def run_llm_streaming_demo(url: str, query: str):
    """
    Run the LLM streaming demo.
    
    Args:
        url: Server URL
        query: Query to send to the LLM
    """
    print(f"\n{BLUE}Query: \"{query}\"{RESET}")
    print(f"\n{BLUE}Streaming LLM response:{RESET}")
    print("-" * 60)
    
    # Create message
    message = Message(
        content=TextContent(text=query),
        role=MessageRole.USER
    )
    
    # Create streaming client
    client = StreamingClient(url)
    
    # Set up visualizer
    visualizer = StreamingVisualizer(show_tokens=True, show_timing=True)
    
    try:
        # Stream the response
        async for chunk in client.stream_response(message):
            await visualizer.process_chunk(chunk)
        
        # Print final stats
        visualizer.print_final_stats()
        
        return visualizer.full_text
        
    except Exception as e:
        print(f"\n\n{RED}Error during streaming: {str(e)}{RESET}")
        if visualizer.total_chars > 0:
            print(f"\n{YELLOW}Partial response ({visualizer.token_count} tokens):{RESET}")
            print(visualizer.full_text)
        return None


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
    
    # Create LLM streaming server
    server = LLMStreamingServer(
        url=server_url,
        provider=args.provider,
        system_prompt="You are a helpful AI assistant that explains concepts clearly."
    )
    
    # Start server in background thread
    print(f"{BLUE}Starting LLM streaming server with {args.provider} on port {port}...{RESET}")
    server_thread = threading.Thread(
        target=lambda: run_server(server, host="localhost", port=port),
        daemon=True
    )
    server_thread.start()
    
    # Wait for server to start
    await asyncio.sleep(1)
    
    # Run initial demo
    await run_llm_streaming_demo(server_url, args.query)
    
    # Interactive mode if requested
    if args.interactive:
        try:
            while True:
                print(f"\n{BLUE}Enter a query (or Ctrl+C to exit):{RESET}")
                next_query = input("> ")
                if next_query.strip():
                    await run_llm_streaming_demo(server_url, next_query)
                else:
                    print(f"{YELLOW}Query cannot be empty{RESET}")
        except KeyboardInterrupt:
            print(f"\n{BLUE}Exiting interactive mode{RESET}")


def main():
    """Parse arguments and run the example."""
    parser = argparse.ArgumentParser(description="LLM Streaming Integration Example")
    parser.add_argument("--provider", choices=["mock_openai", "mock_anthropic", "mock_bedrock"],
                       default=DEFAULT_PROVIDER, help="LLM provider to use")
    parser.add_argument("--query", default=DEFAULT_QUERY,
                       help="Query to send to the LLM")
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