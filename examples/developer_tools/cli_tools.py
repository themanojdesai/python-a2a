#!/usr/bin/env python
"""
CLI Tools Example

This example demonstrates how to use and create command-line interface (CLI)
tools for working with A2A agents. It shows how to create agents, interact
with them via terminal, and connect to remote agents using the CLI.

To run:
    python cli_tools.py [--command COMMAND]

Commands:
    chat    Start a chat session with an A2A agent
    create  Create a new A2A agent from a template
    info    Display information about an A2A agent
    help    Show help information

Example:
    python cli_tools.py --command chat --url http://localhost:5000

Requirements:
    pip install "python-a2a[server]" rich
"""

import sys
import os
import argparse
import json
import time
import subprocess
import tempfile
from pathlib import Path

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import python_a2a
    except ImportError:
        missing_deps.append("python-a2a")
    
    try:
        import rich
    except ImportError:
        missing_deps.append("rich")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required packages:")
        print("    pip install \"python-a2a[server]\" rich")
        print("\nThen run this example again.")
        return False
    
    print("✅ Dependencies installed correctly!")
    return True

def parse_arguments():
    """Parse command line arguments for the main script"""
    parser = argparse.ArgumentParser(description="A2A CLI Tools Example")
    parser.add_argument(
        "--command", type=str, choices=["chat", "create", "info", "help"],
        default="help",
        help="Command to execute (default: help)"
    )
    parser.add_argument(
        "--url", type=str,
        help="URL of the A2A agent for chat and info commands"
    )
    parser.add_argument(
        "--template", type=str, choices=["calculator", "weather", "custom"],
        default="calculator",
        help="Template to use for agent creation (default: calculator)"
    )
    parser.add_argument(
        "--output", type=str,
        help="Output directory or file for the create command"
    )
    return parser.parse_args()

# --- Rich UI Components ---

def setup_rich_console():
    """Set up a Rich console for prettier CLI output"""
    try:
        from rich.console import Console
        from rich.theme import Theme
        from rich.panel import Panel
        from rich.syntax import Syntax
        from rich.markdown import Markdown
        
        # Create a custom theme
        custom_theme = Theme({
            "info": "dim cyan",
            "warning": "yellow",
            "danger": "bold red",
            "success": "green",
            "command": "bold blue",
            "url": "underline cyan",
            "agent": "bold magenta",
            "user": "bold green",
            "response": "cyan",
            "code": "bright_black on black",
        })
        
        # Return a console with our custom theme
        return Console(theme=custom_theme)
    except ImportError:
        # Fallback if Rich is not installed
        class FallbackConsole:
            def print(self, *args, **kwargs):
                style = kwargs.get("style", "")
                if "danger" in style:
                    print("\033[91m", end="")  # Red
                elif "success" in style:
                    print("\033[92m", end="")  # Green
                elif "warning" in style:
                    print("\033[93m", end="")  # Yellow
                elif "info" in style:
                    print("\033[96m", end="")  # Cyan
                
                print(*args, end="")
                print("\033[0m")  # Reset color
        
        return FallbackConsole()

# --- Command Functions ---

def command_help(console, args):
    """Show help information for the CLI tools"""
    from rich.panel import Panel
    from rich.table import Table
    
    console.print("\n[bold]A2A CLI Tools Example[/bold]")
    console.print("This example demonstrates how to use command-line tools with A2A agents.\n")
    
    # Create a commands table
    table = Table(title="Available Commands")
    table.add_column("Command", style="command")
    table.add_column("Description")
    table.add_column("Usage Example", style="dim")
    
    table.add_row(
        "chat",
        "Start a chat session with an A2A agent",
        "python cli_tools.py --command chat --url http://localhost:5000"
    )
    table.add_row(
        "create",
        "Create a new A2A agent from a template",
        "python cli_tools.py --command create --template calculator --output ./my_agent.py"
    )
    table.add_row(
        "info",
        "Display information about an A2A agent",
        "python cli_tools.py --command info --url http://localhost:5000"
    )
    table.add_row(
        "help",
        "Show this help information",
        "python cli_tools.py --command help"
    )
    
    console.print(table)
    
    # Show additional info panel
    console.print(Panel(
        "You can also use the a2a command directly if installed as a package:\n"
        "[command]a2a chat --url http://localhost:5000[/command]\n"
        "[command]a2a create --template calculator[/command]\n"
        "[command]a2a info --url http://localhost:5000[/command]",
        title="Using the A2A CLI Tool",
        expand=False
    ))
    
    console.print("\n[info]For more information on installing and using A2A, see the documentation.[/info]\n")
    return 0

def command_chat(console, args):
    """Start a chat session with an A2A agent"""
    # Check if URL is provided
    if not args.url:
        console.print("[danger]Error: The --url argument is required for the chat command.[/danger]")
        console.print("[info]Example: python cli_tools.py --command chat --url http://localhost:5000[/info]")
        return 1
    
    try:
        from python_a2a import A2AClient
        from rich.markdown import Markdown
        
        # Connect to the agent
        console.print(f"\nConnecting to [url]{args.url}[/url]...", end="")
        client = A2AClient(args.url)
        console.print(" [success]Connected![/success]")
        
        # Get agent information
        try:
            agent_info = client.agent_card
            console.print(f"\n[bold]Chat with [agent]{agent_info.name}[/agent] (v{agent_info.version})[/bold]")
            console.print(f"[dim]{agent_info.description}[/dim]\n")
            
            # Display available skills if present
            if hasattr(agent_info, 'skills') and agent_info.skills:
                console.print("[info]Available skills:[/info]")
                for skill in agent_info.skills:
                    console.print(f"[info]- {skill.name}: {skill.description}[/info]")
                console.print()
        except Exception as e:
            console.print(f"[warning]Could not retrieve agent information: {e}[/warning]")
            console.print("[warning]The agent may not support the A2A discovery protocol.[/warning]")
        
        # Interactive chat loop
        console.print("[bold]Enter your messages below. Type 'exit', 'quit', or 'q' to end the session.[/bold]")
        console.print("[bold]Press Ctrl+C at any time to exit.[/bold]\n")
        
        while True:
            try:
                # Get user input
                user_input = input("[user]You[/user]: ")
                
                # Check for exit commands
                if user_input.lower() in ["exit", "quit", "q"]:
                    console.print("\n[info]Chat session ended.[/info]")
                    break
                
                # Skip empty messages
                if not user_input.strip():
                    continue
                
                # Send to agent and get response
                console.print("[dim]Sending message...[/dim]")
                start_time = time.time()
                response = client.ask(user_input)
                elapsed = time.time() - start_time
                
                # Print response with Markdown formatting if possible
                try:
                    console.print(f"\n[agent]Agent[/agent] [dim]({elapsed:.2f}s)[/dim]:")
                    console.print(Markdown(response))
                except:
                    # Fallback to plain text if Markdown parsing fails
                    console.print(f"\n[agent]Agent[/agent]: {response}")
                
                console.print()  # Add a blank line for readability
                
            except KeyboardInterrupt:
                console.print("\n\n[info]Chat session interrupted.[/info]")
                break
            except Exception as e:
                console.print(f"\n[danger]Error: {e}[/danger]")
                console.print("[info]Try sending a different message or check your connection.[/info]\n")
        
        return 0
            
    except ImportError as e:
        console.print(f"[danger]Error: Required module not found - {e}[/danger]")
        return 1
    except Exception as e:
        console.print(f"[danger]Error connecting to agent: {e}[/danger]")
        console.print("\n[info]Possible reasons:[/info]")
        console.print("[info]- The URL is incorrect[/info]")
        console.print("[info]- The agent server is not running[/info]")
        console.print("[info]- Network connectivity issues[/info]")
        return 1

def command_info(console, args):
    """Display information about an A2A agent"""
    # Check if URL is provided
    if not args.url:
        console.print("[danger]Error: The --url argument is required for the info command.[/danger]")
        console.print("[info]Example: python cli_tools.py --command info --url http://localhost:5000[/info]")
        return 1
    
    try:
        from python_a2a import A2AClient
        from rich.panel import Panel
        from rich.table import Table
        
        # Connect to the agent
        console.print(f"\nConnecting to [url]{args.url}[/url]...", end="")
        client = A2AClient(args.url)
        console.print(" [success]Connected![/success]")
        
        # Get agent information
        try:
            agent_info = client.agent_card
            
            # Create and display agent info panel
            console.print(Panel(
                f"[bold]{agent_info.name}[/bold] (v{agent_info.version})\n"
                f"{agent_info.description}\n\n"
                f"URL: [url]{agent_info.url}[/url]",
                title="Agent Information"
            ))
            
            # Display capabilities if present
            if hasattr(agent_info, 'capabilities') and agent_info.capabilities:
                capability_list = []
                for name, enabled in agent_info.capabilities.items():
                    if enabled:
                        capability_list.append(f"[success]✓[/success] {name}")
                    else:
                        capability_list.append(f"[danger]✗[/danger] {name}")
                
                if capability_list:
                    console.print(Panel(
                        "\n".join(capability_list),
                        title="Capabilities"
                    ))
            
                            # Display skills if present
            if hasattr(agent_info, 'skills') and agent_info.skills:
                # Create a skills table
                skills_table = Table(title="Available Skills")
                skills_table.add_column("Name", style="bold")
                skills_table.add_column("Description")
                skills_table.add_column("Tags", style="dim")
                
                for skill in agent_info.skills:
                    tags = ", ".join(skill.tags) if hasattr(skill, 'tags') and skill.tags else ""
                    skills_table.add_row(skill.name, skill.description, tags)
                
                console.print(skills_table)
                
                # Show examples for skills if available
                for skill in agent_info.skills:
                    if hasattr(skill, 'examples') and skill.examples:
                        console.print(f"\n[bold]Examples for {skill.name}:[/bold]")
                        for example in skill.examples:
                            console.print(f"- [dim]{example}[/dim]")
            
            # Display API documentation URL if available
            if hasattr(agent_info, 'documentation_url') and agent_info.documentation_url:
                console.print(f"\n[info]Documentation: [url]{agent_info.documentation_url}[/url][/info]")
            
            return 0
            
        except Exception as e:
            console.print(f"[warning]Could not retrieve agent information: {e}[/warning]")
            console.print("[warning]The agent may not support the A2A discovery protocol.[/warning]")
            return 1
            
    except ImportError as e:
        console.print(f"[danger]Error: Required module not found - {e}[/danger]")
        return 1
    except Exception as e:
        console.print(f"[danger]Error connecting to agent: {e}[/danger]")
        console.print("\n[info]Possible reasons:[/info]")
        console.print("[info]- The URL is incorrect[/info]")
        console.print("[info]- The agent server is not running[/info]")
        console.print("[info]- Network connectivity issues[/info]")
        return 1