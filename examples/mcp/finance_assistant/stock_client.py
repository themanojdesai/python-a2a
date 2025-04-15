#!/usr/bin/env python
"""
A client for interacting with the stock assistant agent.
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
logger = logging.getLogger("stock_client")

def interactive_session(client, endpoint):
    """Interactive session with the stock assistant agent."""
    print(f"\n===== Stock Price Assistant Interactive Client =====")
    print(f"Connected to: {endpoint}")
    print("Type 'exit' or 'quit' to end the session.")
    print("Example queries:")
    print("  - What's the stock price of Apple?")
    print("  - How much is Microsoft trading for?")
    print("  - Get the current price of Tesla stock")
    print("  - What's Amazon stock at right now?")
    print("=" * 50)

    # First, send an initial message to get the welcome message
    try:
        initial_message = Message(
            content=TextContent(text="Hello"),
            role=MessageRole.USER
        )
        
        print("Connecting to Stock Assistant...")
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
            print("Sending query to Stock Assistant...")
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
    parser = argparse.ArgumentParser(description="Client for stock assistant agent")
    parser.add_argument("--endpoint", default="http://localhost:5000/a2a", 
                        help="Stock assistant endpoint URL (default: http://localhost:5000/a2a)")
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