"""
MCP Transport implementations.

This module provides transport mechanisms for the Model Context Protocol (MCP).
All transports carry JSON-RPC 2.0 messages as specified in the MCP protocol.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, AsyncIterator, List
import httpx

logger = logging.getLogger(__name__)


class Transport(ABC):
    """Abstract base class for MCP transports."""
    
    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to the MCP server."""
        pass
    
    @abstractmethod
    async def disconnect(self) -> None:
        """Close connection to the MCP server."""
        pass
    
    @abstractmethod
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send a JSON-RPC request and wait for response.
        
        Args:
            request: JSON-RPC request object
            
        Returns:
            JSON-RPC response object
            
        Raises:
            Exception: If request fails
        """
        pass
    
    @abstractmethod
    async def send_notification(self, notification: Dict[str, Any]) -> None:
        """
        Send a JSON-RPC notification (no response expected).
        
        Args:
            notification: JSON-RPC notification object
        """
        pass


class StdioTransport(Transport):
    """
    Stdio transport for MCP.
    
    Communicates with MCP server via stdin/stdout of a subprocess.
    """
    
    def __init__(self, command: List[str]):
        """
        Initialize stdio transport.
        
        Args:
            command: Command to start the MCP server process
        """
        self.command = command
        self.process = None
        self._read_task = None
        self._response_queues = {}
        self._notification_handlers = []
    
    async def connect(self) -> None:
        """Start the MCP server process."""
        self.process = await asyncio.create_subprocess_exec(
            *self.command,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        # Start reading from stdout
        self._read_task = asyncio.create_task(self._read_output())
        logger.info(f"Started MCP server process: {' '.join(self.command)}")
    
    async def disconnect(self) -> None:
        """Stop the MCP server process."""
        if self.process:
            self.process.terminate()
            await self.process.wait()
            
        if self._read_task:
            self._read_task.cancel()
            try:
                await self._read_task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped MCP server process")
    
    async def _read_output(self):
        """Read JSON-RPC messages from stdout."""
        while True:
            try:
                line = await self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    message = json.loads(line.decode().strip())
                    
                    # Route message based on type
                    if "id" in message and message["id"] in self._response_queues:
                        # Response to a request
                        await self._response_queues[message["id"]].put(message)
                    elif "method" in message and "id" not in message:
                        # Notification from server
                        for handler in self._notification_handlers:
                            await handler(message)
                    else:
                        logger.warning(f"Unhandled message from MCP server: {message}")
                        
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON from MCP server: {line}")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error reading from MCP server: {e}")
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via stdio."""
        request_id = request["id"]
        self._response_queues[request_id] = asyncio.Queue()
        
        try:
            # Send request
            self.process.stdin.write((json.dumps(request) + "\n").encode())
            await self.process.stdin.drain()
            
            # Wait for response
            response = await asyncio.wait_for(
                self._response_queues[request_id].get(),
                timeout=30.0
            )
            
            return response
            
        finally:
            del self._response_queues[request_id]
    
    async def send_notification(self, notification: Dict[str, Any]) -> None:
        """Send notification via stdio."""
        self.process.stdin.write((json.dumps(notification) + "\n").encode())
        await self.process.stdin.drain()
    
    def add_notification_handler(self, handler):
        """Add handler for server notifications."""
        self._notification_handlers.append(handler)


class SSETransport(Transport):
    """
    Server-Sent Events (SSE) transport for MCP.
    
    Communicates with MCP server via HTTP with SSE for server-to-client messages.
    """
    
    def __init__(self, url: str, headers: Optional[Dict[str, str]] = None):
        """
        Initialize SSE transport.
        
        Args:
            url: URL of the MCP server endpoint
            headers: Optional HTTP headers
        """
        self.url = url
        self.headers = headers or {}
        self.client = None
        self._notification_handlers = []
    
    async def connect(self) -> None:
        """Create HTTP client."""
        self.client = httpx.AsyncClient(
            timeout=30.0,
            headers=self.headers,
            limits=httpx.Limits(max_connections=10)
        )
        logger.info(f"Connected to MCP server at {self.url}")
    
    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self.client:
            await self.client.aclose()
        logger.info("Disconnected from MCP server")
    
    async def send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send request via SSE."""
        headers = {
            **self.headers,
            "Content-Type": "application/json",
            "Accept": "text/event-stream"
        }
        
        request_id = request["id"]
        
        async with self.client.stream(
            "POST",
            self.url,
            json=request,
            headers=headers
        ) as response:
            response.raise_for_status()
            
            # Parse SSE stream for the response
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    try:
                        data = json.loads(line[6:])
                        
                        # Check if this is our response
                        if data.get("id") == request_id:
                            return data
                        
                        # Otherwise it might be a notification
                        if "method" in data and "id" not in data:
                            for handler in self._notification_handlers:
                                await handler(data)
                                
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid JSON in SSE data: {line}")
        
        raise Exception(f"No response received for request {request_id}")
    
    async def send_notification(self, notification: Dict[str, Any]) -> None:
        """Send notification via SSE."""
        headers = {
            **self.headers,
            "Content-Type": "application/json"
        }
        
        response = await self.client.post(
            self.url,
            json=notification,
            headers=headers
        )
        response.raise_for_status()
    
    def add_notification_handler(self, handler):
        """Add handler for server notifications."""
        self._notification_handlers.append(handler)


def create_transport(
    url: Optional[str] = None,
    command: Optional[List[str]] = None,
    headers: Optional[Dict[str, str]] = None
) -> Transport:
    """
    Create appropriate transport based on parameters.
    
    Args:
        url: URL for SSE transport
        command: Command for stdio transport
        headers: Optional headers for SSE transport
        
    Returns:
        Transport instance
        
    Raises:
        ValueError: If neither url nor command is provided
    """
    if command:
        return StdioTransport(command)
    elif url:
        return SSETransport(url, headers)
    else:
        raise ValueError("Either url or command must be provided")