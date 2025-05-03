"""
A2A Discovery Client implementation.

This module provides a client for interacting with agent registry servers.
"""

import time
import logging
import threading
from typing import Dict, List, Optional, Any, Set, Union

from ..models.agent import AgentCard
from ..exceptions import A2AConnectionError, A2AResponseError

# Configure logging
logger = logging.getLogger("python_a2a.discovery")


class DiscoveryClient:
    """
    Client for interacting with agent registries.
    
    This class provides methods for registering with registries,
    discovering agents, and sending heartbeats.
    """
    
    def __init__(self, agent_card: AgentCard):
        """
        Initialize the discovery client.
        
        Args:
            agent_card: Agent card for the agent using this client
        """
        self.agent_card = agent_card
        self.registry_urls: Set[str] = set()
        self._heartbeat_thread = None
        self._shutdown_event = threading.Event()
    
    def add_registry(self, registry_url: str) -> None:
        """
        Add a registry server to the client.
        
        Args:
            registry_url: URL of the registry server
        """
        cleaned_url = registry_url.rstrip('/')
        self.registry_urls.add(cleaned_url)
        logger.info(f"Added registry server: {cleaned_url}")
    
    def remove_registry(self, registry_url: str) -> bool:
        """
        Remove a registry server from the client.
        
        Args:
            registry_url: URL of the registry server to remove
            
        Returns:
            True if the registry was removed, False if not found
        """
        cleaned_url = registry_url.rstrip('/')
        if cleaned_url in self.registry_urls:
            self.registry_urls.remove(cleaned_url)
            logger.info(f"Removed registry server: {cleaned_url}")
            return True
        return False
    
    def register(self) -> List[Dict[str, Any]]:
        """
        Register with all known registries.
        
        Returns:
            List of registration results by registry
        """
        results = []
        
        for registry_url in self.registry_urls:
            try:
                import requests
                url = f"{registry_url}/registry/register"
                response = requests.post(
                    url,
                    json=self.agent_card.to_dict(),
                    headers={"Content-Type": "application/json"},
                    timeout=5.0
                )
                
                # Check if the request was successful
                if response.status_code == 200:
                    results.append({
                        "registry": registry_url,
                        "success": True,
                        "message": "Registration successful"
                    })
                    logger.info(f"Registered with registry: {registry_url}")
                else:
                    # Extract error message if available
                    error_msg = "Registration failed"
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict) and "error" in error_data:
                            error_msg = error_data["error"]
                    except:
                        pass
                    
                    results.append({
                        "registry": registry_url,
                        "success": False,
                        "message": error_msg,
                        "status_code": response.status_code
                    })
                    logger.warning(f"Failed to register with registry {registry_url}: {error_msg}")
                
            except Exception as e:
                results.append({
                    "registry": registry_url,
                    "success": False,
                    "message": str(e),
                    "error_type": type(e).__name__
                })
                logger.warning(f"Error registering with registry {registry_url}: {e}")
        
        return results
    
    def unregister(self) -> List[Dict[str, Any]]:
        """
        Unregister from all known registries.
        
        Returns:
            List of unregistration results by registry
        """
        results = []
        
        for registry_url in self.registry_urls:
            try:
                import requests
                url = f"{registry_url}/registry/unregister"
                response = requests.post(
                    url,
                    json={"url": self.agent_card.url},
                    headers={"Content-Type": "application/json"},
                    timeout=5.0
                )
                
                # Check if the request was successful
                if response.status_code == 200:
                    results.append({
                        "registry": registry_url,
                        "success": True,
                        "message": "Unregistration successful"
                    })
                    logger.info(f"Unregistered from registry: {registry_url}")
                else:
                    # Extract error message if available
                    error_msg = "Unregistration failed"
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict) and "error" in error_data:
                            error_msg = error_data["error"]
                    except:
                        pass
                    
                    results.append({
                        "registry": registry_url,
                        "success": False,
                        "message": error_msg,
                        "status_code": response.status_code
                    })
                    logger.warning(f"Failed to unregister from registry {registry_url}: {error_msg}")
                
            except Exception as e:
                results.append({
                    "registry": registry_url,
                    "success": False,
                    "message": str(e),
                    "error_type": type(e).__name__
                })
                logger.warning(f"Error unregistering from registry {registry_url}: {e}")
        
        return results
    
    def heartbeat(self) -> List[Dict[str, Any]]:
        """
        Send heartbeat to all known registries.
        
        Returns:
            List of heartbeat results by registry
        """
        results = []
        
        for registry_url in self.registry_urls:
            try:
                import requests
                url = f"{registry_url}/registry/heartbeat"
                response = requests.post(
                    url,
                    json={"url": self.agent_card.url},
                    headers={"Content-Type": "application/json"},
                    timeout=5.0
                )
                
                # Only log errors, not successful heartbeats (to avoid log spam)
                if response.status_code != 200:
                    error_msg = "Heartbeat failed"
                    try:
                        error_data = response.json()
                        if isinstance(error_data, dict) and "error" in error_data:
                            error_msg = error_data["error"]
                    except:
                        pass
                    
                    logger.warning(f"Failed heartbeat to registry {registry_url}: {error_msg}")
                
                results.append({
                    "registry": registry_url,
                    "success": response.status_code == 200,
                    "status_code": response.status_code
                })
                
            except Exception as e:
                results.append({
                    "registry": registry_url,
                    "success": False,
                    "message": str(e),
                    "error_type": type(e).__name__
                })
                logger.debug(f"Error sending heartbeat to registry {registry_url}: {e}")
        
        return results
    
    def discover(self, registry_url: Optional[str] = None) -> List[AgentCard]:
        """
        Discover agents from registries.
        
        Args:
            registry_url: URL of specific registry to query, or None for all
            
        Returns:
            List of discovered agent cards
        """
        agents = []
        registries = [registry_url] if registry_url else self.registry_urls
        
        for reg_url in registries:
            try:
                import requests
                url = f"{reg_url}/registry/agents"
                response = requests.get(
                    url,
                    headers={"Accept": "application/json"},
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    try:
                        agents_data = response.json()
                        
                        # Handle different response formats
                        if isinstance(agents_data, list):
                            # Direct list of agent cards
                            for agent_data in agents_data:
                                try:
                                    agent = AgentCard.from_dict(agent_data)
                                    agents.append(agent)
                                except Exception as e:
                                    logger.warning(f"Error parsing agent card: {e}")
                        elif isinstance(agents_data, dict) and "agents" in agents_data:
                            # Google A2A format with "agents" key
                            for agent_data in agents_data["agents"]:
                                try:
                                    agent = AgentCard.from_dict(agent_data)
                                    agents.append(agent)
                                except Exception as e:
                                    logger.warning(f"Error parsing agent card: {e}")
                    except Exception as e:
                        logger.warning(f"Error parsing discovery response from {reg_url}: {e}")
                else:
                    logger.warning(f"Failed to discover agents from registry {reg_url}: {response.status_code}")
            
            except Exception as e:
                logger.warning(f"Error discovering agents from registry {reg_url}: {e}")
        
        return agents
    
    def start_heartbeat(self, interval: int = 60) -> None:
        """
        Start a background thread to send periodic heartbeats.
        
        Args:
            interval: Seconds between heartbeats
        """
        if self._heartbeat_thread is not None:
            logger.warning("Heartbeat thread already running")
            return
        
        def heartbeat_loop():
            while not self._shutdown_event.is_set():
                try:
                    self.heartbeat()
                except Exception as e:
                    logger.error(f"Error in heartbeat thread: {e}")
                
                # Sleep with timeout checking
                self._shutdown_event.wait(timeout=interval)
        
        self._heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
        self._heartbeat_thread.start()
        logger.info(f"Heartbeat thread started (interval={interval}s)")
    
    def stop_heartbeat(self) -> None:
        """Stop the heartbeat thread if it's running."""
        if self._heartbeat_thread is not None:
            self._shutdown_event.set()
            self._heartbeat_thread.join(timeout=5.0)
            self._heartbeat_thread = None
            logger.info("Heartbeat thread stopped")