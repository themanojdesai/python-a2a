"""
Base server for implementing A2A-compatible agents.
"""

from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, AsyncGenerator, Union, Callable, Any

from ..models.message import Message
from ..models.conversation import Conversation
from ..exceptions import A2AStreamingError


class BaseA2AServer(ABC):
    """
    Abstract base class for A2A servers.
    
    Provides a common interface for implementing different types of A2A-compatible
    agents, whether they're based on HTTP servers, local models, or other methods.
    
    All server implementations should inherit from this class and implement the
    `handle_message` method at minimum. The `handle_conversation` method has a
    default implementation that processes the last message in the conversation.
    
    Servers that support streaming should also implement the `stream_response` method.
    Servers that need to define custom HTTP routes should implement `setup_routes`.
    """
    
    @abstractmethod
    def handle_message(self, message: Message) -> Message:
        """
        Process an incoming A2A message and generate a response.
        
        This is the core method that should be implemented by all agent servers.
        It takes an incoming message, processes it according to the agent's logic,
        and returns a response message.
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The agent's response message
        """
        pass
    
    def handle_conversation(self, conversation: Conversation) -> Conversation:
        """
        Process an incoming A2A conversation and generate a response.
        
        The default implementation processes the last message in the conversation
        and adds the response to the conversation. Subclasses can override this
        method to implement more sophisticated conversation handling.
        
        Args:
            conversation: The incoming A2A conversation
            
        Returns:
            The updated conversation with the agent's response
        """
        # Create a deep copy of the conversation to avoid modifying the original
        from copy import deepcopy
        result = deepcopy(conversation)
        
        # By default, just respond to the last message
        if not result.messages:
            # Empty conversation, create an error
            result.create_error_message("Empty conversation received")
            return result
            
        last_message = result.messages[-1]
        response = self.handle_message(last_message)
        
        # Set correct parent and conversation IDs
        response.parent_message_id = last_message.message_id
        response.conversation_id = result.conversation_id
        
        # Add the response to the conversation
        result.add_message(response)
        return result
    
    async def stream_response(self, message: Message) -> AsyncGenerator[str, None]:
        """
        Stream a response for the given message (protocol method).
        
        This is a protocol method that should be implemented by servers
        that support streaming. Servers that don't support streaming
        should leave this method as is.
        
        Args:
            message: The A2A message to respond to
            
        Yields:
            Chunks of the response as they arrive
            
        Raises:
            A2AStreamingError: If the server doesn't support streaming
        """
        raise A2AStreamingError("This server does not support streaming")
    
    def setup_routes(self, app) -> None:
        """
        Set up custom HTTP routes for this server.
        
        This method should be implemented by servers that need to define
        custom routes beyond the standard A2A protocol routes. 
        
        The default implementation does nothing.
        
        Args:
            app: The Flask application to add routes to
        """
        pass
        
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this agent server.
        
        Returns:
            A dictionary of metadata about this agent
        """
        # Basic capabilities
        capabilities = ["text"]  # Default capability is text processing
        
        # Add streaming capability if supported
        if hasattr(self, "stream_response") and self.stream_response != BaseA2AServer.stream_response:
            capabilities.append("streaming")
            
        return {
            "agent_type": self.__class__.__name__,
            "capabilities": capabilities,
            "version": "1.0.0"
        }