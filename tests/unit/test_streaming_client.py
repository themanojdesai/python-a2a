"""
Tests for the StreamingClient class, focusing on content negotiation and HTML fallback.
"""

import json
import unittest
from unittest import mock
import pytest
import asyncio

try:
    import aiohttp
    HAS_AIOHTTP = True
except ImportError:
    HAS_AIOHTTP = False

from python_a2a.client.streaming import StreamingClient


class MockResponse:
    """Mock for aiohttp response."""
    def __init__(self, status=200, content_type='application/json', data=None, error=None):
        self.status = status
        self._content_type = content_type
        self._headers = {'Content-Type': content_type}
        self._data = data or {}
        self._error = error
        self._text = None
        
        if content_type == 'application/json':
            self._text = json.dumps(self._data)
        elif content_type == 'text/html':
            # Create mock HTML if we're testing HTML response
            if isinstance(self._data, dict):
                json_data = json.dumps(self._data)
                self._text = f"""
                <!DOCTYPE html>
                <html>
                <head><title>Agent Card</title></head>
                <body>
                    <h1>Agent Card</h1>
                    <pre>{json_data}</pre>
                </body>
                </html>
                """
            else:
                self._text = "<html><body>No JSON data</body></html>"
    
    async def json(self):
        """Return JSON data."""
        if self._error:
            raise self._error
        if self._content_type != 'application/json':
            raise ValueError(f"Attempt to decode JSON with unexpected mimetype: {self._content_type}")
        return self._data
    
    async def text(self):
        """Return text data."""
        return self._text
        
    async def release(self):
        """Mock release method."""
        pass
        
    @property
    def headers(self):
        """Return headers."""
        return self._headers
    
    @property
    def content(self):
        """Mock content for streaming."""
        class MockContent:
            async def iter_chunked(self, size):
                yield b'test chunk'
                
            async def iter_chunks(self):
                yield (b'test chunk', None)
                
        return MockContent()


class MockSession:
    """Mock for aiohttp ClientSession."""
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.requests = []
        
    async def get(self, url, **kwargs):
        """Mock get method."""
        self.requests.append((url, kwargs))
        
        # Get the response for this URL or a default 404
        if url in self.responses:
            return self.responses[url]
        return MockResponse(status=404)
        
    async def post(self, url, **kwargs):
        """Mock post method."""
        self.requests.append((url, kwargs))
        
        # Get the response for this URL or a default 404
        if url in self.responses:
            return self.responses[url]
        return MockResponse(status=404)
    
    async def __aenter__(self):
        """Context manager enter."""
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        pass


@pytest.mark.asyncio
@unittest.skipIf(not HAS_AIOHTTP, "aiohttp required for these tests")
class TestStreamingClient:
    """Test StreamingClient."""
    
    def setup_method(self):
        """Set up test environment."""
        self.client = StreamingClient("http://localhost:8000")
        
    @mock.patch('python_a2a.client.streaming.StreamingClient._create_session')
    async def test_check_streaming_support_json(self, mock_create_session):
        """Test checking streaming support with JSON response."""
        # Mock the agent.json response with streaming capability
        mock_response = MockResponse(
            data={
                "name": "Test Agent",
                "capabilities": {
                    "streaming": True
                }
            }
        )
        
        # Mock session with the response
        mock_session = MockSession({
            "http://localhost:8000/agent.json": mock_response
        })
        mock_create_session.return_value = mock_session
        
        # Check streaming support
        result = await self.client.check_streaming_support()
        
        # Verify results
        assert result is True
        assert len(mock_session.requests) == 1
        
        # Verify that Accept header was sent
        url, kwargs = mock_session.requests[0]
        assert url == "http://localhost:8000/agent.json"
        assert "headers" in kwargs
        assert kwargs["headers"].get("Accept") == "application/json"
    
    @mock.patch('python_a2a.client.streaming.StreamingClient._create_session')
    async def test_check_streaming_support_html(self, mock_create_session):
        """Test checking streaming support with HTML response."""
        # Mock the agent.json response as HTML with embedded JSON
        mock_response = MockResponse(
            content_type='text/html',
            data={
                "name": "Test Agent",
                "capabilities": {
                    "streaming": True
                }
            }
        )
        
        # Mock session with the response
        mock_session = MockSession({
            "http://localhost:8000/agent.json": mock_response
        })
        mock_create_session.return_value = mock_session
        
        # Check streaming support
        result = await self.client.check_streaming_support()
        
        # Verify results - should still extract JSON from HTML
        assert result is True
        
    @mock.patch('python_a2a.client.streaming.StreamingClient._create_session')
    async def test_alternate_endpoint(self, mock_create_session):
        """Test checking streaming support with alternate endpoint."""
        # Mock the agent.json response as 404
        mock_not_found = MockResponse(status=404)
        
        # Mock the alternate endpoint with streaming capability
        mock_alt_response = MockResponse(
            data={
                "name": "Test Agent",
                "capabilities": {
                    "streaming": True
                }
            }
        )
        
        # Mock session with the responses
        mock_session = MockSession({
            "http://localhost:8000/agent.json": mock_not_found,
            "http://localhost:8000/a2a/agent.json": mock_alt_response
        })
        mock_create_session.return_value = mock_session
        
        # Check streaming support
        result = await self.client.check_streaming_support()
        
        # Verify results
        assert result is True
        assert len(mock_session.requests) == 2
        
        # Verify that both endpoints were tried
        url1, _ = mock_session.requests[0]
        url2, _ = mock_session.requests[1]
        assert url1 == "http://localhost:8000/agent.json"
        assert url2 == "http://localhost:8000/a2a/agent.json"
    
    def test_extract_json_from_response(self):
        """Test extracting JSON from different response formats."""
        # Test pure JSON
        json_text = '{"name": "Test", "capabilities": {"streaming": true}}'
        result = self.client._extract_json_from_response(json_text)
        assert result == {"name": "Test", "capabilities": {"streaming": True}}
        
        # Test HTML with <pre> tag
        html_pre = '<html><pre>{"name": "Test", "capabilities": {"streaming": true}}</pre></html>'
        result = self.client._extract_json_from_response(html_pre)
        assert result == {"name": "Test", "capabilities": {"streaming": True}}
        
        # Test HTML with capabilities in text
        html_capabilities = '<html>Some text {"capabilities": {"streaming": true}} more text</html>'
        result = self.client._extract_json_from_response(html_capabilities)
        assert result == {"capabilities": {"streaming": True}}
        
        # Test HTML with div
        html_div = '<html><div>{"name": "Test"}</div></html>'
        result = self.client._extract_json_from_response(html_div)
        assert result == {"name": "Test"}
        
        # Test invalid HTML
        invalid_html = '<html>No JSON here</html>'
        result = self.client._extract_json_from_response(invalid_html)
        assert result == {}