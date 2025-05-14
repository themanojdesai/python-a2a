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

**Implémentation officielle Python du protocole Google Agent-to-Agent (A2A), avec intégration du Model Context Protocol (MCP)**

</div>

## 🌟 Aperçu

Python A2A est une bibliothèque complète et prête pour la production pour implémenter le [protocole Agent-to-Agent (A2A) de Google](https://google.github.io/A2A/), avec un support complet pour le [Model Context Protocol (MCP)](https://contextual.ai/introducing-mcp/). Elle fournit toutes les fonctionnalités nécessaires pour construire un écosystème d'agents d'IA interoperables capables de collaborer en douceur pour résoudre des problèmes complexes.

Le protocole A2A établit un format de communication standard permettant aux agents d'IA d'interagir, tandis que le MCP étend cette capacité en fournissant une méthode standardisée pour que les agents accèdent à des outils et des sources de données externes. Python A2A rend ces protocoles faciles à utiliser via une API intuitive, permettant aux développeurs de construire des systèmes d'agents d'IA complexes.

## 📋 Nouveautés de la version v0.5.X

- **Découverte d'agents**: Support intégré pour le registre et la découverte d'agents avec une compatibilité totale avec le protocole A2A de Google
- **Intégration LangChain**: Intégration fluide avec les outils et agents de LangChain
- **Écosystème d'outils étendu**: Utilisez des outils provenant à la fois de LangChain et de MCP dans n'importe quel agent
- **Interopérabilité accrue des agents**: Conversion entre agents A2A et agents LangChain
- **Moteur de workflow hybride**: Création de workflows combinant les deux écosystèmes
- **Développement simplifié des agents**: Accès immédiat à des milliers d'outils prédéfinis
- **Architecture de streaming avancée**: Streaming amélioré avec les événements envoyés par le serveur (SSE), un meilleur gestion des erreurs et des mécanismes de secours robustes
- **Streaming basé sur les tâches**: Nouvelle méthode `tasks_send_subscribe` pour le streaming des mises à jour de tâches en temps réel
- **API de gestion des blocs de streaming**: Amélioration de la gestion des blocs avec la classe `StreamingChunk` pour des données structurées
- **Support multi-point de terminaison**: Découverte automatique et mécanismes de secours entre plusieurs points de terminaison de streaming

## 📋 Nouveautés de la version v0.4.X

- **Système de réseau d'agents**: Gestion et découverte de multiples agents avec la nouvelle classe `AgentNetwork`
- **Streaming en temps réel**: Implémentation de réponses en streaming avec `StreamingClient` pour des interfaces utilisateur réactives
- **Moteur de workflow**: Définition de workflows complexes de multiples agents à l'aide de l'API fluide avec des branchements conditionnels et une exécution parallèle
- **Routeur d'IA**: Routage automatique des requêtes vers l'agent le plus approprié avec `AIAgentRouter`
- **Interface en ligne de commande**: Contrôle des agents depuis le terminal avec l'outil CLI
- **Support asynchrone amélioré**: Meilleure prise en charge de async/await à travers toute la bibliothèque
- **Nouvelles options de connexion**: Gestion améliorée des erreurs et logique de réessai pour une communication d'agents plus robuste

## ✨ Pourquoi choisir Python A2A ?

- **Implémentation complète**: Implémente intégralement la spécification A2A officielle sans compromis
- **Découverte d'agents**: Registre et découverte d'agents intégrés pour la création d'écosystèmes d'agents
- **Intégration MCP**: Support de premier plan pour le Model Context Protocol pour des agents utilisant des outils puissants
- **Prêt pour l'entreprise**: Conçu pour les environnements de production avec une gestion robuste des erreurs et une validation rigoureuse
- **Indépendant du framework**: Fonctionne avec n'importe quel framework Python (Flask, FastAPI, Django, etc.)
- **Flexibilité du fournisseur LLM**: Intégrations natives avec OpenAI, Anthropic, AWS Bedrock, et plus encore
- **Dépendances minimales**: La fonctionnalité de base nécessite uniquement la bibliothèque `requests`
- **Expérience développeur exceptionnelle**: Documentation complète, indices de type et exemples

## 📦 Installation

### Avec pip (méthode traditionnelle)

Installez le paquet de base avec toutes les dépendances:

```bash
pip install python-a2a  # Inclut LangChain, MCP et d'autres intégrations
```

Ou installez des composants spécifiques selon vos besoins:

```bash
# Pour le support du serveur basé sur Flask
pip install "python-a2a[server]"

# Pour l'intégration OpenAI
pip install "python-a2a[openai]"

# Pour l'intégration Anthropic Claude
pip install "python-a2a[anthropic]"

# Pour l'intégration AWS-Bedrock
pip install "python-a2a[bedrock]"

# Pour le support MCP (Model Context Protocol)
pip install "python-a2a[mcp]"

# Pour toutes les dépendances optionnelles
pip install "python-a2a[all]"
```

### Avec UV (recommandé)

[UV](https://github.com/astral-sh/uv) est un outil moderne de gestion de paquets Python plus rapide et plus fiable que pip. Pour installer avec UV:

```bash
# Installez UV si ce n'est pas déjà fait
curl -LsSf https://astral.sh/uv/install.sh | sh

# Installez le paquet de base
uv add python-a2a
```

### Installation pour le développement

Pour le développement, UV est recommandé pour sa vitesse:

```bash
# Clonez le dépôt
git clone https://github.com/themanojdesai/python-a2a.git
cd python-a2a

# Créez un environnement virtuel et installez les dépendances de développement
uv venv
source .venv/bin/activate  # Sous Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
```

> 💡 **Astuce**: Cliquez sur les blocs de code pour les copier dans votre presse-papiers.

## 🚀 Exemples d'utilisation rapides

### 1. Créer un agent A2A simple avec des compétences

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
        # Implémentation fictive
        return f"It's sunny and 75°F in {location}"
    
    def handle_task(self, task):
        # Extraire l'emplacement à partir du message
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        if "weather" in text.lower() and "in" in text.lower():
            location = text.split("in", 1)[1].strip().rstrip("?.")
            
            # Obtenir la météo et créer une réponse
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

# Démarrer le serveur
if __name__ == "__main__":
    agent = WeatherAgent()
    run_server(agent, port=5000)
```

### 2. Construire un réseau d'agents avec plusieurs agents

```python
from python_a2a import AgentNetwork, A2AClient, AIAgentRouter

# Créer un réseau d'agents
network = AgentNetwork(name="Travel Assistant Network")

# Ajouter des agents au réseau
network.add("weather", "http://localhost:5001")
network.add("hotels", "http://localhost:5002")
network.add("attractions", "http://localhost:5003")

# Créer un routeur pour diriger intelligemment les requêtes vers l'agent le plus approprié
router = AIAgentRouter(
    llm_client=A2AClient("http://localhost:5000/openai"),  # LLM pour les décisions de routage
    agent_network=network
)

# Router une requête vers l'agent approprié
agent_name, confidence = router.route_query("What's the weather like in Paris?")
print(f"Routage vers {agent_name} avec {confidence:.2f} de confiance")

# Obtenir l'agent sélectionné et poser la question
agent = network.get_agent(agent_name)
response = agent.ask("What's the weather like in Paris?")
print(f"Réponse: {response}")

# Lister tous les agents disponibles
print("\nAgents disponibles:")
for agent_info in network.list_agents():
    print(f"- {agent_info['name']}: {agent_info['description']}")
```

### Streaming en temps réel

Obtenir des réponses en temps réel des agents avec un support de streaming complet:

```python
import asyncio
from python_a2a import StreamingClient, Message, TextContent, MessageRole

async def main():
    client = StreamingClient("http://localhost:5000")
    
    # Créer un message avec le paramètre role requis
    message = Message(
        content=TextContent(text="Tell me about A2A streaming"),
        role=MessageRole.USER
    )
    
    # Streamer la réponse et traiter les blocs en temps réel
    try:
        async for chunk in client.stream_response(message):
            # Gérer différents formats de blocs (chaîne ou dictionnaire)
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
        print(f"Erreur de streaming: {e}")
```

Consultez le répertoire `examples/streaming/` pour des exemples complets de streaming:

- **basic_streaming.py**: Implémentation minimale de streaming (commencez ici!)
- **01_basic_streaming.py**: Introduction complète aux bases du streaming
- **02_advanced_streaming.py**: Streaming avancé avec différentes stratégies de blocage
- **03_streaming_llm_integration.py**: Intégration du streaming avec les fournisseurs LLM
- **04_task_based_streaming.py**: Streaming basé sur les tâches avec suivi de progression
- **05_streaming_ui_integration.py**: Intégration du streaming avec les interfaces utilisateur (CLI et web)
- **06_distributed_streaming.py**: Architecture de streaming distribué

### 3. Moteur de workflow

Le nouveau moteur de workflow permet de définir des interactions complexes entre agents:

```python
from python_a2a import AgentNetwork, Flow
import asyncio

async def main():
    # Configurer le réseau d'agents
    network = AgentNetwork()
    network.add("research", "http://localhost:5001")
    network.add("summarizer", "http://localhost:5002")
    network.add("factchecker", "http://localhost:5003")
    
    # Définir un workflow pour la génération de rapports de recherche
    flow = Flow(agent_network=network, name="Research Report Workflow")
    
    # D'abord, collecter la recherche initiale
    flow.ask("research", "Research the latest developments in {topic}")
    
    # Ensuite, traiter les résultats en parallèle
    parallel_results = (flow.parallel()
        # Branche 1: Créer un résumé
        .ask("summarizer", "Summarize this research: {latest_result}")
        # Branche 2: Vérifier les faits clés
        .branch()
        .ask("factchecker", "Verify these key facts: {latest_result}")
        # Fin du traitement parallèle et collecte des résultats
        .end_parallel(max_concurrency=2))
    
    # Extraire des insights basés sur les résultats de vérification
    flow.execute_function(
        lambda results, context: f"Summary: {results['1']}\nVerified Facts: {results['2']}",
        parallel_results
    )
    
    # Exécuter le workflow
    result = await flow.run({
        "topic": "quantum computing advancements in the last year"
    })
    
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 4. Routeur d'IA

Routage intelligent pour sélectionner l'agent le plus approprié pour chaque requête:

```python
from python_a2a import AgentNetwork, AIAgentRouter, A2AClient
import asyncio

async def main():
    # Créer un réseau avec des agents spécialisés
    network = AgentNetwork()
    network.add("math", "http://localhost:5001")
    network.add("history", "http://localhost:5002")
    network.add("science", "http://localhost:5003")
    network.add("literature", "http://localhost:5004")
    
    # Créer un routeur utilisant un LLM pour la prise de décision
    router = AIAgentRouter(
        llm_client=A2AClient("http://localhost:5000/openai"),
        agent_network=network
    )
    
    # Exemples de requêtes à router
    queries = [
        "What is the formula for the area of a circle?",
        "Who wrote The Great Gatsby?",
        "When did World War II end?",
        "How does photosynthesis work?",
        "What are Newton's laws of motion?"
    ]
    
    # Router chaque requête vers l'agent le plus approprié
    for query in queries:
        agent_name, confidence = router.route_query(query)
        agent = network.get_agent(agent_name)
        
        print(f"Requête: {query}")
        print(f"Routée vers: {agent_name} (confiance: {confidence:.2f})")
        
        # Obtenir la réponse de l'agent sélectionné
        response = agent.ask(query)
        print(f"Réponse: {response[:100]}...\n")

if __name__ == "__main__":
    asyncio.run(main())
```

### 5. Définir des workflows complexes avec plusieurs agents

```python
from python_a2a import AgentNetwork, Flow, AIAgentRouter
import asyncio

async def main():
    # Créer un réseau d'agents
    network = AgentNetwork()
    network.add("weather", "http://localhost:5001")
    network.add("recommendations", "http://localhost:5002")
    network.add("booking", "http://localhost:5003")
    
    # Créer un routeur
    router = AIAgentRouter(
        llm_client=network.get_agent("weather"),  # Utiliser un agent comme LLM pour le routage
        agent_network=network
    )
    
    # Définir un workflow avec de la logique conditionnelle
    flow = Flow(agent_network=network, router=router, name="Travel Planning Workflow")
    
    # Commencer par obtenir la météo
    flow.ask("weather", "What's the weather in {destination}?")
    
    # Branche conditionnelle basée sur la météo
    flow.if_contains("sunny")
    
    # Si ensoleillé, recommander des activités en plein air
    flow.ask("recommendations", "Recommend outdoor activities in {destination}")
    
    # Fin de la condition et ajout d'une branche else
    flow.else_branch()
    
    # Si non ensoleillé, recommander des activités en intérieur
    flow.ask("recommendations", "Recommend indoor activities in {destination}")
    
    # Fin du bloc if-else
    flow.end_if()
    
    # Ajouter des étapes de traitement parallèle
    (flow.parallel()
        .ask("booking", "Find hotels in {destination}")
        .branch()
        .ask("booking", "Find restaurants in {destination}")
        .end_parallel())
    
    # Exécuter le workflow avec un contexte initial
    result = await flow.run({
        "destination": "Paris",
        "travel_dates": "June 12-20"
    })
    
    print("Résultat du workflow:")
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. Utiliser l'interface en ligne de commande

```bash
# Envoyer un message à un agent
a2a send http://localhost:5000 "What is artificial intelligence?"

# Streamer une réponse en temps réel
a2a stream http://localhost:5000 "Generate a step-by-step tutorial for making pasta"

# Démarrer un serveur A2A alimenté par OpenAI
a2a openai --model gpt-4 --system-prompt "You are a helpful coding assistant"

# Démarrer un serveur A2A alimenté par Anthropic
a2a anthropic --model claude-3-opus-20240229 --system-prompt "You are a friendly AI teacher"

# Démarrer un serveur MCP avec des outils
a2a mcp-serve --name "Data Analysis MCP" --port 5001 --script analysis_tools.py

# Démarrer un agent A2A avec MCP
a2a mcp-agent --servers data=http://localhost:5001 calc=http://localhost:5002

# Appeler un outil MCP directement
a2a mcp-call http://localhost:5001 analyze_csv --params file=data.csv columns=price,date

# Gérer les réseaux d'agents
a2a network --add weather=http://localhost:5001 travel=http://localhost:5002 --save network.json

# Exécuter un workflow à partir d'un script
a2a workflow --script research_workflow.py --context initial_data.json
```

## 🔄 Intégration LangChain (Nouveau dans v0.5.X)

Python A2A inclut une intégration LangChain intégrée, facilitant la combinaison des meilleures fonctionnalités des deux écosystèmes:

### 1. Conversion des outils MCP vers LangChain

```python
from python_a2a.mcp import FastMCP, text_response
from python_a2a.langchain import to_langchain_tool

# Créer un serveur MCP avec un outil
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

# Démarrer le serveur
import threading, time
def run_server(server, port):
    server.run(host="0.0.0.0", port=port)
server_thread = threading.Thread(target=run_server, args=(mcp_server, 5000), daemon=True)
server_thread.start()
time.sleep(2)  # Permettre au serveur de démarrer

# Convertir l'outil MCP vers LangChain
calculator_tool = to_langchain_tool("http://localhost:5000", "calculator")

# Utiliser l'outil dans LangChain
result = calculator_tool.run("5 * 9 + 3")
print(f"Résultat: {result}")
```

### 2. Conversion des outils LangChain vers un serveur MCP

```python
from langchain.tools import Tool
from langchain_core.tools import BaseTool
from python_a2a.langchain import to_mcp_server

# Créer des outils LangChain
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

# Convertir vers un serveur MCP
mcp_server = to_mcp_server(calculator_tool)

# Démarrer le serveur
mcp_server.run(port=5000)
```

### 3. Conversion des composants LangChain vers des serveurs A2A

```python
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
from python_a2a import A2AClient, run_server
from python_a2a.langchain import to_a2a_server

# Créer un LLM LangChain
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# Convertir le LLM vers un serveur A2A
llm_server = to_a2a_server(llm)

# Créer une chaîne simple
template = "You are a helpful travel guide.\n\nQuestion: {query}\n\nAnswer:"
prompt = PromptTemplate.from_template(template)
travel_chain = prompt | llm | StrOutputParser()

# Convertir la chaîne vers un serveur A2A
travel_server = to_a2a_server(travel_chain)

# Démarrer les serveurs dans des threads d'arrière-plan
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

# Tester les serveurs
llm_client = A2AClient("http://localhost:5001")
travel_client = A2AClient("http://localhost:5002")

llm_result = llm_client.ask("What is the capital of France?")
travel_result = travel_client.ask('{"query": "What are some must-see attractions in Paris?"}')
```

### 4. Conversion des agents A2A vers des agents LangChain

```python
from python_a2a.langchain import to_langchain_agent

# Convertir un agent A2A vers un agent LangChain
langchain_agent = to_langchain_agent("http://localhost:5000")

# Utiliser l'agent dans LangChain
result = langchain_agent.invoke("What are some famous landmarks in Paris?")
print(result.get('output', ''))

# Utiliser dans un pipeline LangChain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

llm = ChatOpenAI(temperature=0)
prompt = ChatPromptTemplate.from_template(
    "Generate a specific, detailed travel question about {destination}."
)

# Créer un pipeline avec l'agent converti
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

LangChain est automatiquement installé en tant que dépendance avec python-a2a, donc tout fonctionne immédiatement:

```bash
pip install python-a2a
# C'est tout! LangChain est inclus automatiquement
```

## 🧩 Fonctionnalités clés

### Réseaux d'agents

Python A2A inclut maintenant un système puissant pour gérer plusieurs agents:

```python
from python_a2a import AgentNetwork, A2AClient

# Créer un réseau d'agents
network = AgentNetwork(name="Medical Assistant Network")

# Ajouter des agents de différentes manières
network.add("diagnosis", "http://localhost:5001")  # À partir d'une URL
network.add("medications", A2AClient("http://localhost:5002"))  # À partir d'une instance client

# Découvrir des agents à partir d'une liste d'URLs
discovered_count = network.discover_agents([
    "http://localhost:5003",
    "http://localhost:5004",
    "http://localhost:5005"
])
print(f"{discovered_count} nouveaux agents découverts")

# Lister tous les agents dans le réseau
for agent_info in network.list_agents():
    print(f"Agent: {agent_info['name']}")
    print(f"URL: {agent_info['url']}")
    if 'description' in agent_info:
        print(f"Description: {agent_info['description']}")
    print()

# Obtenir un agent spécifique
agent = network.get_agent("diagnosis")
response = agent.ask("What are the symptoms of the flu?")
```

### 7. Découverte et registre d'agents

```python
from python_a2a import AgentCard, A2AServer, run_server
from python_a2a.discovery import AgentRegistry, run_registry, enable_discovery, DiscoveryClient
import threading
import time

# Créer un serveur de registre
registry = AgentRegistry(
    name="A2A Registry Server",
    description="Registre central pour la découverte d'agents"
)

# Démarrer le registre dans un thread d'arrière-plan
registry_port = 8000
thread = threading.Thread(
    target=lambda: run_registry(registry, host="0.0.0.0", port=registry_port),
    daemon=True
)
thread.start()
time.sleep(1)  # Permettre au registre de démarrer

# Créer un agent d'exemple
agent_card = AgentCard(
    name="Weather Agent",
    description="Provides weather information",
    url="http://localhost:8001",
    version="1.0.0",
    capabilities={
        "weather_forecasting": True,
        "google_a2a_compatible": True  # Activer la compatibilité A2A de Google
    }
)
agent = A2AServer(agent_card=agent_card)

# Activer la découverte - cela enregistre l'agent dans le registre
registry_url = f"http://localhost:{registry_port}"
discovery_client = enable_discovery(agent, registry_url=registry_url)

# Démarrer l'agent dans un thread séparé
agent_thread = threading.Thread(
    target=lambda: run_server(agent, host="0.0.0.0", port=8001),
    daemon=True
)
agent_thread.start()
time.sleep(1)  # Permettre à l'agent de démarrer

# Créer un client de découverte pour trouver des agents
client = DiscoveryClient(agent_card=None)  # Aucune carte d'agent nécessaire pour la découverte seule
client.add_registry(registry_url)

# Découvrir tous les agents
agents = client.discover()
print(f"{len(agents)} agents découverts:")
for agent in agents:
    print(f"- {agent.name} à {agent.url}")
    print(f"  Capacités: {agent.capabilities}")
```

## 📖 Architecture et principes de conception

Python A2A est construit sur trois principes de conception clés:

1. **Protocole en premier**: Respect strict des spécifications des protocoles A2A et MCP pour une interopérabilité maximale

2. **Modularité**: Tous les composants sont conçus pour être composable et remplaçable

3. **Amélioration progressive**: Commencer simple et ajouter de la complexité uniquement si nécessaire

L'architecture se compose de huit composants principaux:

- **Modèles**: Structures de données représentant les messages A2A, les tâches et les cartes d'agents
- **Client**: Composants pour envoyer des messages aux agents A2A et gérer les réseaux d'agents
- **Serveur**: Composants pour construire des agents compatibles A2A
- **Découverte**: Mécanismes de registre et de découverte pour les écosystèmes d'agents
- **MCP**: Outils pour implémenter des serveurs et clients du Model Context Protocol
- **LangChain**: Composants pont pour l'intégration LangChain
- **Workflow**: Moteur pour orchestrer des interactions complexes entre agents
- **Utils**: Fonctions d'aide pour les tâches courantes
- **CLI**: Interface en ligne de commande pour interagir avec les agents

## 🗺️ Cas d'utilisation

Python A2A peut être utilisé pour construire une vaste gamme de systèmes d'IA:

### Recherche et développement

- **Cadre d'expérimentation**: Échange facile entre différents backends LLM tout en maintenant la même interface d'agent
- **Benchmarks**: Comparer les performances des différentes implémentations d'agents sur des tâches standardisées
- **Assistants de recherche en streaming**: Créer des outils de recherche réactifs avec une sortie en temps réel via le streaming

### Systèmes d'entreprise

- **Orchestration d'IA**: Coordonner plusieurs agents d'IA entre différents départements via des réseaux d'agents
- **Intégration de systèmes hérités**: Emballer les systèmes hérités avec des interfaces A2A pour une accessibilité à l'IA
- **Workflows complexes**: Créer des processus métier sophistiqués avec des workflows multi-agents et des branchements conditionnels

### Applications orientées client

- **Assistants multi-étapes**: Découper les requêtes complexes des utilisateurs en sous-tâches gérées par des agents spécialisés
- **Agents utilisant des outils**: Connecter des LLM à des agents de base de données, des agents de calcul, etc. via le MCP
- **Interfaces de chat en temps réel**: Construire des applications de chat réactives avec un support de réponse en streaming

### Éducation et formation

- **Éducation en IA**: Créer des systèmes éducatifs démontrant la collaboration entre agents
- **Environnements de simulation**: Construire des environnements simulés où plusieurs agents interagissent
- **Workflows éducatifs**: Concevoir des processus d'apprentissage étape par étape avec des boucles de feedback

## 🛠️ Exemples concrets

Consultez le répertoire [`examples/`](https://github.com/themanojdesai/python-a2a/tree/main/examples) pour des exemples concrets, y compris:

- Systèmes de support client multi-agents
- Assistants de recherche alimentés par LLM avec accès aux outils
- Implémentations de streaming en temps réel
- Exemples d'intégration LangChain
- Implémentations de serveurs MCP pour divers outils
- Exemples d'orchestration de workflows
- Gestion de réseaux d'agents

## 🔄 Projets liés

Voici quelques projets liés dans l'espace des agents d'IA et de l'interopérabilité:

- [**Google A2A**](https://github.com/google/A2A) - La spécification officielle du protocole A2A de Google
- [**LangChain**](https://github.com/langchain-ai/langchain) - Framework pour construire des applications avec des LLM
- [**AutoGen**](https://github.com/microsoft/autogen) - Framework de Microsoft pour les conversations multi-agents
- [**CrewAI**](https://github.com/joaomdmoura/crewAI) - Framework pour orchestrer des agents de rôle
- [**MCP**](https://github.com/contextco/mcp) - Le Model Context Protocol pour les agents utilisant des outils

## 👥 Contributeurs

Merci à tous nos contributeurs!

<a href="https://github.com/themanojdesai/python-a2a/graphs/contributors">
  <img src="https://contrib.rocks/image?repo=themanojdesai/python-a2a" />
</a>

Souhaitez-vous contribuer? Consultez notre [guide de contribution](https://python-a2a.readthedocs.io/en/latest/contributing.html).

## 🤝 Communauté et support

- **[GitHub Issues](https://github.com/themanojdesai/python-a2a/issues)**: Signaler des bugs ou demander des fonctionnalités
- **[GitHub Discussions](https://github.com/themanojdesai/python-a2a/discussions)**: Poser des questions et partager des idées
- **[Guide de contribution](https://python-a2a.readthedocs.io/en/latest/contributing.html)**: Apprendre comment contribuer au projet
- **[ReadTheDocs](https://python-a2a.readthedocs.io/en/latest/)**: Visitez notre site de documentation

## 📝 Citer ce projet

Si vous utilisez Python A2A dans vos travaux de recherche ou académiques, veuillez le citer comme suit:

```
@software{desai2025pythona2a,
  author = {Desai, Manoj},
  title = {Python A2A: A Comprehensive Implementation of the Agent-to-Agent Protocol},
  url = {https://github.com/themanojdesai/python-a2a},
  version = {0.5.0},
  year = {2025},
}
```

## ⭐ Étoilez ce dépôt

Si vous trouvez cette bibliothèque utile, n'hésitez pas à lui donner une étoile sur GitHub! Cela aide les autres à la découvrir et motive le développement ultérieur.

[![GitHub Repo stars](https://img.shields.io/github/stars/themanojdesai/python-a2a?style=social)](https://github.com/themanojdesai/python-a2a/stargazers)

### Historique des étoiles

[![Star History Chart](https://api.star-history.com/svg?repos=themanojdesai/python-a2a&type=Date)](https://star-history.com/#themanojdesai/python-a2a&Date)

## 🙏 Remerciements

- À l'équipe [Google A2A](https://github.com/google/A2A) pour avoir créé le protocole A2A
- À l'équipe [Contextual AI](https://contextual.ai/) pour le Model Context Protocol
- À l'équipe [LangChain](https://github.com/langchain-ai) pour leur framework puissant de LLM
- À tous nos [contributeurs](https://github.com/themanojdesai/python-a2a/graphs/contributors) pour leurs précieux commentaires

## 👨‍💻 Auteur

**Manoj Desai**

- GitHub: [themanojdesai](https://github.com/themanojdesai)
- LinkedIn: [themanojdesai](https://www.linkedin.com/in/themanojdesai/)
- Medium: [@the_manoj_desai](https://medium.com/@the_manoj_desai)

## 📄 Licence

Ce projet est sous licence MIT - voir le fichier [LICENSE](LICENSE) pour plus de détails.

---

Créé avec ❤️ par [Manoj Desai](https://github.com/themanojdesai)
