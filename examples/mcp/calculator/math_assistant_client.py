#!/usr/bin/env python
"""
A client for interacting with the math assistant agent.
"""

import argparse
import logging
import traceback
from python_a2a import (
    A2AClient, Message, TextContent, MessageRole, Conversation
)
from python_a2a.utils import pretty_print_message

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("math_assistant_client")

def interactive_session(client, endpoint):
    """Interactive session with the math assistant agent."""
    print(f"\n===== Math Assistant Interactive Client =====")
    print(f"Connected to: {endpoint}")
    print("Type 'exit' or 'quit' to end the session.")
    print("Example queries:")
    print("  - What is 5 plus 3?")
    print("  - Calculate 10 minus 7")
    print("  - Multiply 4 and 9")
    print("  - Divide 20 by 5")
    print("  - What's the square root of 16?")
    print("=" * 50)

    # First, send an initial message to get the welcome message
    try:
        initial_message = Message(
            content=TextContent(text="Hello"),
            role=MessageRole.USER
        )
        
        print("Sending initial greeting message...")
        response = client.send_message(initial_message)
        pretty_print_message(response)
        
        # Create a conversation to maintain context
        conversation = Conversation()
        conversation.add_message(initial_message)
        conversation.add_message(response)
    except Exception as e:
        logger.error(f"Error during initialization: {e}")
        logger.error(traceback.format_exc())
        print(f"Error connecting to agent: {e}")
        print("Continuing without initial message...")
        conversation = Conversation()
    
    while True:
        try:
            user_input = input("\n> ")
            
            if user_input.lower() in ["exit", "quit"]:
                print("Goodbye!")
                break
            
            # Send as a text message
            message = Message(
                content=TextContent(text=user_input),
                role=MessageRole.USER
            )
            
            # Add to conversation
            conversation.add_message(message)
            
            # Send the message
            print("Sending message to math assistant...")
            response = client.send_message(message)
            
            # Add to conversation
            conversation.add_message(response)
            
            # Display the response
            pretty_print_message(response)
            
        except Exception as e:
            logger.error(f"Error: {e}")
            logger.error(traceback.format_exc())
            print(f"Error: {e}")
            print("Please try again or type 'exit' to quit.")

def main():
    parser = argparse.ArgumentParser(description="Client for math assistant agent")
    parser.add_argument("--endpoint", default="http://localhost:5005/a2a", 
                        help="Math assistant endpoint URL (default: http://localhost:5005/a2a)")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create a client
    client = A2AClient(args.endpoint)
    
    try:
        # Start interactive session
        interactive_session(client, args.endpoint)
    except KeyboardInterrupt:
        print("\nExiting...")
    except Exception as e:
        logger.error(f"Unhandled error: {e}")
        logger.error(traceback.format_exc())
        print(f"\nAn unexpected error occurred: {e}")

if __name__ == "__main__":
    main()