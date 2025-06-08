"""
Playwright MCP Provider

High-level interface to the Playwright MCP server for browser automation.
Provides typed methods for browser operations, page interactions, and data extraction
through the official Playwright MCP server from Microsoft.

The provider automatically handles:
- Node.js and npm detection across platforms
- @playwright/mcp installation if needed
- Browser installation (chromium, firefox, webkit)
- MCP server lifecycle management
- Cross-platform compatibility (Windows, macOS, Linux)

Usage:
    from python_a2a.mcp.providers import PlaywrightMCPServer
    
    # Simple usage with context manager
    async with PlaywrightMCPServer() as playwright:
        await playwright.navigate("https://example.com")
        await playwright.take_screenshot("page.png")
        title = await playwright.get_page_title()
        
    # Customize browser settings
    async with PlaywrightMCPServer(
        browser="firefox", 
        headless=False,
        viewport_width=1400,
        viewport_height=900
    ) as playwright:
        await playwright.navigate("https://github.com")
        await playwright.click_element("Sign in button", "[href='/login']")
"""

import asyncio
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import tempfile

logger = logging.getLogger(__name__)


class PlaywrightMCPError(Exception):
    """Base exception for Playwright MCP provider errors."""
    pass


class PlaywrightMCPServer:
    """
    High-level interface to the Playwright MCP server.
    
    This class provides comprehensive browser automation capabilities through
    the Microsoft Playwright MCP server with automatic setup and management.
    """
    
    def __init__(self, 
                 browser: str = "chromium",
                 headless: bool = True,
                 viewport_width: int = 1280,
                 viewport_height: int = 720,
                 slow_mo: int = 0,
                 timeout: float = 30.0,
                 auto_install: bool = True):
        """
        Initialize Playwright MCP provider.
        
        Args:
            browser: Browser type ("chromium", "firefox", "webkit")
            headless: Run browser in headless mode
            viewport_width: Browser viewport width in pixels
            viewport_height: Browser viewport height in pixels
            slow_mo: Slow down operations by specified milliseconds (useful for debugging)
            timeout: Default timeout for operations in seconds
            auto_install: Automatically install missing dependencies
        """
        self.browser = browser.lower()
        self.headless = headless
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.slow_mo = slow_mo
        self.timeout = timeout
        self.auto_install = auto_install
        
        # Internal state
        self._process: Optional[subprocess.Popen] = None
        self._connected = False
        self._request_id_counter = 0
        self._node_cmd: Optional[str] = None
        self._npm_cmd: Optional[str] = None
        self._npx_cmd: Optional[str] = None
        
        # Validate browser choice
        if self.browser not in ["chromium", "firefox", "webkit"]:
            raise PlaywrightMCPError(f"Unsupported browser: {browser}. Use 'chromium', 'firefox', or 'webkit'")
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to Playwright MCP server."""
        return self._connected and self._process is not None
    
    async def connect(self) -> None:
        """Connect to Playwright MCP server with automatic setup."""
        if self._connected:
            logger.warning("Already connected to Playwright MCP server")
            return
        
        logger.info("🎭 Initializing Playwright MCP server...")
        
        try:
            # Step 1: Detect and validate Node.js environment
            await self._ensure_nodejs_environment()
            
            # Step 2: Ensure @playwright/mcp is available
            await self._ensure_playwright_mcp()
            
            # Step 3: Ensure browsers are installed
            if self.auto_install:
                await self._ensure_browsers_installed()
            
            # Step 4: Start MCP server and establish connection
            await self._start_mcp_server()
            
            logger.info(f"✅ Connected to Playwright MCP server ({self.browser})")
            
        except Exception as e:
            await self._cleanup()
            raise PlaywrightMCPError(f"Failed to connect to Playwright MCP server: {e}") from e
    
    async def disconnect(self) -> None:
        """Disconnect from Playwright MCP server."""
        if not self._connected:
            return
        
        logger.info("🔌 Disconnecting from Playwright MCP server...")
        await self._cleanup()
        logger.info("Disconnected from Playwright MCP server")
    
    async def _ensure_nodejs_environment(self) -> None:
        """Detect and validate Node.js and npm installation."""
        logger.debug("Detecting Node.js environment...")
        
        # Detect Node.js
        self._node_cmd = shutil.which("node")
        if not self._node_cmd:
            # Try platform-specific common paths
            common_paths = self._get_common_nodejs_paths()
            for path in common_paths:
                if os.path.exists(path):
                    self._node_cmd = path
                    break
        
        if not self._node_cmd:
            raise PlaywrightMCPError(
                "Node.js not found. Please install Node.js from https://nodejs.org/\n"
                "Required for Playwright MCP server functionality."
            )
        
        # Validate Node.js version
        try:
            result = subprocess.run([self._node_cmd, "--version"], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                raise PlaywrightMCPError(f"Node.js validation failed: {result.stderr}")
            node_version = result.stdout.strip()
            logger.debug(f"Found Node.js {node_version}")
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            raise PlaywrightMCPError(f"Node.js validation failed: {e}")
        
        # Detect npm
        self._npm_cmd = shutil.which("npm")
        if not self._npm_cmd:
            common_npm_paths = self._get_common_npm_paths()
            for path in common_npm_paths:
                if os.path.exists(path):
                    self._npm_cmd = path
                    break
        
        # Detect npx
        self._npx_cmd = shutil.which("npx")
        if not self._npx_cmd:
            common_npx_paths = self._get_common_npx_paths()
            for path in common_npx_paths:
                if os.path.exists(path):
                    self._npx_cmd = path
                    break
        
        if not self._npx_cmd:
            raise PlaywrightMCPError(
                "npx not found. Please ensure Node.js is properly installed with npm.\n"
                "npx is required to run the Playwright MCP server."
            )
        
        logger.debug(f"Node.js environment detected: node={self._node_cmd}, npm={self._npm_cmd}, npx={self._npx_cmd}")
    
    def _get_common_nodejs_paths(self) -> List[str]:
        """Get platform-specific common Node.js installation paths."""
        system = platform.system().lower()
        
        if system == "windows":
            return [
                "C:\\Program Files\\nodejs\\node.exe",
                "C:\\Program Files (x86)\\nodejs\\node.exe",
                os.path.expanduser("~\\AppData\\Roaming\\npm\\node.exe"),
            ]
        elif system == "darwin":  # macOS
            return [
                "/usr/local/bin/node",
                "/opt/homebrew/bin/node",
                "/usr/bin/node",
                os.path.expanduser("~/.nvm/versions/node/*/bin/node"),
            ]
        else:  # Linux and others
            return [
                "/usr/bin/node",
                "/usr/local/bin/node",
                "/snap/bin/node",
                os.path.expanduser("~/.nvm/versions/node/*/bin/node"),
            ]
    
    def _get_common_npm_paths(self) -> List[str]:
        """Get platform-specific common npm paths."""
        system = platform.system().lower()
        
        if system == "windows":
            return [
                "C:\\Program Files\\nodejs\\npm.cmd",
                "C:\\Program Files (x86)\\nodejs\\npm.cmd",
                os.path.expanduser("~\\AppData\\Roaming\\npm\\npm.cmd"),
            ]
        else:
            return [
                "/usr/local/bin/npm",
                "/opt/homebrew/bin/npm",
                "/usr/bin/npm",
            ]
    
    def _get_common_npx_paths(self) -> List[str]:
        """Get platform-specific common npx paths."""
        system = platform.system().lower()
        
        if system == "windows":
            return [
                "C:\\Program Files\\nodejs\\npx.cmd",
                "C:\\Program Files (x86)\\nodejs\\npx.cmd",
                os.path.expanduser("~\\AppData\\Roaming\\npm\\npx.cmd"),
            ]
        else:
            return [
                "/usr/local/bin/npx",
                "/opt/homebrew/bin/npx",
                "/usr/bin/npx",
            ]
    
    async def _ensure_playwright_mcp(self) -> None:
        """Ensure @playwright/mcp package is available."""
        logger.debug("Checking @playwright/mcp availability...")
        
        # First try to run it directly to see if it's available
        try:
            result = subprocess.run([self._npx_cmd, "@playwright/mcp", "--help"], 
                                  capture_output=True, text=True, timeout=15,
                                  env=os.environ.copy())
            if result.returncode == 0:
                logger.debug("@playwright/mcp is available via npx")
                return
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            pass
        
        # If auto-install is enabled, try to install it
        if self.auto_install and self._npm_cmd:
            logger.info("📦 Installing @playwright/mcp package...")
            try:
                result = subprocess.run([self._npm_cmd, "install", "-g", "@playwright/mcp"], 
                                      capture_output=True, text=True, timeout=120,
                                      env=os.environ.copy())
                if result.returncode == 0:
                    logger.info("✅ @playwright/mcp installed successfully")
                    return
                else:
                    logger.warning(f"Global installation failed: {result.stderr}")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                logger.warning(f"Auto-installation failed: {e}")
        
        # Final check - if still not available, provide helpful error
        try:
            result = subprocess.run([self._npx_cmd, "@playwright/mcp", "--help"], 
                                  capture_output=True, text=True, timeout=10,
                                  env=os.environ.copy())
            if result.returncode != 0:
                raise PlaywrightMCPError(
                    "@playwright/mcp package not available.\n\n"
                    "Please install it manually:\n"
                    "  npm install -g @playwright/mcp\n\n"
                    "Or if you prefer to use npx (no global installation):\n"
                    "  npx @playwright/mcp --help\n\n"
                    "This package is required for Playwright browser automation."
                )
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError):
            raise PlaywrightMCPError("Failed to validate @playwright/mcp installation")
    
    async def _ensure_browsers_installed(self) -> None:
        """Ensure Playwright browsers are installed."""
        logger.debug("Checking Playwright browser installation...")
        
        try:
            # Check if browsers are available by trying to run playwright install --dry-run
            result = subprocess.run([self._npx_cmd, "playwright", "install", "--dry-run"], 
                                  capture_output=True, text=True, timeout=30,
                                  env=os.environ.copy())
            
            # If dry-run shows missing browsers, install them
            if "browser:" in result.stdout.lower():
                logger.info("🌐 Installing Playwright browsers (this may take a few minutes)...")
                install_result = subprocess.run([self._npx_cmd, "playwright", "install"], 
                                              capture_output=True, text=True, timeout=300,
                                              env=os.environ.copy())
                if install_result.returncode == 0:
                    logger.info("✅ Playwright browsers installed successfully")
                else:
                    logger.warning(f"Browser installation had issues: {install_result.stderr}")
                    # Don't fail here as browsers might still work
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
            logger.warning(f"Browser check/installation failed: {e}")
            # Don't fail here - browsers might already be installed or install later
    
    async def _start_mcp_server(self) -> None:
        """Start the Playwright MCP server and establish connection."""
        logger.debug("Starting Playwright MCP server...")
        
        # Prepare environment variables
        env = os.environ.copy()
        env.update({
            "PLAYWRIGHT_BROWSER": self.browser.upper(),
            "PLAYWRIGHT_LAUNCH_OPTIONS": json.dumps({
                "headless": self.headless,
                "browser": self.browser,
                "viewport": {
                    "width": self.viewport_width,
                    "height": self.viewport_height
                },
                "slowMo": self.slow_mo
            })
        })
        
        # Start the MCP server process
        cmd = [self._npx_cmd, "@playwright/mcp"]
        
        try:
            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                env=env
            )
            
            # Initialize MCP connection
            await self._initialize_mcp_connection()
            self._connected = True
            
        except Exception as e:
            if self._process:
                self._process.terminate()
                self._process = None
            raise PlaywrightMCPError(f"Failed to start MCP server: {e}") from e
    
    async def _initialize_mcp_connection(self) -> None:
        """Initialize the MCP connection with proper handshake."""
        if not self._process:
            raise PlaywrightMCPError("MCP server process not started")
        
        # Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2025-03-26",
                "capabilities": {"tools": {}},
                "clientInfo": {
                    "name": "python-a2a-playwright",
                    "version": "1.0.0"
                }
            }
        }
        
        response = await self._send_request(init_request)
        if "error" in response:
            raise PlaywrightMCPError(f"MCP initialization failed: {response['error']}")
        
        # Send initialized notification
        init_notification = {
            "jsonrpc": "2.0",
            "method": "initialized",
            "params": {}
        }
        
        await self._send_notification(init_notification)
        logger.debug("MCP connection initialized successfully")
    
    def _next_request_id(self) -> str:
        """Generate next request ID."""
        self._request_id_counter += 1
        return f"req-{self._request_id_counter}"
    
    async def _send_request(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Send JSON-RPC request and wait for response."""
        if not self._process:
            raise PlaywrightMCPError("Not connected to MCP server")
        
        # Send request
        request_json = json.dumps(request) + '\n'
        self._process.stdin.write(request_json)
        self._process.stdin.flush()
        
        # Wait for response
        try:
            response_line = await asyncio.wait_for(
                asyncio.create_task(self._read_process_line()),
                timeout=self.timeout
            )
            return json.loads(response_line.strip())
        except asyncio.TimeoutError:
            raise PlaywrightMCPError(f"Request timed out after {self.timeout} seconds")
    
    async def _send_notification(self, notification: Dict[str, Any]) -> None:
        """Send JSON-RPC notification (no response expected)."""
        if not self._process:
            raise PlaywrightMCPError("Not connected to MCP server")
        
        notification_json = json.dumps(notification) + '\n'
        self._process.stdin.write(notification_json)
        self._process.stdin.flush()
    
    async def _read_process_line(self) -> str:
        """Read one line from process stdout."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._process.stdout.readline)
    
    async def _cleanup(self) -> None:
        """Clean up resources."""
        self._connected = False
        
        if self._process:
            try:
                # Try graceful shutdown first
                if self._process.poll() is None:
                    self._process.terminate()
                    await asyncio.sleep(1)
                    if self._process.poll() is None:
                        self._process.kill()
            except Exception as e:
                logger.warning(f"Error during cleanup: {e}")
            finally:
                self._process = None
    
    # High-level API methods
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """List all available Playwright tools."""
        if not self._connected:
            raise PlaywrightMCPError("Not connected. Call connect() first.")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/list",
            "params": {}
        }
        
        response = await self._send_request(request)
        if "error" in response:
            raise PlaywrightMCPError(f"Failed to list tools: {response['error']}")
        
        return response.get("result", {}).get("tools", [])
    
    async def call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """Call a specific Playwright tool."""
        if not self._connected:
            raise PlaywrightMCPError("Not connected. Call connect() first.")
        
        request = {
            "jsonrpc": "2.0",
            "id": self._next_request_id(),
            "method": "tools/call",
            "params": {
                "name": tool_name,
                "arguments": arguments or {}
            }
        }
        
        response = await self._send_request(request)
        if "error" in response:
            raise PlaywrightMCPError(f"Tool '{tool_name}' failed: {response['error']}")
        
        return response.get("result")
    
    # Browser Automation Methods
    
    async def navigate(self, url: str) -> Dict[str, Any]:
        """Navigate to a URL."""
        return await self.call_tool("browser_navigate", {"url": url})
    
    async def take_screenshot(self, filename: Optional[str] = None, raw: bool = False) -> Dict[str, Any]:
        """Take a screenshot of the current page."""
        args = {"raw": raw}
        if filename:
            args["filename"] = filename
        return await self.call_tool("browser_take_screenshot", args)
    
    async def get_snapshot(self) -> Dict[str, Any]:
        """Get accessibility snapshot of the current page (better than screenshot for automation)."""
        return await self.call_tool("browser_snapshot")
    
    async def click_element(self, element_description: str, element_ref: str) -> Dict[str, Any]:
        """Click an element on the page."""
        return await self.call_tool("browser_click", {
            "element": element_description,
            "ref": element_ref
        })
    
    async def type_text(self, element_description: str, element_ref: str, text: str, submit: bool = False) -> Dict[str, Any]:
        """Type text into an element."""
        return await self.call_tool("browser_type", {
            "element": element_description,
            "ref": element_ref,
            "text": text,
            "submit": submit
        })
    
    async def go_back(self) -> Dict[str, Any]:
        """Navigate back in browser history."""
        return await self.call_tool("browser_navigate_back")
    
    async def go_forward(self) -> Dict[str, Any]:
        """Navigate forward in browser history."""
        return await self.call_tool("browser_navigate_forward")
    
    async def get_page_title(self) -> str:
        """Get the current page title."""
        result = await self.call_tool("browser_snapshot")
        # Extract title from snapshot or use a more direct method if available
        return result.get("title", "")
    
    async def resize_browser(self, width: int, height: int) -> Dict[str, Any]:
        """Resize the browser window."""
        return await self.call_tool("browser_resize", {"width": width, "height": height})
    
    async def close_browser(self) -> Dict[str, Any]:
        """Close the browser."""
        return await self.call_tool("browser_close")
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def __repr__(self) -> str:
        """String representation."""
        status = "connected" if self._connected else "disconnected"
        return f"PlaywrightMCPServer(browser={self.browser}, status={status})"