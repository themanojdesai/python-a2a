"""
Streaming client for real-time responses from A2A agents.

Provides asynchronous streaming capabilities for agents that support
the streaming API, with fallbacks for those that don't.
"""

import logging
import asyncio
import json
import time
import re
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Callable, Tuple

from .base import BaseA2AClient
from .http import A2AClient
from ..models import Message, TextContent, MessageRole
from ..models import Task, TaskStatus, TaskState
from ..models import Conversation
from ..exceptions import A2AConnectionError, A2AResponseError, A2AStreamingError

logger = logging.getLogger(__name__)


class StreamingChunk:
    """
    A structured representation of a streaming chunk from an A2A agent.
    
    Attributes:
        content: The content of the chunk
        is_last: Whether this is the last chunk
        append: Whether this chunk should be appended to previous chunks
        index: The sequence index of this chunk (if provided)
        event_type: The type of event (default: 'chunk')
    """
    
    def __init__(
        self, 
        content: Any,
        is_last: bool = False,
        append: bool = True,
        index: Optional[int] = None,
        event_type: str = 'chunk'
    ):
        """
        Initialize a streaming chunk.
        
        Args:
            content: The content of the chunk
            is_last: Whether this is the last chunk
            append: Whether this chunk should be appended to previous chunks
            index: The sequence index of this chunk (if provided)
            event_type: The type of event (default: 'chunk')
        """
        self.content = content
        self.is_last = is_last
        self.append = append
        self.index = index
        self.event_type = event_type
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StreamingChunk':
        """
        Create a StreamingChunk from a dictionary.
        
        Args:
            data: Dictionary representation of a streaming chunk
            
        Returns:
            A StreamingChunk object
        """
        content = data.get('content', '')
        
        # Look for text content in different formats
        if isinstance(content, dict) and 'text' in content:
            content = content['text']
        elif isinstance(content, dict) and 'parts' in content and isinstance(content['parts'], list):
            # Extract text from parts array format
            for part in content['parts']:
                if isinstance(part, dict) and part.get('type') == 'text' and 'text' in part:
                    content = part['text']
                    break
        
        return cls(
            content=content,
            is_last=data.get('lastChunk', False),
            append=data.get('append', True),
            index=data.get('index'),
            event_type=data.get('event', 'chunk')
        )


class StreamingClient(BaseA2AClient):
    """
    Client for streaming responses from A2A-compatible agents.
    
    This client enhances the standard A2A client with streaming response
    capabilities, allowing for real-time processing of agent responses.
    """
    
    def __init__(
        self, 
        url: str, 
        headers: Optional[Dict[str, str]] = None,
        timeout: int = 30
    ):
        """
        Initialize a streaming client.
        
        Args:
            url: Base URL of the A2A agent
            headers: Optional HTTP headers to include in requests
            timeout: Request timeout in seconds
        """
        self.url = url.rstrip('/')
        self.headers = headers or {}
        self.timeout = timeout
        
        # Ensure content type is set for JSON
        if 'Content-Type' not in self.headers:
            self.headers['Content-Type'] = 'application/json'
        
        # Check if SSE support is available
        try:
            import aiohttp
            self._has_aiohttp = True
        except ImportError:
            self._has_aiohttp = False
            logger.warning(
                "aiohttp not installed. Streaming will use polling instead. "
                "Install aiohttp for better streaming support."
            )
        
        # Flag for checking if the agent supports streaming
        self._supports_streaming = None
        
    async def check_streaming_support(self) -> bool:
        """
        Check if the agent supports streaming.
        
        Returns:
            True if streaming is supported, False otherwise
        """
        if self._supports_streaming is not None:
            return self._supports_streaming
        
        # Try to fetch agent metadata to check for streaming capability
        try:
            # Check if aiohttp is available
            if not self._has_aiohttp:
                self._supports_streaming = False
                return False
                
            # Import to avoid circular imports
            from ..models import AgentCard
            
            # Try to load agent card
            async with self._create_session() as session:
                # Create headers specifically for JSON content negotiation
                json_headers = {"Accept": "application/json"}
                
                # First attempt with primary endpoint
                async with session.get(
                    f"{self.url}/agent.json", 
                    headers=json_headers
                ) as response:
                    if response.status == 200:
                        # Check content type to ensure we got JSON
                        content_type = response.headers.get('Content-Type', '')
                        if 'application/json' in content_type:
                            # Parse JSON directly
                            data = await response.json()
                        else:
                            # Attempt to extract JSON from non-JSON response
                            try:
                                text = await response.text()
                                data = self._extract_json_from_response(text)
                            except Exception as e:
                                logger.warning(f"Failed to extract JSON from response: {e}")
                                data = {}
                        
                        # Check capabilities
                        self._supports_streaming = (
                            isinstance(data, dict) and
                            isinstance(data.get("capabilities"), dict) and
                            data.get("capabilities", {}).get("streaming", False)
                        )
                    else:
                        # Try alternate endpoint
                        alternate_url = f"{self.url}/a2a/agent.json"
                        async with session.get(
                            alternate_url, 
                            headers=json_headers
                        ) as alt_response:
                            if alt_response.status == 200:
                                # Check content type to ensure we got JSON
                                content_type = alt_response.headers.get('Content-Type', '')
                                if 'application/json' in content_type:
                                    # Parse JSON directly
                                    data = await alt_response.json()
                                else:
                                    # Attempt to extract JSON from non-JSON response
                                    try:
                                        text = await alt_response.text()
                                        data = self._extract_json_from_response(text)
                                    except Exception as e:
                                        logger.warning(f"Failed to extract JSON from response: {e}")
                                        data = {}
                                
                                # Check capabilities
                                self._supports_streaming = (
                                    isinstance(data, dict) and
                                    isinstance(data.get("capabilities"), dict) and
                                    data.get("capabilities", {}).get("streaming", False)
                                )
                            else:
                                self._supports_streaming = False
                                
        except Exception as e:
            logger.warning(f"Error checking streaming support: {e}")
            self._supports_streaming = False
        
        return self._supports_streaming
    
    def _create_session(self):
        """Create an aiohttp session."""
        if not self._has_aiohttp:
            raise ImportError(
                "aiohttp is required for streaming. "
                "Install it with 'pip install aiohttp'."
            )
        
        import aiohttp
        return aiohttp.ClientSession(
            headers=self.headers,
            timeout=aiohttp.ClientTimeout(total=self.timeout)
        )
    
    def send_message(self, message: Message) -> Message:
        """
        Send a message to an A2A-compatible agent (synchronous).
        
        This method overrides the BaseA2AClient.send_message method
        to provide backward compatibility.
        
        Args:
            message: The A2A message to send
            
        Returns:
            The agent's response as an A2A message
        """
        # For synchronous calls, use asyncio.run on the async version
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in this thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_message_async(message))
        
    def send_conversation(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to an A2A-compatible agent (synchronous).
        
        This method overrides the BaseA2AClient.send_conversation method
        to provide backward compatibility.
        
        Args:
            conversation: The conversation to send
            
        Returns:
            The updated conversation with the agent's response
        """
        # Create a synchronous version using asyncio
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in this thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        return loop.run_until_complete(self.send_conversation_async(conversation))
        
    async def send_conversation_async(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to an A2A-compatible agent (asynchronous).
        
        Args:
            conversation: The conversation to send
            
        Returns:
            The updated conversation with the agent's response
        """
        # For simplicity, extract the last message and send it
        if not conversation.messages:
            raise ValueError("Cannot send an empty conversation")
        
        # Get last message (typically from the user)
        last_message = conversation.messages[-1]
        
        # Send the message
        response = await self.send_message_async(last_message)
        
        # Add the response to the conversation
        conversation.add_message(response)
        
        return conversation
    
    async def send_message_async(self, message: Message) -> Message:
        """
        Send a message to an A2A-compatible agent (asynchronous).
        
        Args:
            message: The A2A message to send
            
        Returns:
            The agent's response as an A2A message
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
        """
        try:
            if not self._has_aiohttp:
                # Fall back to synchronous requests if aiohttp not available
                import requests
                response = requests.post(
                    self.url,
                    json=message.to_dict(),
                    headers=self.headers,
                    timeout=self.timeout
                )
                response.raise_for_status()
                return Message.from_dict(response.json())
            
            # Asynchronous request with aiohttp
            async with self._create_session() as session:
                async with session.post(
                    self.url,
                    json=message.to_dict()
                ) as response:
                    # Handle HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise A2AConnectionError(
                            f"HTTP error {response.status}: {error_text}"
                        )
                    
                    # Parse the response
                    try:
                        data = await response.json()
                        return Message.from_dict(data)
                    except ValueError as e:
                        raise A2AResponseError(f"Invalid response from agent: {str(e)}")
                    
        except Exception as e:
            if isinstance(e, (A2AConnectionError, A2AResponseError)):
                raise
            
            # Create an error message as response
            return Message(
                content=TextContent(text=f"Error: {str(e)}"),
                role=MessageRole.SYSTEM,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
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
        
        if not self._has_aiohttp:
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
            async with self._create_session() as session:
                headers = dict(self.headers)
                # Add headers to request server-sent events
                headers['Accept'] = 'text/event-stream'
                
                async with session.post(
                    f"{self.url}/stream",
                    json=message.to_dict(),
                    headers=headers
                ) as response:
                    # Handle HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise A2AConnectionError(
                            f"HTTP error {response.status}: {error_text}"
                        )
                    
                    # Process the streaming response
                    async for chunk in self._process_stream(response, chunk_callback):
                        yield chunk
        
        except Exception as e:
            if isinstance(e, (A2AConnectionError, A2AResponseError)):
                raise
            
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
    
    async def create_task(self, message: Union[str, Message]) -> Task:
        """
        Create a task from a message.
        
        Args:
            message: Text message or Message object
            
        Returns:
            The created task
        """
        # Convert to Message if needed
        if isinstance(message, str):
            message_obj = Message(
                content=TextContent(text=message),
                role=MessageRole.USER
            )
        else:
            message_obj = message
        
        # Create a task
        task = Task(
            id=str(id(message_obj)),  # Simple unique ID
            message=message_obj.to_dict()
        )
        
        return task
    
    async def send_task(self, task: Task) -> Task:
        """
        Send a task to an A2A-compatible agent.
        
        Args:
            task: The task to send
            
        Returns:
            The updated task with the agent's response
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
        """
        try:
            if not self._has_aiohttp:
                # Fall back to synchronous requests if aiohttp not available
                import requests
                
                # Try POST to /tasks/send endpoint
                try:
                    response = requests.post(
                        f"{self.url}/tasks/send",
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tasks/send",
                            "params": task.to_dict()
                        },
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    result = response.json().get("result", {})
                    return Task.from_dict(result)
                except Exception:
                    # Try alternate endpoint
                    response = requests.post(
                        f"{self.url}/a2a/tasks/send",
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tasks/send",
                            "params": task.to_dict()
                        },
                        headers=self.headers,
                        timeout=self.timeout
                    )
                    response.raise_for_status()
                    result = response.json().get("result", {})
                    return Task.from_dict(result)
            
            # Asynchronous request with aiohttp
            async with self._create_session() as session:
                # Try POST to /tasks/send endpoint
                try:
                    async with session.post(
                        f"{self.url}/tasks/send",
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tasks/send",
                            "params": task.to_dict()
                        }
                    ) as response:
                        # Handle HTTP errors
                        if response.status >= 400:
                            # Try alternate endpoint
                            raise Exception("First endpoint failed")
                        
                        # Parse the response
                        data = await response.json()
                        result = data.get("result", {})
                        return Task.from_dict(result)
                        
                except Exception:
                    # Try alternate endpoint
                    async with session.post(
                        f"{self.url}/a2a/tasks/send",
                        json={
                            "jsonrpc": "2.0",
                            "id": 1,
                            "method": "tasks/send",
                            "params": task.to_dict()
                        }
                    ) as response:
                        # Handle HTTP errors
                        if response.status >= 400:
                            error_text = await response.text()
                            raise A2AConnectionError(
                                f"HTTP error {response.status}: {error_text}"
                            )
                        
                        # Parse the response
                        data = await response.json()
                        result = data.get("result", {})
                        return Task.from_dict(result)
                    
        except Exception as e:
            if isinstance(e, (A2AConnectionError, A2AResponseError)):
                raise
            
            # Create an error task as response
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"error": str(e)}
            )
            return task
    
    async def tasks_send_subscribe(self, task: Task) -> AsyncGenerator[Task, None]:
        """
        Send a task and subscribe to streaming updates using tasks/sendSubscribe.
        
        Args:
            task: The task to send and subscribe to
            
        Yields:
            Task updates as they arrive
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
            A2AStreamingError: If streaming is not supported by the agent
        """
        if not self._has_aiohttp:
            raise A2AStreamingError(
                "aiohttp is required for tasks_send_subscribe. "
                "Install it with 'pip install aiohttp'."
            )
        
        # Check if streaming is supported
        supports_streaming = await self.check_streaming_support()
        if not supports_streaming:
            # For backward compatibility, fall back to send_task
            task_result = await self.send_task(task)
            yield task_result
            return
        
        # Real streaming implementation with aiohttp
        try:
            # Set up streaming request
            async with self._create_session() as session:
                headers = dict(self.headers)
                # Add headers to request server-sent events
                headers['Accept'] = 'text/event-stream'
                
                # Use the direct task instead of JsonRPC format for better compatibility
                request_data = task.to_dict()
                
                # Add debug logging
                logger.debug(f"Sending task streaming request with task ID: {task.id}")
                
                # Store the endpoint URLs to try
                endpoints_to_try = []
                
                # If a custom stream_task_url is set, use it first
                if hasattr(self, '_stream_task_url') and self._stream_task_url:
                    logger.debug(f"Using custom task streaming URL: {self._stream_task_url}")
                    endpoints_to_try.append(self._stream_task_url)
                
                # Then try standard endpoints
                endpoints_to_try.extend([
                    f"{self.url}/a2a/tasks/stream",  # Try A2A-specific endpoint first
                    f"{self.url}/tasks/stream",      # Then standard tasks endpoint
                    f"{self.url}/stream"             # Finally fallback to regular stream endpoint
                ])
                
                response = None
                last_error = None
                
                # Try each endpoint in order
                for endpoint_url in endpoints_to_try:
                    try:
                        logger.debug(f"Trying task streaming endpoint: {endpoint_url}")
                        
                        # Close previous response if we had one
                        if response:
                            await response.release()
                            
                        # Send the request to this endpoint
                        response = await session.post(
                            endpoint_url,
                            json=request_data,
                            headers=headers
                        )
                        
                        # Check for success
                        if response.status < 400:
                            logger.debug(f"Successfully connected to endpoint: {endpoint_url}")
                            break
                            
                        # Store error for retry
                        error_text = await response.text()
                        last_error = A2AConnectionError(f"HTTP error {response.status}: {error_text}")
                        
                    except Exception as req_error:
                        # Log the error and continue to next endpoint
                        logger.debug(f"Error with endpoint {endpoint_url}: {req_error}")
                        last_error = req_error
                
                # If we didn't get a successful response, raise the last error
                if not response or response.status >= 400:
                    if last_error:
                        raise last_error
                    else:
                        raise A2AConnectionError("All task streaming endpoints failed")
                
                try:
                    # Process the streaming response
                    buffer = ""
                    current_task = task
                    
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
                            event_id = None
                            
                            for line in event.split("\n"):
                                if line.startswith("event:"):
                                    event_type = line[6:].strip()
                                elif line.startswith("data:"):
                                    event_data = line[5:].strip()
                                elif line.startswith("id:"):
                                    event_id = line[3:].strip()
                            
                            # Skip if no data
                            if not event_data:
                                continue
                                
                            # Try to parse the data as JSON
                            try:
                                data_obj = json.loads(event_data)
                                
                                # Handle task updates
                                if event_type == "update" or event_type == "complete":
                                    if isinstance(data_obj, dict):
                                        # Parse as a Task
                                        current_task = Task.from_dict(data_obj)
                                        yield current_task
                                        
                                        # If this is a complete event, we're done
                                        if event_type == "complete" or current_task.status.state in [
                                            TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED
                                        ]:
                                            return
                                
                                # Handle other event types
                                elif event_type == "error":
                                    error_msg = data_obj.get("error", "Unknown error")
                                    raise A2AStreamingError(f"Stream error: {error_msg}")
                                    
                                # Handle raw data (artifact updates, etc.)
                                else:
                                    # Update the current task with the new data
                                    # This is a simplification; real updates should merge properly
                                    if "artifacts" in data_obj:
                                        current_task.artifacts = data_obj["artifacts"]
                                    
                                    if "status" in data_obj:
                                        current_task.status = TaskStatus.from_dict(data_obj["status"])
                                    
                                    yield current_task
                                    
                            except json.JSONDecodeError:
                                # Not JSON, create a text update
                                logger.warning(f"Received non-JSON data in stream: {event_data[:50]}...")
                                # Create a text artifact for backward compatibility
                                current_task.artifacts.append({
                                    "parts": [{"type": "text", "text": event_data}]
                                })
                                yield current_task
                
                finally:
                    # Ensure we close the response
                    if response:
                        await response.release()
        
        except Exception as e:
            if isinstance(e, (A2AConnectionError, A2AResponseError, A2AStreamingError)):
                raise
            
            # For any other error, yield a complete task with the error
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message={"error": str(e)}
            )
            yield task
    
    async def tasks_resubscribe(self, task_id: str, session_id: Optional[str] = None) -> AsyncGenerator[Task, None]:
        """
        Resubscribe to an existing task's updates.
        
        Args:
            task_id: The ID of the task to resubscribe to
            session_id: Optional session ID (if known)
            
        Yields:
            Task updates as they arrive
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
            A2AStreamingError: If streaming is not supported by the agent
        """
        if not self._has_aiohttp:
            raise A2AStreamingError(
                "aiohttp is required for tasks_resubscribe. "
                "Install it with 'pip install aiohttp'."
            )
        
        # Check if streaming is supported
        supports_streaming = await self.check_streaming_support()
        if not supports_streaming:
            raise A2AStreamingError("Agent does not support streaming")
        
        # Real streaming implementation with aiohttp
        try:
            # Set up streaming request
            async with self._create_session() as session:
                headers = dict(self.headers)
                # Add headers to request server-sent events
                headers['Accept'] = 'text/event-stream'
                
                # Create JsonRPC request
                request_data = {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tasks/resubscribe",
                    "params": {
                        "id": task_id
                    }
                }
                
                # Add session_id if provided
                if session_id:
                    request_data["params"]["sessionId"] = session_id
                
                # Try primary endpoint first
                endpoint_url = f"{self.url}/tasks/stream"
                response = None
                try:
                    response = await session.post(
                        endpoint_url,
                        json=request_data,
                        headers=headers
                    )
                    
                    # Check for HTTP errors
                    if response.status >= 400:
                        # Try alternate endpoint
                        logger.debug(f"Primary endpoint failed with status {response.status}, trying alternate")
                        if response:
                            await response.release()
                        endpoint_url = f"{self.url}/a2a/tasks/stream"
                        response = await session.post(
                            endpoint_url,
                            json=request_data,
                            headers=headers
                        )
                        
                        # Check for HTTP errors again
                        if response.status >= 400:
                            error_text = await response.text()
                            raise A2AConnectionError(
                                f"HTTP error {response.status}: {error_text}"
                            )
                except Exception as req_error:
                    # Try alternate endpoint if first fails
                    logger.debug(f"Primary endpoint failed: {req_error}, trying alternate")
                    if response:
                        await response.release()
                    endpoint_url = f"{self.url}/a2a/tasks/stream"
                    response = await session.post(
                        endpoint_url,
                        json=request_data,
                        headers=headers
                    )
                    
                    # Check for HTTP errors
                    if response.status >= 400:
                        error_text = await response.text()
                        raise A2AConnectionError(
                            f"HTTP error {response.status}: {error_text}"
                        )
                
                try:
                    # Process the streaming response
                    buffer = ""
                    current_task = None
                    
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
                            event_id = None
                            
                            for line in event.split("\n"):
                                if line.startswith("event:"):
                                    event_type = line[6:].strip()
                                elif line.startswith("data:"):
                                    event_data = line[5:].strip()
                                elif line.startswith("id:"):
                                    event_id = line[3:].strip()
                            
                            # Skip if no data
                            if not event_data:
                                continue
                                
                            # Try to parse the data as JSON
                            try:
                                data_obj = json.loads(event_data)
                                
                                # Handle task updates
                                if event_type == "update" or event_type == "complete":
                                    if isinstance(data_obj, dict):
                                        # Parse as a Task
                                        current_task = Task.from_dict(data_obj)
                                        yield current_task
                                        
                                        # If this is a complete event, we're done
                                        if event_type == "complete" or (current_task and current_task.status.state in [
                                            TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED
                                        ]):
                                            return
                                
                                # Handle other event types
                                elif event_type == "error":
                                    error_msg = data_obj.get("error", "Unknown error")
                                    raise A2AStreamingError(f"Stream error: {error_msg}")
                                    
                                # Handle raw data (artifact updates, etc.)
                                else:
                                    # Initialize a task if we don't have one yet
                                    if not current_task:
                                        current_task = Task(
                                            id=task_id,
                                            session_id=session_id
                                        )
                                    
                                    # Update the current task with the new data
                                    if "artifacts" in data_obj:
                                        current_task.artifacts = data_obj["artifacts"]
                                    
                                    if "status" in data_obj:
                                        current_task.status = TaskStatus.from_dict(data_obj["status"])
                                    
                                    yield current_task
                                    
                            except json.JSONDecodeError:
                                # Not JSON, create a text update
                                logger.warning(f"Received non-JSON data in stream: {event_data[:50]}...")
                                
                                # Initialize a task if we don't have one yet
                                if not current_task:
                                    current_task = Task(
                                        id=task_id,
                                        session_id=session_id
                                    )
                                
                                # Create a text artifact for backward compatibility
                                current_task.artifacts.append({
                                    "parts": [{"type": "text", "text": event_data}]
                                })
                                yield current_task
                
                finally:
                    # Ensure we close the response
                    if response:
                        await response.release()
        
        except Exception as e:
            if isinstance(e, (A2AConnectionError, A2AResponseError, A2AStreamingError)):
                raise
            
            # For any other error, yield a task with the error
            error_task = Task(
                id=task_id,
                session_id=session_id,
                status=TaskStatus(
                    state=TaskState.FAILED,
                    message={"error": str(e)}
                )
            )
            yield error_task
    
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
            
        Raises:
            A2AConnectionError: If connection to the agent fails
            A2AResponseError: If the agent returns an invalid response
        """
        # For backward compatibility, first try the enhanced tasks_send_subscribe method
        try:
            async for task_update in self.tasks_send_subscribe(task):
                # Extract status and artifacts for backward compatibility
                chunk = {
                    "status": task_update.status.state.value,
                    "artifacts": task_update.artifacts
                }
                
                # Call the callback if provided
                if chunk_callback:
                    chunk_callback(chunk)
                
                yield chunk
                
                # If the task is complete, we're done
                if task_update.status.state in [TaskState.COMPLETED, TaskState.FAILED, TaskState.CANCELED]:
                    return
            
            # If we reach here, we've completed the task
            return
            
        except (A2AStreamingError, ImportError) as e:
            # Fall back to legacy implementation
            logger.debug(f"Enhanced streaming not supported or failed: {e}. Falling back to legacy implementation.")
            pass
        
        # Legacy implementation starts here
        # Check if streaming is supported
        supports_streaming = await self.check_streaming_support()
        
        if not supports_streaming:
            # Fall back to non-streaming if not supported
            result = await self.send_task(task)
            
            # Create a single chunk with the complete result
            chunk = {
                "status": result.status.state.value,
                "artifacts": result.artifacts
            }
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(chunk)
            yield chunk
            return
        
        if not self._has_aiohttp:
            # Fall back to non-streaming if aiohttp not available
            result = await self.send_task(task)
            
            # Create a single chunk with the complete result
            chunk = {
                "status": result.status.state.value,
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
            async with self._create_session() as session:
                headers = dict(self.headers)
                # Add headers to request server-sent events
                headers['Accept'] = 'text/event-stream'
                
                async with session.post(
                    f"{self.url}/tasks/stream",
                    json={
                        "jsonrpc": "2.0",
                        "id": 1,
                        "method": "tasks/stream",
                        "params": task.to_dict()
                    },
                    headers=headers
                ) as response:
                    # Handle HTTP errors
                    if response.status >= 400:
                        # Try alternate endpoint
                        try:
                            async with session.post(
                                f"{self.url}/a2a/tasks/stream",
                                json={
                                    "jsonrpc": "2.0",
                                    "id": 1,
                                    "method": "tasks/stream",
                                    "params": task.to_dict()
                                },
                                headers=headers
                            ) as alt_response:
                                # Handle HTTP errors
                                if alt_response.status >= 400:
                                    error_text = await alt_response.text()
                                    raise A2AConnectionError(
                                        f"HTTP error {alt_response.status}: {error_text}"
                                    )
                                
                                # Process the streaming response
                                async for chunk in self._process_stream(alt_response, chunk_callback):
                                    yield chunk
                                    
                        except Exception:
                            error_text = await response.text()
                            raise A2AConnectionError(
                                f"HTTP error {response.status}: {error_text}"
                            )
                    else:
                        # Process the streaming response from original endpoint
                        async for chunk in self._process_stream(response, chunk_callback):
                            yield chunk
        
        except Exception as e:
            if isinstance(e, (A2AConnectionError, A2AResponseError)):
                raise
            
            # Fall back to non-streaming for other errors
            logger.warning(f"Error in streaming, falling back to non-streaming: {e}")
            result = await self.send_task(task)
            
            # Create a single chunk with the complete result
            chunk = {
                "status": result.status.state.value,
                "artifacts": result.artifacts
            }
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(chunk)
            yield chunk
    
    async def _process_stream(self, response, chunk_callback=None):
        """Process a streaming response using enhanced parsing."""
        try:
            buffer = ""
            last_event_type = None
            chunks_received = 0
            bytes_received = 0
            
            # Debug logging
            logger.debug(f"Starting to process streaming response")
            logger.debug(f"Response headers: {response.headers}")
            
            async for chunk in response.content.iter_chunks():
                if not chunk:
                    continue
                
                # Update metrics
                chunks_received += 1
                bytes_received += len(chunk[0])
                
                # Decode chunk
                chunk_text = chunk[0].decode('utf-8')
                buffer += chunk_text
                
                # Debug every 10 chunks
                if chunks_received % 10 == 0:
                    logger.debug(f"Processed {chunks_received} chunks, {bytes_received} bytes")
                    
                # Detailed debug for first few chunks
                if chunks_received <= 3:
                    logger.debug(f"Raw chunk {chunks_received}: {chunk_text}")
                
                # Process complete events (separated by double newlines)
                while "\n\n" in buffer:
                    event, buffer = buffer.split("\n\n", 1)
                    
                    # Skip comments (lines starting with colon)
                    if event.startswith(':'):
                        logger.debug(f"Skipping SSE comment: {event}")
                        continue
                    
                    # Extract fields from the event
                    event_type = None
                    event_data = None
                    event_id = None
                    retry_time = None
                    
                    for line in event.split("\n"):
                        line = line.strip()
                        if not line:
                            continue
                            
                        if line.startswith("event:"):
                            event_type = line[6:].strip()
                            logger.debug(f"Found event type: {event_type}")
                        elif line.startswith("data:"):
                            event_data = line[5:].strip()
                            logger.debug(f"Found event data: {event_data[:50]}...")
                        elif line.startswith("id:"):
                            event_id = line[3:].strip()
                            logger.debug(f"Found event ID: {event_id}")
                        elif line.startswith("retry:"):
                            try:
                                retry_time = int(line[6:].strip())
                                logger.debug(f"Found retry time: {retry_time}")
                            except ValueError:
                                pass
                    
                    # Default to "message" event type if none provided
                    if not event_type:
                        event_type = last_event_type or "message"
                    
                    last_event_type = event_type
                    
                    # Handle connected event
                    if event_type == "connected":
                        logger.info("Received connected event from server")
                        continue
                    
                    # Handle error events
                    if event_type == "error":
                        if event_data:
                            try:
                                error_data = json.loads(event_data)
                                logger.error(f"Received error event: {error_data}")
                                # Raise exception to be caught by the outer handler
                                raise A2AStreamingError(error_data.get("error", "Unknown streaming error"))
                            except json.JSONDecodeError:
                                # Bad JSON in error, use raw text
                                logger.error(f"Received malformed error event: {event_data}")
                                raise A2AStreamingError(f"Stream error: {event_data}")
                        continue
                    
                    # Skip if no data
                    if not event_data:
                        logger.warning("Empty event data, skipping")
                        continue
                    
                    # Try to parse as JSON
                    try:
                        data_obj = json.loads(event_data)
                        logger.debug(f"Successfully parsed JSON data: {str(data_obj)[:50]}...")
                        
                        # Handle structured events with the new StreamingChunk class
                        if isinstance(data_obj, dict):
                            streaming_chunk = StreamingChunk.from_dict(data_obj)
                            
                            # If lastChunk is set, this is the final chunk
                            is_last = streaming_chunk.is_last
                            
                            # Process with callback if provided
                            if chunk_callback:
                                chunk_callback(data_obj)
                            
                            # Yield the chunk
                            yield data_obj
                            
                            # If this is the last chunk, we're done
                            if is_last:
                                logger.info("Received last chunk, ending stream")
                                return
                        else:
                            # Non-dict JSON, pass through
                            logger.debug(f"Non-dict JSON data: {str(data_obj)[:50]}...")
                            if chunk_callback:
                                chunk_callback(data_obj)
                            yield data_obj
                    except json.JSONDecodeError:
                        # Not JSON, create a text chunk
                        logger.warning(f"Failed to parse JSON, treating as text: {event_data[:50]}...")
                        text_chunk = {"type": "text", "text": event_data}
                        if chunk_callback:
                            chunk_callback(text_chunk)
                        yield text_chunk
            
            # Log completion
            logger.info(f"Stream completed, processed {chunks_received} raw chunks")
        
        except Exception as e:
            logger.error(f"Error processing streaming response: {e}")
            # Include stack trace for debugging
            logger.debug(traceback.format_exc())
            raise
    
    def _extract_json_from_response(self, text):
        """
        Extract JSON data from a response that might be HTML or contain embedded JSON.
        
        Args:
            text: The response text to parse
            
        Returns:
            Extracted JSON data as dictionary
        """
        # Check if the text is pure JSON first
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from HTML (look for JSON in a <pre> tag or <script> tag)
        import re
        
        # Pattern 1: Look for content in <pre> tags (common in HTML API responses)
        pre_match = re.search(r'<pre[^>]*>(.*?)</pre>', text, re.DOTALL)
        if pre_match:
            try:
                return json.loads(pre_match.group(1))
            except json.JSONDecodeError:
                pass
                
        # Pattern 2: Look for a JSON object with capabilities field
        json_match = re.search(r'({[^{}]*"capabilities"[^{}]*})', text)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
                
        # Pattern 3: Look for application/json content
        json_content_match = re.search(r'<div[^>]*>({\s*"[^"]*"\s*:.*?})</div>', text, re.DOTALL)
        if json_content_match:
            try:
                return json.loads(json_content_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Fallback: Return empty dict if we couldn't extract valid JSON
        return {}
    
    def _extract_text_from_chunk(self, chunk):
        """Extract text content from a response chunk."""
        # Handle different types of chunks
        if isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, dict):
            # First check for the new structure
            if "content" in chunk:
                # Content might be a string or object
                content = chunk["content"]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict) and "text" in content:
                    return content["text"]
                elif isinstance(content, list):
                    for item in content:
                        if isinstance(item, dict) and item.get("type") == "text":
                            return item.get("text", "")
            
            # Check for direct text field
            if "text" in chunk:
                return chunk["text"]
            
            # Check for artifacts which might contain text
            if "artifacts" in chunk and isinstance(chunk["artifacts"], list):
                for artifact in chunk["artifacts"]:
                    if isinstance(artifact, dict) and "parts" in artifact:
                        for part in artifact["parts"]:
                            if isinstance(part, dict) and part.get("type") == "text":
                                return part.get("text", "")
        
        # Return empty string for unhandled formats
        return ""