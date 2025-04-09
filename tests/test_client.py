"""
Tests for the client module.
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import responses

from python_a2a import (
    A2AClient, Message, TextContent, MessageRole, Conversation,
    FunctionCallContent, FunctionParameter, A2AConnectionError
)


class TestA2AClient:
    def test_init(self):
        """Test initializing the client"""
        client = A2AClient("https://example.com/a2a")
        
        assert client.endpoint_url == "https://example.com/a2a"
        assert "Content-Type" in client.headers
        assert client.headers["Content-Type"] == "application/json"
    
    @responses.activate
    def test_send_message(self, text_message):
        """Test sending a message to an agent"""
        # Setup mock response
        responses.add(
            responses.POST,
            "https://example.com/a2a",
            json={
                "content": {"type": "text", "text": "Response text"},
                "role": "agent",
                "message_id": "response-id",
                "parent_message_id": text_message.message_id,
                "conversation_id": text_message.conversation_id
            },
            status=200
        )
        
        # Create client and send message
        client = A2AClient("https://example.com/a2a")
        response = client.send_message(text_message)
        
        # Check request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://example.com/a2a"
        
        # Check response
        assert response.content.type == "text"
        assert response.content.text == "Response text"
        assert response.role == MessageRole.AGENT
        assert response.parent_message_id == text_message.message_id
        assert response.conversation_id == text_message.conversation_id
    
    @responses.activate
    def test_send_conversation(self, conversation):
        """Test sending a conversation to an agent"""
        # Setup mock response
        responses.add(
            responses.POST,
            "https://example.com/a2a",
            json={
                "conversation_id": conversation.conversation_id,
                "messages": [msg.to_dict() for msg in conversation.messages] + [{
                    "content": {"type": "text", "text": "New response"},
                    "role": "agent",
                    "message_id": "new-msg",
                    "parent_message_id": conversation.messages[-1].message_id,
                    "conversation_id": conversation.conversation_id
                }]
            },
            status=200
        )
        
        # Create client and send conversation
        client = A2AClient("https://example.com/a2a")
        response = client.send_conversation(conversation)
        
        # Check request
        assert len(responses.calls) == 1
        assert responses.calls[0].request.url == "https://example.com/a2a"
        
        # Check response
        assert response.conversation_id == conversation.conversation_id
        assert len(response.messages) == len(conversation.messages) + 1
        assert response.messages[-1].content.type == "text"
        assert response.messages[-1].content.text == "New response"
        assert response.messages[-1].parent_message_id == conversation.messages[-1].message_id
    
    @responses.activate
    def test_connection_error(self, text_message):
        """Test handling connection errors"""
        # Setup mock response
        responses.add(
            responses.POST,
            "https://example.com/a2a",
            json={"error": "Internal Server Error"},
            status=500
        )
        
        # Create client and send message
        client = A2AClient("https://example.com/a2a")
        
        # Should raise an exception
        with pytest.raises(A2AConnectionError):
            client.send_message(text_message)