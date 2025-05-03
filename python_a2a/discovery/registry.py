"""
A2A Agent Registry implementation.

This module provides a registry server for agent discovery in the A2A protocol.
"""

import os
import json
import time
import logging
import threading
from typing import Dict, List, Optional, Set, Any, Union
import uuid

try:
    from flask import Flask, request, jsonify, Response, render_template_string
except ImportError:
    Flask = None

from ..models.agent import AgentCard, AgentSkill
from ..server.http import create_flask_app
from ..server.base import BaseA2AServer
from ..exceptions import A2AImportError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("python_a2a.discovery")


class AgentRegistry(BaseA2AServer):
    """
    Agent registry for A2A agent discovery.
    
    This class provides a registry server that implements the agent discovery
    mechanism described in the Google A2A specification.
    """
    
    def __init__(self, name: str = "A2A Agent Registry", description: str = None):
        """
        Initialize the agent registry.
        
        Args:
            name: Name of the registry
            description: Optional description of the registry
        """
        # Set up the agent card for this registry
        self.agent_card = AgentCard(
            name=name,
            description=description or "Registry server for A2A agent discovery",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            capabilities={
                "agent_discovery": True,
                "registry": True,
                "google_a2a_compatible": True,
                "parts_array_format": True
            }
        )
        
        # Initialize registry state
        self.agents: Dict[str, AgentCard] = {}
        self.last_seen: Dict[str, float] = {}
        self._pruning_thread = None
        self._shutdown_event = threading.Event()
    
    def register_agent(self, agent_card: AgentCard) -> bool:
        """
        Register an agent with the registry.
        
        Args:
            agent_card: Agent card to register
            
        Returns:
            True if registration was successful, False otherwise
        """
        if not agent_card.url:
            logger.warning(f"Cannot register agent without URL: {agent_card.name}")
            return False
        
        agent_id = agent_card.url
        self.agents[agent_id] = agent_card
        self.last_seen[agent_id] = time.time()
        logger.info(f"Registered agent: {agent_card.name} at {agent_card.url}")
        return True
    
    def unregister_agent(self, agent_url: str) -> bool:
        """
        Unregister an agent from the registry.
        
        Args:
            agent_url: URL of the agent to unregister
            
        Returns:
            True if unregistration was successful, False otherwise
        """
        if agent_url in self.agents:
            agent_name = self.agents[agent_url].name
            del self.agents[agent_url]
            if agent_url in self.last_seen:
                del self.last_seen[agent_url]
            logger.info(f"Unregistered agent: {agent_name} at {agent_url}")
            return True
        return False
    
    def get_all_agents(self) -> List[AgentCard]:
        """
        Get all registered agents.
        
        Returns:
            List of agent cards
        """
        return list(self.agents.values())
    
    def get_agent(self, agent_url: str) -> Optional[AgentCard]:
        """
        Get a specific agent by URL.
        
        Args:
            agent_url: URL of the agent to get
            
        Returns:
            Agent card if found, None otherwise
        """
        return self.agents.get(agent_url)
    
    def prune_inactive_agents(self, max_age: int = 300) -> int:
        """
        Remove agents that haven't been seen recently.
        
        Args:
            max_age: Maximum age in seconds before an agent is considered inactive
            
        Returns:
            Number of agents pruned
        """
        now = time.time()
        to_remove = []
        
        for agent_url, last_seen in self.last_seen.items():
            if now - last_seen > max_age:
                to_remove.append(agent_url)
        
        for agent_url in to_remove:
            self.unregister_agent(agent_url)
        
        return len(to_remove)
    
    def _start_pruning_thread(self, interval: int = 60, max_age: int = 300) -> None:
        """
        Start a background thread to periodically prune inactive agents.
        
        Args:
            interval: Seconds between pruning runs
            max_age: Maximum age in seconds before an agent is considered inactive
        """
        if self._pruning_thread is not None:
            logger.warning("Pruning thread already running")
            return
        
        def prune_loop():
            while not self._shutdown_event.is_set():
                try:
                    pruned = self.prune_inactive_agents(max_age=max_age)
                    if pruned > 0:
                        logger.info(f"Pruned {pruned} inactive agents")
                except Exception as e:
                    logger.error(f"Error in agent pruning: {e}")
                
                # Sleep with timeout checking
                self._shutdown_event.wait(timeout=interval)
        
        self._pruning_thread = threading.Thread(target=prune_loop, daemon=True)
        self._pruning_thread.start()
        logger.info(f"Agent pruning thread started (interval={interval}s, max_age={max_age}s)")
    
    def _stop_pruning_thread(self) -> None:
        """Stop the pruning thread if it's running."""
        if self._pruning_thread is not None:
            self._shutdown_event.set()
            self._pruning_thread.join(timeout=5.0)
            self._pruning_thread = None
            logger.info("Agent pruning thread stopped")
    
    def handle_message(self, message):
        """Handle incoming messages (not used but required by BaseA2AServer)."""
        from ..models.message import Message, MessageRole
        from ..models.content import TextContent
        
        return Message(
            content=TextContent(
                text="This is an A2A agent registry server. Please use the specific registry endpoints."
            ),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id if hasattr(message, 'message_id') else None,
            conversation_id=message.conversation_id if hasattr(message, 'conversation_id') else None
        )
    
    def setup_routes(self, app) -> None:
        """
        Set up custom routes for the registry server.
        Implements the standardized BaseA2AServer interface.
        
        Args:
            app: Flask application to add routes to
        """
        # Call the parent class setup_routes first
        super().setup_routes(app)
        # Route for agent registration
        @app.route("/registry/register", methods=["POST"])
        def register():
            """Handle agent registration."""
            try:
                data = request.json
                agent_card = AgentCard.from_dict(data)
                success = self.register_agent(agent_card)
                return jsonify({"success": success})
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
                
                success = self.unregister_agent(agent_url)
                return jsonify({"success": success})
            except Exception as e:
                logger.error(f"Error unregistering agent: {e}")
                return jsonify({"success": False, "error": str(e)}), 400
        
        # Route for getting all agents
        @app.route("/registry/agents", methods=["GET"])
        def get_agents():
            """Get all registered agents."""
            agents = self.get_all_agents()
            return jsonify([agent.to_dict() for agent in agents])
        
        # Route for getting agent details
        @app.route("/registry/agents/<path:agent_url>", methods=["GET"])
        def get_agent(agent_url):
            """Get a specific agent by URL."""
            agent = self.get_agent(agent_url)
            if agent:
                return jsonify(agent.to_dict())
            return jsonify({"error": "Agent not found"}), 404
        
        # Route for Google A2A demo compatibility
        @app.route("/a2a/agents", methods=["GET"])
        def get_a2a_agents():
            """Get all agents in Google A2A demo format."""
            agents = self.get_all_agents()
            return jsonify({
                "agents": [agent.to_dict() for agent in agents]
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
    
    def run(self, host: str = "0.0.0.0", port: int = 8000, 
            prune_interval: int = 60, max_age: int = 300,
            debug: bool = False) -> None:
        """
        Run the registry server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
            prune_interval: Interval in seconds for pruning inactive agents
            max_age: Maximum age in seconds before an agent is considered inactive
            debug: Whether to run in debug mode
        """
        if Flask is None:
            raise A2AImportError(
                "Flask is not installed. "
                "Install it with 'pip install flask'"
            )
        
        # Update the URL in the agent card
        self.agent_card.url = f"http://{host}:{port}"
        
        # Create Flask app with custom routes
        app = create_flask_app(self)
        
        # Start pruning thread
        self._start_pruning_thread(interval=prune_interval, max_age=max_age)
        
        try:
            # Run the Flask app
            logger.info(f"Starting registry server on http://{host}:{port}")
            app.run(host=host, port=port, debug=debug)
        finally:
            # Stop pruning thread
            self._stop_pruning_thread()


def run_registry(registry: Optional[AgentRegistry] = None, 
                host: str = "0.0.0.0", port: int = 8000,
                prune_interval: int = 60, max_age: int = 300,
                debug: bool = False) -> None:
    """
    Run a registry server.
    
    This is a convenience function for running a registry server.
    
    Args:
        registry: AgentRegistry instance or None to create a new one
        host: Host to bind to
        port: Port to bind to
        prune_interval: Interval in seconds for pruning inactive agents
        max_age: Maximum age in seconds before an agent is considered inactive
        debug: Whether to run in debug mode
    """
    if registry is None:
        registry = AgentRegistry()
    
    registry.run(host=host, port=port, prune_interval=prune_interval, 
                max_age=max_age, debug=debug)