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
      <a href="README.md">English</a> | <a href="README_zh.md">简体中文</a> | <a href="README_zh-TW.md">繁體中文</a> | <a href="README_ja.md">日本語</a> | <a href="README_es.md">Español</a> | <a href="README_de.md">Deutsch</a> | <a href="README_fr.md">Français</a>
      <!-- Add other languages here like: | <a href="README_de.md">Deutsch</a> -->
  </p>
  
**Implementación oficial de Python para el protocolo Google Agent-to-Agent (A2A), con integración de Model Context Protocol (MCP)**

</div>

## 🌟 Descripción general

Python A2A es una biblioteca completa y lista para producción para implementar el [protocolo Agent-to-Agent (A2A) de Google](https://google.github.io/A2A/) con soporte completo para el [Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/). Proporciona todas las funcionalidades necesarias para construir un ecosistema de agentes de IA interoperables que puedan colaborar de forma fluida para resolver problemas complejos.

El protocolo A2A establece un formato de comunicación estándar para que los agentes de IA interactúen, y el MCP amplía esta capacidad proporcionando un método estandarizado para que los agentes accedan a herramientas y fuentes de datos externas. Python A2A hace que estos protocolos sean fáciles de usar mediante una API intuitiva, permitiendo a los desarrolladores construir sistemas de agentes complejos.

## 📋 Nuevas características en v0.5.X

- **Descubrimiento de agentes**: Soporte integrado para registro y descubrimiento de agentes con compatibilidad completa con el protocolo Google A2A
- **Integración con LangChain**: Integración fluida con las herramientas y agentes de LangChain
- **Ecosistema de herramientas expandido**: Use herramientas de LangChain y MCP en cualquier agente
- **Interoperabilidad mejorada entre agentes**: Convierta entre agentes A2A y agentes de LangChain 
- **Motor de flujo de trabajo mixto**: Cree flujos de trabajo combinando ambos ecosistemas
- **Desarrollo de agentes simplificado**: Acceda a miles de herramientas preconstruidas de inmediato
- **Arquitectura de transmisión avanzada**: Transmisión mejorada con eventos de servidor enviado (SSE), mejor manejo de errores y mecanismos de respaldo robustos
- **Transmisión basada en tareas**: Nuevo método `tasks_send_subscribe` para transmisión de actualizaciones de tareas en tiempo real
- **API de fragmentos de transmisión**: Procesamiento de fragmentos mejorado con la clase `StreamingChunk` para datos de transmisión estructurados
- **Soporte para múltiples puntos finales**: Descubrimiento y respaldo automáticos entre múltiples puntos finales de transmisión

## 📋 Nuevas características en v0.4.X

- **Sistema de red de agentes**: Administre y descubra múltiples agentes con la nueva clase `AgentNetwork`
- **Transmisión en tiempo real**: Implemente respuestas de transmisión con `StreamingClient` para interfaces de usuario responsivas
- **Motor de flujo de trabajo**: Defina flujos de trabajo complejos de múltiples agentes usando la nueva API fluida con bifurcación condicional y ejecución paralela
- **Enrutador impulsado por IA**: Enrutamiento automático de consultas al agente más adecuado con `AIAgentRouter`
- **Interfaz de línea de comandos**: Controle sus agentes desde el terminal con la nueva herramienta CLI
- **Soporte asincrónico mejorado**: Mejor soporte para async/await a lo largo de la biblioteca
- **Nuevas opciones de conexión**: Mejor manejo de errores y lógica de reintento para una comunicación de agentes más robusta

## ✨ ¿Por qué elegir Python A2A?

- **Implementación completa**: Implementa completamente la especificación oficial de A2A sin compromisos
- **Descubrimiento de agentes**: Registro y descubrimiento integrados para construir ecosistemas de agentes
- **Integración de MCP**: Soporte de primera clase para el Protocolo de Contexto del Modelo para agentes que usan herramientas
- **Listo para empresas**: Construido para entornos de producción con manejo robusto de errores y validación
- **Agnóstico de marco**: Funciona con cualquier marco de Python (Flask, FastAPI, Django, etc.)
- **Flexibilidad del proveedor de LLM**: Integraciones nativas con OpenAI, Anthropic, AWS Bedrock y más
- **Dependencias mínimas**: La funcionalidad básica requiere solo la biblioteca `requests`
- **Excelente experiencia del desarrollador**: Documentación completa, sugerencias de tipo y ejemplos

## 📦 Instalación

### Usando pip (tradicional)

Instale el paquete base con todas las dependencias:

```bash
pip install python-a2a  # Incluye LangChain, MCP y otras integraciones
```

O instale con componentes específicos según sus necesidades:

```bash
# Para soporte de servidor basado en Flask
pip install "python-a2a[server]"

# Para integración con OpenAI
pip install "python-a2a[openai]"

# Para integración con Anthropic Claude
pip install "python-a2a[anthropic]"

# Para integración con AWS-Bedrock
pip install "python-a2a[bedrock]"

# Para soporte de MCP (Model Context Protocol)
pip install "python-a2a[mcp]"

# Para todas las dependencias opcionales
pip install "python-a2a[all]"
```

### Usando UV (recomendado)

[UV](https://github.com/astral-sh/uv) es una herramienta moderna de gestión de paquetes de Python que es más rápida y confiable que pip. Para instalar con UV:

```bash
# Instale UV si aún no lo tiene
curl -LsSf https://astral.sh/uv/install.sh | sh

# Instale el paquete base
uv install python-a2a
```

### Instalación para desarrollo

Para desarrollo, se recomienda UV por su velocidad:

```bash
# Clone el repositorio
git clone https://github.com/themanojdesai/python-a2a.git
cd python-a2a

# Cree un entorno virtual y instale dependencias de desarrollo
uv venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

> 💡 **Consejo**: Haga clic en los bloques de código para copiarlos a su portapapeles.

## 🚀 Ejemplos rápidos

### 1. Cree un agente A2A simple con habilidades

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

### 2. Construya una red de agentes con múltiples agentes

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

### Transmisión en tiempo real

Obtenga respuestas en tiempo real de los agentes con soporte de transmisión completo:

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

Consulte el directorio `examples/streaming/` para ejemplos completos de transmisión:

- **basic_streaming.py**: Implementación mínima de transmisión (¡comience aquí!)
- **01_basic_streaming.py**: Introducción completa a los fundamentos de transmisión
- **02_advanced_streaming.py**: Transmisión avanzada con diferentes estrategias de fragmentación
- **03_streaming_llm_integration.py**: Integración de transmisión con proveedores de LLM
- **04_task_based_streaming.py**: Transmisión basada en tareas con seguimiento de progreso
- **05_streaming_ui_integration.py**: Integración de interfaz de usuario de transmisión (CLI y web)
- **06_distributed_streaming.py**: Arquitectura de transmisión distribuida

### 3. Motor de flujo de trabajo

El nuevo motor de flujo de trabajo le permite definir interacciones complejas entre agentes:

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

### 4. Enrutador impulsado por IA

Enrutamiento inteligente para seleccionar el mejor agente para cada consulta:

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

### 5. Defina flujos de trabajo complejos con múltiples agentes

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

### 6. Use la interfaz de línea de comandos

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

## 🔄 Integración con LangChain (Nuevo en v0.5.X)

Python A2A incluye una integración integrada con LangChain, lo que facilita combinar lo mejor de ambos ecosistemas:

### 1. Conversión de herramientas MCP a LangChain

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

### 2. Conversión de herramientas de LangChain a servidor MCP

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

### 3. Conversión de componentes de LangChain a servidores A2A

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

### 4. Conversión de agentes A2A a agentes de LangChain

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

LangChain se instala automáticamente como dependencia con python-a2a, por lo que todo funciona de inmediato:

```bash
pip install python-a2a
# ¡Eso es todo! LangChain se incluye automáticamente
```

## 🧩 Características principales

### Redes de agentes

Python A2A ahora incluye un sistema poderoso para administrar múltiples agentes:

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

### 7. Descubrimiento y registro de agentes

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

## 📖 Arquitectura y principios de diseño

Python A2A se basa en tres principios de diseño fundamentales:

1. **Protocolo primero**: Se adhiere estrictamente a las especificaciones de los protocolos A2A y MCP para máxima interoperabilidad

2. **Modularidad**: Todos los componentes están diseñados para ser componibles y reemplazables

3. **Mejora progresiva**: Comience simple y agregue complejidad solo cuando sea necesario

La arquitectura consta de ocho componentes principales:

- **Modelos**: Estructuras de datos que representan mensajes A2A, tareas y tarjetas de agentes
- **Cliente**: Componentes para enviar mensajes a agentes A2A y administrar redes de agentes
- **Servidor**: Componentes para construir agentes compatibles con A2A
- **Descubrimiento**: Mecanismos de registro y descubrimiento para ecosistemas de agentes
- **MCP**: Herramientas para implementar servidores y clientes del Protocolo de Contexto del Modelo
- **LangChain**: Componentes de puente para la integración con LangChain
- **Flujo de trabajo**: Motor para orquestar interacciones complejas entre agentes
- **Utils**: Funciones auxiliares para tareas comunes
- **CLI**: Interfaz de línea de comandos para interactuar con agentes

## 🗺️ Casos de uso

Python A2A puede usarse para construir una amplia gama de sistemas de IA:

### Investigación y desarrollo

- **Marco de experimentación**: Cambie fácilmente entre diferentes backend de LLM manteniendo la misma interfaz de agente
- **Conjunto de pruebas**: Compare el rendimiento de diferentes implementaciones de agentes en tareas estandarizadas
- **Asistentes de investigación con transmisión**: Cree herramientas de investigación responsivas con salida en tiempo real usando transmisión

### Sistemas empresariales

- **Orquestación de IA**: Coordine múltiples agentes de IA a través de diferentes departamentos usando redes de agentes
- **Integración con sistemas legados**: Envuelva sistemas legados con interfaces A2A para accesibilidad de IA
- **Flujos de trabajo complejos**: Cree procesos empresariales sofisticados con flujos de trabajo de múltiples agentes y bifurcación condicional

### Aplicaciones orientadas al cliente

- **Asistentes de varias etapas**: Divida consultas complejas del usuario en subtareas manejadas por agentes especializados
- **Agentes que usan herramientas**: Conecte LLMs a agentes de base de datos, agentes de cálculo y más usando MCP
- **Interfaz de chat en tiempo real**: Construya aplicaciones de chat responsivas con soporte de transmisión de respuestas

### Educación y capacitación

- **Sistemas educativos de IA**: Cree sistemas educativos que demuestren la colaboración de agentes
- **Entornos de simulación**: Construya entornos simulados donde múltiples agentes interactúen
- **Flujos de trabajo educativos**: Diseñe procesos de aprendizaje paso a paso con bucles de retroalimentación

## 🛠️ Ejemplos del mundo real

Consulte el directorio [`examples/`](https://github.com/themanojdesai/python-a2a/tree/main/examples) para ejemplos del mundo real, incluyendo:

- Sistemas de soporte al cliente de múltiples agentes
- Asistentes de investigación impulsados por LLM con acceso a herramientas
- Implementaciones de transmisión en tiempo real
- Ejemplos de integración con LangChain
- Implementaciones de servidores MCP para diversas herramientas
- Ejemplos de orquestación de flujos de trabajo
- Administración de redes de agentes

## 🔄 Proyectos relacionados

Aquí hay algunos proyectos relacionados en el espacio de agentes de IA e interoperabilidad:

- [**Google A2A**](https://github.com/google/A2A) - La especificación oficial del protocolo A2A de Google
- [**LangChain**](https://github.com/langchain-ai/langchain) - Marco para construir aplicaciones con LLM
- [**AutoGen**](https://github.com/microsoft/autogen) - Marco de Microsoft para conversaciones de múltiples agentes
- [**CrewAI**](https://github.com/joaomdmoura/crewAI) - Marco para orquestar agentes de role-playing
- [**MCP**](https://github.com/contextco/mcp) - El Protocolo de Contexto del Modelo para agentes que usan herramientas

## 👥 Colaboradores

¡Gracias a todos nuestros colaboradores!

<a href="https://github.com/themanojdesai/python-a2a/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=themanojdesai/python-a2a" />
</a>

¿Quiere contribuir? Consulte nuestra [guía de contribución](https://python-a2a.readthedocs.io/en/latest/contributing.html).

## 🤝 Comunidad y soporte

- **[Problemas de GitHub](https://github.com/themanojdesai/python-a2a/issues)**: Informe errores o solicite características
- **[Discusiones de GitHub](https://github.com/themanojdesai/python-a2a/discussions)**: Haga preguntas y comparta ideas
- **[Guía de contribución](https://python-a2a.readthedocs.io/en/latest/contributing.html)**: Aprenda cómo contribuir al proyecto
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**: Visite nuestro sitio de documentación

## 📝 Citar este proyecto

Si usa Python A2A en sus trabajos de investigación o académicos, por favor cite como:

```
@software{desai2025pythona2a,
  author = {Desai, Manoj},
  title = {Python A2A: A Comprehensive Implementation of the Agent-to-Agent Protocol},
  url = {https://github.com/themanojdesai/python-a2a},
  version = {0.5.0},
  year = {2025},
}
```

## ⭐ Estrelle este repositorio

Si encuentra esta biblioteca útil, por favor considere darle una estrella en GitHub. ¡Ayuda a que otros la descubran y motiva el desarrollo futuro!

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

### Historial de estrellas

[![Star History Chart](https://api.star-history.com/svg?repos=themanojdesai/python-a2a&type=Date)](https://star-history.com/#themanojdesai/python-a2a&Date)

## 🙏 Agradecimientos

- Al equipo de [Google A2A](https://github.com/google/A2A) por crear el protocolo A2A
- Al equipo de [Contextual AI](https://contextual.ai/) por el Protocolo de Contexto del Modelo
- Al equipo de [LangChain](https://github.com/langchain-ai) por su marco de LLM potente
- A todos nuestros [colaboradores](https://github.com/themanojdesai/python-a2a/graphs/contributors) por sus valiosos comentarios

## 👨‍💻 Autor

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 Licencia

Este proyecto está bajo la licencia MIT - vea el archivo [LICENSE](LICENSE) para más detalles.

---

Creado con ❤️ por [Manoj Desai](https://github.com/themanojdesai)
