"""
MCP Connection Management - Handles the complete MCP connection lifecycle.

This module provides connection management for MCP following the 2025-03-26
specification including initialization, operation, and graceful shutdown.
"""

import asyncio
import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable, Protocol
from enum import Enum

from .protocol import (
    MCPProtocolHandler,
    MCPProtocolError,
    MCPConnectionError,
    MCPTimeoutError,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    JSONRPCErrorCode,
    MCPImplementationInfo,
    MCPCapabilities
)

logger = logging.getLogger(__name__)


class MCPConnectionState(Enum):
    """MCP connection lifecycle states."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    INITIALIZING = "initializing"
    INITIALIZED = "initialized"
    OPERATING = "operating"
    SHUTTING_DOWN = "shutting_down"
    ERROR = "error"


class MCPTransport(Protocol):
    """Transport interface for MCP connections."""
    
    async def connect(self) -> None:
        """Establish transport connection."""
        ...
    
    async def disconnect(self) -> None:
        """Close transport connection."""
        ...
    
    async def send(self, message: bytes) -> None:
        """Send message bytes."""
        ...
    
    async def receive(self) -> bytes:
        """Receive message bytes."""
        ...
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        ...


class MCPMessageHandler(ABC):
    """Abstract message handler for MCP requests and notifications."""
    
    @abstractmethod
    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle incoming request and return response."""
        pass
    
    @abstractmethod
    async def handle_notification(self, notification: JSONRPCRequest) -> None:
        """Handle incoming notification."""
        pass


class MCPConnection:
    """
    Complete MCP connection implementation.
    
    Manages the full lifecycle of an MCP connection including initialization,
    operation, and cleanup following the MCP 2025-03-26 specification.
    """
    
    def __init__(
        self,
        transport: MCPTransport,
        handler: MCPMessageHandler,
        implementation_info: MCPImplementationInfo,
        capabilities: MCPCapabilities,
        timeout: float = 30.0,
        legacy_mode: bool = False
    ):
        """
        Initialize MCP connection.
        
        Args:
            transport: Transport implementation
            handler: Message handler
            implementation_info: Client/server information
            capabilities: Supported capabilities
            timeout: Operation timeout
            legacy_mode: Enable backward compatibility
        """
        self.transport = transport
        self.handler = handler
        self.timeout = timeout
        self.legacy_mode = legacy_mode
        
        # Protocol handler
        self.protocol = MCPProtocolHandler(
            implementation_info=implementation_info,
            capabilities=capabilities,
            timeout=timeout,
            legacy_mode=legacy_mode
        )
        
        # Connection state
        self.state = MCPConnectionState.DISCONNECTED
        self._shutdown_event = asyncio.Event()
        self._receive_task: Optional[asyncio.Task] = None
        self._pending_requests: Dict[Union[str, int], asyncio.Future] = {}
        
        # Statistics
        self.stats = {
            "messages_sent": 0,
            "messages_received": 0,
            "requests_sent": 0,
            "responses_received": 0,
            "notifications_sent": 0,
            "notifications_received": 0,
            "errors": 0
        }
        
        logger.info(f"Created MCP connection with {implementation_info.name}")
    
    @property
    def is_initialized(self) -> bool:
        """Check if connection is properly initialized."""
        return self.state == MCPConnectionState.OPERATING
    
    @property
    def peer_info(self) -> Optional[MCPImplementationInfo]:
        """Get peer implementation information."""
        return self.protocol.peer_info
    
    @property
    def peer_capabilities(self) -> Optional[MCPCapabilities]:
        """Get peer capabilities."""
        return self.protocol.peer_capabilities
    
    async def connect(self) -> None:
        """Establish connection and perform MCP initialization."""
        if self.state != MCPConnectionState.DISCONNECTED:
            raise MCPConnectionError(f"Cannot connect from state {self.state.value}")
        
        try:
            self.state = MCPConnectionState.CONNECTING
            logger.info("Connecting to MCP peer...")
            
            # Establish transport connection
            await self.transport.connect()
            
            # Start message receiving
            self._receive_task = asyncio.create_task(self._receive_loop())
            
            # MCP connections start in INITIALIZING state and wait for explicit initialization
            self.state = MCPConnectionState.INITIALIZING
            logger.info("MCP connection ready for initialization")
            
        except Exception as e:
            self.state = MCPConnectionState.ERROR
            await self._cleanup()
            raise MCPConnectionError(f"Connection failed: {e}") from e
    
    async def initialize_client(self) -> None:
        """Initialize as MCP client (send initialize request)."""
        if self.state != MCPConnectionState.INITIALIZING:
            raise MCPConnectionError(f"Cannot initialize client from state {self.state.value}")
        
        try:
            await self._perform_initialization()
            self.state = MCPConnectionState.OPERATING
            logger.info(f"MCP client connection established with {self.peer_info.name}")
        except Exception as e:
            self.state = MCPConnectionState.ERROR
            raise MCPConnectionError(f"Client initialization failed: {e}") from e
    
    async def wait_for_initialization(self) -> None:
        """Wait for client to initialize this server connection."""
        if self.state != MCPConnectionState.INITIALIZING:
            raise MCPConnectionError(f"Cannot wait for initialization from state {self.state.value}")
        
        # Server waits for initialize request to be processed by message handler
        # When it receives and responds to initialize + receives initialized notification,
        # the message handler should call complete_initialization()
        logger.info("MCP server waiting for client initialization...")
        
        # Wait until initialization is complete
        while self.state == MCPConnectionState.INITIALIZING:
            await asyncio.sleep(0.1)
    
    def complete_initialization(self, peer_info: MCPImplementationInfo, peer_capabilities: MCPCapabilities) -> None:
        """Complete initialization after successful handshake (called by message handler)."""
        self.protocol.peer_info = peer_info
        self.protocol.peer_capabilities = peer_capabilities
        self.protocol.initialized = True
        self.state = MCPConnectionState.OPERATING
        logger.info(f"MCP server initialization completed with {peer_info.name}")

    async def disconnect(self) -> None:
        """Gracefully disconnect from MCP peer."""
        if self.state == MCPConnectionState.DISCONNECTED:
            return
        
        logger.info("Disconnecting from MCP peer...")
        self.state = MCPConnectionState.SHUTTING_DOWN
        
        # Signal shutdown
        self._shutdown_event.set()
        
        # Cancel pending requests
        for future in self._pending_requests.values():
            if not future.done():
                future.cancel()
        self._pending_requests.clear()
        
        await self._cleanup()
        self.state = MCPConnectionState.DISCONNECTED
        logger.info("MCP connection closed")
    
    async def send_request(self, request: JSONRPCRequest, timeout: Optional[float] = None) -> JSONRPCResponse:
        """Send request and wait for response with optional custom timeout."""
        if not self.is_initialized:
            raise MCPConnectionError("Connection not initialized")
        
        if request.is_notification():
            raise MCPProtocolError("Cannot send notification as request")
        
        request_id = request.id
        actual_timeout = timeout if timeout is not None else self.timeout
        
        # Create future for response
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # Send request
            await self._send_message(request)
            self.stats["requests_sent"] += 1
            
            # Wait for response with custom timeout
            response = await asyncio.wait_for(future, timeout=actual_timeout)
            self.stats["responses_received"] += 1
            
            return response
            
        except asyncio.TimeoutError:
            self.stats["errors"] += 1
            raise MCPTimeoutError(f"Request {request_id} timed out after {actual_timeout}s")
        except Exception as e:
            self.stats["errors"] += 1
            raise
        finally:
            self._pending_requests.pop(request_id, None)
    
    async def send_notification(self, notification: JSONRPCRequest) -> None:
        """Send notification (no response expected)."""
        if not self.is_initialized:
            raise MCPConnectionError("Connection not initialized")
        
        if not notification.is_notification():
            raise MCPProtocolError("Cannot send request as notification")
        
        await self._send_message(notification)
        self.stats["notifications_sent"] += 1
    
    async def _perform_initialization(self) -> None:
        """Perform MCP initialization handshake."""
        try:
            # Send initialize request
            init_request = self.protocol.create_initialize_request()
            
            logger.debug(f"Sending initialize request with version {self.protocol.CURRENT_VERSION}")
            
            # Send and wait for response
            response = await self._send_request_direct(init_request)
            
            # Handle response
            self.protocol.handle_initialize_response(response)
            
            # Send initialized notification
            init_notification = self.protocol.create_initialized_notification()
            await self._send_message(init_notification)
            
            logger.info("MCP initialization completed successfully")
            
        except Exception as e:
            logger.error(f"MCP initialization failed: {e}")
            raise MCPProtocolError(f"Initialization failed: {e}") from e
    
    async def _send_request_direct(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Send request during initialization."""
        request_id = request.id
        
        # Create future for response
        future = asyncio.Future()
        self._pending_requests[request_id] = future
        
        try:
            # Send request
            await self._send_message(request)
            
            # Wait for response
            response = await asyncio.wait_for(future, timeout=self.timeout)
            return response
            
        except asyncio.TimeoutError:
            raise MCPTimeoutError(f"Request {request_id} timed out")
        finally:
            self._pending_requests.pop(request_id, None)
    
    async def _send_message(self, message: Union[JSONRPCRequest, JSONRPCResponse]) -> None:
        """Send message via transport."""
        if not self.transport.is_connected():
            raise MCPConnectionError("Transport not connected")
        
        try:
            message_dict = message.to_dict()
            message_json = json.dumps(message_dict)
            message_bytes = message_json.encode("utf-8")
            
            await self.transport.send(message_bytes)
            self.stats["messages_sent"] += 1
            
        except Exception as e:
            self.stats["errors"] += 1
            logger.error(f"Failed to send message: {e}")
            raise MCPConnectionError(f"Send failed: {e}") from e
    
    async def _receive_loop(self) -> None:
        """Main message receiving loop."""
        logger.debug("Started message receive loop")
        
        try:
            while not self._shutdown_event.is_set():
                try:
                    # Receive message with timeout
                    message_data = await asyncio.wait_for(
                        self.transport.receive(),
                        timeout=1.0  # Short timeout to check shutdown
                    )
                    
                    # Process message
                    await self._process_received_message(message_data)
                    self.stats["messages_received"] += 1
                    
                except asyncio.TimeoutError:
                    # Normal timeout, continue loop
                    continue
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    self.stats["errors"] += 1
                    
                    # For serious errors, break the loop
                    if isinstance(e, (ConnectionError, OSError)):
                        logger.error(f"Breaking receive loop due to connection error: {e}")
                        break
                    
        except Exception as e:
            logger.error(f"Receive loop failed: {e}")
            self.state = MCPConnectionState.ERROR
            logger.error(f"Connection state changed to ERROR due to receive loop failure")
        
        logger.debug("Message receive loop ended")
    
    async def _process_received_message(self, message_data: bytes) -> None:
        """Process received message."""
        try:
            # Parse JSON
            try:
                message_text = message_data.decode("utf-8")
                message = json.loads(message_text)
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                logger.error(f"Invalid message format: {e}")
                return
            
            # Handle batch vs single message
            if isinstance(message, list):
                await self._process_batch_message(message)
            else:
                await self._process_single_message(message)
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.stats["errors"] += 1
    
    async def _process_batch_message(self, batch: List[Dict[str, Any]]) -> None:
        """Process batch of messages."""
        tasks = []
        for message_dict in batch:
            tasks.append(self._process_single_message(message_dict))
        
        await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _process_single_message(self, message_dict: Dict[str, Any]) -> None:
        """Process single message."""
        try:
            # Check if this is a response
            if "result" in message_dict or "error" in message_dict:
                await self._handle_response(message_dict)
                return
            
            # Parse as request/notification
            request = JSONRPCRequest.from_dict(message_dict)
            
            if request.is_notification():
                # Handle notification
                await self.handler.handle_notification(request)
                self.stats["notifications_received"] += 1
            else:
                # Handle request and send response
                try:
                    response = await self.handler.handle_request(request)
                    await self._send_message(response)
                except Exception as e:
                    # Send error response
                    error_response = self.protocol.create_error_response(
                        request.id,
                        JSONRPCErrorCode.INTERNAL_ERROR,
                        str(e)
                    )
                    await self._send_message(error_response)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            self.stats["errors"] += 1
    
    async def _handle_response(self, message_dict: Dict[str, Any]) -> None:
        """Handle response to our request."""
        try:
            response = JSONRPCResponse.from_dict(message_dict)
            request_id = response.id
            
            if request_id in self._pending_requests:
                future = self._pending_requests[request_id]
                if not future.done():
                    future.set_result(response)
                    
        except Exception as e:
            logger.error(f"Error handling response: {e}")
            self.stats["errors"] += 1
    
    async def _cleanup(self) -> None:
        """Clean up connection resources."""
        try:
            # Cancel receive task
            if self._receive_task and not self._receive_task.done():
                self._receive_task.cancel()
                try:
                    await self._receive_task
                except asyncio.CancelledError:
                    pass
            
            # Close transport
            if self.transport.is_connected():
                await self.transport.disconnect()
                
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def get_stats(self) -> Dict[str, int]:
        """Get connection statistics."""
        return self.stats.copy()