"""
Agent Discovery Module for A2A Protocol

This module provides functionality for agent discovery and registry in the A2A protocol.
It allows agents to register themselves and discover other agents through a standard interface
compatible with the Google A2A demo.

Usage:
    from python_a2a.discovery import AgentRegistry, enable_discovery, DiscoveryClient
    
    # Option 1: Create a standalone registry server
    registry = AgentRegistry(name="My A2A Registry")
    registry.run(port=8000)
    
    # Option 2: Enable discovery on an existing server
    server = A2AServer(agent_card)
    enable_discovery(server, registry_url="http://localhost:8000")
"""

from .registry import AgentRegistry, run_registry
from .client import DiscoveryClient
from .server import enable_discovery, RegistryAgent

__all__ = [
    'AgentRegistry',
    'run_registry',
    'DiscoveryClient',
    'enable_discovery',
    'RegistryAgent'
]