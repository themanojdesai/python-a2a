# LangChain Integration for Python A2A

This module provides seamless interoperability between LangChain and the A2A/MCP protocols, allowing you to use components from both ecosystems together.

## Overview

The LangChain integration enables bidirectional conversion between:
- LangChain agents/components and A2A servers
- LangChain tools and MCP endpoints
- A2A agents and LangChain agents
- MCP tools and LangChain tools

## Architecture

```
┌─────────────────────────┐          ┌─────────────────────────┐
│                         │          │                         │
│   LangChain Ecosystem   │◄────────►│   A2A/MCP Ecosystem     │
│                         │          │                         │
└───────────┬─────────────┘          └───────────┬─────────────┘
            │                                    │
            ▼                                    ▼
┌───────────────────────┐          ┌───────────────────────────┐
│                       │          │                           │
│  LangChain Components │          │    A2A/MCP Components     │
│                       │          │                           │
│ • Agents              │          │ • A2A Servers             │
│ • Chains              │          │ • A2A Clients             │
│ • Tools               │          │ • MCP Servers             │
│ • LLMs                │          │ • MCP Tools               │
│                       │          │                           │
└───────────┬───────────┘          └───────────┬───────────────┘
            │                                   │
            └────────────┬────────────┬─────────┘
                         │            │
                         ▼            ▼
          ┌─────────────────────────────────────────┐
          │                                         │
          │        LangChain Integration            │
          │                                         │
          │  ┌─────────────────────────────────┐   │
          │  │           Conversion            │   │
          │  │  ┌───────────────────────────┐  │   │
          │  │  │  to_a2a_server            │  │   │
          │  │  │  to_langchain_agent       │  │   │
          │  │  │  to_mcp_server            │  │   │
          │  │  │  to_langchain_tool        │  │   │
          │  │  └───────────────────────────┘  │   │
          │  └─────────────────────────────────┘   │
          │                                         │
          └─────────────────────────────────────────┘
```

## Protocol Compliance

### A2A Protocol Compliance

The integration respects the A2A protocol by:

1. **Maintaining HTTP Communication**: All A2A communication occurs via HTTP, not via direct method calls.
2. **Preserving Agent Boundaries**: A2A agents remain independent servers with their own endpoints.
3. **Respecting Message Format**: All messages follow the standard A2A message format.
4. **Handling Conversation State**: Proper conversation history and state management.
5. **Supporting Async Communication**: Full support for synchronous and asynchronous interactions.

### MCP Protocol Compliance

The integration respects the MCP protocol by:

1. **Preserving Tool Structure**: Tools follow the MCP schema definition and parameter format.
2. **Maintaining HTTP API**: All tool calls go through the MCP's HTTP API.
3. **Proper Tool Discovery**: Tools can be discovered and described through the MCP protocol.
4. **Type Preservation**: Parameter types and validation are preserved between ecosystems.
5. **Error Handling**: MCP-specific error responses are correctly processed and propagated.

## Installation

```bash
# Install with LangChain support
pip install "python-a2a[langchain]"

# Or install dependencies manually
pip install python-a2a langchain langchain-core
```

## Usage Examples

### Converting LangChain Agent to A2A Server

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain.llms import OpenAI
from python_a2a import run_server
from python_a2a.langchain import to_a2a_server

# Create a LangChain agent
llm = OpenAI(temperature=0)
agent = create_react_agent(llm, tools, prompt)
agent_executor = AgentExecutor(agent=agent, tools=tools)

# Convert to A2A server
a2a_server = to_a2a_server(agent_executor)

# Run the server
run_server(a2a_server, port=8000)
```

### Converting A2A Agent to LangChain Agent

```python
from python_a2a.langchain import to_langchain_agent

# Convert A2A agent to LangChain
langchain_agent = to_langchain_agent("http://localhost:8000")

# Use the agent in LangChain
result = langchain_agent.run("What's the capital of France?")
```

### Converting LangChain Tools to MCP Server

```python
from langchain.tools import Tool 
from python_a2a.langchain import to_mcp_server

# Create LangChain tools
calculator = Tool(
    name="calculator",
    description="Performs calculations",
    func=lambda x: eval(x)
)

# Convert to MCP server
server = to_mcp_server([calculator])

# Run the server
server.run(port=8080)
```

### Converting MCP Tools to LangChain

```python
from python_a2a.langchain import to_langchain_tool

# Convert all tools from an MCP server
tools = to_langchain_tool("http://localhost:8080")

# Convert a specific tool
calculator_tool = to_langchain_tool("http://localhost:8080", "calculator")

# Use in LangChain
from langchain.agents import initialize_agent
agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
```

### Using the Flow API with Both Ecosystems

```python
from python_a2a import Flow, AgentNetwork
from python_a2a.langchain import to_a2a_server

# Create LangChain components
summarizer = create_summarization_chain(llm)
a2a_summarizer = to_a2a_server(summarizer)

# Run the A2A server
import threading
server_thread = threading.Thread(
    target=lambda: run_server(a2a_summarizer, port=8001),
    daemon=True
)
server_thread.start()

# Create agent network with mixed components
network = AgentNetwork()
network.add("research", "http://localhost:8000")  # A2A research agent
network.add("summarize", "http://localhost:8001") # LangChain-powered A2A agent

# Create workflow using the flow API
flow = Flow(network)
flow.ask("research", "Research quantum computing")
flow.ask("summarize", "Summarize this: {latest_result}")

# Run the workflow
result = flow.run_sync()
```

## Error Handling

The integration provides detailed error handling with specific exception types:

```python
try:
    tool = to_langchain_tool("http://localhost:8080", "non_existent_tool")
except MCPToolConversionError as e:
    print(f"MCP tool error: {e}")
```

Available exceptions:
- `LangChainIntegrationError`: Base exception
- `LangChainNotInstalledError`: When LangChain is not installed
- `LangChainToolConversionError`: When a LangChain tool cannot be converted
- `MCPToolConversionError`: When an MCP tool cannot be converted
- `LangChainAgentConversionError`: When a LangChain agent cannot be converted
- `A2AAgentConversionError`: When an A2A agent cannot be converted

## Benefits

1. **Ecosystem Expansion**: Access tools and capabilities from both ecosystems.
2. **Protocol Compliance**: All interactions respect protocol boundaries and standards.
3. **Simple API**: Clean, focused API that's easy to use with minimal code.
4. **Robust Error Handling**: Detailed error reporting with specific exception types.
5. **Bidirectional Conversion**: Full support for converting in both directions.

## Best Practices

1. **Server Lifecycle Management**: When converting to servers, manage server lifecycle properly.
2. **Error Handling**: Use the specific exception types for better error handling.
3. **Parameter Types**: Pay attention to parameter types when converting tools.
4. **Conversation State**: Be aware of conversation state when using agents.
5. **Tool Selection**: Choose the right tools for each task based on capabilities.