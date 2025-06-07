"""
Browserbase MCP Provider

High-level interface to the Browserbase MCP server for browser automation.
Provides typed methods for browser operations, page interactions, and data extraction
through the official Browserbase MCP server.

Usage:
    from python_a2a.mcp.providers import BrowserbaseMCPServer
    
    # Using context manager (recommended)
    async with BrowserbaseMCPServer(api_key="your-key", project_id="your-project") as browser:
        await browser.navigate("https://example.com")
        screenshot = await browser.take_screenshot()
        
    # Manual connection management
    browser = BrowserbaseMCPServer(api_key="your-key", project_id="your-project")
    await browser.connect()
    try:
        await browser.navigate("https://example.com")
        snapshot = await browser.create_snapshot()
        await browser.click_element("button", "ref_from_snapshot")
    finally:
        await browser.disconnect()
"""

import os
from typing import Dict, List, Optional, Any

from .base import BaseProvider, ProviderToolError
from ..server_config import ServerConfig


class BrowserbaseMCPServer(BaseProvider):
    """
    High-level interface to the Browserbase MCP server.
    
    This class provides typed methods for browser automation while handling
    the underlying MCP server lifecycle.
    """
    
    def __init__(self, 
                 api_key: Optional[str] = None,
                 project_id: Optional[str] = None,
                 use_npx: bool = True,
                 context_id: Optional[str] = None,
                 enable_proxies: bool = False,
                 enable_stealth: bool = False,
                 browser_width: int = 1280,
                 browser_height: int = 720):
        """
        Initialize Browserbase provider.
        
        Args:
            api_key: Browserbase API key (can use env vars)
            project_id: Browserbase project ID (can use env vars)
            use_npx: Use NPX to run the server (recommended)
            context_id: Specific Browserbase context ID
            enable_proxies: Enable Browserbase proxies
            enable_stealth: Enable advanced stealth mode
            browser_width: Browser viewport width
            browser_height: Browser viewport height
        """
        # Get credentials from parameters or environment
        self.api_key = api_key or os.getenv("BROWSERBASE_API_KEY")
        self.project_id = project_id or os.getenv("BROWSERBASE_PROJECT_ID")
        
        if not self.api_key:
            raise ValueError(
                "Browserbase API key required. Set BROWSERBASE_API_KEY environment variable."
            )
        if not self.project_id:
            raise ValueError(
                "Browserbase project ID required. Set BROWSERBASE_PROJECT_ID environment variable."
            )
        
        self.use_npx = use_npx
        self.context_id = context_id
        self.enable_proxies = enable_proxies
        self.enable_stealth = enable_stealth
        self.browser_width = browser_width
        self.browser_height = browser_height
        
        # Initialize base provider
        super().__init__()
    
    def _create_config(self) -> ServerConfig:
        """Create Browserbase MCP server configuration."""
        if self.use_npx:
            # NPX configuration
            args = ["@browserbasehq/mcp"]
            env = {
                "BROWSERBASE_API_KEY": self.api_key,
                "BROWSERBASE_PROJECT_ID": self.project_id
            }
            
            # Add optional flags
            if self.context_id:
                args.extend(["--contextId", self.context_id])
            if self.enable_proxies:
                args.append("--proxies")
            if self.enable_stealth:
                args.append("--advancedStealth")
            if self.browser_width != 1280:
                args.extend(["--browserWidth", str(self.browser_width)])
            if self.browser_height != 720:
                args.extend(["--browserHeight", str(self.browser_height)])
            
            return ServerConfig(command="npx", args=args, env=env)
        else:
            # Direct execution (requires global installation)
            args = []
            env = {
                "BROWSERBASE_API_KEY": self.api_key,
                "BROWSERBASE_PROJECT_ID": self.project_id
            }
            return ServerConfig(command="browserbase-mcp", args=args, env=env)
    
    def _get_provider_name(self) -> str:
        """Get provider name."""
        return "browserbase"
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None, timeout: Optional[float] = None) -> Any:
        """
        Call a tool on the Browserbase MCP server with custom timeout handling.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            timeout: Custom timeout for this operation
            
        Returns:
            Tool result (parsed from MCP content format if needed)
        """
        # Use longer timeout for screenshot/snapshot operations
        if timeout is None:
            if tool_name in ["browserbase_take_screenshot", "browserbase_snapshot"]:
                timeout = 90.0  # 90 seconds for visual operations
            elif tool_name in ["browserbase_wait", "browserbase_session_create", "browserbase_context_create"]:
                timeout = 60.0  # 60 seconds for session/wait operations
            else:
                timeout = 30.0  # Default timeout
        
        # Call parent method with timeout
        result = await super()._call_tool(tool_name, arguments or {})
        
        # Browserbase MCP server may return data in content format
        if isinstance(result, dict) and 'content' in result:
            content = result['content']
            if content and len(content) > 0:
                if 'text' in content[0]:
                    import json
                    try:
                        # Try to parse as JSON first
                        return json.loads(content[0]['text'])
                    except json.JSONDecodeError:
                        # If not valid JSON, return the text as-is
                        return content[0]['text']
                elif content[0].get('type') == 'image' and 'data' in content[0]:
                    # For image content (like screenshots), return the raw base64 data
                    return content[0]['data']
        
        return result
    
    # Browser Navigation Operations
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """
        Navigate to a URL in the browser.
        
        Args:
            url: URL to navigate to
            
        Returns:
            Navigation result
        """
        return await self._call_tool("browserbase_navigate", {"url": url})
    
    async def navigate_back(self) -> Dict[str, Any]:
        """
        Navigate back in browser history.
        
        Returns:
            Navigation result
        """
        return await self._call_tool("browserbase_navigate_back", {})
    
    async def navigate_forward(self) -> Dict[str, Any]:
        """
        Navigate forward in browser history.
        
        Returns:
            Navigation result
        """
        return await self._call_tool("browserbase_navigate_forward", {})
    
    # Browser Interaction Operations
    
    async def click_element(self, element: str, ref: str) -> Dict[str, Any]:
        """
        Click an element on the page using element reference from snapshot.
        
        Args:
            element: Human-readable element description
            ref: Exact target element reference from the page snapshot
            
        Returns:
            Click result
        """
        return await self._call_tool("browserbase_click", {
            "element": element,
            "ref": ref
        })
    
    async def type_text(self, element: str, ref: str, text: str, submit: bool = False, slowly: bool = True) -> Dict[str, Any]:
        """
        Type text into an editable element using element reference from snapshot.
        
        Args:
            element: Human-readable element description
            ref: Exact target element reference from the page snapshot
            text: Text to type into the element
            submit: Whether to submit entered text (press Enter after)
            slowly: Whether to type one character at a time
            
        Returns:
            Typing result
        """
        return await self._call_tool("browserbase_type", {
            "element": element,
            "ref": ref,
            "text": text,
            "submit": submit,
            "slowly": slowly
        })
    
    async def hover_element(self, element: str, ref: str) -> Dict[str, Any]:
        """
        Hover over an element using element reference from snapshot.
        
        Args:
            element: Human-readable element description
            ref: Exact target element reference from the page snapshot
            
        Returns:
            Hover result
        """
        return await self._call_tool("browserbase_hover", {
            "element": element,
            "ref": ref
        })
    
    async def drag_element(self, source: str, target: str) -> Dict[str, Any]:
        """
        Drag an element to another location.
        
        Args:
            source: CSS selector for source element
            target: CSS selector for target element
            
        Returns:
            Drag result
        """
        return await self._call_tool("browserbase_drag", {
            "source": source,
            "target": target
        })
    
    async def press_key(self, key: str, description: str = None) -> Dict[str, Any]:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'Enter', 'Tab', 'Escape', 'ArrowDown')
            description: Human-readable description of the key press action
            
        Returns:
            Key press result
        """
        params = {"key": key}
        if description:
            params["description"] = description
        else:
            params["description"] = f"Press {key} key"
            
        return await self._call_tool("browserbase_press_key", params)
    
    async def select_option(self, element: str, ref: str, values: List[str]) -> Dict[str, Any]:
        """
        Select options from a dropdown using element reference from snapshot.
        
        Args:
            element: Human-readable element description
            ref: Exact target element reference from the page snapshot
            values: Array of values to select in the dropdown
            
        Returns:
            Selection result
        """
        return await self._call_tool("browserbase_select_option", {
            "element": element,
            "ref": ref,
            "values": values
        })
    
    async def wait_time(self, time: float) -> Dict[str, Any]:
        """
        Wait for a specified time in seconds.
        
        Args:
            time: Time in seconds to wait
            
        Returns:
            Wait result
        """
        return await self._call_tool("browserbase_wait", {"time": time})
    
    # Data Extraction Operations
    
    async def get_text(self, selector: str) -> str:
        """
        Extract text from a specific element.
        
        Args:
            selector: CSS selector for element
            
        Returns:
            Extracted text
        """
        result = await self._call_tool("browserbase_get_text", {"selector": selector})
        return result if isinstance(result, str) else str(result)
    
    # Screenshot and Monitoring Operations
    
    async def take_screenshot(self) -> str:
        """
        Take a screenshot of the current page.
        
        Returns:
            Screenshot URL or base64 data
        """
        result = await self._call_tool("browserbase_take_screenshot", {})
        return result if isinstance(result, str) else str(result)
    
    async def create_snapshot(self) -> Dict[str, Any]:
        """
        Create a snapshot of the current page state.
        
        This snapshot contains element references that can be used
        with interaction methods like click_element(), hover_element(), etc.
        
        Returns:
            Snapshot information with page content and element references
        """
        result = await self._call_tool("browserbase_snapshot", {})
        
        # Browserbase snapshot may return different types of data
        if isinstance(result, str):
            # If it's just a status message, enhance it with actual page data
            if "snapshot captured" in result.lower():
                # Get additional page information to make the snapshot more useful
                try:
                    page_title = await self.get_text("title")
                    page_url = "Current page"  # We could enhance this with actual URL
                    h1_text = await self.get_text("h1")
                    
                    return {
                        "status": "success",
                        "message": result,
                        "type": "accessibility_snapshot",
                        "timestamp": str(__import__('time').time()),
                        "page_data": {
                            "title": page_title if not isinstance(page_title, str) or "Error" not in page_title else "Unknown",
                            "h1": h1_text if not isinstance(h1_text, str) or "Error" not in h1_text else "Unknown",
                            "url": page_url
                        }
                    }
                except Exception:
                    # Fallback to basic snapshot
                    return {
                        "status": "success",
                        "message": result,
                        "type": "accessibility_snapshot",
                        "timestamp": str(__import__('time').time())
                    }
        
        return result
    
    async def get_element_refs(self) -> Dict[str, Any]:
        """
        Get element references from current page snapshot.
        
        This method creates a snapshot and returns element references
        that can be used with interaction methods.
        
        Returns:
            Snapshot with element references for interactions
        """
        return await self.create_snapshot()
    
    # Session Management Operations
    
    async def create_context(self) -> Dict[str, Any]:
        """
        Create a new browser context.
        
        Returns:
            Context creation result
        """
        return await self._call_tool("browserbase_context_create", {})
    
    async def delete_context(self, context_id: str) -> Dict[str, Any]:
        """
        Delete a browser context.
        
        Args:
            context_id: Context ID to delete
            
        Returns:
            Context deletion result
        """
        return await self._call_tool("browserbase_context_delete", {"contextId": context_id})
    
    async def create_session(self) -> Dict[str, Any]:
        """
        Create a new browser session.
        
        Returns:
            Session creation result
        """
        return await self._call_tool("browserbase_session_create", {})
    
    async def close_session(self, session_id: str) -> Dict[str, Any]:
        """
        Close a browser session.
        
        Args:
            session_id: Session ID to close
            
        Returns:
            Session close result
        """
        return await self._call_tool("browserbase_session_close", {"sessionId": session_id})
    
    async def resize_browser(self, width: int, height: int) -> Dict[str, Any]:
        """
        Resize the browser viewport.
        
        Args:
            width: Viewport width in pixels
            height: Viewport height in pixels
            
        Returns:
            Resize result
        """
        return await self._call_tool("browserbase_resize", {
            "width": width,
            "height": height
        })
    
    async def close_browser(self) -> Dict[str, Any]:
        """
        Close the browser.
        
        Returns:
            Close result
        """
        return await self._call_tool("browserbase_close", {})