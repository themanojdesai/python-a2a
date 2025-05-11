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

  <p>
      <a href="README.md">English</a> | <a href="README_zh.md">简体中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_es.md">Español</a> | <a href="README_de.md">Deutsch</a> | <a href="README_fr.md">Français</a>
      <!-- Add other languages here like: | <a href="README_de.md">Deutsch</a> -->
  </p>
  
**Offizielle Python-Implementierung des Google Agent-to-Agent (A2A)-Protokolls mit Model Context Protocol (MCP)-Integration**

</div>

## 🌟 Überblick

Python A2A ist eine umfassende, für die Produktion bereite Bibliothek zur Implementierung des [Google Agent-to-Agent (A2A)-Protokolls](https://google.github.io/A2A/), mit vollständiger Unterstützung für das [Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/). Sie bietet alle Funktionen, die erforderlich sind, um ein interoperables Ökosystem von KI-Agenten zu erstellen, die nahtlos zusammenarbeiten können, um komplexe Probleme zu lösen.

Das A2A-Protokoll definiert einen Standardkommunikationsstandard für die Interaktion von KI-Agenten, und das MCP erweitert diese Fähigkeit durch einen standardisierten Ansatz, mit dem Agenten auf externe Tools und Datenspeicher zugreifen können. Python A2A macht diese Protokolle durch eine intuitive API leicht nutzbar, sodass Entwickler komplexe Multi-Agenten-Systeme erstellen können.

## 📋 Was ist neu in v0.5.X

- **Agenten-Entdeckung**: Einbaulose Unterstützung für Agenten-Registrierung und -Entdeckung mit vollständiger Kompatibilität zum Google A2A-Protokoll
- **LangChain-Integration**: Nahtlose Integration mit LangChains Tools und Agenten
- **Erweitertes Tool-Ökosystem**: Nutzen Sie Tools sowohl von LangChain als auch von MCP in jedem Agenten
- **Erhöhte Agenten-Interoperabilität**: Konvertieren Sie zwischen A2A-Agenten und LangChain-Agenten
- **Gemischter Workflow-Engine**: Erstellen Sie Workflows, die beide Ökosysteme kombinieren
- **Vereinfachte Agenten-Entwicklung**: Greifen Sie sofort auf tausende vordefinierter Tools zu
- **Erweiterte Streaming-Architektur**: Verbessertes Streaming mit Server-Sent Events (SSE), bessere Fehlerbehandlung und robuste Fallback-Mechanismen
- **Aufgabenbasiertes Streaming**: Neues `tasks_send_subscribe`-Verfahren für Echtzeit-Updates zu Aufgaben
- **Streaming-Chunk-API**: Verbesserte Chunk-Verarbeitung mit der `StreamingChunk`-Klasse für strukturierte Streaming-Daten
- **Mehrfach-Endpunkt-Unterstützung**: Automatische Entdeckung und Fallback-Mechanismen über mehrere Streaming-Endpunkte

## 📋 Was ist neu in v0.4.X

- **Agenten-Netzwerksystem**: Verwalten und entdecken Sie mehrere Agenten mit der neuen `AgentNetwork`-Klasse
- **Echtzeit-Streaming**: Implementieren Sie Streaming-Antworten mit `StreamingClient` für reaktive Benutzeroberflächen
- **Workflow-Engine**: Definieren Sie komplexe Multi-Agenten-Workflows mit der neuen flüssigen API, einschließlich bedingter Verzweigungen und paralleler Ausführung
- **KI-gestützter Router**: Routen Sie Abfragen automatisch an den passenden Agenten mit dem `AIAgentRouter`
- **Kommandozeilen-Schnittstelle**: Steuern Sie Ihre Agenten über die Terminal mit dem neuen CLI-Tool
- **Erweiterte Asynchron-Unterstützung**: Bessere async/await-Unterstützung in der gesamten Bibliothek
- **Neue Verbindungs-Optionen**: Verbesserte Fehlerbehandlung und Wiederholungslogik für robustere Agenten-Kommunikation

## ✨ Warum Python A2A wählen?

- **Vollständige Implementierung**: Implementiert das offizielle A2A-Spezifikation ohne Kompromisse
- **Agenten-Entdeckung**: Einbaulose Agenten-Registrierung und -Entdeckung für die Erstellung von Agenten-Ökosystemen
- **MCP-Integration**: Erste Wahl für das Model Context Protocol für leistungsstarke Tool-nutzende Agenten
- **Unternehmensbereit**: Für Produktionsumgebungen gebaut mit robuster Fehlerbehandlung und Validierung
- **Framework-unabhängig**: Funktioniert mit jedem Python-Framework (Flask, FastAPI, Django, etc.)
- **LLM-Anbieter-Flexibilität**: Native Integrationen mit OpenAI, Anthropic, AWS Bedrock und mehr
- **Minimale Abhängigkeiten**: Kernfunktionalität benötigt nur die `requests`-Bibliothek
- **Exzellentes Entwicklererlebnis**: Umfassende Dokumentation, Typ-Hinweise und Beispiele

## 📦 Installation

### Mit pip (traditionell)

Installieren Sie das Basispaket mit allen Abhängigkeiten:

```bash
pip install python-a2a  # Enthält LangChain, MCP und andere Integrationen
```

Oder installieren Sie mit spezifischen Komponenten basierend auf Ihren Bedürfnissen:

```bash
# Für Flask-basierte Server-Unterstützung
pip install "python-a2a[server]"

# Für OpenAI-Integration
pip install "python-a2a[openai]"

# Für Anthropic Claude-Integration
pip install "python-a2a[anthropic]"

# Für AWS-Bedrock-Integration
pip install "python-a2a[bedrock]"

# Für MCP-Unterstützung (Model Context Protocol)
pip install "python-a2a[mcp]"

# Für alle optionalen Abhängigkeiten
pip install "python-a2a[all]"
```

### Mit UV (empfohlen)

[UV](https://github.com/astral-sh/uv) ist ein modernes Python-Paketverwaltungs-Tool, das schneller und zuverlässiger als pip ist. Um mit UV zu installieren:

```bash
# Installieren Sie UV, falls Sie es noch nicht haben
curl -LsSf https://astral.sh/uv/install.sh | sh

# Installieren Sie das Basispaket
uv install python-a2a
```

### Entwicklungsininstallation

Für die Entwicklung wird UV empfohlen, da es schneller ist:

```bash
# Klonen Sie das Repository
git clone https://github.com/themanojdesai/python-a2a.git
cd python-a2a

# Erstellen Sie eine virtuelle Umgebung und installieren Sie die Entwicklungsabhängigkeiten
uv venv
source .venv/bin/activate  # Auf Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

> 💡 **Tipp**: Klicken Sie auf die Code-Blöcke, um sie in die Zwischenablage zu kopieren.

## 🚀 Schnellstart-Beispiele

### 1. Erstellen eines einfachen A2A-Agenten mit Fähigkeiten

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

### 2. Erstellen eines Agenten-Netzwerks mit mehreren Agenten

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

### Echtzeit-Streaming

Erhalten Sie Echtzeit-Antworten von Agenten mit umfassender Streaming-Unterstützung:

```python
import asyncio
from python_a2a import StreamingClient, Message, TextContent, MessageRole

async def main():
    client = StreamingClient("http://localhost:5000")
    
    # Create a message with required role parameter
    message = Message(
        content=TextContent(text="Tell me about A2A streaming"),
        role=MessageRole.USER
    )
    
    # Stream the response and process chunks in real-time
    try:
        async for chunk in client.stream_response(message):
            # Handle different chunk formats (string or dictionary)
            if isinstance(chunk, dict):
                if "content" in chunk:
                    print(chunk["content"], end="", flush=True)
                elif "text" in chunk:
                    print(chunk["text"], end="", flush=True)
                else:
                    print(str(chunk), end="", flush=True)
            else:
                print(str(chunk), end="", flush=True)
    except Exception as e:
        print(f"Streaming error: {e}")
```

Schauen Sie sich das Verzeichnis `examples/streaming/` für vollständige Streaming-Beispiele an:

- **basic_streaming.py**: Minimaler Streaming-Implementierung (starten Sie hier!)
- **01_basic_streaming.py**: Umfassende Einführung in die Grundlagen des Streamings
- **02_advanced_streaming.py**: Erweitertes Streaming mit verschiedenen Chunking-Strategien
- **03_streaming_llm_integration.py**: Integration von Streaming mit LLM-Anbietern
- **04_task_based_streaming.py**: Aufgabenbasiertes Streaming mit Fortschrittsüberwachung
- **05_streaming_ui_integration.py**: Streaming-Benutzeroberflächenintegration (CLI und Web)
- **06_distributed_streaming.py**: Verteilte Streaming-Architektur

### 3. Workflow-Engine

Die neue Workflow-Engine ermöglicht es Ihnen, komplexe Agenten-Interaktionen zu definieren:

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

### 4. KI-gestützter Router

Intelligente Routierung, um den besten Agenten für jede Abfrage auszuwählen:

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

### 5. Definieren komplexer Workflows mit mehreren Agenten

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

### 6. Verwenden der Kommandozeilen-Schnittstelle

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

## 🔄 LangChain-Integration (Neu in v0.5.X)

Python A2A enthält eine eingebaute LangChain-Integration, die es einfach macht, das Beste aus beiden Ökosystemen zu kombinieren:

### 1. Konvertieren von MCP-Tools in LangChain

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

### 2. Konvertieren von LangChain-Tools in MCP-Server

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

### 3. Konvertieren von LangChain-Komponenten in A2A-Server

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

### 4. Konvertieren von A2A-Agenten in LangChain-Agenten

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

LangChain wird automatisch als Abhängigkeit mit python-a2a installiert, also funktioniert alles direkt aus der Box:

```bash
pip install python-a2a
# Das ist alles! LangChain ist automatisch enthalten
```

## 🧩 Kernfunktionen

### Agenten-Netzwerke

Python A2A enthält jetzt ein leistungsstarkes System zur Verwaltung mehrerer Agenten:

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

### 7. Agenten-Entdeckung und -Registrierung

```python
from python_a2a import AgentCard, A2AServer, run_server
from python_a2a.discovery import AgentRegistry, run_registry, enable_discovery, DiscoveryClient
import threading
import time

# Create a registry server
registry = AgentRegistry(
    name="A2A Registry Server",
    description="Central registry for agent discovery"
)

# Run the registry in a background thread
registry_port = 8000
thread = threading.Thread(
    target=lambda: run_registry(registry, host="0.0.0.0", port=registry_port),
    daemon=True
)
thread.start()
time.sleep(1)  # Let the registry start

# Create a sample agent
agent_card = AgentCard(
    name="Weather Agent",
    description="Provides weather information",
    url="http://localhost:8001",
    version="1.0.0",
    capabilities={
        "weather_forecasting": True,
        "google_a2a_compatible": True  # Enable Google A2A compatibility
    }
)
agent = A2AServer(agent_card=agent_card)

# Enable discovery - this registers with the registry
registry_url = f"http://localhost:{registry_port}"
discovery_client = enable_discovery(agent, registry_url=registry_url)

# Run the agent in a separate thread
agent_thread = threading.Thread(
    target=lambda: run_server(agent, host="0.0.0.0", port=8001),
    daemon=True
)
agent_thread.start()
time.sleep(1)  # Let the agent start

# Create a discovery client for discovering agents
client = DiscoveryClient(agent_card=None)  # No agent card needed for discovery only
client.add_registry(registry_url)

# Discover all agents
agents = client.discover()
print(f"Discovered {len(agents)} agents:")
for agent in agents:
    print(f"- {agent.name} at {agent.url}")
    print(f"  Capabilities: {agent.capabilities}")
```

## 📖 Architektur & Designprinzipien

Python A2A basiert auf drei grundlegenden Designprinzipien:

1. **Protokoll zuerst**: Strenges Einhalten der A2A- und MCP-Protokoll-Spezifikationen für maximale Interoperabilität

2. **Modularität**: Alle Komponenten sind so gestaltet, dass sie komponierbar und austauschbar sind

3. **Progressive Erweiterung**: Starten Sie einfach und fügen Sie nur dann Komplexität hinzu, wenn sie benötigt wird

Die Architektur besteht aus acht Hauptkomponenten:

- **Modelle**: Datenstrukturen, die A2A-Nachrichten, Aufgaben und Agenten-Karten darstellen
- **Client**: Komponenten zum Senden von Nachrichten an A2A-Agenten und Verwalten von Agenten-Netzwerken
- **Server**: Komponenten zum Erstellen von A2A-kompatiblen Agenten
- **Entdeckung**: Registrierungs- und Entdeckungsmechanismen für Agenten-Ökosysteme
- **MCP**: Tools zur Implementierung von Model Context Protocol-Servern und -Clients
- **LangChain**: Brückenkomponenten für die LangChain-Integration
- **Workflow**: Motor zur Orchestrierung komplexer Agenten-Interaktionen
- **Utils**: Hilfsfunktionen für allgemeine Aufgaben
- **CLI**: Kommandozeilen-Schnittstelle zur Interaktion mit Agenten

## 🗺️ Anwendungsfälle

Python A2A kann verwendet werden, um eine breite Palette von KI-Systemen zu erstellen:

### Forschung & Entwicklung

- **Experimentier-Framework**: Wechseln Sie leicht zwischen verschiedenen LLM-Backends, während Sie die gleiche Agenten-Schnittstelle beibehalten
- **Benchmark-Suite**: Vergleichen Sie die Leistung verschiedener Agenten-Implementierungen auf standardisierten Aufgaben
- **Streaming-Forschungs-Assistenten**: Erstellen Sie reaktive Forschungstools mit Echtzeit-Ausgabe mithilfe von Streaming

### Unternehmenssysteme

- **KI-Orchestrierung**: Koordinieren Sie mehrere KI-Agenten über verschiedene Abteilungen hinweg mit Agenten-Netzwerken
- **Integration in Legacy-Systeme**: Verpacken Sie Legacy-Systeme mit A2A-Schnittstellen für KI-Zugänglichkeit
- **Komplexe Workflows**: Erstellen Sie komplexe Geschäftsprozesse mit Multi-Agenten-Workflows und bedingten Verzweigungen

### Kundennahen Anwendungen

- **Mehrfach-Stufen-Assistenten**: Zerlegen Sie komplexe Benutzeranfragen in Unteraufgaben, die von spezialisierten Agenten bearbeitet werden
- **Tool-nutzende Agenten**: Verbinden Sie LLMs mit Datenbank-Agenten, Rechenagenten und mehr mithilfe von MCP
- **Echtzeit-Chatschnittstellen**: Erstellen Sie reaktive Chat-Anwendungen mit Streaming-Antwort-Unterstützung

### Bildung & Training

- **KI-Bildung**: Erstellen Sie Bildungssysteme, die die Zusammenarbeit von Agenten demonstrieren
- **Simulationsumgebungen**: Erstellen Sie Simulationsumgebungen, in denen mehrere Agenten interagieren
- **Bildungsworkflows**: Gestalten Sie Schritt-für-Schritt-Lernprozesse mit Rückkopplungsschleifen

## 🛠️ Reale Beispiele

Schauen Sie sich das Verzeichnis [`examples/`](https://github.com/themanojdesai/python-a2a/tree/main/examples) für reale Beispiele an, einschließlich:

- Multi-Agenten-Kundendienst-Systeme
- LLM-gestützte Forschungsassistenten mit Tool-Zugriff
- Echtzeit-Streaming-Implementierungen
- LangChain-Integration-Beispiele
- MCP-Server-Implementierungen für verschiedene Tools
- Workflow-Orchestrierungsbeispiele
- Agenten-Netzwerk-Verwaltung

## 🔄 Verwandte Projekte

Hier sind einige verwandte Projekte im Bereich KI-Agenten und Interoperabilität:

- [**Google A2A**](https://github.com/google/A2A) - Die offizielle Google A2A-Protokoll-Spezifikation
- [**LangChain**](https://github.com/langchain-ai/langchain) - Framework für die Erstellung von Anwendungen mit LLMs
- [**AutoGen**](https://github.com/microsoft/autogen) - Microsofts Framework für Multi-Agenten-Unterhaltungen
- [**CrewAI**](https://github.com/joaomdmoura/crewAI) - Framework für die Orchestrierung von Rollenspiel-Agenten
- [**MCP**](https://github.com/contextco/mcp) - Das Model Context Protocol für Tool-nutzende Agenten

## 👥 Mitwirkende

Vielen Dank an alle Mitwirkenden!

<a href="https://github.com/themanojdesai/python-a2a/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=themanojdesai/python-a2a" />
</a>

Möchten Sie mitwirken? Schauen Sie sich unser [Mitwirkungshandbuch](https://python-a2a.readthedocs.io/en/latest/contributing.html) an.

## 🤝 Community & Support

- **[GitHub-Probleme](https://github.com/themanojdesai/python-a2a/issues)**: Melden Sie Fehler oder fordern Sie Funktionen an
- **[GitHub-Diskussionen](https://github.com/themanojdesai/python-a2a/discussions)**: Stellen Sie Fragen und teilen Sie Ideen
- **[Mitwirkungshandbuch](https://python-a2a.readthedocs.io/en/latest/contributing.html)**: Erfahren Sie, wie Sie zum Projekt beitragen können
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**: Besuchen Sie unsere Dokumentationsseite

## 📝 Zitieren dieses Projekts

Wenn Sie Python A2A in Ihren Forschungs- oder akademischen Arbeiten verwenden, zitieren Sie es bitte wie folgt:

```
@software{desai2025pythona2a,
  author = {Desai, Manoj},
  title = {Python A2A: A Comprehensive Implementation of the Agent-to-Agent Protocol},
  url = {https://github.com/themanojdesai/python-a2a},
  version = {0.5.0},
  year = {2025},
}
```

## ⭐ Sternen Sie dieses Repository

Wenn Sie diese Bibliothek nützlich finden, geben Sie ihr bitte einen Stern auf GitHub! Es hilft anderen, das Projekt zu entdecken und motiviert die weitere Entwicklung.

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

### Stern-Historie

[![Star History Chart](https://api.star-history.com/svg?repos=themanojdesai/python-a2a&type=Date)](https://star-history.com/#themanojdesai/python-a2a&Date)

## 🙏 Anerkennungen

- Das [Google A2A-Team](https://github.com/google/A2A) für das Erstellen des A2A-Protokolls
- Das [Contextual AI-Team](https://contextual.ai/) für das Model Context Protocol
- Das [LangChain-Team](https://github.com/langchain-ai) für ihr leistungsstarkes LLM-Framework
- Alle unsere [Mitwirkenden](https://github.com/themanojdesai/python-a2a/graphs/contributors) für ihre wertvollen Beiträge

## 👨‍💻 Autor

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 Lizenz

Dieses Projekt unterliegt der MIT-Lizenz - siehe die Datei [LICENSE](LICENSE) für weitere Details.

---

Erschaffen mit ❤️ von [Manoj Desai](https://github.com/themanojdesai)
