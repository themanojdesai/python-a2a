"""
Example 05: Streaming UI Integration

This example demonstrates how to integrate A2A streaming with user interfaces,
including:
1. Simple CLI UI with real-time updates
2. Web interface using Server-Sent Events (SSE)
3. Interactive streaming responses

Key concepts:
- UI rendering of streamed content
- Client-side SSE handling
- Interactive streaming controls
- Progress visualization

Prerequisites:
- Install additional requirements: pip install flask tqdm colorama
"""

import asyncio
import json
import os
import random
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import AsyncGenerator, Dict, List, Optional, Union

import colorama
from colorama import Fore, Style
from flask import Flask, Response, render_template_string, request
from tqdm import tqdm

# Import from the A2A library
from python_a2a.client import A2AClient
from python_a2a.client.streaming import StreamingClient
from python_a2a.models.message import Message, MessageRole
from python_a2a.models.content import TextContent
from python_a2a.models.agent import AgentCard
from python_a2a.server.base import BaseA2AServer
from python_a2a.server.http import run_server

# Initialize colorama for cross-platform terminal colors
colorama.init()

# HTML Template for web UI
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>A2A Streaming Demo</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            max-width: 800px; 
            margin: 0 auto; 
            padding: 20px;
        }
        #output {
            min-height: 200px;
            border: 1px solid #ccc;
            padding: 10px;
            margin-bottom: 20px;
            white-space: pre-wrap;
            overflow-y: auto;
        }
        .progress-bar {
            width: 100%;
            background-color: #f3f3f3;
            border-radius: 5px;
            margin-bottom: 10px;
        }
        .progress {
            height: 20px;
            background-color: #4CAF50;
            border-radius: 5px;
            transition: width 0.3s ease;
            text-align: center;
            color: white;
        }
        .control-panel {
            display: flex;
            justify-content: space-between;
            margin-bottom: 20px;
        }
        button {
            padding: 8px 16px;
            border: none;
            border-radius: 4px;
            background-color: #4CAF50;
            color: white;
            cursor: pointer;
        }
        button:hover {
            background-color: #45a049;
        }
        button:disabled {
            background-color: #cccccc;
            cursor: not-allowed;
        }
        input {
            flex-grow: 1;
            padding: 8px;
            margin-right: 10px;
            border: 1px solid #ccc;
            border-radius: 4px;
        }
        .controls {
            margin-top: 10px;
        }
        .speed-control {
            margin-top: 10px;
        }
        .thinking {
            color: #999;
            font-style: italic;
        }
    </style>
</head>
<body>
    <h1>A2A Streaming UI Demo</h1>
    
    <div class="progress-bar">
        <div id="progress" class="progress" style="width: 0%">0%</div>
    </div>
    
    <div id="output"></div>
    
    <div class="control-panel">
        <input type="text" id="query" placeholder="Enter your query...">
        <button id="send">Send</button>
    </div>
    
    <div class="controls">
        <button id="pause" disabled>Pause</button>
        <button id="resume" disabled>Resume</button>
        <button id="cancel" disabled>Cancel</button>
    </div>
    
    <div class="speed-control">
        <label for="speed">Stream Speed:</label>
        <select id="speed">
            <option value="1">Normal</option>
            <option value="2">Fast</option>
            <option value="0.5">Slow</option>
        </select>
    </div>

    <script>
        const outputElement = document.getElementById('output');
        const progressElement = document.getElementById('progress');
        const queryInput = document.getElementById('query');
        const sendButton = document.getElementById('send');
        const pauseButton = document.getElementById('pause');
        const resumeButton = document.getElementById('resume');
        const cancelButton = document.getElementById('cancel');
        const speedSelect = document.getElementById('speed');
        
        let eventSource = null;
        let isPaused = false;
        let chunks = [];
        let totalChunks = 0;
        let streamId = null;
        
        sendButton.addEventListener('click', startStreaming);
        pauseButton.addEventListener('click', pauseStream);
        resumeButton.addEventListener('click', resumeStream);
        cancelButton.addEventListener('click', cancelStream);
        
        queryInput.addEventListener('keypress', function(event) {
            if (event.key === 'Enter') {
                startStreaming();
            }
        });
        
        function startStreaming() {
            const query = queryInput.value.trim();
            if (!query) return;
            
            // Clear previous output
            outputElement.innerHTML = '<span class="thinking">Thinking...</span>';
            progressElement.style.width = '0%';
            progressElement.textContent = '0%';
            chunks = [];
            totalChunks = 0;
            
            // Disable input during streaming
            queryInput.disabled = true;
            sendButton.disabled = true;
            pauseButton.disabled = false;
            cancelButton.disabled = false;
            
            // Close existing EventSource if any
            if (eventSource) {
                eventSource.close();
            }
            
            // Create a new EventSource with the current speed setting
            const speedFactor = speedSelect.value;
            eventSource = new EventSource(`/stream?query=${encodeURIComponent(query)}&speed=${speedFactor}`);
            
            eventSource.onmessage = function(event) {
                // Parse the event data
                const data = JSON.parse(event.data);
                
                if (data.type === 'connect' && data.stream_id) {
                    streamId = data.stream_id;
                    console.log('Connected to stream:', streamId);
                }
                else if (data.type === 'chunk') {
                    chunks.push(data.content);
                    totalChunks = data.total_chunks || totalChunks;
                    
                    // Update the output
                    outputElement.innerHTML = chunks.join('');
                    
                    // Update progress
                    const progress = Math.min(Math.round((chunks.length / totalChunks) * 100), 100);
                    progressElement.style.width = `${progress}%`;
                    progressElement.textContent = `${progress}%`;
                }
                else if (data.type === 'complete') {
                    // Stream complete
                    finishStream();
                }
                else if (data.type === 'error') {
                    outputElement.innerHTML += `<div style="color: red">Error: ${data.message}</div>`;
                    finishStream();
                }
            };
            
            eventSource.onerror = function() {
                outputElement.innerHTML += '<div style="color: red">Connection error. Please try again.</div>';
                finishStream();
            };
        }
        
        function pauseStream() {
            if (eventSource && !isPaused && streamId) {
                isPaused = true;
                fetch(`/pause_stream?stream_id=${streamId}`).then(response => response.json())
                .then(data => {
                    pauseButton.disabled = true;
                    resumeButton.disabled = false;
                })
                .catch(error => {
                    console.error('Error pausing stream:', error);
                });
            }
        }
        
        function resumeStream() {
            if (eventSource && isPaused && streamId) {
                isPaused = false;
                fetch(`/resume_stream?stream_id=${streamId}`).then(response => response.json())
                .then(data => {
                    pauseButton.disabled = false;
                    resumeButton.disabled = true;
                })
                .catch(error => {
                    console.error('Error resuming stream:', error);
                });
            }
        }
        
        function cancelStream() {
            if (eventSource && streamId) {
                fetch(`/cancel_stream?stream_id=${streamId}`).then(response => response.json())
                .then(data => {
                    finishStream();
                })
                .catch(error => {
                    console.error('Error canceling stream:', error);
                    finishStream();
                });
            }
        }
        
        function finishStream() {
            if (eventSource) {
                eventSource.close();
                eventSource = null;
            }
            
            // Enable input controls
            queryInput.disabled = false;
            sendButton.disabled = false;
            pauseButton.disabled = true;
            resumeButton.disabled = true;
            cancelButton.disabled = true;
            isPaused = false;
            streamId = null;
        }
    </script>
</body>
</html>
"""


class UIStreamingServer(BaseA2AServer):
    """A2A server with UI-oriented streaming capabilities."""
    
    def __init__(self, name="UI Streaming Server"):
        # BaseA2AServer doesn't have a defined __init__, so no need to call super().__init__()
        self.name = name
        self.agent_card = AgentCard(
            name=name,
            description="UI-oriented streaming A2A agent",
            url="http://localhost:8080",  # Default, will be updated
            version="1.0.0",
            capabilities={"streaming": True}
        )
        self.stream_paused = {}  # Track pause state for each stream
        self.stream_canceled = {}  # Track cancel state for each stream
        self.responses = {}  # Store prepared responses
    
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
        
        # Generate a simple response
        sentences = self.prepare_response(query)
        response_text = " ".join(sentences[:3]) + " [Use streaming for the full response]"
        
        # Create and return response message
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
        
    def prepare_response(self, query: str) -> List[str]:
        """Prepare a response based on the query."""
        # Generate a response with 10-20 sentences
        num_sentences = random.randint(10, 20)
        sentences = []
        
        topics = [
            "Streaming data processing",
            "Real-time UI updates",
            "Server-sent events",
            "Interactive user interfaces",
            "Progress visualization",
            "Client-side rendering",
            "Push notifications",
            "WebSockets vs SSE",
            "UI/UX best practices",
            "Responsive design",
        ]
        
        # Generate some sentences
        for i in range(num_sentences):
            topic = random.choice(topics)
            templates = [
                f"When implementing {topic}, it's important to consider the user experience.",
                f"One key aspect of {topic} is ensuring smooth data flow.",
                f"Modern applications often leverage {topic} for better interactivity.",
                f"The benefits of {topic} include improved user engagement and feedback.",
                f"Developers should carefully test {topic} implementations across different devices.",
                f"A common challenge with {topic} is handling network interruptions gracefully.",
                f"Recent advances in {topic} have made it more accessible to developers.",
                f"When designing {topic} solutions, always prioritize performance and reliability.",
                f"The future of {topic} looks promising as more tools and frameworks emerge.",
                f"Successful {topic} requires attention to both technical and user experience details."
            ]
            sentences.append(random.choice(templates))
        
        return sentences

    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """Stream a response with UI considerations."""
        # Extract query from message
        query = message.content.text if hasattr(message.content, "text") else "No query provided"
        
        # Generate a unique stream ID
        stream_id = f"{time.time()}_{random.randint(1000, 9999)}"
        self.stream_paused[stream_id] = False
        self.stream_canceled[stream_id] = False
        
        # Prepare the response
        sentences = self.prepare_response(query)
        self.responses[stream_id] = sentences
        
        # Initial processing delay
        await asyncio.sleep(1)
        
        # Stream each sentence
        for i, sentence in enumerate(sentences):
            # Check if stream was canceled
            if self.stream_canceled.get(stream_id, False):
                break
                
            # Check if stream is paused and wait if needed
            while self.stream_paused.get(stream_id, False):
                await asyncio.sleep(0.1)
                # Check for cancellation during pause
                if self.stream_canceled.get(stream_id, False):
                    break
            
            # Add a simulated thinking delay
            await asyncio.sleep(random.uniform(0.3, 0.7))
            
            # Yield the sentence as a chunk
            yield sentence
            
        # Clean up
        if stream_id in self.stream_paused:
            del self.stream_paused[stream_id]
        if stream_id in self.stream_canceled:
            del self.stream_canceled[stream_id]
        if stream_id in self.responses:
            del self.responses[stream_id]


class CliStreamingClient:
    """A client that demonstrates CLI-based streaming visualization."""
    
    def __init__(self, server_url: str):
        self.server_url = server_url
        self.client = StreamingClient(server_url)
        
    async def send_query(self, query: str):
        """Send a query and display the response with fancy CLI visualization."""
        message = Message(content=TextContent(text=query), role=MessageRole.USER)
        
        print(f"\n{Fore.CYAN}💬 You: {Style.RESET_ALL}{query}")
        print(f"{Fore.YELLOW}⏳ Agent is thinking...{Style.RESET_ALL}")
        
        # Prepare for streaming display
        response_chunks = []
        start_time = time.time()
        chunk_times = []
        
        # Create a progress bar that will update as chunks arrive
        with tqdm(desc="Receiving", unit="chunks", dynamic_ncols=True) as pbar:
            async for chunk in self.client.stream_response(message):
                # Record chunk timestamp
                chunk_times.append(time.time() - start_time)
                
                # Extract text from chunk if it's a dictionary
                if isinstance(chunk, dict):
                    if "content" in chunk:
                        chunk_text = chunk["content"]
                    else:
                        # Try to convert dict to string
                        try:
                            chunk_text = json.dumps(chunk)
                        except:
                            chunk_text = str(chunk)
                else:
                    chunk_text = str(chunk)
                
                # Add to our accumulated response
                response_chunks.append(chunk_text)
                
                # Update progress bar
                pbar.update(1)
                
                # Clear line and print current accumulated response
                if os.name == 'nt':  # Windows
                    os.system('cls')
                else:  # Unix/Linux/MacOS
                    os.system('clear')
                
                print(f"\n{Fore.CYAN}💬 You: {Style.RESET_ALL}{query}")
                print(f"\n{Fore.GREEN}🤖 Agent: {Style.RESET_ALL}", end="")
                print("".join(response_chunks))
                
                # Simulate interactive rendering
                await asyncio.sleep(0.05)
        
        # Calculate and display metrics
        elapsed = time.time() - start_time
        chunks = len(response_chunks)
        chars = sum(len(chunk) for chunk in response_chunks)
        
        print(f"\n{Fore.BLUE}📊 Streaming Metrics:{Style.RESET_ALL}")
        print(f"  ⏱️  Total time: {elapsed:.2f}s")
        print(f"  🧩 Chunks: {chunks}")
        print(f"  📝 Characters: {chars}")
        if elapsed > 0:
            print(f"  🚀 Speed: {chars/elapsed:.2f} chars/sec")
        else:
            print(f"  🚀 Speed: N/A (elapsed time too short)")
        
        # Calculate and show chunk timing
        if len(chunk_times) > 1:
            delays = [chunk_times[i] - chunk_times[i-1] for i in range(1, len(chunk_times))]
            avg_delay = sum(delays) / len(delays)
            print(f"  ⏱️  Average chunk delay: {avg_delay*1000:.2f}ms")
            
        # Return the combined response as a string
        full_response = "".join(response_chunks)
        return full_response


class WebStreamingInterface:
    """A web interface for streaming A2A responses."""
    
    def __init__(self, server: UIStreamingServer, host: str = "localhost", port: int = 8080):
        self.server = server
        self.app = Flask(__name__)
        self.host = host
        self.port = port
        self.active_streams = {}
        self.setup_routes()
        
    def setup_routes(self):
        """Set up the Flask routes."""
        @self.app.route('/')
        def index():
            return render_template_string(HTML_TEMPLATE)
        
        @self.app.route('/stream')
        def stream():
            query = request.args.get('query', '')
            speed_factor = float(request.args.get('speed', '1.0'))
            
            # Generate a stream ID
            stream_id = f"{time.time()}_{random.randint(1000, 9999)}"
            self.active_streams[stream_id] = {
                'query': query,
                'paused': False,
                'canceled': False,
                'speed_factor': speed_factor
            }
            
            def generate():
                """Generate SSE events."""
                # Send initial event to establish connection
                yield f'data: {json.dumps({"type": "connect", "stream_id": stream_id})}\n\n'
                
                # Prepare response
                sentences = self.server.prepare_response(query)
                total_chunks = len(sentences)
                
                # Send sentences as chunks
                for i, sentence in enumerate(sentences):
                    # Check if stream was canceled
                    if self.active_streams.get(stream_id, {}).get('canceled', False):
                        break
                        
                    # Check if stream is paused and wait if needed
                    while self.active_streams.get(stream_id, {}).get('paused', False):
                        time.sleep(0.1)
                        # Check for cancellation during pause
                        if self.active_streams.get(stream_id, {}).get('canceled', False):
                            break
                    
                    # Adjust delay based on speed factor
                    speed = self.active_streams.get(stream_id, {}).get('speed_factor', 1.0)
                    time.sleep(random.uniform(0.3, 0.7) / speed)
                    
                    # Send chunk event
                    data = {
                        'type': 'chunk',
                        'content': sentence + ' ',  # Add space for readability
                        'chunk_index': i,
                        'total_chunks': total_chunks,
                        'timestamp': datetime.now().isoformat()
                    }
                    yield f'data: {json.dumps(data)}\n\n'
                
                # Send completion event
                yield f'data: {json.dumps({"type": "complete"})}\n\n'
                
                # Clean up
                if stream_id in self.active_streams:
                    del self.active_streams[stream_id]
            
            return Response(generate(), mimetype='text/event-stream')
        
        @self.app.route('/pause_stream')
        def pause_stream():
            stream_id = request.args.get('stream_id')
            if stream_id and stream_id in self.active_streams:
                self.active_streams[stream_id]['paused'] = True
            return json.dumps({'status': 'paused'})
        
        @self.app.route('/resume_stream')
        def resume_stream():
            stream_id = request.args.get('stream_id')
            if stream_id and stream_id in self.active_streams:
                self.active_streams[stream_id]['paused'] = False
            return json.dumps({'status': 'resumed'})
        
        @self.app.route('/cancel_stream')
        def cancel_stream():
            stream_id = request.args.get('stream_id')
            if stream_id and stream_id in self.active_streams:
                self.active_streams[stream_id]['canceled'] = True
            return json.dumps({'status': 'canceled'})
    
    def run(self):
        """Run the Flask application."""
        self.app.run(host=self.host, port=self.port, debug=True, threaded=True)


async def cli_demo():
    """Run the CLI streaming demo."""
    print(f"{Fore.BLUE}=== A2A CLI Streaming Demo ==={Style.RESET_ALL}")
    print("This demo shows how to render streaming responses in a terminal UI.")
    
    # Create server and server future objects
    server = None
    server_future = None
    executor = None
    
    try:
        # Start server in a separate thread
        server = UIStreamingServer()
        server_port = 8079
        
        # Update the server's agent card URL
        server.agent_card.url = f"http://localhost:{server_port}"
        
        executor = ThreadPoolExecutor()
        server_future = executor.submit(
            run_server, server, "localhost", server_port, debug=False
        )
        
        # Wait for server to start
        await asyncio.sleep(2)
        
        # Create client
        client = CliStreamingClient(f"http://localhost:{server_port}")
        
        # Sample queries
        queries = [
            "Tell me about streaming data visualization",
            "How does server-sent events work?",
            "What are best practices for real-time UIs?",
        ]
        
        # Let the user choose a query or enter their own
        print(f"\n{Fore.YELLOW}Choose a query or enter your own:{Style.RESET_ALL}")
        for i, q in enumerate(queries, 1):
            print(f"{i}. {q}")
        print(f"0. Enter your own query")
        
        choice = input(f"\n{Fore.CYAN}Enter your choice (0-{len(queries)}): {Style.RESET_ALL}")
        
        try:
            choice_num = int(choice)
            if 1 <= choice_num <= len(queries):
                query = queries[choice_num - 1]
            else:
                query = input(f"\n{Fore.CYAN}Enter your query: {Style.RESET_ALL}")
        except ValueError:
            query = input(f"\n{Fore.CYAN}Enter your query: {Style.RESET_ALL}")
        
        # Send query and display streaming response
        await client.send_query(query)
        
    except Exception as e:
        # Handle any errors that occur during the demo
        print(f"\n{Fore.RED}Error in CLI demo: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Clean up
        print(f"\n{Fore.BLUE}Demo complete. Shutting down server...{Style.RESET_ALL}")
        
        # Safely shut down the executor
        if executor:
            executor.shutdown(wait=False)


def web_demo():
    """Run the web streaming demo."""
    try:
        # Create server
        server = UIStreamingServer()
        
        # Update the server's agent card URL
        server.agent_card.url = "http://localhost:8080"
        
        # Create web interface
        web_interface = WebStreamingInterface(server, port=8080)
        
        print(f"{Fore.BLUE}=== A2A Web Streaming Demo ==={Style.RESET_ALL}")
        print(f"Web interface starting at http://localhost:8080")
        print("Press Ctrl+C to stop")
        
        # Run the web interface
        try:
            web_interface.run()
        except KeyboardInterrupt:
            print(f"\n{Fore.BLUE}Demo stopped by user.{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}Error in web demo: {str(e)}{Style.RESET_ALL}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print(f"{Fore.GREEN}A2A Streaming UI Integration Demo{Style.RESET_ALL}")
    print("This example demonstrates different ways to integrate streaming with UIs.")
    print("\nChoose a demo to run:")
    print("1. CLI Streaming Demo (interactive terminal UI)")
    print("2. Web Streaming Demo (browser-based UI with SSE)")
    
    choice = input("Enter choice (1 or 2): ")
    
    try:
        if choice == "1":
            # Run CLI demo
            asyncio.run(cli_demo())
        else:
            # Run web demo (default)
            web_demo()
    except KeyboardInterrupt:
        print(f"\n{Fore.BLUE}Demo stopped by user.{Style.RESET_ALL}")