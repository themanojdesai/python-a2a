"""
Command-line interface for the A2A package.
"""

import argparse
import json
import sys
import os
from typing import Dict, Any, Optional, List, Tuple

from .models import Message, TextContent, MessageRole, Conversation
from .client import A2AClient
from .server import A2AServer, run_server
from .utils import (
    pretty_print_message, 
    pretty_print_conversation,
    create_text_message
)
from .exceptions import A2AError, A2AImportError


def send_command(args: argparse.Namespace) -> int:
    """
    Send a message to an A2A agent
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        client = A2AClient(args.endpoint)
        
        # Check if input is a file path or direct text
        if args.message.endswith('.json') and os.path.isfile(args.message):
            # Load message from JSON file
            with open(args.message) as f:
                message_data = json.load(f)
                try:
                    if "messages" in message_data:
                        # This is a conversation
                        conversation = Conversation.from_dict(message_data)
                        print(f"Sending conversation with {len(conversation.messages)} messages...")
                        response = client.send_conversation(conversation)
                        pretty_print_conversation(response)
                    else:
                        # This is a single message
                        message = Message.from_dict(message_data)
                        print("Sending message...")
                        response = client.send_message(message)
                        pretty_print_message(response)
                except Exception as e:
                    print(f"Error parsing JSON: {str(e)}")
                    return 1
        else:
            # Create a simple text message
            message = create_text_message(args.message)
            
            print("Sending message...")
            response = client.send_message(message)
            
            pretty_print_message(response)
        
        return 0
    
    except A2AError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


def serve_command(args: argparse.Namespace) -> int:
    """
    Start an A2A server
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Try to import Flask
        try:
            from flask import Flask
        except ImportError:
            raise A2AImportError(
                "Flask is not installed. "
                "Install it with 'pip install flask'"
            )
        
        # Create a simple A2A server
        agent = A2AServer()
        
        # Start the server
        run_server(
            agent=agent,
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
        return 0
    
    except A2AError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


def openai_command(args: argparse.Namespace) -> int:
    """
    Start an OpenAI-powered A2A server
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Check for OpenAI API key
        api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
        if not api_key:
            print("Error: OpenAI API key is required. Provide it with --api-key or set the OPENAI_API_KEY environment variable.")
            return 1
        
        # Import OpenAI server
        try:
            from .server.llm import OpenAIA2AServer
        except ImportError as e:
            raise A2AImportError(
                f"Could not import OpenAIA2AServer: {str(e)}. "
                "Make sure openai is installed with 'pip install openai'"
            )
        
        # Create OpenAI server
        agent = OpenAIA2AServer(
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
            system_prompt=args.system_prompt
        )
        
        print(f"Starting OpenAI-powered A2A server with model {args.model}")
        print(f"System prompt: {args.system_prompt}")
        
        # Start the server
        run_server(
            agent=agent,
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
        return 0
    
    except A2AError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


def anthropic_command(args: argparse.Namespace) -> int:
    """
    Start an Anthropic-powered A2A server
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Check for Anthropic API key
        api_key = args.api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            print("Error: Anthropic API key is required. Provide it with --api-key or set the ANTHROPIC_API_KEY environment variable.")
            return 1
        
        # Import Anthropic server
        try:
            from .server.llm import AnthropicA2AServer
        except ImportError as e:
            raise A2AImportError(
                f"Could not import AnthropicA2AServer: {str(e)}. "
                "Make sure anthropic is installed with 'pip install anthropic'"
            )
        
        # Create Anthropic server
        agent = AnthropicA2AServer(
            api_key=api_key,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens,
            system_prompt=args.system_prompt
        )
        
        print(f"Starting Anthropic-powered A2A server with model {args.model}")
        print(f"System prompt: {args.system_prompt}")
        
        # Start the server
        run_server(
            agent=agent,
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
        return 0
    
    except A2AError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


def mcp_command(args: argparse.Namespace) -> int:
    """
    Start an MCP server
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import FastMCP and related modules
        try:
            from .mcp import FastMCP, create_fastapi_app
            import uvicorn
        except ImportError as e:
            raise A2AImportError(
                f"Could not import MCP modules: {str(e)}. "
                "Make sure required packages are installed with 'pip install fastapi uvicorn'"
            )
        
        # Create a FastMCP server
        mcp_server = FastMCP(
            name=args.name,
            version=args.version,
            description=args.description
        )
        
        if args.script:
            # Load tools from a Python script
            try:
                import importlib.util
                spec = importlib.util.spec_from_file_location("mcp_tools", args.script)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Look for a setup_mcp function in the module
                if hasattr(module, 'setup_mcp'):
                    module.setup_mcp(mcp_server)
                    print(f"Loaded MCP tools from {args.script}")
                else:
                    print(f"Warning: No setup_mcp function found in {args.script}")
            except Exception as e:
                print(f"Error loading script {args.script}: {e}")
                return 1
        
        # Create FastAPI app
        app = create_fastapi_app(mcp_server)
        
        print(f"Starting MCP server '{args.name}' v{args.version} on http://{args.host}:{args.port}")
        print(f"Description: {args.description}")
        
        # Run the server using uvicorn
        uvicorn.run(app, host=args.host, port=args.port)
        
        return 0
    
    except A2AError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


def mcp_agent_command(args: argparse.Namespace) -> int:
    """
    Start an MCP-enabled A2A agent
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import MCP agent classes
        try:
            from .mcp import A2AMCPAgent, FastMCP
            import importlib.util
        except ImportError as e:
            raise A2AImportError(
                f"Could not import MCP modules: {str(e)}. "
                "Make sure required packages are installed"
            )
        
        # Load MCP servers from config file if provided
        mcp_servers = {}
        if args.config:
            try:
                with open(args.config, 'r') as f:
                    config = json.load(f)
                    
                # Process server configurations
                for server_name, server_config in config.get("servers", {}).items():
                    if isinstance(server_config, str):
                        # Simple URL string
                        mcp_servers[server_name] = server_config
                    elif isinstance(server_config, dict) and "url" in server_config:
                        # Dictionary with URL and other options
                        mcp_servers[server_name] = server_config
            except Exception as e:
                print(f"Error loading config file {args.config}: {e}")
                return 1
        
        # Add any individually specified servers
        if args.servers:
            for server_spec in args.servers:
                try:
                    name, url = server_spec.split("=", 1)
                    mcp_servers[name] = url
                except ValueError:
                    print(f"Error: Invalid server specification '{server_spec}'. Use format 'name=url'")
                    return 1
        
        # Load script if provided
        if args.script:
            try:
                spec = importlib.util.spec_from_file_location("mcp_agent", args.script)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Create agent using function from module
                if hasattr(module, 'create_agent'):
                    agent = module.create_agent(mcp_servers=mcp_servers)
                else:
                    raise ValueError(f"No create_agent function found in {args.script}")
            except Exception as e:
                print(f"Error loading script {args.script}: {e}")
                return 1
        else:
            # Create a default A2A MCP agent
            agent = A2AMCPAgent(
                name=args.name,
                description=args.description,
                mcp_servers=mcp_servers
            )
        
        print(f"Starting MCP-enabled A2A agent '{args.name}' on http://{args.host}:{args.port}/a2a")
        if mcp_servers:
            print(f"Connected to MCP servers:")
            for name, config in mcp_servers.items():
                if isinstance(config, str):
                    print(f"  - {name}: {config}")
                elif isinstance(config, dict) and "url" in config:
                    print(f"  - {name}: {config['url']}")
        
        # Start the server
        run_server(
            agent=agent,
            host=args.host,
            port=args.port,
            debug=args.debug
        )
        
        return 0
    
    except A2AError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


def mcp_call_command(args: argparse.Namespace) -> int:
    """
    Call an MCP tool directly
    
    Args:
        args: Command-line arguments
        
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    try:
        # Import MCP client
        try:
            from .mcp import MCPClient
            import asyncio
        except ImportError as e:
            raise A2AImportError(
                f"Could not import MCP modules: {str(e)}. "
                "Make sure required packages are installed"
            )
        
        # Create client
        client = MCPClient(args.endpoint)
        
        # Parse parameters
        params = {}
        if args.params:
            for param in args.params:
                try:
                    name, value = param.split("=", 1)
                    # Try to convert to appropriate type (int, float, bool)
                    if value.lower() == "true":
                        value = True
                    elif value.lower() == "false":
                        value = False
                    elif value.isdigit():
                        value = int(value)
                    else:
                        try:
                            value = float(value)
                        except ValueError:
                            # Keep as string
                            pass
                    
                    params[name] = value
                except ValueError:
                    print(f"Error: Invalid parameter '{param}'. Use format 'name=value'")
                    return 1
        
        # Define async function to call the tool
        async def call_tool():
            try:
                # Initialize MCP client if needed
                if hasattr(client, 'initialize_mcp_servers'):
                    await client.initialize_mcp_servers()
                
                # Call the tool
                result = await client.call_tool(args.tool, **params)
                
                # Print result
                if isinstance(result, dict):
                    print(json.dumps(result, indent=2))
                elif isinstance(result, str):
                    print(result)
                else:
                    print(f"Result: {result}")
                
                return True
            except Exception as e:
                print(f"Error calling tool: {e}")
                return False
        
        # Run the async function
        loop = asyncio.get_event_loop()
        success = loop.run_until_complete(call_tool())
        
        return 0 if success else 1
    
    except A2AError as e:
        print(f"Error: {str(e)}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return 1


def parse_args() -> argparse.Namespace:
    """
    Parse command-line arguments
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(description="A2A command line tools")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Send message command
    send_parser = subparsers.add_parser("send", help="Send a message to an A2A agent")
    send_parser.add_argument("endpoint", help="A2A endpoint URL")
    send_parser.add_argument("message", help="Message text or JSON file path")
    send_parser.set_defaults(func=send_command)
    
    # Common server arguments
    server_args = argparse.ArgumentParser(add_help=False)
    server_args.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    server_args.add_argument("--port", type=int, default=5000, help="Port to listen on")
    server_args.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    # Start simple server command
    serve_parser = subparsers.add_parser(
        "serve", 
        help="Start a simple A2A server",
        parents=[server_args]
    )
    serve_parser.set_defaults(func=serve_command)
    
    # Start OpenAI server command
    openai_parser = subparsers.add_parser(
        "openai", 
        help="Start an OpenAI-powered A2A server",
        parents=[server_args]
    )
    openai_parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY)")
    openai_parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    openai_parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    openai_parser.add_argument("--system-prompt", default="You are a helpful AI assistant.", help="System prompt")
    openai_parser.set_defaults(func=openai_command)
    
    # Start Anthropic server command
    anthropic_parser = subparsers.add_parser(
        "anthropic", 
        help="Start an Anthropic-powered A2A server",
        parents=[server_args]
    )
    anthropic_parser.add_argument("--api-key", help="Anthropic API key (or set ANTHROPIC_API_KEY)")
    anthropic_parser.add_argument("--model", default="claude-3-opus-20240229", help="Anthropic model to use")
    anthropic_parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    anthropic_parser.add_argument("--max-tokens", type=int, default=1000, help="Maximum tokens to generate")
    anthropic_parser.add_argument("--system-prompt", default="You are a helpful AI assistant.", help="System prompt")
    anthropic_parser.set_defaults(func=anthropic_command)
    
    # Start MCP server command
    mcp_parser = subparsers.add_parser(
        "mcp-serve",
        help="Start an MCP server",
        parents=[server_args]
    )
    mcp_parser.add_argument("--name", default="MCP Server", help="Server name")
    mcp_parser.add_argument("--version", default="1.0.0", help="Server version")
    mcp_parser.add_argument("--description", default="MCP Server", help="Server description")
    mcp_parser.add_argument("--script", help="Python script with MCP tools")
    mcp_parser.set_defaults(func=mcp_command)
    
    # Start MCP-enabled A2A agent command
    mcp_agent_parser = subparsers.add_parser(
        "mcp-agent",
        help="Start an MCP-enabled A2A agent",
        parents=[server_args]
    )
    mcp_agent_parser.add_argument("--name", default="MCP-Enabled Agent", help="Agent name")
    mcp_agent_parser.add_argument("--description", default="MCP-Enabled A2A Agent", help="Agent description")
    mcp_agent_parser.add_argument("--config", help="JSON config file for MCP servers")
    mcp_agent_parser.add_argument("--servers", nargs="*", help="MCP servers in format 'name=url'")
    mcp_agent_parser.add_argument("--script", help="Python script with agent implementation")
    mcp_agent_parser.set_defaults(func=mcp_agent_command)
    
    # Call MCP tool command
    mcp_call_parser = subparsers.add_parser(
        "mcp-call",
        help="Call an MCP tool directly"
    )
    mcp_call_parser.add_argument("endpoint", help="MCP server endpoint URL")
    mcp_call_parser.add_argument("tool", help="Tool name to call")
    mcp_call_parser.add_argument("--params", nargs="*", help="Parameters in format 'name=value'")
    mcp_call_parser.set_defaults(func=mcp_call_command)
    
    return parser.parse_args()


def main() -> int:
    """
    Main entry point for the CLI
    
    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args()
    
    if not args.command:
        print("Error: No command specified")
        return 1
    
    if not hasattr(args, 'func'):
        print(f"Error: Unknown command '{args.command}'")
        return 1
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())