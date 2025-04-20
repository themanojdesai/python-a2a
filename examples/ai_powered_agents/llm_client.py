#!/usr/bin/env python
"""
LLM Client Example

This example demonstrates how to use specialized A2A clients for directly
connecting to various LLM providers like OpenAI and Anthropic without
needing to run a separate server.

To run:
    # For OpenAI:
    export OPENAI_API_KEY=your_api_key
    python llm_client.py --provider openai

    # For Anthropic:
    export ANTHROPIC_API_KEY=your_api_key
    python llm_client.py --provider anthropic

Requirements:
    # For OpenAI:
    pip install "python-a2a[openai]"

    # For Anthropic:
    pip install "python-a2a[anthropic]"
"""

import sys
import os
import argparse
import time

def check_dependencies(provider):
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import python_a2a
    except ImportError:
        missing_deps.append("python-a2a")
    
    if provider == "openai":
        try:
            import openai
        except ImportError:
            missing_deps.append("openai")
    elif provider == "anthropic":
        try:
            import anthropic
        except ImportError:
            missing_deps.append("anthropic")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print(f"\nPlease install the required dependencies:")
        print(f"    pip install \"python-a2a[{provider}]\"")
        print("\nThen run this example again.")
        return False
    
    print("✅ All dependencies are installed correctly!")
    return True

def check_api_key(provider):
    """Check if the API key is available for the specified provider"""
    env_var = f"{provider.upper()}_API_KEY"
    api_key = os.environ.get(env_var)
    
    if not api_key:
        print(f"❌ {env_var} environment variable not set!")
        print(f"\nPlease set your {provider.capitalize()} API key with:")
        print(f"    export {env_var}=your_api_key")
        print("\nThen run this example again.")
        return False
    
    # Mask the API key for display
    masked_key = api_key[:4] + "..." + api_key[-4:]
    print(f"✅ {env_var} environment variable is set: {masked_key}")
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="LLM Client Example")
    parser.add_argument(
        "--provider", type=str, choices=["openai", "anthropic"], default="openai",
        help="LLM provider to use (default: openai)"
    )
    parser.add_argument(
        "--model", type=str, default=None,
        help="Model to use (default: provider-specific default)"
    )
    parser.add_argument(
        "--temperature", type=float, default=0.7,
        help="Temperature for generation (default: 0.7)"
    )
    parser.add_argument(
        "--interactive", action="store_true",
        help="Run in interactive mode (default: run demo with preset questions)"
    )
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    provider = args.provider
    
    # Check dependencies for the specified provider
    if not check_dependencies(provider):
        return 1
    
    # Check API key for the specified provider
    if not check_api_key(provider):
        return 1
    
    print(f"\n🌟 LLM Client Example - {provider.capitalize()} 🌟")
    print(f"This example demonstrates how to use the {provider.capitalize()} A2A client directly without a server.\n")
    
    # Import the appropriate client and set up the default model
    if provider == "openai":
        from python_a2a import OpenAIA2AClient
        default_model = "gpt-4o-mini"
        model = args.model or default_model
        
        print(f"=== Creating OpenAI Client ===")
        print(f"Model: {model}")
        print(f"Temperature: {args.temperature}")
        
        try:
            client = OpenAIA2AClient(
                api_key=os.environ["OPENAI_API_KEY"],
                model=model,
                temperature=args.temperature
            )
        except Exception as e:
            print(f"❌ Error creating OpenAI client: {e}")
            print("\nPossible causes:")
            print("- Invalid API key")
            print("- Invalid model name")
            print("- Network connectivity issues")
            return 1
    
    elif provider == "anthropic":
        from python_a2a import AnthropicA2AClient
        default_model = "claude-3-haiku-20240307"
        model = args.model or default_model
        
        print(f"=== Creating Anthropic Client ===")
        print(f"Model: {model}")
        print(f"Temperature: {args.temperature}")
        
        try:
            client = AnthropicA2AClient(
                api_key=os.environ["ANTHROPIC_API_KEY"],
                model=model,
                temperature=args.temperature
            )
        except Exception as e:
            print(f"❌ Error creating Anthropic client: {e}")
            print("\nPossible causes:")
            print("- Invalid API key")
            print("- Invalid model name")
            print("- Network connectivity issues")
            return 1
    
    # If interactive mode is enabled, let the user chat with the model
    if args.interactive:
        print("\n=== Interactive Mode ===")
        print("Type your messages below. Type 'exit', 'quit', or 'q' to end the session.")
        print("Press Ctrl+C at any time to exit.\n")
        
        # Import conversation tools
        from python_a2a import Message, Conversation, MessageRole, TextContent, pretty_print_conversation
        
        # Create a conversation
        conversation = Conversation()
        
        try:
            while True:
                # Get user input
                user_input = input("You: ")
                
                # Check for exit command
                if user_input.lower() in ["exit", "quit", "q"]:
                    print("\nExiting interactive mode.")
                    break
                
                # Skip empty messages
                if not user_input.strip():
                    continue
                
                # Create a message and add it to the conversation
                user_message = Message(
                    content=TextContent(text=user_input),
                    role=MessageRole.USER
                )
                conversation.add_message(user_message)
                
                try:
                    # Print "thinking" indicator
                    print(f"\n{provider.capitalize()} is thinking...", end="", flush=True)
                    
                    # Time the response
                    start_time = time.time()
                    
                    # Get the response by sending the conversation
                    updated_conversation = client.send_conversation(conversation)
                    
                    # Calculate elapsed time
                    elapsed_time = time.time() - start_time
                    
                    # Clear the "thinking" indicator
                    print("\r" + " " * 30 + "\r", end="", flush=True)
                    
                    # Extract the latest response
                    latest_response = updated_conversation.messages[-1]
                    
                    # Print the response with timing info
                    print(f"{provider.capitalize()} ({elapsed_time:.2f}s): {latest_response.content.text}\n")
                    
                    # Update our conversation with the response
                    conversation = updated_conversation
                    
                except Exception as e:
                    # Clear the "thinking" indicator
                    print("\r" + " " * 30 + "\r", end="", flush=True)
                    
                    print(f"\n❌ Error: {e}")
                    print("Try sending a different message.\n")
        
        except KeyboardInterrupt:
            print("\n\nSession ended by user.")
        
        # Print the full conversation summary at the end
        message_count = len(conversation.messages)
        print(f"\n=== Conversation Summary ===")
        print(f"Total messages: {message_count}")
        print(f"User messages: {sum(1 for m in conversation.messages if m.role == MessageRole.USER)}")
        print(f"Assistant messages: {sum(1 for m in conversation.messages if m.role == MessageRole.AGENT)}")
        
        # Ask if user wants to see the full conversation
        if message_count > 3:
            choice = input("\nWould you like to see the full conversation? (y/n): ")
            if choice.lower().startswith('y'):
                print("\n=== Full Conversation ===")
                pretty_print_conversation(conversation)
        
    else:
        # Demo mode with preset questions
        print("\n=== Demo Mode ===")
        demo_questions = [
            "What's the capital of France?",
            "Explain how a car engine works in simple terms.",
            "Write a short poem about technology."
        ]
        
        for question in demo_questions:
            print(f"\n💬 Question: {question}")
            
            try:
                # Print "thinking" indicator
                print(f"{provider.capitalize()} is thinking...", end="", flush=True)
                
                # Time the request
                start_time = time.time()
                
                # Use the send_message method
                from python_a2a import Message, TextContent, MessageRole
                
                message = Message(
                    content=TextContent(text=question),
                    role=MessageRole.USER
                )
                
                response = client.send_message(message)
                elapsed_time = time.time() - start_time
                
                # Clear the "thinking" indicator
                print("\r" + " " * 30 + "\r", end="", flush=True)
                
                # Print the response
                print(f"🤖 Response ({elapsed_time:.2f}s):")
                if hasattr(response.content, "text"):
                    print(f"{response.content.text}")
                else:
                    print(f"{response}")
                
            except Exception as e:
                # Clear the "thinking" indicator
                print("\r" + " " * 30 + "\r", end="", flush=True)
                
                print(f"❌ Error: {e}")
                print("Possible causes:")
                print("- Invalid API key or model name")
                print("- Network connectivity issues")
                print("- Rate limiting by the provider")
            
            # Short pause between questions
            time.sleep(1)
    
    print("\n=== What's Next? ===")
    
    if provider == "openai":
        print("1. Try this example with Anthropic: python llm_client.py --provider anthropic")
    else:
        print("1. Try this example with OpenAI: python llm_client.py --provider openai")
        
    print("2. Try the --interactive flag to chat with the model")
    print(f"3. Try creating an {provider.capitalize()} server with '{provider}_agent.py'")
    print("4. Try 'mcp_tools.py' to learn how to extend LLMs with external tools")
    
    print(f"\n🎉 You've used the {provider.capitalize()} A2A client directly! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)