#!/usr/bin/env python3
"""
Example demonstrating how to create A2A agents with MCP server tools.

This is a key feature of python-a2a: easily attaching any MCP server 
to agents to give them additional capabilities.
"""

import asyncio
import argparse
import socket
from python_a2a import (
    A2AServer, AgentCard, run_server, Message, MessageRole, 
    TextContent, FunctionResponseContent
)
from python_a2a.mcp import A2AMCPAgent, FastMCPAgent, MCPClient


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


# Example 1: Creating an A2A Server with MCP capabilities
class MCPEnabledAssistant(A2AServer, FastMCPAgent):
    """A2A Server with MCP capabilities - the recommended approach"""
    
    def __init__(self, port=None):
        # Use provided port or find a free one
        if port is None:
            port = find_free_port()
        
        # Initialize agent card
        agent_card = AgentCard(
            name="Assistant with Tools",
            description="An AI assistant with weather, filesystem, and git capabilities",
            url=f"http://localhost:{port}",
            version="1.0.0"
        )
        
        # Initialize A2AServer
        A2AServer.__init__(self, agent_card=agent_card)
        
        # Define MCP servers to attach
        mcp_servers = {
            # URL-based MCP server (SSE transport)
            "weather": "https://weather-mcp-server.example.com",
            
            # Command-based MCP server (stdio transport)
            "filesystem": {
                "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
            },
            
            # Another way to specify stdio transport
            "git": {
                "command": ["mcp-server-git", "--repo", "."]
            }
        }
        
        # Initialize FastMCPAgent with MCP servers
        FastMCPAgent.__init__(self, mcp_servers=mcp_servers)
        
        # Store port for reference
        self.port = port
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming messages"""
        return Message(
            content=TextContent(
                text=f"I'm an assistant with {len(self.mcp_servers)} MCP servers attached!"
            ),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


def example1_simple_agent(port=None):
    """Create an agent with MCP tools"""
    agent = MCPEnabledAssistant(port)
    return agent, agent.port


# Example 2: Custom agent class with MCP capabilities
class CustomAssistant(A2AServer, FastMCPAgent):
    """
    Custom agent that inherits MCP capabilities through FastMCPAgent mixin.
    
    This approach gives you more control over message handling while
    still having easy MCP integration.
    """
    
    def __init__(self, port=None):
        # Use provided port or find a free one
        if port is None:
            port = find_free_port()
        
        # Initialize agent card
        agent_card = AgentCard(
            name="Custom Assistant",
            description="A customized assistant with MCP tools",
            url=f"http://localhost:{port}",
            version="1.0.0"
        )
        
        # Store port for reference
        self.port = port
        
        # Initialize A2AServer
        A2AServer.__init__(self, agent_card=agent_card)
        
        # Initialize FastMCPAgent with MCP servers
        FastMCPAgent.__init__(
            self,
            mcp_servers={
                # Can mix different types of MCP servers
                "calculator": "http://localhost:3000",  # REST MCP server
                "database": {
                    "command": ["mcp-server-sqlite", "mydb.db"]
                },
                # Can also pass pre-configured MCPClient instances
                "custom": MCPClient(
                    server_url="https://custom-mcp.example.com",
                    headers={"Authorization": "Bearer token"}
                )
            }
        )
    
    def handle_message(self, message: Message) -> Message:
        """Custom message handling with MCP tool routing"""
        
        # Extract text content
        text = message.content.text if hasattr(message.content, 'text') else ""
        
        # Custom logic for text messages
        if "calculate" in text.lower():
            # Use calculator MCP tool
            try:
                # Example: extract numbers and operation
                import re
                numbers = re.findall(r'\d+', text)
                if len(numbers) >= 2:
                    a, b = int(numbers[0]), int(numbers[1])
                    
                    # Call MCP tool synchronously
                    loop = asyncio.get_event_loop()
                    if "add" in text:
                        result = loop.run_until_complete(
                            self.call_mcp_tool("calculator", "add", a=a, b=b)
                        )
                    elif "multiply" in text:
                        result = loop.run_until_complete(
                            self.call_mcp_tool("calculator", "multiply", a=a, b=b)
                        )
                    else:
                        result = "Please specify 'add' or 'multiply'"
                    
                    response_text = f"Result: {result}"
                else:
                    response_text = "Please provide two numbers"
            except Exception as e:
                response_text = f"Error: {str(e)}"
        
        elif "list files" in text.lower():
            # Use filesystem MCP tool
            try:
                loop = asyncio.get_event_loop()
                files = loop.run_until_complete(
                    self.call_mcp_tool("filesystem", "list_directory", path="/tmp")
                )
                response_text = f"Files in /tmp:\n{files}"
            except Exception as e:
                response_text = f"Error listing files: {str(e)}"
        
        else:
            # Default response
            response_text = (
                "I'm a custom assistant with MCP tools. I can:\n"
                "- Calculate (e.g., 'add 5 and 3')\n"
                "- List files (e.g., 'list files')\n"
                "- Access database and other tools"
            )
        
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


# Example 3: Dynamic MCP server attachment
class DynamicMCPAgent(A2AServer, FastMCPAgent):
    """Agent that can dynamically add/remove MCP servers at runtime"""
    
    def __init__(self, port=None):
        # Use provided port or find a free one
        if port is None:
            port = find_free_port()
        
        agent_card = AgentCard(
            name="Dynamic MCP Agent",
            description="Agent that can add MCP servers dynamically",
            url=f"http://localhost:{port}",
            version="1.0.0"
        )
        
        # Store port for reference
        self.port = port
        
        A2AServer.__init__(self, agent_card=agent_card)
        FastMCPAgent.__init__(self)  # No initial MCP servers
        
    def handle_message(self, message: Message) -> Message:
        """Handle messages and allow dynamic MCP server management"""
        
        text = message.content.text if hasattr(message.content, 'text') else ""
        
        if text.startswith("add mcp "):
            # Dynamic MCP server addition
            parts = text.split(maxsplit=3)
            if len(parts) >= 4:
                _, _, name, url = parts
                try:
                    self.add_mcp_server(name, url)
                    response_text = f"Added MCP server '{name}' at {url}"
                except Exception as e:
                    response_text = f"Error adding MCP server: {str(e)}"
            else:
                response_text = "Usage: add mcp <name> <url>"
        
        elif text == "list mcp":
            # List current MCP servers
            servers = list(self.mcp_servers.keys())
            response_text = f"Current MCP servers: {', '.join(servers) if servers else 'none'}"
        
        else:
            response_text = (
                "I can dynamically manage MCP servers. Commands:\n"
                "- add mcp <name> <url> - Add a new MCP server\n"
                "- list mcp - List current MCP servers"
            )
        
        return Message(
            content=TextContent(text=response_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


# Example 4: Production-ready agent with error handling
class ProductionAgent(A2AServer, FastMCPAgent):
    """Production-ready agent with proper error handling and logging"""
    
    def __init__(self, mcp_config: dict, port=None):
        """
        Initialize with MCP configuration.
        
        Args:
            mcp_config: Dictionary of MCP server configurations
            port: Optional port number, will find free port if not provided
        """
        # Use provided port or find a free one
        if port is None:
            port = find_free_port()
        
        agent_card = AgentCard(
            name="Production Agent",
            description="Production-ready agent with MCP tools",
            url=f"http://localhost:{port}",
            version="1.0.0",
            capabilities={
                "mcp_enabled": True,
                "tools": list(mcp_config.keys())
            }
        )
        
        # Store port for reference
        self.port = port
        
        A2AServer.__init__(self, agent_card=agent_card)
        
        # Initialize MCP servers with error handling
        valid_servers = {}
        for name, config in mcp_config.items():
            try:
                if isinstance(config, dict) and "test" in config and config["test"]:
                    # Skip test servers in production
                    continue
                valid_servers[name] = config
            except Exception as e:
                print(f"Warning: Skipping MCP server '{name}': {e}")
        
        FastMCPAgent.__init__(self, mcp_servers=valid_servers)
        
        # Set up cleanup on shutdown
        import atexit
        atexit.register(self._cleanup)
    
    def _cleanup(self):
        """Clean up MCP connections on shutdown"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.close_mcp_connections())
        loop.close()
    
    async def handle_message_async(self, message: Message) -> Message:
        """Async message handling with proper error handling"""
        
        try:
            # Log incoming message
            print(f"Received message: {message.content}")
            
            # Handle function calls through MCP
            if message.content.type == "function_call":
                result = await self.handle_function_call(message.content)
                
                return Message(
                    content=FunctionResponseContent(
                        name=message.content.name,
                        response={"result": result}
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            # Handle text messages
            else:
                available_tools = []
                for server_name, client in self.mcp_clients.items():
                    if client:
                        try:
                            tools = await client.get_tools()
                            for tool in tools:
                                available_tools.append(f"{server_name}:{tool['name']}")
                        except:
                            pass
                
                response_text = (
                    f"I'm a production agent with {len(self.mcp_servers)} MCP servers. "
                    f"Available tools: {', '.join(available_tools[:5])}..."
                    if available_tools else "No tools available."
                )
                
                return Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
                
        except Exception as e:
            print(f"Error handling message: {e}")
            return Message(
                content=TextContent(text=f"An error occurred: {str(e)}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_message(self, message: Message) -> Message:
        """Sync wrapper for async message handler"""
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(self.handle_message_async(message))


def main():
    parser = argparse.ArgumentParser(description="Examples of agents with MCP tools")
    parser.add_argument(
        "--example", type=int, choices=[1, 2, 3, 4], default=1,
        help="Which example to run"
    )
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port for the agent server (finds free port if not specified)"
    )
    
    args = parser.parse_args()
    
    # Determine port to use
    port = args.port
    
    # Select and run example
    if args.example == 1:
        print("Running Example 1: A2A Server with MCP capabilities")
        agent, actual_port = example1_simple_agent(port)
        port = actual_port
    
    elif args.example == 2:
        print("Running Example 2: Custom agent with MCP")
        agent = CustomAssistant(port)
        if port is None:
            port = agent.port
    
    elif args.example == 3:
        print("Running Example 3: Dynamic MCP agent")
        agent = DynamicMCPAgent(port)
        if port is None:
            port = agent.port
    
    elif args.example == 4:
        print("Running Example 4: Production agent")
        # Example configuration
        mcp_config = {
            "tools": "http://localhost:3000",
            "database": {"command": ["mcp-server-sqlite", "prod.db"]},
            "test_server": {"url": "http://test.com", "test": True}  # Will be skipped
        }
        agent = ProductionAgent(mcp_config, port)
        if port is None:
            port = agent.port
    
    # Run the agent server
    print(f"\nStarting agent on http://localhost:{port}")
    print("Send messages to test MCP integration!")
    run_server(agent, host="localhost", port=port)


if __name__ == "__main__":
    main()