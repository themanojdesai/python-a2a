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

Agent Flow is included as part of the python-a2a package. To start using it:

```bash
# Install python-a2a
pip install python-a2a

# Or install in development mode
pip install -e .

# Start the Agent Flow UI
a2a ui
```

The UI will automatically open in your browser at http://localhost:8080.

## Quick Start

### 1. Start the Agent Flow UI

Start the Agent Flow UI to begin creating workflows:

```bash
# Start the UI server
a2a ui
```

This will open the UI in your browser at http://localhost:8080.

### 2. Discover and Connect Agents

In the UI, you can discover and connect to agents:

1. Go to the "Agents" tab in the UI
2. Click "Discover Agents" to find agents on your network
3. Add agents manually by providing their URL

Or use the CLI to discover agents:

```bash
# Discover agents using the command line
a2a agent discover
```

### 3. Build Workflows in the UI

After discovering agents, you can build workflows using the visual editor:

1. Drag and drop nodes onto the canvas
2. Connect nodes with edges
3. Configure node properties
4. Save and run your workflow

## Creating Your Own Workflow

### 1. Define Your Workflow in JSON

Create a file called `my_workflow.json`:

```json
{
  "name": "Simple Agent Workflow",
  "description": "A basic workflow connecting two agents",
  "nodes": [
    {
      "id": "input",
      "name": "User Input",
      "type": "INPUT",
      "position": {"x": 100, "y": 100},
      "config": {
        "input_key": "query"
      }
    },
    {
      "id": "weather",
      "name": "Weather Agent",
      "type": "AGENT",
      "position": {"x": 400, "y": 100},
      "config": {
        "agent_id": "REPLACE_WITH_WEATHER_AGENT_ID"
      }
    },
    {
      "id": "output",
      "name": "Result",
      "type": "OUTPUT",
      "position": {"x": 700, "y": 100},
      "config": {
        "output_key": "result"
      }
    }
  ],
  "edges": [
    {
      "id": "e1",
      "source": "input",
      "target": "weather",
      "type": "DATA"
    },
    {
      "id": "e2",
      "source": "weather",
      "target": "output",
      "type": "DATA"
    }
  ]
}
```

Replace `REPLACE_WITH_WEATHER_AGENT_ID` with the actual agent ID from the discovery step.

### 2. Import and Run Your Workflow

```bash
# Import your workflow
a2a workflow create --file my_workflow.json

# Run your workflow
a2a workflow run YOUR_WORKFLOW_ID --input '{"query": "What is the weather in London?"}'
```

## Architecture

Agent Flow is built on a modular architecture:

- **Models**: Core data models for workflows, agents, and tools
- **Engine**: Execution engine for running workflows
- **Storage**: Storage services for saving and loading workflows
- **Server**: REST API and web interface
- **CLI**: Command-line interface

## Web UI and REST API

Start the Agent Flow UI:

```bash
a2a ui
```

The browser will automatically open to http://localhost:8080 to access the visual editor.

Command options:
- `--port PORT`: Specify a custom port (default: 8080)
- `--host HOST`: Specify a custom host (default: localhost)
- `--storage-dir DIR`: Specify a directory for workflow storage
- `--no-browser`: Don't open browser automatically
- `--debug`: Enable debug mode

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

## Creating Advanced Workflows

For more complex workflows with conditional branching:

1. Add a conditional node to check for specific conditions in responses
2. Connect the nodes with different edge types (DATA, CONDITION_TRUE, CONDITION_FALSE)
3. Add transform nodes to modify data between agents

## Adding MCP Tools

To add external tools to your workflows:

1. Start an MCP server with tools
2. Discover and register the tools using the UI or CLI
3. Add tool nodes to your workflow and configure them

## Next Steps

- Check the API docs at http://localhost:8080/api/docs
- Create complex workflows with multiple agents and tools
- Connect your own AI models and agents
- Contribute to the project by submitting issues and pull requests

## License

This project is licensed under the MIT License - see the LICENSE file for details.