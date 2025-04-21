"""
HTTP client for interacting with A2A-compatible agents.
"""

import requests
import uuid
from typing import Optional, Dict, Any, List, Union

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent, ErrorContent
from ..models.agent import AgentCard, AgentSkill
from ..models.task import Task, TaskStatus, TaskState
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
        self.endpoint_url = endpoint_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        
        # Always include content type for JSON
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
        # Try to fetch the agent card for A2A protocol support
        try:
            self.agent_card = self._fetch_agent_card()
        except Exception as e:
            # Create a default agent card
            self.agent_card = AgentCard(
                name="Unknown Agent",
                description="Agent card not available",
                url=self.endpoint_url,
                version="unknown"
            )
    
    def _fetch_agent_card(self):
        """Fetch the agent card from the well-known URL"""
        # Try standard A2A endpoint first
        try:
            card_url = f"{self.endpoint_url}/.well-known/agent.json"
            response = requests.get(card_url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            card_data = response.json()
        except Exception:
            # Try alternate endpoint
            try:
                card_url = f"{self.endpoint_url}/a2a/agent.json"
                response = requests.get(card_url, headers=self.headers, timeout=self.timeout)
                response.raise_for_status()
                card_data = response.json()
            except Exception as e:
                # If both fail, create a minimal card and continue
                return AgentCard(
                    name="Unknown Agent",
                    description="Agent card not available",
                    url=self.endpoint_url,
                    version="unknown"
                )
        
        # Create AgentSkill objects from data
        skills = []
        for skill_data in card_data.get("skills", []):
            skills.append(AgentSkill(
                id=skill_data.get("id", str(uuid.uuid4())),
                name=skill_data.get("name", "Unknown Skill"),
                description=skill_data.get("description", ""),
                tags=skill_data.get("tags", []),
                examples=skill_data.get("examples", [])
            ))
        
        # Create AgentCard object
        return AgentCard(
            name=card_data.get("name", "Unknown Agent"),
            description=card_data.get("description", ""),
            url=self.endpoint_url,
            version=card_data.get("version", "unknown"),
            authentication=card_data.get("authentication"),
            capabilities=card_data.get("capabilities", {}),
            skills=skills,
            provider=card_data.get("provider"),
            documentation_url=card_data.get("documentationUrl")
        )
    
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
        # First try A2A protocol style with tasks
        try:
            # Create a task from the message
            task = self._create_task(message)
            
            # Send the task
            result = self._send_task(task)
            
            # Convert the task result back to a message
            if result.artifacts and len(result.artifacts) > 0:
                for part in result.artifacts[0].get("parts", []):
                    if part.get("type") == "text":
                        return Message(
                            content=TextContent(text=part.get("text", "")),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
        except Exception:
            # Fall back to legacy behavior if A2A protocol fails
            pass
        
        # Legacy behavior - direct message posting
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
                role=MessageRole.AGENT,
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
        # Try legacy behavior first
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
    
    def ask(self, message_text):
        """
        Simple helper for text-based queries
        
        Args:
            message_text: Text message to send
            
        Returns:
            Text response from the agent
        """
        # Check if message is already a Message object
        if isinstance(message_text, str):
            message = Message(
                content=TextContent(text=message_text),
                role=MessageRole.USER
            )
        else:
            message = message_text
        
        # Send message
        response = self.send_message(message)
        
        # Extract text from response
        if hasattr(response.content, "text"):
            return response.content.text
        return "No text response"
    
    def _create_task(self, message):
        """
        Create a new task with a message
        
        Args:
            message: Message object or text
            
        Returns:
            A new Task object
        """
        # Convert string to Message if needed
        if isinstance(message, str):
            message = Message(
                content=TextContent(text=message),
                role=MessageRole.USER
            )
        
        # Create a task
        return Task(
            id=str(uuid.uuid4()),
            message=message.to_dict() if isinstance(message, Message) else message
        )
    
    def _send_task(self, task):
        """
        Send a task to the agent
        
        Args:
            task: The task to send
            
        Returns:
            The updated task with the agent's response
        """
        # Prepare JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tasks/send",
            "params": task.to_dict()
        }
        
        try:
            # Try the standard endpoint first
            try:
                response = requests.post(
                    f"{self.endpoint_url}/tasks/send",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            except Exception:
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.endpoint_url}/a2a/tasks/send",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            result = response_data.get("result", {})
            
            # Convert to Task object
            return Task.from_dict(result)
            
        except Exception as e:
            # Create an error task
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"error": str(e)}
            )
            return task
    
    def get_task(self, task_id, history_length=0):
        """
        Get a task by ID
        
        Args:
            task_id: ID of the task to retrieve
            history_length: Number of history messages to include
            
        Returns:
            The task with current status and results
        """
        # Prepare JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tasks/get",
            "params": {
                "id": task_id,
                "historyLength": history_length
            }
        }
        
        try:
            # Try the standard endpoint first
            try:
                response = requests.post(
                    f"{self.endpoint_url}/tasks/get",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            except Exception:
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.endpoint_url}/a2a/tasks/get",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            result = response_data.get("result", {})
            
            # Convert to Task object
            return Task.from_dict(result)
            
        except Exception as e:
            # Create an error task
            return Task(
                id=task_id,
                status=TaskStatus(
                    state=TaskState.FAILED,
                    message={"error": str(e)}
                )
            )
    
    def cancel_task(self, task_id):
        """
        Cancel a task
        
        Args:
            task_id: ID of the task to cancel
            
        Returns:
            The canceled task
        """
        # Prepare JSON-RPC request
        request_data = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tasks/cancel",
            "params": {
                "id": task_id
            }
        }
        
        try:
            # Try the standard endpoint first
            try:
                response = requests.post(
                    f"{self.endpoint_url}/tasks/cancel",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            except Exception:
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.endpoint_url}/a2a/tasks/cancel",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
            
            # Parse the response
            response_data = response.json()
            result = response_data.get("result", {})
            
            # Convert to Task object
            return Task.from_dict(result)
            
        except Exception as e:
            # Create an error task
            return Task(
                id=task_id,
                status=TaskStatus(
                    state=TaskState.CANCELED,
                    message={"error": str(e)}
                )
            )