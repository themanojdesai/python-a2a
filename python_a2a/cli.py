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