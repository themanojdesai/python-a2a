#!/usr/bin/env python
"""
Agent Registry Example

This example demonstrates how to create and run an A2A agent registry server
that enables agent discovery. It shows:

- How to create a registry server
- How to enable discovery on existing agents
- How to discover agents through a registry

To run:
    python agent_registry.py

This will start a registry server and a sample agent that registers with it.
"""

import sys
import time
import threading
import argparse
import socket
from typing import Optional

from python_a2a import AgentCard, A2AServer, run_server, Message, TextContent, MessageRole
from python_a2a.discovery import AgentRegistry, run_registry, enable_discovery

# Find an available port
def find_free_port() -> int:
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


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


def start_registry(port: int, ready_event: Optional[threading.Event] = None) -> None:
    """Start a registry server."""
    print(f"Starting registry server on port {port}...")
    
    # Create registry
    registry = AgentRegistry(
        name="A2A Registry Server",
        description="Registry server for agent discovery"
    )
    
    # Signal that the registry is ready to start
    if ready_event:
        ready_event.set()
    
    # Run registry
    run_registry(registry, host="0.0.0.0", port=port, debug=False)


def start_sample_agent(name: str, port: int, registry_port: int, 
                       ready_event: Optional[threading.Event] = None) -> None:
    """Start a sample agent that registers with the registry."""
    print(f"Starting agent {name} on port {port}...")
    
    # Create agent
    agent = SampleAgent(
        name=name,
        description=f"Sample agent that demonstrates discovery",
        url=f"http://localhost:{port}"
    )
    
    # Enable discovery
    registry_url = f"http://localhost:{registry_port}"
    discovery_client = enable_discovery(agent, registry_url=registry_url)
    
    # Signal that the agent is ready to start
    if ready_event:
        ready_event.set()
    
    # Run agent
    run_server(agent, host="0.0.0.0", port=port)


def list_agents(registry_port: int) -> None:
    """List all registered agents."""
    import requests
    import json
    
    try:
        # Get agents from registry
        url = f"http://localhost:{registry_port}/registry/agents"
        response = requests.get(url, timeout=5.0)
        
        if response.status_code == 200:
            agents = response.json()
            
            if not agents:
                print("No agents registered.")
                return
            
            print("\nRegistered Agents:")
            print("-----------------")
            
            for i, agent in enumerate(agents, start=1):
                print(f"{i}. {agent.get('name')} ({agent.get('url')})")
                print(f"   Description: {agent.get('description')}")
                print(f"   Version: {agent.get('version')}")
                
                # Print capabilities
                capabilities = agent.get('capabilities', {})
                enabled_capabilities = [k for k, v in capabilities.items() if v]
                if enabled_capabilities:
                    print(f"   Capabilities: {', '.join(enabled_capabilities)}")
                
                # Print skills
                skills = agent.get('skills', [])
                if skills:
                    print(f"   Skills: {len(skills)}")
                    for j, skill in enumerate(skills, start=1):
                        print(f"     {j}. {skill.get('name')}: {skill.get('description')}")
                
                print()
                
        else:
            print(f"Error listing agents: {response.status_code}")
            
    except Exception as e:
        print(f"Error listing agents: {e}")


def main():
    """Run the example."""
    parser = argparse.ArgumentParser(description="Agent Registry Example")
    parser.add_argument("--registry-port", type=int, default=None,
                       help="Port for the registry server")
    parser.add_argument("--agent1-port", type=int, default=None,
                       help="Port for the first agent")
    parser.add_argument("--agent2-port", type=int, default=None,
                       help="Port for the second agent")
    parser.add_argument("--agents", type=int, default=2,
                       help="Number of sample agents to create")
    
    args = parser.parse_args()
    
    # Use provided ports or find free ones
    registry_port = args.registry_port or find_free_port()
    agent_ports = []
    
    if args.agent1_port:
        agent_ports.append(args.agent1_port)
    if args.agent2_port and args.agents >= 2:
        agent_ports.append(args.agent2_port)
    
    # Find free ports for the remaining agents
    while len(agent_ports) < args.agents:
        agent_ports.append(find_free_port())
    
    # Start the registry in a separate thread
    registry_ready = threading.Event()
    registry_thread = threading.Thread(
        target=start_registry,
        args=(registry_port, registry_ready),
        daemon=True
    )
    registry_thread.start()
    
    # Wait for registry to be ready
    registry_ready.wait(timeout=5.0)
    time.sleep(1)  # Give it a moment to start
    
    # Start agents in separate threads
    agent_threads = []
    agent_ready_events = []
    
    for i, port in enumerate(agent_ports, start=1):
        agent_ready = threading.Event()
        agent_ready_events.append(agent_ready)
        
        thread = threading.Thread(
            target=start_sample_agent,
            args=(f"Sample Agent {i}", port, registry_port, agent_ready),
            daemon=True
        )
        agent_threads.append(thread)
        thread.start()
    
    # Wait for all agents to be ready
    for event in agent_ready_events:
        event.wait(timeout=5.0)
    
    # Give agents time to register
    print("\nWaiting for agents to register...")
    time.sleep(2)
    
    # List registered agents
    list_agents(registry_port)
    
    print("\nRegistry and agents are running. Press Ctrl+C to stop.")
    print(f"Registry URL: http://localhost:{registry_port}")
    for i, port in enumerate(agent_ports, start=1):
        print(f"Agent {i} URL: http://localhost:{port}")
    
    # Keep running until interrupted
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping...")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())