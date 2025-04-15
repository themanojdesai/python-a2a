# Python A2A

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![PyPI Downloads](https://static.pepy.tech/badge/python-a2a)](https://pepy.tech/project/python-a2a)
[![Documentation Status](https://readthedocs.org/projects/python-a2a/badge/?version=latest)](https://python-a2a.readthedocs.io/en/latest/?badge=latest)
[![GitHub stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

**The Definitive Python Implementation of Google's Agent-to-Agent (A2A) Protocol with Model Context Protocol (MCP) Integration**

</div>

## 🌟 Overview

Python A2A is a comprehensive, production-ready library for implementing Google's [Agent-to-Agent (A2A) protocol](https://google.github.io/A2A/) with full support for the [Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/). It provides everything you need to build interoperable AI agent ecosystems that can collaborate seamlessly to solve complex problems.

The A2A protocol establishes a standard communication format that enables AI agents to interact regardless of their underlying implementation, while MCP extends this capability by providing a standardized way for agents to access external tools and data sources. Python A2A makes these protocols accessible with an intuitive API that developers of all skill levels can use to build sophisticated multi-agent systems.

## ✨ Why Choose Python A2A?

- **Complete Implementation**: Fully implements the official A2A specification with zero compromises
- **MCP Integration**: First-class support for Model Context Protocol for powerful tool-using agents
- **Enterprise Ready**: Built for production environments with robust error handling and validation
- **Framework Agnostic**: Works with any Python framework (Flask, FastAPI, Django, etc.)
- **LLM Provider Flexibility**: Native integrations with OpenAI, Anthropic, and HuggingFace
- **Minimal Dependencies**: Core functionality requires only the `requests` library
- **Excellent Developer Experience**: Comprehensive documentation, type hints, and examples

## 📦 Installation

Install the base package with minimal dependencies:

```bash
pip install python-a2a
```

Or install with optional components based on your needs:

```bash
# For Flask-based server support
pip install "python-a2a[server]"

# For OpenAI integration
pip install "python-a2a[openai]"

# For Anthropic Claude integration
pip install "python-a2a[anthropic]"

# For MCP support (Model Context Protocol)
pip install "python-a2a[mcp]"

# For all optional dependencies
pip install "python-a2a[all]"
```

## 🚀 Quick Start Examples

### 1. Create a Simple A2A Agent Server

```python
from python_a2a import A2AServer, Message, TextContent, MessageRole, run_server

class EchoAgent(A2AServer):
    """A simple agent that echoes back messages with a prefix."""
    
    def handle_message(self, message):
        if message.content.type == "text":
            return Message(
                content=TextContent(text=f"Echo: {message.content.text}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

# Run the server
if __name__ == "__main__":
    agent = EchoAgent()
    run_server(agent, host="0.0.0.0", port=5000)
```

### 2. Send Messages to an A2A Agent

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole
from python_a2a.utils import pretty_print_message

# Create a client connected to an A2A-compatible agent
client = A2AClient("http://localhost:5000/a2a")

# Create a simple message
message = Message(
    content=TextContent(text="Hello, A2A!"),
    role=MessageRole.USER
)

# Send the message and get a response
response = client.send_message(message)

# Display the response
pretty_print_message(response)
```

### 3. Create an LLM-Powered Agent

```python
import os
from python_a2a import OpenAIA2AServer, run_server

# Create an agent powered by OpenAI
agent = OpenAIA2AServer(
    api_key=os.environ["OPENAI_API_KEY"],
    model="gpt-4",
    system_prompt="You are a helpful AI assistant specialized in explaining complex topics simply."
)

# Run the server
if __name__ == "__main__":
    run_server(agent, host="0.0.0.0", port=5000)
```

### 4. Create an MCP Server with Tools

```python
from python_a2a.mcp import FastMCP, text_response

# Create a FastMCP server
calculator_mcp = FastMCP(
    name="Calculator MCP",
    version="1.0.0",
    description="Provides mathematical calculation functions"
)

# Define tools using decorator syntax
@calculator_mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@calculator_mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b

@calculator_mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

# Run the MCP server
if __name__ == "__main__":
    calculator_mcp.run(host="0.0.0.0", port=5001)
```

### 5. Create an MCP-Enabled A2A Agent

```python
from python_a2a import A2AServer, Message, TextContent, MessageRole, run_server
from python_a2a.mcp import FastMCPAgent, FastMCP

# First, create or connect to MCP servers
calculator_mcp = FastMCP(
    name="Calculator MCP",
    version="1.0.0",
    description="Provides calculation functions"
)

@calculator_mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

# Create an A2A agent with MCP capabilities
class CalculatorAgent(A2AServer, FastMCPAgent):
    def __init__(self):
        # Initialize both parent classes
        A2AServer.__init__(self)
        FastMCPAgent.__init__(
            self,
            mcp_servers={"calc": calculator_mcp}
        )
    
    async def handle_message_async(self, message):
        try:
            if message.content.type == "text":
                # Extract calculation from text
                text = message.content.text.lower()
                if "add" in text or "plus" in text or "+" in text:
                    # Extract numbers
                    import re
                    numbers = [float(n) for n in re.findall(r"[-+]?\d*\.?\d+", text)]
                    if len(numbers) >= 2:
                        # Call MCP tool
                        result = await self.call_mcp_tool("calc", "add", a=numbers[0], b=numbers[1])
                        return Message(
                            content=TextContent(text=f"The sum is {result}"),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                # Default response
                return Message(
                    content=TextContent(text="I can help with calculations."),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        except Exception as e:
            # Error handling
            return Message(
                content=TextContent(text=f"Error: {str(e)}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

# Run the agent
if __name__ == "__main__":
    agent = CalculatorAgent()
    run_server(agent, host="0.0.0.0", port=5000)
```

### 6. Build a Multi-Agent System with MCP

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole

# Connect to specialized agents
ticker_agent = A2AClient("http://localhost:5001/a2a")  # DuckDuckGo agent for ticker symbols
price_agent = A2AClient("http://localhost:5002/a2a")   # YFinance agent for stock prices

def get_stock_price(company_name):
    """Chain multiple agents to get stock price information."""
    # Step 1: Get ticker symbol
    ticker_message = Message(
        content=TextContent(text=f"What's the ticker symbol for {company_name}?"),
        role=MessageRole.USER
    )
    ticker_response = ticker_agent.send_message(ticker_message)
    
    # Extract ticker from response
    import re
    ticker_match = re.search(r'ticker\s+(?:symbol\s+)?(?:for\s+[\w\s]+\s+)?is\s+([A-Z]{1,5})', 
                            ticker_response.content.text, re.I)
    if ticker_match:
        ticker = ticker_match.group(1)
        
        # Step 2: Get stock price using ticker
        price_message = Message(
            content=TextContent(text=f"What's the current price of {ticker}?"),
            role=MessageRole.USER
        )
        price_response = price_agent.send_message(price_message)
        return price_response.content.text
    else:
        return f"Could not find ticker symbol for {company_name}"

# Get stock price for a company
price_info = get_stock_price("Apple")
print(price_info)
```

## 🧩 Core Features

### Messages and Conversations

Python A2A provides a rich set of models for A2A messages and conversations:

```python
from python_a2a import (
    Message, TextContent, FunctionCallContent, FunctionResponseContent, 
    MessageRole, Conversation
)

# Create a conversation
conversation = Conversation()

# Add messages to the conversation
conversation.create_text_message(
    text="What's the weather like in New York?", 
    role=MessageRole.USER
)

# Add a function call message
conversation.create_function_call(
    name="get_weather",
    parameters=[
        {"name": "location", "value": "New York"},
        {"name": "unit", "value": "celsius"}
    ],
    role=MessageRole.AGENT
)

# Add a function response
conversation.create_function_response(
    name="get_weather",
    response={"temperature": 22, "conditions": "Partly Cloudy"},
    role=MessageRole.AGENT
)
```

### Function Calling

The A2A protocol supports function calling between agents, making it easy to expose capabilities:

```python
from python_a2a import (
    Message, FunctionCallContent, FunctionParameter, FunctionResponseContent,
    MessageRole
)

# Create a function call message
function_call = Message(
    content=FunctionCallContent(
        name="calculate",
        parameters=[
            FunctionParameter(name="operation", value="add"),
            FunctionParameter(name="a", value=5),
            FunctionParameter(name="b", value=3)
        ]
    ),
    role=MessageRole.USER
)

# Create a function response message
function_response = Message(
    content=FunctionResponseContent(
        name="calculate",
        response={"result": 8}
    ),
    role=MessageRole.AGENT,
    parent_message_id=function_call.message_id
)
```

### MCP for Tool Integration

MCP provides a standardized way to expose tools and capabilities:

```python
from python_a2a.mcp import FastMCP, text_response, error_response

# Create an MCP server
mcp_server = FastMCP(
    name="Finance Tools",
    description="Financial analysis tools"
)

# Define tools with type hints and documentation
@mcp_server.tool()
def calculate_roi(investment: float, returns: float) -> float:
    """
    Calculate return on investment.
    
    Args:
        investment: Initial investment amount
        returns: Returns from the investment
        
    Returns:
        ROI as a percentage
    """
    if investment <= 0:
        return error_response("Investment must be greater than zero")
    roi = (returns - investment) / investment * 100
    return text_response(f"ROI: {roi:.2f}%")

# Run the server
if __name__ == "__main__":
    mcp_server.run(port=5000)
```

### Command-Line Interface

Python A2A includes a CLI for interacting with A2A and MCP agents:

```bash
# Send a message to an agent
a2a send http://localhost:5000/a2a "What's the weather like in Tokyo?"

# Start a simple A2A server
a2a serve --host 0.0.0.0 --port 5000

# Start an OpenAI-powered agent
a2a openai --api-key YOUR_API_KEY --model gpt-4

# Start an MCP server
a2a mcp-serve --port 5001 --name "Calculator" --script calculator_tools.py

# Start an MCP-enabled A2A agent
a2a mcp-agent --port 5000 --servers calc=http://localhost:5001/

# Call an MCP tool directly
a2a mcp-call http://localhost:5001/ add --params a=5 b=3
```

## 📖 Architecture & Design Principles

Python A2A is built on three core design principles:

1. **Protocol First**: Adheres strictly to the A2A and MCP protocol specifications for maximum interoperability

2. **Modularity**: All components are designed to be composable and replaceable

3. **Progressive Enhancement**: Start simple and add complexity only as needed

The architecture consists of five main components:

- **Models**: Data structures representing A2A messages and conversations
- **Client**: Components for sending messages to A2A agents
- **Server**: Components for building A2A-compatible agents
- **MCP**: Tools for implementing Model Context Protocol servers and clients
- **Utils**: Helper functions for common tasks

## 🗺️ Use Cases

Python A2A can be used to build a wide range of AI systems:

### Research & Development

- **Experimentation Framework**: Easily swap out different LLM backends while keeping the same agent interface
- **Benchmark Suite**: Compare performance of different agent implementations on standardized tasks

### Enterprise Systems

- **AI Orchestration**: Coordinate multiple AI agents across different departments
- **Legacy System Integration**: Wrap legacy systems with A2A interfaces for AI accessibility

### Customer-Facing Applications

- **Multi-Stage Assistants**: Break complex user queries into subtasks handled by specialized agents
- **Tool-Using Agents**: Connect LLMs to database agents, calculation agents, and more using MCP

### Education & Training

- **AI Education**: Create educational systems that demonstrate agent collaboration
- **Simulation Environments**: Build simulated environments where multiple agents interact

## 🛠️ Real-World Examples

### Stock Information System

The library includes a complete stock information system example that demonstrates the power of combining A2A with MCP:

1. **DuckDuckGo Agent**: Uses MCP to search for stock ticker symbols
2. **YFinance Agent**: Uses MCP to fetch current stock prices
3. **Stock Assistant**: Orchestrates between the specialized agents

```bash
# Start each component in separate terminals
python examples/mcp/duckduckgo_agent.py --port 5001
python examples/mcp/yfinance_agent.py --port 5002
python examples/mcp/stock_assistant.py --port 5000 --openai-api-key YOUR_API_KEY
python examples/mcp/stock_client.py
```

### Calculator Example

A simpler example showing MCP tool integration:

```bash
# Start the calculator MCP agent
python examples/mcp/calculator_agent.py --port 5001
```

## 🔍 Detailed Documentation

For comprehensive documentation, tutorials, and API reference, visit:

- **[User Guide](https://python-a2a.readthedocs.io/en/latest/user_guide.html)**: Step-by-step tutorials and guides
- **[API Reference](https://python-a2a.readthedocs.io/en/latest/api.html)**: Detailed API documentation
- **[Examples](https://python-a2a.readthedocs.io/en/latest/examples.html)**: Real-world examples and use cases
- **[Jupyter Notebooks](https://github.com/themanojdesai/python-a2a/tree/main/notebooks)**: Interactive examples and tutorials

## 🤝 Community & Support

- **[GitHub Issues](https://github.com/themanojdesai/python-a2a/issues)**: Report bugs or request features
- **[GitHub Discussions](https://github.com/themanojdesai/python-a2a/discussions)**: Ask questions and share ideas
- **[Contributing Guide](https://python-a2a.readthedocs.io/en/latest/contributing.html)**: Learn how to contribute to the project
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**: Visit our documentation site

## ⭐ Star This Repository

If you find this library useful, please consider giving it a star on GitHub! It helps others discover the project and motivates further development.

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)


## 🙏 Acknowledgements

- The [Google A2A team](https://github.com/google/A2A) for creating the A2A protocol
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