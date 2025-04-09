# Python A2A

<div align="center">

![Python A2A Logo](https://via.placeholder.com/800x200?text=Python+A2A)

[![PyPI version](https://img.shields.io/pypi/v/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![Python Versions](https://img.shields.io/pypi/pyversions/python-a2a.svg)](https://pypi.org/project/python-a2a/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Downloads](https://static.pepy.tech/badge/python-a2a/month)](https://pepy.tech/project/python-a2a)

**A Comprehensive Python Library for Google's Agent-to-Agent (A2A) Protocol**

</div>

## 🌟 Overview

Python A2A is a powerful, easy-to-use library for implementing Google's [Agent-to-Agent (A2A) protocol](https://google.github.io/A2A/). It enables seamless communication between AI agents, creating interoperable agent ecosystems that can collaborate to solve complex problems.

Whether you're building specialized agents with distinct capabilities, orchestrating complex workflows, or creating modular AI systems, Python A2A makes it simple to implement the A2A protocol in your applications.

## 🚀 Key Features

- **Complete Protocol Implementation**: Full implementation of Google's A2A protocol specification
- **Message & Conversation Models**: Robust data models for A2A messages and conversations
- **HTTP Client & Server**: Easy-to-use HTTP client and server components
- **LLM Integration**: Built-in support for OpenAI, Anthropic (Claude), and HuggingFace models
- **Function Calling**: First-class support for function calling between agents
- **CLI Tools**: Command-line interface for interacting with A2A agents
- **Comprehensive Validation**: Robust validation and error handling
- **Type Hints**: Complete type annotations for better IDE support
- **Thorough Documentation**: Detailed documentation and examples

## 📦 Installation

```bash
pip install python-a2a
```

## 🔍 Quick Start

### Creating a Simple A2A Agent

```python
from python_a2a import A2AServer, Message, TextContent, MessageRole, run_server

class EchoAgent(A2AServer):
    def handle_message(self, message):
        if message.content.type == "text":
            return Message(
                content=TextContent(text=f"Echo: {message.content.text}"),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

# Run the server
agent = EchoAgent()
run_server(agent, host="0.0.0.0", port=5000)
```

### Sending Messages to an Agent

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole

# Create a client
client = A2AClient("http://localhost:5000/a2a")

# Create a message
message = Message(
    content=TextContent(text="Hello, agent!"),
    role=MessageRole.USER
)

# Send the message and get a response
response = client.send_message(message)
print(f"Agent response: {response.content.text}")
```

### Creating an LLM-Powered Agent

```python
from python_a2a import OpenAIA2AServer, run_server
import os

# Create an OpenAI-powered agent
agent = OpenAIA2AServer(
    api_key=os.environ.get("OPENAI_API_KEY"),
    model="gpt-4",
    system_prompt="You are a helpful assistant."
)

# Run the server
run_server(agent, host="0.0.0.0", port=5000)
```

### Chaining Multiple Agents

```python
from python_a2a import A2AClient, Message, TextContent, MessageRole

# Create clients for different specialized agents
weather_client = A2AClient("http://localhost:5001/a2a")
planning_client = A2AClient("http://localhost:5002/a2a")

# Ask the weather agent about the forecast
weather_message = Message(
    content=TextContent(text="What's the weather like in Tokyo?"),
    role=MessageRole.USER
)
weather_response = weather_client.send_message(weather_message)

# Use the weather information to ask the planning agent for recommendations
planning_message = Message(
    content=TextContent(
        text=f"I'm planning a trip to Tokyo. Here's the weather forecast: {weather_response.content.text}"
    ),
    role=MessageRole.USER
)
planning_response = planning_client.send_message(planning_message)

print(planning_response.content.text)
```

## 📚 Detailed Documentation

For more detailed documentation and examples, please check out our [Documentation Site](https://github.com/themanojdesai/python-a2a).

## 💡 Why A2A Matters

The Agent-to-Agent (A2A) protocol enables a new paradigm of interoperable AI systems with several key benefits:

- **Specialization**: Agents can excel at specific tasks rather than trying to do everything
- **Modularity**: Components can be improved or replaced independently
- **Composability**: Agents can be combined in different ways to solve new problems
- **Robustness**: If one agent fails, others can continue to operate
- **Scalability**: Complex workflows can be broken down into manageable pieces

A2A allows developers to create ecosystems of agents that can collaborate to solve complex problems that would be difficult for a single agent to handle alone.

## 📋 Example Use Cases

- **Multi-step reasoning**: Break down complex reasoning into specialized steps
- **Tool use**: Connect LLMs to specialized agents that access tools and APIs
- **Customer service**: Route customer queries to specialized agent bots
- **Research assistants**: Combine agents for literature search, data analysis, and summary generation
- **Collaborative writing**: Connect agents for ideation, drafting, editing, and fact-checking
- **Enterprise systems**: Integrate agents that interface with different internal tools and databases

## 🔗 Resources

- [Google A2A Protocol Documentation](https://google.github.io/A2A/)
- [Google A2A GitHub Repository](https://github.com/google/A2A)
- [Google Developers Blog: A2A - A New Era of Agent Interoperability](https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/)

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 👨‍💻 Author

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.