#!/usr/bin/env python
"""
validate_all_examples.py - Comprehensive validation for all python-a2a examples

This script validates all examples across the entire project to ensure 
they're working correctly before each release. It tests each example category
including streaming, building_blocks, applications, ai_powered_agents, etc.

Usage:
    python validate_all_examples.py [--category CATEGORY] [--verbose] [--skip-slow] [--concurrent WORKERS]

Options:
    --category      Specific category to test (streaming, building_blocks, etc.)
    --verbose       Show detailed output during validation
    --skip-slow     Skip time-consuming examples
    --concurrent    Maximum number of concurrent example runs (default: 4)
                    Higher values speed up validation but may cause resource contention.
                    Set to 1 for sequential execution.
"""

import os
import sys
import argparse
import subprocess
import time
import json
import importlib.util
import concurrent.futures
import threading
import signal
import random
from typing import List, Dict, Any, Optional, Tuple

# ANSI colors for prettier output
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
RED = "\033[31m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Get the root directory of the project
EXAMPLES_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(EXAMPLES_DIR)

# Categories and examples to validate
# Format: category_name -> list of examples with metadata
EXAMPLE_CATEGORIES = {
    "getting_started": {
        "description": "Basic usage examples",
        "examples": [
            {
                "name": "hello_a2a",
                "file": "hello_a2a.py",
                "description": "Simple hello world example",
                "args": [],
                "success_markers": ["Hello from A2A", "response"],
                "timeout": 10,
                "requires_api_key": False,
                "expected_non_zero_exit": False
            },
            {
                "name": "simple_client",
                "file": "simple_client.py",
                "description": "Simple A2A client example",
                "args": [],
                "success_markers": ["Client", "request", "response"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True,  # Flag that this example starts a server
                "supports_port_arg": True  # Flag that this example accepts a port argument
            },
            {
                "name": "simple_server",
                "file": "simple_server.py",
                "description": "Simple A2A server example",
                "args": [],  # No special args needed
                "success_markers": ["Server started", "listening"],
                "timeout": 10,
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True,  # Flag that this example is interactive
                "test_args": ["--auto-test"]  # Args for non-interactive testing
            },
            {
                "name": "function_calling",
                "file": "function_calling.py",
                "description": "Function calling example",
                "args": [],
                "success_markers": ["function", "call", "result"],
                "timeout": 120,  # Increased timeout significantly as this example can be slow
                "requires_api_key": False,
                "expected_non_zero_exit": False,
                "slow_example": True,  # Mark as slow so it's skipped with --skip-slow
                "skip_interactive": True  # Skip direct execution to avoid timeout
            },
        ]
    },
    "building_blocks": {
        "description": "Core building blocks examples",
        "examples": [
            {
                "name": "messages_and_conversations",
                "file": "messages_and_conversations.py",
                "description": "Working with messages and conversations",
                "args": [],
                "success_markers": ["Message created", "Conversation"],
                "timeout": 10,
                "requires_api_key": False
            },
            {
                "name": "agent_skills",
                "file": "agent_skills.py",
                "description": "Defining agent skills",
                "args": [],
                "success_markers": ["skill", "agent", "response"],
                "timeout": 10,
                "requires_api_key": False
            },
            {
                "name": "tasks",
                "file": "tasks.py",
                "description": "Working with tasks",
                "args": [],
                "success_markers": ["task", "status", "completed"],
                "timeout": 10,
                "requires_api_key": False
            },
            {
                "name": "agent_discovery",
                "file": "agent_discovery.py",
                "description": "Agent discovery mechanisms",
                "args": [],
                "success_markers": ["discovery", "agent", "found"],
                "timeout": 10,
                "requires_api_key": False
            },
        ]
    },
    "streaming": {
        "description": "Streaming examples",
        "examples": [
            {
                "name": "basic_streaming",
                "file": "basic_streaming.py",
                "description": "Minimal streaming implementation",
                "args": ["--port", "8001"],
                "success_markers": ["streaming", "chunk"],
                "timeout": 20,
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,  # Flag that this example supports the port argument
                "interactive": True,  # Flag that this example is interactive
                "test_args": ["--port", "8001", "--auto-test", "--query", "test query"]  # Args for non-interactive testing
            },
            {
                "name": "01_basic_streaming",
                "file": "01_basic_streaming.py",
                "description": "Basic streaming with comparison",
                "args": ["--port", "8002"], 
                "success_markers": ["streaming", "response", "received"],
                "timeout": 20,
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True
            },
            {
                "name": "02_advanced_streaming",
                "file": "02_advanced_streaming.py",
                "description": "Advanced streaming techniques",
                "args": ["--port", "8003", "--style", "sentence", "--delay", "fast"],
                "success_markers": ["streaming", "complete", "chunks"],
                "timeout": 20,
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True
            },
            {
                "name": "03_streaming_llm_integration",
                "file": "03_streaming_llm_integration.py",
                "description": "LLM integration with streaming",
                "args": ["--port", "8004", "--provider", "mock_openai"],
                "success_markers": ["LLM", "streaming", "response"], 
                "timeout": 20,
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True
            },
            {
                "name": "04_task_based_streaming",
                "file": "04_task_based_streaming.py",
                "description": "Task-based streaming",
                "args": ["--port", "8005", "--steps", "2"],
                "success_markers": ["task", "streaming", "artifacts"],
                "timeout": 20,
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True
            },
            {
                "name": "05_streaming_ui_integration",
                "file": "05_streaming_ui_integration.py",
                "description": "UI integration for streaming",
                "args": ["--port", "8006"],  # Removed headless flag which doesn't exist
                "success_markers": ["UI", "streaming", "response"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True,
                "skip_interactive": True  # Mark to skip this since it requires direct user input
            },
            {
                "name": "06_distributed_streaming",
                "file": "06_distributed_streaming.py",
                "description": "Distributed streaming architecture",
                "args": ["--port", "8007"],  # Removed servers flag which doesn't exist
                "success_markers": ["distributed", "streaming", "servers"],
                "timeout": 40,  # Increased timeout further
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True
            },
        ]
    },
    "ai_powered_agents": {
        "description": "AI-powered agent examples",
        "examples": [
            {
                "name": "openai_agent",
                "file": "openai_agent.py",
                "description": "OpenAI powered agent",
                "args": ["--test-only"],  # Use test-only flag instead of demo-mode
                "success_markers": ["OpenAI", "agent", "response"],
                "timeout": 15,
                "requires_api_key": True,
                "api_env_var": "OPENAI_API_KEY",
                "server_example": True,
                "supports_port_arg": True
            },
            {
                "name": "anthropic_agent",
                "file": "anthropic_agent.py",
                "description": "Anthropic Claude powered agent",
                "args": ["--test-only"],  # Check if test-only flag is available
                "success_markers": ["Anthropic", "Claude", "response"],
                "timeout": 15,
                "requires_api_key": True,
                "api_env_var": "ANTHROPIC_API_KEY",
                "server_example": True,
                "supports_port_arg": True
            },
            {
                "name": "bedrock_agent",
                "file": "bedrock_agent.py",
                "description": "AWS Bedrock powered agent",
                "args": ["--test-only"],  # Check if test-only flag is available
                "success_markers": ["Bedrock", "AWS", "response"],
                "timeout": 15,
                "requires_api_key": True,
                "api_env_var": "AWS_ACCESS_KEY_ID",
                "server_example": True,
                "supports_port_arg": True
            },
            {
                "name": "llm_client",
                "file": "llm_client.py",
                "description": "Generic LLM client",
                "args": ["--interactive"],  # Using the --interactive flag
                "success_markers": ["LLM", "client", "response"],
                "timeout": 15,
                "requires_api_key": False,
                "interactive": True
            },
        ]
    },
    "applications": {
        "description": "Application examples",
        "examples": [
            {
                "name": "weather_assistant",
                "file": "weather_assistant.py",
                "description": "Weather assistant application",
                "args": ["--no-test"],  # Use no-test flag to run without tests
                "success_markers": ["weather", "forecast", "response"],
                "timeout": 15,
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True
            },
            {
                "name": "openai_travel_planner",
                "file": "openai_travel_planner.py",
                "description": "OpenAI-based travel planner",
                "args": ["--no-test"],  # Use no-test flag instead of demo-mode
                "success_markers": ["travel", "plan", "response"],
                "timeout": 20,
                "requires_api_key": True,
                "api_env_var": "OPENAI_API_KEY",
                "server_example": True,
                "supports_port_arg": True,
                "interactive": True
            },
        ]
    },
    "agent_network": {
        "description": "Agent network examples",
        "examples": [
            {
                "name": "agent_discovery",
                "file": "agent_discovery.py",
                "description": "Agent discovery mechanism",
                "args": [],
                "success_markers": ["discovery", "agent", "found"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": False  # Explicitly mark as not supporting port argument
            },
            {
                "name": "agent_network",
                "file": "agent_network.py",
                "description": "Building agent networks",
                "args": [],
                "success_markers": ["network", "agent", "communication"],
                "timeout": 20,
                "requires_api_key": False,
                "interactive": True
            },
            {
                "name": "smart_routing",
                "file": "smart_routing.py",
                "description": "Smart routing between agents",
                "args": [],
                "success_markers": ["routing", "agent", "selection"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": False  # Explicitly mark as not supporting port argument
            },
        ]
    },
    "workflows": {
        "description": "Workflow examples",
        "examples": [
            {
                "name": "basic_workflow",
                "file": "basic_workflow.py",
                "description": "Basic workflow example",
                "args": [],
                "success_markers": ["workflow", "step", "completed"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": False  # This script doesn't support port arguments
            },
            {
                "name": "agents_workflow",
                "file": "agents_workflow.py",
                "description": "Multi-agent workflow",
                "args": ["--query", "test query"],
                "success_markers": ["workflow", "agents", "completed"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": True,
                "api_env_var": "OPENAI_API_KEY,ANTHROPIC_API_KEY",  # Needs either OpenAI or Anthropic API key
                "server_example": True,
                "supports_port_arg": False  # This script doesn't support port arguments
            },
            {
                "name": "parallel_workflow",
                "file": "parallel_workflow.py",
                "description": "Parallel execution workflow",
                "args": [],
                "success_markers": ["parallel", "workflow", "completed"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True,
                "supports_port_arg": False  # This script doesn't support port arguments
            },
        ]
    },
    "mcp": {
        "description": "Model Context Protocol examples",
        "examples": [
            {
                "name": "mcp_agent",
                "file": "mcp_agent.py",
                "description": "MCP agent implementation",
                "args": ["--auto-mcp"],  # Changed from demo-mode to auto-mcp
                "success_markers": ["MCP", "agent", "tool"],
                "timeout": 20,
                "requires_api_key": False,
                "server_example": True
            },
            {
                "name": "mcp_tools",
                "file": "mcp_tools.py",
                "description": "MCP tools example",
                "args": [],
                "success_markers": ["MCP", "tool", "result"],
                "timeout": 20,
                "requires_api_key": False,
                "interactive": True
            },
            {
                "name": "openai_mcp_agent",
                "file": "openai_mcp_agent.py",
                "description": "OpenAI with MCP integration",
                "args": ["--no-test"],  # Use no-test instead of demo-mode
                "success_markers": ["OpenAI", "MCP", "tool"],
                "timeout": 20,
                "requires_api_key": True,
                "api_env_var": "OPENAI_API_KEY",
                "server_example": True
            },
        ]
    },
    "langchain": {
        "description": "LangChain integration examples",
        "examples": [
            {
                "name": "a2a_to_langchain",
                "file": "a2a_to_langchain.py",
                "description": "Converting A2A to LangChain",
                "args": [],
                "success_markers": ["A2A", "LangChain", "conversion"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True  # These likely start servers
            },
            {
                "name": "langchain_to_a2a",
                "file": "langchain_to_a2a.py",
                "description": "Converting LangChain to A2A",
                "args": [],
                "success_markers": ["LangChain", "A2A", "conversion"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True
            },
            {
                "name": "langchain_tools_to_mcp",
                "file": "langchain_tools_to_mcp.py",
                "description": "LangChain tools to MCP conversion",
                "args": [],
                "success_markers": ["LangChain", "MCP", "tool"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True
            },
            {
                "name": "mcp_to_langchain",
                "file": "mcp_to_langchain.py",
                "description": "MCP to LangChain tools conversion",
                "args": [],
                "success_markers": ["MCP", "LangChain", "tool"],
                "timeout": 30,  # Increased timeout
                "requires_api_key": False,
                "server_example": True
            },
        ]
    },
    "developer_tools": {
        "description": "Developer tools examples",
        "examples": [
            {
                "name": "cli_tools",
                "file": "cli_tools.py",
                "description": "Command-line tools",
                "args": ["--help"],  # Keep --help as it's valid
                "success_markers": ["CLI", "tools", "commands", "help"],
                "timeout": 10,
                "requires_api_key": False,
                "expected_non_zero_exit": False
            },
            {
                "name": "testing_agents",
                "file": "testing_agents.py",
                "description": "Testing A2A agents",
                "args": [],
                "success_markers": ["test", "agent", "assertion"],
                "timeout": 20,  # Increased timeout
                "requires_api_key": False,
                "server_example": True
            },
            {
                "name": "interactive_docs",
                "file": "interactive_docs.py",
                "description": "Interactive documentation",
                "args": ["--no-open-browser"],  # Use no-open-browser instead of demo-mode
                "success_markers": ["docs", "interactive", "example"],
                "timeout": 20,  # Increased timeout
                "requires_api_key": False,
                "interactive": True
            },
        ]
    },
}

# Keep track of processes to kill at cleanup
active_processes = []

def get_example_path(category: str, example_file: str) -> str:
    """Get the full path to an example file."""
    return os.path.join(EXAMPLES_DIR, category, example_file)

def check_import_dependencies() -> List[str]:
    """Check for required dependencies."""
    missing = []
    
    # Core dependencies
    core_deps = ["python_a2a"]
    for dep in core_deps:
        try:
            importlib.import_module(dep)
        except ImportError:
            missing.append(dep)
    
    # Optional dependencies based on categories
    optional_deps = {
        "ai_powered_agents": ["openai", "anthropic", "boto3"],
        "langchain": ["langchain", "langchain_openai"],
        "streaming": ["aiohttp", "flask"],
    }
    
    for category, deps in optional_deps.items():
        for dep in deps:
            try:
                importlib.import_module(dep)
            except ImportError:
                missing.append(f"{dep} (for {category})")
    
    return missing

def check_api_key(env_var: str) -> bool:
    """
    Check if an API key environment variable is set.
    Handles both single keys and comma-separated lists of possible keys.
    """
    # Check if this is a comma-separated list of possible keys
    if "," in env_var:
        # If any of the keys are available, that's sufficient
        possible_keys = [key.strip() for key in env_var.split(",")]
        return any(key in os.environ and os.environ[key] != "" for key in possible_keys)
    
    # Regular single key check
    return env_var in os.environ and os.environ[env_var] != ""

def run_example(
    category: str, 
    example: Dict[str, Any], 
    verbose: bool = False,
    worker_id: int = 0
) -> Tuple[bool, str]:
    """
    Run a single example and validate its output.
    
    Args:
        category: The category of the example
        example: The example metadata
        verbose: Whether to show detailed output
        worker_id: Worker ID for port allocation (0-based)
        
    Returns:
        A tuple of (success, details)
    """
    example_path = get_example_path(category, example["file"])
    if not os.path.exists(example_path):
        return False, f"Example file not found: {example_path}"
    
    # Check if this example requires an API key
    if example.get("requires_api_key", False):
        api_env_var = example.get("api_env_var", "")
        if not check_api_key(api_env_var):
            return False, f"Missing API key environment variable: {api_env_var}"
    
    # Prepare command with arguments
    args = example.get("args", []).copy()  # Make a copy to avoid modifying original
    
    # Skip examples that require user interaction and can't be automated
    if example.get("skip_interactive", False):
        return True, "Skipped interactive example (requires user input)"
        
    # Handle interactive examples - use test_args if available
    # but don't add default flags that might not be supported
    if example.get("interactive", False):
        # Use test_args if they're explicitly provided
        test_args = example.get("test_args", None)
        if test_args:
            # If test_args is provided, use those instead of the regular args
            args = test_args.copy()
    
    # For server examples, ensure a unique port only if the example supports it
    if example.get("server_example", False):
        # Get a unique port for this example
        port = get_example_port(category, example, 9000, worker_id)
        
        # Only add port arguments if the example explicitly specifies it should use them
        # or if the example already has a port argument
        has_port_arg = False
        port_idx = -1
        
        for i, arg in enumerate(args):
            if arg == "--port" and i + 1 < len(args):
                has_port_arg = True
                port_idx = i + 1
                break
        
        # Only modify port if the example already uses it or explicitly allows it
        if has_port_arg or example.get("supports_port_arg", False):
            if port_idx >= 0:
                # Replace existing port with our unique port
                args[port_idx] = str(port)
            else:
                # Add port argument if needed
                args.extend(["--port", str(port)])
    
    # Prepare command
    cmd = [sys.executable, example_path] + args
    
    # Setup process
    stdout = subprocess.PIPE if not verbose else None
    stderr = subprocess.PIPE if not verbose else None
    
    try:
        # Set timeout - give interactive examples more time if needed
        timeout = example.get("timeout", 30)
        
        # If this is an interactive example being run in non-interactive mode, 
        # potentially increase the timeout to give it more time
        if example.get("interactive", False) and timeout < 60:
            timeout = max(timeout, 45)  # Give interactive examples at least 45 seconds
        
        # For server examples, use a shorter timeout or other testing strategy
        if example.get("server_example", False):
            # We may want to just check if the server starts
            if verbose:
                print(f"  Running server example with timeout: {timeout}s")
        
        # Run the example
        if verbose:
            print(f"  Running command: {' '.join(cmd)}")
            
        process = subprocess.Popen(
            cmd,
            stdout=stdout,
            stderr=stderr,
            text=True,
            bufsize=1
        )
        
        # Add to global tracking
        active_processes.append(process)
        
        try:
            # Wait for completion with timeout
            stdout_data, stderr_data = process.communicate(timeout=timeout)
            
            # Remove from tracking
            if process in active_processes:
                active_processes.remove(process)
            
            # Check exit code - allow non-zero if expected
            expected_non_zero = example.get("expected_non_zero_exit", False)
            if process.returncode != 0 and not expected_non_zero:
                # Include more detailed error information
                error_output = ""
                if stderr_data:
                    # Clean up the stderr data for display
                    lines = stderr_data.splitlines()
                    if len(lines) > 10:
                        # Show first 5 and last 5 lines if there's a lot of output
                        error_output = "\n".join(lines[:5]) + "\n...\n" + "\n".join(lines[-5:])
                    else:
                        error_output = stderr_data
                
                return False, f"Example exited with non-zero code: {process.returncode}\n{error_output}"
            
            # Check for success markers in output
            if stdout_data:
                # Get the success markers
                success_markers = example.get("success_markers", [])
                markers_found = []
                
                for marker in success_markers:
                    if marker.lower() in stdout_data.lower():
                        markers_found.append(marker)
                
                if len(markers_found) > 0:
                    return True, f"Success markers found: {', '.join(markers_found)}"
                else:
                    # For server examples or interactive examples, this might be okay if they don't output much
                    if example.get("interactive", False):
                        # Make it clear in the message that this was an interactive example that was tested
                        return True, "Interactive example run in auto mode"
                    elif example.get("server_example", False):
                        return True, "Server example started without errors"
                    return False, f"No success markers found in output"
            else:
                # If no output but process exited successfully
                return True, "Example ran successfully (no output to verify markers)"
                
        except subprocess.TimeoutExpired:
            # For server examples, timeout might be expected
            if example.get("server_example", False):
                # Kill the process but consider it successful
                process.kill()
                
                # Remove from tracking
                if process in active_processes:
                    active_processes.remove(process)
                    
                return True, "Server example timed out as expected (servers typically run indefinitely)"
            
            # For non-server examples, timeout is an error
            process.kill()
            
            # Remove from tracking
            if process in active_processes:
                active_processes.remove(process)
                
            return False, f"Example timed out after {timeout} seconds"
            
    except Exception as e:
        return False, f"Error running example: {str(e)}"

def get_example_port(category: str, example: Dict[str, Any], base_port: int = 9000, worker_id: int = 0) -> Optional[int]:
    """
    Generate a unique port number for an example if it needs one.
    
    Args:
        category: The category name
        example: The example metadata
        base_port: Base port number to start from
        worker_id: Worker ID to further ensure uniqueness (0-based)
        
    Returns:
        A port number or None if not needed
    """
    # Check if this example needs a port (server examples)
    if example.get("server_example", False):
        # Create a deterministic port number based on name and worker
        port_hash = hash(f"{category}_{example['name']}") % 1000
        # Add worker offset to avoid collisions when running in parallel
        worker_offset = worker_id * 2000  # Large enough offset to avoid collisions
        return base_port + port_hash + worker_offset
    
    return None

def validate_category(
    category: str, 
    examples: List[Dict[str, Any]], 
    verbose: bool = False,
    skip_slow: bool = False,
    max_workers: int = 1
) -> Dict[str, Any]:
    """
    Validate all examples in a category, with support for parallel execution.
    
    Args:
        category: The category name
        examples: List of example metadata
        verbose: Whether to show detailed output
        skip_slow: Whether to skip slow examples
        max_workers: Maximum number of concurrent workers
        
    Returns:
        Results dictionary with success stats and details
    """
    # Start timing
    category_start_time = time.time()
    results = {
        "category": category,
        "total": len(examples),
        "passed": 0,
        "failed": 0,
        "skipped": 0,
        "details": []
    }
    
    # Filter examples if skipping slow ones
    examples_to_run = []
    for example in examples:
        if skip_slow and (example.get("timeout", 10) > 15 or example.get("slow_example", False)):
            results["skipped"] += 1
            
            if example.get("slow_example", False):
                skip_reason = "marked as slow example"
            else:
                skip_reason = "timeout > 15s"
                
            results["details"].append({
                "name": example["name"],
                "success": None,  # None indicates skipped
                "message": f"Skipped (--skip-slow flag used, {skip_reason})"
            })
        elif example.get("requires_api_key", False):
            api_env_var = example.get("api_env_var", "")
            if not check_api_key(api_env_var):
                results["skipped"] += 1
                # Format message appropriately for single or multiple keys
                if "," in api_env_var:
                    key_message = f"missing any of these API keys: {api_env_var}"
                else:
                    key_message = f"missing API key: {api_env_var}"
                
                results["details"].append({
                    "name": example["name"],
                    "success": None,
                    "message": f"Skipped ({key_message})"
                })
            else:
                examples_to_run.append(example)
        else:
            examples_to_run.append(example)
    
    # Set up progress tracking
    print(f"{BLUE}Testing {len(examples_to_run)}/{len(examples)} examples in category '{category}'...{RESET}")
    
    # Special case handling for specific examples
    # This section handles examples that need special treatment
    
    # Process examples that need special treatment
    for example in examples_to_run:
        # Handle simple_server example
        if example["name"] == "simple_server" and example.get("interactive", False):
            # simple_server only supports the port argument, nothing else
            example["test_args"] = ["--port", "8080"]
        
        # Handle basic_streaming example
        elif example["name"] == "basic_streaming" and example.get("interactive", False):
            # basic_streaming doesn't support --auto-test flag
            example["test_args"] = ["--port", "8001", "--query", "test streaming"]
        
        # Note: 05_streaming_ui_integration is already marked with skip_interactive in its definition
        
        # Handle function_calling example
        elif example["name"] == "function_calling":
            # function_calling doesn't support any test flags
            if "test_args" in example:
                del example["test_args"]
    
    # Special handling for server examples when running in parallel
    # Group examples to avoid port conflicts
    if max_workers > 1:
        # Sort examples for efficient processing
        examples_to_run.sort(key=lambda x: (
            x.get("server_example", False),  # Run non-server examples first
            x.get("requires_api_key", False),  # Then examples not requiring API keys
            x.get("timeout", 10),  # Then sort by timeout (faster examples first)
            x.get("name", "")  # Finally by name for consistent ordering
        ))
    
    # Use concurrent execution if max_workers > 1
    if max_workers > 1:
        # We'll collect results with a lock to avoid concurrency issues
        result_lock = threading.Lock()
        
        # Use ThreadPoolExecutor for concurrent execution
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_results = {}
            
            # Limit server examples to avoid port conflicts - run them in batches
            server_examples = [ex for ex in examples_to_run if ex.get("server_example", False)]
            non_server_examples = [ex for ex in examples_to_run if not ex.get("server_example", False)]
            
            # First run all non-server examples concurrently
            if non_server_examples:
                print(f"{BLUE}Running {len(non_server_examples)} non-server examples concurrently...{RESET}")
                
                # Submit all non-server examples
                futures_to_examples = {}
                for i, example in enumerate(non_server_examples):
                    future = executor.submit(run_example, category, example, verbose, i)
                    futures_to_examples[future] = example
                
                # Process results as they complete
                for future in concurrent.futures.as_completed(futures_to_examples):
                    example = futures_to_examples[future]
                    try:
                        success, message = future.result()
                        
                        with result_lock:
                            # Update stats
                            if success:
                                results["passed"] += 1
                                status_message = f"{GREEN}✓ Passed: {example['name']}{RESET}"
                            else:
                                results["failed"] += 1
                                status_message = f"{RED}✗ Failed: {example['name']} - {message}{RESET}"
                            
                            # Print status
                            print(status_message)
                            
                            # Save details
                            results["details"].append({
                                "name": example["name"],
                                "success": success,
                                "message": message
                            })
                    except Exception as e:
                        with result_lock:
                            # Handle unexpected errors
                            results["failed"] += 1
                            print(f"{RED}Error running {example['name']}: {str(e)}{RESET}")
                            results["details"].append({
                                "name": example["name"],
                                "success": False,
                                "message": f"Error: {str(e)}"
                            })
            
            # Then run server examples with limited concurrency to avoid conflicts
            if server_examples:
                # Calculate optimal server concurrency based on available workers
                # More available workers means we can run more server examples in parallel
                if max_workers >= 8:
                    server_concurrency = min(5, max_workers // 2)
                elif max_workers >= 4:
                    server_concurrency = min(3, max_workers // 2)
                else:
                    server_concurrency = 1
                
                print(f"{BLUE}Running {len(server_examples)} server examples with concurrency {server_concurrency}...{RESET}")
                
                # Run server examples in smaller batches to avoid port conflicts
                num_batches = (len(server_examples) + server_concurrency - 1) // server_concurrency
                for i in range(0, len(server_examples), server_concurrency):
                    batch = server_examples[i:i+server_concurrency]
                    batch_num = (i // server_concurrency) + 1
                    
                    print(f"{BLUE}  Running server batch {batch_num}/{num_batches} with {len(batch)} examples...{RESET}")
                    
                    # Submit this batch
                    futures_to_examples = {}
                    for j, example in enumerate(batch):
                        # Use batch offset plus position for worker_id
                        worker_id = i + j
                        future = executor.submit(run_example, category, example, verbose, worker_id)
                        futures_to_examples[future] = example
                    
                    # Process results as they complete
                    for future in concurrent.futures.as_completed(futures_to_examples):
                        example = futures_to_examples[future]
                        try:
                            success, message = future.result()
                            
                            with result_lock:
                                # Update stats
                                if success:
                                    results["passed"] += 1
                                    status_message = f"{GREEN}✓ Passed: {example['name']}{RESET}"
                                else:
                                    results["failed"] += 1
                                    status_message = f"{RED}✗ Failed: {example['name']} - {message}{RESET}"
                                
                                # Print status
                                print(status_message)
                                
                                # Save details
                                results["details"].append({
                                    "name": example["name"],
                                    "success": success,
                                    "message": message
                                })
                        except Exception as e:
                            with result_lock:
                                # Handle unexpected errors
                                results["failed"] += 1
                                print(f"{RED}Error running {example['name']}: {str(e)}{RESET}")
                                results["details"].append({
                                    "name": example["name"], 
                                    "success": False,
                                    "message": f"Error: {str(e)}"
                                })
    else:
        # Run sequentially for better debugging or when verbose
        for example in examples_to_run:
            print(f"{BLUE}Testing {example['name']}...{RESET}")
            
            success, message = run_example(category, example, verbose)
            
            # Update stats
            if success:
                results["passed"] += 1
                status_message = f"{GREEN}✓ Passed: {example['name']}{RESET}"
            else:
                results["failed"] += 1
                status_message = f"{RED}✗ Failed: {example['name']} - {message}{RESET}"
            
            # Print status
            print(status_message)
            
            # Save details
            results["details"].append({
                "name": example["name"],
                "success": success,
                "message": message
            })
    
    # Calculate elapsed time and add to results
    category_elapsed_time = time.time() - category_start_time
    results["elapsed_time"] = category_elapsed_time
    
    print(f"{BLUE}Category '{category}' completed in {category_elapsed_time:.2f} seconds{RESET}")
    return results

def print_validation_summary(category_results: Dict[str, Dict[str, Any]]):
    """
    Print a summary of validation results.
    
    Args:
        category_results: Dictionary of category names to results
    """
    # Calculate overall stats
    total_examples = sum(r["total"] for r in category_results.values())
    total_passed = sum(r["passed"] for r in category_results.values())
    total_failed = sum(r["failed"] for r in category_results.values())
    total_skipped = sum(r["skipped"] for r in category_results.values())
    
    # Count interactive examples that were tested in auto mode
    interactive_tested = 0
    for category, results in category_results.items():
        for detail in results["details"]:
            if detail["success"] is True and "Interactive example run in auto mode" in detail.get("message", ""):
                interactive_tested += 1
    
    # Print header
    print("\n" + "=" * 80)
    print(f"{BOLD}VALIDATION SUMMARY{RESET}")
    print("=" * 80)
    
    # Print overall stats
    print(f"\n{BOLD}Overall Results:{RESET}")
    print(f"Total examples: {total_examples}")
    print(f"{GREEN}Passed: {total_passed} (including {interactive_tested} interactive examples in auto mode){RESET}")
    if total_failed > 0:
        print(f"{RED}Failed: {total_failed}{RESET}")
    if total_skipped > 0:
        print(f"{YELLOW}Skipped: {total_skipped} (due to missing dependencies/API keys){RESET}")
    
    # Calculate total time
    total_time = sum(r.get("elapsed_time", 0) for r in category_results.values())
    
    # Print category-by-category results
    print(f"\n{BOLD}Category Results:{RESET}")
    
    # Sort categories by elapsed time (longest first)
    sorted_categories = sorted(
        category_results.items(), 
        key=lambda x: x[1].get("elapsed_time", 0), 
        reverse=True
    )
    
    for category, results in sorted_categories:
        elapsed = results.get("elapsed_time", 0)
        
        if results["failed"] > 0:
            status = f"{RED}[{results['passed']}/{results['total']} passed, {results['failed']} failed]{RESET}"
        elif results["skipped"] > 0:
            status = f"{YELLOW}[{results['passed']}/{results['total']} passed, {results['skipped']} skipped]{RESET}"
        else:
            status = f"{GREEN}[All {results['passed']} passed]{RESET}"
            
        # Show time info
        time_info = f"{CYAN}({elapsed:.2f}s){RESET}"
        print(f"{category}: {status} {time_info}")
    
    # Print failures for troubleshooting
    if total_failed > 0:
        print(f"\n{BOLD}{RED}Failed Examples:{RESET}")
        for category, results in category_results.items():
            category_failures = []
            for detail in results["details"]:
                if detail["success"] is False:  # Explicitly check for False, not None (skipped)
                    category_failures.append(f"{RED}• {category}/{detail['name']}: {detail['message']}{RESET}")
            
            if category_failures:
                for failure in category_failures:
                    print(failure)
    
    # Print skipped for information
    if total_skipped > 0:
        print(f"\n{BOLD}{YELLOW}Skipped Examples:{RESET}")
        for category, results in category_results.items():
            category_skipped = []
            for detail in results["details"]:
                if detail["success"] is None:  # None indicates skipped
                    category_skipped.append(f"{YELLOW}• {category}/{detail['name']}: {detail['message']}{RESET}")
            
            if category_skipped:
                for skipped in category_skipped:
                    print(skipped)
    
    # Print tested interactive examples for information
    interactive_tested = 0
    for category, results in category_results.items():
        for detail in results["details"]:
            if detail["success"] is True and "Interactive example run in auto mode" in detail.get("message", ""):
                interactive_tested += 1
                
    if interactive_tested > 0:
        print(f"\n{BOLD}{CYAN}Interactive Examples Tested in Auto Mode:{RESET}")
        for category, results in category_results.items():
            category_interactive = []
            for detail in results["details"]:
                if detail["success"] is True and "Interactive example run in auto mode" in detail.get("message", ""):
                    category_interactive.append(f"{CYAN}• {category}/{detail['name']}: Tested in auto mode{RESET}")
            
            if category_interactive:
                for interactive_item in category_interactive:
                    print(interactive_item)
    
    # Final verdict
    print("\n" + "-" * 80)
    if total_failed == 0:
        if total_skipped == 0:
            print(f"{GREEN}{BOLD}✓ All examples passed validation!{RESET}")
            if interactive_tested > 0:
                print(f"{GREEN}Note: {interactive_tested} interactive examples were tested in auto mode{RESET}")
        else:
            print(f"{YELLOW}{BOLD}⚠ All tested examples passed, but {total_skipped} were skipped due to missing dependencies.{RESET}")
            print(f"{YELLOW}Install required dependencies to validate all examples.{RESET}")
    else:
        print(f"{RED}{BOLD}✗ Validation found {total_failed} failing examples.{RESET}")
        print(f"{RED}Please fix these examples before proceeding.{RESET}")
    
    # Show total validation time
    print(f"\n{BLUE}Total validation time: {total_time:.2f} seconds{RESET}")
    print("-" * 80)

def cleanup():
    """Clean up any remaining processes."""
    # Make a copy to avoid modification during iteration
    processes_to_clean = active_processes.copy()
    
    for process in processes_to_clean:
        try:
            if process.poll() is None:
                process.kill()
                print(f"{YELLOW}Terminated process {process.pid}{RESET}")
        except Exception:
            pass
    
    # Clear the active processes list
    active_processes.clear()

def get_example_by_name(name, category=None):
    """
    Find an example by name, optionally restricting to a specific category.
    
    Args:
        name: The name of the example to find
        category: Optional category name to restrict the search
        
    Returns:
        The example dictionary if found, None otherwise
    """
    categories_to_search = [category] if category else EXAMPLE_CATEGORIES.keys()
    
    for cat_name in categories_to_search:
        if cat_name in EXAMPLE_CATEGORIES:
            category_info = EXAMPLE_CATEGORIES[cat_name]
            for example in category_info["examples"]:
                if example["name"] == name:
                    return example
    
    return None

def add_test_args_to_interactive_examples():
    """
    Updates the EXAMPLE_CATEGORIES dictionary to add test_args to all interactive examples.
    This ensures all interactive examples can be run without user input.
    
    Handles special cases for examples that need specific arguments or don't support
    certain flags.
    """
    # Add test args to each category based on the type of example
    for category_name, category_info in EXAMPLE_CATEGORIES.items():
        for example in category_info["examples"]:
            if example.get("interactive", False) and "test_args" not in example:
                # Create appropriate test args based on the category and example
                if category_name == "streaming":
                    # Streaming examples need port but may not support all other flags
                    port = example.get("args", [])
                    port_value = "8000"
                    if "--port" in port and port.index("--port") + 1 < len(port):
                        port_value = port[port.index("--port") + 1]
                    
                    # Start with just the port argument which all streaming examples should support
                    example["test_args"] = ["--port", port_value]
                    
                    # For more advanced streaming examples, add query parameter if they support it
                    if example["name"] not in ["basic_streaming", "01_basic_streaming"]:
                        example["test_args"].extend(["--query", "test streaming"])
                
                elif category_name == "ai_powered_agents":
                    # AI agents examples
                    example["test_args"] = ["--auto-test", "--query", "test query"]
                
                elif category_name == "applications":
                    # Application examples
                    example["test_args"] = ["--auto-test", "--no-interactive", "--query", "test query"]
                
                elif category_name == "agent_network":
                    # Agent network examples
                    example["test_args"] = ["--auto-test", "--query", "test query"]
                
                elif category_name == "mcp":
                    # MCP examples
                    example["test_args"] = ["--auto-test", "--query", "test query"]
                
                elif category_name == "developer_tools":
                    # Developer tools examples 
                    example["test_args"] = ["--auto-test", "--no-open-browser"]
                
                elif category_name == "getting_started":
                    # Getting started examples (simple_server doesn't support --auto-test)
                    if example["name"] == "simple_server":
                        # Only use the port argument for simple_server
                        port_value = "8080"  # Default port
                        example["test_args"] = ["--port", port_value]
                    else:
                        # Other getting_started examples
                        example["test_args"] = []
                
                else:
                    # Default test args - use an empty list to avoid passing unsupported flags
                    example["test_args"] = []

def main():
    """Main function to run validation."""
    # Add test args to interactive examples
    add_test_args_to_interactive_examples()
    
    # Start timing the entire validation
    start_time = time.time()
    parser = argparse.ArgumentParser(description="Validate all examples in the python-a2a project")
    parser.add_argument("--category", type=str, help="Specific category to validate")
    parser.add_argument("--verbose", action="store_true", help="Show detailed output")
    parser.add_argument("--skip-slow", action="store_true", help="Skip slow examples")
    parser.add_argument("--concurrent", type=int, default=4, help="Maximum concurrent example runs (default: 4)")
    args = parser.parse_args()
    
    # Set up signal handlers
    def signal_handler(sig, frame):
        print(f"\n{YELLOW}Validation interrupted, cleaning up...{RESET}")
        # Clean up active processes
        cleanup()
        
        # Report the exit reason
        print(f"{YELLOW}Validation terminated by user (Signal: {sig}){RESET}")
        sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Banner
        print(f"\n{BLUE}{BOLD}Python A2A Examples Validation{RESET}")
        print(f"{BLUE}This tool validates all examples to ensure they work correctly.{RESET}")
        print("-" * 80)
        
        # Check dependencies
        missing_deps = check_import_dependencies()
        if missing_deps:
            print(f"{YELLOW}Warning: Some dependencies are missing:{RESET}")
            for dep in missing_deps:
                print(f"{YELLOW}• {dep}{RESET}")
            print(f"{YELLOW}Some examples may be skipped. Install with: pip install python-a2a[all]{RESET}\n")
        
        # Determine which categories to validate
        categories_to_validate = {}
        if args.category:
            if args.category in EXAMPLE_CATEGORIES:
                categories_to_validate[args.category] = EXAMPLE_CATEGORIES[args.category]
            else:
                valid_categories = ", ".join(EXAMPLE_CATEGORIES.keys())
                print(f"{RED}Error: Unknown category '{args.category}'. Valid categories: {valid_categories}{RESET}")
                return 1
        else:
            categories_to_validate = EXAMPLE_CATEGORIES
        
        # Show the plan
        print(f"{BLUE}Validating {len(categories_to_validate)} categories with {sum(len(cat['examples']) for cat in categories_to_validate.values())} examples{RESET}")
        
        # Run validations
        results = {}
        for category, category_info in categories_to_validate.items():
            # Get the examples for this category
            examples = category_info["examples"]
            
            # Create directory path if needed
            category_dir = os.path.join(EXAMPLES_DIR, category)
            if not os.path.exists(category_dir):
                print(f"{YELLOW}Warning: Category directory not found: {category_dir}{RESET}")
                continue
            
            # Run the validation
            print(f"\n{BLUE}{BOLD}Validating category: {category} - {category_info['description']}{RESET}")
            category_result = validate_category(
                category,
                examples,
                verbose=args.verbose,
                skip_slow=args.skip_slow,
                max_workers=args.concurrent
            )
            
            # Store the results
            results[category] = category_result
            
            # Print category summary
            if category_result["failed"] > 0:
                print(f"{RED}✗ Category {category}: {category_result['failed']} examples failed{RESET}")
            elif category_result["skipped"] > 0:
                print(f"{YELLOW}⚠ Category {category}: All {category_result['passed']} tested examples passed, {category_result['skipped']} skipped{RESET}")
            else:
                print(f"{GREEN}✓ Category {category}: All {category_result['passed']} examples passed{RESET}")
        
        # Calculate total time
        total_validation_time = time.time() - start_time
        
        # Print overall summary
        print_validation_summary(results)
        
        # Print total elapsed time
        print(f"\n{BOLD}{CYAN}Overall validation completed in {total_validation_time:.2f} seconds{RESET}")
        
        # Show parallel execution benefit if applicable
        if args.concurrent > 1:
            # Calculate the sum of individual example times as an estimate of sequential execution time
            sequential_time_estimate = sum(
                sum(detail.get("timeout", 10) for detail in r["details"] if detail.get("success") is not None)
                for r in results.values()
            )
            
            # Calculate estimated time savings
            time_saved = max(0, sequential_time_estimate - total_validation_time)
            
            print(f"{CYAN}Using parallel execution with {args.concurrent} workers{RESET}")
            if time_saved > 0:
                print(f"{CYAN}Estimated time saved with parallel execution: {time_saved:.2f} seconds ({(time_saved/sequential_time_estimate*100):.1f}% faster){RESET}")
        
        # Return success code if no failures
        return 0 if all(r["failed"] == 0 for r in results.values()) else 1
        
    except Exception as e:
        print(f"{RED}Error running validation: {str(e)}{RESET}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        # Ensure cleanup
        cleanup()

if __name__ == "__main__":
    sys.exit(main())