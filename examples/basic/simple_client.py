# examples/basic/simple_client.py
"""
A simple client that demonstrates how to interact with A2A agents.
"""

import argparse
from python_a2a import A2AClient, Message, TextContent, MessageRole
from python_a2a.utils import pretty_print_message

def main():
    parser = argparse.ArgumentParser(description="Simple A2A client")
    parser.add_argument("endpoint", help="A2A endpoint URL")
    parser.add_argument("message", help="Message to send to the agent")
    
    args = parser.parse_args()
    
    # Create a client pointing to the specified endpoint
    client = A2AClient(args.endpoint)
    
    # Create a simple text message
    message = Message(
        content=TextContent(text=args.message),
        role=MessageRole.USER
    )
    
    print(f"Sending message to {args.endpoint}...")
    print(f"Message: {args.message}")
    print("-" * 50)
    
    # Send the message and get a response
    response = client.send_message(message)
    
    print("Received response:")
    pretty_print_message(response)

if __name__ == "__main__":
    main()