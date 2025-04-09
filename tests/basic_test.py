"""
Simple test script to verify that the A2A package works correctly
"""

import os
import sys
import json

# Add the parent directory to the path so we can import the package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import (
    Message, TextContent, FunctionCallContent, FunctionResponseContent,
    FunctionParameter, MessageRole, MessageType, Conversation
)
from python_a2a.utils import pretty_print_message, create_text_message, format_function_params


def test_message_serialization():
    """Test that messages can be serialized and deserialized correctly"""
    print("=== Testing Message Serialization ===")
    
    # Create a text message
    text_message = create_text_message("Hello, A2A!", MessageRole.USER)
    
    # Serialize to JSON
    json_str = text_message.to_json()
    print(f"Serialized: {json_str}")
    
    # Deserialize from JSON
    deserialized = Message.from_json(json_str)
    print("Deserialized:")
    pretty_print_message(deserialized)
    
    # Verify content is the same
    assert deserialized.content.text == text_message.content.text
    assert deserialized.role == text_message.role
    print("✅ Text message serialization test passed")
    print()


def test_function_call():
    """Test that function calls work correctly"""
    print("=== Testing Function Call ===")
    
    # Create a function call
    params = format_function_params({
        "query": "weather in San Francisco",
        "units": "celsius"
    })
    
    function_call = Message(
        content=FunctionCallContent(
            name="get_weather",
            parameters=[
                FunctionParameter(name=p["name"], value=p["value"]) 
                for p in params
            ]
        ),
        role=MessageRole.USER
    )
    
    # Serialize to JSON
    json_str = function_call.to_json()
    print(f"Serialized: {json_str}")
    
    # Deserialize from JSON
    deserialized = Message.from_json(json_str)
    print("Deserialized:")
    pretty_print_message(deserialized)
    
    # Verify content is the same
    assert deserialized.content.name == function_call.content.name
    assert len(deserialized.content.parameters) == len(function_call.content.parameters)
    print("✅ Function call test passed")
    print()


def test_conversation():
    """Test that conversations work correctly"""
    print("=== Testing Conversation ===")
    
    # Create a conversation
    conversation = Conversation()
    
    # Add messages to the conversation
    msg1 = conversation.create_text_message(
        text="Hi, I need some information.",
        role=MessageRole.USER
    )
    
    # Add a function call to the conversation
    msg2 = conversation.create_function_call(
        name="get_data",
        parameters=[
            {"name": "topic", "value": "climate change"},
            {"name": "format", "value": "summary"}
        ],
        role=MessageRole.USER,
        parent_message_id=msg1.message_id
    )
    
    # Serialize to JSON
    json_str = conversation.to_json()
    print(f"Serialized: {json_str}")
    
    # Deserialize from JSON
    deserialized = Conversation.from_json(json_str)
    print(f"Deserialized conversation with {len(deserialized.messages)} messages:")
    
    # Verify content
    assert len(deserialized.messages) == len(conversation.messages)
    assert deserialized.conversation_id == conversation.conversation_id
    
    # Print each message in the conversation
    for i, message in enumerate(deserialized.messages):
        print(f"Message {i+1}:")
        pretty_print_message(message)
    
    print("✅ Conversation test passed")
    print()


if __name__ == "__main__":
    test_message_serialization()
    test_function_call()
    test_conversation()
    print("All tests passed! ✅")