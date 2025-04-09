"""
Base client for interacting with A2A-compatible agents.
"""

from abc import ABC, abstractmethod
from typing import Optional

from ..models.message import Message
from ..models.conversation import Conversation


class BaseA2AClient(ABC):
    """
    Abstract base class for A2A clients.
    
    Provides a common interface for interacting with different types of A2A-compatible
    agents, whether they're accessible via HTTP APIs, local models, or other methods.
    
    All client implementations should inherit from this class and implement the
    `send_message` and `send_conversation` methods.
    """
    
    @abstractmethod
    def send_message(self, message: Message) -> Message:
        """
        Send a message to an A2A-compatible agent and get a response.
        
        Args:
            message: The message to send
            
        Returns:
            The agent's response
        """
        pass
    
    @abstractmethod
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to an A2A-compatible agent and get an updated conversation.
        
        Args:
            conversation: The conversation to send
            
        Returns:
            The updated conversation with the agent's response
        """
        pass