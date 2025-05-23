#!/usr/bin/env python3
"""
MCP Client Example - One-Click Demo of MCP Integration

This example demonstrates the power of MCP (Model Context Protocol) integration
in python-a2a with a seamless, one-click experience.

Features demonstrated:
- Automatic MCP server detection and connection
- Interactive agent with real MCP tools
- Both local (stdio) and remote (SSE) MCP servers
- Live demonstration with working tools

Just run: python mcp_client_example.py
"""

import asyncio
import argparse
import socket
import time
import threading
from typing import Dict
from python_a2a import (
    A2AServer, AgentCard, run_server, Message, MessageRole, 
    TextContent, AgentSkill
)
from python_a2a.mcp import MCPClient, FastMCPAgent, FastMCP

# ANSI colors for beautiful output
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
RED = "\033[91m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def print_banner():
    """Print a beautiful banner"""
    print(f"\n{BLUE}{'='*60}{RESET}")
    print(f"{BOLD}{CYAN}🚀 MCP Client Example - Experience the Magic! 🚀{RESET}")
    print(f"{BLUE}{'='*60}{RESET}\n")


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


class SmartMCPAgent(A2AServer, FastMCPAgent):
    """
    A smart agent that automatically discovers and uses MCP servers.
    
    This agent demonstrates the best practices for MCP integration:
    - Automatic tool discovery
    - Intelligent routing
    - User-friendly interactions
    """
    
    def __init__(self, port=None):
        # Find a free port if not provided
        if port is None:
            port = find_free_port()
        
        # Create an impressive agent card
        agent_card = AgentCard(
            name="MCP Smart Assistant",
            description="An intelligent assistant powered by multiple MCP servers",
            url=f"http://localhost:{port}",
            version="2.0.0",
            skills=[
                AgentSkill(
                    name="MCP Tool Discovery",
                    description="Automatically discovers and uses MCP tools",
                    tags=["mcp", "tools", "discovery"],
                    examples=["What tools do you have?", "Show me your capabilities"]
                ),
                AgentSkill(
                    name="File Operations",
                    description="Read, write, and manage files",
                    tags=["files", "filesystem", "storage"],
                    examples=["List files in current directory", "Read README.md"]
                ),
                AgentSkill(
                    name="Calculations",
                    description="Perform mathematical calculations",
                    tags=["math", "calculator", "compute"],
                    examples=["Calculate 15 * 27", "What's the sum of 100 and 250?"]
                ),
                AgentSkill(
                    name="Information Lookup",
                    description="Search and retrieve information",
                    tags=["search", "info", "knowledge"],
                    examples=["Tell me about Python", "What's the weather like?"]
                )
            ]
        )
        
        # Initialize A2AServer
        A2AServer.__init__(self, agent_card=agent_card)
        
        # Initialize with built-in demo MCP servers
        mcp_servers = self._create_demo_mcp_servers()
        FastMCPAgent.__init__(self, mcp_servers=mcp_servers)
        
        # Store port
        self.port = port
        
        # Track available tools
        self.available_tools = {}
        
        # Flag to track if discovery has been done
        self._tools_discovered = False
    
    async def setup(self):
        """Setup method to be called after server starts"""
        await self._discover_tools()
        self._tools_discovered = True
    
    def _create_demo_mcp_servers(self) -> Dict:
        """Create demo MCP servers that work out of the box"""
        servers = {}
        
        # 1. Built-in Calculator MCP (always works!)
        calc_mcp = FastMCP(
            name="Calculator",
            description="Mathematical calculations"
        )
        
        @calc_mcp.tool()
        def add(a: float, b: float) -> float:
            """Add two numbers"""
            return a + b
        
        @calc_mcp.tool()
        def multiply(a: float, b: float) -> float:
            """Multiply two numbers"""
            return a * b
        
        @calc_mcp.tool()
        def divide(a: float, b: float) -> float:
            """Divide two numbers"""
            if b == 0:
                return "Error: Division by zero"
            return a / b
        
        servers["calculator"] = calc_mcp
        
        # 2. Built-in Info MCP
        info_mcp = FastMCP(
            name="Info Tools",
            description="Information and utility tools"
        )
        
        @info_mcp.tool()
        def get_time() -> str:
            """Get current time"""
            return time.strftime("%Y-%m-%d %H:%M:%S")
        
        @info_mcp.tool()
        def get_info(topic: str) -> str:
            """Get information about a topic"""
            info_db = {
                "python": "Python is a high-level programming language known for its simplicity and readability.",
                "mcp": "Model Context Protocol (MCP) is a standard for connecting AI agents to tools and data sources.",
                "a2a": "Agent-to-Agent (A2A) protocol enables communication between AI agents.",
                "weather": "I don't have real-time weather access, but it's probably nice somewhere!"
            }
            return info_db.get(topic.lower(), f"I don't have specific information about '{topic}'")
        
        servers["info"] = info_mcp
        
        # 3. Try to add filesystem MCP if npx is available
        if self._check_command_exists("npx"):
            servers["filesystem"] = {
                "command": ["npx", "-y", "@modelcontextprotocol/server-filesystem", "."]
            }
        
        return servers
    
    def _check_command_exists(self, command: str) -> bool:
        """Check if a command exists on the system"""
        import shutil
        return shutil.which(command) is not None
    
    async def _discover_tools(self):
        """Discover available tools from all MCP servers"""
        await asyncio.sleep(0.5)  # Give servers time to initialize
        
        print(f"\n{YELLOW}🔍 Discovering MCP tools...{RESET}")
        
        for server_name, client in self.mcp_clients.items():
            if client is None:  # FastMCP server
                # For FastMCP, we can't easily list tools without accessing internals
                self.available_tools[server_name] = ["(FastMCP tools available)"]
                print(f"{GREEN}✓{RESET} {server_name}: Built-in tools ready")
            else:
                try:
                    tools = await client.get_tools()
                    tool_names = [tool['name'] for tool in tools]
                    self.available_tools[server_name] = tool_names
                    print(f"{GREEN}✓{RESET} {server_name}: {len(tools)} tools discovered")
                except Exception as e:
                    print(f"{RED}✗{RESET} {server_name}: Failed to discover tools - {e}")
                    self.available_tools[server_name] = []
        
        total_tools = sum(len(tools) for tools in self.available_tools.values())
        print(f"\n{GREEN}🎉 Total tools available: {total_tools}{RESET}\n")
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming messages with intelligent routing"""
        text = message.content.text if hasattr(message.content, 'text') else ""
        
        # Tool discovery commands
        if any(phrase in text.lower() for phrase in ["what tools", "show tools", "list tools", "capabilities"]):
            return self._list_tools_response(message)
        
        # Calculator commands
        elif any(word in text.lower() for word in ["calculate", "add", "multiply", "divide", "sum", "product"]):
            return self._handle_calculation(message, text)
        
        # Time/info commands
        elif any(word in text.lower() for word in ["time", "date", "info", "tell me about"]):
            return self._handle_info_request(message, text)
        
        # File operations
        elif any(word in text.lower() for word in ["list files", "read file", "show files"]):
            return self._handle_file_operation(message, text)
        
        # Help command
        elif "help" in text.lower():
            return self._help_response(message)
        
        # Default friendly response
        else:
            return Message(
                content=TextContent(text=self._get_friendly_response()),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def _list_tools_response(self, message: Message) -> Message:
        """List all available tools"""
        # Ensure tools are discovered
        if not self._tools_discovered:
            # For now, provide basic info
            self.available_tools = {
                "calculator": ["add", "multiply", "divide"],
                "info": ["get_time", "get_info"],
                "filesystem": ["(if npx is available)"]
            }
        
        lines = [f"{BOLD}🛠️  Available MCP Tools:{RESET}\n"]
        
        for server, tools in self.available_tools.items():
            lines.append(f"{CYAN}{server}:{RESET}")
            if tools:
                for tool in tools[:5]:  # Show first 5 tools
                    lines.append(f"  • {tool}")
                if len(tools) > 5:
                    lines.append(f"  • ... and {len(tools) - 5} more")
            else:
                lines.append("  • No tools available")
            lines.append("")
        
        lines.append(f"{YELLOW}💡 Tip: Try 'calculate 10 + 20' or 'what time is it?'{RESET}")
        
        return Message(
            content=TextContent(text="\n".join(lines)),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _handle_calculation(self, message: Message, text: str) -> Message:
        """Handle calculation requests"""
        import re
        
        # Extract numbers from the text
        numbers = re.findall(r'-?\d+\.?\d*', text)
        
        if len(numbers) >= 2:
            a, b = float(numbers[0]), float(numbers[1])
            
            # Determine operation
            if "add" in text.lower() or "+" in text:
                result = asyncio.run(self.call_mcp_tool("calculator", "add", a=a, b=b))
                operation = "addition"
            elif "multiply" in text.lower() or "*" in text or "×" in text:
                result = asyncio.run(self.call_mcp_tool("calculator", "multiply", a=a, b=b))
                operation = "multiplication"
            elif "divide" in text.lower() or "/" in text or "÷" in text:
                result = asyncio.run(self.call_mcp_tool("calculator", "divide", a=a, b=b))
                operation = "division"
            else:
                # Default to addition
                result = asyncio.run(self.call_mcp_tool("calculator", "add", a=a, b=b))
                operation = "sum"
            
            response = f"{GREEN}🧮 Calculation Result:{RESET}\n{operation.capitalize()} of {a} and {b} = {BOLD}{result}{RESET}"
        else:
            response = f"{YELLOW}Please provide two numbers for calculation. Example: 'add 10 and 20'{RESET}"
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _handle_info_request(self, message: Message, text: str) -> Message:
        """Handle information requests"""
        if "time" in text.lower() or "date" in text.lower():
            result = asyncio.run(self.call_mcp_tool("info", "get_time"))
            response = f"{BLUE}🕐 Current Time:{RESET} {result}"
        else:
            # Extract topic
            if "about" in text.lower():
                parts = text.lower().split("about")
                if len(parts) > 1:
                    topic = parts[1].strip()
                else:
                    topic = "general"
            else:
                topic = "general"
            
            result = asyncio.run(self.call_mcp_tool("info", "get_info", topic=topic))
            response = f"{MAGENTA}📚 Information:{RESET}\n{result}"
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _handle_file_operation(self, message: Message, text: str) -> Message:
        """Handle file operations"""
        if "filesystem" in self.available_tools and self.available_tools["filesystem"]:
            # This would call the actual filesystem MCP
            response = f"{CYAN}📁 File operations are available through the filesystem MCP server.{RESET}"
        else:
            response = f"{YELLOW}📁 Filesystem MCP not available. Make sure Node.js and npx are installed.{RESET}"
        
        return Message(
            content=TextContent(text=response),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _help_response(self, message: Message) -> Message:
        """Provide help information"""
        help_text = f"""
{BOLD}{CYAN}🤖 MCP Smart Assistant Help{RESET}

{YELLOW}Available Commands:{RESET}
• {GREEN}list tools{RESET} - Show all available MCP tools
• {GREEN}calculate X + Y{RESET} - Perform calculations (add, multiply, divide)
• {GREEN}what time is it?{RESET} - Get current time
• {GREEN}tell me about [topic]{RESET} - Get information about Python, MCP, A2A, etc.
• {GREEN}help{RESET} - Show this help message

{YELLOW}Example Queries:{RESET}
• "Calculate 42 * 7"
• "What's 100 divided by 4?"
• "Tell me about Python"
• "What tools do you have?"

{MAGENTA}💡 This agent automatically discovers and uses MCP tools!{RESET}
"""
        return Message(
            content=TextContent(text=help_text),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def _get_friendly_response(self) -> str:
        """Get a friendly default response"""
        responses = [
            f"{GREEN}Hello! I'm your MCP-powered assistant. Type 'help' to see what I can do!{RESET}",
            f"{BLUE}I'm ready to help! Try asking me to calculate something or type 'list tools'.{RESET}",
            f"{MAGENTA}Need assistance? I can do calculations, tell time, and more. Type 'help' for details!{RESET}",
        ]
        import random
        return random.choice(responses)


def print_demo_queries():
    """Print some demo queries for the user"""
    print(f"\n{YELLOW}🎯 Try these example queries:{RESET}")
    queries = [
        "list tools",
        "calculate 42 * 7",
        "what's 100 + 250?",
        "what time is it?",
        "tell me about Python",
        "help"
    ]
    for query in queries:
        print(f"   {GREEN}•{RESET} {query}")
    print()


def main():
    parser = argparse.ArgumentParser(
        description="MCP Client Example - Experience seamless MCP integration!",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python mcp_client_example.py              # Run interactive agent (recommended!)
  python mcp_client_example.py --port 8080  # Use specific port
  python mcp_client_example.py --test       # Run quick test
        """
    )
    
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port for the agent server (auto-finds free port if not specified)"
    )
    parser.add_argument(
        "--test", action="store_true",
        help="Run a quick test of MCP functionality"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print_banner()
    
    if args.test:
        # Quick test mode
        print(f"{CYAN}Running MCP functionality test...{RESET}\n")
        
        async def quick_test():
            # Test calculator
            calc = FastMCP("Test")
            @calc.tool()
            def add(a: int, b: int) -> int:
                return a + b
            
            print(f"{GREEN}✓{RESET} FastMCP creation: Success")
            
            # Test client creation
            try:
                client = MCPClient(command=["echo", "test"])
                print(f"{GREEN}✓{RESET} MCPClient creation: Success")
            except Exception as e:
                print(f"{RED}✗{RESET} MCPClient creation: {e}")
            
            print(f"\n{GREEN}🎉 MCP functionality test completed!{RESET}")
        
        asyncio.run(quick_test())
    
    else:
        # Run the interactive agent
        agent = SmartMCPAgent(args.port)
        port = agent.port
        
        print(f"{GREEN}🚀 Starting MCP Smart Assistant on http://localhost:{port}{RESET}")
        print(f"{BLUE}📡 Agent URL: http://localhost:{port}/a2a{RESET}")
        
        # Print demo queries
        print_demo_queries()
        
        print(f"{CYAN}{'='*60}{RESET}")
        print(f"{YELLOW}Ready to receive messages! The agent is now running...{RESET}")
        print(f"{CYAN}{'='*60}{RESET}\n")
        
        # Start tool discovery in background
        def run_setup():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(agent.setup())
            loop.close()
        
        setup_thread = threading.Thread(target=run_setup)
        setup_thread.daemon = True
        setup_thread.start()
        
        # Run the server
        run_server(agent, host="localhost", port=port)


if __name__ == "__main__":
    main()