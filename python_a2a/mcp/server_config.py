"""
MCP Server Configuration System.

This module provides a configuration system for MCP servers that matches
how Claude Desktop and other MCP hosts configure and run servers.

Key Concepts:
- MCP servers are ALWAYS run as subprocesses (not remote HTTP services)
- Communication happens via stdio (stdin/stdout) using JSON-RPC
- Servers can be Docker containers, NPX packages, or direct executables
- Configuration follows Claude Desktop's JSON format
"""

import asyncio
import json
import logging
import os
import subprocess
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from pathlib import Path

from .clients import MCPClient, create_stdio_client

logger = logging.getLogger(__name__)


@dataclass
class ServerConfig:
    """
    Configuration for an MCP server.
    
    This matches Claude Desktop's configuration format:
    {
        "command": "npx",
        "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path"],
        "env": {"KEY": "value"}
    }
    """
    command: str
    args: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    package_name: Optional[str] = None  # For better error messages
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ServerConfig":
        """Create from dictionary configuration."""
        return cls(
            command=data["command"],
            args=data.get("args", []),
            env=data.get("env", {}),
            package_name=data.get("package_name")
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "command": self.command,
            "args": self.args,
            "env": self.env
        }


class MCPServerRunner:
    """
    Runs MCP servers as subprocesses and manages their lifecycle.
    
    This class handles:
    - Starting server processes
    - Creating stdio clients for communication
    - Managing server lifecycle
    - Handling errors and restarts
    """
    
    def __init__(self, name: str, config: ServerConfig):
        """
        Initialize server runner.
        
        Args:
            name: Server name (e.g. "github", "filesystem")
            config: Server configuration
        """
        self.name = name
        self.config = config
        self.process: Optional[subprocess.Popen] = None
        self.client: Optional[MCPClient] = None
        self._running = False
        
    async def start(self) -> MCPClient:
        """
        Start the server process and create a client.
        
        Returns:
            MCPClient connected to the server
            
        Raises:
            RuntimeError: If server fails to start
        """
        if self._running:
            raise RuntimeError(f"Server {self.name} is already running")
        
        try:
            # Prepare environment
            env = os.environ.copy()
            env.update(self.config.env)
            
            # Start the process and create client
            logger.info(f"Starting MCP server {self.name}: {self.config.command} {' '.join(self.config.args)}")
            
            # Create stdio client - this will start the process internally
            self.client = await create_stdio_client(
                command=[self.config.command] + self.config.args,
                env=env
            )
            
            # The process is now managed by the client
            self.process = None
            
            self._running = True
            logger.info(f"MCP server {self.name} started successfully")
            
            return self.client
            
        except Exception as e:
            logger.error(f"Failed to start MCP server {self.name}: {e}")
            await self.stop()
            raise RuntimeError(f"Failed to start server {self.name}: {e}")
    
    async def stop(self):
        """Stop the server process."""
        if self.client:
            try:
                await self.client.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting client for {self.name}: {e}")
            self.client = None
        
        self._running = False
        logger.info(f"MCP server {self.name} stopped")
    
    @property
    def is_running(self) -> bool:
        """Check if server is running."""
        return self._running and self.client is not None and self.client.is_connected


class MCPServerManager:
    """
    Manages multiple MCP servers.
    
    This class provides:
    - Loading server configurations
    - Starting/stopping servers
    - Accessing server clients
    - Health monitoring
    """
    
    def __init__(self):
        """Initialize the server manager."""
        self.servers: Dict[str, MCPServerRunner] = {}
        self._configs: Dict[str, ServerConfig] = {}
    
    def add_server(self, name: str, config: Union[ServerConfig, Dict[str, Any]]):
        """
        Add a server configuration.
        
        Args:
            name: Server name
            config: Server configuration (ServerConfig or dict)
        """
        if isinstance(config, dict):
            config = ServerConfig.from_dict(config)
        
        self._configs[name] = config
        logger.info(f"Added server configuration: {name}")
    
    def load_config(self, config_path: Union[str, Path]):
        """
        Load server configurations from a JSON file.
        
        The file should have the same format as Claude Desktop:
        {
            "mcpServers": {
                "github": {
                    "command": "docker",
                    "args": [...],
                    "env": {...}
                },
                "filesystem": {
                    "command": "npx",
                    "args": [...]
                }
            }
        }
        
        Args:
            config_path: Path to configuration file
        """
        config_path = Path(config_path)
        
        with open(config_path, 'r') as f:
            data = json.load(f)
        
        servers = data.get("mcpServers", {})
        for name, config in servers.items():
            self.add_server(name, config)
        
        logger.info(f"Loaded {len(servers)} server configurations from {config_path}")
    
    async def start_server(self, name: str) -> MCPClient:
        """
        Start a specific server.
        
        Args:
            name: Server name
            
        Returns:
            MCPClient connected to the server
            
        Raises:
            KeyError: If server not configured
            RuntimeError: If server fails to start
        """
        if name not in self._configs:
            raise KeyError(f"Server {name} not configured")
        
        if name in self.servers and self.servers[name].is_running:
            logger.info(f"Server {name} is already running")
            return self.servers[name].client
        
        runner = MCPServerRunner(name, self._configs[name])
        client = await runner.start()
        self.servers[name] = runner
        
        return client
    
    async def stop_server(self, name: str):
        """
        Stop a specific server.
        
        Args:
            name: Server name
        """
        if name in self.servers:
            await self.servers[name].stop()
            del self.servers[name]
    
    async def start_all(self) -> Dict[str, MCPClient]:
        """
        Start all configured servers.
        
        Returns:
            Dictionary mapping server names to clients
        """
        clients = {}
        
        for name in self._configs:
            try:
                client = await self.start_server(name)
                clients[name] = client
            except Exception as e:
                logger.error(f"Failed to start server {name}: {e}")
        
        return clients
    
    async def stop_all(self):
        """Stop all running servers."""
        server_names = list(self.servers.keys())
        
        for name in server_names:
            try:
                await self.stop_server(name)
            except Exception as e:
                logger.error(f"Error stopping server {name}: {e}")
    
    def get_client(self, name: str) -> Optional[MCPClient]:
        """
        Get client for a running server.
        
        Args:
            name: Server name
            
        Returns:
            MCPClient if server is running, None otherwise
        """
        if name in self.servers and self.servers[name].is_running:
            return self.servers[name].client
        return None
    
    def list_configured(self) -> List[str]:
        """List all configured server names."""
        return list(self._configs.keys())
    
    def list_running(self) -> List[str]:
        """List all running server names."""
        return [name for name, runner in self.servers.items() if runner.is_running]


# Convenience functions
def create_github_config(token: str) -> ServerConfig:
    """
    Create configuration for GitHub MCP server.
    
    Args:
        token: GitHub personal access token
        
    Returns:
        ServerConfig for GitHub MCP server
    """
    return ServerConfig(
        command="docker",
        args=[
            "run", "-i", "--rm",
            "-e", "GITHUB_PERSONAL_ACCESS_TOKEN",
            "ghcr.io/github/github-mcp-server"
        ],
        env={"GITHUB_PERSONAL_ACCESS_TOKEN": token}
    )


def create_filesystem_config(allowed_paths: List[str]) -> ServerConfig:
    """
    Create configuration for filesystem MCP server.
    
    Args:
        allowed_paths: List of allowed directory paths
        
    Returns:
        ServerConfig for filesystem MCP server
    """
    return ServerConfig(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem"] + allowed_paths
    )