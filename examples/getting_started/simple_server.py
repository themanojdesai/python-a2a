#!/usr/bin/env python
"""
Simple A2A Server Example

This example shows how to create a basic A2A server that responds
to messages. It demonstrates the minimal code needed to get a
server up and running.

To run:
    python simple_server.py [--port PORT]

Example:
    python simple_server.py --port 5000

Requirements:
    pip install "python-a2a[server]"
"""

import sys
import argparse
import socket

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
    parser = argparse.ArgumentParser(description="Simple A2A Server Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    return parser.parse_args()

def main():
    # First, check dependencies
    if not check_dependencies():
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
    from python_a2a import A2AServer, run_server, AgentCard, AgentSkill
    
    print("\n🌟 Creating a Simple A2A Server 🌟")
    
    # Create an agent card with skills information
    agent_card = AgentCard(
        name="Echo Server",
        description="A simple A2A server that echoes messages back to the client with extras",
        url=f"http://localhost:{port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Echo",
                description="Echoes back the message with some extras",
                examples=["Hello!", "How are you?"]
            ),
            AgentSkill(
                name="Count Words",
                description="Counts the number of words in the message",
                examples=["Count how many words are in this sentence"]
            )
        ]
    )
    
    # Create a custom A2A server
    class EchoServer(A2AServer):
        def __init__(self):
            # Initialize with our agent card
            super().__init__(agent_card=agent_card)
        
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Check for specific commands
            if "count words" in text.lower():
                # Count words in the message
                word_count = len(text.split())
                response = f"Your message has {word_count} words."
            else:
                # Echo the message with some extras
                response = f"You said: {text}\n\nThis is a simple A2A Echo Server that responds to messages."
                
                if text.endswith("?"):
                    response += "\n\nI see you asked a question! To get more capabilities, try the other examples."
            
            # Create response artifact
            task.artifacts = [{
                "parts": [{"type": "text", "text": response}]
            }]
            
            from python_a2a import TaskStatus, TaskState
            task.status = TaskStatus(state=TaskState.COMPLETED)
            return task
    
    # Create the server
    echo_server = EchoServer()
    
    print("\n=== Server Information ===")
    print(f"Name: {echo_server.agent_card.name}")
    print(f"Description: {echo_server.agent_card.description}")
    print(f"URL: http://localhost:{port}")
    print("\nSkills:")
    for skill in echo_server.agent_card.skills:
        print(f"- {skill.name}: {skill.description}")
    
    print("\n🚀 Starting server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start the server
        run_server(echo_server, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\n✅ Server stopped successfully")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        if "Address already in use" in str(e):
            print(f"\nPort {port} is already in use. Try using a different port:")
            print(f"    python simple_server.py --port {port + 1}")
        return 1
    
    print("\n=== What's Next? ===")
    print("1. Connect to this server using 'simple_client.py':")
    print(f"  python simple_client.py --external http://localhost:{port}")
    print("2. Try 'function_calling.py' to add function calling capability")
    print("3. Explore more examples to build more powerful agents")
    
    print("\n🎉 You've created your first A2A server! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)