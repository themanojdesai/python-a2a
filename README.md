# Python A2A

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Downloads](https://static.pepy.tech/badge/python-a2a)](https://pepy.tech/project/python-a2a)
[![Documentation Status](https://readthedocs.org/projects/python-a2a/badge/?version=latest)](https://python-a2a.readthedocs.io/en/latest/?badge=latest)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![UV Compatible](https://img.shields.io/badge/UV-Compatible-5C63FF.svg)](https://github.com/astral-sh/uv)
[![GitHub stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

**The Definitive Python Implementation of Google's Agent-to-Agent (A2A) Protocol with Model Context Protocol (MCP) Integration**

</div>

## 🌟 Overview

Python A2A is a comprehensive, production-ready library for implementing Google's [Agent-to-Agent (A2A) protocol](https://google.github.io/A2A/) with full support for the [Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/). It provides everything you need to build interoperable AI agent ecosystems that can collaborate seamlessly to solve complex problems.

The A2A protocol establishes a standard communication format that enables AI agents to interact regardless of their underlying implementation, while MCP extends this capability by providing a standardized way for agents to access external tools and data sources. Python A2A makes these protocols accessible with an intuitive API that developers of all skill levels can use to build sophisticated multi-agent systems.

## 📋 What's New in v0.5.X

- **LangChain Integration**: Seamless integration with LangChain's tools and agents
- **Expanded Tool Ecosystem**: Use tools from both LangChain and MCP in any agent
- **Enhanced Agent Interoperability**: Convert between A2A agents and LangChain agents 
- **Mixed Workflow Engine**: Build workflows combining both ecosystems
- **Simplified Agent Development**: Access thousands of pre-built tools instantly

## 📋 What's New in v0.4.X

- **Agent Network System**: Manage and discover multiple agents with the new `AgentNetwork` class
- **Real-time Streaming**: Implement streaming responses with `StreamingClient` for responsive UIs
- **Workflow Engine**: Define complex multi-agent workflows using the new fluent API with conditional branching and parallel execution
- **AI-Powered Router**: Automatically route queries to the most appropriate agent with the `AIAgentRouter`
- **Command Line Interface**: Control your agents from the terminal with the new CLI tool
- **Enhanced Asynchronous Support**: Better async/await support throughout the library
- **New Connection Options**: Improved error handling and retry logic for more robust agent communication

## ✨ Why Choose Python A2A?

- **Complete Implementation**: Fully implements the official A2A specification with zero compromises
- **MCP Integration**: First-class support for Model Context Protocol for powerful tool-using agents
- **Enterprise Ready**: Built for production environments with robust error handling and validation
- **Framework Agnostic**: Works with any Python framework (Flask, FastAPI, Django, etc.)
- **LLM Provider Flexibility**: Native integrations with OpenAI, Anthropic, AWS Bedrock, and more
- **Minimal Dependencies**: Core functionality requires only the `requests` library
- **Excellent Developer Experience**: Comprehensive documentation, type hints, and examples

## 📦 Installation

### Using pip (traditional)

Install the base package with all dependencies:

```bash
pip install python-a2a  # Includes LangChain, MCP, and other integrations
```

Or install with specific components based on your needs:

```bash
# For Flask-based server support
pip install "python-a2a[server]"

# For OpenAI integration
pip install "python-a2a[openai]"

# For Anthropic Claude integration
pip install "python-a2a[anthropic]"

# For AWS-Bedrock integration
pip install "python-a2a[bedrock]"

# For MCP support (Model Context Protocol)
pip install "python-a2a[mcp]"

# For all optional dependencies
pip install "python-a2a[all]"
```

### Using UV (recommended)

[UV](https://github.com/astral-sh/uv) is a modern Python package management tool that's faster and more reliable than pip. To install with UV:

```bash
# Install UV if you don't have it already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install the base package
uv install python-a2a
```

### Development Installation

For development, UV is recommended for its speed:

```bash
# Clone the repository
git clone https://github.com/themanojdesai/python-a2a.git
cd python-a2a

# Create a virtual environment and install development dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

> 💡 **Tip**: Click the code blocks to copy them to your clipboard.

## 🚀 Quick Start Examples

### 1. Create a Simple A2A Agent with Skills

```python
from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState

@agent(
    name="Weather Agent",
    description="Provides weather information",
    version="1.0.0"
)
class WeatherAgent(A2AServer):
    
    @skill(
        name="Get Weather",
        description="Get current weather for a location",
        tags=["weather", "forecast"]
    )
    def get_weather(self, location):
        """Get weather for a location."""
        # Mock implementation
        return f"It's sunny and 75°F in {location}"
    
    def handle_task(self, task):
        # Extract location from message
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        if "weather" in text.lower() and "in" in text.lower():
            location = text.split("in", 1)[1].strip().rstrip("?.")
            
            # Get weather and create response
            weather_text = self.get_weather(location)
            task.artifacts = [{
                "parts": [{"type": "text", "text": weather_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
        else:
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={"role": "agent", "content": {"type": "text", 
                         "text": "Please ask about weather in a specific location."}}
            )
        return task

# Run the server
if __name__ == "__main__":
    agent = WeatherAgent()
    run_server(agent, port=5000)
```

### 2. Build an Agent Network with Multiple Agents

```python
from python_a2a import AgentNetwork, A2AClient, AIAgentRouter

# Create an agent network
network = AgentNetwork(name="Travel Assistant Network")

# Add agents to the network
network.add("weather", "http://localhost:5001")
network.add("hotels", "http://localhost:5002")
network.add("attractions", "http://localhost:5003")

# Create a router to intelligently direct queries to the best agent
router = AIAgentRouter(
    llm_client=A2AClient("http://localhost:5000/openai"),  # LLM for making routing decisions
    agent_network=network
)

# Route a query to the appropriate agent
agent_name, confidence = router.route_query("What's the weather like in Paris?")
print(f"Routing to {agent_name} with {confidence:.2f} confidence")

# Get the selected agent and ask the question
agent = network.get_agent(agent_name)
response = agent.ask("What's the weather like in Paris?")
print(f"Response: {response}")

# List all available agents
print("\nAvailable Agents:")
for agent_info in network.list_agents():
    print(f"- {agent_info['name']}: {agent_info['description']}")
```

### 3. Stream Responses for Real-time Updates

```python
import asyncio
from python_a2a import StreamingClient, Message, TextContent, MessageRole
from python_a2a import Task, TaskStatus, TaskState

async def main():
    # Create a streaming client
    client = StreamingClient("http://localhost:5000")
    
    # Stream a simple message
    message = Message(
        content=TextContent(text="Write a short story about space exploration"),
        role=MessageRole.USER
    )
    
    print("Streaming response:")
    print("-" * 50)
    
    # Define a callback function to process chunks
    def print_chunk(chunk):
        print(chunk, end="", flush=True)
    
    # Stream the response with the callback
    async for chunk in client.stream_response(message, chunk_callback=print_chunk):
        pass  # Chunks are handled by the callback
    
    print("\n" + "-" * 50)
    
    # Alternatively, create and stream a task
    task = await client.create_task("Explain quantum computing in simple terms")
    
    print("\nStreaming task response:")
    print("-" * 50)
    
    # Stream the task execution
    async for chunk in client.stream_task(task, chunk_callback=lambda c: print(c.get("text", ""), end="", flush=True)):
        pass

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Define Complex Workflows with Multiple Agents

```python
from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio

async def main():
    # Create an agent network
    network = AgentNetwork()
    network.add("weather", "http://localhost:5001")
    network.add("recommendations", "http://localhost:5002")
    network.add("booking", "http://localhost:5003")
    
    # Create a router
    router = AIAgentRouter(
        llm_client=network.get_agent("weather"),  # Using one agent as LLM for routing
        agent_network=network
    )
    
    # Define a workflow with conditional logic
    flow = Flow(agent_network=network, router=router, name="Travel Planning Workflow")
    
    # Start by getting the weather
    flow.ask("weather", "What's the weather in {destination}?")
    
    # Conditionally branch based on weather
    flow.if_contains("sunny")
    
    # If sunny, recommend outdoor activities
    flow.ask("recommendations", "Recommend outdoor activities in {destination}")
    
    # End the condition and add an else branch
    flow.else_branch()
    
    # If not sunny, recommend indoor activities
    flow.ask("recommendations", "Recommend indoor activities in {destination}")
    
    # End the if-else block
    flow.end_if()
    
    # Add parallel processing steps
    (flow.parallel()
        .ask("booking", "Find hotels in {destination}")
        .branch()
        .ask("booking", "Find restaurants in {destination}")
        .end_parallel())
    
    # Execute the workflow with initial context
    result = await flow.run({
        "destination": "Paris",
        "travel_dates": "June 12-20"
    })
    
    print("Workflow result:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Use the Command Line Interface

```bash
# Start an OpenAI-powered agent
a2a openai --api-key YOUR_API_KEY --model gpt-4 --port 5000

# In another terminal, send a message to the agent
a2a send http://localhost:5000 "Explain quantum computing in simple terms"

# Stream a response with real-time updates
a2a stream http://localhost:5000 "Write a short story about aliens visiting Earth"

# Start an MCP server with custom tools
a2a mcp-serve --name "Calculator MCP" --script calculator_tools.py --port 5001

# Create an agent network
a2a network --add weather=http://localhost:5001 recommendations=http://localhost:5002 --save network.json

# Run a workflow from a script
a2a workflow --script travel_workflow.py --agents weather=http://localhost:5001 recommendations=http://localhost:5002
```

## 🔄 LangChain Integration (New in v0.5.X)

Python A2A includes built-in LangChain integration, making it easy to combine the best of both ecosystems:

### 1. Converting MCP Tools to LangChain

```python
from python_a2a.mcp import FastMCP, text_response
from python_a2a.langchain import to_langchain_tool

# Create MCP server with a tool
mcp_server = FastMCP(name="Basic Tools", description="Simple utility tools")

@mcp_server.tool(
    name="calculator",
    description="Calculate a mathematical expression"
)
def calculator(input):
    """Simple calculator that evaluates an expression."""
    try:
        result = eval(input)
        return text_response(f"Result: {result}")
    except Exception as e:
        return text_response(f"Error: {e}")

# Start the server
import threading, time
def run_server(server, port):
    server.run(host="0.0.0.0", port=port)
server_thread = threading.Thread(target=run_server, args=(mcp_server, 5000), daemon=True)
server_thread.start()
time.sleep(2)  # Allow server to start

# Convert MCP tool to LangChain
calculator_tool = to_langchain_tool("http://localhost:5000", "calculator")

# Use the tool in LangChain
result = calculator_tool.run("5 * 9 + 3")
print(f"Result: {result}")
```

### 2. Converting LangChain Tools to MCP Server

```python
from langchain.tools import Tool
from langchain_core.tools import BaseTool
from python_a2a.langchain import to_mcp_server

# Create LangChain tools
def calculator(expression: str) -> str:
    """Evaluate a mathematical expression"""
    try:
        result = eval(expression)
        return f"Result: {expression} = {result}"
    except Exception as e:
        return f"Error: {e}"

calculator_tool = Tool(
    name="calculator",
    description="Evaluate a mathematical expression",
    func=calculator
)

# Convert to MCP server
mcp_server = to_mcp_server(calculator_tool)

# Run the server
mcp_server.run(port=5000)
```

### 3. Converting LangChain Components to A2A Servers

```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from python_a2a import A2AClient, run_server
from python_a2a.langchain import to_a2a_server

# Create a LangChain LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Convert LLM to A2A server
llm_server = to_a2a_server(llm)

# Create a simple chain
template = "You are a helpful travel guide.\n\nQuestion: {query}\n\nAnswer:"
prompt = PromptTemplate.from_template(template)
travel_chain = prompt | llm | StrOutputParser()

# Convert chain to A2A server
travel_server = to_a2a_server(travel_chain)

# Run servers in background threads
import threading
llm_thread = threading.Thread(
    target=lambda: run_server(llm_server, port=5001),
    daemon=True
)
llm_thread.start()

travel_thread = threading.Thread(
    target=lambda: run_server(travel_server, port=5002),
    daemon=True
)
travel_thread.start()

# Test the servers
llm_client = A2AClient("http://localhost:5001")
travel_client = A2AClient("http://localhost:5002")

llm_result = llm_client.ask("What is the capital of France?")
travel_result = travel_client.ask('{"query": "What are some must-see attractions in Paris?"}')
```

### 4. Converting A2A Agents to LangChain Agents

```python
from python_a2a.langchain import to_langchain_agent

# Convert A2A agent to LangChain agent
langchain_agent = to_langchain_agent("http://localhost:5000")

# Use the agent in LangChain
result = langchain_agent.invoke("What are some famous landmarks in Paris?")
print(result.get('output', ''))

# Use in a LangChain pipeline
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(temperature=0)
prompt = ChatPromptTemplate.from_template(
    "Generate a specific, detailed travel question about {destination}."
)

# Create a pipeline with the converted agent
chain = (
    prompt |
    llm |
    StrOutputParser() |
    langchain_agent |
    (lambda x: f"Travel Info: {x.get('output', '')}")
)

result = chain.invoke({"destination": "Japan"})
print(result)
```

LangChain is automatically installed as a dependency with python-a2a, so everything works right out of the box:

```bash
pip install python-a2a
# That's it! LangChain is included automatically
```

## 🧩 Core Features

### Agent Networks

Python A2A now includes a powerful system for managing multiple agents:

```python
from python_a2a import AgentNetwork, A2AClient

# Create a network of agents
network = AgentNetwork(name="Medical Assistant Network")

# Add agents in different ways
network.add("diagnosis", "http://localhost:5001")  # From URL
network.add("medications", A2AClient("http://localhost:5002"))  # From client instance

# Discover agents from a list of URLs
discovered_count = network.discover_agents([
    "http://localhost:5003",
    "http://localhost:5004",
    "http://localhost:5005"
])
print(f"Discovered {discovered_count} new agents")

# List all agents in the network
for agent_info in network.list_agents():
    print(f"Agent: {agent_info['name']}")
    print(f"URL: {agent_info['url']}")
    if 'description' in agent_info:
        print(f"Description: {agent_info['description']}")
    print()

# Get a specific agent
agent = network.get_agent("diagnosis")
response = agent.ask("What are the symptoms of the flu?")
```

### Real-time Streaming

Get real-time responses from agents with streaming support:

```python
import asyncio
from python_a2a import StreamingClient

async def main():
    client = StreamingClient("http://localhost:5000")
    
    # Define a callback to process each chunk as it arrives
    def handle_chunk(chunk):
        if isinstance(chunk, str):
            print(chunk, end="", flush=True)
        elif isinstance(chunk, dict) and "text" in chunk:
            print(chunk["text"], end="", flush=True)
    
    # Stream a response in real-time
    print("Generating a story...")
    async for chunk in client.stream_response(
        "Write me a short story about a robot that learns to paint",
        chunk_callback=handle_chunk
    ):
        pass  # Processing is done in the callback
    
    print("\nDone!")

if __name__ == "__main__":
    asyncio.run(main())
```

### Workflow Engine

The new workflow engine allows you to define complex agent interactions:

```python
from python_a2a import AgentNetwork, Flow
import asyncio

async def main():
    # Set up agent network
    network = AgentNetwork()
    network.add("research", "http://localhost:5001")
    network.add("summarizer", "http://localhost:5002")
    network.add("factchecker", "http://localhost:5003")
    
    # Define a workflow for research report generation
    flow = Flow(agent_network=network, name="Research Report Workflow")
    
    # First, gather initial research
    flow.ask("research", "Research the latest developments in {topic}")
    
    # Then process the results in parallel
    parallel_results = (flow.parallel()
        # Branch 1: Create a summary
        .ask("summarizer", "Summarize this research: {latest_result}")
        # Branch 2: Verify key facts
        .branch()
        .ask("factchecker", "Verify these key facts: {latest_result}")
        # End parallel processing and collect results
        .end_parallel(max_concurrency=2))
    
    # Extract insights based on verification results
    flow.execute_function(
        lambda results, context: f"Summary: {results['1']}\nVerified Facts: {results['2']}",
        parallel_results
    )
    
    # Execute the workflow
    result = await flow.run({
        "topic": "quantum computing advancements in the last year"
    })
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### AI-Powered Router

Intelligent routing to select the best agent for each query:

```python
from python_a2a import AgentNetwork, AIAgentRouter, A2AClient
import asyncio

async def main():
    # Create a network with specialized agents
    network = AgentNetwork()
    network.add("math", "http://localhost:5001")
    network.add("history", "http://localhost:5002")
    network.add("science", "http://localhost:5003")
    network.add("literature", "http://localhost:5004")
    
    # Create a router using an LLM for decision making
    router = AIAgentRouter(
        llm_client=A2AClient("http://localhost:5000/openai"),
        agent_network=network
    )
    
    # Sample queries to route
    queries = [
        "What is the formula for the area of a circle?",
        "Who wrote The Great Gatsby?",
        "When did World War II end?",
        "How does photosynthesis work?",
        "What are Newton's laws of motion?"
    ]
    
    # Route each query to the best agent
    for query in queries:
        agent_name, confidence = router.route_query(query)
        agent = network.get_agent(agent_name)
        
        print(f"Query: {query}")
        print(f"Routed to: {agent_name} (confidence: {confidence:.2f})")
        
        # Get response from the selected agent
        response = agent.ask(query)
        print(f"Response: {response[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### Command Line Interface

The new CLI provides easy access to agent functionality:

```bash
# Send a message to an agent
a2a send http://localhost:5000 "What is artificial intelligence?"

# Stream a response in real-time
a2a stream http://localhost:5000 "Generate a step-by-step tutorial for making pasta"

# Start an OpenAI-powered A2A server
a2a openai --model gpt-4 --system-prompt "You are a helpful coding assistant"

# Start an Anthropic-powered A2A server
a2a anthropic --model claude-3-opus-20240229 --system-prompt "You are a friendly AI teacher"

# Start an MCP server with tools
a2a mcp-serve --name "Data Analysis MCP" --port 5001 --script analysis_tools.py

# Start an MCP-enabled A2A agent
a2a mcp-agent --servers data=http://localhost:5001 calc=http://localhost:5002

# Call an MCP tool directly
a2a mcp-call http://localhost:5001 analyze_csv --params file=data.csv columns=price,date

# Manage agent networks
a2a network --add weather=http://localhost:5001 travel=http://localhost:5002 --save network.json

# Run a workflow from a script
a2a workflow --script research_workflow.py --context initial_data.json
```

## 📖 Architecture & Design Principles

Python A2A is built on three core design principles:

1. **Protocol First**: Adheres strictly to the A2A and MCP protocol specifications for maximum interoperability

2. **Modularity**: All components are designed to be composable and replaceable

3. **Progressive Enhancement**: Start simple and add complexity only as needed

The architecture consists of seven main components:

- **Models**: Data structures representing A2A messages, tasks, and agent cards
- **Client**: Components for sending messages to A2A agents and managing agent networks
- **Server**: Components for building A2A-compatible agents
- **MCP**: Tools for implementing Model Context Protocol servers and clients
- **LangChain**: Bridge components for LangChain integration
- **Workflow**: Engine for orchestrating complex agent interactions
- **Utils**: Helper functions for common tasks
- **CLI**: Command-line interface for interacting with agents

## 🗺️ Use Cases

Python A2A can be used to build a wide range of AI systems:

### Research & Development

- **Experimentation Framework**: Easily swap out different LLM backends while keeping the same agent interface
- **Benchmark Suite**: Compare performance of different agent implementations on standardized tasks
- **Streaming Research Assistants**: Create responsive research tools with real-time output using streaming

### Enterprise Systems

- **AI Orchestration**: Coordinate multiple AI agents across different departments using agent networks
- **Legacy System Integration**: Wrap legacy systems with A2A interfaces for AI accessibility
- **Complex Workflows**: Create sophisticated business processes with multi-agent workflows and conditional branching

### Customer-Facing Applications

- **Multi-Stage Assistants**: Break complex user queries into subtasks handled by specialized agents
- **Tool-Using Agents**: Connect LLMs to database agents, calculation agents, and more using MCP
- **Real-time Chat Interfaces**: Build responsive chat applications with streaming response support

### Education & Training

- **AI Education**: Create educational systems that demonstrate agent collaboration
- **Simulation Environments**: Build simulated environments where multiple agents interact
- **Educational Workflows**: Design step-by-step learning processes with feedback loops

## 🛠️ Real-World Examples

Check out the [`examples/`](https://github.com/themanojdesai/python-a2a/tree/main/examples) directory for real-world examples, including:

- Multi-agent customer support systems
- LLM-powered research assistants with tool access
- LangChain integration examples
- MCP server implementations for various tools
- Workflow orchestration examples
- Agent network management

## 🔄 Related Projects

Here are some related projects in the AI agent and interoperability space:

- [**Google A2A**](https://github.com/google/A2A) - The official Google A2A protocol specification
- [**LangChain**](https://github.com/langchain-ai/langchain) - Framework for building applications with LLMs
- [**AutoGen**](https://github.com/microsoft/autogen) - Microsoft's framework for multi-agent conversations
- [**CrewAI**](https://github.com/joaomdmoura/crewAI) - Framework for orchestrating role-playing agents
- [**MCP**](https://github.com/contextco/mcp) - The Model Context Protocol for tool-using agents

## 👥 Contributors

Thanks to all our contributors!

<a href="https://github.com/themanojdesai/python-a2a/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=themanojdesai/python-a2a" />
</a>

Want to contribute? Check out our [contributing guide](https://python-a2a.readthedocs.io/en/latest/contributing.html).

## 🤝 Community & Support

- **[GitHub Issues](https://github.com/themanojdesai/python-a2a/issues)**: Report bugs or request features
- **[GitHub Discussions](https://github.com/themanojdesai/python-a2a/discussions)**: Ask questions and share ideas
- **[Contributing Guide](https://python-a2a.readthedocs.io/en/latest/contributing.html)**: Learn how to contribute to the project
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**: Visit our documentation site

## 📝 Citing this Project

If you use Python A2A in your research or academic work, please cite it as:

```
@software{desai2025pythona2a,
  author = {Desai, Manoj},
  title = {Python A2A: A Comprehensive Implementation of the Agent-to-Agent Protocol},
  url = {https://github.com/themanojdesai/python-a2a},
  version = {0.5.0},
  year = {2025},
}
```

## ⭐ Star This Repository

If you find this library useful, please consider giving it a star on GitHub! It helps others discover the project and motivates further development.

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

### Star History

[![Star History Chart](https://api.star-history.com/svg?repos=themanojdesai/python-a2a&type=Date)](https://star-history.com/#themanojdesai/python-a2a&Date)

## 🙏 Acknowledgements

- The [Google A2A team](https://github.com/google/A2A) for creating the A2A protocol
- The [Contextual AI team](https://contextual.ai/) for the Model Context Protocol
- The [LangChain team](https://github.com/langchain-ai) for their powerful LLM framework
- All our [contributors](https://github.com/themanojdesai/python-a2a/graphs/contributors) for their valuable input

## 👨‍💻 Author

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

Made with ❤️ by [Manoj Desai](https://github.com/themanojdesai)