"""
MCP Server Implementation following 2025-03-26 specification.

This module provides a complete MCP server implementation with support for:
- Tools (executable functions)
- Resources (data and content)
- Prompts (templated messages)
- Proper capability negotiation and lifecycle management

Designed for production use by millions of users with robust validation.
"""

import asyncio
import inspect
import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union, Callable, Set
from enum import Enum

from .protocol import (
    MCPProtocolHandler,
    MCPProtocolError,
    JSONRPCRequest,
    JSONRPCResponse,
    JSONRPCError,
    JSONRPCErrorCode,
    MCPImplementationInfo,
    MCPCapabilities,
    MCPContent,
    create_text_content
)
from .connection import MCPMessageHandler, MCPConnection

logger = logging.getLogger(__name__)


@dataclass
class MCPTool:
    """MCP tool definition following specification."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Callable
    # Tool annotations for behavior metadata
    annotations: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP protocol format."""
        result = {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema
        }
        if self.annotations:
            result["annotations"] = self.annotations
        return result
    
    def validate_arguments(self, arguments: Dict[str, Any]) -> None:
        """Validate tool arguments against schema."""
        # Basic validation - could be extended with jsonschema
        schema = self.input_schema
        
        if schema.get("type") == "object":
            properties = schema.get("properties", {})
            required = schema.get("required", [])
            
            # Check required properties
            for prop in required:
                if prop not in arguments:
                    raise MCPProtocolError(f"Missing required argument: {prop}")
            
            # Check argument types
            for arg_name, arg_value in arguments.items():
                if arg_name in properties:
                    prop_schema = properties[arg_name]
                    expected_type = prop_schema.get("type")
                    
                    if expected_type and not self._check_type(arg_value, expected_type):
                        raise MCPProtocolError(
                            f"Argument {arg_name} has wrong type, expected {expected_type}"
                        )
    
    def _check_type(self, value: Any, expected_type: str) -> bool:
        """Check if value matches expected JSON schema type."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }
        
        expected_python_type = type_map.get(expected_type)
        if expected_python_type:
            return isinstance(value, expected_python_type)
        
        return True  # Unknown type, accept


@dataclass
class MCPResource:
    """MCP resource definition following specification."""
    uri: str
    name: str
    description: str
    handler: Callable
    mime_type: Optional[str] = None
    # For template resources
    uri_template: Optional[str] = None
    template_params: Optional[List[Dict[str, Any]]] = None
    
    @property
    def is_template(self) -> bool:
        """Check if this is a template resource."""
        return self.uri_template is not None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP protocol format."""
        if self.is_template:
            result = {
                "uriTemplate": self.uri_template,
                "name": self.name,
                "description": self.description
            }
            if self.template_params:
                result["arguments"] = self.template_params
        else:
            result = {
                "uri": self.uri,
                "name": self.name,
                "description": self.description
            }
            if self.mime_type:
                result["mimeType"] = self.mime_type
        
        return result
    
    def matches_uri(self, uri: str) -> Optional[Dict[str, str]]:
        """Check if URI matches this resource and extract parameters."""
        if not self.is_template:
            return {} if uri == self.uri else None
        
        # Simple template matching - could be enhanced
        import re
        
        # Convert template to regex
        pattern = self.uri_template
        param_names = []
        
        def replace_param(match):
            param_name = match.group(1).split(':')[0]
            param_names.append(param_name)
            return f"(?P<{param_name}>[^/]+)"
        
        pattern = re.sub(r'{([^{}]+)}', replace_param, pattern)
        pattern = f"^{pattern}$"
        
        match = re.match(pattern, uri)
        if match:
            return match.groupdict()
        
        return None


@dataclass
class MCPPrompt:
    """MCP prompt definition following specification."""
    name: str
    description: str
    handler: Callable
    arguments: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to MCP protocol format."""
        result = {
            "name": self.name,
            "description": self.description
        }
        if self.arguments:
            result["arguments"] = self.arguments
        return result


class MCPServerHandler(MCPMessageHandler):
    """
    MCP server message handler implementing all server capabilities.
    
    This handler processes incoming requests and routes them to appropriate
    tools, resources, or prompts based on the MCP specification.
    """
    
    def __init__(
        self,
        implementation_info: MCPImplementationInfo,
        capabilities: MCPCapabilities
    ):
        """
        Initialize server handler.
        
        Args:
            implementation_info: Server implementation details
            capabilities: Server capabilities
        """
        self.implementation_info = implementation_info
        self.capabilities = capabilities
        
        # Server state
        self.tools: Dict[str, MCPTool] = {}
        self.resources: Dict[str, MCPResource] = {}
        self.prompts: Dict[str, MCPPrompt] = {}
        
        # Protocol handler
        self.protocol = MCPProtocolHandler(
            implementation_info=implementation_info,
            capabilities=capabilities
        )
        
        logger.info(f"Initialized MCP server handler: {implementation_info.name}")
    
    def set_connection(self, connection) -> None:
        """Set the connection reference for lifecycle management."""
        self._connection = connection
    
    async def handle_request(self, request: JSONRPCRequest) -> JSONRPCResponse:
        """Handle incoming JSON-RPC request."""
        method = request.method
        params = request.params or {}
        request_id = request.id
        
        try:
            # Route based on method
            if method == "initialize":
                result = await self._handle_initialize(params)
            elif method == "tools/list":
                result = await self._handle_tools_list(params)
            elif method == "tools/call":
                result = await self._handle_tools_call(params)
            elif method == "resources/list":
                result = await self._handle_resources_list(params)
            elif method == "resources/read":
                result = await self._handle_resources_read(params)
            elif method == "prompts/list":
                result = await self._handle_prompts_list(params)
            elif method == "prompts/get":
                result = await self._handle_prompts_get(params)
            elif method == "ping":
                result = {}  # Simple ping response
            else:
                return self.protocol.create_error_response(
                    request_id,
                    JSONRPCErrorCode.METHOD_NOT_FOUND,
                    f"Method not found: {method}"
                )
            
            return self.protocol.create_response(request_id, result=result)
            
        except MCPProtocolError as e:
            logger.warning(f"Protocol error in {method}: {e}")
            return self.protocol.create_error_response(
                request_id,
                JSONRPCErrorCode.INVALID_PARAMS,
                str(e)
            )
        except Exception as e:
            logger.error(f"Internal error in {method}: {e}")
            return self.protocol.create_error_response(
                request_id,
                JSONRPCErrorCode.INTERNAL_ERROR,
                "Internal server error"
            )
    
    async def handle_notification(self, notification: JSONRPCRequest) -> None:
        """Handle incoming JSON-RPC notification."""
        method = notification.method
        params = notification.params or {}
        
        try:
            if method == "initialized":
                await self._handle_initialized(params)
            elif method == "notifications/cancelled":
                await self._handle_cancelled(params)
            else:
                logger.warning(f"Unknown notification method: {method}")
                
        except Exception as e:
            logger.error(f"Error handling notification {method}: {e}")
    
    async def _handle_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle initialize request."""
        # Basic parameter validation
        if not isinstance(params, dict):
            raise MCPProtocolError("Initialize params must be an object")
        
        # Extract client info
        protocol_version = params.get("protocolVersion")
        client_capabilities = MCPCapabilities.from_dict(params.get("capabilities", {}))
        client_info = MCPImplementationInfo.from_dict(params.get("clientInfo", {}))
        
        # Store peer info for later use in initialized notification
        self._peer_info = client_info
        self._peer_capabilities = client_capabilities
        
        logger.info(f"Initialize request from {client_info.name} v{client_info.version}")
        
        # Negotiate protocol version
        if protocol_version not in self.protocol.SUPPORTED_VERSIONS:
            raise MCPProtocolError(f"Unsupported protocol version: {protocol_version}")
        
        # Return server capabilities
        return {
            "protocolVersion": protocol_version,
            "capabilities": self.capabilities.to_dict(),
            "serverInfo": self.implementation_info.to_dict()
        }
    
    async def _handle_initialized(self, params: Dict[str, Any]) -> None:
        """Handle initialized notification."""
        logger.info("Client initialization completed")
        # Notify connection that initialization is complete
        if hasattr(self, '_connection'):
            # Extract peer info from the previous initialize request
            peer_info = getattr(self, '_peer_info', MCPImplementationInfo("unknown", "unknown"))
            peer_capabilities = getattr(self, '_peer_capabilities', MCPCapabilities())
            self._connection.complete_initialization(peer_info, peer_capabilities)
    
    async def _handle_cancelled(self, params: Dict[str, Any]) -> None:
        """Handle request cancellation notification."""
        request_id = params.get("requestId")
        logger.info(f"Request cancelled: {request_id}")
    
    async def _handle_tools_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/list request."""
        # Support pagination
        cursor = params.get("cursor")
        
        tools_list = list(self.tools.values())
        
        # Simple pagination implementation
        if cursor:
            try:
                start_idx = int(cursor)
                tools_list = tools_list[start_idx:]
            except (ValueError, IndexError):
                pass
        
        # Limit results (could be configurable)
        page_size = 100
        if len(tools_list) > page_size:
            next_cursor = str(page_size)
            tools_list = tools_list[:page_size]
        else:
            next_cursor = None
        
        result = {
            "tools": [tool.to_dict() for tool in tools_list]
        }
        
        if next_cursor:
            result["nextCursor"] = next_cursor
        
        return result
    
    async def _handle_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle tools/call request."""
        # Basic validation
        if "name" not in params:
            raise MCPProtocolError("Missing required parameter: name")
        
        tool_name = params["name"]
        arguments = params.get("arguments", {})
        
        if tool_name not in self.tools:
            raise MCPProtocolError(f"Tool not found: {tool_name}")
        
        tool = self.tools[tool_name]
        
        # Validate arguments
        tool.validate_arguments(arguments)
        
        try:
            # Call tool handler
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool.handler(**arguments))
            
            # Format result as content
            content = self._format_tool_result(result)
            
            return {
                "content": content,
                "isError": False
            }
            
        except Exception as e:
            logger.error(f"Tool {tool_name} failed: {e}")
            error_content = [create_text_content(f"Tool error: {str(e)}").to_dict()]
            
            return {
                "content": error_content,
                "isError": True
            }
    
    async def _handle_resources_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/list request."""
        # Support pagination similar to tools
        cursor = params.get("cursor")
        
        resources_list = list(self.resources.values())
        
        if cursor:
            try:
                start_idx = int(cursor)
                resources_list = resources_list[start_idx:]
            except (ValueError, IndexError):
                pass
        
        page_size = 100
        if len(resources_list) > page_size:
            next_cursor = str(page_size)
            resources_list = resources_list[:page_size]
        else:
            next_cursor = None
        
        result = {
            "resources": [resource.to_dict() for resource in resources_list]
        }
        
        if next_cursor:
            result["nextCursor"] = next_cursor
        
        return result
    
    async def _handle_resources_read(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle resources/read request."""
        uri = params.get("uri")
        if not uri:
            raise MCPProtocolError("Missing uri parameter")
        
        # Find matching resource
        resource = None
        template_params = {}
        
        # Check exact URI match first
        for res in self.resources.values():
            if not res.is_template and res.uri == uri:
                resource = res
                break
        
        # Check template matches
        if not resource:
            for res in self.resources.values():
                if res.is_template:
                    params_match = res.matches_uri(uri)
                    if params_match is not None:
                        resource = res
                        template_params = params_match
                        break
        
        if not resource:
            raise MCPProtocolError(f"Resource not found: {uri}")
        
        try:
            # Call resource handler
            if template_params:
                if asyncio.iscoroutinefunction(resource.handler):
                    result = await resource.handler(**template_params)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, lambda: resource.handler(**template_params)
                    )
            else:
                if asyncio.iscoroutinefunction(resource.handler):
                    result = await resource.handler()
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(None, resource.handler)
            
            # Format result as content
            content = self._format_resource_result(result)
            
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": resource.mime_type,
                        "content": content
                    }
                ]
            }
            
        except Exception as e:
            logger.error(f"Resource {uri} failed: {e}")
            raise MCPProtocolError(f"Resource error: {str(e)}")
    
    async def _handle_prompts_list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/list request."""
        cursor = params.get("cursor")
        
        prompts_list = list(self.prompts.values())
        
        if cursor:
            try:
                start_idx = int(cursor)
                prompts_list = prompts_list[start_idx:]
            except (ValueError, IndexError):
                pass
        
        page_size = 100
        if len(prompts_list) > page_size:
            next_cursor = str(page_size)
            prompts_list = prompts_list[:page_size]
        else:
            next_cursor = None
        
        result = {
            "prompts": [prompt.to_dict() for prompt in prompts_list]
        }
        
        if next_cursor:
            result["nextCursor"] = next_cursor
        
        return result
    
    async def _handle_prompts_get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle prompts/get request."""
        name = params.get("name")
        arguments = params.get("arguments", {})
        
        if not name:
            raise MCPProtocolError("Missing name parameter")
        
        if name not in self.prompts:
            raise MCPProtocolError(f"Prompt not found: {name}")
        
        prompt = self.prompts[name]
        
        try:
            # Call prompt handler
            if asyncio.iscoroutinefunction(prompt.handler):
                result = await prompt.handler(**arguments)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: prompt.handler(**arguments)
                )
            
            # Format result as messages
            messages = self._format_prompt_result(result)
            
            return {
                "description": prompt.description,
                "messages": messages
            }
            
        except Exception as e:
            logger.error(f"Prompt {name} failed: {e}")
            raise MCPProtocolError(f"Prompt error: {str(e)}")
    
    def _format_tool_result(self, result: Any) -> List[Dict[str, Any]]:
        """Format tool result as MCP content."""
        if isinstance(result, list) and all(isinstance(item, MCPContent) for item in result):
            return [item.to_dict() for item in result]
        elif isinstance(result, MCPContent):
            return [result.to_dict()]
        elif isinstance(result, str):
            return [create_text_content(result).to_dict()]
        elif isinstance(result, dict):
            # Check if it's already in content format
            if "type" in result:
                return [result]
            else:
                return [create_text_content(json.dumps(result)).to_dict()]
        else:
            return [create_text_content(str(result)).to_dict()]
    
    def _format_resource_result(self, result: Any) -> List[Dict[str, Any]]:
        """Format resource result as MCP content."""
        return self._format_tool_result(result)
    
    def _format_prompt_result(self, result: Any) -> List[Dict[str, Any]]:
        """Format prompt result as MCP messages."""
        if isinstance(result, list):
            return result
        elif isinstance(result, dict):
            return [result]
        elif isinstance(result, str):
            return [{
                "role": "user",
                "content": {
                    "type": "text",
                    "text": result
                }
            }]
        else:
            return [{
                "role": "user", 
                "content": {
                    "type": "text",
                    "text": str(result)
                }
            }]
    
    def add_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: Callable,
        annotations: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a tool to the server."""
        tool = MCPTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
            annotations=annotations
        )
        self.tools[name] = tool
        logger.info(f"Added tool: {name}")
    
    def add_resource(
        self,
        uri: str,
        name: str,
        description: str,
        handler: Callable,
        mime_type: Optional[str] = None,
        uri_template: Optional[str] = None,
        template_params: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add a resource to the server."""
        resource = MCPResource(
            uri=uri,
            name=name,
            description=description,
            handler=handler,
            mime_type=mime_type,
            uri_template=uri_template,
            template_params=template_params
        )
        self.resources[uri] = resource
        logger.info(f"Added resource: {uri}")
    
    def add_prompt(
        self,
        name: str,
        description: str,
        handler: Callable,
        arguments: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        """Add a prompt to the server."""
        prompt = MCPPrompt(
            name=name,
            description=description,
            handler=handler,
            arguments=arguments
        )
        self.prompts[name] = prompt
        logger.info(f"Added prompt: {name}")


class MCPServer:
    """
    Complete MCP server implementation.
    
    This class provides a high-level interface for creating MCP servers
    with proper lifecycle management and capability handling.
    """
    
    def __init__(
        self,
        name: str,
        version: str,
        description: Optional[str] = None,
        tools_enabled: bool = True,
        resources_enabled: bool = True,
        prompts_enabled: bool = True
    ):
        """
        Initialize MCP server.
        
        Args:
            name: Server name
            version: Server version
            description: Server description
            tools_enabled: Enable tools capability
            resources_enabled: Enable resources capability
            prompts_enabled: Enable prompts capability
        """
        self.name = name
        self.version = version
        self.description = description or f"{name} MCP Server"
        
        # Build capabilities
        capabilities = MCPCapabilities()
        if tools_enabled:
            capabilities.tools = {}
        if resources_enabled:
            capabilities.resources = {}
        if prompts_enabled:
            capabilities.prompts = {}
        
        # Implementation info
        implementation_info = MCPImplementationInfo(
            name=self.name,
            version=self.version
        )
        
        # Create handler
        self.handler = MCPServerHandler(implementation_info, capabilities)
        
        logger.info(f"Created MCP server: {name} v{version}")
    
    def tool(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None,
        annotations: Optional[Dict[str, Any]] = None
    ) -> Callable:
        """Decorator to register a tool."""
        def decorator(func: Callable) -> Callable:
            tool_name = name or func.__name__
            tool_description = description or (func.__doc__ or "").strip()
            
            # Generate schema from function signature if not provided
            if schema is None:
                sig = inspect.signature(func)
                input_schema = self._generate_schema_from_signature(sig, func)
            else:
                input_schema = schema
            
            self.handler.add_tool(
                name=tool_name,
                description=tool_description,
                input_schema=input_schema,
                handler=func,
                annotations=annotations
            )
            
            return func
        
        return decorator
    
    def resource(
        self,
        uri: str,
        name: Optional[str] = None,
        description: Optional[str] = None,
        mime_type: Optional[str] = None
    ) -> Callable:
        """Decorator to register a resource."""
        def decorator(func: Callable) -> Callable:
            resource_name = name or func.__name__
            resource_description = description or (func.__doc__ or "").strip()
            
            # Check if URI is a template
            is_template = "{" in uri and "}" in uri
            uri_template = uri if is_template else None
            actual_uri = None if is_template else uri
            
            self.handler.add_resource(
                uri=actual_uri or uri,
                name=resource_name,
                description=resource_description,
                handler=func,
                mime_type=mime_type,
                uri_template=uri_template
            )
            
            return func
        
        return decorator
    
    def prompt(
        self,
        name: Optional[str] = None,
        description: Optional[str] = None,
        arguments: Optional[List[Dict[str, Any]]] = None
    ) -> Callable:
        """Decorator to register a prompt."""
        def decorator(func: Callable) -> Callable:
            prompt_name = name or func.__name__
            prompt_description = description or (func.__doc__ or "").strip()
            
            self.handler.add_prompt(
                name=prompt_name,
                description=prompt_description,
                handler=func,
                arguments=arguments
            )
            
            return func
        
        return decorator
    
    def _generate_schema_from_signature(
        self,
        sig: 'inspect.Signature',
        func: Callable
    ) -> Dict[str, Any]:
        """Generate JSON schema from function signature."""
        from typing import get_type_hints
        
        type_hints = get_type_hints(func)
        
        schema = {
            "type": "object",
            "properties": {},
            "required": []
        }
        
        for param_name, param in sig.parameters.items():
            if param_name in ("self", "cls"):
                continue
            
            # Get type information
            param_type = type_hints.get(param_name, str)
            json_type = self._python_type_to_json_type(param_type)
            
            schema["properties"][param_name] = {
                "type": json_type,
                "description": f"Parameter {param_name}"
            }
            
            # Check if required
            if param.default == param.empty:
                schema["required"].append(param_name)
        
        return schema
    
    def _python_type_to_json_type(self, python_type: type) -> str:
        """Convert Python type to JSON schema type."""
        if python_type == str:
            return "string"
        elif python_type == int:
            return "integer"
        elif python_type == float:
            return "number"
        elif python_type == bool:
            return "boolean"
        elif python_type == list:
            return "array"
        elif python_type == dict:
            return "object"
        else:
            return "string"  # Default fallback