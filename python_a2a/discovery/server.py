"""
A2A Discovery Server Components.

This module provides functionality for adding discovery capabilities
to existing A2A servers.
"""

import logging
import threading
from typing import Dict, List, Optional, Any, Union, Callable

from ..models.agent import AgentCard
from ..server.base import BaseA2AServer
from ..exceptions import A2AImportError
from .client import DiscoveryClient

# Configure logging
logger = logging.getLogger("python_a2a.discovery")


class RegistryAgent(BaseA2AServer):
    """
    A specialized A2A agent that also acts as a registry.
    
    This class combines the functionality of an A2A agent with
    registry capabilities, allowing it to serve both roles.
    """
    
    def __init__(self, agent_card: AgentCard):
        """
        Initialize the registry agent.
        
        Args:
            agent_card: Agent card for this agent
        """
        # Make sure the agent card has registry capabilities
        if not hasattr(agent_card, "capabilities"):
            agent_card.capabilities = {}
        
        agent_card.capabilities["agent_discovery"] = True
        agent_card.capabilities["registry"] = True
        agent_card.capabilities["google_a2a_compatible"] = True
        agent_card.capabilities["parts_array_format"] = True
        
        # Initialize registry state
        self.agents: Dict[str, AgentCard] = {}
        self.last_seen: Dict[str, float] = {}
        self._pruning_thread = None
        self._shutdown_event = threading.Event()
        
        # Call parent constructor
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message):
        """Handle incoming messages."""
        # In a real implementation, this would respond with registry information
        from ..models.message import Message, MessageRole
        from ..models.content import TextContent
        
        return Message(
            content=TextContent(
                text="This is a combined A2A agent and registry server."
            ),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id if hasattr(message, 'message_id') else None,
            conversation_id=message.conversation_id if hasattr(message, 'conversation_id') else None
        )
    
    def setup_routes(self, app) -> None:
        """
        Set up custom routes for this agent.
        
        This adds registry-related routes to the standard A2A agent.
        Implements the standardized BaseA2AServer interface.
        
        Args:
            app: Flask application to add routes to
        """
        # Call the parent class setup_routes first 
        super().setup_routes(app)
        # Add registry routes similar to AgentRegistry
        from flask import request, jsonify
        import time
        
        # Route for agent registration
        @app.route("/registry/register", methods=["POST"])
        def register():
            """Handle agent registration."""
            try:
                data = request.json
                agent_card = AgentCard.from_dict(data)
                
                # Register the agent
                if not agent_card.url:
                    return jsonify({"success": False, "error": "URL is required"}), 400
                
                agent_id = agent_card.url
                self.agents[agent_id] = agent_card
                self.last_seen[agent_id] = time.time()
                logger.info(f"Registered agent: {agent_card.name} at {agent_card.url}")
                
                return jsonify({"success": True})
            except Exception as e:
                logger.error(f"Error registering agent: {e}")
                return jsonify({"success": False, "error": str(e)}), 400
        
        # Route for agent unregistration
        @app.route("/registry/unregister", methods=["POST"])
        def unregister():
            """Handle agent unregistration."""
            try:
                data = request.json
                agent_url = data.get("url")
                if not agent_url:
                    return jsonify({"success": False, "error": "URL is required"}), 400
                
                if agent_url in self.agents:
                    agent_name = self.agents[agent_url].name
                    del self.agents[agent_url]
                    if agent_url in self.last_seen:
                        del self.last_seen[agent_url]
                    logger.info(f"Unregistered agent: {agent_name} at {agent_url}")
                    return jsonify({"success": True})
                
                return jsonify({"success": False, "error": "Agent not registered"}), 404
            except Exception as e:
                logger.error(f"Error unregistering agent: {e}")
                return jsonify({"success": False, "error": str(e)}), 400
        
        # Route for getting all agents
        @app.route("/registry/agents", methods=["GET"])
        def get_agents():
            """Get all registered agents."""
            return jsonify([agent.to_dict() for agent in self.agents.values()])
        
        # Route for getting agent details
        @app.route("/registry/agents/<path:agent_url>", methods=["GET"])
        def get_agent(agent_url):
            """Get a specific agent by URL."""
            agent = self.agents.get(agent_url)
            if agent:
                return jsonify(agent.to_dict())
            return jsonify({"error": "Agent not found"}), 404
        
        # Route for Google A2A demo compatibility
        @app.route("/a2a/agents", methods=["GET"])
        def get_a2a_agents():
            """Get all agents in Google A2A demo format."""
            return jsonify({
                "agents": [agent.to_dict() for agent in self.agents.values()]
            })
        
        # Agent heartbeat route
        @app.route("/registry/heartbeat", methods=["POST"])
        def heartbeat():
            """Handle agent heartbeat."""
            try:
                data = request.json
                agent_url = data.get("url")
                if not agent_url:
                    return jsonify({"success": False, "error": "URL is required"}), 400
                
                if agent_url in self.agents:
                    self.last_seen[agent_url] = time.time()
                    return jsonify({"success": True})
                
                return jsonify({"success": False, "error": "Agent not registered"}), 404
            except Exception as e:
                logger.error(f"Error processing heartbeat: {e}")
                return jsonify({"success": False, "error": str(e)}), 400


def enable_discovery(server: BaseA2AServer, registry_url: Optional[str] = None,
                   heartbeat_interval: int = 60) -> DiscoveryClient:
    """
    Enable agent discovery on an existing A2A server.
    
    This function adds discovery capabilities to an existing A2A server,
    allowing it to register with a registry server and be discovered by other agents.
    
    Args:
        server: A2A server to enable discovery on
        registry_url: URL of the registry server (optional)
        heartbeat_interval: Seconds between heartbeats
        
    Returns:
        DiscoveryClient instance attached to the server
    """
    # Make sure the agent card has discovery capabilities
    if not hasattr(server.agent_card, "capabilities"):
        server.agent_card.capabilities = {}
    
    # Enable discovery capability
    server.agent_card.capabilities["agent_discovery"] = True
    
    # Create discovery client
    client = DiscoveryClient(server.agent_card)
    
    # Add registry URL if provided
    if registry_url:
        client.add_registry(registry_url)
        
        # Register with registry
        client.register()
        
        # Start heartbeat
        client.start_heartbeat(interval=heartbeat_interval)
    
    # Create a DiscoveryEnabledServer by extending the server class
    class DiscoveryEnabledServer(server.__class__):
        """
        Enhanced server class with discovery capabilities.
        This is a dynamically created class that extends the server's class
        with discovery-specific functionality.
        """
        
        def __init__(self, *args, **kwargs):
            """Initialize the enhanced server."""
            super().__init__(*args, **kwargs)
            self.discovery_client = None
            
        def setup_routes(self, app):
            """Set up discovery-related routes for the server."""
            # Call the parent class setup_routes first
            super().setup_routes(app)
            
            # Import Flask components
            try:
                from flask import request, jsonify
            except ImportError:
                logger.error("Flask is required for discovery server enhancements")
                return
            
            # Add discovery-related routes
            @app.route("/a2a/discovery/register", methods=["POST"])
            def discovery_register():
                """Register with a registry server."""
                try:
                    data = request.json
                    registry_url = data.get("registry_url")
                    if not registry_url:
                        return jsonify({"success": False, "error": "registry_url is required"}), 400
                    
                    self.discovery_client.add_registry(registry_url)
                    results = self.discovery_client.register()
                    
                    # Start heartbeat if not already running
                    if not self.discovery_client._heartbeat_thread:
                        self.discovery_client.start_heartbeat(interval=heartbeat_interval)
                    
                    return jsonify({"success": True, "results": results})
                except Exception as e:
                    logger.error(f"Error registering with registry: {e}")
                    return jsonify({"success": False, "error": str(e)}), 400
            
            @app.route("/a2a/discovery/unregister", methods=["POST"])
            def discovery_unregister():
                """Unregister from registry servers."""
                try:
                    registry_url = None
                    if request.json:
                        registry_url = request.json.get("registry_url")
                    
                    if registry_url:
                        # Unregister from a specific registry
                        if registry_url in self.discovery_client.registry_urls:
                            self.discovery_client.remove_registry(registry_url)
                            return jsonify({"success": True})
                        else:
                            return jsonify({"success": False, "error": "Registry not found"}), 404
                    else:
                        # Unregister from all registries
                        results = self.discovery_client.unregister()
                        return jsonify({"success": True, "results": results})
                except Exception as e:
                    logger.error(f"Error unregistering from registry: {e}")
                    return jsonify({"success": False, "error": str(e)}), 400
            
            @app.route("/a2a/discovery/discover", methods=["GET"])
            def discovery_discover():
                """Discover agents from registry servers."""
                try:
                    registry_url = request.args.get("registry_url")
                    
                    # Discover agents
                    agents = self.discovery_client.discover(registry_url)
                    
                    # Convert to dictionaries
                    agent_dicts = [agent.to_dict() for agent in agents]
                    
                    return jsonify({"agents": agent_dicts})
                except Exception as e:
                    logger.error(f"Error discovering agents: {e}")
                    return jsonify({"success": False, "error": str(e)}), 400
    
    # Create a new instance of the enhanced server class
    # We first create a new instance to hold the state
    enhanced_server = DiscoveryEnabledServer.__new__(DiscoveryEnabledServer)
    
    # Copy all attributes from the original server
    for attr_name in dir(server):
        # Skip special attributes and methods
        if attr_name.startswith('__'):
            continue
        try:
            setattr(enhanced_server, attr_name, getattr(server, attr_name))
        except (AttributeError, TypeError):
            pass
    
    # Initialize the discovery client attribute
    enhanced_server.discovery_client = client
    
    # Replace the original server with the enhanced server
    # This will update the server in-place with the enhanced functionality
    for attr_name in dir(enhanced_server):
        # Skip special attributes and methods
        if attr_name.startswith('__'):
            continue
        try:
            setattr(server, attr_name, getattr(enhanced_server, attr_name))
        except (AttributeError, TypeError):
            pass
    
    # Store the discovery client on the server
    setattr(server, 'discovery_client', client)
    
    return client