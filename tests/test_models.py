"""
Tests for the models module.
"""

import pytest
import json
import uuid
from python_a2a import (
    Message, MessageRole, Conversation,
    TextContent, FunctionCallContent, FunctionResponseContent, ErrorContent,
    FunctionParameter
)


class TestMessage:
    def test_text_message_creation(self):
        """Test creating a text message"""
        message = Message(
            content=TextContent(text="Hello"),
            role=MessageRole.USER
        )
        
        assert message.content.text == "Hello"
        assert message.role == MessageRole.USER
        assert message.message_id is not None
        assert message.parent_message_id is None
        assert message.conversation_id is None
    
    def test_function_call_message_creation(self):
        """Test creating a function call message"""
        message = Message(
            content=FunctionCallContent(
                name="test_function",
                parameters=[
                    FunctionParameter(name="param1", value="value1"),
                    FunctionParameter(name="param2", value=42)
                ]
            ),
            role=MessageRole.USER
        )
        
        assert message.content.name == "test_function"
        assert len(message.content.parameters) == 2
        assert message.content.parameters[0].name == "param1"
        assert message.content.parameters[0].value == "value1"
        assert message.content.parameters[1].name == "param2"
        assert message.content.parameters[1].value == 42
    
    def test_message_serialization(self, text_message):
        """Test serializing a message to JSON and back"""
        # Serialize
        json_str = text_message.to_json()
        
        # Deserialize
        parsed = Message.from_json(json_str)
        
        # Check equality
        assert parsed.content.type == text_message.content.type
        assert parsed.content.text == text_message.content.text
        assert parsed.role == text_message.role
        assert parsed.message_id == text_message.message_id
        assert parsed.conversation_id == text_message.conversation_id
    
    def test_function_call_serialization(self, function_call_message):
        """Test serializing a function call message to JSON and back"""
        # Serialize
        json_str = function_call_message.to_json()
        
        # Deserialize
        parsed = Message.from_json(json_str)
        
        # Check equality
        assert parsed.content.type == function_call_message.content.type
        assert parsed.content.name == function_call_message.content.name
        assert len(parsed.content.parameters) == len(function_call_message.content.parameters)
        assert parsed.content.parameters[0].name == function_call_message.content.parameters[0].name
        assert parsed.content.parameters[0].value == function_call_message.content.parameters[0].value


class TestConversation:
    def test_conversation_creation(self):
        """Test creating a conversation"""
        conversation = Conversation()
        
        assert conversation.conversation_id is not None
        assert len(conversation.messages) == 0
    
    def test_add_message(self):
        """Test adding a message to a conversation"""
        conversation = Conversation()
        message = Message(
            content=TextContent(text="Hello"),
            role=MessageRole.USER
        )
        
        added = conversation.add_message(message)
        
        assert len(conversation.messages) == 1
        assert conversation.messages[0] == message
        assert added == message
        assert message.conversation_id == conversation.conversation_id
    
    def test_create_text_message(self):
        """Test creating a text message in a conversation"""
        conversation = Conversation()
        
        message = conversation.create_text_message(
            text="Hello from conversation",
            role=MessageRole.USER
        )
        
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content.text == "Hello from conversation"
        assert conversation.messages[0].role == MessageRole.USER
        assert conversation.messages[0].conversation_id == conversation.conversation_id
    
    def test_create_function_call(self):
        """Test creating a function call in a conversation"""
        conversation = Conversation()
        
        message = conversation.create_function_call(
            name="test_function",
            parameters=[
                {"name": "param1", "value": "value1"},
                {"name": "param2", "value": 42}
            ],
            role=MessageRole.USER
        )
        
        assert len(conversation.messages) == 1
        assert conversation.messages[0].content.name == "test_function"
        assert len(conversation.messages[0].content.parameters) == 2
        assert conversation.messages[0].content.parameters[0].name == "param1"
        assert conversation.messages[0].content.parameters[0].value == "value1"
    
    def test_conversation_serialization(self, conversation):
        """Test serializing a conversation to JSON and back"""
        # Serialize
        json_str = conversation.to_json()
        
        # Deserialize
        parsed = Conversation.from_json(json_str)
        
        # Check equality
        assert parsed.conversation_id == conversation.conversation_id
        assert len(parsed.messages) == len(conversation.messages)
        
        # Check first message
        assert parsed.messages[0].content.type == conversation.messages[0].content.type
        assert parsed.messages[0].content.text == conversation.messages[0].content.text