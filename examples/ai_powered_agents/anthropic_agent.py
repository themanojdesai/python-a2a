#!/usr/bin/env python
"""
Anthropic-Powered A2A Agent

This example demonstrates how to create an A2A agent powered by Anthropic's Claude models.
It shows how to set up the agent, handle environment variables, and connect to the API.

To run:
    export ANTHROPIC_API_KEY=your_api_key
    python anthropic_agent.py [--port PORT] [--model MODEL]

Example:
    python anthropic_agent.py --port 5000 --model claude-3-haiku-20240307

Requirements:
    pip install "python-a2a[anthropic,server]"
"""

import sys
import os
import argparse
import socket
import time
import multiprocessing

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import python_a2a
    except ImportError:
        missing_deps.append("python-a2a")
    
    try:
        import flask
    except ImportError:
        missing_deps.append("flask")
    
    try:
        import anthropic
    except ImportError:
        missing_deps.append("anthropic")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required dependencies:")
        print("    pip install \"python-a2a[anthropic,server]\"")
        print("\nThen run this example again.")
        return False
    
    print("✅ All dependencies are installed correctly!")
    return True

def check_api_key():
    """Check if the Anthropic API key is available"""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("❌ ANTHROPIC_API_KEY environment variable not set!")
        print("\nPlease set your Anthropic API key with:")
        print("    export ANTHROPIC_API_KEY=your_api_key")
        print("\nThen run this example again.")
        return False
    
    # Mask the API key for display
    masked_key = api_key[:4] + "..." + api_key[-4:]
    print(f"✅ ANTHROPIC_API_KEY environment variable is set: {masked_key}")
    return True

def find_available_port(start_port=5000, max_tries=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_tries):
        try:
            # Try to create a socket on the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            # Port is already in use, try the next one
            continue
    
    # If we get here, no ports were available
    print(f"⚠️  Could not find an available port in range {start_port}-{start_port + max_tries - 1}")
    return start_port  # Return the start port as default

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Anthropic-Powered A2A Agent Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    parser.add_argument(
        "--model", type=str, default="claude-3-haiku-20240307",
        help="Anthropic model to use (default: claude-3-haiku-20240307)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.7,
        help="Temperature for generation (default: 0.7)"
    )
    parser.add_argument(
        "--max-tokens", type=int, default=1000,
        help="Maximum number of tokens to generate (default: 1000)"
    )
    parser.add_argument(
        "--test-only", action="store_true",
        help="Only test the agent without starting a server"
    )
    return parser.parse_args()

def start_client_process(port):
    """Start a client process to test the server"""
    from python_a2a import A2AClient
    import time
    
    # Wait a bit for the server to start
    time.sleep(2)
    
    try:
        # Connect to the server
        print(f"\n🔌 Connecting to A2A agent at: http://localhost:{port}")
        client = A2AClient(f"http://localhost:{port}")
        
        # Send some test messages
        test_questions = [
            "What's the capital of Japan?",
            "Explain how rainbows form in simple terms.",
            "Give me three tips for sustainable living."
        ]
        
        for question in test_questions:
            print(f"\n💬 Question: {question}")
            try:
                # Use client.ask() which sends a simple text message
                response = client.ask(question)
                print(f"🤖 Response: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Check the server logs for details.")
            
            # Short pause between questions
            time.sleep(1)
        
        print("\n✅ Test completed successfully!")
        print("Press Ctrl+C in the server terminal to stop the server.")
        
    except Exception as e:
        print(f"\n❌ Error connecting to agent: {e}")

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Check API key
    if not check_api_key():
        return 1
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Find an available port if none was specified
    if args.port is None:
        port = find_available_port()
        print(f"🔍 Auto-selected port: {port}")
    else:
        port = args.port
        print(f"🔍 Using specified port: {port}")
    
    # Import after checking dependencies
    from python_a2a import AnthropicA2AServer, run_server, AgentCard, AgentSkill
    from python_a2a import A2AServer  # Import A2AServer for wrapping
    
    print("\n🌟 Anthropic-Powered A2A Agent 🌟")
    print(f"This example demonstrates how to create an A2A agent powered by Anthropic's {args.model}.\n")
    
    # Create an Agent Card for our Anthropic-powered agent
    agent_card = AgentCard(
        name="Claude Assistant",
        description=f"An A2A agent powered by Anthropic's {args.model}",
        url=f"http://localhost:{port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Knowledge Questions",
                description="Answer knowledge questions with accurate information",
                examples=["What's the distance to the Moon?", "How does photosynthesis work?"]
            ),
            AgentSkill(
                name="Summarization",
                description="Summarize and explain complex topics",
                examples=["Summarize the theory of relativity", "Explain climate change simply"]
            ),
            AgentSkill(
                name="Creative Writing",
                description="Generate various creative text formats",
                examples=["Write a poem about the ocean", "Create a short story about time travel"]
            )
        ]
    )
    
    # Create the Anthropic-powered A2A server
    print("=== Creating Anthropic-Powered Agent ===")
    print(f"Model: {args.model}")
    print(f"Temperature: {args.temperature}")
    print(f"Max Tokens: {args.max_tokens}")
    
    # Create the Anthropic server
    anthropic_server = AnthropicA2AServer(
        api_key=os.environ["ANTHROPIC_API_KEY"],
        model=args.model,
        temperature=args.temperature,
        max_tokens=args.max_tokens,
        system_prompt="You are Claude, a helpful and harmless AI assistant. You provide accurate, concise, and useful information. Your tone is friendly and conversational, and you aim to be as helpful as possible while acknowledging the limitations of your knowledge."
    )
    
    # Wrap it in a standard A2A server to ensure proper handling of all request types
    class AnthropicAgent(A2AServer):
        def __init__(self, anthropic_server, agent_card):
            super().__init__(agent_card=agent_card)
            self.anthropic_server = anthropic_server
        
        def handle_task(self, task):
            # Forward the task to the Anthropic server's handle_message method
            message_data = task.message or {}
            
            # Import necessary classes
            from python_a2a import Message, TaskStatus, TaskState
            
            # Convert to Message object if it's a dict
            if isinstance(message_data, dict):
                try:
                    message = Message.from_dict(message_data)
                except:
                    # If conversion fails, create a default message
                    from python_a2a import TextContent, MessageRole
                    content = message_data.get("content", {})
                    text = content.get("text", "") if isinstance(content, dict) else ""
                    message = Message(
                        content=TextContent(text=text),
                        role=MessageRole.USER
                    )
            else:
                message = message_data
                
            try:
                # Process the message with the Anthropic server
                response = self.anthropic_server.handle_message(message)
                
                # Create artifact from response
                task.artifacts = [{
                    "parts": [{
                        "type": "text", 
                        "text": response.content.text
                    }]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            except Exception as e:
                # Handle errors
                print(f"Error in Anthropic processing: {e}")
                task.artifacts = [{
                    "parts": [{
                        "type": "text", 
                        "text": f"Error processing your request: {str(e)}"
                    }]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
            
            return task
    
    # Create the wrapped agent
    anthropic_agent = AnthropicAgent(anthropic_server, agent_card)
    
    # If this is a test-only run, we'll just create a client and send some messages directly
    if args.test_only:
        print("\n=== Testing Agent Directly (no server) ===")
        
        # Import additional modules for testing
        from python_a2a import Message, TextContent, MessageRole, pretty_print_message
        
        test_questions = [
            "What's the capital of Japan?",
            "Explain how rainbows form in simple terms.",
            "Write a haiku about autumn."
        ]
        
        for question in test_questions:
            print(f"\n💬 Question: {question}")
            
            # Create a message
            message = Message(
                content=TextContent(text=question),
                role=MessageRole.USER
            )
            
            # Get a response directly from the agent
            try:
                response = anthropic_server.handle_message(message)
                print(f"🤖 Response: {response.content.text}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Short pause between questions
            time.sleep(1)
        
        print("\n✅ Test completed successfully!")
        return 0
    
    # Start the server and a client in separate processes
    print(f"\n🚀 Starting server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start a client process to test the server
        client_process = multiprocessing.Process(target=start_client_process, args=(port,))
        client_process.start()
        
        # Start the server (this will block until interrupted)
        run_server(anthropic_agent, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        # Make sure client process is terminated
        if 'client_process' in locals():
            client_process.terminate()
            client_process.join()
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        if "Address already in use" in str(e):
            print(f"\nPort {port} is already in use. Try using a different port:")
            print(f"    python anthropic_agent.py --port {port + 1}")
        return 1
    
    print("\n=== What's Next? ===")
    print("1. Try 'bedrock_agent.py' to create an agent powered by AWS Bedrock")
    print("2. Try 'openai_agent.py' to create an agent powered by OpenAI")
    print("3. Try 'llm_client.py' to connect to an LLM-powered agent")
    
    print("\n🎉 You've created an Anthropic-powered A2A agent! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)