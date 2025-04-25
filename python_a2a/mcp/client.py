"""
Client for communicating with MCP servers.
"""

import asyncio
import httpx
import json
import logging
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class MCPError(Exception):
    """Base error for MCP-related issues"""
    pass

class MCPConnectionError(MCPError):
    """Error connecting to MCP server"""
    pass

class MCPTimeoutError(MCPError):
    """Timeout during MCP request"""
    pass

class MCPToolError(MCPError):
    """Error executing an MCP tool"""
    pass

class MCPTools:
    """Container for MCP tool information with cache management"""
    
    def __init__(self, tools: List[Dict[str, Any]], 
                 timestamp: Optional[datetime] = None,
                 ttl: int = 3600):  # Default TTL of 1 hour
        """
        Initialize tools container
        
        Args:
            tools: List of tool definitions
            timestamp: When the tools were fetched
            ttl: Time-to-live in seconds
        """
        self.tools = tools
        self.timestamp = timestamp or datetime.now()
        self.ttl = ttl
    
    def is_stale(self) -> bool:
        """Check if the cached tools are stale"""
        return datetime.now() > self.timestamp + timedelta(seconds=self.ttl)

class MCPClient:
    """Client for interacting with MCP servers with enhanced features"""
    
    def __init__(
        self, 
        server_url: str, 
        timeout: int = 30,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        headers: Optional[Dict[str, str]] = None,
        auth: Optional[Dict[str, Any]] = None,
        tools_ttl: int = 3600  # 1 hour cache TTL by default
    ):
        """
        Initialize an MCP client
        
        Args:
            server_url: URL of the MCP server
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries (will be exponentially increased)
            headers: Optional HTTP headers for requests
            auth: Optional authentication configuration
            tools_ttl: Time-to-live for tools cache in seconds
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.headers = headers or {}
        self.auth = auth
        self.tools_ttl = tools_ttl
        
        # Set up default headers
        if "Content-Type" not in self.headers:
            self.headers["Content-Type"] = "application/json"
        if "Accept" not in self.headers:
            self.headers["Accept"] = "application/json"
        
        # Create HTTP client with limits for production use
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers=self.headers,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
        )
        
        # Set up authentication if provided
        if auth:
            self._setup_auth(auth)
        
        # Tools cache
        self._tools_cache = None
        
    def _setup_auth(self, auth: Dict[str, Any]):
        """
        Set up authentication for the client
        
        Args:
            auth: Authentication configuration
        """
        auth_type = auth.get("type", "").lower()
        
        if auth_type == "basic":
            username = auth.get("username", "")
            password = auth.get("password", "")
            self.client.auth = (username, password)
        
        elif auth_type == "bearer":
            token = auth.get("token", "")
            self.headers["Authorization"] = f"Bearer {token}"
            self.client = httpx.AsyncClient(
                timeout=self.timeout,
                headers=self.headers,
                limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
            )
        
        elif auth_type == "api_key":
            key = auth.get("key", "")
            key_name = auth.get("key_name", "X-API-Key")
            location = auth.get("location", "header")
            
            if location == "header":
                self.headers[key_name] = key
                self.client = httpx.AsyncClient(
                    timeout=self.timeout,
                    headers=self.headers,
                    limits=httpx.Limits(max_connections=100, max_keepalive_connections=20)
                )
            elif location == "query":
                self.client.params = {key_name: key}
        
    async def close(self):
        """Close the underlying HTTP client"""
        await self.client.aclose()
        
    async def get_tools(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get available tools from the MCP server
        
        Args:
            force_refresh: Force a refresh of the tools cache
            
        Returns:
            List of available tools with their metadata
            
        Raises:
            MCPConnectionError: If connection to the server fails
            MCPTimeoutError: If the request times out
            MCPError: For other errors
        """
        # Return cached tools if available and not stale
        if self._tools_cache is not None and not force_refresh:
            if not self._tools_cache.is_stale():
                return self._tools_cache.tools
            logger.debug("Tools cache is stale, refreshing")
        
        retry_count = 0
        delay = self.retry_delay
        
        while retry_count <= self.max_retries:
            try:
                response = await self.client.get(f"{self.server_url}/tools")
                response.raise_for_status()
                
                tools = response.json()
                self._tools_cache = MCPTools(tools, ttl=self.tools_ttl)
                return tools
                
            except httpx.TimeoutException as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    logger.error(f"Timeout getting tools from MCP server after {self.max_retries} retries")
                    raise MCPTimeoutError(f"Timeout getting tools from MCP server: {str(e)}")
                
                logger.warning(f"Timeout getting tools from MCP server, retrying ({retry_count}/{self.max_retries})")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error getting tools from MCP server: {e}")
                raise MCPConnectionError(f"HTTP error getting tools from MCP server: {e.response.status_code} - {e.response.text}")
                
            except httpx.RequestError as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    logger.error(f"Request error getting tools from MCP server after {self.max_retries} retries")
                    raise MCPConnectionError(f"Request error getting tools from MCP server: {str(e)}")
                
                logger.warning(f"Request error getting tools from MCP server, retrying ({retry_count}/{self.max_retries})")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
                
            except Exception as e:
                logger.error(f"Unexpected error getting tools from MCP server: {e}")
                raise MCPError(f"Failed to get tools from MCP server: {str(e)}")
            
    async def call_tool(
        self, 
        tool_name: str, 
        stream: bool = False,
        callback: Optional[Callable[[str], None]] = None,
        **params
    ) -> Any:
        """
        Call a tool on the MCP server
        
        Args:
            tool_name: Name of the tool to call
            stream: Whether to stream the response
            callback: Callback function for streaming responses
            **params: Parameters to pass to the tool
            
        Returns:
            Result from the tool
            
        Raises:
            MCPConnectionError: If connection to the server fails
            MCPTimeoutError: If the request times out
            MCPToolError: If the tool execution fails
            MCPError: For other errors
        """
        retry_count = 0
        delay = self.retry_delay
        
        while retry_count <= self.max_retries:
            try:
                if stream and callback:
                    return await self._stream_tool_call(tool_name, callback, **params)
                
                # FIXED: Changed URL pattern from /tool/{tool_name} to /tools/{tool_name} (plural)
                response = await self.client.post(
                    f"{self.server_url}/tools/{tool_name}",
                    json=params
                )
                response.raise_for_status()
                
                result = response.json()
                
                # Check for error in the response
                if isinstance(result, dict) and result.get("isError", False):
                    error_msg = "Unknown error"
                    if "content" in result and isinstance(result["content"], list):
                        for item in result["content"]:
                            if item.get("type") == "text":
                                error_msg = item.get("text", error_msg)
                                break
                    raise MCPToolError(f"Tool execution error: {error_msg}")
                
                # Process result based on MCP format
                if isinstance(result, dict) and "content" in result and isinstance(result["content"], list):
                    # Extract text content from MCP response format
                    text_content = []
                    for item in result["content"]:
                        if item.get("type") == "text":
                            text_content.append(item.get("text", ""))
                    return "\n".join(text_content)
                
                # Return raw result if not a standard format
                return result
                
            except httpx.TimeoutException as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    logger.error(f"Timeout calling MCP tool {tool_name} after {self.max_retries} retries")
                    raise MCPTimeoutError(f"Timeout calling MCP tool {tool_name}: {str(e)}")
                
                logger.warning(f"Timeout calling MCP tool {tool_name}, retrying ({retry_count}/{self.max_retries})")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
                
            except httpx.HTTPStatusError as e:
                logger.error(f"HTTP error calling MCP tool {tool_name}: {e}")
                raise MCPToolError(f"HTTP error calling MCP tool {tool_name}: {e.response.status_code} - {e.response.text}")
                
            except httpx.RequestError as e:
                retry_count += 1
                if retry_count > self.max_retries:
                    logger.error(f"Request error calling MCP tool {tool_name} after {self.max_retries} retries")
                    raise MCPConnectionError(f"Request error calling MCP tool {tool_name}: {str(e)}")
                
                logger.warning(f"Request error calling MCP tool {tool_name}, retrying ({retry_count}/{self.max_retries})")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
                
            except MCPToolError:
                # Don't retry tool execution errors
                raise
                
            except Exception as e:
                logger.error(f"Unexpected error calling MCP tool {tool_name}: {e}")
                raise MCPError(f"Failed to call MCP tool {tool_name}: {str(e)}")
    
    async def _stream_tool_call(
        self, 
        tool_name: str, 
        callback: Callable[[str], None],
        **params
    ) -> str:
        """
        Stream a tool call response
        
        Args:
            tool_name: Name of the tool to call
            callback: Function to call with each chunk of the response
            **params: Parameters to pass to the tool
            
        Returns:
            Complete response as a string
        """
        full_response = []
        
        # FIXED: Changed URL pattern from /tool/{tool_name} to /tools/{tool_name} (plural)
        async with self.client.stream(
            "POST",
            f"{self.server_url}/tools/{tool_name}",
            json=params
        ) as response:
            response.raise_for_status()
            
            async for chunk in response.aiter_bytes():
                chunk_str = chunk.decode("utf-8")
                full_response.append(chunk_str)
                callback(chunk_str)
                
        return "".join(full_response)
    
    def call_tool_sync(self, tool_name: str, **params) -> Any:
        """
        Call a tool synchronously
        
        Args:
            tool_name: Name of the tool to call
            **params: Parameters to pass to the tool
            
        Returns:
            Result from the tool
            
        Raises:
            MCPError: For any errors
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.call_tool(tool_name, **params))
    
    def get_tools_sync(self) -> List[Dict[str, Any]]:
        """
        Get available tools synchronously
        
        Returns:
            List of available tools with their metadata
            
        Raises:
            MCPError: For any errors
        """
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.get_tools())
            
    def get_function_specs(self) -> List[Dict[str, Any]]:
        """
        Get tool specifications in function-calling format
        
        Returns:
            List of specifications suitable for function calling
        """
        if self._tools_cache is None:
            return []
            
        function_specs = []
        
        for tool in self._tools_cache.tools:
            # Convert MCP tool spec to function spec format
            spec = {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "required": []
                }
            }
            
            # Add parameters
            for param in tool.get("parameters", []):
                spec["parameters"]["properties"][param["name"]] = {
                    "type": param.get("type", "string"),
                    "description": param.get("description", "")
                }
                
                if param.get("required", False):
                    spec["parameters"]["required"].append(param["name"])
                    
            function_specs.append(spec)
            
        return function_specs