"""
MCP Providers Module

This module provides high-level interfaces to local MCP servers.
Providers are clients that connect to and interact with external MCP servers via subprocess.

Local Providers (subprocess-based):
    from python_a2a.mcp.providers import GitHubMCPServer, PlaywrightMCPServer
    
    # GitHub provider
    github = GitHubMCPServer(token="your-token")
    await github.connect()
    user = await github.get_user("octocat")
    await github.disconnect()
    
    # Playwright provider
    async with PlaywrightMCPServer() as playwright:
        await playwright.navigate("https://example.com")
        await playwright.take_screenshot("page.png")
"""

# Local providers
from .github import GitHubMCPServer
from .browserbase import BrowserbaseMCPServer
from .filesystem import FilesystemMCPServer
from .puppeteer import PuppeteerMCPServer
from .playwright import PlaywrightMCPServer
from .base import BaseProvider

__all__ = [
    # Local providers
    "GitHubMCPServer",
    "BrowserbaseMCPServer", 
    "FilesystemMCPServer",
    "PuppeteerMCPServer",
    "PlaywrightMCPServer",
    "BaseProvider"
]