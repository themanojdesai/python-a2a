#!/usr/bin/env python
"""
Hello World with Python A2A

This is the simplest possible example of using Python A2A. 
It demonstrates how to create basic messages and provides a first
hands-on experience with the library.

To run:
    python hello_a2a.py

Requirements:
    pip install python-a2a
"""

import sys

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import python_a2a
        print("✅ python-a2a is installed correctly!")
        return True
    except ImportError:
        print("❌ python-a2a is not installed!")
        print("\nPlease install it with:")
        print("    pip install python-a2a")
        print("\nThen run this example again.")
        return False

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Import after checking dependencies
    from python_a2a import Message, TextContent, MessageRole, pretty_print_message
    
    print("\n🌟 Welcome to Python A2A! 🌟")
    print("This example shows how to create and work with A2A messages.\n")
    
    # Create a simple text message
    message = Message(
        content=TextContent(text="Hello, A2A World!"),
        role=MessageRole.USER
    )
    
    # Print the message in a formatted way
    print("=== Basic A2A Message ===")
    pretty_print_message(message)
    
    # Create a response message
    response = Message(
        content=TextContent(text="Hello! I'm an A2A agent. How can I help you today?"),
        role=MessageRole.AGENT,
        parent_message_id=message.message_id  # Link to the original message
    )
    
    # Print the response
    print("\n=== Response Message ===")
    pretty_print_message(response)
    
    # You can also access message properties directly
    print("\n=== Message Properties ===")
    print(f"Content: {message.content.text}")
    print(f"Role: {message.role}")
    print(f"Message ID: {message.message_id}")
    
    print("\n=== What's Next? ===")
    print("1. Try editing this code to create different kinds of messages")
    print("2. Try 'simple_client.py' to connect to an A2A agent")
    print("3. Try 'simple_server.py' to create your own A2A agent")
    
    print("\n🎉 Congratulations! You've created your first A2A messages! 🎉")
    return 0

if __name__ == "__main__":
    sys.exit(main())