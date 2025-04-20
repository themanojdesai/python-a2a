#!/usr/bin/env python
"""
OpenAI-Powered A2A Agent

This example demonstrates how to create an A2A agent powered by OpenAI's GPT models.
It shows how to set up the agent, handle environment variables, and connect to the API.

To run:
    export OPENAI_API_KEY=your_api_key
    python openai_agent.py [--port PORT] [--model MODEL]

Example:
    python openai_agent.py --port 5000 --model gpt-4o-mini

Requirements:
    pip install "python-a2a[openai,server]"
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
        import openai
    except ImportError:
        missing_deps.append("openai")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required dependencies:")
        print("    pip install \"python-a2a[openai,server]\"")
        print("\nThen run this example again.")
        return False
    
    print("✅ All dependencies are installed correctly!")
    return True

def check_api_key():
    """Check if the OpenAI API key is available"""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set!")
        print("\nPlease set your OpenAI API key with:")
        print("    export OPENAI_API_KEY=your_api_key")
        print("\nThen run this example again.")
        return False
    
    # Mask the API key for display
    masked_key = api_key[:4] + "..." + api_key[-4:]
    print(f"✅ OPENAI_API_KEY environment variable is set: {masked_key}")
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
    parser = argparse.ArgumentParser(description="OpenAI-Powered A2A Agent Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    parser.add_argument(
        "--model", type=str, default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.7,
        help="Temperature for generation (default: 0.7)"
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
            "What's the capital of France?",
            "Explain quantum computing in simple terms.",
            "What are three benefits of exercise?"
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
    from python_a2a import OpenAIA2AServer, run_server, AgentCard, AgentSkill
    from python_a2a import A2AServer  # Import A2AServer for wrapping
    
    print("\n🌟 OpenAI-Powered A2A Agent 🌟")
    print(f"This example demonstrates how to create an A2A agent powered by OpenAI's {args.model}.\n")
    
    # Create an Agent Card for our OpenAI-powered agent
    agent_card = AgentCard(
        name="OpenAI Assistant",
        description=f"An A2A agent powered by OpenAI's {args.model}",
        url=f"http://localhost:{port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="General Questions",
                description="Answer general knowledge questions",
                examples=["What's the capital of Japan?", "How do solar panels work?"]
            ),
            AgentSkill(
                name="Creative Writing",
                description="Generate creative content",
                examples=["Write a short poem about autumn", "Create a slogan for a coffee shop"]
            ),
            AgentSkill(
                name="Problem Solving",
                description="Help solve problems and provide solutions",
                examples=["How do I improve my time management?", "What's a good strategy for learning a new language?"]
            )
        ]
    )
    
    # Create the OpenAI-powered A2A server
    print("=== Creating OpenAI-Powered Agent ===")
    print(f"Model: {args.model}")
    print(f"Temperature: {args.temperature}")
    
    # Create the OpenAI server
    openai_server = OpenAIA2AServer(
        api_key=os.environ["OPENAI_API_KEY"],
        model=args.model,
        temperature=args.temperature,
        system_prompt="You are a helpful AI assistant that provides accurate, concise, and useful information. Your responses should be informative yet easy to understand."
    )
    
    # Wrap it in a standard A2A server to ensure proper handling of all request types
    class OpenAIAgent(A2AServer):
        def __init__(self, openai_server, agent_card):
            super().__init__(agent_card=agent_card)
            self.openai_server = openai_server
        
        def handle_task(self, task):
            # Forward the task to the OpenAI server's handle_message method
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
                # Process the message with the OpenAI server
                response = self.openai_server.handle_message(message)
                
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
                print(f"Error in OpenAI processing: {e}")
                task.artifacts = [{
                    "parts": [{
                        "type": "text", 
                        "text": f"Error processing your request: {str(e)}"
                    }]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
            
            return task
    
    # Create the wrapped agent
    openai_agent = OpenAIAgent(openai_server, agent_card)
    
    # If this is a test-only run, we'll just create a client and send some messages directly
    if args.test_only:
        print("\n=== Testing Agent Directly (no server) ===")
        
        # Import additional modules for testing
        from python_a2a import Message, TextContent, MessageRole, pretty_print_message
        
        test_questions = [
            "What's the capital of France?",
            "Explain quantum computing in simple terms.",
            "Write a haiku about programming."
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
                response = openai_server.handle_message(message)
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
        run_server(openai_agent, host="0.0.0.0", port=port)
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
            print(f"    python openai_agent.py --port {port + 1}")
        return 1
    
    print("\n=== What's Next? ===")
    print("1. Try 'anthropic_agent.py' to create an agent powered by Anthropic Claude")
    print("2. Try 'bedrock_agent.py' to create an agent powered by AWS Bedrock")
    print("3. Try 'openai_function_calling.py' to use OpenAI's function calling capabilities")
    
    print("\n🎉 You've created an OpenAI-powered A2A agent! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)