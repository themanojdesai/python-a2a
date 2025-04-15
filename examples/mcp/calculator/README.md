# MCP-Enabled Calculator Example

This example demonstrates how to create a calculator agent that leverages Model Context Protocol (MCP) capabilities and how to build another agent that can communicate with it using the A2A protocol.

## Prerequisites

Before running this example, ensure you have the required packages installed:

```bash
# Install python-a2a with all dependencies
pip install "python-a2a[all]"

# Install additional dependencies
pip install httpx uvicorn fastapi pydantic
```

## Overview

This example showcases a multi-agent system with three components:

1. **MCP Calculator Agent**: A powerful calculator agent that uses MCP to provide mathematical operations
2. **Math Assistant Agent**: An intelligent agent that processes natural language queries and delegates calculations to the calculator agent
3. **Math Assistant Client**: A user-friendly client application for interacting with the math assistant agent

This architecture demonstrates the power of agent interoperability, where specialized agents can expose their capabilities through standardized protocols, enabling other agents to leverage these capabilities without needing to implement them directly.

## Components

### MCP Calculator Agent (`mcp_calculator_agent.py`)

The calculator agent exposes mathematical operations as MCP tools, including:
- Addition
- Subtraction
- Multiplication
- Division
- Square root

It uses FastMCP to define these operations with proper parameter typing and validation, making them easily accessible via the A2A protocol.

### Math Assistant Agent (`math_assistant_agent.py`)

The math assistant agent provides a natural language interface for mathematical operations:
- Accepts queries in plain English (e.g., "What is 5 plus 3?")
- Parses these queries to identify the operation and extract numbers
- Calls the appropriate function on the calculator agent using A2A
- Formats the results in a user-friendly way
- Handles errors gracefully

### Math Assistant Client (`math_assistant_client.py`)

A simple interactive client that allows users to:
- Connect to the math assistant agent
- Send natural language queries about mathematical operations
- View responses in a well-formatted way
- Maintain conversation history

## Running the Example

1. Start the MCP calculator agent:
   ```bash
   python mcp_calculator_agent.py --port 5004
   ```

2. Start the math assistant agent (in another terminal):
   ```bash
   python math_assistant_agent.py --port 5005 --calculator http://localhost:5004/a2a
   ```

3. Start the client to interact with the math assistant (in a third terminal):
   ```bash
   python math_assistant_client.py
   ```

4. Try asking the math assistant various questions:
   - "What is 5 plus 3?"
   - "Calculate 10 minus 7"
   - "Multiply 4 and 9"
   - "Divide 20 by 5"
   - "What's the square root of 16?"

## Architecture Diagram

```
┌──────────────┐        ┌───────────────────┐        ┌────────────────┐
│              │        │                   │        │                │
│    Human     │◄──────►│  Math Assistant   │◄──────►│  Calculator    │
│    Client    │  A2A   │  Agent            │  A2A   │  Agent (MCP)   │
│              │        │                   │        │                │
└──────────────┘        └───────────────────┘        └────────────────┘
                           │            ▲
                           │            │
                           ▼            │
                        Parses natural language
                        Formats responses
```

## Key Concepts Demonstrated

- **A2A Protocol**: Standardized communication between agents, enabling modularity and interoperability
- **MCP Integration**: Using the Model Context Protocol to expose specialized capabilities as well-defined tools
- **Agent Hierarchy**: System of specialized agents providing services to higher-level agents
- **Natural Language Processing**: Extracting structured information from unstructured text queries
- **Error Handling**: Robust error handling at all levels of the system
- **Asynchronous Processing**: Using async/await for efficient handling of operations

## Extending the Example

This example can be extended in several ways:
- Add more mathematical operations (trigonometric functions, logarithms, etc.)
- Implement persistent storage for calculation history
- Add formula parsing capabilities
- Create a web-based user interface
- Implement user authentication and personalized settings

## Troubleshooting

If you encounter any issues:

1. Ensure all dependencies are correctly installed
2. Check that the ports are not in use by other applications
3. Look at the log output for detailed error messages
4. Verify that all agents are running before attempting to connect

## License

This example is provided under the MIT License.