"""
Tests for the utils module.
"""

import pytest

from python_a2a import (
    validate_message, validate_conversation, 
    is_valid_message, is_valid_conversation,
    format_message_as_text, format_conversation_as_text,
    create_text_message, create_function_call, create_function_response, create_error_message,
    format_function_params, A2AValidationError
)


class TestValidation:
    def test_validate_message(self, text_message):
        """Test validating a valid message"""
        # Should not raise an exception
        validate_message(text_message)
    
    def test_validate_message_missing_content(self):
        """Test validating a message with missing content"""
        # Create a message with no content
        message = text_message = create_text_message("Hello")
        message.content = None
        
        # Should raise an exception
        with pytest.raises(A2AValidationError):
            validate_message(message)
    
    def test_is_valid_message(self, text_message):
        """Test checking if a message is valid"""
        assert is_valid_message(text_message) is True
        
        # Create an invalid message
        message = text_message = create_text_message("Hello")
        message.content = None
        
        assert is_valid_message(message) is False
    
    def test_validate_conversation(self, conversation):
        """Test validating a valid conversation"""
        # Should not raise an exception
        validate_conversation(conversation)
    
    def test_validate_conversation_mismatched_ids(self, conversation):
        """Test validating a conversation with mismatched IDs"""
        # Create a message with a different conversation ID
        message = create_text_message("Hello")
        message.conversation_id = "different-id"
        
        # Add to conversation
        conversation.messages.append(message)
        
        # Should raise an exception
        with pytest.raises(A2AValidationError):
            validate_conversation(conversation)
    
    def test_is_valid_conversation(self, conversation):
        """Test checking if a conversation is valid"""
        assert is_valid_conversation(conversation) is True
        
        # Create a conversation with an invalid message
        message = create_text_message("Hello")
        message.content = None
        conversation.messages.append(message)
        
        assert is_valid_conversation(conversation) is False


class TestFormatting:
    def test_format_message_as_text(self, text_message, function_call_message, error_message):
        """Test formatting messages as text"""
        # Text message
        text = format_message_as_text(text_message)
        assert "User: Hello, world!" in text
        
        # Function call message
        text = format_message_as_text(function_call_message)
        assert "User calls function: get_weather" in text
        assert "location=New York" in text
        
        # Error message
        text = format_message_as_text(error_message)
        assert "System error:" in text
        assert "An error occurred" in text
    
    def test_format_conversation_as_text(self, conversation):
        """Test formatting a conversation as text"""
        text = format_conversation_as_text(conversation)
        
        # Should contain all messages
        assert "User: Hello, world!" in text
        assert "User calls function: get_weather" in text
        assert "Agent function response: get_weather" in text


class TestConversion:
    def test_create_text_message(self):
        """Test creating a text message"""
        message = create_text_message(
            text="Hello, world!",
            role="user",
            conversation_id="conv-1"
        )
        
        assert message.content.type == "text"
        assert message.content.text == "Hello, world!"
        assert message.role == "user"
        assert message.conversation_id == "conv-1"
    
    def test_create_function_call(self):
        """Test creating a function call message"""
        message = create_function_call(
            function_name="get_weather",
            parameters=[
                {"name": "location", "value": "New York"},
                {"name": "unit", "value": "celsius"}
            ],
            role="user"
        )
        
        assert message.content.type == "function_call"
        assert message.content.name == "get_weather"
        assert len(message.content.parameters) == 2
        assert message.content.parameters[0].name == "location"
        assert message.content.parameters[0].value == "New York"
    
    def test_format_function_params(self):
        """Test formatting function parameters"""
        params = {
            "location": "New York",
            "unit": "celsius"
        }
        
        formatted = format_function_params(params)
        
        assert len(formatted) == 2
        assert {"name": "location", "value": "New York"} in formatted
        assert {"name": "unit", "value": "celsius"} in formatted