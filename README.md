# Python A2A

<div align="center">

[![PyPI version](https://img.shields.io/pypi/v/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://img.shields.io/pypi/dm/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![PyPI Downloads](https://static.pepy.tech/badge/python-a2a)](https://pepy.tech/project/python-a2a)
[![Documentation Status](https://readthedocs.org/projects/python-a2a/badge/?version=latest)](https://python-a2a.readthedocs.io/en/latest/?badge=latest)
[![GitHub stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

**The Definitive Python Implementation of Google's Agent-to-Agent (A2A) Protocol**

</div>

## 🌟 Overview

Python A2A is a comprehensive, production-ready library for implementing Google's [Agent-to-Agent (A2A) protocol](https://google.github.io/A2A/). It provides everything you need to build interoperable AI agent ecosystems that can collaborate seamlessly to solve complex problems.

The A2A protocol establishes a standard communication format that enables AI agents to interact regardless of their underlying implementation. Python A2A makes this protocol accessible with an intuitive API that developers of all skill levels can use to build sophisticated multi-agent systems.

## ✨ Why Choose Python A2A?

- **Complete Implementation**: Fully implements the official A2A specification with zero compromises
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

### 4. Build an Agent Chain for Complex Tasks

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole

# Connect to specialized agents
weather_agent = A2AClient("http://localhost:5001/a2a")
planning_agent = A2AClient("http://localhost:5002/a2a")

def plan_trip(location):
    """Chain multiple agents to plan a trip."""
    # Step 1: Get weather information
    weather_message = Message(
        content=TextContent(text=f"What's the weather forecast for {location}?"),
        role=MessageRole.USER
    )
    weather_response = weather_agent.send_message(weather_message)
    
    # Step 2: Use weather data to create a trip plan
    planning_message = Message(
        content=TextContent(
            text=f"I'm planning a trip to {location}. Weather forecast: {weather_response.content.text}"
                 f"Please suggest activities and packing recommendations."
        ),
        role=MessageRole.USER
    )
    planning_response = planning_agent.send_message(planning_message)
    
    return planning_response.content.text

# Use the chained agents
trip_plan = plan_trip("Tokyo")
print(trip_plan)
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

### Command-Line Interface

Python A2A includes a CLI for interacting with A2A agents:

```bash
# Send a message to an agent
a2a send http://localhost:5000/a2a "What's the weather like in Tokyo?"

# Start a simple A2A server
a2a serve --host 0.0.0.0 --port 5000

# Start an OpenAI-powered agent
a2a openai --api-key YOUR_API_KEY --model gpt-4

# Start an Anthropic-powered agent
a2a anthropic --api-key YOUR_API_KEY --model claude-3-opus-20240229
```

## 📖 Architecture & Design Principles

Python A2A is built on three core design principles:

1. **Protocol First**: Adheres strictly to the A2A protocol specification for maximum interoperability

2. **Modularity**: All components are designed to be composable and replaceable

3. **Progressive Enhancement**: Start simple and add complexity only as needed

The architecture consists of four main components:

- **Models**: Data structures representing A2A messages and conversations
- **Client**: Components for sending messages to A2A agents
- **Server**: Components for building A2A-compatible agents
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
- **Tool-Using Agents**: Connect LLMs to database agents, calculation agents, and more

### Education & Training

- **AI Education**: Create educational systems that demonstrate agent collaboration
- **Simulation Environments**: Build simulated environments where multiple agents interact

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

## 🛣️ Roadmap

- **Streaming Support**: Streaming responses for real-time communication
- **WebSocket Support**: WebSocket transport for persistent connections
- **More LLM Integrations**: Support for additional LLM providers
- **Agent Registry**: A registry for discovering and registering agents
- **Agent Composition Tools**: Higher-level tools for composing agents

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