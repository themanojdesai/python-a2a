# Agent Flow

An n8n-like workflow system for creating and managing A2A agent networks.

## Overview

Agent Flow is a Python-based workflow system that allows you to:

- Connect multiple A2A agents together into networks
- Use conditional branching, transformations, and parallel execution
- Integrate with MCP tools for additional functionality
- Create, save, and run complex workflows
- Build powerful agent-based applications

Based on the Python A2A framework, Agent Flow provides a unified way to connect LLMs, agents, and tools.

## Features

- **Agent Integration**: Connect to local and remote A2A agents
- **Agent Management**: Create, monitor, and control A2A agents from templates
- **Tool Integration**: Use MCP tools in your workflows
- **Workflow Engine**: Powerful execution engine with conditional branching
- **Visual Editor**: Drag-and-drop interface for building workflows
- **CLI Interface**: Command-line interface for managing workflows
- **REST API**: HTTP API for programmatic access
- **Persistence**: Save and load workflows

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/agent-flow.git

# Install with all dependencies
cd agent-flow
pip install -e ".[all]"
```

## Quick Start

### Running the Example Workflows

Agent Flow comes with example workflows to help you get started:

1. Weather Trip Planner:

```bash
python -m agent_flow.examples.weather_trip_planner Tokyo
```

2. MCP Tool Workflow:

```bash
python -m agent_flow.examples.mcp_workflow "calculate 15 * 7"
```

### CLI Usage

Agent Flow provides a command-line interface for managing agents, tools, and workflows:

```bash
# List available commands
python -m agent_flow.cli

# Discover and add agents
python -m agent_flow.cli agent discover

# Create and run a workflow
python -m agent_flow.cli workflow create --file my_workflow.json
python -m agent_flow.cli workflow run WORKFLOW_ID
```

## Architecture

Agent Flow is built on a modular architecture:

- **Models**: Core data models for workflows, agents, and tools
- **Engine**: Execution engine for running workflows
- **Storage**: Storage services for saving and loading workflows
- **Server**: REST API and web interface
- **CLI**: Command-line interface

## Web UI and REST API

Start the web server and API:

```bash
python -m agent_flow.cli server --port 8080
```

Then open your browser to http://localhost:8080 to access the visual editor.

The API provides endpoints for:
- `/api/agents`: Managing agent definitions
- `/api/tools`: Managing tool definitions
- `/api/workflows`: Managing workflows
- `/api/executions`: Managing workflow executions
- `/api/agent_templates`: List agent templates
- `/api/agent_servers`: Manage running agent servers
- `/api/create_agent`: Create agents from templates
- `/api/import_agents`: Import agent collections
- `/api/export_agents`: Export agent collections

### Agent Management

Agent Flow includes a comprehensive agent management system that allows you to:

1. Create agents from templates, including:
   - Weather Agent
   - Travel Agent 
   - Math Agent
   - Knowledge Agent
   - OpenAI-powered Agent (requires API key)
   - Anthropic-powered Agent (requires API key)
   - Custom Script Agent

2. Monitor agent health and status
3. Start and stop agent servers
4. Import and export agent configurations

The agent management UI is accessible at http://localhost:8080/agents

## License

This project is licensed under the MIT License - see the LICENSE file for details.