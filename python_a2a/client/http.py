"""
HTTP client for interacting with A2A-compatible agents.
"""

import requests
import uuid
import json
import re
import asyncio
import logging
from typing import Optional, Dict, Any, List, Union, AsyncGenerator, Callable

from ..models.message import Message, MessageRole
from ..models.conversation import Conversation
from ..models.content import (
    TextContent, ErrorContent, FunctionCallContent, 
    FunctionResponseContent, FunctionParameter
)
from ..models.agent import AgentCard, AgentSkill
from ..models.task import Task, TaskStatus, TaskState
from .base import BaseA2AClient
from ..exceptions import A2AConnectionError, A2AResponseError, A2AStreamingError

logger = logging.getLogger(__name__)


class A2AClient(BaseA2AClient):
    """Client for interacting with HTTP-based A2A-compatible agents"""
    
    def __init__(self, endpoint_url: str, headers: Optional[Dict[str, str]] = None, 
                 timeout: int = 30, google_a2a_compatible: bool = False):
        """
        Initialize a client with an agent endpoint URL
        
        Args:
            endpoint_url: The URL of the A2A-compatible agent
            headers: Optional HTTP headers to include in requests
            timeout: Request timeout in seconds
            google_a2a_compatible: Whether to use Google A2A format by default (not normally needed)
        """
        self.endpoint_url = endpoint_url.rstrip("/")
        self.headers = headers or {}
        self.timeout = timeout
        self._use_google_a2a = google_a2a_compatible
        self._protocol_detected = False  # True after we've detected the protocol type
        
        # Always include content type for JSON
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        
        # Try to fetch the agent card for A2A protocol support
        try:
            self.agent_card = self._fetch_agent_card()
            
            # Check for protocol hints in the agent card
            if hasattr(self.agent_card, 'capabilities'):
                capabilities = getattr(self.agent_card, 'capabilities', {})
                if isinstance(capabilities, dict) and (
                    capabilities.get("google_a2a_compatible") or 
                    capabilities.get("parts_array_format")
                ):
                    self._use_google_a2a = True
                    self._protocol_detected = True
        except Exception as e:
            # Create a default agent card
            self.agent_card = AgentCard(
                name="Unknown Agent",
                description="Agent card not available",
                url=self.endpoint_url,
                version="unknown"
            )
            
    def get_agent_card(self) -> AgentCard:
        """
        Get the agent card for this client.
        
        Returns:
            The agent card for the connected agent
        """
        return self.agent_card
    
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
        
        # Check for protocol hints in the agent card
        if "capabilities" in card_data:
            capabilities = card_data.get("capabilities", {})
            if isinstance(capabilities, dict) and (
                capabilities.get("google_a2a_compatible") or 
                capabilities.get("parts_array_format")
            ):
                self._use_google_a2a = True
                self._protocol_detected = True
        
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
    
    def _detect_protocol_version(self, response_error=None):
        """
        Detect protocol version based on the error or endpoint probing
        
        Args:
            response_error: Optional error from a failed request
            
        Returns:
            True if Google A2A format should be used, False otherwise
        """
        # Already detected or explicitly set
        if self._protocol_detected:
            return self._use_google_a2a
        
        # Check if error contains clues about missing 'parts' field (Google A2A)
        if response_error:
            error_str = str(response_error).lower()
            # Be very specific with error detection to avoid false positives
            if "parts" in error_str and any(term in error_str for term in 
                                        ["required", "missing", "validation", "schema"]):
                self._use_google_a2a = True
                self._protocol_detected = True
                return True
            
            # Special handling for specific common Google A2A errors with strict pattern
            if ("tagged-union" in error_str and "parts" in error_str and 
                "missing" in error_str):
                self._use_google_a2a = True
                self._protocol_detected = True
                return True
        
        # No clear indication, use the current setting
        return self._use_google_a2a
    
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
        # Try possible endpoints in order of preference
        endpoints_to_try = [
            self.endpoint_url,                  # Try the exact URL first
            self.endpoint_url.rstrip("/"),      # URL without trailing slash
            f"{self.endpoint_url.rstrip('/')}/a2a",  # Try /a2a endpoint
            f"{self.endpoint_url.rstrip('/')}/tasks/send"  # Try direct tasks endpoint
        ]
        
        # Deduplicate endpoints
        endpoints_to_try = list(dict.fromkeys(endpoints_to_try))
        
        # First try A2A protocol style with tasks
        task_response = None
        for endpoint in endpoints_to_try:
            try:
                # Create a task from the message
                task = self._create_task(message)
                
                # Try to send the task to this endpoint
                result = self._send_task(task, endpoint_override=endpoint)
                
                # If we get here, the endpoint worked
                # Remember this working endpoint for future requests
                self.endpoint_url = endpoint
                
                # Convert the task result back to a message
                if result.artifacts and len(result.artifacts) > 0:
                    for artifact in result.artifacts:
                        if "parts" in artifact:
                            parts = artifact["parts"]
                            for part in parts:
                                if part.get("type") == "text":
                                    task_response = Message(
                                        content=TextContent(text=part.get("text", "")),
                                        role=MessageRole.AGENT,
                                        parent_message_id=message.message_id,
                                        conversation_id=message.conversation_id
                                    )
                                    break
                                elif part.get("type") == "function_response":
                                    task_response = Message(
                                        content=FunctionResponseContent(
                                            name=part.get("name", ""),
                                            response=part.get("response", {})
                                        ),
                                        role=MessageRole.AGENT,
                                        parent_message_id=message.message_id,
                                        conversation_id=message.conversation_id
                                    )
                                    break
                                elif part.get("type") == "function_call":
                                    # Convert parameters to FunctionParameter objects
                                    params = []
                                    for param in part.get("parameters", []):
                                        params.append(FunctionParameter(
                                            name=param.get("name", ""),
                                            value=param.get("value", "")
                                        ))
                                    
                                    task_response = Message(
                                        content=FunctionCallContent(
                                            name=part.get("name", ""),
                                            parameters=params
                                        ),
                                        role=MessageRole.AGENT,
                                        parent_message_id=message.message_id,
                                        conversation_id=message.conversation_id
                                    )
                                    break
                                elif part.get("type") == "error":
                                    task_response = Message(
                                        content=ErrorContent(message=part.get("message", "")),
                                        role=MessageRole.AGENT,
                                        parent_message_id=message.message_id,
                                        conversation_id=message.conversation_id
                                    )
                                    break
                        
                # If we got a response, return it
                if task_response is not None:
                    return task_response
                    
            except Exception as e:
                # This endpoint didn't work, try the next one
                continue
        
        # If we get here, all task endpoints failed, try legacy behavior - direct message posting
        # First try standard python_a2a format
        if not self._use_google_a2a:
            for endpoint in endpoints_to_try:
                try:
                    # Standard python_a2a format
                    response = requests.post(
                        endpoint,
                        json=message.to_dict(),
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    # If we succeed, remember this endpoint
                    self.endpoint_url = endpoint
                    
                    # Check for HTTP error
                    try:
                        response.raise_for_status()
                    except requests.HTTPError as e:
                        # Try to extract error details for protocol detection
                        try:
                            error_data = response.json()
                            error_str = json.dumps(error_data)
                        except:
                            error_str = str(e)
                        
                        # Update protocol detection based on error
                        should_retry_with_google = self._detect_protocol_version(error_str)
                        
                        # If we detected Google A2A format, break to try Google format
                        if should_retry_with_google:
                            break
                        
                        # Otherwise try next endpoint
                        continue
                    
                    # Process successful response
                    try:
                        # Check if response has clear Google A2A format indicators
                        response_data = response.json()
                        
                        # Check for clear Google A2A format markers
                        if ("parts" in response_data and isinstance(response_data.get("parts"), list) and
                            "role" in response_data and not "content" in response_data):
                            # Response is in Google A2A format
                            self._use_google_a2a = True
                            self._protocol_detected = True
                            return Message.from_google_a2a(response_data)
                        else:
                            # Standard format
                            return Message.from_dict(response_data)
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
                            
                        # Try next endpoint
                        continue
                        
                except requests.RequestException:
                    # Try next endpoint
                    continue
        
        # Try with Google A2A format if needed
        if self._use_google_a2a or self._protocol_detected:
            for endpoint in endpoints_to_try:
                try:
                    # Google A2A format
                    response = requests.post(
                        endpoint,
                        json=message.to_google_a2a(),
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    # If we succeed, remember this endpoint
                    self.endpoint_url = endpoint
                    
                    # Handle HTTP errors
                    try:
                        response.raise_for_status()
                    except requests.HTTPError:
                        # Try next endpoint
                        continue
                    
                    # Process successful response
                    try:
                        response_data = response.json()
                        
                        # Check for Google A2A format response
                        if ("parts" in response_data and 
                            isinstance(response_data.get("parts"), list) and 
                            "role" in response_data):
                            # Google A2A format response
                            self._use_google_a2a = True
                            self._protocol_detected = True
                            return Message.from_google_a2a(response_data)
                        else:
                            # Standard format response
                            return Message.from_dict(response_data)
                    except Exception:
                        # Try to handle plain text response
                        try:
                            text = response.text.strip()
                            if text:
                                return Message(
                                    content=TextContent(text=text),
                                    role=MessageRole.AGENT,
                                    parent_message_id=message.message_id,
                                    conversation_id=message.conversation_id
                                )
                        except:
                            pass
                        
                        # Try next endpoint
                        continue
                    
                except requests.RequestException:
                    # Try next endpoint
                    continue
        
        # If we get here, all endpoints failed
        return Message(
            content=ErrorContent(message=f"Failed to communicate with agent at {self.endpoint_url}. Tried multiple endpoint variations."),
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
        # Try possible endpoints in order of preference
        endpoints_to_try = [
            self.endpoint_url,                  # Try the exact URL first
            self.endpoint_url.rstrip("/"),      # URL without trailing slash
            f"{self.endpoint_url.rstrip('/')}/a2a",  # Try /a2a endpoint
        ]
        
        # Deduplicate endpoints
        endpoints_to_try = list(dict.fromkeys(endpoints_to_try))
        
        # First try standard python_a2a format
        if not self._use_google_a2a:
            for endpoint in endpoints_to_try:
                try:
                    response = requests.post(
                        endpoint,
                        json=conversation.to_dict(),
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    # If we succeed, remember this endpoint
                    self.endpoint_url = endpoint
                    
                    # Handle HTTP errors
                    try:
                        response.raise_for_status()
                    except requests.HTTPError as e:
                        # Try to extract error details for protocol detection
                        try:
                            error_data = response.json()
                            error_str = json.dumps(error_data)
                        except:
                            error_str = str(e)
                        
                        # Update protocol detection based on error
                        should_retry_with_google = self._detect_protocol_version(error_str)
                        
                        # If we detected Google A2A format, break to try Google format
                        if should_retry_with_google:
                            break
                        
                        # Otherwise try next endpoint
                        continue
                    
                    # Process successful response
                    try:
                        response_data = response.json()
                        
                        # Check if the response is in Google A2A format
                        if "messages" in response_data and isinstance(response_data["messages"], list):
                            if (response_data["messages"] and 
                                "parts" in response_data["messages"][0] and 
                                isinstance(response_data["messages"][0].get("parts"), list)):
                                # Response is in Google A2A format
                                self._use_google_a2a = True
                                self._protocol_detected = True
                                return Conversation.from_google_a2a(response_data)
                        
                        # Standard format
                        return Conversation.from_dict(response_data)
                    except Exception:
                        # Try to extract text content if JSON parsing fails
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
                        
                        # Try next endpoint
                        continue
                
                except requests.RequestException:
                    # Try next endpoint
                    continue
        
        # Try with Google A2A format if needed
        if self._use_google_a2a or self._protocol_detected:
            for endpoint in endpoints_to_try:
                try:
                    # Google A2A format
                    response = requests.post(
                        endpoint,
                        json=conversation.to_google_a2a(),
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    
                    # If we succeed, remember this endpoint
                    self.endpoint_url = endpoint
                    
                    # Handle HTTP errors
                    try:
                        response.raise_for_status()
                    except requests.HTTPError:
                        # Try next endpoint
                        continue
                    
                    # Process successful response
                    try:
                        response_data = response.json()
                        
                        # Check if the response is in Google A2A format
                        if "messages" in response_data and isinstance(response_data["messages"], list):
                            if (response_data["messages"] and 
                                "parts" in response_data["messages"][0] and 
                                isinstance(response_data["messages"][0].get("parts"), list)):
                                # Response is in Google A2A format
                                self._use_google_a2a = True
                                self._protocol_detected = True
                                return Conversation.from_google_a2a(response_data)
                        
                        # Standard format
                        return Conversation.from_dict(response_data)
                    except Exception:
                        # Try to extract text content if JSON parsing fails
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
                        
                        # Try next endpoint
                        continue
                
                except requests.RequestException:
                    # Try next endpoint
                    continue
        
        # If we get here, all endpoints failed
        # Create an error message and add it to the conversation
        error_msg = f"Failed to communicate with agent at {self.endpoint_url}. Tried multiple endpoint variations."
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
            content_type = getattr(response.content, "type", None)
            
            if content_type == "text":
                return response.content.text
            elif content_type == "error":
                return f"Error: {response.content.message}"
            elif content_type == "function_response":
                return f"Function '{response.content.name}' returned: {json.dumps(response.content.response, indent=2)}"
            elif content_type == "function_call":
                params = {p.name: p.value for p in response.content.parameters}
                return f"Function call '{response.content.name}' with parameters: {json.dumps(params, indent=2)}"
            elif response.content is not None:
                return str(response.content)
        
        # If text extraction from standard format failed, check for Google A2A format
        if response:
            try:
                # Try to access parts directly
                google_format = response.to_google_a2a()
                if "parts" in google_format:
                    for part in google_format["parts"]:
                        if part.get("type") == "text" and "text" in part:
                            return part["text"]
            except:
                pass
        
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
    
    def _send_task(self, task, endpoint_override=None):
        """
        Send a task to the agent
        
        Args:
            task: The task to send
            endpoint_override: Optional override for the endpoint URL
            
        Returns:
            The updated task with the agent's response
        """
        # Use the override if provided, otherwise use the standard endpoint
        base_url = endpoint_override if endpoint_override else self.endpoint_url
        
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
                endpoint = f"{base_url}/tasks/send"
                if endpoint.endswith("/tasks/send/tasks/send"):
                    # Avoid doubled path
                    endpoint = endpoint.replace("/tasks/send/tasks/send", "/tasks/send")
                    
                response = requests.post(
                    endpoint,
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
                endpoint = f"{base_url}/a2a/tasks/send"
                if endpoint.endswith("/a2a/tasks/send/a2a/tasks/send"):
                    # Avoid doubled path
                    endpoint = endpoint.replace("/a2a/tasks/send/a2a/tasks/send", "/a2a/tasks/send")
                    
                response = requests.post(
                    endpoint,
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
                result_task = Task.from_dict(result)
                
                # Check if this might be Google A2A format
                if result and isinstance(result, dict):
                    try:
                        for artifact in result.get("artifacts", []):
                            if "parts" in artifact and isinstance(artifact["parts"], list):
                                for part in artifact["parts"]:
                                    if part.get("type") == "text" and "text" in part:
                                        # This looks like Google A2A format
                                        self._use_google_a2a = True
                                        self._protocol_detected = True
                                        break
                    except:
                        pass
                        
                return result_task
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
        
        # Try possible endpoints
        endpoints = [
            f"{self.endpoint_url}/tasks/get",
            f"{self.endpoint_url}/a2a/tasks/get"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Parse the response
                response_data = response.json()
                result = response_data.get("result", {})
                
                # Try to convert to Task object
                try:
                    # Check for Google A2A format
                    if result and isinstance(result, dict):
                        for artifact in result.get("artifacts", []):
                            if "parts" in artifact and isinstance(artifact["parts"], list):
                                for part in artifact["parts"]:
                                    if part.get("type") == "text" and "text" in part:
                                        # This looks like Google A2A format
                                        self._use_google_a2a = True
                                        self._protocol_detected = True
                                        return Task.from_google_a2a(result)
                            
                    # Standard format
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
            except Exception:
                # Try next endpoint
                continue
        
        # If we get here, all endpoints failed
        return Task(
            id=task_id,
            status=TaskStatus(
                state=TaskState.FAILED,
                message={"error": f"Failed to get task from {self.endpoint_url}"}
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
        
        # Try possible endpoints
        endpoints = [
            f"{self.endpoint_url}/tasks/cancel",
            f"{self.endpoint_url}/a2a/tasks/cancel"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.post(
                    endpoint,
                    json=request_data,
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                
                # Parse the response
                response_data = response.json()
                result = response_data.get("result", {})
                
                # Try to convert to Task object
                try:
                    # Check for Google A2A format
                    if result and isinstance(result, dict):
                        for artifact in result.get("artifacts", []):
                            if "parts" in artifact and isinstance(artifact["parts"], list):
                                for part in artifact["parts"]:
                                    if part.get("type") == "text" and "text" in part:
                                        # This looks like Google A2A format
                                        self._use_google_a2a = True
                                        self._protocol_detected = True
                                        return Task.from_google_a2a(result)
                        
                    # Standard format
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
            except Exception:
                # Try next endpoint
                continue
        
        # If we get here, all endpoints failed
        return Task(
            id=task_id,
            status=TaskStatus(
                state=TaskState.CANCELED,
                message={"error": f"Failed to cancel task on {self.endpoint_url}"}
            )
        )
    
    def use_google_a2a_format(self, use_google_format: bool = True) -> None:
        """
        Set whether to use Google A2A format for requests
        
        This method is not typically needed as format is automatically detected.
        
        Args:
            use_google_format: Whether to use Google A2A format
        """
        self._use_google_a2a = use_google_format
        self._protocol_detected = True
        
    def is_using_google_a2a_format(self) -> bool:
        """
        Check if using Google A2A format
        
        Returns:
            True if using Google A2A format, False otherwise
        """
        return self._use_google_a2a
        
    async def send_message_async(self, message: Message) -> Message:
        """
        Send a message to an A2A-compatible agent asynchronously.
        
        Args:
            message: The A2A message to send
            
        Returns:
            The agent's response as an A2A message
        """
        # Implement async version of send_message using asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_message, message)
    
    async def send_conversation_async(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to an A2A-compatible agent asynchronously.
        
        Args:
            conversation: The conversation to send
            
        Returns:
            The updated conversation with the agent's response
        """
        # Implement async version of send_conversation using asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_conversation, conversation)
    
    async def send_task_async(self, task: Task) -> Task:
        """
        Send a task to an A2A-compatible agent asynchronously.
        
        Args:
            task: The task to send
            
        Returns:
            The updated task with the agent's response
        """
        # Implement async version of _send_task using asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._send_task, task)
    
    async def check_streaming_support(self) -> bool:
        """
        Check if the agent supports streaming.
        
        Returns:
            True if streaming is supported, False otherwise
        """
        try:
            # Check the agent card capabilities
            if hasattr(self.agent_card, 'capabilities'):
                capabilities = getattr(self.agent_card, 'capabilities', {})
                if isinstance(capabilities, dict) and capabilities.get("streaming", False):
                    return True
            
            # Try to fetch agent metadata to check for streaming capability
            try:
                # Add Accept header to prefer JSON
                headers = dict(self.headers)
                headers["Accept"] = "application/json"
                
                # Try the standard endpoint first
                endpoint = f"{self.endpoint_url}/agent.json"
                try:
                    async with self._create_aiohttp_session() as session:
                        async with session.get(endpoint, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json(content_type=None)
                                if isinstance(data, dict) and isinstance(data.get("capabilities"), dict):
                                    return data.get("capabilities", {}).get("streaming", False)
                except:
                    # Try alternate endpoint
                    endpoint = f"{self.endpoint_url}/a2a/agent.json"
                    async with self._create_aiohttp_session() as session:
                        async with session.get(endpoint, headers=headers) as response:
                            if response.status == 200:
                                data = await response.json(content_type=None)
                                if isinstance(data, dict) and isinstance(data.get("capabilities"), dict):
                                    return data.get("capabilities", {}).get("streaming", False)
            except:
                # Ignore errors in the async check
                pass
                
            # Fall back to synchronous check
            try:
                # Add Accept header to prefer JSON
                headers = dict(self.headers)
                headers["Accept"] = "application/json"
                
                # Try the standard endpoint first
                endpoint = f"{self.endpoint_url}/agent.json"
                try:
                    response = requests.get(endpoint, headers=headers, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and isinstance(data.get("capabilities"), dict):
                            return data.get("capabilities", {}).get("streaming", False)
                except:
                    # Try alternate endpoint
                    endpoint = f"{self.endpoint_url}/a2a/agent.json"
                    response = requests.get(endpoint, headers=headers, timeout=self.timeout)
                    if response.status_code == 200:
                        data = response.json()
                        if isinstance(data, dict) and isinstance(data.get("capabilities"), dict):
                            return data.get("capabilities", {}).get("streaming", False)
            except:
                # Ignore errors in the synchronous check
                pass
        except Exception as e:
            logger.warning(f"Error checking streaming support: {e}")
        
        # Default to false if we couldn't determine streaming support
        return False
    
    def _create_aiohttp_session(self):
        """
        Create an aiohttp session for async HTTP requests.
        
        Returns:
            An aiohttp session
        
        Raises:
            ImportError: If aiohttp is not installed
        """
        try:
            import aiohttp
            return aiohttp.ClientSession(
                headers=self.headers,
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        except ImportError:
            raise ImportError(
                "aiohttp is required for streaming. "
                "Install it with 'pip install aiohttp'."
            )
    
    async def stream_response(
        self, 
        message: Message,
        chunk_callback: Optional[Callable[[Union[str, Dict]], None]] = None
    ) -> AsyncGenerator[Union[str, Dict], None]:
        """
        Stream a response from an A2A-compatible agent.
        
        Args:
            message: The A2A message to send
            chunk_callback: Optional callback function for each chunk
            
        Yields:
            Response chunks from the agent
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
            A2AStreamingError: If streaming is not supported by the agent
        """
        # Check if streaming is supported
        supports_streaming = await self.check_streaming_support()
        
        if not supports_streaming:
            # Fall back to non-streaming if not supported
            response = await self.send_message_async(message)
            
            # Get text from response
            if hasattr(response.content, "text"):
                result = response.content.text
            else:
                result = str(response.content)
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(result)
            yield result
            return
        
        # Try to import aiohttp for streaming
        try:
            import aiohttp
        except ImportError:
            # Fall back to non-streaming if aiohttp not available
            response = await self.send_message_async(message)
            
            # Get text from response
            if hasattr(response.content, "text"):
                result = response.content.text
            else:
                result = str(response.content)
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(result)
            yield result
            return
            
        # Real streaming implementation with aiohttp
        try:
            # Set up streaming request
            async with self._create_aiohttp_session() as session:
                headers = dict(self.headers)
                # Add headers to request server-sent events
                headers['Accept'] = 'text/event-stream'
                
                # Try possible endpoints in order of preference
                endpoints_to_try = [
                    f"{self.endpoint_url}/stream",  # Standard streaming endpoint
                    f"{self.endpoint_url}/a2a/stream",  # A2A-specific streaming endpoint
                ]
                
                response = None
                last_error = None
                
                for endpoint in endpoints_to_try:
                    try:
                        logger.debug(f"Trying streaming endpoint: {endpoint}")
                        
                        # Close previous response if we had one
                        if response:
                            await response.release()
                            
                        # Prepare message data for the request
                        # Try different formats based on our protocol detection
                        if self._use_google_a2a:
                            data = message.to_google_a2a()
                        else:
                            data = message.to_dict()
                            
                        # Make the request
                        response = await session.post(
                            endpoint,
                            json=data,
                            headers=headers
                        )
                        
                        # If we succeed, break out of the loop
                        if response.status < 400:
                            break
                            
                        # Store error for retry
                        error_text = await response.text()
                        last_error = A2AConnectionError(f"HTTP error {response.status}: {error_text}")
                        
                    except Exception as e:
                        # Log the error and continue to next endpoint
                        logger.debug(f"Error with streaming endpoint {endpoint}: {e}")
                        last_error = e
                
                # If we didn't get a successful response, raise the last error
                if not response or response.status >= 400:
                    if last_error:
                        raise last_error
                    else:
                        raise A2AConnectionError("All streaming endpoints failed")
                
                # Process the streaming response
                try:
                    buffer = ""
                    
                    async for chunk in response.content.iter_chunks():
                        if not chunk:
                            continue
                            
                        # Decode chunk
                        chunk_text = chunk[0].decode('utf-8')
                        buffer += chunk_text
                        
                        # Process complete events (separated by double newlines)
                        while "\n\n" in buffer:
                            event, buffer = buffer.split("\n\n", 1)
                            
                            # Extract data fields and event type from event
                            event_type = "message"  # Default event type
                            event_data = None
                            
                            for line in event.split("\n"):
                                if line.startswith("event:"):
                                    event_type = line[6:].strip()
                                elif line.startswith("data:"):
                                    event_data = line[5:].strip()
                            
                            # Skip if no data
                            if not event_data:
                                continue
                                
                            # Try to parse the data as JSON
                            try:
                                data_obj = json.loads(event_data)
                                # Process with callback if provided
                                if chunk_callback:
                                    chunk_callback(data_obj)
                                
                                # Extract text from object if possible
                                text_content = self._extract_text_from_chunk(data_obj)
                                if text_content:
                                    yield text_content
                                else:
                                    yield data_obj
                            except json.JSONDecodeError:
                                # Not JSON, treat as text
                                if chunk_callback:
                                    chunk_callback(event_data)
                                yield event_data
                
                finally:
                    # Ensure we close the response
                    if response:
                        await response.release()
        
        except Exception as e:
            # Fall back to non-streaming for other errors
            logger.warning(f"Error in streaming, falling back to non-streaming: {e}")
            response = await self.send_message_async(message)
            
            # Get text from response
            if hasattr(response.content, "text"):
                result = response.content.text
            else:
                result = str(response.content)
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(result)
            yield result
            
    def _extract_text_from_chunk(self, chunk: Any) -> Optional[str]:
        """
        Extract text content from a response chunk.
        
        Args:
            chunk: The chunk to extract text from
            
        Returns:
            The extracted text or None if no text could be extracted
        """
        # Handle different types of chunks
        if isinstance(chunk, str):
            return chunk
            
        if isinstance(chunk, dict):
            # First check for content field
            if "content" in chunk:
                # Content might be a string or object
                content = chunk["content"]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict) and "text" in content:
                    return content["text"]
                    
            # Check for text field
            if "text" in chunk:
                return chunk["text"]
                
            # Check for parts array
            if "parts" in chunk and isinstance(chunk["parts"], list):
                for part in chunk["parts"]:
                    if isinstance(part, dict) and part.get("type") == "text" and "text" in part:
                        return part["text"]
        
        # Return None if no text could be extracted
        return None
        
    async def stream_task(
        self, 
        task: Task,
        chunk_callback: Optional[Callable[[Dict], None]] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream the execution of a task.
        
        Args:
            task: The task to execute
            chunk_callback: Optional callback function for each chunk
            
        Yields:
            Task status and result chunks
        """
        # Check if streaming is supported
        supports_streaming = await self.check_streaming_support()
        
        if not supports_streaming:
            # Fall back to non-streaming if not supported
            result = await self.send_task_async(task)
            
            # Create a single chunk with the complete result
            chunk = {
                "status": result.status.state.value if hasattr(result.status, "state") else "unknown",
                "artifacts": result.artifacts
            }
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(chunk)
            yield chunk
            return
        
        # Try to import aiohttp for streaming
        try:
            import aiohttp
        except ImportError:
            # Fall back to non-streaming if aiohttp not available
            result = await self.send_task_async(task)
            
            # Create a single chunk with the complete result
            chunk = {
                "status": result.status.state.value if hasattr(result.status, "state") else "unknown",
                "artifacts": result.artifacts
            }
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(chunk)
            yield chunk
            return
        
        # Real streaming implementation with aiohttp
        try:
            # Set up streaming request
            async with self._create_aiohttp_session() as session:
                headers = dict(self.headers)
                # Add headers to request server-sent events
                headers['Accept'] = 'text/event-stream'
                
                # Prepare JSON-RPC request
                request_data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tasks/stream",
                    "params": task.to_dict()
                }
                
                # Try possible endpoints in order of preference
                endpoints_to_try = [
                    f"{self.endpoint_url}/tasks/stream",  # Standard tasks streaming endpoint
                    f"{self.endpoint_url}/a2a/tasks/stream",  # A2A-specific tasks streaming endpoint
                ]
                
                response = None
                last_error = None
                
                for endpoint in endpoints_to_try:
                    try:
                        logger.debug(f"Trying tasks streaming endpoint: {endpoint}")
                        
                        # Close previous response if we had one
                        if response:
                            await response.release()
                            
                        # Make the request
                        response = await session.post(
                            endpoint,
                            json=request_data,
                            headers=headers
                        )
                        
                        # If we succeed, break out of the loop
                        if response.status < 400:
                            break
                            
                        # Store error for retry
                        error_text = await response.text()
                        last_error = A2AConnectionError(f"HTTP error {response.status}: {error_text}")
                        
                    except Exception as e:
                        # Log the error and continue to next endpoint
                        logger.debug(f"Error with tasks streaming endpoint {endpoint}: {e}")
                        last_error = e
                
                # If we didn't get a successful response, raise the last error
                if not response or response.status >= 400:
                    if last_error:
                        raise last_error
                    else:
                        raise A2AConnectionError("All tasks streaming endpoints failed")
                
                # Process the streaming response
                try:
                    buffer = ""
                    
                    async for chunk in response.content.iter_chunks():
                        if not chunk:
                            continue
                            
                        # Decode chunk
                        chunk_text = chunk[0].decode('utf-8')
                        buffer += chunk_text
                        
                        # Process complete events (separated by double newlines)
                        while "\n\n" in buffer:
                            event, buffer = buffer.split("\n\n", 1)
                            
                            # Extract data fields and event type from event
                            event_type = "update"  # Default event type
                            event_data = None
                            
                            for line in event.split("\n"):
                                if line.startswith("event:"):
                                    event_type = line[6:].strip()
                                elif line.startswith("data:"):
                                    event_data = line[5:].strip()
                            
                            # Skip if no data
                            if not event_data:
                                continue
                                
                            # Try to parse the data as JSON
                            try:
                                data_obj = json.loads(event_data)
                                # Process with callback if provided
                                if chunk_callback:
                                    chunk_callback(data_obj)
                                
                                # Yield the data object
                                yield data_obj
                                
                                # Check if this is the final update
                                if event_type == "complete":
                                    return
                            except json.JSONDecodeError:
                                # Not JSON, create a text chunk
                                text_chunk = {
                                    "type": "text",
                                    "text": event_data
                                }
                                if chunk_callback:
                                    chunk_callback(text_chunk)
                                yield text_chunk
                
                finally:
                    # Ensure we close the response
                    if response:
                        await response.release()
        
        except Exception as e:
            # Fall back to non-streaming for other errors
            logger.warning(f"Error in task streaming, falling back to non-streaming: {e}")
            result = await self.send_task_async(task)
            
            # Create a single chunk with the complete result
            chunk = {
                "status": result.status.state.value if hasattr(result.status, "state") else "unknown",
                "artifacts": result.artifacts
            }
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(chunk)
            yield chunk