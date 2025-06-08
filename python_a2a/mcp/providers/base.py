"""
Base Provider Class

Abstract base class for all MCP providers. Provides common functionality
and enforces a consistent interface across all external MCP server integrations.
"""

import logging
import os
import shutil
import subprocess
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Union, Tuple
from pathlib import Path

from ..clients import MCPClient
from ..server_config import ServerConfig, MCPServerRunner

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """
    Abstract base class for MCP providers.
    
    A provider is a high-level interface to an external MCP server.
    It handles server lifecycle, connection management, and provides
    typed methods for the server's functionality.
    
    Subclasses must implement:
    - _create_config(): Create server configuration
    - _get_provider_name(): Return provider name for logging
    """
    
    def __init__(self):
        """Initialize the base provider."""
        self.client: Optional[MCPClient] = None
        self.runner: Optional[MCPServerRunner] = None
        self._connected = False
        
        # Get provider configuration
        self.config = self._create_config()
        self.provider_name = self._get_provider_name()
        
        # Create server runner
        self.runner = MCPServerRunner(self.provider_name, self.config)
    
    @abstractmethod
    def _create_config(self) -> ServerConfig:
        """
        Create server configuration for this provider.
        
        Returns:
            ServerConfig with command, args, env, etc.
        """
        pass
    
    @abstractmethod
    def _get_provider_name(self) -> str:
        """
        Get the provider name for logging and identification.
        
        Returns:
            Provider name (e.g., "github", "browserbase", "filesystem")
        """
        pass
    
    async def connect(self) -> None:
        """
        Connect to the MCP server.
        
        Raises:
            RuntimeError: If already connected or connection fails
        """
        if self._connected:
            raise RuntimeError(f"{self.provider_name} provider already connected")
        
        logger.info(f"Starting {self.provider_name} MCP server...")
        
        try:
            self.client = await self.runner.start()
            self._connected = True
            logger.info(f"Connected to {self.provider_name} MCP server")
        except Exception as e:
            error_msg = str(e)
            
            # Provide specific guidance based on error type
            if "timed out" in error_msg.lower():
                enhanced_msg = f"""
❌ {self.provider_name.title()} MCP server connection timed out.

🔧 Troubleshooting steps:
1. Ensure the MCP server package is installed correctly
2. Check that Node.js and npm are working: node --version && npm --version
3. Try installing manually: npm install -g {self.config.package_name or 'unknown'}
4. Test the server directly: npx {self.config.package_name or 'unknown'}

💡 Common causes:
- Package not found or corrupted installation
- Network connectivity issues during package download
- Insufficient permissions for npm installation
- Antivirus software blocking execution

Original error: {error_msg}
"""
                raise RuntimeError(enhanced_msg) from e
            elif "not found" in error_msg.lower() or "command not found" in error_msg.lower():
                enhanced_msg = f"""
❌ {self.provider_name.title()} MCP server command not found.

🔧 Installation required:
1. Install Node.js: https://nodejs.org/
2. Install the MCP server: npm install -g {self.config.package_name or 'unknown'}
3. Verify installation: npx {self.config.package_name or 'unknown'} --help

💡 Alternative: Use npx for one-time execution without global installation

Original error: {error_msg}
"""
                raise RuntimeError(enhanced_msg) from e
            else:
                # Generic error with basic guidance
                enhanced_msg = f"""
❌ Failed to start {self.provider_name.title()} MCP server.

🔧 General troubleshooting:
1. Check Node.js installation: node --version
2. Verify package availability: npm view {self.config.package_name or 'unknown'}
3. Try manual installation: npm install -g {self.config.package_name or 'unknown'}

Original error: {error_msg}
"""
                raise RuntimeError(enhanced_msg) from e
    
    async def disconnect(self) -> None:
        """Disconnect from the MCP server."""
        if self.runner:
            await self.runner.stop()
        self.client = None
        self._connected = False
        logger.info(f"Disconnected from {self.provider_name} MCP server")
    
    @property
    def is_connected(self) -> bool:
        """Check if provider is connected to the MCP server."""
        return self._connected and self.client is not None
    
    def _ensure_connected(self) -> None:
        """Ensure provider is connected, raise error if not."""
        if not self.is_connected:
            raise RuntimeError(f"{self.provider_name} provider not connected. Call connect() first.")
    
    async def list_tools(self) -> List[Dict[str, Any]]:
        """
        List all available tools from the MCP server.
        
        Returns:
            List of available tools with their descriptions
        """
        self._ensure_connected()
        
        tools_response = await self.client.list_tools()
        
        # Handle different response formats (some servers return {'tools': [...]})
        if isinstance(tools_response, dict) and 'tools' in tools_response:
            return tools_response['tools']
        elif isinstance(tools_response, list):
            return tools_response
        else:
            return tools_response if tools_response else []
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None, timeout: Optional[float] = None) -> Any:
        """
        Call a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments
            timeout: Custom timeout for this operation
            
        Returns:
            Tool result (parsed from MCP content format if needed)
            
        Raises:
            RuntimeError: If not connected
        """
        self._ensure_connected()
        
        # Use the client's built-in timeout support
        result = await self.client.call_tool(tool_name, arguments or {}, timeout=timeout)
        
        # Parse MCP content format if present
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
    
    # Context manager support
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.disconnect()
    
    def __repr__(self) -> str:
        """String representation of the provider."""
        status = "connected" if self.is_connected else "disconnected"
        return f"{self.__class__.__name__}(status={status})"
    
    # Shared utility methods for Node.js/npm-based providers
    
    def _detect_node_npm(self) -> Tuple[Optional[str], Optional[str]]:
        """
        Detect Node.js and npm executables dynamically.
        
        Returns:
            Tuple of (node_path, npm_path) or (None, None) if not found
        """
        # Try to find Node.js
        node_cmd = shutil.which("node")
        if not node_cmd:
            # Try common paths
            possible_node_paths = [
                "/usr/local/bin/node",
                "/usr/bin/node",
                "/opt/homebrew/bin/node"
            ]
            for path in possible_node_paths:
                if os.path.exists(path):
                    node_cmd = path
                    break
        
        # Try to find npm
        npm_cmd = shutil.which("npm")
        if not npm_cmd:
            # Try common paths
            possible_npm_paths = [
                "/usr/local/bin/npm",
                "/usr/bin/npm", 
                "/opt/homebrew/bin/npm"
            ]
            for path in possible_npm_paths:
                if os.path.exists(path):
                    npm_cmd = path
                    break
        
        return node_cmd, npm_cmd
    
    def _ensure_npm_package(self, package_name: str, node_cmd: str, npm_cmd: str, use_npx: bool = True) -> Dict[str, Any]:
        """
        Ensure an npm package is available, install if needed.
        
        Args:
            package_name: npm package name (e.g., "@modelcontextprotocol/server-filesystem")
            node_cmd: Path to Node.js executable
            npm_cmd: Path to npm executable  
            use_npx: Whether to prefer NPX over global installation
            
        Returns:
            Dict with 'type' ('global' or 'npx') and 'path' (for global) or None (for npx)
        """
        # First, try to find existing global installation
        if npm_cmd and not use_npx:
            try:
                # Get npm global prefix
                result = subprocess.run([npm_cmd, "config", "get", "prefix"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    npm_prefix = result.stdout.strip()
                    
                    # Convert package name to path (e.g., @scope/package -> @scope/package)
                    package_path = package_name.replace("/", "/")
                    
                    # Check different possible paths
                    possible_paths = [
                        f"{npm_prefix}/lib/node_modules/{package_path}/dist/index.js",
                        f"{npm_prefix}/lib/node_modules/{package_path}/index.js",
                        f"{npm_prefix}/lib/node_modules/{package_path}/bin/index.js",
                        f"{npm_prefix}/node_modules/{package_path}/dist/index.js",
                        f"{npm_prefix}/node_modules/{package_path}/index.js"
                    ]
                    
                    for server_path in possible_paths:
                        if os.path.exists(server_path):
                            return {'type': 'global', 'path': server_path}
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                pass
        
        # If not found globally and we want global installation, try to install it
        if npm_cmd and not use_npx:
            try:
                logger.info(f"Installing {package_name} globally...")
                result = subprocess.run([npm_cmd, "install", "-g", package_name], 
                                      capture_output=True, text=True, timeout=120)
                if result.returncode == 0:
                    logger.info(f"{package_name} installed successfully")
                    # Try to find it again
                    result = subprocess.run([npm_cmd, "config", "get", "prefix"], 
                                          capture_output=True, text=True, timeout=10)
                    if result.returncode == 0:
                        npm_prefix = result.stdout.strip()
                        package_path = package_name.replace("/", "/")
                        
                        possible_paths = [
                            f"{npm_prefix}/lib/node_modules/{package_path}/dist/index.js",
                            f"{npm_prefix}/lib/node_modules/{package_path}/index.js",
                            f"{npm_prefix}/lib/node_modules/{package_path}/bin/index.js",
                            f"{npm_prefix}/node_modules/{package_path}/dist/index.js",
                            f"{npm_prefix}/node_modules/{package_path}/index.js"
                        ]
                        
                        for server_path in possible_paths:
                            if os.path.exists(server_path):
                                return {'type': 'global', 'path': server_path}
                else:
                    logger.warning(f"Global installation failed: {result.stderr}")
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
                logger.warning("Could not install globally, will use NPX")
        
        # Fallback to NPX
        return {'type': 'npx', 'path': None}
    
    def _create_npm_server_config(self, package_name: str, args: List[str] = None, env: Dict[str, str] = None, 
                                 use_npx: bool = True, require_node: bool = True) -> ServerConfig:
        """
        Create a ServerConfig for npm-based MCP servers with auto-installation.
        
        Args:
            package_name: npm package name (e.g., "@modelcontextprotocol/server-filesystem")
            args: Additional arguments to pass to the server
            env: Environment variables
            use_npx: Whether to prefer NPX over global installation  
            require_node: Whether to require Node.js (raise error if not found)
            
        Returns:
            ServerConfig with appropriate command and arguments
            
        Raises:
            RuntimeError: If Node.js not found and require_node=True
        """
        args = args or []
        env = env or {}
        
        # Auto-detect Node.js and npm setup
        node_cmd, npm_cmd = self._detect_node_npm()
        
        if not node_cmd and require_node:
            error_msg = f"""
❌ Node.js not found. Please install Node.js to use {package_name}.

📋 Installation instructions:
1. Download and install Node.js from: https://nodejs.org/
2. After installation, restart your terminal
3. Verify installation: node --version && npm --version
4. Run your script again

💡 Alternatively, you can install {package_name} manually:
   npm install -g {package_name}
   
🔧 Or use npx to run without global installation:
   npx {package_name}
"""
            raise RuntimeError(error_msg)
        
        if not node_cmd:
            # Fallback to NPX without validation
            logger.info(f"Using npx to run {package_name} (Node.js path detection failed)")
            return ServerConfig(command="npx", args=["-y", package_name] + args, env=env, package_name=package_name)
        
        # Try to find existing installation or install if needed
        server_info = self._ensure_npm_package(package_name, node_cmd, npm_cmd, use_npx)
        
        if server_info['type'] == 'global' and server_info['path']:
            # Use globally installed server with absolute paths
            logger.info(f"Using globally installed {package_name} at {server_info['path']}")
            return ServerConfig(command=node_cmd, args=[server_info['path']] + args, env=env, package_name=package_name)
        elif server_info['type'] == 'npx':
            # Use NPX as fallback
            logger.info(f"Using npx to run {package_name}")
            return ServerConfig(command="npx", args=["-y", package_name] + args, env=env, package_name=package_name)
        else:
            error_msg = f"""
❌ Failed to configure {package_name} MCP server.

📋 Manual installation options:
1. Global installation: npm install -g {package_name}
2. Use npx directly: npx {package_name}
3. Check package availability: npm view {package_name}

🔧 If the package doesn't exist, verify the correct package name:
   - Check the official repository documentation
   - Search npm registry: https://www.npmjs.com/search?q={package_name}
"""
            raise RuntimeError(error_msg)


class ProviderError(Exception):
    """Base exception for provider-related errors."""
    
    def __init__(self, provider_name: str, message: str):
        self.provider_name = provider_name
        super().__init__(f"{provider_name} provider error: {message}")


class ProviderConnectionError(ProviderError):
    """Raised when provider connection fails."""
    pass


class ProviderToolError(ProviderError):
    """Raised when tool execution fails."""
    
    def __init__(self, provider_name: str, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(provider_name, f"Tool '{tool_name}' failed: {message}")