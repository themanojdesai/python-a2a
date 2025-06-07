"""
MCP Protocol Foundation - JSON-RPC 2.0 and MCP 2025-03-26 implementation.

This module provides the core protocol handling for the Model Context Protocol
following the official specification. It handles JSON-RPC 2.0 message format,
MCP-specific extensions, and proper validation.
"""

import asyncio
import json
import logging
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable, Set
from datetime import datetime

logger = logging.getLogger(__name__)

# Import legacy errors for backward compatibility
try:
    from .client import MCPError, MCPConnectionError, MCPTimeoutError, MCPToolError
except ImportError:
    # Define if not available
    class MCPError(Exception):
        """Base MCP error."""
        pass

    class MCPConnectionError(MCPError):
        """MCP connection error."""
        pass

    class MCPTimeoutError(MCPError):
        """MCP timeout error."""
        pass

    class MCPToolError(MCPError):
        """MCP tool error."""
        pass


class MCPProtocolError(MCPError):
    """MCP protocol violation error."""
    pass


class JSONRPCErrorCode(Enum):
    """Standard JSON-RPC 2.0 error codes with MCP extensions."""
    # Standard JSON-RPC errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # MCP-specific error codes
    INITIALIZATION_FAILED = -32000
    CAPABILITY_NOT_SUPPORTED = -32001
    TOOL_NOT_FOUND = -32002
    RESOURCE_NOT_FOUND = -32003
    PROMPT_NOT_FOUND = -32004
    AUTHENTICATION_FAILED = -32005
    AUTHORIZATION_FAILED = -32006


@dataclass
class JSONRPCError:
    """JSON-RPC 2.0 error object."""
    code: int
    message: str
    data: Optional[Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {
            "code": self.code,
            "message": self.message
        }
        if self.data is not None:
            result["data"] = self.data
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONRPCError':
        """Create from dictionary with validation."""
        if not isinstance(data, dict):
            raise ValueError("Error data must be a dictionary")
        
        code = data.get("code")
        if not isinstance(code, int):
            raise ValueError("Error code must be an integer")
        
        message = data.get("message", "")
        if not isinstance(message, str):
            raise ValueError("Error message must be a string")
        
        return cls(
            code=code,
            message=message,
            data=data.get("data")
        )


@dataclass
class JSONRPCMessage:
    """Base JSON-RPC 2.0 message."""
    jsonrpc: str = "2.0"
    
    def validate(self) -> None:
        """Validate message format according to JSON-RPC 2.0."""
        if self.jsonrpc != "2.0":
            raise MCPProtocolError("Invalid JSON-RPC version")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {"jsonrpc": self.jsonrpc}


@dataclass
class JSONRPCRequest(JSONRPCMessage):
    """JSON-RPC 2.0 request/notification."""
    method: str = ""
    params: Optional[Dict[str, Any]] = None
    id: Optional[Union[str, int]] = None
    
    def validate(self) -> None:
        """Validate request format."""
        super().validate()
        
        if not self.method or not isinstance(self.method, str):
            raise MCPProtocolError("Method must be a non-empty string")
        
        # MCP requirement: Request ID must not be null if present
        if hasattr(self, '_has_id') and self._has_id and self.id is None:
            raise MCPProtocolError("Request ID must not be null")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["method"] = self.method
        
        if self.params is not None:
            result["params"] = self.params
        
        if not self.is_notification():
            result["id"] = self.id
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONRPCRequest':
        """Create from dictionary with validation."""
        if not isinstance(data, dict):
            raise MCPProtocolError("Request data must be a dictionary")
        
        request = cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            method=data.get("method", ""),
            params=data.get("params"),
            id=data.get("id")
        )
        
        # Track if ID was explicitly provided
        request._has_id = "id" in data
        
        request.validate()
        return request
    
    def is_notification(self) -> bool:
        """Check if this is a notification (no response expected)."""
        return not hasattr(self, '_has_id') or not self._has_id


@dataclass
class JSONRPCResponse(JSONRPCMessage):
    """JSON-RPC 2.0 response."""
    result: Optional[Any] = None
    error: Optional[JSONRPCError] = None
    id: Optional[Union[str, int]] = None
    
    def validate(self) -> None:
        """Validate response format."""
        super().validate()
        
        # Must have either result or error, but not both
        has_result = self.result is not None
        has_error = self.error is not None
        
        if has_result and has_error:
            raise MCPProtocolError("Response cannot have both result and error")
        
        if not has_result and not has_error:
            raise MCPProtocolError("Response must have either result or error")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = super().to_dict()
        result["id"] = self.id
        
        if self.error:
            result["error"] = self.error.to_dict()
        else:
            result["result"] = self.result
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'JSONRPCResponse':
        """Create from dictionary with validation."""
        if not isinstance(data, dict):
            raise MCPProtocolError("Response data must be a dictionary")
        
        error_data = data.get("error")
        error = None
        if error_data:
            error = JSONRPCError.from_dict(error_data)
        
        response = cls(
            jsonrpc=data.get("jsonrpc", "2.0"),
            result=data.get("result"),
            error=error,
            id=data.get("id")
        )
        response.validate()
        return response


@dataclass
class MCPCapabilities:
    """MCP capability definitions."""
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None
    roots: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {}
        
        if self.tools is not None:
            result["tools"] = self.tools
        if self.resources is not None:
            result["resources"] = self.resources
        if self.prompts is not None:
            result["prompts"] = self.prompts
        if self.roots is not None:
            result["roots"] = self.roots
        if self.sampling is not None:
            result["sampling"] = self.sampling
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPCapabilities':
        """Create from dictionary."""
        if not isinstance(data, dict):
            data = {}
        
        return cls(
            tools=data.get("tools"),
            resources=data.get("resources"),
            prompts=data.get("prompts"),
            roots=data.get("roots"),
            sampling=data.get("sampling")
        )


@dataclass
class MCPImplementationInfo:
    """MCP implementation information."""
    name: str
    version: str
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "version": self.version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPImplementationInfo':
        """Create from dictionary."""
        if not isinstance(data, dict):
            data = {}
        
        return cls(
            name=data.get("name", "Unknown"),
            version=data.get("version", "Unknown")
        )


@dataclass
class MCPContent:
    """MCP content item."""
    type: str
    text: Optional[str] = None
    data: Optional[str] = None
    mime_type: Optional[str] = None
    annotations: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        result = {"type": self.type}
        
        if self.text is not None:
            result["text"] = self.text
        if self.data is not None:
            result["data"] = self.data
        if self.mime_type is not None:
            result["mimeType"] = self.mime_type
        if self.annotations is not None:
            result["annotations"] = self.annotations
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MCPContent':
        """Create from dictionary."""
        if not isinstance(data, dict):
            raise ValueError("Content data must be a dictionary")
        
        content_type = data.get("type")
        if not isinstance(content_type, str):
            raise ValueError("Content type must be a string")
        
        return cls(
            type=content_type,
            text=data.get("text"),
            data=data.get("data"),
            mime_type=data.get("mimeType"),
            annotations=data.get("annotations")
        )


class MCPProtocolHandler:
    """
    Core MCP protocol handler.
    
    Handles JSON-RPC 2.0 message processing and MCP-specific protocol logic
    following the 2025-03-26 specification.
    """
    
    # MCP protocol versions supported
    SUPPORTED_VERSIONS = ["2025-03-26", "2024-11-05"]  # Include legacy for compatibility
    CURRENT_VERSION = "2025-03-26"
    
    def __init__(
        self,
        implementation_info: MCPImplementationInfo,
        capabilities: MCPCapabilities,
        timeout: float = 30.0,
        legacy_mode: bool = False
    ):
        """
        Initialize protocol handler.
        
        Args:
            implementation_info: Implementation details
            capabilities: Supported capabilities
            timeout: Request timeout
            legacy_mode: Enable backward compatibility
        """
        self.implementation_info = implementation_info
        self.capabilities = capabilities
        self.timeout = timeout
        self.legacy_mode = legacy_mode
        
        # Protocol state
        self.initialized = False
        self.negotiated_version = self.CURRENT_VERSION
        self.peer_info: Optional[MCPImplementationInfo] = None
        self.peer_capabilities: Optional[MCPCapabilities] = None
        
        # Request tracking
        self._request_counter = 0
        self._used_request_ids: Set[Union[str, int]] = set()
        
        logger.info(f"Initialized MCP protocol handler v{self.CURRENT_VERSION}")
    
    def generate_request_id(self) -> Union[str, int]:
        """Generate unique request ID."""
        while True:
            request_id = str(uuid.uuid4())
            if request_id not in self._used_request_ids:
                self._used_request_ids.add(request_id)
                return request_id
    
    def create_request(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> JSONRPCRequest:
        """Create JSON-RPC request."""
        request = JSONRPCRequest(
            method=method,
            params=params,
            id=self.generate_request_id()
        )
        request._has_id = True
        return request
    
    def create_notification(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None
    ) -> JSONRPCRequest:
        """Create JSON-RPC notification."""
        notification = JSONRPCRequest(
            method=method,
            params=params
        )
        # Don't set _has_id to make it a notification
        return notification
    
    def create_response(
        self,
        request_id: Union[str, int],
        result: Optional[Any] = None,
        error: Optional[JSONRPCError] = None
    ) -> JSONRPCResponse:
        """Create JSON-RPC response."""
        return JSONRPCResponse(
            result=result,
            error=error,
            id=request_id
        )
    
    def create_error_response(
        self,
        request_id: Union[str, int],
        code: JSONRPCErrorCode,
        message: str,
        data: Optional[Any] = None
    ) -> JSONRPCResponse:
        """Create error response."""
        error = JSONRPCError(
            code=code.value,
            message=message,
            data=data
        )
        return self.create_response(request_id, error=error)
    
    def create_initialize_request(self) -> JSONRPCRequest:
        """Create MCP initialize request."""
        return self.create_request("initialize", {
            "protocolVersion": self.CURRENT_VERSION,
            "capabilities": self.capabilities.to_dict(),
            "clientInfo": self.implementation_info.to_dict()
        })
    
    def create_initialized_notification(self) -> JSONRPCRequest:
        """Create MCP initialized notification."""
        return self.create_notification("initialized", {})
    
    def handle_initialize_response(self, response: JSONRPCResponse) -> None:
        """Handle initialize response."""
        if response.error:
            raise MCPProtocolError(f"Initialize failed: {response.error.message}")
        
        result = response.result or {}
        
        # Extract negotiated version
        negotiated_version = result.get("protocolVersion", self.CURRENT_VERSION)
        if negotiated_version not in self.SUPPORTED_VERSIONS:
            if self.legacy_mode and negotiated_version in ["2024-11-05"]:
                logger.warning(f"Using legacy protocol version: {negotiated_version}")
            else:
                raise MCPProtocolError(f"Unsupported protocol version: {negotiated_version}")
        
        self.negotiated_version = negotiated_version
        
        # Extract peer info
        peer_info_data = result.get("serverInfo", {})
        self.peer_info = MCPImplementationInfo.from_dict(peer_info_data)
        
        # Extract peer capabilities
        capabilities_data = result.get("capabilities", {})
        self.peer_capabilities = MCPCapabilities.from_dict(capabilities_data)
        
        self.initialized = True
        
        logger.info(
            f"MCP initialized with {self.peer_info.name} v{self.peer_info.version}, "
            f"protocol {self.negotiated_version}"
        )


# Content creation helpers
def create_text_content(text: str) -> MCPContent:
    """Create text content item."""
    return MCPContent(type="text", text=text)


def create_image_content(data: str, mime_type: str = "image/png") -> MCPContent:
    """Create image content item."""
    return MCPContent(type="image", data=data, mime_type=mime_type)


def create_blob_content(data: str, mime_type: str) -> MCPContent:
    """Create blob content item."""
    return MCPContent(type="blob", data=data, mime_type=mime_type)