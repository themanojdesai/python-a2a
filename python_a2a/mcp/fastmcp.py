"""
FastMCP - A simple and powerful MCP server implementation for Python A2A.

This module provides a decorator-based API for creating MCP servers that can be used
with A2A agents or as standalone servers. It handles the details of the MCP protocol,
allowing developers to focus on implementing the actual functionality.
"""

import asyncio
import inspect
import json
import logging
import uuid
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
from typing import Any, Callable, Dict, List, Optional, Set, Type, Union, get_type_hints
import pydantic
from pydantic import BaseModel, Field

from .client import MCPError, MCPConnectionError, MCPTimeoutError, MCPToolError

# Configure logging
logger = logging.getLogger("python_a2a.mcp.fastmcp")

class ContentType(str, Enum):
    """MCP content types"""
    TEXT = "text"
    IMAGE = "image"
    BLOB = "blob"

class MCPResponse:
    """MCP response format"""
    
    def __init__(
        self, 
        content: List[Dict[str, Any]] = None, 
        is_error: bool = False
    ):
        """
        Initialize MCP response.
        
        Args:
            content: List of content items
            is_error: Whether this is an error response
        """
        self.content = content or []
        self.is_error = is_error
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for JSON serialization"""
        return {
            "content": self.content,
            "isError": self.is_error
        }
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'MCPResponse':
        """Create from dictionary representation"""
        return MCPResponse(
            content=data.get("content", []),
            is_error=data.get("isError", False)
        )

class ToolDefinition:
    """MCP tool definition"""
    
    def __init__(
        self, 
        name: str, 
        description: str,
        parameters: List[Dict[str, Any]],
        handler: Callable
    ):
        """
        Initialize tool definition.
        
        Args:
            name: Tool name
            description: Tool description
            parameters: Tool parameters schema
            handler: Tool handler function
        """
        self.name = name
        self.description = description
        self.parameters = parameters
        self.handler = handler
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for the MCP protocol"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }

class ResourceDefinition:
    """MCP resource definition"""
    
    def __init__(
        self, 
        uri: str, 
        name: str, 
        description: str,
        handler: Callable,
        is_template: bool = False
    ):
        """
        Initialize resource definition.
        
        Args:
            uri: Resource URI or URI template
            name: Resource name
            description: Resource description
            handler: Resource handler function
            is_template: Whether this is a template resource
        """
        self.uri = uri
        self.name = name
        self.description = description
        self.handler = handler
        self.is_template = is_template
        
        # Extract template parameters if this is a template
        self.template_params = []
        if is_template:
            import re
            # Extract {param} or {param:type} from URI
            param_matches = re.findall(r'{([^{}:]+)(?::([^{}]+))?}', uri)
            for name, type_hint in param_matches:
                self.template_params.append({
                    "name": name,
                    "type": type_hint or "string"
                })
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation for the MCP protocol"""
        if self.is_template:
            return {
                "uriTemplate": self.uri,
                "name": self.name,
                "description": self.description,
                "arguments": [
                    {
                        "name": param["name"],
                        "type": param["type"],
                        "required": True  # Default to required
                    }
                    for param in self.template_params
                ]
            }
        else:
            return {
                "uri": self.uri,
                "name": self.name,
                "description": self.description
            }
    
    def matches_uri(self, uri: str) -> Dict[str, str]:
        """
        Check if a URI matches this resource definition and extract parameters.
        
        Args:
            uri: URI to check
            
        Returns:
            Dictionary of extracted parameters if match, empty dict otherwise
        """
        if not self.is_template:
            return {} if uri == self.uri else None
        
        # For templates, parse according to the template pattern
        import re
        
        # Convert template to regex pattern
        pattern = self.uri
        param_names = []
        
        def replace_param(match):
            param_name = match.group(1).split(':')[0]
            param_names.append(param_name)
            return f"(?P<{param_name}>[^/]+)"
        
        pattern = re.sub(r'{([^{}]+)}', replace_param, pattern)
        pattern = f"^{pattern}$"
        
        # Try to match
        match = re.match(pattern, uri)
        if match:
            return match.groupdict()
        return None

def _format_response(result: Any) -> MCPResponse:
    """
    Format function result as an MCP response.
    
    Args:
        result: Function result
        
    Returns:
        Formatted MCP response
    """
    # If already an MCPResponse, return as is
    if isinstance(result, MCPResponse):
        return result
    
    # If a dictionary with 'content' key, convert to MCPResponse
    if isinstance(result, dict) and "content" in result:
        return MCPResponse(
            content=result["content"],
            is_error=result.get("isError", False)
        )
    
    # If a string, convert to text content
    if isinstance(result, str):
        return MCPResponse(
            content=[
                {
                    "type": "text",
                    "text": result
                }
            ]
        )
    
    # If a list of strings, convert to multiple text content items
    if isinstance(result, list) and all(isinstance(item, str) for item in result):
        return MCPResponse(
            content=[
                {
                    "type": "text",
                    "text": item
                }
                for item in result
            ]
        )
    
    # Otherwise, convert to JSON string and then to text content
    try:
        return MCPResponse(
            content=[
                {
                    "type": "text",
                    "text": json.dumps(result)
                }
            ]
        )
    except:
        # If JSON conversion fails, use string representation
        return MCPResponse(
            content=[
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        )

def text_response(text: str) -> MCPResponse:
    """
    Create a text response.
    
    Args:
        text: Text content
        
    Returns:
        MCP response with text content
    """
    return MCPResponse(
        content=[
            {
                "type": "text",
                "text": text
            }
        ]
    )

def error_response(message: str) -> MCPResponse:
    """
    Create an error response.
    
    Args:
        message: Error message
        
    Returns:
        MCP error response with text content
    """
    return MCPResponse(
        content=[
            {
                "type": "text",
                "text": message
            }
        ],
        is_error=True
    )

def image_response(
    data: Union[str, bytes], 
    mime_type: str = "image/png"
) -> MCPResponse:
    """
    Create an image response.
    
    Args:
        data: Image data as base64 string or bytes
        mime_type: Image MIME type
        
    Returns:
        MCP response with image content
    """
    import base64
    
    # Convert bytes to base64 if necessary
    if isinstance(data, bytes):
        data = base64.b64encode(data).decode('utf-8')
        
    return MCPResponse(
        content=[
            {
                "type": "image",
                "data": data,
                "mimeType": mime_type
            }
        ]
    )

def multi_content_response(content_items: List[Dict[str, Any]]) -> MCPResponse:
    """
    Create a response with multiple content items.
    
    Args:
        content_items: List of content items
        
    Returns:
        MCP response with multiple content items
    """
    return MCPResponse(content=content_items)

class FastMCP:
    """
    FastMCP server implementation for Python A2A.
    
    This class provides a simple way to create MCP servers with a decorator-based API.
    """
    
    def __init__(
        self, 
        name: str, 
        version: str = "1.0.0", 
        description: str = "",
        dependencies: List[str] = None
    ):
        """
        Initialize the FastMCP server.
        
        Args:
            name: Server name
            version: Server version
            description: Server description
            dependencies: List of package dependencies
        """
        self.name = name
        self.version = version
        self.description = description or f"{name} MCP Server"
        self.dependencies = dependencies or []
        
        # Storage for tools and resources
        self.tools: Dict[str, ToolDefinition] = {}
        self.resources: Dict[str, ResourceDefinition] = {}
        
        # Server metadata
        self.metadata = {
            "name": name,
            "version": version,
            "description": description,
            "capabilities": ["tools", "resources"]
        }
        
        logger.info(f"Initialized FastMCP server: {name} v{version}")
    
    def tool(
        self, 
        name: Optional[str] = None, 
        description: Optional[str] = None
    ) -> Callable:
        """
        Decorator to register a tool.
        
        Args:
            name: Optional tool name (default: function name)
            description: Optional tool description (default: function docstring)
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            # Get tool name
            tool_name = name or func.__name__
            
            # Get tool description
            tool_description = description or (func.__doc__ or "").strip()
            
            # Get parameter information from type hints and docstring
            sig = inspect.signature(func)
            type_hints = get_type_hints(func)
            
            # Build parameter schema
            parameters = {
                "type": "object",
                "properties": {},
                "required": []
            }
            
            param_docs = {}
            if func.__doc__:
                # Extract parameter descriptions from docstring
                import re
                param_sections = re.findall(r'Args:(.*?)(?:\n\n|\n\s*Returns:|$)', func.__doc__, re.DOTALL)
                if param_sections:
                    param_section = param_sections[0]
                    param_matches = re.findall(r'\s+(\w+)\s*:\s*(.+?)(?=\n\s+\w+\s*:|$)', param_section, re.DOTALL)
                    for param_name, param_desc in param_matches:
                        param_docs[param_name] = param_desc.strip()
            
            # Process parameters
            for param_name, param in sig.parameters.items():
                if param_name == "self" or param_name == "cls":
                    continue
                
                # Determine parameter type
                param_type = type_hints.get(param_name, Any)
                if param_type == str:
                    json_type = "string"
                elif param_type == int:
                    json_type = "integer"
                elif param_type == float:
                    json_type = "number"
                elif param_type == bool:
                    json_type = "boolean"
                elif hasattr(param_type, "__origin__") and param_type.__origin__ == list:
                    json_type = "array"
                elif hasattr(param_type, "__origin__") and param_type.__origin__ == dict:
                    json_type = "object"
                else:
                    json_type = "string"
                
                # Get parameter description
                param_description = param_docs.get(param_name, "")
                
                # Add to schema
                parameters["properties"][param_name] = {
                    "type": json_type,
                    "description": param_description
                }
                
                # Check if required
                if param.default == inspect.Parameter.empty:
                    parameters["required"].append(param_name)
            
            # Register the tool
            self.tools[tool_name] = ToolDefinition(
                name=tool_name,
                description=tool_description,
                parameters=parameters,
                handler=func
            )
            
            logger.info(f"Registered tool: {tool_name}")
            
            # Return the original function
            return func
        
        return decorator
    
    def resource(
        self, 
        uri: str, 
        name: Optional[str] = None, 
        description: Optional[str] = None
    ) -> Callable:
        """
        Decorator to register a resource or resource template.
        
        Args:
            uri: Resource URI or URI template
            name: Optional resource name (default: function name)
            description: Optional resource description (default: function docstring)
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            # Get resource name
            resource_name = name or func.__name__
            
            # Get resource description
            resource_description = description or (func.__doc__ or "").strip()
            
            # Determine if this is a template
            is_template = "{" in uri and "}" in uri
            
            # Register the resource
            self.resources[uri] = ResourceDefinition(
                uri=uri,
                name=resource_name,
                description=resource_description,
                handler=func,
                is_template=is_template
            )
            
            logger.info(f"Registered {'template ' if is_template else ''}resource: {uri}")
            
            # Return the original function
            return func
        
        return decorator
    
    async def call_tool(self, tool_name: str, params: Dict[str, Any]) -> MCPResponse:
        """
        Call a tool by name with parameters.
        
        Args:
            tool_name: Tool name
            params: Tool parameters
            
        Returns:
            Tool response
            
        Raises:
            ValueError: If tool is not found
        """
        # Check if tool exists
        if tool_name not in self.tools:
            raise ValueError(f"Tool not found: {tool_name}")
        
        # Get tool definition
        tool = self.tools[tool_name]
        
        try:
            # Call the handler function
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**params)
            else:
                result = tool.handler(**params)
            
            # Format the response
            return _format_response(result)
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return error_response(f"Error calling tool {tool_name}: {str(e)}")
    
    async def get_resource(self, uri: str) -> MCPResponse:
        """
        Get a resource by URI.
        
        Args:
            uri: Resource URI
            
        Returns:
            Resource response
            
        Raises:
            ValueError: If resource is not found
        """
        # Check if direct resource match
        if uri in self.resources:
            resource = self.resources[uri]
            try:
                # Call the handler function with no arguments
                if asyncio.iscoroutinefunction(resource.handler):
                    result = await resource.handler()
                else:
                    result = resource.handler()
                
                # Format the response
                return _format_response(result)
            except Exception as e:
                logger.error(f"Error getting resource {uri}: {e}")
                return error_response(f"Error getting resource {uri}: {str(e)}")
        
        # Check template resources
        for resource_uri, resource in self.resources.items():
            if resource.is_template:
                params = resource.matches_uri(uri)
                if params is not None:
                    try:
                        # Call the handler function with extracted parameters
                        if asyncio.iscoroutinefunction(resource.handler):
                            result = await resource.handler(**params)
                        else:
                            result = resource.handler(**params)
                        
                        # Format the response
                        return _format_response(result)
                    except Exception as e:
                        logger.error(f"Error getting resource {uri}: {e}")
                        return error_response(f"Error getting resource {uri}: {str(e)}")
        
        # Resource not found
        raise ValueError(f"Resource not found: {uri}")
    
    def get_tools(self) -> List[Dict[str, Any]]:
        """
        Get all registered tools.
        
        Returns:
            List of tool definitions
        """
        return [tool.to_dict() for tool in self.tools.values()]
    
    def get_resources(self) -> List[Dict[str, Any]]:
        """
        Get all registered resources.
        
        Returns:
            List of resource definitions
        """
        return [resource.to_dict() for resource in self.resources.values()]
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get server metadata.
        
        Returns:
            Server metadata
        """
        return self.metadata.copy()
    
    def run(self, transport="fastapi", host="0.0.0.0", port=5000):
        """
        Run the MCP server.
        
        Args:
            transport: Transport to use (fastapi, etc.)
            host: Host to bind to
            port: Port to listen on
        """
        if transport == "fastapi":
            from .transport.fastapi import create_fastapi_app
            app = create_fastapi_app(self)
            
            # Run with uvicorn
            import uvicorn
            uvicorn.run(app, host=host, port=port)
        else:
            raise ValueError(f"Unsupported transport: {transport}")
    
    @classmethod
    def as_proxy(cls, mcp_client, name=None):
        """
        Create a FastMCP server that acts as a proxy to another MCP server.
        
        Args:
            mcp_client: MCP client to proxy to
            name: Optional server name
            
        Returns:
            FastMCP server instance
        """
        from .proxy import create_proxy_server
        return create_proxy_server(mcp_client, name)