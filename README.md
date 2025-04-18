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

## 📋 What's New in v0.3.0

- **Full A2A Protocol Support**: Enhanced implementation with Agent Cards, Tasks, and Skills
- **Interactive Documentation**: FastAPI-style OpenAPI documentation for agents
- **Streamlined Developer Experience**: New decorators for easier agent and skill creation
- **Backward Compatibility**: All existing code continues to work without modification
- **Enhanced Messaging**: Improved error handling and support for rich message content

## ✨ Why Choose Python A2A?

- **Complete Implementation**: Fully implements the official A2A specification with zero compromises
- **MCP Integration**: First-class support for Model Context Protocol for powerful tool-using agents
- **Enterprise Ready**: Built for production environments with robust error handling and validation
- **Framework Agnostic**: Works with any Python framework (Flask, FastAPI, Django, etc.)
- **LLM Provider Flexibility**: Native integrations with OpenAI, Anthropic, and more
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

### 2. Connect to an A2A Agent

```python
from python_a2a import A2AClient

# Create a client connected to an A2A-compatible agent
client = A2AClient("http://localhost:5000")

# View agent information
print(f"Connected to: {client.agent_card.name}")
print(f"Description: {client.agent_card.description}")
print(f"Skills: {[skill.name for skill in client.agent_card.skills]}")

# Ask a question
response = client.ask("What's the weather in Paris?")
print(f"Response: {response}")
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

### 4. Generate Interactive Documentation

```python
from python_a2a import AgentCard, AgentSkill, generate_a2a_docs, generate_html_docs
import os

# Create an agent card 
agent_card = AgentCard(
    name="Travel API",
    description="Get travel information and recommendations",
    url="http://localhost:5000",
    version="1.0.0",
    skills=[
        AgentSkill(
            name="Get Weather",
            description="Get weather for a destination",
            tags=["weather", "travel"]
        ),
        AgentSkill(
            name="Find Attractions",
            description="Find attractions at a destination",
            tags=["attractions", "travel"]
        )
    ]
)

# Generate documentation
output_dir = "docs"
os.makedirs(output_dir, exist_ok=True)
spec = generate_a2a_docs(agent_card, output_dir)
html = generate_html_docs(spec)

with open(os.path.join(output_dir, "index.html"), "w") as f:
    f.write(html)

print(f"Documentation available at: {os.path.abspath(os.path.join(output_dir, 'index.html'))}")
```

### 5. Create an MCP-Enabled A2A Agent

```python
from python_a2a import A2AServer, A2AMCPAgent, run_server
from python_a2a.mcp import FastMCP, text_response

# Create MCP server
calculator_mcp = FastMCP(
    name="Calculator MCP",
    description="Provides calculation functions"
)

@calculator_mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

# Create A2A agent with MCP capabilities
class CalculatorAgent(A2AServer, A2AMCPAgent):
    def __init__(self):
        A2AServer.__init__(self)
        A2AMCPAgent.__init__(self, mcp_servers={"calc": calculator_mcp})
    
    async def handle_task_async(self, task):
        try:
            text = task.message.get("content", {}).get("text", "")
            if "add" in text:
                # Extract numbers
                import re
                numbers = [float(n) for n in re.findall(r"[-+]?\d*\.?\d+", text)]
                if len(numbers) >= 2:
                    # Call MCP tool
                    result = await self.call_mcp_tool("calc", "add", a=numbers[0], b=numbers[1])
                    task.artifacts = [{
                        "parts": [{"type": "text", "text": f"The sum is {result}"}]
                    }]
                    return task
            # Default response
            task.artifacts = [{
                "parts": [{"type": "text", "text": "I can help with calculations."}]
            }]
            return task
        except Exception as e:
            task.artifacts = [{
                "parts": [{"type": "text", "text": f"Error: {str(e)}"}]
            }]
            return task

# Run the agent
if __name__ == "__main__":
    agent = CalculatorAgent()
    run_server(agent, port=5000)
```

## 🧩 Core Features

### Agent Discovery

Python A2A provides a rich set of models for agent discovery:

```python
from python_a2a import AgentCard, AgentSkill

# Create an agent card
agent_card = AgentCard(
    name="Weather API",
    description="Get weather information for locations",
    url="http://localhost:5000",
    version="1.0.0",
    capabilities={"streaming": True},
    skills=[
        AgentSkill(
            name="Get Weather",
            description="Get current weather for a location",
            tags=["weather", "current"],
            examples=["What's the weather in New York?"]
        ),
        AgentSkill(
            name="Get Forecast",
            description="Get 5-day forecast for a location",
            tags=["weather", "forecast"],
            examples=["5-day forecast for Tokyo"]
        )
    ]
)
```

### Tasks and Messaging

The A2A protocol uses tasks to represent units of work:

```python
from python_a2a import Task, TaskStatus, TaskState, Message, TextContent, MessageRole

# Create a task with a message
message = Message(
    content=TextContent(text="What's the weather in Paris?"),
    role=MessageRole.USER
)
task = Task(message=message.to_dict())

# Update task status
task.status = TaskStatus(state=TaskState.COMPLETED)

# Add response artifact
task.artifacts = [{
    "parts": [{
        "type": "text",
        "text": "It's sunny and 72°F in Paris"
    }]
}]
```

### Decorators for Easy Agent Creation

The new decorator syntax makes agent and skill creation seamless:

```python
from python_a2a import agent, skill, A2AServer, run_server

@agent(
    name="Calculator",
    description="Performs calculations",
    version="1.0.0"
)
class CalculatorAgent(A2AServer):
    
    @skill(
        name="Add",
        description="Add two numbers",
        tags=["math", "addition"]
    )
    def add(self, a, b):
        """
        Add two numbers together.
        
        Examples:
            "What is 5 + 3?"
            "Add 10 and 20"
        """
        return float(a) + float(b)
    
    @skill(
        name="Subtract",
        description="Subtract two numbers",
        tags=["math", "subtraction"]
    )
    def subtract(self, a, b):
        """Subtract b from a."""
        return float(a) - float(b)
    
    # Implement task handling
    def handle_task(self, task):
        # Task handling logic here
        pass

# Run the server
calculator = CalculatorAgent()
run_server(calculator, port=5000)
```

### Interactive Documentation

Generate OpenAPI-style documentation for your A2A agents:

```python
from python_a2a import AgentCard, generate_a2a_docs, generate_html_docs
import os

# Create or load agent card
agent_card = AgentCard(...)

# Generate documentation
docs_dir = "docs"
os.makedirs(docs_dir, exist_ok=True)

# Create OpenAPI spec
spec = generate_a2a_docs(agent_card, docs_dir)

# Generate HTML documentation
html = generate_html_docs(spec)
with open(os.path.join(docs_dir, "index.html"), "w") as f:
    f.write(html)
```

## 📖 Architecture & Design Principles

Python A2A is built on three core design principles:

1. **Protocol First**: Adheres strictly to the A2A and MCP protocol specifications for maximum interoperability

2. **Modularity**: All components are designed to be composable and replaceable

3. **Progressive Enhancement**: Start simple and add complexity only as needed

The architecture consists of five main components:

- **Models**: Data structures representing A2A messages, tasks, and agent cards
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

### Weather Information System

Let's build a simple weather information system using A2A agents:

1. **Weather Data Agent**: Provides current weather and forecasts
2. **Travel Recommendation Agent**: Uses weather data to make travel suggestions
3. **User Interface Agent**: Orchestrates the other agents to answer user queries

```python
# Weather Data Agent
@agent(name="Weather API", description="Weather data source")
class WeatherAgent(A2AServer):
    @skill(name="Get Weather", description="Get current weather")
    def get_weather(self, location):
        # Implementation...
        return weather_data

# Travel Recommendation Agent
@agent(name="Travel Advisor", description="Travel recommendations")
class TravelAgent(A2AServer):
    def __init__(self):
        super().__init__()
        self.weather_client = A2AClient("http://localhost:5001")
    
    @skill(name="Recommend Destination", description="Suggest travel destinations")
    def recommend(self, preferences):
        # Get weather for potential destinations
        weather_data = self.weather_client.ask(f"Get weather for {destination}")
        # Make recommendations based on weather and preferences
        return recommendations

# User Interface Agent
@agent(name="Travel Assistant", description="Your personal travel assistant")
class AssistantAgent(A2AServer):
    def __init__(self):
        super().__init__()
        self.weather_client = A2AClient("http://localhost:5001")
        self.travel_client = A2AClient("http://localhost:5002")
    
    def handle_task(self, task):
        # Extract user query
        text = task.message.get("content", {}).get("text", "")
        
        if "weather" in text.lower():
            # Forward to weather agent
            response = self.weather_client.ask(text)
        elif "recommend" in text.lower() or "suggest" in text.lower():
            # Forward to travel agent
            response = self.travel_client.ask(text)
        else:
            # General response
            response = "I can help with weather information and travel recommendations."
        
        # Create artifact with response
        task.artifacts = [{"parts": [{"type": "text", "text": response}]}]
        return task
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
- The [Contextual AI team](https://contextual.ai/) for the Model Context Protocol
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