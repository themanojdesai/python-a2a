"""
Streaming client for real-time responses from A2A agents.

Provides asynchronous streaming capabilities for agents that support
the streaming API, with fallbacks for those that don't.
"""

import logging
import asyncio
import json
from typing import Dict, List, Any, Optional, Union, AsyncGenerator, Callable
import time

from .base import BaseA2AClient
from ..models import Message, TextContent, MessageRole
from ..models import Task, TaskStatus, TaskState
from ..exceptions import A2AConnectionError, A2AResponseError

logger = logging.getLogger(__name__)


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
                async with session.get(f"{self.url}/agent.json") as response:
                    if response.status == 200:
                        data = await response.json()
                        # Check capabilities
                        self._supports_streaming = (
                            isinstance(data, dict) and
                            isinstance(data.get("capabilities"), dict) and
                            data.get("capabilities", {}).get("streaming", False)
                        )
                    else:
                        # Try alternate endpoint
                        alternate_url = f"{self.url}/a2a/agent.json"
                        async with session.get(alternate_url) as alt_response:
                            if alt_response.status == 200:
                                data = await alt_response.json()
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
        chunk_callback: Optional[Callable[[str], None]] = None
    ) -> AsyncGenerator[str, None]:
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
                            
                            # Extract data fields from event
                            for line in event.split("\n"):
                                if line.startswith("data:"):
                                    data = line[5:].strip()
                                    
                                    # Try to parse as JSON
                                    try:
                                        data_obj = json.loads(data)
                                        # Extract text content
                                        text = self._extract_text_from_chunk(data_obj)
                                        if text:
                                            if chunk_callback:
                                                chunk_callback(text)
                                            yield text
                                    except json.JSONDecodeError:
                                        # Not JSON, yield raw data
                                        if chunk_callback:
                                            chunk_callback(data)
                                        yield data
        
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
        # Check if streaming is supported
        supports_streaming = await self.check_streaming_support()
        
        if not supports_streaming:
            # Fall back to non-streaming if not supported
            result = await self.send_task(task)
            
            # Create a single chunk with the complete result
            chunk = {
                "status": result.status.state,
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
                "status": result.status.state,
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
                "status": result.status.state,
                "artifacts": result.artifacts
            }
                
            # Yield the entire response as one chunk
            if chunk_callback:
                chunk_callback(chunk)
            yield chunk
    
    async def _process_stream(self, response, chunk_callback):
        """Process a streaming response."""
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
                
                # Extract data fields from event
                for line in event.split("\n"):
                    if line.startswith("data:"):
                        data = line[5:].strip()
                        
                        # Try to parse as JSON
                        try:
                            data_obj = json.loads(data)
                            if chunk_callback:
                                chunk_callback(data_obj)
                            yield data_obj
                        except json.JSONDecodeError:
                            # Not JSON, yield raw data as text chunk
                            text_chunk = {"type": "text", "text": data}
                            if chunk_callback:
                                chunk_callback(text_chunk)
                            yield text_chunk
    
    def _extract_text_from_chunk(self, chunk):
        """Extract text content from a response chunk."""
        # Handle different types of chunks
        if isinstance(chunk, str):
            return chunk
        elif isinstance(chunk, dict):
            # Check for standard patterns
            if "text" in chunk:
                return chunk["text"]
            elif "content" in chunk and isinstance(chunk["content"], dict) and "text" in chunk["content"]:
                return chunk["content"]["text"]
            elif "content" in chunk and isinstance(chunk["content"], list):
                for item in chunk["content"]:
                    if isinstance(item, dict) and item.get("type") == "text":
                        return item.get("text", "")
            elif "artifacts" in chunk and isinstance(chunk["artifacts"], list):
                for artifact in chunk["artifacts"]:
                    if isinstance(artifact, dict) and "parts" in artifact:
                        for part in artifact["parts"]:
                            if isinstance(part, dict) and part.get("type") == "text":
                                return part.get("text", "")
        
        # Return empty string for unhandled formats
        return ""