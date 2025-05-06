"""
Base client for interacting with A2A-compatible agents.
"""

from abc import ABC, abstractmethod
from typing import Optional, AsyncGenerator, Any, Union, Dict, Callable

from ..models.message import Message
from ..models.conversation import Conversation
from ..models.task import Task


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
            
        Note:
            This is a default implementation that should be overridden by
            client implementations that support streaming.
        """
        # Default implementation just yields the entire response as one chunk
        response = self.send_message(message)
        
        # Get text from response
        if hasattr(response.content, "text"):
            result = response.content.text
        else:
            result = str(response.content)
            
        # Call the callback if provided
        if chunk_callback:
            chunk_callback(result)
            
        # Yield the entire response as one chunk
        yield result
        
    async def send_message_async(self, message: Message) -> Message:
        """
        Send a message to an A2A-compatible agent asynchronously.
        
        Default implementation that wraps the synchronous send_message
        in an asynchronous interface.
        
        Args:
            message: The A2A message to send
            
        Returns:
            The agent's response
        """
        # Default implementation runs sync version in executor
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_message, message)
    
    async def send_conversation_async(self, conversation: Conversation) -> Conversation:
        """
        Send a conversation to an A2A-compatible agent asynchronously.
        
        Default implementation that wraps the synchronous send_conversation
        in an asynchronous interface.
        
        Args:
            conversation: The conversation to send
            
        Returns:
            The updated conversation with the agent's response
        """
        # Default implementation runs sync version in executor
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.send_conversation, conversation)
    
    async def stream_task(
        self, 
        task: Task,
        chunk_callback: Optional[Callable[[Dict], None]] = None
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream the execution of a task.
        
        Default implementation that doesn't support actual streaming,
        just returns the final result.
        
        Args:
            task: The task to execute
            chunk_callback: Optional callback function for each chunk
            
        Yields:
            Task status and result chunks
        """
        # Create a complete task result
        result = await self.send_task_async(task)
        
        # Create a single chunk with the complete result
        chunk = {
            "status": result.status.state.value if hasattr(result.status, "state") else "unknown",
            "artifacts": result.artifacts
        }
            
        # Call the callback if provided
        if chunk_callback:
            chunk_callback(chunk)
            
        # Yield the entire response as one chunk
        yield chunk
    
    async def send_task_async(self, task: Task) -> Task:
        """
        Send a task to an A2A-compatible agent asynchronously.
        
        Default implementation for task handling. Should be overridden
        by implementations that support the tasks API.
        
        Args:
            task: The task to send
            
        Returns:
            The updated task with the agent's response
        """
        from ..models.task import TaskStatus, TaskState
        from ..models.message import MessageRole, TextContent
        
        # Default implementation extracts message from task and uses send_message
        message_data = task.message or {}
        content = message_data.get("content", {})
        
        if isinstance(content, dict) and "text" in content:
            text = content["text"]
        elif hasattr(content, '__str__'):
            text = str(content)
        else:
            text = repr(content) if content else ""
        
        if not text:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message="Please provide a text query."
            )
            return task
        
        try:
            # Create a message
            message = Message(
                content=TextContent(text=text),
                role=MessageRole.USER
            )
            
            # Process with send_message
            response = await self.send_message_async(message)
            
            # Extract text
            if hasattr(response.content, "text"):
                result = response.content.text
            else:
                result = str(response.content)
            
            # Create response
            task.artifacts = [{
                "parts": [{"type": "text", "text": result}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        except Exception as e:
            # Handle error
            import logging
            logging.exception("Error processing task")
            task.status = TaskStatus(
                state=TaskState.FAILED,
                message=f"Error: {str(e)}"
            )
        
        return task