"""
Network of interconnected A2A agents with discovery and management capabilities.
"""

import logging
from typing import Dict, Any, Optional, List, Union
import uuid

from ..client import A2AClient, BaseA2AClient
from ..models import AgentCard
from ..exceptions import A2AConnectionError

logger = logging.getLogger(__name__)


class AgentNetwork:
    """
    Manages a network of A2A-compatible agents.
    
    Provides methods for adding, discovering, and accessing agents in the network.
    Supports both URL-based and client-based agent registration.
    """
    
    def __init__(self, name: str = "Agent Network"):
        """
        Initialize an agent network.
        
        Args:
            name: Name of the agent network
        """
        self.name = name
        self.agents = {}  # Map of agent name to client
        self.agent_cards = {}  # Cache of agent cards by name
        self.agent_urls = {}  # Original URLs for agents
        self._id = str(uuid.uuid4())
    
    def add(
        self, 
        name: str, 
        agent_or_url: Union[str, BaseA2AClient],
        headers: Optional[Dict[str, str]] = None
    ) -> 'AgentNetwork':
        """
        Add an agent to the network.
        
        Args:
            name: Name to reference the agent by
            agent_or_url: Either an agent client instance or URL string
            headers: Optional HTTP headers for URL-based agents
            
        Returns:
            Self for method chaining
        """
        # Handle already added agents
        if name in self.agents:
            logger.warning(f"Agent '{name}' already exists in network. Replacing.")
        
        # Create client if URL string is provided
        if isinstance(agent_or_url, str):
            try:
                client = A2AClient(agent_or_url, headers=headers)
                self.agents[name] = client
                self.agent_urls[name] = agent_or_url
                # Cache agent card
                self.agent_cards[name] = getattr(client, 'agent_card', None)
                logger.info(f"Added agent '{name}' from URL: {agent_or_url}")
            except A2AConnectionError as e:
                logger.warning(f"Error connecting to agent '{name}' at {agent_or_url}: {e}")
                return self
        else:
            # Use provided client directly
            self.agents[name] = agent_or_url
            self.agent_cards[name] = getattr(agent_or_url, 'agent_card', None)
            logger.info(f"Added existing client as agent '{name}'")
        
        return self  # Enable method chaining
    
    def get_agent(self, name: str) -> Optional[BaseA2AClient]:
        """
        Get an agent by name.
        
        Args:
            name: Name of the agent to get
            
        Returns:
            The agent client, or None if not found
        """
        return self.agents.get(name)
    
    def has_agent(self, name: str) -> bool:
        """
        Check if an agent exists in the network.
        
        Args:
            name: Name of the agent to check
            
        Returns:
            True if the agent exists, False otherwise
        """
        return name in self.agents
    
    def get_agent_card(self, name: str) -> Optional[AgentCard]:
        """
        Get the agent card for an agent.
        
        Args:
            name: Name of the agent
            
        Returns:
            The agent card, or None if not available
        """
        # Check cache first
        if name in self.agent_cards and self.agent_cards[name] is not None:
            return self.agent_cards[name]
        
        # Try to get from agent
        if name in self.agents:
            agent = self.agents[name]
            # Try to access agent_card attribute
            card = getattr(agent, 'agent_card', None)
            if card:
                self.agent_cards[name] = card
                return card
        
        return None
    
    def list_agents(self) -> List[Dict[str, Any]]:
        """
        List all agents in the network with their metadata.
        
        Returns:
            List of agent information dictionaries
        """
        agents_info = []
        
        for name, agent in self.agents.items():
            info = {
                "name": name,
                "url": self.agent_urls.get(name, "N/A"),
            }
            
            # Add agent card info if available
            card = self.get_agent_card(name)
            if card:
                info.update({
                    "description": card.description,
                    "version": card.version,
                    "skills_count": len(getattr(card, 'skills', [])),
                })
            
            agents_info.append(info)
        
        return agents_info
    
    def discover_agents(self, urls: List[str], headers: Optional[Dict[str, str]] = None) -> int:
        """
        Discover and add agents from a list of URLs.
        
        Args:
            urls: List of URLs to check for A2A agents
            headers: Optional HTTP headers for requests
            
        Returns:
            Number of agents successfully added
        """
        added_count = 0
        
        for url in urls:
            try:
                # Try to connect to the URL as an A2A agent
                client = A2AClient(url, headers=headers)
                
                # Get agent name from card if available
                agent_name = None
                if hasattr(client, 'agent_card'):
                    agent_name = client.agent_card.name
                
                # Fall back to domain name if no card
                if not agent_name:
                    from urllib.parse import urlparse
                    parsed_url = urlparse(url)
                    agent_name = parsed_url.netloc.split('.')[0]
                
                # Ensure unique name
                final_name = agent_name
                count = 1
                while final_name in self.agents:
                    final_name = f"{agent_name}_{count}"
                    count += 1
                
                # Add the agent
                self.add(final_name, client)
                added_count += 1
                
            except Exception as e:
                logger.debug(f"URL {url} is not a valid A2A agent: {str(e)}")
        
        return added_count
    
    def remove(self, name: str) -> bool:
        """
        Remove an agent from the network.
        
        Args:
            name: Name of the agent to remove
            
        Returns:
            True if removed, False if not found
        """
        if name in self.agents:
            del self.agents[name]
            if name in self.agent_cards:
                del self.agent_cards[name]
            if name in self.agent_urls:
                del self.agent_urls[name]
            logger.info(f"Removed agent '{name}' from network")
            return True
        
        return False