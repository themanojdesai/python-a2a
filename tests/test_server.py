"""
Tests for the server module.
"""

import pytest
from unittest.mock import patch, MagicMock

from python_a2a import (
    A2AServer, Message, TextContent, MessageRole, Conversation,
    BaseA2AServer, run_server
)


class TestBaseA2AServer:
    def test_handle_message_abstract(self):
        """Test that handle_message is abstract"""
        with pytest.raises(TypeError):
            # Should raise TypeError because handle_message is abstract
            server = BaseA2AServer()
    
    def test_handle_conversation(self, echo_server, conversation):
        """Test handling a conversation"""
        # Handle the conversation
        result = echo_server.handle_conversation(conversation)
        
        # Should add a new message to the conversation
        assert len(result.messages) == len(conversation.messages) + 1
        
        # Check the new message
        new_message = result.messages[-1]
        assert new_message.role == MessageRole.AGENT
        assert new_message.parent_message_id == conversation.messages[-1].message_id
        assert new_message.conversation_id == conversation.conversation_id


class TestA2AServer:
    def test_init_with_handler(self):
        """Test initializing with a custom handler"""
        handler = lambda message: Message(
            content=TextContent(text="Custom response"),
            role=MessageRole.AGENT
        )
        
        server = A2AServer(message_handler=handler)
        
        assert server.message_handler == handler
    
    def test_handle_message_with_handler(self, text_message):
        """Test handling a message with a custom handler"""
        # Create a mock handler
        handler = MagicMock(return_value=Message(
            content=TextContent(text="Custom response"),
            role=MessageRole.AGENT
        ))
        
        # Create server with the handler
        server = A2AServer(message_handler=handler)
        
        # Handle the message
        response = server.handle_message(text_message)
        
        # Check that the handler was called
        handler.assert_called_once_with(text_message)
        
        # Check the response
        assert response.content.type == "text"
        assert response.content.text == "Custom response"
        assert response.role == MessageRole.AGENT
    
    def test_handle_message_default(self, text_message):
        """Test default message handling"""
        server = A2AServer()
        
        response = server.handle_message(text_message)
        
        assert response.content.type == "text"
        assert response.content.text.startswith("Echo:")
        assert response.role == MessageRole.AGENT
    
    def test_get_metadata(self):
        """Test getting server metadata"""
        server = A2AServer()
        
        metadata = server.get_metadata()
        
        assert "agent_type" in metadata
        assert "capabilities" in metadata
        assert "text" in metadata["capabilities"]


class TestRunServer:
    def test_create_flask_app(self, echo_server):
        """Test creating a Flask app"""
        with patch('python_a2a.server.http.Flask') as MockFlask:
            MockFlask.return_value = MagicMock()
            
            from python_a2a.server.http import create_flask_app
            app = create_flask_app(echo_server)
            
            # Check that Flask was initialized
            MockFlask.assert_called_once()
            
            # The app should have routes for /a2a, /a2a/metadata, and /a2a/health
            app.route.assert_any_call("/a2a", methods=["POST"])
            app.route.assert_any_call("/a2a/metadata", methods=["GET"])
            app.route.assert_any_call("/a2a/health", methods=["GET"])
    
    def test_run_server(self, echo_server):
        """Test running a server"""
        with patch('python_a2a.server.http.create_flask_app') as mock_create_app:
            mock_app = MagicMock()
            mock_create_app.return_value = mock_app
            
            run_server(echo_server, host="localhost", port=8080, debug=True)
            
            # Check that the app was created and run
            mock_create_app.assert_called_once_with(echo_server)
            mock_app.run.assert_called_once_with(host="localhost", port=8080, debug=True)