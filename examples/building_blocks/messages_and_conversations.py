#!/usr/bin/env python
"""
A2A Messages and Conversations

This example demonstrates how to create, manipulate, and work with A2A
message and conversation objects. You'll learn how to build conversations
with different message types and handle message history.

To run:
    python messages_and_conversations.py

Requirements:
    pip install python-a2a
"""

import sys
import json

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
    from python_a2a import (
        Message, Conversation, MessageRole,
        TextContent, FunctionCallContent, FunctionResponseContent, FunctionParameter,
        pretty_print_message, pretty_print_conversation
    )
    
    print("\n🌟 A2A Messages and Conversations 🌟")
    print("This example shows how to work with the core data structures of A2A.\n")
    
    # Create a new conversation
    conversation = Conversation()
    print(f"Created new conversation with ID: {conversation.conversation_id}")
    
    # 1. Add a simple text message from the user
    print("\n=== Creating a Text Message ===")
    user_message = Message(
        content=TextContent(text="What's the weather in New York?"),
        role=MessageRole.USER
    )
    conversation.add_message(user_message)
    print("Added user message:")
    pretty_print_message(user_message)
    
    # 2. Add a function call message from the agent
    print("\n=== Creating a Function Call Message ===")
    function_call = Message(
        content=FunctionCallContent(
            name="get_weather",
            parameters=[
                FunctionParameter(name="location", value="New York"),
                FunctionParameter(name="units", value="fahrenheit")
            ]
        ),
        role=MessageRole.AGENT,
        parent_message_id=user_message.message_id
    )
    conversation.add_message(function_call)
    print("Added function call message:")
    pretty_print_message(function_call)
    
    # 3. Add a function response message
    print("\n=== Creating a Function Response Message ===")
    function_response = Message(
        content=FunctionResponseContent(
            name="get_weather",
            response={
                "condition": "Sunny",
                "temperature": 72,
                "humidity": 45,
                "wind_speed": 5
            }
        ),
        role=MessageRole.SYSTEM,
        parent_message_id=function_call.message_id
    )
    conversation.add_message(function_response)
    print("Added function response message:")
    pretty_print_message(function_response)
    
    # 4. Add a final text message from the agent
    print("\n=== Creating a Final Response Message ===")
    agent_message = Message(
        content=TextContent(
            text="The weather in New York is currently sunny with a temperature of 72°F. "
                 "Humidity is at 45% with a light breeze of 5 mph."
        ),
        role=MessageRole.AGENT,
        parent_message_id=function_response.message_id
    )
    conversation.add_message(agent_message)
    print("Added agent message:")
    pretty_print_message(agent_message)
    
    # Display the full conversation
    print("\n=== Complete Conversation ===")
    pretty_print_conversation(conversation)
    
    # Convert to JSON (for storage or transmission)
    print("\n=== Conversation as JSON ===")
    conversation_json = conversation.to_json()
    pretty_json = json.dumps(json.loads(conversation_json), indent=2)
    print(pretty_json[:500] + "...\n(truncated for brevity)")
    
    # Demonstrate how to save and load conversations
    print("\n=== Saving and Loading Conversations ===")
    
    # Save to file
    with open("conversation.json", "w") as f:
        f.write(conversation_json)
    print("Saved conversation to conversation.json")
    
    # Load from file
    with open("conversation.json", "r") as f:
        loaded_json = f.read()
    
    loaded_conversation = Conversation.from_json(loaded_json)
    print(f"Loaded conversation with ID: {loaded_conversation.conversation_id}")
    print(f"Number of messages: {len(loaded_conversation.messages)}")
    
    # Demonstrate helper methods
    print("\n=== Using Conversation Helper Methods ===")
    
    # Create a new conversation with helper methods
    helper_convo = Conversation()
    
    # Add messages using helper methods
    helper_convo.create_text_message(
        text="Hello, can you help me with something?",
        role=MessageRole.USER
    )
    
    helper_convo.create_text_message(
        text="Of course! What can I help you with?",
        role=MessageRole.AGENT,
        parent_message_id=helper_convo.messages[0].message_id
    )
    
    helper_convo.create_function_call(
        name="search_database",
        parameters=[
            {"name": "query", "value": "best restaurants"},
            {"name": "location", "value": "downtown"}
        ],
        role=MessageRole.AGENT,
        parent_message_id=helper_convo.messages[1].message_id
    )
    
    helper_convo.create_function_response(
        name="search_database",
        response=["Restaurant A", "Restaurant B", "Restaurant C"],
        parent_message_id=helper_convo.messages[2].message_id
    )
    
    print("Created conversation using helper methods:")
    pretty_print_conversation(helper_convo)
    
    print("\n=== What's Next? ===")
    print("1. Try 'agent_discovery.py' to learn about agent cards and skills")
    print("2. Try 'tasks.py' to learn about the A2A task model")
    print("3. Try 'mcp_tools.py' to learn about tool integration with MCP")
    
    print("\n🎉 You've learned how to work with A2A messages and conversations! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)