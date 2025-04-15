"""
FastAPI transport for FastMCP.

This module provides functions to create a FastAPI app that serves an MCP server.
"""

import asyncio
import json
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from ..fastmcp import FastMCP, MCPResponse

# Configure logging
logger = logging.getLogger("python_a2a.mcp.transport.fastapi")

def create_fastapi_app(mcp_server: FastMCP) -> FastAPI:
    """
    Create a FastAPI app for an MCP server.
    
    Args:
        mcp_server: FastMCP server instance
        
    Returns:
        FastAPI app
    """
    app = FastAPI(
        title=mcp_server.name,
        description=mcp_server.description,
        version=mcp_server.version
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy"}
    
    # MCP metadata endpoint
    @app.get("/metadata")
    async def get_metadata():
        """Get MCP server metadata"""
        return mcp_server.get_metadata()
    
    # List tools endpoint
    @app.get("/tools")
    async def list_tools():
        """List all available tools"""
        return mcp_server.get_tools()
    
    # List resources endpoint
    @app.get("/resources")
    async def list_resources():
        """List all available resources"""
        return mcp_server.get_resources()
    
    # Call tool endpoint
    @app.post("/tools/{tool_name}")
    async def call_tool(tool_name: str, request: Request):
        """Call a tool with parameters"""
        # Parse request body
        try:
            params = await request.json()
        except json.JSONDecodeError:
            params = {}
        
        try:
            # Call the tool
            response = await mcp_server.call_tool(tool_name, params)
            return response.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            error_response = MCPResponse(
                content=[
                    {
                        "type": "text",
                        "text": f"Error calling tool {tool_name}: {str(e)}"
                    }
                ],
                is_error=True
            )
            return error_response.to_dict()
    
    # Get resource endpoint
    @app.get("/resources/{path:path}")
    async def get_resource(path: str):
        """Get a resource by URI"""
        try:
            # Construct complete URI
            uri = path
            
            # Get the resource
            response = await mcp_server.get_resource(uri)
            return response.to_dict()
        except ValueError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except Exception as e:
            logger.error(f"Error getting resource {uri}: {e}")
            error_response = MCPResponse(
                content=[
                    {
                        "type": "text",
                        "text": f"Error getting resource {uri}: {str(e)}"
                    }
                ],
                is_error=True
            )
            return error_response.to_dict()
    
    return app