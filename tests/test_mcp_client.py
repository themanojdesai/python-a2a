"""
Tests for the MCP client implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from python_a2a.mcp import MCPClient, MCPError, JSONRPCError
from python_a2a.mcp.client_transport import Transport, StdioTransport, SSETransport


@pytest.mark.asyncio
async def test_mcp_client_stdio_transport():
    """Test MCPClient with stdio transport"""
    # Create client with stdio transport
    client = MCPClient(command=["echo", "test"])
    
    # Verify transport type
    assert isinstance(client.transport, StdioTransport)
    assert client.transport.command == ["echo", "test"]


@pytest.mark.asyncio
async def test_mcp_client_sse_transport():
    """Test MCPClient with SSE transport"""
    # Create client with SSE transport
    client = MCPClient(server_url="https://example.com/mcp")
    
    # Verify transport type
    assert isinstance(client.transport, SSETransport)
    assert client.transport.url == "https://example.com/mcp"


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """Test MCP client initialization handshake"""
    # Mock transport
    mock_transport = AsyncMock()
    
    # Mock responses
    mock_transport.send_request.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "protocolVersion": "2024-11-05",
            "serverInfo": {
                "name": "Test Server",
                "version": "1.0.0"
            },
            "capabilities": {
                "tools": {},
                "resources": {}
            }
        }
    }
    
    # Create client with mocked transport
    client = MCPClient(server_url="https://example.com/mcp")
    client.transport = mock_transport
    
    # Connect and initialize
    await client.connect()
    await client._initialize()
    
    # Verify initialization
    assert client.initialized
    assert client.server_info.name == "Test Server"
    assert client.server_info.version == "1.0.0"
    
    # Verify correct requests were sent
    assert mock_transport.send_request.call_count == 1
    assert mock_transport.send_notification.call_count == 1
    
    # Check initialize request
    init_request = mock_transport.send_request.call_args[0][0]
    assert init_request["method"] == "initialize"
    assert init_request["params"]["protocolVersion"] == "2024-11-05"
    
    # Check initialized notification
    init_notif = mock_transport.send_notification.call_args[0][0]
    assert init_notif["method"] == "initialized"


@pytest.mark.asyncio
async def test_mcp_client_get_tools():
    """Test getting tools from MCP server"""
    # Mock transport
    mock_transport = AsyncMock()
    
    # Mock tool list response
    mock_transport.send_request.side_effect = [
        # Initialize response
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "Test", "version": "1.0.0"},
                "capabilities": {}
            }
        },
        # Tools list response
        {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "A test tool",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "param": {"type": "string"}
                            }
                        }
                    }
                ]
            }
        }
    ]
    
    # Create client
    client = MCPClient(server_url="https://example.com/mcp")
    client.transport = mock_transport
    
    # Get tools
    tools = await client.get_tools()
    
    # Verify tools
    assert len(tools) == 1
    assert tools[0]["name"] == "test_tool"
    assert tools[0]["description"] == "A test tool"


@pytest.mark.asyncio
async def test_mcp_client_call_tool():
    """Test calling a tool on MCP server"""
    # Mock transport
    mock_transport = AsyncMock()
    
    # Mock responses
    mock_transport.send_request.side_effect = [
        # Initialize response
        {
            "jsonrpc": "2.0",
            "id": 1,
            "result": {
                "protocolVersion": "2024-11-05",
                "serverInfo": {"name": "Test", "version": "1.0.0"},
                "capabilities": {}
            }
        },
        # Tool call response
        {
            "jsonrpc": "2.0",
            "id": 2,
            "result": {
                "content": [
                    {
                        "type": "text",
                        "text": "Tool result"
                    }
                ]
            }
        }
    ]
    
    # Create client
    client = MCPClient(server_url="https://example.com/mcp")
    client.transport = mock_transport
    
    # Call tool
    result = await client.call_tool("test_tool", param="value")
    
    # Verify result
    assert result == "Tool result"
    
    # Verify request
    call_request = mock_transport.send_request.call_args_list[1][0][0]
    assert call_request["method"] == "tools/call"
    assert call_request["params"]["name"] == "test_tool"
    assert call_request["params"]["arguments"] == {"param": "value"}


@pytest.mark.asyncio
async def test_mcp_client_error_handling():
    """Test error handling in MCP client"""
    # Mock transport
    mock_transport = AsyncMock()
    
    # Mock error response
    mock_transport.send_request.return_value = {
        "jsonrpc": "2.0",
        "id": 1,
        "error": {
            "code": -32601,
            "message": "Method not found"
        }
    }
    
    # Create client
    client = MCPClient(server_url="https://example.com/mcp")
    client.transport = mock_transport
    client._connected = True
    client.initialized = True
    
    # Test error handling
    with pytest.raises(JSONRPCError) as exc_info:
        await client.get_tools()
    
    assert exc_info.value.code == -32601
    assert exc_info.value.message == "Method not found"


@pytest.mark.asyncio
async def test_mcp_client_legacy_compatibility():
    """Test legacy method compatibility"""
    # Create client
    client = MCPClient(
        server_url="https://example.com/mcp",
        max_retries=5,  # Legacy parameter
        retry_delay=2.0,  # Legacy parameter
        auth={"type": "bearer", "token": "test-token"}  # Legacy auth
    )
    
    # Verify legacy parameters are stored
    assert client.max_retries == 5
    assert client.retry_delay == 2.0
    assert client.headers["Authorization"] == "Bearer test-token"


def test_transport_creation():
    """Test transport creation logic"""
    from python_a2a.mcp.client_transport import create_transport
    
    # Test stdio transport
    transport = create_transport(command=["test"])
    assert isinstance(transport, StdioTransport)
    
    # Test SSE transport
    transport = create_transport(url="https://example.com")
    assert isinstance(transport, SSETransport)
    
    # Test error when neither provided
    with pytest.raises(ValueError):
        create_transport()