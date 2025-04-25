#!/usr/bin/env python
"""
A2A to LangChain Integration Example

This example demonstrates how to create an OpenAI-powered A2A agent
and then integrate it with LangChain workflows.

To run:
    export OPENAI_API_KEY=your_api_key
    python a2a_to_langchain.py [--port PORT] [--model MODEL]

Requirements:
    pip install "python-a2a[langchain,openai,server]" langchain langchain-openai
"""

import os
import sys
import argparse
import socket
import time
import threading

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import python_a2a
    except ImportError:
        missing_deps.append("python-a2a")
    
    try:
        import langchain
    except ImportError:
        missing_deps.append("langchain")
    
    try:
        import openai
    except ImportError:
        missing_deps.append("openai")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required dependencies:")
        print('    pip install "python-a2a[langchain,openai,server]" langchain langchain-openai')
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
    parser = argparse.ArgumentParser(description="A2A to LangChain Integration Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    parser.add_argument(
        "--model", type=str, default="gpt-3.5-turbo",
        help="OpenAI model to use (default: gpt-3.5-turbo)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.0,
        help="Temperature for generation (default: 0.0)"
    )
    return parser.parse_args()

def main():
    """Main function"""
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Check API key
    if not check_api_key():
        return 1
    
    # Parse arguments
    args = parse_arguments()
    
    # Find an available port if none was specified
    if args.port is None:
        port = find_available_port()
        print(f"🔍 Auto-selected port: {port}")
    else:
        port = args.port
        print(f"🔍 Using specified port: {port}")
    
    # Import required components
    from python_a2a import OpenAIA2AServer, run_server, A2AServer, AgentCard, AgentSkill
    from python_a2a import A2AClient
    from python_a2a.langchain import to_langchain_agent
    
    print("\n🌟 A2A to LangChain Integration Example 🌟")
    print(f"This example demonstrates how to integrate an OpenAI-powered A2A agent with LangChain.")
    
    # Step 1: Create the OpenAI-powered A2A server
    print("\n📝 Step 1: Creating OpenAI-Powered A2A Server")
    
    # Create an Agent Card for our OpenAI-powered agent
    agent_card = AgentCard(
        name="Geography Expert",
        description=f"An A2A agent specialized in geography and travel information",
        url=f"http://localhost:{port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Geography Knowledge",
                description="Answer questions about countries, capitals, landmarks, etc.",
                examples=["What's the capital of Japan?", "What are famous landmarks in Paris?"]
            ),
            AgentSkill(
                name="Travel Information",
                description="Provide information about travel destinations",
                examples=["What's the best time to visit Italy?", "What should I know before traveling to Egypt?"]
            )
        ]
    )
    
    # Create the OpenAI server
    openai_server = OpenAIA2AServer(
        api_key=os.environ["OPENAI_API_KEY"],
        model=args.model,
        temperature=args.temperature,
        system_prompt="You are a geography and travel expert. Provide accurate, concise information about countries, cities, landmarks, and travel tips. Focus only on geography and travel related queries."
    )
    
    # Wrap it in a standard A2A server for proper handling
    class GeographyAgent(A2AServer):
        def __init__(self, openai_server, agent_card):
            super().__init__(agent_card=agent_card)
            self.openai_server = openai_server
        
        def handle_message(self, message):
            """Handle incoming messages by delegating to OpenAI server"""
            return self.openai_server.handle_message(message)
    
    # Create the wrapped agent
    geography_agent = GeographyAgent(openai_server, agent_card)
    
    # Start the server in a background thread
    server_url = f"http://localhost:{port}"
    print(f"\nStarting A2A server on {server_url}...")
    
    def run_server_thread():
        """Run the server in a thread"""
        run_server(geography_agent, host="0.0.0.0", port=port)
    
    server_thread = threading.Thread(target=run_server_thread, daemon=True)
    server_thread.start()
    
    # Give the server time to start
    time.sleep(2)
    
    # Test the A2A server directly
    print("\n📝 Testing A2A Server Directly")
    
    try:
        client = A2AClient(server_url)
        response = client.ask("What's the capital of France?")
        print(f"A2A Response: {response}")
    except Exception as e:
        print(f"❌ Error testing A2A server: {e}")
        return 1
    
    # Step 2: Convert A2A agent to LangChain
    print("\n📝 Step 2: Converting A2A Agent to LangChain")
    
    try:
        langchain_agent = to_langchain_agent(server_url)
        print("✅ Successfully converted A2A agent to LangChain")
    except Exception as e:
        print(f"❌ Error converting A2A agent to LangChain: {e}")
        return 1
    
    # Test the LangChain agent
    print("\n📝 Testing LangChain Agent")
    
    try:
        result = langchain_agent.invoke("What are some famous landmarks in Paris?")
        print(f"LangChain Agent Response: {result.get('output', '')}")
    except Exception as e:
        print(f"❌ Error using LangChain agent: {e}")
        return 1
    
    # Step 3: Using the converted agent in a LangChain workflow
    print("\n📝 Step 3: Using the Converted Agent in a LangChain Workflow")
    
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.prompts import ChatPromptTemplate
        from langchain_core.output_parsers import StrOutputParser
        
        # Create a LangChain LLM
        llm = ChatOpenAI(temperature=0)
        
        # Create a prompt template for generating travel queries
        prompt = ChatPromptTemplate.from_template(
            "Generate a specific, detailed travel question about {destination} that would be appropriate for a geography expert."
        )
        
        # Create a simple pipeline that:
        # 1. Takes a destination
        # 2. Generates a detailed question about it
        # 3. Sends that question to our A2A-derived agent
        # 4. Formats the response
        
        # Define a function to safely extract agent response
        def extract_agent_output(agent_result):
            """Safely extract output from agent result, handling various formats."""
            if isinstance(agent_result, dict):
                return agent_result.get('output', str(agent_result))
            return str(agent_result)
        
        # Create the pipeline with proper output handling
        chain = (
            prompt |
            llm |
            StrOutputParser() |
            langchain_agent |
            extract_agent_output |
            (lambda x: f"🌍 Travel Info: {x}")
        )
        
        # Test the chain
        destinations = ["Japan", "Egypt", "Brazil"]
        
        for destination in destinations:
            print(f"\nProcessing query about {destination}:")
            try:
                result = chain.invoke({"destination": destination})
                print(result)
            except Exception as e:
                print(f"❌ Error processing chain for {destination}: {e}")
                import traceback
                traceback.print_exc()
    except Exception as e:
        print(f"❌ Error setting up LangChain workflow: {e}")
        return 1
    
    # Keep the server running until user interrupts
    print("\n✅ Integration successful!")
    print("Press Ctrl+C to stop the server and exit")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nExiting...")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted by user")
        sys.exit(0)