"""
Puppeteer MCP Provider

High-level interface to the Puppeteer MCP server for browser automation.
Provides typed methods for browser operations, page interactions, and data extraction
through the official Puppeteer MCP server from Anthropic.

Usage:
    from python_a2a.mcp.providers import PuppeteerMCPServer
    
    # Using context manager (recommended)
    async with PuppeteerMCPServer(headless=False) as puppeteer:
        await puppeteer.navigate("https://example.com")
        screenshot = await puppeteer.take_screenshot("page_screenshot")
        
    # Manual connection management
    puppeteer = PuppeteerMCPServer(headless=True)
    await puppeteer.connect()
    try:
        await puppeteer.navigate("https://example.com")
        await puppeteer.click("button.submit")
        result = await puppeteer.evaluate("document.title")
    finally:
        await puppeteer.disconnect()
"""

from typing import Dict, List, Optional, Any, Union

from .base import BaseProvider
from ..server_config import ServerConfig


class PuppeteerMCPServer(BaseProvider):
    """
    High-level interface to the Puppeteer MCP server.
    
    This class provides typed methods for browser automation while handling
    the underlying Puppeteer MCP server lifecycle.
    
    Available tools from the official Puppeteer MCP server:
    - puppeteer_navigate: Navigate to a URL
    - puppeteer_screenshot: Take screenshots
    - puppeteer_click: Click elements
    - puppeteer_fill: Fill input fields
    - puppeteer_select: Select dropdown options
    - puppeteer_hover: Hover over elements
    - puppeteer_evaluate: Execute JavaScript
    """
    
    def __init__(self, 
                 headless: bool = True,
                 use_npx: bool = False,
                 user_data_dir: Optional[str] = None,
                 viewport_width: int = 1280,
                 viewport_height: int = 720,
                 executable_path: Optional[str] = None,
                 devtools: bool = False,
                 ignore_https_errors: bool = False,
                 disable_web_security: bool = False,
                 user_agent: Optional[str] = None):
        """
        Initialize Chrome provider using Puppeteer MCP server.
        
        Args:
            headless: Run browser in headless mode
            use_npx: Use NPX to run the server (recommended)
            user_data_dir: User data directory for browser profile
            viewport_width: Browser viewport width
            viewport_height: Browser viewport height
            executable_path: Path to Chrome executable
            devtools: Open Chrome DevTools automatically
            ignore_https_errors: Ignore HTTPS certificate errors
            disable_web_security: Disable web security (CORS)
            user_agent: Custom user agent string
        """
        self.headless = headless
        self.use_npx = use_npx
        self.user_data_dir = user_data_dir
        self.viewport_width = viewport_width
        self.viewport_height = viewport_height
        self.executable_path = executable_path
        self.devtools = devtools
        self.ignore_https_errors = ignore_https_errors
        self.disable_web_security = disable_web_security
        self.user_agent = user_agent
        
        # Initialize base provider
        super().__init__()
    
    def _create_config(self) -> ServerConfig:
        """Create Chrome MCP server configuration using official Puppeteer MCP server."""
        # Create launch options JSON for Puppeteer MCP server
        import json
        import os
        import platform
        import subprocess
        import shutil
        
        launch_options = {
            "headless": self.headless,
            "defaultViewport": {
                "width": self.viewport_width,
                "height": self.viewport_height
            }
        }
        
        # Auto-detect Chrome executable if needed
        if not self.executable_path:
            if platform.system() == "Darwin":  # macOS
                chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
                if os.path.exists(chrome_path):
                    launch_options["executablePath"] = chrome_path
            elif platform.system() == "Linux":
                for path in ["/usr/bin/google-chrome", "/usr/bin/chromium-browser", "/usr/bin/chromium"]:
                    if os.path.exists(path):
                        launch_options["executablePath"] = path
                        break
            elif platform.system() == "Windows":
                for path in ["C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe", 
                           "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"]:
                    if os.path.exists(path):
                        launch_options["executablePath"] = path
                        break
        else:
            launch_options["executablePath"] = self.executable_path
        
        # Add Chrome arguments for better compatibility
        chrome_args = ["--no-first-run", "--disable-default-apps"]
        
        if self.headless:
            chrome_args.extend([
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-extensions"
            ])
        
        if self.disable_web_security:
            chrome_args.append("--disable-web-security")
        if self.user_agent:
            chrome_args.append(f"--user-agent={self.user_agent}")
        
        launch_options["args"] = chrome_args
        
        if self.user_data_dir:
            launch_options["userDataDir"] = self.user_data_dir
        if self.devtools and not self.headless:
            launch_options["devtools"] = self.devtools
        if self.ignore_https_errors:
            launch_options["ignoreHTTPSErrors"] = self.ignore_https_errors
        
        # Environment variables for Puppeteer MCP server
        env = {
            "PUPPETEER_LAUNCH_OPTIONS": json.dumps(launch_options),
            "ALLOW_DANGEROUS": "true"
        }
        
        # Use shared utility for robust npm/npx handling
        return self._create_npm_server_config(
            package_name="@modelcontextprotocol/server-puppeteer",
            args=[],
            env=env,
            use_npx=self.use_npx,
            require_node=True
        )
    
    def _get_provider_name(self) -> str:
        """Get provider name."""
        return "chrome"
    
    def get_launch_options(self) -> Dict[str, Any]:
        """
        Get Puppeteer launch options based on initialization parameters.
        
        Returns:
            Dictionary of Puppeteer launch options
        """
        options = {
            "headless": self.headless,
            "defaultViewport": {
                "width": self.viewport_width,
                "height": self.viewport_height
            }
        }
        
        # Try to find Chrome executable if not specified
        if not self.executable_path:
            import os
            import platform
            
            # Common Chrome paths by platform
            if platform.system() == "Darwin":  # macOS
                possible_paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium"
                ]
            elif platform.system() == "Linux":
                possible_paths = [
                    "/usr/bin/google-chrome",
                    "/usr/bin/chromium-browser",
                    "/usr/bin/chromium"
                ]
            elif platform.system() == "Windows":
                possible_paths = [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                ]
            else:
                possible_paths = []
            
            for path in possible_paths:
                if os.path.exists(path):
                    options["executablePath"] = path
                    break
        else:
            options["executablePath"] = self.executable_path
        
        # Essential args for reliable operation
        args = [
            "--no-first-run",
            "--disable-default-apps",
            "--disable-background-timer-throttling",
            "--disable-backgrounding-occluded-windows",
            "--disable-renderer-backgrounding"
        ]
        
        if self.headless:
            # Safe args for headless mode
            args.extend([
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--disable-software-rasterizer",
                "--disable-extensions"
            ])
        
        if self.user_data_dir:
            options["userDataDir"] = self.user_data_dir
        if self.devtools and not self.headless:  # DevTools only works in non-headless mode
            options["devtools"] = self.devtools
        if self.ignore_https_errors:
            options["ignoreHTTPSErrors"] = self.ignore_https_errors
        if self.disable_web_security:
            args.append("--disable-web-security")
        if self.user_agent:
            args.append(f"--user-agent={self.user_agent}")
        
        options["args"] = args
        
        # Set timeout for operations
        options["timeout"] = 30000  # 30 seconds
            
        return options
    
    def get_safe_launch_options(self) -> Dict[str, Any]:
        """
        Get safe Puppeteer launch options that don't require allowDangerous=true.
        
        Returns:
            Dictionary of safe Puppeteer launch options
        """
        options = {
            "headless": self.headless,
            "defaultViewport": {
                "width": self.viewport_width,
                "height": self.viewport_height
            }
        }
        
        # Try to find Chrome executable if not specified
        if not self.executable_path:
            import os
            import platform
            
            # Common Chrome paths by platform
            if platform.system() == "Darwin":  # macOS
                possible_paths = [
                    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                    "/Applications/Chromium.app/Contents/MacOS/Chromium"
                ]
            elif platform.system() == "Linux":
                possible_paths = [
                    "/usr/bin/google-chrome",
                    "/usr/bin/chromium-browser",
                    "/usr/bin/chromium"
                ]
            elif platform.system() == "Windows":
                possible_paths = [
                    "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    "C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe"
                ]
            else:
                possible_paths = []
            
            for path in possible_paths:
                if os.path.exists(path):
                    options["executablePath"] = path
                    break
        else:
            options["executablePath"] = self.executable_path
        
        # Only safe args that don't require allowDangerous
        safe_args = [
            "--no-first-run",
            "--disable-default-apps"
        ]
        
        if self.headless:
            # Safe args for headless mode
            safe_args.extend([
                "--disable-extensions",
                "--disable-plugins"
            ])
        
        if self.user_data_dir:
            options["userDataDir"] = self.user_data_dir
        if self.devtools and not self.headless:  # DevTools only works in non-headless mode
            options["devtools"] = self.devtools
        if self.ignore_https_errors:
            options["ignoreHTTPSErrors"] = self.ignore_https_errors
        if self.user_agent:
            safe_args.append(f"--user-agent={self.user_agent}")
        
        options["args"] = safe_args
        
        # Set timeout for operations
        options["timeout"] = 30000  # 30 seconds
            
        return options
    
    # Browser Navigation Operations
    
    async def navigate(self, url: str, launch_options: Optional[Dict[str, Any]] = None, allow_dangerous: bool = True) -> Dict[str, Any]:
        """
        Navigate to a URL in the browser.
        
        Args:
            url: URL to navigate to
            launch_options: Puppeteer launch options (overrides environment config)
            allow_dangerous: Allow potentially dangerous operations
            
        Returns:
            Navigation result with page info
        """
        params = {"url": url}
        
        # Only pass launch options if explicitly provided, otherwise use environment config
        if launch_options:
            params["launchOptions"] = launch_options
            params["allowDangerous"] = allow_dangerous
            
        # Use longer timeout for navigation operations (2 minutes)
        return await self._call_tool("puppeteer_navigate", params, timeout=120.0)
    
    # Page Interaction Operations
    
    async def click(self, selector: str) -> Dict[str, Any]:
        """
        Click an element on the page.
        
        Args:
            selector: CSS selector for the element to click
            
        Returns:
            Click result
        """
        return await self._call_tool("puppeteer_click", {"selector": selector}, timeout=60.0)
    
    async def fill(self, selector: str, value: str) -> Dict[str, Any]:
        """
        Fill out an input field.
        
        Args:
            selector: CSS selector for the input field
            value: Value to fill in the field
            
        Returns:
            Fill result
        """
        return await self._call_tool("puppeteer_fill", {
            "selector": selector,
            "value": value
        }, timeout=60.0)
    
    async def select(self, selector: str, value: str) -> Dict[str, Any]:
        """
        Select an option from a dropdown/select element.
        
        Args:
            selector: CSS selector for the select element
            value: Value to select
            
        Returns:
            Selection result
        """
        return await self._call_tool("puppeteer_select", {
            "selector": selector,
            "value": value
        }, timeout=60.0)
    
    async def hover(self, selector: str) -> Dict[str, Any]:
        """
        Hover over an element on the page.
        
        Args:
            selector: CSS selector for the element to hover
            
        Returns:
            Hover result
        """
        return await self._call_tool("puppeteer_hover", {"selector": selector})
    
    # Screenshot Operations
    
    async def take_screenshot(self, 
                             name: str = "screenshot", 
                             selector: Optional[str] = None, 
                             width: Optional[int] = None, 
                             height: Optional[int] = None, 
                             encoded: bool = True) -> str:
        """
        Take a screenshot of the current page or a specific element.
        
        Args:
            name: Name for the screenshot file
            selector: CSS selector for specific element (full page if None)
            width: Screenshot width (uses viewport width if None)
            height: Screenshot height (uses viewport height if None)
            encoded: Return base64 encoded data
            
        Returns:
            Screenshot data (base64 encoded if encoded=True)
        """
        params = {"name": name, "encoded": encoded}
        
        if selector:
            params["selector"] = selector
        if width:
            params["width"] = width
        if height:
            params["height"] = height
            
        result = await self._call_tool("puppeteer_screenshot", params)
        return result if isinstance(result, str) else str(result)
    
    async def screenshot_element(self, selector: str, name: str = "element_screenshot") -> str:
        """
        Take a screenshot of a specific element.
        
        Args:
            selector: CSS selector for the element
            name: Name for the screenshot file
            
        Returns:
            Screenshot data as base64 string
        """
        return await self.take_screenshot(name=name, selector=selector)
    
    async def screenshot_full_page(self, name: str = "full_page_screenshot") -> str:
        """
        Take a screenshot of the full page.
        
        Args:
            name: Name for the screenshot file
            
        Returns:
            Screenshot data as base64 string
        """
        return await self.take_screenshot(name=name)
    
    # JavaScript Execution
    
    async def evaluate(self, script: str) -> Any:
        """
        Execute JavaScript in the browser console.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Script execution result
        """
        result = await self._call_tool("puppeteer_evaluate", {"script": script})
        
        # Parse Puppeteer MCP server response format
        if isinstance(result, str) and "Execution result:" in result:
            lines = result.split('\n')
            for i, line in enumerate(lines):
                if line.strip() == "Execution result:":
                    if i + 1 < len(lines):
                        result_line = lines[i + 1].strip()
                        # Remove quotes if present
                        if result_line.startswith('"') and result_line.endswith('"'):
                            return result_line[1:-1]
                        # Try to parse as JSON
                        try:
                            import json
                            return json.loads(result_line)
                        except (json.JSONDecodeError, ValueError):
                            return result_line
                    break
        
        return result
    
    async def execute_javascript(self, script: str) -> Any:
        """
        Alias for evaluate() method for consistency with other providers.
        
        Args:
            script: JavaScript code to execute
            
        Returns:
            Script execution result
        """
        return await self.evaluate(script)
    
    # Convenience Methods for Common Operations
    
    async def get_page_title(self) -> str:
        """
        Get the page title.
        
        Returns:
            Page title
        """
        result = await self.evaluate("document.title")
        return result if isinstance(result, str) else str(result)
    
    async def get_page_url(self) -> str:
        """
        Get the current page URL.
        
        Returns:
            Current URL
        """
        result = await self.evaluate("window.location.href")
        return result if isinstance(result, str) else str(result)
    
    async def get_text(self, selector: str) -> str:
        """
        Get text content from an element.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            Element text content
        """
        script = f"document.querySelector('{selector}')?.textContent || ''"
        result = await self.evaluate(script)
        return result if isinstance(result, str) else str(result)
    
    async def get_attribute(self, selector: str, attribute: str) -> Optional[str]:
        """
        Get an attribute value from an element.
        
        Args:
            selector: CSS selector for the element
            attribute: Attribute name
            
        Returns:
            Attribute value or None if not found
        """
        script = f"document.querySelector('{selector}')?.getAttribute('{attribute}')"
        result = await self.evaluate(script)
        return result if result is not None else None
    
    async def get_value(self, selector: str) -> str:
        """
        Get the value of an input element.
        
        Args:
            selector: CSS selector for the input element
            
        Returns:
            Input value
        """
        script = f"document.querySelector('{selector}')?.value || ''"
        result = await self.evaluate(script)
        return result if isinstance(result, str) else str(result)
    
    async def wait_for_element(self, selector: str, timeout: int = 30000) -> bool:
        """
        Wait for an element to appear on the page.
        
        Args:
            selector: CSS selector for the element
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if element found, False if timeout
        """
        script = f"""
        new Promise((resolve) => {{
            const element = document.querySelector('{selector}');
            if (element) {{
                resolve(true);
                return;
            }}
            
            const observer = new MutationObserver(() => {{
                const element = document.querySelector('{selector}');
                if (element) {{
                    observer.disconnect();
                    resolve(true);
                }}
            }});
            
            observer.observe(document.body, {{
                childList: true,
                subtree: true
            }});
            
            setTimeout(() => {{
                observer.disconnect();
                resolve(false);
            }}, {timeout});
        }})
        """
        
        result = await self.evaluate(script)
        return bool(result)
    
    async def wait_for_navigation(self, timeout: int = 30000) -> bool:
        """
        Wait for page navigation to complete.
        
        Args:
            timeout: Maximum time to wait in milliseconds
            
        Returns:
            True if navigation completed, False if timeout
        """
        script = f"""
        new Promise((resolve) => {{
            if (document.readyState === 'complete') {{
                resolve(true);
                return;
            }}
            
            const checkReady = () => {{
                if (document.readyState === 'complete') {{
                    resolve(true);
                }}
            }};
            
            document.addEventListener('readystatechange', checkReady);
            window.addEventListener('load', () => resolve(true));
            
            setTimeout(() => {{
                document.removeEventListener('readystatechange', checkReady);
                resolve(false);
            }}, {timeout});
        }})
        """
        
        result = await self.evaluate(script)
        return bool(result)
    
    async def scroll_to_element(self, selector: str) -> Dict[str, Any]:
        """
        Scroll to bring an element into view.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            Scroll result
        """
        script = f"""
        const element = document.querySelector('{selector}');
        if (element) {{
            element.scrollIntoView({{ behavior: 'smooth', block: 'center' }});
            return {{ success: true, scrolled: true }};
        }}
        return {{ success: false, error: 'Element not found' }};
        """
        
        return await self.evaluate(script)
    
    async def scroll(self, x: int = 0, y: int = 0) -> Dict[str, Any]:
        """
        Scroll the page to specific coordinates.
        
        Args:
            x: Horizontal scroll position (default: 0)
            y: Vertical scroll position (default: 0)
            
        Returns:
            Scroll result with new position
        """
        script = f"""
        window.scrollTo({x}, {y});
        return {{
            success: true,
            scrollX: window.scrollX,
            scrollY: window.scrollY
        }};
        """
        
        return await self.evaluate(script)
    
    async def scroll_by(self, x: int = 0, y: int = 0) -> Dict[str, Any]:
        """
        Scroll the page by a relative amount.
        
        Args:
            x: Horizontal scroll amount (default: 0)
            y: Vertical scroll amount (default: 0)
            
        Returns:
            Scroll result with new position
        """
        script = f"""
        window.scrollBy({x}, {y});
        return {{
            success: true,
            scrollX: window.scrollX,
            scrollY: window.scrollY
        }};
        """
        
        return await self.evaluate(script)
    
    async def scroll_to_bottom(self) -> Dict[str, Any]:
        """
        Scroll to the bottom of the page.
        
        Returns:
            Scroll result with final position
        """
        script = """
        window.scrollTo(0, document.body.scrollHeight);
        return {
            success: true,
            scrollX: window.scrollX,
            scrollY: window.scrollY,
            pageHeight: document.body.scrollHeight
        };
        """
        
        return await self.evaluate(script)
    
    async def scroll_to_top(self) -> Dict[str, Any]:
        """
        Scroll to the top of the page.
        
        Returns:
            Scroll result with position
        """
        script = """
        window.scrollTo(0, 0);
        return {
            success: true,
            scrollX: 0,
            scrollY: 0
        };
        """
        
        return await self.evaluate(script)
    
    async def type_text(self, selector: str, text: str, delay: int = 100) -> Dict[str, Any]:
        """
        Type text into an element with optional delay between characters.
        
        Args:
            selector: CSS selector for the element
            text: Text to type
            delay: Delay between characters in milliseconds
            
        Returns:
            Typing result
        """
        # Click the element first to focus it
        await self.click(selector)
        
        # Clear existing content and fill with new text
        await self.fill(selector, text)
        
        return {"success": True, "text": text, "selector": selector}
    
    async def press_key(self, key: str) -> Dict[str, Any]:
        """
        Press a keyboard key.
        
        Args:
            key: Key to press (e.g., 'Enter', 'Tab', 'Escape')
            
        Returns:
            Key press result
        """
        # Simulate key press using JavaScript
        script = f"""
        const event = new KeyboardEvent('keydown', {{
            key: '{key}',
            bubbles: true,
            cancelable: true
        }});
        document.activeElement.dispatchEvent(event);
        
        const eventUp = new KeyboardEvent('keyup', {{
            key: '{key}',
            bubbles: true,
            cancelable: true
        }});
        document.activeElement.dispatchEvent(eventUp);
        
        return {{ success: true, key: '{key}' }};
        """
        
        return await self.evaluate(script)
    
    async def get_page_content(self) -> str:
        """
        Get the full HTML content of the page.
        
        Returns:
            Page HTML content
        """
        result = await self.evaluate("document.documentElement.outerHTML")
        return result if isinstance(result, str) else str(result)
    
    async def count_elements(self, selector: str) -> int:
        """
        Count the number of elements matching a selector.
        
        Args:
            selector: CSS selector
            
        Returns:
            Number of matching elements
        """
        script = f"document.querySelectorAll('{selector}').length"
        result = await self.evaluate(script)
        return int(result) if isinstance(result, (int, float, str)) else 0
    
    async def element_exists(self, selector: str) -> bool:
        """
        Check if an element exists on the page.
        
        Args:
            selector: CSS selector
            
        Returns:
            True if element exists, False otherwise
        """
        count = await self.count_elements(selector)
        return count > 0
    
    async def element_visible(self, selector: str) -> bool:
        """
        Check if an element is visible on the page.
        
        Args:
            selector: CSS selector
            
        Returns:
            True if element is visible, False otherwise
        """
        script = f"""
        const element = document.querySelector('{selector}');
        if (!element) return false;
        
        const style = window.getComputedStyle(element);
        return style.display !== 'none' && 
               style.visibility !== 'hidden' && 
               style.opacity !== '0' &&
               element.offsetWidth > 0 && 
               element.offsetHeight > 0;
        """
        
        result = await self.evaluate(script)
        return bool(result)