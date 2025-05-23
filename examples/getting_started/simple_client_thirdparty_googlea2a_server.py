#!/usr/bin/env python
"""
Simple A2A Client Example

This example shows how to use the A2A client to connect to a Google A2A-compatible agent
and send messages. It requires an external A2A server to be running.

To run:
    python simple_client_thirdparty_googlea2a_server.py --external URL

Example:
    python simple_client_thirdparty_googlea2a_server.py --external http://localhost:8000

Requirements:
    pip install "python-a2a[server]"

Note:
    You need to run a Google A2A server first. You can find example servers at:
    https://github.com/google/a2a-python/tree/main/examples/langgraph
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
        print("\n❌ No external A2A server specified!")
        print("\nTo run this example, you need to:")
        print("1. Clone and run a demo A2A server from: https://github.com/google/a2a-python/tree/main/examples/langgraph")
        print("2. Run this client with the server URL using: --external URL")
        raise ValueError("External Google A2A server URL is required")
    
    try:
        # Create an A2A client and connect to the server
        print(f"🔌 Connecting to A2A agent at: {endpoint_url}")
        client = A2AClient(endpoint_url, google_a2a_compatible=True)
        
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