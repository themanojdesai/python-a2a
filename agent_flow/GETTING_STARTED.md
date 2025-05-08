# Getting Started with Agent Flow

This guide will help you quickly set up and use Agent Flow to create powerful agent networks.

## Installation

```bash
# Install Agent Flow with all dependencies
pip install -e ".[all]"
```

## Quick Start

### 1. Start Some Agent Servers

First, you need some agents to connect to. You can use the examples provided:

```bash
# In terminal 1: Start a weather agent
python -m python_a2a.examples.getting_started.simple_server --port 8001 --agent-type weather

# In terminal 2: Start a travel agent
python -m python_a2a.examples.getting_started.simple_server --port 8002 --agent-type travel
```

### 2. Create a Workflow Using the CLI

```bash
# Discover available agents
python -m agent_flow.cli agent discover

# Create a simple workflow
python -m agent_flow.cli workflow create --name "My First Workflow"
```

### 3. Run the Example Workflow

```bash
# Run the weather trip planner example
python -m agent_flow.examples.weather_trip_planner London
```

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
python -m agent_flow.cli workflow create --file my_workflow.json

# Run your workflow
python -m agent_flow.cli workflow run YOUR_WORKFLOW_ID --input '{"query": "What is the weather in London?"}'
```

## Using the API Server

### 1. Start the Server

```bash
python -m agent_flow.cli server --port 8080
```

### 2. Access the API

The API is now available at `http://localhost:8080/api/` with the following endpoints:

- `GET /api/agents` - List all registered agents
- `POST /api/agents/discover` - Discover new agents
- `GET /api/workflows` - List all workflows
- `POST /api/workflows` - Create a new workflow
- `POST /api/workflows/{id}/run` - Run a workflow

### 3. Make API Calls

Using curl:

```bash
# Get all workflows
curl http://localhost:8080/api/workflows

# Run a workflow
curl -X POST http://localhost:8080/api/workflows/YOUR_WORKFLOW_ID/run \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the weather in Paris?"}'
```

## Creating Advanced Workflows

For more complex workflows with conditional branching:

1. Add a conditional node to check for specific conditions in responses
2. Connect the nodes with different edge types (DATA, CONDITION_TRUE, CONDITION_FALSE)
3. Add transform nodes to modify data between agents

See the `weather_trip_planner.py` example for a complete implementation.

## Adding MCP Tools

To add external tools to your workflows:

1. Start an MCP server with tools
2. Discover and register the tools using the CLI
3. Add tool nodes to your workflow

Check the `mcp_workflow.py` example for details.

## Next Steps

- Explore the examples in the `agent_flow/examples` directory
- Read the documentation in the `agent_flow/README.md` file
- Try creating more complex workflows with multiple agents and tools