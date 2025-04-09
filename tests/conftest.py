"""
Test fixtures for the Python A2A package.
"""

import pytest
import uuid
from python_a2a import (
    Message, MessageRole, Conversation,
    TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent,
    FunctionParameter, A2AServer
)


@pytest.fixture
def text_message():
    """Fixture for a text message"""
    return Message(
        content=TextContent(text="Hello, world!"),
        role=MessageRole.USER,
        message_id="msg-1",
        conversation_id="conv-1"
    )


@pytest.fixture
def function_call_message():
    """Fixture for a function call message"""
    return Message(
        content=FunctionCallContent(
            name="get_weather",
            parameters=[
                FunctionParameter(name="location", value="New York"),
                FunctionParameter(name="unit", value="celsius")
            ]
        ),
        role=MessageRole.USER,
        message_id="msg-2",
        conversation_id="conv-1"
    )


@pytest.fixture
def function_response_message():
    """Fixture for a function response message"""
    return Message(
        content=FunctionResponseContent(
            name="get_weather",
            response={"temperature": 22, "conditions": "sunny"}
        ),
        role=MessageRole.AGENT,
        message_id="msg-3",
        parent_message_id="msg-2",
        conversation_id="conv-1"
    )


@pytest.fixture
def error_message():
    """Fixture for an error message"""
    return Message(
        content=ErrorContent(message="An error occurred"),
        role=MessageRole.SYSTEM,
        message_id="msg-4",
        conversation_id="conv-1"
    )


@pytest.fixture
def conversation(text_message, function_call_message, function_response_message):
    """Fixture for a conversation"""
    conversation = Conversation(conversation_id="conv-1")
    conversation.add_message(text_message)
    conversation.add_message(function_call_message)
    conversation.add_message(function_response_message)
    return conversation


@pytest.fixture
def echo_server():
    """Fixture for a simple echo server"""
    class EchoServer(A2AServer):
        def handle_message(self, message):
            if message.content.type == "text":
                return Message(
                    content=TextContent(text=f"Echo: {message.content.text}"),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            else:
                return Message(
                    content=TextContent(text=f"Received {message.content.type} message"),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
    
    return EchoServer()