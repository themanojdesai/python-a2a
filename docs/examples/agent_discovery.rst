Agent Discovery Examples
======================

This section provides examples for using the agent discovery features in Python A2A.

Registry Server Example
----------------------

The following example shows how to create a registry server and agents that register with it:

.. code-block:: python

    from python_a2a import AgentCard, A2AServer, run_server, Message, TextContent, MessageRole
    from python_a2a.discovery import AgentRegistry, run_registry, enable_discovery
    import threading

    # Create a simple agent that will register with the registry
    class SampleAgent(A2AServer):
        """A sample agent that registers with the registry."""
        
        def __init__(self, name: str, description: str, url: str):
            """Initialize the sample agent."""
            agent_card = AgentCard(
                name=name,
                description=description,
                url=url,
                version="1.0.0",
                capabilities={
                    "streaming": False,
                    "pushNotifications": False,
                    "stateTransitionHistory": False,
                    "google_a2a_compatible": True,
                    "parts_array_format": True
                }
            )
            super().__init__(agent_card=agent_card)
        
        def handle_message(self, message: Message) -> Message:
            """Handle incoming messages."""
            return Message(
                content=TextContent(
                    text=f"Hello from {self.agent_card.name}! I received: {message.content.text}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

    # Start a registry server in a separate thread
    registry_port = 8000
    registry_thread = threading.Thread(
        target=lambda: run_registry(
            AgentRegistry(name="A2A Registry Server"),
            host="0.0.0.0", 
            port=registry_port
        ),
        daemon=True
    )
    registry_thread.start()

    # Create and run an agent that registers with the registry
    agent = SampleAgent(
        name="Sample Agent",
        description="Sample agent that demonstrates discovery",
        url="http://localhost:8001"
    )
    
    # Enable discovery - this registers the agent with the registry
    registry_url = f"http://localhost:{registry_port}"
    discovery_client = enable_discovery(agent, registry_url=registry_url)
    
    # Run the agent
    run_server(agent, host="0.0.0.0", port=8001)

Discovering Agents
-----------------

The following example shows how to discover agents from a registry:

.. code-block:: python

    from python_a2a.discovery import DiscoveryClient, AgentRegistry
    
    # Create a discovery client (without registering)
    discovery_client = DiscoveryClient(agent_card=None)  # You can also pass your own agent card
    discovery_client.add_registry("http://localhost:8000")
    
    # Discover all agents
    agents = discovery_client.discover()
    
    for agent in agents:
        print(f"Found agent: {agent.name} at {agent.url}")
        print(f"Capabilities: {agent.capabilities}")
        
    # You can also filter agents by capabilities
    weather_agents = [agent for agent in agents 
                     if agent.capabilities.get("weather_forecasting")]
    
    for agent in weather_agents:
        print(f"Found weather agent: {agent.name} at {agent.url}")

Running a Registry Server
-----------------------

To run a standalone registry server:

.. code-block:: python

    from python_a2a.discovery import AgentRegistry, run_registry
    
    # Create a registry
    registry = AgentRegistry(
        name="A2A Registry Server",
        description="Registry server for agent discovery"
    )
    
    # Run the registry server
    run_registry(registry, host="0.0.0.0", port=8000)

For more examples, see the ``examples/agent_network`` directory in the Python A2A package.