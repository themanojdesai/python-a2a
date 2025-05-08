# Agent Flow: A2A-based Workflow System

## Project Summary

Agent Flow is an n8n-like workflow system built on Python A2A for creating, managing, and executing agent networks. It provides a unified platform for connecting different agents and tools together, with powerful workflow capabilities including conditional branching, transformations, and parallel execution.

## Components Implemented

1. **Core Models**
   - `Workflow`, `WorkflowNode`, and `WorkflowEdge` for representing workflows
   - `AgentDefinition` and `AgentRegistry` for managing agent connections
   - `ToolDefinition` and `ToolRegistry` for integrating with MCP tools

2. **Workflow Engine**
   - `WorkflowExecutor` for running workflows
   - Support for conditional branching based on agent responses
   - Error handling and execution state management

3. **Storage Services**
   - `FileWorkflowStorage` for file-based persistence
   - `SqliteWorkflowStorage` for database-based persistence

4. **API and CLI**
   - REST API for programmatic workflow management
   - Command-line interface for easy workflow creation and execution

5. **Example Workflows**
   - Weather Trip Planner: Connects weather and activity agents
   - MCP Tool Workflow: Integrates with utility tools like calculators and converters

## Core Features

- **Agent Integration**: Connect to any A2A compatible agent
- **Agent Discovery**: Automatically discover agents on local ports
- **MCP Tool Integration**: Use any MCP compatible tool in workflows
- **Conditional Flows**: Create branching workflows based on responses
- **Transformations**: Transform and manipulate data between nodes
- **Persistence**: Save and load workflows for later use
- **CLI and API**: Multiple interfaces for different use cases

## Next Steps

1. **Web UI Implementation**: Create a visual editor for building workflows
2. **Enhanced Monitoring**: Add better monitoring and debugging tools
3. **Authentication and Security**: Implement authentication for API access
4. **Distributed Execution**: Support for running workflows across multiple machines

## Project Architecture

Agent Flow follows a modular, layered architecture:

```
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│  User Layer   │     │ Business Layer │     │   Data Layer  │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
┌───────▼───────┐     ┌───────▼───────┐     ┌───────▼───────┐
│   Web UI      │     │  Workflow     │     │  Persistence  │
│   CLI         │◄───►│  Engine       │◄───►│  Service      │
│   REST API    │     │               │     │               │
└───────────────┘     └───────┬───────┘     └───────────────┘
                              │                      
                      ┌───────▼───────┐               
                      │  Agent        │               
                      │  Network      │               
                      │               │                
                      └───────┬───────┘                
                              │                      
                      ┌───────▼───────┐              
                      │  MCP Tool     │              
                      │  Integration  │              
                      │               │              
                      └───────────────┘                
```

## Usage Example

Here's a simple example of how to create a workflow connecting a weather agent and an activity recommendation agent:

```python
from agent_flow.models.workflow import Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
from agent_flow.models.agent import AgentRegistry, AgentDefinition
from agent_flow.engine.executor import WorkflowExecutor

# Register agents
agent_registry = AgentRegistry()
agent_registry.register(AgentDefinition(name="Weather Agent", url="http://localhost:8000"))
agent_registry.register(AgentDefinition(name="Activity Agent", url="http://localhost:8001"))

# Create workflow
workflow = Workflow(name="Trip Planner")

# Add nodes
input_node = WorkflowNode(name="City Input", node_type=NodeType.INPUT)
weather_node = WorkflowNode(name="Weather Check", node_type=NodeType.AGENT, 
                           config={"agent_id": "weather-agent-id"})
activity_node = WorkflowNode(name="Get Activities", node_type=NodeType.AGENT,
                            config={"agent_id": "activity-agent-id"})
output_node = WorkflowNode(name="Final Output", node_type=NodeType.OUTPUT)

workflow.add_node(input_node)
workflow.add_node(weather_node)
workflow.add_node(activity_node)
workflow.add_node(output_node)

# Connect nodes
workflow.add_edge(input_node.id, weather_node.id, EdgeType.DATA)
workflow.add_edge(weather_node.id, activity_node.id, EdgeType.DATA)
workflow.add_edge(activity_node.id, output_node.id, EdgeType.DATA)

# Run the workflow
executor = WorkflowExecutor(agent_registry, None)
result = executor.execute_workflow(workflow, {"city": "London"})
```

## Conclusion

Agent Flow provides a powerful platform for building agent networks with Python A2A. It allows users to connect various agents and tools together in flexible workflows, enabling the creation of complex, agent-based applications.