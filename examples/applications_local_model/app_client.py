#!/usr/bin/env python
"""
Simple A2A Client Example

This example shows how to use the A2A client to connect to an A2A-compatible agent
and send messages. It includes a built-in server for a complete self-contained example.

To run:
    python simple_client.py [--port PORT]

Example:
    python simple_client.py --port 5000

Requirements:
    pip install "python-a2a[server]"
"""

import sys
import argparse
import socket
import time
import threading
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
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required dependencies:")
        print("    pip install \"python-a2a[server]\"")
        print("\nThen run this example again.")
        return False
    
    print("✅ All dependencies are installed correctly!")
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
    parser = argparse.ArgumentParser(description="Simple A2A Client Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    parser.add_argument(
        "--external", type=str, default=None,
        help="External A2A endpoint URL (if provided, won't start local server)"
    )
    return parser.parse_args()

def start_local_server(port):
    """Start a local A2A server on the specified port"""
    from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState
    
    # Create an agent card with skills information
    agent_card = AgentCard(
        name="Demo Agent",
        description="A simple A2A server for demonstration purposes",
        url=f"http://localhost:{port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Echo",
                description="Echoes back your message",
                examples=["Hello!", "How are you?"]
            ),
            AgentSkill(
                name="Greeting",
                description="Greets you with a friendly message",
                examples=["Greet me", "Say hello"]
            )
        ]
    )
    
    # Create a simple A2A server
    class DemoServer(A2AServer):
        def __init__(self):
            # Initialize with our agent card
            super().__init__(agent_card=agent_card)
        
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Prepare response based on message content
            text_lower = text.lower()
            
            if "greet" in text_lower or "hello" in text_lower or "hi" in text_lower:
                response = f"👋 Hello there! I'm the Demo Agent. How can I help you today?"
            else:
                response = f"You said: {text}\n\nI'm a simple demo agent for the A2A protocol. Try saying 'Hello' or 'Greet me'!"
            
            # Create response artifact
            task.artifacts = [{
                "parts": [{"type": "text", "text": response}]
            }]
            
            task.status = TaskStatus(state=TaskState.COMPLETED)
            return task
    
    # Create and run the server
    server = DemoServer()
    run_server(server, host="localhost", port=port)

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Import after checking dependencies
    from python_a2a import A2AClient
    
    # Handle external or local server
    if args.external:
        endpoint_url = args.external
        print(f"\n🚀 Connecting to external A2A agent at: {endpoint_url}")
        server_process = None
    else:
        # Find an available port if none was specified
        if args.port is None:
            port = find_available_port()
            print(f"🔍 Auto-selected port: {port}")
        else:
            port = args.port
            print(f"🔍 Using specified port: {port}")
        
        endpoint_url = f"http://localhost:{port}"
        
        # Start a local server in a separate process
        print(f"\n🚀 Starting a local demo A2A server on port {port}...")
        server_process = multiprocessing.Process(target=start_local_server, args=(port,))
        server_process.start()
        
        # Give the server some time to start
        print("⏳ Waiting for server to start...")
        time.sleep(2)
    
    try:
        # Create an A2A client and connect to the server
        print(f"🔌 Connecting to A2A agent at: {endpoint_url}")
        client = A2AClient(endpoint_url)
        
        # Try to get agent information
        try:
            print("\n=== Agent Information ===")
            print(f"Name: {client.agent_card.name}")
            print(f"Description: {client.agent_card.description}")
            print(f"Version: {client.agent_card.version}")
            
            if client.agent_card.skills:
                print("\nAvailable Skills:")
                for skill in client.agent_card.skills:
                    print(f"- {skill.name}: {skill.description}")
                    if skill.examples:
                        print(f"  Examples: {', '.join(skill.examples)}")
        except Exception as e:
            print(f"\n⚠️ Could not retrieve agent card: {e}")
            print("The agent may not support the A2A discovery protocol.")
            print("You can still send messages to the agent.")
        
        # Interactive message sending loop
        print("\n=== Send Messages to the Agent ===")
        print("Type your messages (or 'exit' to quit):")
        
        while True:
            try:
                user_input = input("\n> ")
                if user_input.lower() in ["exit", "quit", "q"]:
                    break
                
                # Send the message and get the response
                print("\nSending message to agent...")
                response = client.ask(user_input)
                
                # Print the response
                print("\nAgent response:")
                print(f"{response}")
                
            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")
                print("Try sending a different message or check your connection.")
    
    except Exception as e:
        print(f"\n❌ Error connecting to agent: {e}")
        print("\nPossible reasons:")
        print("- The endpoint URL is incorrect")
        print("- The agent server is not running")
        print("- Network connectivity issues")
        print("\nPlease check the URL and try again.")
        return 1
    finally:
        # Clean up the server process if we started one
        if server_process:
            print("\n🛑 Stopping local server...")
            server_process.terminate()
            server_process.join(timeout=2)
            print("✅ Local server stopped")
    
    print("\n=== What's Next? ===")
    print("1. Try 'simple_server.py' to create your own A2A server")
    print("2. Try 'function_calling.py' to use function calling with A2A")
    print("3. Try the other examples to explore more A2A features")
    
    print("\n🎉 You've successfully used the A2A client! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)