"""
Client for interacting with A2A-compatible agents
"""

import requests
from typing import Dict, Any

from .models import Message, Conversation, ErrorContent, MessageRole


class A2AClient:
    """Client for interacting with A2A-compatible agents"""
    
    def __init__(self, endpoint_url: str):
        """
        Initialize a client with an agent endpoint URL
        
        Args:
            endpoint_url: The URL of the A2A-compatible agent
        """
        self.endpoint_url = endpoint_url
        
    def send_message(self, message: Message) -> Message:
        """
        Send a message to an A2A-compatible agent and get a response
        
        Args:
            message: The A2A message to send
            
        Returns:
            The agent's response as an A2A message
        """
        try:
            response = requests.post(
                self.endpoint_url,
                json=message.to_dict(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return Message.from_dict(response.json())
        except requests.RequestException as e:
            # Create an error message as response
            return Message(
                content=ErrorContent(message=f"Failed to communicate with agent: {str(e)}"),
                role=MessageRole.SYSTEM,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a full conversation to an A2A-compatible agent and get an updated conversation
        
        Args:
            conversation: The A2A conversation to send
            
        Returns:
            The updated conversation with the agent's response
        """
        try:
            response = requests.post(
                self.endpoint_url,
                json=conversation.to_dict(),
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return Conversation.from_dict(response.json())
        except requests.RequestException as e:
            # Create an error message and add it to the conversation
            error_msg = f"Failed to communicate with agent: {str(e)}"
            conversation.create_error_message(error_msg)
            return conversation