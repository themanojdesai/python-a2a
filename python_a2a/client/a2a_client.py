"""
Enhanced A2A client with protocol support.
"""

import requests
import uuid
from typing import Dict, Any, Optional, List, Union

from ..models.agent import AgentCard, AgentSkill
from ..models.task import Task, TaskStatus, TaskState
from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import TextContent
from .base import BaseA2AClient
from ..exceptions import A2AConnectionError


class A2AClient(BaseA2AClient):
    """
    Enhanced A2A client with protocol support
    """
    
    def __init__(self, url, headers=None):
        """
        Initialize a client for an A2A agent
        
        Args:
            url: The base URL of the agent
            headers: Optional HTTP headers to include in requests
        """
        self.url = url.rstrip("/")
        self.headers = headers or {}
        
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
        # Try to fetch the agent card
        try:
            self.agent_card = self._fetch_agent_card()
        except Exception as e:
            print(f"Warning: Could not fetch agent card: {e}")
            # Create a default agent card
            self.agent_card = AgentCard(
                name="Unknown Agent",
                description="Agent card not available",
                url=self.url,
                version="unknown"
            )
    
    def _fetch_agent_card(self):
        """Fetch the agent card from the well-known URL"""
        # Try standard A2A endpoint first
        try:
            card_url = f"{self.url}/agent.json"
            response = requests.get(card_url, headers=self.headers)
            response.raise_for_status()
            card_data = response.json()
        except Exception:
            # Try alternate endpoint
            card_url = f"{self.url}/a2a/agent.json"
            response = requests.get(card_url, headers=self.headers)
            response.raise_for_status()
            card_data = response.json()
        
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
            url=self.url,
            version=card_data.get("version", "unknown"),
            authentication=card_data.get("authentication"),
            capabilities=card_data.get("capabilities", {}),
            skills=skills,
            provider=card_data.get("provider"),
            documentation_url=card_data.get("documentationUrl")
        )
    
    def send_message(self, message: Message) -> Message:
        """
        Send a message to the A2A agent (required for BaseA2AClient)
        
        Args:
            message: The message to send
            
        Returns:
            The agent's response
        """
        # Create a task from the message
        task = self.create_task(message)
        
        # Send the task
        result = self.send_task(task)
        
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
        
        # If no artifacts found, create a default response
        return Message(
            content=TextContent(text="No response content"),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to the A2A agent (required for BaseA2AClient)
        
        Args:
            conversation: The conversation to send
            
        Returns:
            The updated conversation
        """
        if not conversation.messages:
            return conversation
        
        # Get the last message
        last_message = conversation.messages[-1]
        
        # Send it to the agent
        response = self.send_message(last_message)
        
        # Add the response to the conversation
        conversation.add_message(response)
        
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
    
    def create_task(self, message):
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
    
    def send_task(self, task):
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
                    f"{self.url}/tasks/send",
                    json=request_data,
                    headers=self.headers
                )
                response.raise_for_status()
            except Exception:
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.url}/a2a/tasks/send",
                    json=request_data,
                    headers=self.headers
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
                    f"{self.url}/tasks/get",
                    json=request_data,
                    headers=self.headers
                )
                response.raise_for_status()
            except Exception:
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.url}/a2a/tasks/get",
                    json=request_data,
                    headers=self.headers
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
                    f"{self.url}/tasks/cancel",
                    json=request_data,
                    headers=self.headers
                )
                response.raise_for_status()
            except Exception:
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.url}/a2a/tasks/cancel",
                    json=request_data,
                    headers=self.headers
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