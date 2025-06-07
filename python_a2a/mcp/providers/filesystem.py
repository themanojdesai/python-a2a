"""
Filesystem MCP Provider

High-level interface to the Filesystem MCP server for file operations.
Provides typed methods for file I/O, directory management, and search operations
through the official Filesystem MCP server.

Usage:
    from python_a2a.mcp.providers import FilesystemMCPServer
    
    # Using context manager (recommended)
    async with FilesystemMCPServer(allowed_directories=["/tmp", "/Users/user/Documents"]) as fs:
        content = await fs.read_file("/tmp/test.txt")
        await fs.write_file("/tmp/output.txt", "Hello World")
        
    # Manual connection management
    fs = FilesystemMCPServer(allowed_directories=["/tmp", "/Users/user/Documents"])
    await fs.connect()
    try:
        files = await fs.list_directory("/tmp")
        info = await fs.get_file_info("/tmp/test.txt")
    finally:
        await fs.disconnect()
"""

from pathlib import Path
from typing import Dict, List, Optional, Any, Union

from .base import BaseProvider, ProviderToolError
from ..server_config import ServerConfig


class FilesystemMCPServer(BaseProvider):
    """
    High-level interface to the Filesystem MCP server.
    
    This class provides typed methods for file operations while handling
    the underlying MCP server lifecycle.
    """
    
    def __init__(self, 
                 allowed_directories: List[Union[str, Path]],
                 use_npx: bool = True):
        """
        Initialize Filesystem provider.
        
        Args:
            allowed_directories: List of directories the server can access
            use_npx: Use NPX to run the server (recommended)
        """
        self.allowed_directories = [str(Path(d).resolve()) for d in allowed_directories]
        self.use_npx = use_npx
        
        if not self.allowed_directories:
            raise ValueError("At least one allowed directory must be specified")
        
        # Initialize base provider
        super().__init__()
    
    def _create_config(self) -> ServerConfig:
        """Create Filesystem MCP server configuration."""
        if self.use_npx:
            # NPX configuration
            args = ["-y", "@modelcontextprotocol/server-filesystem"] + self.allowed_directories
            return ServerConfig(command="npx", args=args)
        else:
            # Direct execution (requires global installation)
            args = self.allowed_directories
            return ServerConfig(command="mcp-server-filesystem", args=args)
    
    def _get_provider_name(self) -> str:
        """Get provider name."""
        return "filesystem"
    
    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any] = None) -> Any:
        """
        Call a tool on the Filesystem MCP server.
        
        Args:
            tool_name: Name of the tool
            arguments: Tool arguments
            
        Returns:
            Tool result (parsed from MCP content format if needed)
        """
        result = await super()._call_tool(tool_name, arguments or {})
        
        # Filesystem MCP server returns data in content format: {'content': [{'type': 'text', 'text': '...'}]}
        if isinstance(result, dict) and 'content' in result:
            content = result['content']
            if content and len(content) > 0 and 'text' in content[0]:
                # Filesystem server returns text format, not JSON
                return content[0]['text']
        
        return result
    
    # File Operations
    
    async def read_file(self, path: str) -> str:
        """
        Read the complete contents of a file.
        
        Args:
            path: Path to the file to read
            
        Returns:
            File contents as string
        """
        result = await self._call_tool("read_file", {"path": path})
        return result
    
    async def read_multiple_files(self, paths: List[str]) -> List[Dict[str, Any]]:
        """
        Read the contents of multiple files simultaneously.
        
        Args:
            paths: List of file paths to read
            
        Returns:
            List of file contents with metadata
        """
        result = await self._call_tool("read_multiple_files", {"paths": paths})
        return result if isinstance(result, list) else []
    
    async def write_file(self, path: str, content: str) -> Dict[str, Any]:
        """
        Create a new file or completely overwrite an existing file.
        
        Args:
            path: Path to the file to write
            content: Content to write
            
        Returns:
            Operation result
        """
        return await self._call_tool("write_file", {"path": path, "content": content})
    
    async def edit_file(self, 
                       path: str, 
                       edits: List[Dict[str, str]], 
                       dry_run: bool = False) -> Dict[str, Any]:
        """
        Make line-based edits to a text file.
        
        Args:
            path: Path to the file to edit
            edits: List of edits with 'oldText' and 'newText' keys
            dry_run: Preview changes without applying them
            
        Returns:
            Edit result with diff information
        """
        return await self._call_tool("edit_file", {
            "path": path,
            "edits": edits,
            "dryRun": dry_run
        })
    
    # Directory Operations
    
    async def create_directory(self, path: str) -> Dict[str, Any]:
        """
        Create a new directory or ensure a directory exists.
        
        Args:
            path: Path to the directory to create
            
        Returns:
            Operation result
        """
        return await self._call_tool("create_directory", {"path": path})
    
    async def list_directory(self, path: str) -> List[str]:
        """
        Get a detailed listing of all files and directories.
        
        Args:
            path: Path to the directory to list
            
        Returns:
            List of directory contents with [FILE] and [DIR] prefixes
        """
        result = await self._call_tool("list_directory", {"path": path})
        
        # Parse string format response
        if isinstance(result, str):
            items = []
            for line in result.strip().split('\n'):
                line = line.strip()
                if line:
                    items.append(line)
            return items
        return result if isinstance(result, list) else []
    
    async def directory_tree(self, path: str) -> Dict[str, Any]:
        """
        Get a recursive tree view of files and directories.
        
        Args:
            path: Path to the directory to traverse
            
        Returns:
            JSON structure with files and directories
        """
        result = await self._call_tool("directory_tree", {"path": path})
        
        # Parse different response formats
        if isinstance(result, str):
            import json
            try:
                # Try parsing as JSON string
                parsed = json.loads(result)
                return parsed
            except json.JSONDecodeError:
                # Fallback to basic structure
                return {
                    "name": Path(path).name,
                    "type": "directory",
                    "children": []
                }
        elif isinstance(result, list):
            return {
                "name": Path(path).name,
                "type": "directory", 
                "children": result
            }
        return result
    
    # File Management Operations
    
    async def move_file(self, source: str, destination: str) -> Dict[str, Any]:
        """
        Move or rename files and directories.
        
        Args:
            source: Source path
            destination: Destination path
            
        Returns:
            Operation result
        """
        return await self._call_tool("move_file", {
            "source": source,
            "destination": destination
        })
    
    async def search_files(self, 
                          path: str, 
                          pattern: str, 
                          exclude_patterns: Optional[List[str]] = None) -> List[str]:
        """
        Recursively search for files and directories matching a pattern.
        
        Args:
            path: Starting path for search
            pattern: Search pattern (case-insensitive)
            exclude_patterns: Patterns to exclude from search
            
        Returns:
            List of matching file paths
        """
        params = {"path": path, "pattern": pattern}
        if exclude_patterns:
            params["excludePatterns"] = exclude_patterns
        
        result = await self._call_tool("search_files", params)
        return result if isinstance(result, list) else []
    
    async def get_file_info(self, path: str) -> Dict[str, Any]:
        """
        Retrieve detailed metadata about a file or directory.
        
        Args:
            path: Path to the file or directory
            
        Returns:
            File metadata including size, timestamps, permissions
        """
        result = await self._call_tool("get_file_info", {"path": path})
        
        # Parse string format response into dict
        if isinstance(result, str):
            info = {}
            for line in result.strip().split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    info[key.strip()] = value.strip()
            return info
        return result
    
    async def list_allowed_directories(self) -> List[str]:
        """
        Get the list of directories that this server can access.
        
        Returns:
            List of allowed directory paths
        """
        result = await self._call_tool("list_allowed_directories", {})
        
        # Parse string format response
        if isinstance(result, str):
            lines = result.strip().split('\n')
            directories = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith('Allowed directories:'):
                    directories.append(line)
            return directories
        return result if isinstance(result, list) else []