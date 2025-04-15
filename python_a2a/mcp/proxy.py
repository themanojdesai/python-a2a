"""
Proxy functionality for FastMCP.

This module provides functions to create a FastMCP server that acts as a proxy
to another MCP server.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union

from .client import MCPClient
from .fastmcp import FastMCP, MCPResponse, text_response, error_response

# Configure logging
logger = logging.getLogger("python_a2a.mcp.proxy")

async def create_proxy_server(
    mcp_client: MCPClient, 
    name: Optional[str] = None
) -> FastMCP:
    """
    Create a FastMCP server that acts as a proxy to another MCP server.
    
    Args:
        mcp_client: MCP client to proxy to
        name: Optional server name
        
    Returns:
        FastMCP server instance
    """
    # Get server metadata
    try:
        # Try to get metadata from the server
        metadata = await mcp_client.get_metadata()
        server_name = metadata.get("name", "MCP Proxy")
        server_version = metadata.get("version", "1.0.0")
        server_description = metadata.get("description", "MCP Proxy Server")
    except Exception as e:
        logger.warning(f"Failed to get metadata from MCP server: {e}")
        server_name = "MCP Proxy"
        server_version = "1.0.0"
        server_description = "MCP Proxy Server"
    
    # Use provided name if available
    if name:
        server_name = name
    
    # Create the server
    server = FastMCP(
        name=server_name,
        version=server_version,
        description=server_description
    )
    
    # Get available tools
    try:
        tools = await mcp_client.get_tools()
        logger.info(f"Found {len(tools)} tools on target MCP server")
        
        # Register each tool as a proxy
        for tool_info in tools:
            tool_name = tool_info["name"]
            tool_description = tool_info.get("description", "")
            tool_parameters = tool_info.get("parameters", {})
            
            # Create a proxy function for this tool
            @server.tool(name=tool_name, description=tool_description)
            async def proxy_tool(**params):
                try:
                    return await mcp_client.call_tool(tool_name, **params)
                except Exception as e:
                    logger.error(f"Error proxying tool {tool_name}: {e}")
                    return error_response(f"Error proxying tool {tool_name}: {str(e)}")
    except Exception as e:
        logger.warning(f"Failed to get tools from MCP server: {e}")
    
    # Get available resources
    try:
        resources = await mcp_client.get_resources()
        logger.info(f"Found {len(resources)} resources on target MCP server")
        
        # Register each resource as a proxy
        for resource_info in resources:
            if "uri" in resource_info:
                # Static resource
                resource_uri = resource_info["uri"]
                resource_name = resource_info.get("name", "")
                resource_description = resource_info.get("description", "")
                
                @server.resource(uri=resource_uri, name=resource_name, description=resource_description)
                async def proxy_resource():
                    try:
                        return await mcp_client.get_resource(resource_uri)
                    except Exception as e:
                        logger.error(f"Error proxying resource {resource_uri}: {e}")
                        return error_response(f"Error proxying resource {resource_uri}: {str(e)}")
            
            elif "uriTemplate" in resource_info:
                # Template resource
                template_uri = resource_info["uriTemplate"]
                template_name = resource_info.get("name", "")
                template_description = resource_info.get("description", "")
                
                @server.resource(uri=template_uri, name=template_name, description=template_description)
                async def proxy_template_resource(**params):
                    try:
                        # Construct the actual URI by substituting parameters
                        actual_uri = template_uri
                        for param_name, param_value in params.items():
                            actual_uri = actual_uri.replace(f"{{{param_name}}}", str(param_value))
                        
                        return await mcp_client.get_resource(actual_uri)
                    except Exception as e:
                        logger.error(f"Error proxying template resource {template_uri}: {e}")
                        return error_response(f"Error proxying template resource {template_uri}: {str(e)}")
    except Exception as e:
        logger.warning(f"Failed to get resources from MCP server: {e}")
    
    return server

async def create_proxy_server_sync(
    mcp_client: MCPClient, 
    name: Optional[str] = None
) -> FastMCP:
    """
    Synchronous wrapper for create_proxy_server.
    
    Args:
        mcp_client: MCP client to proxy to
        name: Optional server name
        
    Returns:
        FastMCP server instance
    """
    loop = asyncio.get_event_loop()
    return await create_proxy_server(mcp_client, name)