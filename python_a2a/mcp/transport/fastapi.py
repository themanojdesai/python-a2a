import os
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

# JSON-RPC models
class JSONRPCRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

class JSONRPCResponse(BaseModel):
    jsonrpc: str = "2.0"
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    id: Optional[Any] = None

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
    allowed_origins = os.environ.get("A2A_MCP_ALLOWED_ORIGINS", "").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if allowed_origins and allowed_origins != [""] else [],
        allow_credentials=False,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization"],
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
    
    # JSON-RPC endpoint for MCP protocol compliance
    @app.post("/")
    async def json_rpc_endpoint(request: Request):
        """Handle JSON-RPC requests for MCP protocol"""
        try:
            # Parse JSON-RPC request
            body = await request.json()
            
            if not isinstance(body, dict):
                return JSONRPCResponse(
                    error={"code": -32600, "message": "Invalid Request"},
                    id=body.get("id") if isinstance(body, dict) else None
                ).dict()
            
            jsonrpc_version = body.get("jsonrpc")
            if jsonrpc_version != "2.0":
                return JSONRPCResponse(
                    error={"code": -32600, "message": "Invalid Request - jsonrpc must be '2.0'"},
                    id=body.get("id")
                ).dict()
            
            method = body.get("method")
            params = body.get("params", {})
            request_id = body.get("id")
            
            # Handle different MCP methods
            try:
                if method == "tools/list":
                    tools = mcp_server.get_tools()
                    return JSONRPCResponse(result={"tools": tools}, id=request_id).dict()
                
                elif method == "tools/call":
                    tool_name = params.get("name")
                    arguments = params.get("arguments", {})
                    
                    if not tool_name:
                        return JSONRPCResponse(
                            error={"code": -32602, "message": "Missing required parameter: name"},
                            id=request_id
                        ).dict()
                    
                    try:
                        response = await mcp_server.call_tool(tool_name, arguments)
                        return JSONRPCResponse(result=response.to_dict(), id=request_id).dict()
                    except ValueError as e:
                        return JSONRPCResponse(
                            error={"code": -32000, "message": f"Tool not found: {tool_name}"},
                            id=request_id
                        ).dict()
                    except Exception as e:
                        return JSONRPCResponse(
                            error={"code": -32603, "message": f"Internal error: {str(e)}"},
                            id=request_id
                        ).dict()
                
                elif method == "resources/list":
                    resources = mcp_server.get_resources()
                    return JSONRPCResponse(result={"resources": resources}, id=request_id).dict()
                
                elif method == "resources/read":
                    uri = params.get("uri")
                    if not uri:
                        return JSONRPCResponse(
                            error={"code": -32602, "message": "Missing required parameter: uri"},
                            id=request_id
                        ).dict()
                    
                    try:
                        response = await mcp_server.get_resource(uri)
                        return JSONRPCResponse(result=response.to_dict(), id=request_id).dict()
                    except ValueError as e:
                        return JSONRPCResponse(
                            error={"code": -32000, "message": f"Resource not found: {uri}"},
                            id=request_id
                        ).dict()
                    except Exception as e:
                        return JSONRPCResponse(
                            error={"code": -32603, "message": f"Internal error: {str(e)}"},
                            id=request_id
                        ).dict()
                
                else:
                    return JSONRPCResponse(
                        error={"code": -32601, "message": f"Method not found: {method}"},
                        id=request_id
                    ).dict()
                    
            except Exception as e:
                logger.error(f"Error handling JSON-RPC method {method}: {e}")
                return JSONRPCResponse(
                    error={"code": -32603, "message": f"Internal error: {str(e)}"},
                    id=request_id
                ).dict()
                
        except json.JSONDecodeError:
            return JSONRPCResponse(
                error={"code": -32700, "message": "Parse error"},
                id=None
            ).dict()
        except Exception as e:
            logger.error(f"Error processing JSON-RPC request: {e}")
            return JSONRPCResponse(
                error={"code": -32603, "message": f"Internal error: {str(e)}"},
                id=None
            ).dict()
    
    return app