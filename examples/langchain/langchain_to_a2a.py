#!/usr/bin/env python
"""
LangChain to A2A Conversion Example

This example demonstrates how to convert LangChain components to A2A servers,
making them accessible via the A2A protocol.

To run:
    python langchain_to_a2a.py

Requirements:
    python-a2a[langchain] langchain langchain_openai openai
"""

import os
import threading
import time
import socket
from typing import Dict, List, Any

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import python_a2a
        import langchain
        import openai
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("Please install the required dependencies:")
        print('    pip install "python-a2a[langchain]" langchain langchain_openai openai')
        return False

def find_available_port(start_port=8000, max_tries=100):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_tries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    
    # If we couldn't find a port, just return a high-numbered one
    return start_port + 1000

def run_server_in_thread(server, port=None):
    """Run an A2A server in a background thread with auto port assignment"""
    from python_a2a import run_server
    
    # Find an available port if none provided
    if port is None:
        port = find_available_port()
    
    # Store the port on the server object for reference
    server._port = port
    
    def server_thread():
        print(f"Starting server on port {port}...")
        run_server(server, host="0.0.0.0", port=port)
    
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
    time.sleep(2)  # Give the server time to start
    
    # Return both the thread and the port
    return thread, port

def main():
    """Main function"""
    # Check for dependencies
    if not check_dependencies():
        return 1
    
    # Check for API key
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("Please set your API key:")
        print("    export OPENAI_API_KEY=your-api-key")
        return 1
    
    print("\n⭐ LangChain to A2A Conversion Example")
    print("This example converts a LangChain LLM and a simple LLM wrapper to A2A servers")
    
    # Import required components
    from langchain_openai import ChatOpenAI
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.prompts import PromptTemplate
    
    from python_a2a import A2AClient
    from python_a2a.langchain import to_a2a_server
    
    # Example 1: Converting an LLM to A2A
    print("\n📝 Example 1: Converting an LLM to A2A")
    
    # Create a LangChain LLM
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0
    )
    
    # Convert to A2A server
    llm_server = to_a2a_server(llm)
    
    # Run the server in a background thread with auto port assignment
    llm_thread, llm_port = run_server_in_thread(llm_server)
    
    # Test the server
    llm_client = A2AClient(f"http://localhost:{llm_port}")
    result = llm_client.ask("What is the capital of France?")
    print(f"LLM Response: {result}")
    
    # Example 2: Converting a simple LLM wrapper to A2A
    print("\n📝 Example 2: Converting a Simple LLM Wrapper to A2A")
    
    # Create a simple LLM wrapper with the modern LangChain pipeline approach
    template = """
    You are a helpful travel guide.
    
    Question: {query}
    
    Answer:
    """
    prompt = PromptTemplate.from_template(template)
    
    # Create a simple chain using the modern pipe syntax
    travel_chain = prompt | llm | StrOutputParser()
    
    # Convert to A2A server
    travel_server = to_a2a_server(travel_chain)
    
    # Run the server in a background thread with auto port assignment
    travel_thread, travel_port = run_server_in_thread(travel_server)
    
    # Test the server with a specific input format
    travel_client = A2AClient(f"http://localhost:{travel_port}")
    result = travel_client.ask('{"query": "What are some must-see attractions in Paris?"}')
    print(f"Travel Guide Response: {result}")
    
    # Print server details
    print("\n📋 Server Information:")
    print(f"  LLM Server: http://localhost:{llm_port}")
    print(f"  Travel Guide Server: http://localhost:{travel_port}")
    
    # Keep servers running until user interrupts
    print("\n✅ All servers are running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping servers...")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())