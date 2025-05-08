#!/usr/bin/env python
"""
Command Line Interface for the Agent Flow workflow system.

This module provides a CLI for creating, managing, and executing workflows.
"""

import os
import sys
import json
import argparse
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

from .models.workflow import (
    Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
)
from .models.agent import AgentRegistry, AgentDefinition, AgentSource, AgentStatus
from .models.tool import ToolRegistry, ToolDefinition, ToolSource, ToolStatus
from .engine.executor import WorkflowExecutor
from .storage.workflow_storage import FileWorkflowStorage, SqliteWorkflowStorage


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentFlowCLI")


class AgentFlowCLI:
    """Command Line Interface for Agent Flow."""
    
    def __init__(self, storage_dir: Optional[str] = None):
        """
        Initialize the CLI.
        
        Args:
            storage_dir: Directory for storing data (defaults to ~/.agent_flow)
        """
        # Set up storage directory
        if not storage_dir:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".agent_flow")
        
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        
        # Initialize registries
        self.agent_registry = AgentRegistry()
        self.tool_registry = ToolRegistry()
        
        # Initialize storage
        self.workflow_storage = FileWorkflowStorage(
            os.path.join(storage_dir, "workflows")
        )
        
        # Initialize executor
        self.workflow_executor = WorkflowExecutor(
            self.agent_registry, self.tool_registry
        )
    
    def run(self, args=None):
        """
        Run the CLI with the given arguments.
        
        Args:
            args: Command line arguments (defaults to sys.argv[1:])
        """
        parser = self._create_parser()
        parsed_args = parser.parse_args(args)
        
        if not parsed_args.command:
            parser.print_help()
            return
        
        # Run the appropriate command
        command_func = parsed_args.func
        command_func(parsed_args)
    
    def _create_parser(self):
        """Create the argument parser for the CLI."""
        parser = argparse.ArgumentParser(
            description="Agent Flow - A2A-based Workflow System"
        )
        
        subparsers = parser.add_subparsers(dest="command")
        
        # Agent commands
        agent_parser = subparsers.add_parser(
            "agent", help="Manage agent definitions"
        )
        agent_subparsers = agent_parser.add_subparsers(dest="agent_command")
        
        # agent list
        agent_list_parser = agent_subparsers.add_parser(
            "list", help="List available agents"
        )
        agent_list_parser.set_defaults(func=self.agent_list)
        
        # agent add
        agent_add_parser = agent_subparsers.add_parser(
            "add", help="Add an agent"
        )
        agent_add_parser.add_argument("name", help="Name of the agent")
        agent_add_parser.add_argument("url", help="URL of the agent")
        agent_add_parser.add_argument(
            "--description", "-d",
            help="Description of the agent"
        )
        agent_add_parser.add_argument(
            "--type", "-t",
            choices=["a2a", "llm", "custom"],
            default="a2a",
            help="Type of the agent"
        )
        agent_add_parser.set_defaults(func=self.agent_add)
        
        # agent remove
        agent_remove_parser = agent_subparsers.add_parser(
            "remove", help="Remove an agent"
        )
        agent_remove_parser.add_argument("id", help="ID of the agent to remove")
        agent_remove_parser.set_defaults(func=self.agent_remove)
        
        # agent show
        agent_show_parser = agent_subparsers.add_parser(
            "show", help="Show agent details"
        )
        agent_show_parser.add_argument("id", help="ID of the agent to show")
        agent_show_parser.set_defaults(func=self.agent_show)
        
        # agent discover
        agent_discover_parser = agent_subparsers.add_parser(
            "discover", help="Discover agents"
        )
        agent_discover_parser.add_argument(
            "--base-url", "-b",
            default="http://localhost",
            help="Base URL for discovery"
        )
        agent_discover_parser.add_argument(
            "--port-min", "-p",
            type=int,
            default=8000,
            help="Minimum port number"
        )
        agent_discover_parser.add_argument(
            "--port-max", "-P",
            type=int,
            default=9000,
            help="Maximum port number"
        )
        agent_discover_parser.set_defaults(func=self.agent_discover)
        
        # Tool commands
        tool_parser = subparsers.add_parser(
            "tool", help="Manage tool definitions"
        )
        tool_subparsers = tool_parser.add_subparsers(dest="tool_command")
        
        # tool list
        tool_list_parser = tool_subparsers.add_parser(
            "list", help="List available tools"
        )
        tool_list_parser.set_defaults(func=self.tool_list)
        
        # tool discover
        tool_discover_parser = tool_subparsers.add_parser(
            "discover", help="Discover tools from an MCP server"
        )
        tool_discover_parser.add_argument(
            "url", help="URL of the MCP server"
        )
        tool_discover_parser.set_defaults(func=self.tool_discover)
        
        # Workflow commands
        workflow_parser = subparsers.add_parser(
            "workflow", help="Manage workflows"
        )
        workflow_subparsers = workflow_parser.add_subparsers(dest="workflow_command")
        
        # workflow list
        workflow_list_parser = workflow_subparsers.add_parser(
            "list", help="List workflows"
        )
        workflow_list_parser.set_defaults(func=self.workflow_list)
        
        # workflow show
        workflow_show_parser = workflow_subparsers.add_parser(
            "show", help="Show workflow details"
        )
        workflow_show_parser.add_argument("id", help="ID of the workflow to show")
        workflow_show_parser.set_defaults(func=self.workflow_show)
        
        # workflow create
        workflow_create_parser = workflow_subparsers.add_parser(
            "create", help="Create a new workflow"
        )
        workflow_create_parser.add_argument(
            "--file", "-f",
            help="JSON file containing workflow definition"
        )
        workflow_create_parser.add_argument(
            "--name", "-n",
            help="Name of the workflow"
        )
        workflow_create_parser.add_argument(
            "--description", "-d",
            help="Description of the workflow"
        )
        workflow_create_parser.set_defaults(func=self.workflow_create)
        
        # workflow delete
        workflow_delete_parser = workflow_subparsers.add_parser(
            "delete", help="Delete a workflow"
        )
        workflow_delete_parser.add_argument("id", help="ID of the workflow to delete")
        workflow_delete_parser.set_defaults(func=self.workflow_delete)
        
        # workflow run
        workflow_run_parser = workflow_subparsers.add_parser(
            "run", help="Run a workflow"
        )
        workflow_run_parser.add_argument("id", help="ID of the workflow to run")
        workflow_run_parser.add_argument(
            "--input", "-i",
            help="JSON file or string containing input data"
        )
        workflow_run_parser.add_argument(
            "--async", "-a",
            action="store_true",
            dest="async_mode",
            help="Run asynchronously and return execution ID"
        )
        workflow_run_parser.set_defaults(func=self.workflow_run)
        
        # Server commands
        server_parser = subparsers.add_parser(
            "server", help="Start API server"
        )
        server_parser.add_argument(
            "--host", "-H",
            default="localhost",
            help="Host to bind server to"
        )
        server_parser.add_argument(
            "--port", "-p",
            type=int,
            default=8080,
            help="Port to run server on"
        )
        server_parser.set_defaults(func=self.server_start)
        
        return parser
    
    # Agent commands
    
    def agent_list(self, args):
        """List available agents."""
        agents = self.agent_registry.list_agents()
        
        if not agents:
            print("No agents registered.")
            return
        
        print(f"Found {len(agents)} agents:")
        for i, agent in enumerate(agents, 1):
            status = "✓ Connected" if agent.status == AgentStatus.CONNECTED else "✗ Disconnected"
            print(f"{i}. {agent.name} ({agent.id}) - {status}")
            print(f"   URL: {agent.url}")
            if agent.description:
                print(f"   Description: {agent.description}")
            print()
    
    def agent_add(self, args):
        """Add an agent."""
        # Create agent definition
        agent = AgentDefinition(
            name=args.name,
            description=args.description or "",
            url=args.url,
            agent_source=AgentSource.REMOTE,
            agent_type=args.type
        )
        
        # Try to connect to the agent
        print(f"Connecting to agent at {args.url}...")
        if agent.connect():
            print(f"Successfully connected to agent: {agent.name}")
            
            if agent.skills:
                print(f"Agent has {len(agent.skills)} skills:")
                for skill in agent.skills:
                    print(f"- {skill.name}: {skill.description}")
        else:
            print(f"Warning: Could not connect to agent: {agent.error_message}")
            print("Adding agent anyway.")
        
        # Register the agent
        self.agent_registry.register(agent)
        print(f"Agent registered with ID: {agent.id}")
        
        return agent.id
    
    def agent_remove(self, args):
        """Remove an agent."""
        if self.agent_registry.unregister(args.id):
            print(f"Agent {args.id} removed.")
        else:
            print(f"Agent {args.id} not found.")
    
    def agent_show(self, args):
        """Show agent details."""
        agent = self.agent_registry.get(args.id)
        
        if not agent:
            print(f"Agent {args.id} not found.")
            return
        
        print(f"Agent: {agent.name} ({agent.id})")
        print(f"URL: {agent.url}")
        print(f"Description: {agent.description}")
        print(f"Type: {agent.agent_type}")
        print(f"Source: {agent.agent_source.name}")
        
        # Try to connect if not already connected
        if agent.status != AgentStatus.CONNECTED:
            print("Connecting to agent...")
            agent.connect()
        
        print(f"Status: {agent.status.name}")
        
        if agent.skills:
            print(f"\nSkills ({len(agent.skills)}):")
            for skill in agent.skills:
                print(f"- {skill.name}: {skill.description}")
        
        if agent.error_message:
            print(f"\nError: {agent.error_message}")
    
    def agent_discover(self, args):
        """Discover agents on local ports."""
        port_range = (args.port_min, args.port_max)
        print(f"Discovering agents on ports {port_range[0]}-{port_range[1]}...")
        
        agents = self.agent_registry.discover_agents(args.base_url, port_range)
        
        if not agents:
            print("No agents discovered.")
            return
        
        print(f"Discovered {len(agents)} agents:")
        for i, agent in enumerate(agents, 1):
            print(f"{i}. {agent.name} ({agent.id})")
            print(f"   URL: {agent.url}")
            if agent.description:
                print(f"   Description: {agent.description}")
            
            if agent.skills:
                print(f"   Skills: {len(agent.skills)}")
            
            print()
    
    # Tool commands
    
    def tool_list(self, args):
        """List available tools."""
        tools = self.tool_registry.list_tools()
        
        if not tools:
            print("No tools registered.")
            return
        
        print(f"Found {len(tools)} tools:")
        for i, tool in enumerate(tools, 1):
            status = "✓ Available" if tool.status == ToolStatus.AVAILABLE else "✗ Unavailable"
            print(f"{i}. {tool.name} ({tool.id}) - {status}")
            print(f"   URL: {tool.url}")
            if tool.description:
                print(f"   Description: {tool.description}")
            
            if tool.parameters:
                print(f"   Parameters: {len(tool.parameters)}")
                for param in tool.parameters:
                    required = " (required)" if param.required else ""
                    print(f"      - {param.name}: {param.type_name}{required}")
            
            print()
    
    def tool_discover(self, args):
        """Discover tools from an MCP server."""
        print(f"Discovering tools from MCP server at {args.url}...")
        
        tools = self.tool_registry.discover_tools(args.url)
        
        if not tools:
            print("No tools discovered.")
            return
        
        print(f"Discovered {len(tools)} tools:")
        for i, tool in enumerate(tools, 1):
            print(f"{i}. {tool.name} ({tool.id})")
            if tool.description:
                print(f"   Description: {tool.description}")
            
            if tool.parameters:
                print(f"   Parameters: {len(tool.parameters)}")
                for param in tool.parameters:
                    required = " (required)" if param.required else ""
                    print(f"      - {param.name}: {param.type_name}{required}")
            
            print()
    
    # Workflow commands
    
    def workflow_list(self, args):
        """List workflows."""
        workflows = self.workflow_storage.list_workflows()
        
        if not workflows:
            print("No workflows found.")
            return
        
        print(f"Found {len(workflows)} workflows:")
        for i, workflow in enumerate(workflows, 1):
            print(f"{i}. {workflow['name']} ({workflow['id']})")
            if workflow.get('description'):
                print(f"   Description: {workflow['description']}")
            
            print(f"   Created: {workflow['created_at']}")
            print(f"   Updated: {workflow['updated_at']}")
            print(f"   Version: {workflow['version']}")
            print()
    
    def workflow_show(self, args):
        """Show workflow details."""
        workflow = self.workflow_storage.load_workflow(args.id)
        
        if not workflow:
            print(f"Workflow {args.id} not found.")
            return
        
        print(f"Workflow: {workflow.name} ({workflow.id})")
        print(f"Description: {workflow.description}")
        print(f"Created: {workflow.created_at.isoformat()}")
        print(f"Updated: {workflow.updated_at.isoformat()}")
        print(f"Version: {workflow.version}")
        
        print(f"\nNodes ({len(workflow.nodes)}):")
        for node_id, node in workflow.nodes.items():
            print(f"- {node.name} ({node_id}) - Type: {node.node_type.name}")
        
        print(f"\nEdges ({len(workflow.edges)}):")
        for edge_id, edge in workflow.edges.items():
            source_node = workflow.nodes.get(edge.source_node_id, None)
            target_node = workflow.nodes.get(edge.target_node_id, None)
            
            source_name = source_node.name if source_node else "<unknown>"
            target_name = target_node.name if target_node else "<unknown>"
            
            print(f"- {source_name} -> {target_name} ({edge.edge_type.name})")
    
    def workflow_create(self, args):
        """Create a new workflow."""
        if args.file:
            # Load workflow from file
            try:
                with open(args.file, "r") as f:
                    workflow_data = json.load(f)
                
                workflow = Workflow.from_dict(workflow_data)
                
                # Override name and description if provided
                if args.name:
                    workflow.name = args.name
                
                if args.description:
                    workflow.description = args.description
                
            except Exception as e:
                print(f"Error loading workflow from file: {e}")
                return
        else:
            # Create empty workflow
            workflow = Workflow(
                name=args.name or "New Workflow",
                description=args.description or ""
            )
        
        # Validate the workflow
        valid, errors = workflow.validate()
        if not valid:
            print("Warning: Workflow is not valid:")
            for error in errors:
                print(f"- {error}")
            
            print("\nSaving workflow anyway.")
        
        # Save the workflow
        workflow_id = self.workflow_storage.save_workflow(workflow)
        print(f"Workflow saved with ID: {workflow_id}")
        
        return workflow_id
    
    def workflow_delete(self, args):
        """Delete a workflow."""
        if self.workflow_storage.delete_workflow(args.id):
            print(f"Workflow {args.id} deleted.")
        else:
            print(f"Workflow {args.id} not found.")
    
    def workflow_run(self, args):
        """Run a workflow."""
        # Load the workflow
        workflow = self.workflow_storage.load_workflow(args.id)
        
        if not workflow:
            print(f"Workflow {args.id} not found.")
            return
        
        # Parse input data if provided
        input_data = None
        if args.input:
            try:
                if os.path.isfile(args.input):
                    # Load from file
                    with open(args.input, "r") as f:
                        input_data = json.load(f)
                else:
                    # Parse as JSON string
                    input_data = json.loads(args.input)
            except Exception as e:
                print(f"Error parsing input data: {e}")
                return
        
        # Run the workflow
        print(f"Running workflow: {workflow.name} ({workflow.id})")
        
        try:
            if args.async_mode:
                # Run asynchronously
                execution_id = self.workflow_executor.execute_workflow(
                    workflow, input_data, wait=False
                )
                print(f"Workflow execution started. Execution ID: {execution_id}")
                return execution_id
            else:
                # Run synchronously
                print("Executing workflow (this may take a while)...")
                results = self.workflow_executor.execute_workflow(
                    workflow, input_data, wait=True
                )
                
                print("\nWorkflow execution completed!")
                print("\nResults:")
                for key, value in results.items():
                    print(f"{key}: {value}")
                
                return results
                
        except Exception as e:
            print(f"Error executing workflow: {e}")
    
    # Server commands
    
    def server_start(self, args):
        """Start the API server."""
        try:
            # Import here to avoid circular imports
            from .server.api import create_app
            
            print(f"Starting API server on {args.host}:{args.port}...")
            
            # Create and run Flask app
            app = create_app(
                self.agent_registry,
                self.tool_registry,
                self.workflow_storage,
                self.workflow_executor
            )
            
            app.run(host=args.host, port=args.port)
            
        except ImportError:
            print("Error: Flask is required to run the API server.")
            print("Please install Flask with: pip install flask")


def main():
    """Main entry point for the CLI."""
    cli = AgentFlowCLI()
    cli.run()


if __name__ == "__main__":
    main()