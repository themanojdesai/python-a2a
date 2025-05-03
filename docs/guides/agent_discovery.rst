Agent Discovery
==============

Agent discovery is a mechanism for agents to find each other and learn about their capabilities.
This guide explains how to use the agent discovery features in python-a2a.

Overview
--------

The A2A protocol supports agent discovery through standardized agent cards and registry servers.
The ``python_a2a.discovery`` module provides a complete implementation of this mechanism, allowing
agents to register with registries and discover other agents.

There are three primary components:

1. **AgentRegistry**: A server that maintains a registry of available agents
2. **DiscoveryClient**: A client for interacting with registry servers
3. **enable_discovery**: A function to add discovery capabilities to an existing A2A server

Key Concepts
-----------

**Agent Cards**

Agent cards are metadata structures that describe an agent's capabilities, including:

* Basic information (name, description, URL)
* Supported capabilities (streaming, push notifications, etc.)
* Skills the agent can perform
* Input and output modes it supports

In python-a2a, agent cards are represented by the ``AgentCard`` class in the ``models.agent`` module.

**Registry Servers**

Registry servers maintain a list of available agents and provide APIs for:

* Agent registration and unregistration
* Agent discovery and filtering
* Heartbeat mechanism to track agent availability

**Discovery Protocol**

The discovery protocol consists of these key endpoints:

* ``/registry/register`` - Register an agent with the registry
* ``/registry/unregister`` - Unregister an agent from the registry
* ``/registry/agents`` - Get a list of all registered agents
* ``/registry/heartbeat`` - Send a heartbeat to the registry
* ``/a2a/agents`` - Google A2A compatibility endpoint for agent discovery

Usage Examples
-------------

Running a Registry Server
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from python_a2a.discovery import AgentRegistry, run_registry
    
    # Create a registry server
    registry = AgentRegistry(name="My A2A Registry")
    
    # Run the registry server
    run_registry(registry, host="localhost", port=8000)

Enabling Discovery on an Existing Server
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from python_a2a import A2AServer, AgentCard
    from python_a2a.discovery import enable_discovery
    
    # Create an A2A server
    agent_card = AgentCard(
        name="My Agent",
        description="An agent with discovery capabilities",
        url="http://localhost:5000",
        version="1.0.0"
    )
    server = A2AServer(agent_card=agent_card)
    
    # Enable discovery and register with a registry
    enable_discovery(server, registry_url="http://localhost:8000")
    
    # Run the server
    from python_a2a import run_server
    run_server(server, host="localhost", port=5000)

Using the Discovery Client Directly
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from python_a2a.discovery import DiscoveryClient
    from python_a2a import AgentCard
    
    # Create an agent card
    agent_card = AgentCard(
        name="My Agent",
        description="An agent that discovers other agents",
        url="http://localhost:5000",
        version="1.0.0"
    )
    
    # Create a discovery client
    client = DiscoveryClient(agent_card)
    client.add_registry("http://localhost:8000")
    
    # Register with the registry
    client.register()
    
    # Start sending heartbeats
    client.start_heartbeat(interval=60)
    
    # Discover other agents
    agents = client.discover()
    for agent in agents:
        print(f"Found agent: {agent.name} at {agent.url}")
    
    # When done, unregister and stop heartbeats
    client.unregister()
    client.stop_heartbeat()

Creating a Combined Agent and Registry
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from python_a2a import AgentCard, run_server
    from python_a2a.discovery import RegistryAgent
    
    # Create a combined agent and registry
    agent_card = AgentCard(
        name="Agent Registry",
        description="Combined agent and registry",
        url="http://localhost:8000",
        version="1.0.0"
    )
    registry_agent = RegistryAgent(agent_card=agent_card)
    
    # Run the server
    run_server(registry_agent, host="localhost", port=8000)

Google A2A Demo Integration
---------------------------

The discovery module is compatible with the Google A2A demo UI. To connect your agents
to the Google A2A demo:

1. Enable discovery on your agent:

.. code-block:: python

    enable_discovery(server, registry_url="https://a2a-demo-registry.example.com")

2. The Google A2A demo will discover your agent through the registry.

3. Your agent will be available for use in the Google A2A demo UI.

API Reference
------------

AgentRegistry
~~~~~~~~~~~~

.. code-block:: python

    class AgentRegistry(BaseA2AServer):
        """Agent registry for A2A agent discovery."""
        
        def __init__(self, name: str = "A2A Agent Registry", description: str = None):
            """Initialize the agent registry."""
            
        def register_agent(self, agent_card: AgentCard) -> bool:
            """Register an agent with the registry."""
            
        def unregister_agent(self, agent_url: str) -> bool:
            """Unregister an agent from the registry."""
            
        def get_all_agents(self) -> List[AgentCard]:
            """Get all registered agents."""
            
        def get_agent(self, agent_url: str) -> Optional[AgentCard]:
            """Get a specific agent by URL."""
            
        def prune_inactive_agents(self, max_age: int = 300) -> int:
            """Remove agents that haven't been seen recently."""
            
        def run(self, host: str = "0.0.0.0", port: int = 8000, 
                prune_interval: int = 60, max_age: int = 300,
                debug: bool = False) -> None:
            """Run the registry server."""

DiscoveryClient
~~~~~~~~~~~~~~

.. code-block:: python

    class DiscoveryClient:
        """Client for interacting with agent registries."""
        
        def __init__(self, agent_card: AgentCard):
            """Initialize the discovery client."""
            
        def add_registry(self, registry_url: str) -> None:
            """Add a registry server to the client."""
            
        def remove_registry(self, registry_url: str) -> bool:
            """Remove a registry server from the client."""
            
        def register(self) -> List[Dict[str, Any]]:
            """Register with all known registries."""
            
        def unregister(self) -> List[Dict[str, Any]]:
            """Unregister from all known registries."""
            
        def heartbeat(self) -> List[Dict[str, Any]]:
            """Send heartbeat to all known registries."""
            
        def discover(self, registry_url: Optional[str] = None) -> List[AgentCard]:
            """Discover agents from registries."""
            
        def start_heartbeat(self, interval: int = 60) -> None:
            """Start a background thread to send periodic heartbeats."""
            
        def stop_heartbeat(self) -> None:
            """Stop the heartbeat thread if it's running."""

Functions
~~~~~~~~

.. code-block:: python

    def run_registry(registry: Optional[AgentRegistry] = None, 
                   host: str = "0.0.0.0", port: int = 8000,
                   prune_interval: int = 60, max_age: int = 300,
                   debug: bool = False) -> None:
        """Run a registry server."""
        
    def enable_discovery(server: BaseA2AServer, registry_url: Optional[str] = None,
                       heartbeat_interval: int = 60) -> DiscoveryClient:
        """Enable agent discovery on an existing A2A server."""