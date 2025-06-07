"""
MCP Transport Implementations - Standard stdio and HTTP transports.

This module provides transport implementations for MCP following the 
2025-03-26 specification. The stdio transport is the primary mechanism
that MCP clients SHOULD support whenever possible.
"""

import asyncio
import json
import logging
import os
import sys
from typing import List, Optional, Dict, Any
from pathlib import Path

from .protocol import MCPConnectionError, MCPProtocolError

logger = logging.getLogger(__name__)


class StdioTransport:
    """
    Standard stdio transport for MCP clients.
    
    Communicates with MCP servers via stdin/stdout of a subprocess,
    following the MCP specification's stdio transport requirements.
    """
    
    def __init__(
        self,
        command: List[str],
        cwd: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        timeout: float = 30.0
    ):
        """
        Initialize stdio transport.
        
        Args:
            command: Command and arguments to start MCP server
            cwd: Working directory for server process
            env: Environment variables for server process
            timeout: Process startup timeout
        """
        self.command = command
        self.cwd = cwd
        self.env = env or {}
        self.timeout = timeout
        
        # Process management
        self.process: Optional[asyncio.subprocess.Process] = None
        self._connected = False
        self._receive_queue = asyncio.Queue()
        self._reader_task: Optional[asyncio.Task] = None
        
        logger.info(f"Created stdio transport for command: {' '.join(command)}")
    
    async def connect(self) -> None:
        """Start the MCP server process and establish communication."""
        if self._connected:
            raise MCPConnectionError("Transport already connected")
        
        try:
            # Prepare environment
            full_env = os.environ.copy()
            full_env.update(self.env)
            
            # Validate command
            if not self.command:
                raise MCPConnectionError("Command cannot be empty")
            
            # Check if command exists
            command_path = self.command[0]
            if not self._command_exists(command_path):
                raise MCPConnectionError(f"Command not found: {command_path}")
            
            logger.info(f"Starting MCP server: {' '.join(self.command)}")
            
            # Start process
            self.process = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *self.command,
                    stdin=asyncio.subprocess.PIPE,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=self.cwd,
                    env=full_env,
                    # Ensure clean process group for proper cleanup
                    preexec_fn=os.setsid if hasattr(os, 'setsid') else None
                ),
                timeout=self.timeout
            )
            
            # Start reading stdout
            self._reader_task = asyncio.create_task(self._read_stdout())
            
            # Verify process is running
            if self.process.returncode is not None:
                raise MCPConnectionError(f"Process exited immediately with code {self.process.returncode}")
            
            self._connected = True
            logger.info(f"MCP server started with PID {self.process.pid}")
            
        except asyncio.TimeoutError:
            raise MCPConnectionError(f"Process startup timed out after {self.timeout}s")
        except Exception as e:
            await self._cleanup_process()
            raise MCPConnectionError(f"Failed to start process: {e}") from e
    
    async def disconnect(self) -> None:
        """Stop the MCP server process and clean up resources."""
        if not self._connected:
            return
        
        logger.info("Stopping MCP server process")
        
        self._connected = False
        
        # Stop reader task
        if self._reader_task and not self._reader_task.done():
            self._reader_task.cancel()
            try:
                await self._reader_task
            except asyncio.CancelledError:
                pass
        
        # Clean up process
        await self._cleanup_process()
        
        logger.info("MCP server process stopped")
    
    async def send(self, message: bytes) -> None:
        """Send message to MCP server via stdin."""
        if not self._connected or not self.process:
            raise MCPConnectionError("Transport not connected")
        
        if self.process.returncode is not None:
            raise MCPConnectionError(f"Process has exited with code {self.process.returncode}")
        
        try:
            # MCP stdio protocol: each message is a line
            message_line = message + b'\n'
            
            self.process.stdin.write(message_line)
            await self.process.stdin.drain()
            
            logger.debug(f"Sent {len(message)} bytes to MCP server")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise MCPConnectionError(f"Send failed: {e}") from e
    
    async def receive(self) -> bytes:
        """Receive message from MCP server via stdout."""
        if not self._connected:
            raise MCPConnectionError("Transport not connected")
        
        try:
            # Get message from queue (populated by reader task)
            message = await self._receive_queue.get()
            
            # Check for special error marker
            if isinstance(message, Exception):
                raise message
            
            logger.debug(f"Received {len(message)} bytes from MCP server")
            return message
            
        except Exception as e:
            if isinstance(e, MCPConnectionError):
                raise
            logger.error(f"Failed to receive message: {e}")
            raise MCPConnectionError(f"Receive failed: {e}") from e
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return (
            self._connected and 
            self.process is not None and 
            self.process.returncode is None
        )
    
    async def _read_stdout(self) -> None:
        """Read messages from process stdout with proper handling of large JSON responses."""
        logger.debug("Started stdout reader task")
        
        try:
            buffer = b''
            max_message_size = 50 * 1024 * 1024  # 50MB limit for large responses like screenshots
            
            while self._connected and self.process:
                try:
                    # Read data in chunks
                    chunk = await self.process.stdout.read(65536)  # 64KB chunks
                    if not chunk:
                        logger.info("MCP server closed stdout")
                        break
                    
                    buffer += chunk
                    
                    # Process complete JSON-RPC messages from buffer
                    while True:
                        newline_pos = buffer.find(b'\n')
                        if newline_pos == -1:
                            break
                        
                        # Extract complete message
                        message_bytes = buffer[:newline_pos].rstrip(b'\r')
                        buffer = buffer[newline_pos + 1:]
                        
                        # Validate message size
                        if len(message_bytes) > max_message_size:
                            logger.error(f"Message too large: {len(message_bytes)} bytes, skipping")
                            continue
                        
                        # Decode and validate as JSON
                        if message_bytes:
                            try:
                                message_text = message_bytes.decode('utf-8')
                                # Validate it's proper JSON-RPC
                                import json
                                json.loads(message_text)  # Validate JSON structure
                                await self._receive_queue.put(message_bytes)
                            except (UnicodeDecodeError, json.JSONDecodeError) as e:
                                logger.warning(f"Invalid message from MCP server: {e}")
                                continue
                    
                    # Check if buffer is getting too large
                    if len(buffer) > max_message_size:
                        logger.error("Buffer overflow, clearing incomplete message")
                        buffer = b''
                        
                except Exception as e:
                    logger.error(f"Error reading stdout: {e}")
                    break
                
        except Exception as e:
            logger.error(f"Stdout reader error: {e}")
            await self._receive_queue.put(MCPConnectionError(f"Reader failed: {e}"))
        
        logger.debug("Stdout reader task ended")
    
    async def _cleanup_process(self) -> None:
        """Clean up the server process."""
        if not self.process:
            return
        
        try:
            # Try graceful termination first
            if self.process.returncode is None:
                self.process.terminate()
                
                try:
                    # Wait for graceful exit
                    await asyncio.wait_for(self.process.wait(), timeout=5.0)
                except asyncio.TimeoutError:
                    # Force kill if graceful termination fails
                    logger.warning("Process did not terminate gracefully, killing")
                    self.process.kill()
                    await self.process.wait()
            
            # Read any remaining stderr for debugging
            if self.process.stderr:
                stderr_data = await self.process.stderr.read()
                if stderr_data:
                    stderr_text = stderr_data.decode('utf-8', errors='replace')
                    logger.debug(f"MCP server stderr: {stderr_text}")
            
            exit_code = self.process.returncode
            if exit_code != 0:
                logger.warning(f"MCP server exited with code {exit_code}")
            else:
                logger.info("MCP server exited normally")
                
        except Exception as e:
            logger.error(f"Error cleaning up process: {e}")
        finally:
            self.process = None
    
    def _command_exists(self, command: str) -> bool:
        """Check if command exists in PATH or as absolute path."""
        # If absolute path, check directly
        if os.path.isabs(command):
            return os.path.isfile(command) and os.access(command, os.X_OK)
        
        # Check in PATH
        path_env = os.environ.get('PATH', '')
        for path_dir in path_env.split(os.pathsep):
            if not path_dir:
                continue
            
            full_path = os.path.join(path_dir, command)
            if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
                return True
        
        return False
    
    def get_process_info(self) -> Dict[str, Any]:
        """Get information about the server process."""
        if not self.process:
            return {"status": "not_started"}
        
        return {
            "pid": self.process.pid,
            "returncode": self.process.returncode,
            "command": self.command,
            "cwd": self.cwd,
            "connected": self._connected
        }


class ServerStdioTransport:
    """
    Server-side stdio transport for MCP servers.
    
    Handles communication via stdin/stdout when the MCP server
    is being run as a subprocess by a client.
    """
    
    def __init__(self):
        """Initialize server stdio transport."""
        self._connected = False
        self._stdin_reader: Optional[asyncio.Task] = None
        self._receive_queue = asyncio.Queue()
        
        logger.info("Created server stdio transport")
    
    async def connect(self) -> None:
        """Start reading from stdin."""
        if self._connected:
            raise MCPConnectionError("Transport already connected")
        
        # Start stdin reader
        self._stdin_reader = asyncio.create_task(self._read_stdin())
        self._connected = True
        
        logger.info("Server stdio transport connected")
    
    async def disconnect(self) -> None:
        """Stop reading from stdin."""
        if not self._connected:
            return
        
        self._connected = False
        
        if self._stdin_reader and not self._stdin_reader.done():
            self._stdin_reader.cancel()
            try:
                await self._stdin_reader
            except asyncio.CancelledError:
                pass
        
        logger.info("Server stdio transport disconnected")
    
    async def send(self, message: bytes) -> None:
        """Send message via stdout."""
        if not self._connected:
            raise MCPConnectionError("Transport not connected")
        
        try:
            # Write to stdout with newline
            message_line = message + b'\n'
            sys.stdout.buffer.write(message_line)
            sys.stdout.buffer.flush()
            
            logger.debug(f"Sent {len(message)} bytes via stdout")
            
        except Exception as e:
            logger.error(f"Failed to send message: {e}")
            raise MCPConnectionError(f"Send failed: {e}") from e
    
    async def receive(self) -> bytes:
        """Receive message from stdin."""
        if not self._connected:
            raise MCPConnectionError("Transport not connected")
        
        try:
            message = await self._receive_queue.get()
            
            if isinstance(message, Exception):
                raise message
            
            logger.debug(f"Received {len(message)} bytes from stdin")
            return message
            
        except Exception as e:
            if isinstance(e, MCPConnectionError):
                raise
            logger.error(f"Failed to receive message: {e}")
            raise MCPConnectionError(f"Receive failed: {e}") from e
    
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        return self._connected
    
    async def _read_stdin(self) -> None:
        """Read messages from stdin."""
        logger.debug("Started stdin reader task")
        
        try:
            # Use asyncio subprocess communication approach
            reader = asyncio.StreamReader()
            protocol = asyncio.StreamReaderProtocol(reader)
            
            # Connect to stdin properly
            loop = asyncio.get_event_loop()
            transport, _ = await loop.connect_read_pipe(
                lambda: protocol, sys.stdin
            )
            
            try:
                while self._connected:
                    # Read line from stdin with timeout
                    try:
                        line = await asyncio.wait_for(reader.readline(), timeout=1.0)
                        
                        if not line:
                            # EOF - but only break if we're sure stdin is closed
                            logger.debug("Received EOF from stdin")
                            # Small delay to ensure we're not just hitting a temporary EOF
                            await asyncio.sleep(0.1)
                            continue
                        
                        # Remove newline and decode
                        try:
                            message_text = line.rstrip(b'\n\r').decode('utf-8')
                            if message_text:  # Skip empty lines
                                message_bytes = message_text.encode('utf-8')
                                await self._receive_queue.put(message_bytes)
                        except UnicodeDecodeError as e:
                            logger.warning(f"Invalid UTF-8 from stdin: {e}")
                            continue
                            
                    except asyncio.TimeoutError:
                        # Normal timeout, continue loop
                        continue
                        
            finally:
                transport.close()
                
        except Exception as e:
            logger.error(f"Stdin reader error: {e}")
            await self._receive_queue.put(MCPConnectionError(f"Reader failed: {e}"))
        
        logger.debug("Stdin reader task ended")


# Factory functions
def create_stdio_transport(
    command: List[str],
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    timeout: float = 30.0
) -> StdioTransport:
    """
    Create stdio transport for MCP client.
    
    Args:
        command: Command to start MCP server
        cwd: Working directory
        env: Environment variables
        timeout: Startup timeout
        
    Returns:
        Configured stdio transport
    """
    return StdioTransport(command, cwd, env, timeout)


def create_server_stdio_transport() -> ServerStdioTransport:
    """
    Create stdio transport for MCP server.
    
    Returns:
        Configured server stdio transport
    """
    return ServerStdioTransport()