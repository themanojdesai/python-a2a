"""
HTTP client for interacting with A2A-compatible agents.
"""

import requests
import uuid
import json
import re
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
    
    def _extract_json_from_html(self, html_content: str) -> Dict[str, Any]:
        """Extract JSON data from HTML content, typically when agent card is rendered as HTML"""
        try:
            # Look for JSON content in a <pre><code class="language-json"> block
            # This pattern matches JSON content between code tags
            json_pattern = re.compile(r'<code[^>]*>(.*?)</code>', re.DOTALL)
            matches = json_pattern.findall(html_content)
            
            if matches:
                # Get the longest match (most likely to be complete JSON)
                json_text = max(matches, key=len)
                
                # Unescape HTML entities if present
                json_text = json_text.replace('&quot;', '"')
                json_text = json_text.replace('&#34;', '"')
                json_text = json_text.replace('&amp;', '&')
                
                # Parse the extracted JSON
                return json.loads(json_text)
        
        except (json.JSONDecodeError, Exception):
            pass
        
        # Fallback: Try to find any JSON-like content in the HTML
        try:
            json_pattern = re.compile(r'({[\s\S]*"name"[\s\S]*})')
            matches = json_pattern.findall(html_content)
            if matches:
                for match in matches:
                    try:
                        return json.loads(match)
                    except:
                        continue
        except Exception:
            pass
        
        # No valid JSON found
        return {}
    
    def _fetch_agent_card(self):
        """Fetch the agent card from the well-known URL"""
        # Try standard A2A endpoint first
        try:
            card_url = f"{self.endpoint_url}/agent.json"
            
            # Add Accept header to prefer JSON
            headers = dict(self.headers)
            headers["Accept"] = "application/json"
            
            # Make the request
            response = requests.get(card_url, headers=headers, timeout=self.timeout)
            response.raise_for_status()
            
            # Check content type to handle HTML responses
            content_type = response.headers.get("Content-Type", "").lower()
            
            if "json" in content_type:
                # JSON response
                card_data = response.json()
            elif "html" in content_type:
                # HTML response - extract JSON
                card_data = self._extract_json_from_html(response.text)
                if not card_data:
                    raise ValueError("Could not extract JSON from HTML response")
            else:
                # Try parsing as JSON anyway
                try:
                    card_data = response.json()
                except json.JSONDecodeError:
                    # Try to extract JSON from the response text
                    card_data = self._extract_json_from_html(response.text)
                    if not card_data:
                        raise ValueError(f"Unexpected content type: {content_type}")
                        
        except Exception:
            # Try alternate endpoint
            try:
                card_url = f"{self.endpoint_url}/a2a/agent.json"
                
                # Add Accept header to prefer JSON
                headers = dict(self.headers)
                headers["Accept"] = "application/json"
                
                # Make the request
                response = requests.get(card_url, headers=headers, timeout=self.timeout)
                response.raise_for_status()
                
                # Check content type to handle HTML responses
                content_type = response.headers.get("Content-Type", "").lower()
                
                if "json" in content_type:
                    # JSON response
                    card_data = response.json()
                elif "html" in content_type:
                    # HTML response - extract JSON
                    card_data = self._extract_json_from_html(response.text)
                    if not card_data:
                        raise ValueError("Could not extract JSON from HTML response")
                else:
                    # Try parsing as JSON anyway
                    try:
                        card_data = response.json()
                    except json.JSONDecodeError:
                        # Try to extract JSON from the response text
                        card_data = self._extract_json_from_html(response.text)
                        if not card_data:
                            raise ValueError(f"Unexpected content type: {content_type}")
            except Exception as e:
                # If both fail, create a minimal card and continue
                raise A2AConnectionError(
                    f"Failed to fetch agent card: {str(e)}"
                ) from e
        
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
        task_response = None
        try:
            # Create a task from the message
            task = self._create_task(message)
            
            # Send the task
            result = self._send_task(task)
            
            # Convert the task result back to a message
            if result.artifacts and len(result.artifacts) > 0:
                for part in result.artifacts[0].get("parts", []):
                    if part.get("type") == "text":
                        task_response = Message(
                            content=TextContent(text=part.get("text", "")),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
        except Exception:
            # Fall back to legacy behavior if A2A protocol fails
            task_response = None
        
        # Return task response if we got one
        if task_response is not None:
            return task_response
            
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
                # Try to get plain text if JSON parsing fails
                try:
                    text_content = response.text.strip()
                    if text_content:
                        return Message(
                            content=TextContent(text=text_content),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                except:
                    pass
                    
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
                # Try to extract text content from response if JSON parsing fails
                try:
                    text_content = response.text.strip()
                    if text_content:
                        # Create a new message with the response text
                        last_message = conversation.messages[-1] if conversation.messages else None
                        parent_id = last_message.message_id if last_message else None
                        
                        # Add a response message to the conversation
                        conversation.create_text_message(
                            text=text_content,
                            role=MessageRole.AGENT,
                            parent_message_id=parent_id
                        )
                        return conversation
                except:
                    pass
                
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
        if response and hasattr(response, "content"):
            if hasattr(response.content, "text"):
                return response.content.text
            elif hasattr(response.content, "message"):
                return response.content.message
            elif response.content is not None:
                return str(response.content)
        
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
            endpoint_tried = False
            try:
                response = requests.post(
                    f"{self.endpoint_url}/tasks/send",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                endpoint_tried = True
                
                # Check for content type
                if "application/json" not in response.headers.get("Content-Type", "").lower():
                    # Try to parse as JSON anyway
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError:
                        # If we can't parse as JSON, consider this a failure
                        raise ValueError("Response is not valid JSON")
                else:
                    response_data = response.json()
                    
            except Exception as e:
                if endpoint_tried:
                    # If we've tried this endpoint and it failed with a response error,
                    # take a different approach for alternate endpoint
                    raise e
                
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.endpoint_url}/a2a/tasks/send",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Check for content type
                if "application/json" not in response.headers.get("Content-Type", "").lower():
                    # Try to parse as JSON anyway
                    try:
                        response_data = response.json()
                    except json.JSONDecodeError:
                        # If we can't parse as JSON, consider this a failure
                        raise ValueError("Response is not valid JSON")
                else:
                    response_data = response.json()
            
            # Parse the response
            result = response_data.get("result", {})
            
            # If result is empty but we have a text response, create a task with it
            if not result and isinstance(response_data, dict) and "text" in response_data:
                # Create a simple task with text response
                task.artifacts = [{
                    "parts": [{
                        "type": "text",
                        "text": response_data["text"]
                    }]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
                return task
            
            # Convert to Task object or use raw result if parsing fails
            try:
                return Task.from_dict(result)
            except Exception:
                # Create a simple task with the raw result
                task.artifacts = [{
                    "parts": [{
                        "type": "text",
                        "text": str(result)
                    }]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
                return task
            
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
            endpoint_tried = False
            try:
                response = requests.post(
                    f"{self.endpoint_url}/tasks/get",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                endpoint_tried = True
                
                # Check content type and try to parse JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    # If not valid JSON, attempt to handle text response
                    if response.text:
                        return Task(
                            id=task_id,
                            status=TaskStatus(state=TaskState.COMPLETED),
                            artifacts=[{
                                "parts": [{
                                    "type": "text",
                                    "text": response.text
                                }]
                            }]
                        )
                    raise ValueError("Response is not valid JSON")
                    
            except Exception as e:
                if endpoint_tried:
                    # If we've tried this endpoint and got a response error,
                    # take a different approach for alternate endpoint
                    raise e
                    
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.endpoint_url}/a2a/tasks/get",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Check content type and try to parse JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    # If not valid JSON, attempt to handle text response
                    if response.text:
                        return Task(
                            id=task_id,
                            status=TaskStatus(state=TaskState.COMPLETED),
                            artifacts=[{
                                "parts": [{
                                    "type": "text",
                                    "text": response.text
                                }]
                            }]
                        )
                    raise ValueError("Response is not valid JSON")
            
            # Extract result from response data
            result = response_data.get("result", {})
            
            # Handle different response structures
            if not result and isinstance(response_data, dict):
                # Check for direct response fields
                if "text" in response_data:
                    # Create a simple task with the text content
                    return Task(
                        id=task_id,
                        status=TaskStatus(state=TaskState.COMPLETED),
                        artifacts=[{
                            "parts": [{
                                "type": "text",
                                "text": response_data["text"]
                            }]
                        }]
                    )
                elif "content" in response_data:
                    # Handle MCP-style content array
                    content_text = ""
                    for item in response_data["content"]:
                        if item.get("type") == "text":
                            content_text += item.get("text", "")
                    
                    if content_text:
                        return Task(
                            id=task_id,
                            status=TaskStatus(state=TaskState.COMPLETED),
                            artifacts=[{
                                "parts": [{
                                    "type": "text",
                                    "text": content_text
                                }]
                            }]
                        )
            
            # Try to convert to Task object
            try:
                return Task.from_dict(result)
            except Exception:
                # If conversion fails, create a simple task with the raw result
                return Task(
                    id=task_id,
                    status=TaskStatus(state=TaskState.COMPLETED),
                    artifacts=[{
                        "parts": [{
                            "type": "text",
                            "text": str(result or response_data)
                        }]
                    }]
                )
                
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
            endpoint_tried = False
            try:
                response = requests.post(
                    f"{self.endpoint_url}/tasks/cancel",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                endpoint_tried = True
                
                # Try to parse the response as JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    # If not JSON, create a basic canceled task with any text content
                    if response.text:
                        return Task(
                            id=task_id,
                            status=TaskStatus(state=TaskState.CANCELED),
                            artifacts=[{
                                "parts": [{
                                    "type": "text",
                                    "text": response.text
                                }]
                            }]
                        )
                    raise ValueError("Response is not valid JSON")
                    
            except Exception as e:
                if endpoint_tried:
                    # If we've tried this endpoint and got a response error,
                    # rethrow for the catch block
                    raise e
                    
                # Try the alternate endpoint
                response = requests.post(
                    f"{self.endpoint_url}/a2a/tasks/cancel",
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Try to parse the response as JSON
                try:
                    response_data = response.json()
                except json.JSONDecodeError:
                    # If not JSON, create a basic canceled task with any text content
                    if response.text:
                        return Task(
                            id=task_id,
                            status=TaskStatus(state=TaskState.CANCELED),
                            artifacts=[{
                                "parts": [{
                                    "type": "text",
                                    "text": response.text
                                }]
                            }]
                        )
                    raise ValueError("Response is not valid JSON")
            
            # Get the result
            result = response_data.get("result", {})
            
            # Handle different response structures
            if not result and isinstance(response_data, dict):
                # Check for direct response fields
                if "text" in response_data:
                    # Create a simple task with the text content
                    return Task(
                        id=task_id,
                        status=TaskStatus(state=TaskState.CANCELED),
                        artifacts=[{
                            "parts": [{
                                "type": "text",
                                "text": response_data["text"]
                            }]
                        }]
                    )
                elif "content" in response_data:
                    # Handle MCP-style content array
                    content_text = ""
                    for item in response_data["content"]:
                        if item.get("type") == "text":
                            content_text += item.get("text", "")
                    
                    if content_text:
                        return Task(
                            id=task_id,
                            status=TaskStatus(state=TaskState.CANCELED),
                            artifacts=[{
                                "parts": [{
                                    "type": "text",
                                    "text": content_text
                                }]
                            }]
                        )
            
            # Try to convert to Task object
            try:
                return Task.from_dict(result)
            except Exception:
                # If conversion fails, create a simple task with the raw result
                return Task(
                    id=task_id,
                    status=TaskStatus(state=TaskState.CANCELED),
                    artifacts=[{
                        "parts": [{
                            "type": "text",
                            "text": str(result or response_data)
                        }]
                    }]
                )
            
        except Exception as e:
            # Create an error task
            return Task(
                id=task_id,
                status=TaskStatus(
                    state=TaskState.CANCELED,
                    message={"error": str(e)}
                )
            )