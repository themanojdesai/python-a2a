"""
Example client for interacting with an A2A-compatible agent
"""

import os
import sys
import json

# Add parent directory to path to import the library
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import (
    A2AClient, Message, Conversation, TextContent, FunctionCallContent,
    FunctionParameter, MessageRole, MessageType
)

def main():
    """
    Example of using the A2A client to interact with a calculator agent
    """
    
    # Create a client pointing to our calculator agent
    client = A2AClient("http://localhost:5000/a2a")
    
    # 1. First, send a text message to the agent
    print("\n--- Sending a text message ---")
    message = Message(
        content=TextContent(text="Hello, calculator!"),
        role=MessageRole.USER
    )
    
    print(f"Sending: {message.to_json()}")
    response = client.send_message(message)
    print(f"Received: {response.to_json()}")
    
    # 2. Now, let's create a function call to perform a calculation
    print("\n--- Calling calculate function (add) ---")
    
    # Create parameters for the function call
    parameters = [
        FunctionParameter(name="operation", value="add"),
        FunctionParameter(name="a", value=5),
        FunctionParameter(name="b", value=3)
    ]
    
    # Create a function call message
    function_call = Message(
        content=FunctionCallContent(name="calculate", parameters=parameters),
        role=MessageRole.USER
    )
    
    print(f"Sending: {function_call.to_json()}")
    response = client.send_message(function_call)
    print(f"Received: {response.to_json()}")
    
    if response.content.type == MessageType.FUNCTION_RESPONSE:
        result = response.content.response.get("result")
        if result is not None:
            print(f"Calculation result: {result}")
        else:
            error = response.content.response.get("error")
            print(f"Calculation error: {error}")
    
    # 3. Let's try another operation (division)
    print("\n--- Calling calculate function (divide) ---")
    
    # Create parameters for the division
    parameters = [
        FunctionParameter(name="operation", value="divide"),
        FunctionParameter(name="a", value=10),
        FunctionParameter(name="b", value=2)
    ]
    
    # Create a function call message
    function_call = Message(
        content=FunctionCallContent(name="calculate", parameters=parameters),
        role=MessageRole.USER
    )
    
    print(f"Sending: {function_call.to_json()}")
    response = client.send_message(function_call)
    print(f"Received: {response.to_json()}")
    
    if response.content.type == MessageType.FUNCTION_RESPONSE:
        result = response.content.response.get("result")
        if result is not None:
            print(f"Calculation result: {result}")
        else:
            error = response.content.response.get("error")
            print(f"Calculation error: {error}")
    
    # 4. Let's try an operation that will cause an error (division by zero)
    print("\n--- Calling calculate function (divide by zero) ---")
    
    # Create parameters for the error case
    parameters = [
        FunctionParameter(name="operation", value="divide"),
        FunctionParameter(name="a", value=10),
        FunctionParameter(name="b", value=0)
    ]
    
    # Create a function call message
    function_call = Message(
        content=FunctionCallContent(name="calculate", parameters=parameters),
        role=MessageRole.USER
    )
    
    print(f"Sending: {function_call.to_json()}")
    response = client.send_message(function_call)
    print(f"Received: {response.to_json()}")
    
    if response.content.type == MessageType.FUNCTION_RESPONSE:
        result = response.content.response.get("result")
        if result is not None:
            print(f"Calculation result: {result}")
        else:
            error = response.content.response.get("error")
            print(f"Calculation error: {error}")
    
    # 5. Now let's demonstrate working with a conversation
    print("\n--- Using a conversation ---")
    
    # Create a new conversation
    conversation = Conversation()
    
    # Add a text message
    conversation.create_text_message(
        text="Hello, I need to perform some calculations.",
        role=MessageRole.USER
    )
    
    # Add a function call
    msg_id = conversation.create_function_call(
        name="calculate",
        parameters=[
            {"name": "operation", "value": "multiply"},
            {"name": "a", "value": 7},
            {"name": "b", "value": 6}
        ],
        role=MessageRole.USER
    ).message_id
    
    print(f"Sending conversation: {conversation.to_json()}")
    updated_conversation = client.send_conversation(conversation)
    print(f"Received updated conversation: {updated_conversation.to_json()}")
    
    # Get the last message from the conversation
    if updated_conversation.messages:
        last_message = updated_conversation.messages[-1]
        if last_message.content.type == MessageType.FUNCTION_RESPONSE:
            result = last_message.content.response.get("result")
            if result is not None:
                print(f"Conversation calculation result: {result}")
            else:
                error = last_message.content.response.get("error")
                print(f"Conversation calculation error: {error}")


if __name__ == "__main__":
    main()