"""
HTTP client for interacting with A2A-compatible agents.
"""

import requests
from typing import Optional, Dict, Any

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import ErrorContent
from .base import BaseA2AClient
from ..exceptions import A2AConnectionError, A2AResponseError


class A2AClient(BaseA2AClient):
    """Client for interacting with HTTP-based A2A-compatible agents"""
    
    def __init__(self, endpoint_url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30):
        """
        Initialize a client with an agent endpoint URL
        
        Args:
            endpoint_url: The URL of the A2A-compatible agent
            headers: Optional HTTP headers to include in requests
            timeout: Request timeout in seconds
        """
        self.endpoint_url = endpoint_url
        self.headers = headers or {}
        self.timeout = timeout
        
        # Always include content type for JSON
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
    def send_message(self, message: Message) -> Message:
        """
        Send a message to an A2A-compatible agent and get a response
        
        Args:
            message: The A2A message to send
            
        Returns:
            The agent's response as an A2A message
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
        """
        try:
            response = requests.post(
                self.endpoint_url,
                json=message.to_dict(),
                headers=self.headers,
                timeout=self.timeout
            )
            
            # Handle HTTP errors
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                # Try to extract error message from JSON response if possible
                error_msg = str(e)
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = f"{error_msg}: {error_data['error']}"
                except:
                    pass
                
                raise A2AConnectionError(error_msg)
            
            # Parse the response
            try:
                return Message.from_dict(response.json())
            except ValueError as e:
                raise A2AResponseError(f"Invalid response from agent: {str(e)}")
            
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
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
        """
        try:
            response = requests.post(
                self.endpoint_url,
                json=conversation.to_dict(),
                headers=self.headers,
                timeout=self.timeout
            )
            
            # Handle HTTP errors
            try:
                response.raise_for_status()
            except requests.HTTPError as e:
                # Try to extract error message from JSON response if possible
                error_msg = str(e)
                try:
                    error_data = response.json()
                    if "error" in error_data:
                        error_msg = f"{error_msg}: {error_data['error']}"
                except:
                    pass
                
                raise A2AConnectionError(error_msg)
            
            # Parse the response
            try:
                return Conversation.from_dict(response.json())
            except ValueError as e:
                raise A2AResponseError(f"Invalid response from agent: {str(e)}")
            
        except requests.RequestException as e:
            # Create an error message and add it to the conversation
            error_msg = f"Failed to communicate with agent: {str(e)}"
            conversation.create_error_message(error_msg)
            return conversation