"""
MCP Providers Module

This module provides high-level interfaces to external MCP servers.
Providers are clients that connect to and interact with external MCP servers.

Usage:
    from python_a2a.mcp.providers.github import GitHubMCPServer
    from python_a2a.mcp.providers.browserbase import BrowserbaseMCPServer
    from python_a2a.mcp.providers.filesystem import FilesystemMCPServer
    
    # GitHub provider
    github = GitHubMCPServer(token="your-token")
    await github.connect()
    user = await github.get_user("octocat")
    await github.disconnect()
    
    # Or with context manager
    async with GitHubMCPServer(token="your-token") as github:
        user = await github.get_user("octocat")
"""

from .github import GitHubMCPServer
from .browserbase import BrowserbaseMCPServer
from .filesystem import FilesystemMCPServer
from .base import BaseProvider

__all__ = [
    "GitHubMCPServer",
    "BrowserbaseMCPServer", 
    "FilesystemMCPServer",
    "BaseProvider"
]