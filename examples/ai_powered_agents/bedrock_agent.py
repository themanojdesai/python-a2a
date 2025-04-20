#!/usr/bin/env python
"""
AWS Bedrock-Powered A2A Agent

This example demonstrates how to create an A2A agent powered by AWS Bedrock models,
including Claude, Titan, and other models available on AWS Bedrock.

To run:
    export AWS_ACCESS_KEY_ID=your_access_key
    export AWS_SECRET_ACCESS_KEY=your_secret_key
    export AWS_REGION=your_region
    python bedrock_agent.py [--port PORT] [--model MODEL]

Example:
    python bedrock_agent.py --port 5000 --model anthropic.claude-3-sonnet-20240229-v1:0

Requirements:
    pip install "python-a2a[bedrock,server]"
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
        import boto3
    except ImportError:
        missing_deps.append("boto3")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required dependencies:")
        print("    pip install \"python-a2a[bedrock,server]\"")
        print("\nThen run this example again.")
        return False
    
    print("✅ All dependencies are installed correctly!")
    return True

def check_aws_credentials():
    """Check if AWS credentials are available"""
    aws_access_key = os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_key = os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = os.environ.get("AWS_REGION")
    
    missing = []
    if not aws_access_key:
        missing.append("AWS_ACCESS_KEY_ID")
    if not aws_secret_key:
        missing.append("AWS_SECRET_ACCESS_KEY")
    if not aws_region:
        missing.append("AWS_REGION")
    
    if missing:
        print("❌ Missing AWS credentials!")
        print("\nPlease set the following environment variables:")
        for var in missing:
            print(f"    export {var}=your_{var.lower()}")
        print("\nThen run this example again.")
        return False
    
    # Mask the credentials for display
    masked_access_key = aws_access_key[:4] + "..." + aws_access_key[-4:] if aws_access_key else ""
    masked_secret_key = aws_secret_key[:4] + "..." + aws_secret_key[-4:] if aws_secret_key else ""
    
    print("✅ AWS credentials are set:")
    print(f"    AWS_ACCESS_KEY_ID: {masked_access_key}")
    print(f"    AWS_SECRET_ACCESS_KEY: {masked_secret_key}")
    print(f"    AWS_REGION: {aws_region}")
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
    parser = argparse.ArgumentParser(description="AWS Bedrock-Powered A2A Agent Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    parser.add_argument(
        "--model", type=str, default="anthropic.claude-3-sonnet-20240229-v1:0",
        help="AWS Bedrock model to use (default: anthropic.claude-3-sonnet-20240229-v1:0)"
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
    time.sleep(3)  # Longer wait for Bedrock as it can take a bit more time
    
    try:
        # Connect to the server
        print(f"\n🔌 Connecting to A2A agent at: http://localhost:{port}")
        client = A2AClient(f"http://localhost:{port}")
        
        # Send some test messages
        test_questions = [
            "What's the tallest mountain in the world?",
            "Give me a recipe for chocolate chip cookies.",
            "Explain the concept of machine learning."
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
            
            # Short pause between questions to avoid rate limits
            time.sleep(2)
        
        print("\n✅ Test completed successfully!")
        print("Press Ctrl+C in the server terminal to stop the server.")
        
    except Exception as e:
        print(f"\n❌ Error connecting to agent: {e}")

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Check AWS credentials
    if not check_aws_credentials():
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
    
    # Get model provider from model ID
    if "anthropic" in args.model.lower():
        provider = "Anthropic Claude"
    elif "titan" in args.model.lower():
        provider = "Amazon Titan"
    elif "cohere" in args.model.lower():
        provider = "Cohere"
    elif "ai21" in args.model.lower():
        provider = "AI21 Labs"
    else:
        provider = "AWS Bedrock"
    
    # Import after checking dependencies
    from python_a2a import BedrockA2AServer, run_server, AgentCard, AgentSkill
    from python_a2a import A2AServer  # Import A2AServer for wrapping
    
    print("\n🌟 AWS Bedrock-Powered A2A Agent 🌟")
    print(f"This example demonstrates how to create an A2A agent powered by {provider} via AWS Bedrock.\n")
    
    # Create an Agent Card for our Bedrock-powered agent
    agent_card = AgentCard(
        name=f"Bedrock {provider} Assistant",
        description=f"An A2A agent powered by {provider} via AWS Bedrock",
        url=f"http://localhost:{port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Knowledge Questions",
                description="Answer questions with accurate information",
                examples=["What's the population of Brazil?", "When was the first computer invented?"]
            ),
            AgentSkill(
                name="Writing Assistant",
                description="Help with various writing tasks",
                examples=["Write a professional email", "Create a product description"]
            ),
            AgentSkill(
                name="Learning Resources",
                description="Provide educational content and explanations",
                examples=["Explain how batteries work", "What are the planets in our solar system?"]
            )
        ]
    )
    
    # Create the Bedrock-powered A2A server
    print("=== Creating AWS Bedrock-Powered Agent ===")
    print(f"Model: {args.model}")
    print(f"Provider: {provider}")
    print(f"Temperature: {args.temperature}")
    print(f"Max Tokens: {args.max_tokens}")
    
    try:
        # Create the Bedrock server
        bedrock_server = BedrockA2AServer(
            model_id=args.model,
            aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
            aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
            aws_region=os.environ["AWS_REGION"],
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            system_prompt="You are a helpful, accurate, and friendly AI assistant. You provide clear, concise, and informative responses to questions on a wide range of topics."
        )
        
        # Wrap it in a standard A2A server to ensure proper handling of all request types
        class BedrockAgent(A2AServer):
            def __init__(self, bedrock_server, agent_card):
                super().__init__(agent_card=agent_card)
                self.bedrock_server = bedrock_server
            
            def handle_task(self, task):
                # Forward the task to the Bedrock server's handle_message method
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
                    # Process the message with the Bedrock server
                    response = self.bedrock_server.handle_message(message)
                    
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
                    print(f"Error in Bedrock processing: {e}")
                    task.artifacts = [{
                        "parts": [{
                            "type": "text", 
                            "text": f"Error processing your request: {str(e)}"
                        }]
                    }]
                    task.status = TaskStatus(state=TaskState.FAILED)
                
                return task
        
        # Create the wrapped agent
        bedrock_agent = BedrockAgent(bedrock_server, agent_card)
    except Exception as e:
        print(f"❌ Error creating Bedrock agent: {e}")
        print("\nPossible causes:")
        print("- Invalid AWS credentials")
        print("- Region doesn't support the specified model")
        print("- Model ID is incorrect")
        print("- AWS account doesn't have access to the specified model")
        return 1
    
    # If this is a test-only run, we'll just create a client and send some messages directly
    if args.test_only:
        print("\n=== Testing Agent Directly (no server) ===")
        
        # Import additional modules for testing
        from python_a2a import Message, TextContent, MessageRole, pretty_print_message
        
        test_questions = [
            "What's the tallest mountain in the world?",
            "Give me a recipe for chocolate chip cookies.",
            "Write a haiku about the ocean."
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
                response = bedrock_server.handle_message(message)
                print(f"🤖 Response: {response.content.text}")
            except Exception as e:
                print(f"❌ Error: {e}")
            
            # Short pause between questions to avoid rate limits
            time.sleep(2)
        
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
        run_server(bedrock_agent, host="0.0.0.0", port=port)
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
            print(f"    python bedrock_agent.py --port {port + 1}")
        return 1
    
    print("\n=== What's Next? ===")
    print("1. Try 'openai_agent.py' to create an agent powered by OpenAI")
    print("2. Try 'anthropic_agent.py' to create an agent powered by Anthropic Claude")
    print("3. Try 'llm_client.py' to connect to an LLM-powered agent")
    
    print("\n🎉 You've created an AWS Bedrock-powered A2A agent! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)