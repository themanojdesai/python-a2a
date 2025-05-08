"""
Agent models for representing and connecting to A2A agents.
"""

import json
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, Union, Tuple

from python_a2a import (
    AgentCard, AgentSkill, A2AClient, 
    Message, TextContent, MessageRole
)


class AgentSource(Enum):
    """Source types for agents."""
    LOCAL = auto()  # Local agent (part of this system)
    REMOTE = auto()  # Remote A2A agent
    LLM = auto()    # Language model powered agent
    CUSTOM = auto()  # Custom agent implementation


class AgentStatus(Enum):
    """Status of an agent connection."""
    CONNECTED = auto()
    DISCONNECTED = auto()
    ERROR = auto()


class AgentDefinition:
    """
    Definition of an agent to be used in workflows.
    
    This represents a specific agent instance with its configuration,
    capabilities, and connection details.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "Unnamed Agent",
        description: str = "",
        url: str = "",
        agent_source: AgentSource = AgentSource.REMOTE,
        agent_type: str = "a2a",
        config: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize an agent definition.
        
        Args:
            id: Unique identifier (generated if not provided)
            name: Human-readable name
            description: Description of the agent's purpose
            url: URL where the agent is accessible
            agent_source: Source type of the agent
            agent_type: Type of the agent (a2a, langchain, mcp, etc.)
            config: Configuration parameters for the agent
            created_at: Creation timestamp
            updated_at: Last update timestamp
            metadata: Additional metadata
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.url = url
        self.agent_source = agent_source
        self.agent_type = agent_type
        self.config = config or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
        self.skills: List[AgentSkill] = []
        self.status = AgentStatus.DISCONNECTED
        self.agent_card: Optional[AgentCard] = None
        self.client: Optional[A2AClient] = None
        self.error_message: Optional[str] = None
    
    def connect(self) -> bool:
        """
        Connect to the agent and fetch its capabilities.
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Initialize client
            self.client = A2AClient(self.url)
            
            # Fetch agent card
            self.agent_card = self.client.get_agent_card()
            
            # Update properties from agent card
            if self.agent_card:
                self.name = self.agent_card.name or self.name
                self.description = self.agent_card.description or self.description
                if hasattr(self.agent_card, 'skills'):
                    self.skills = self.agent_card.skills
            
            self.status = AgentStatus.CONNECTED
            self.error_message = None
            return True
            
        except Exception as e:
            self.status = AgentStatus.ERROR
            self.error_message = str(e)
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the agent."""
        self.client = None
        self.status = AgentStatus.DISCONNECTED
    
    def send_message(self, text: str) -> Optional[str]:
        """
        Send a message to the agent and return the response.
        
        Args:
            text: Message text to send
            
        Returns:
            Response text if successful, None on error
        """
        if not self.client or self.status != AgentStatus.CONNECTED:
            self.error_message = "Agent not connected"
            return None
        
        try:
            response = self.client.ask(text)
            return response
        except Exception as e:
            self.error_message = str(e)
            return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the agent definition to a dictionary.
        
        Returns:
            Dictionary representation of the agent definition
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "agent_source": self.agent_source.name,
            "agent_type": self.agent_type,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "skills": [skill.to_dict() for skill in self.skills],
            "status": self.status.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentDefinition':
        """
        Create an agent definition from a dictionary.
        
        Args:
            data: Dictionary representation of the agent definition
            
        Returns:
            AgentDefinition instance
        """
        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        # Create agent definition
        agent_def = cls(
            id=data.get("id"),
            name=data.get("name", "Unnamed Agent"),
            description=data.get("description", ""),
            url=data.get("url", ""),
            agent_source=AgentSource[data.get("agent_source", "REMOTE")],
            agent_type=data.get("agent_type", "a2a"),
            config=data.get("config", {}),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )
        
        # Add skills
        for skill_data in data.get("skills", []):
            if isinstance(skill_data, dict):
                skill = AgentSkill(
                    name=skill_data.get("name", ""),
                    description=skill_data.get("description", ""),
                    tags=skill_data.get("tags", []),
                    examples=skill_data.get("examples", [])
                )
                agent_def.skills.append(skill)
        
        # Set status
        status_str = data.get("status", "DISCONNECTED")
        agent_def.status = AgentStatus[status_str]
        
        return agent_def


class AgentRegistry:
    """
    Registry for managing agent definitions.
    
    The registry maintains a collection of available agents that can be
    used in workflows, providing lookup, registration, and connection
    management.
    """
    
    def __init__(self):
        """Initialize the agent registry."""
        self.agents: Dict[str, AgentDefinition] = {}
    
    def register(self, agent: AgentDefinition) -> None:
        """
        Register an agent in the registry.
        
        Args:
            agent: Agent definition to register
        """
        self.agents[agent.id] = agent
    
    def unregister(self, agent_id: str) -> bool:
        """
        Remove an agent from the registry.
        
        Args:
            agent_id: ID of the agent to remove
            
        Returns:
            True if removed, False if not found
        """
        if agent_id in self.agents:
            # Disconnect if connected
            agent = self.agents[agent_id]
            if agent.status == AgentStatus.CONNECTED:
                agent.disconnect()
            
            # Remove from registry
            del self.agents[agent_id]
            return True
        
        return False
    
    def get(self, agent_id: str) -> Optional[AgentDefinition]:
        """
        Get an agent by ID.
        
        Args:
            agent_id: ID of the agent to get
            
        Returns:
            AgentDefinition if found, None otherwise
        """
        return self.agents.get(agent_id)
    
    def list_agents(self) -> List[AgentDefinition]:
        """
        Get all registered agents.
        
        Returns:
            List of all agent definitions
        """
        return list(self.agents.values())
    
    def connect_all(self) -> Tuple[int, int]:
        """
        Connect to all agents in the registry.
        
        Returns:
            Tuple of (successful, failed) connection counts
        """
        successful = 0
        failed = 0
        
        for agent in self.agents.values():
            if agent.connect():
                successful += 1
            else:
                failed += 1
        
        return successful, failed
    
    def disconnect_all(self) -> None:
        """Disconnect from all agents in the registry."""
        for agent in self.agents.values():
            agent.disconnect()
    
    def discover_agents(self, base_url: str, port_range: Tuple[int, int]) -> List[AgentDefinition]:
        """
        Discover agents running on local ports.
        
        Args:
            base_url: Base URL for discovery (e.g., "http://localhost")
            port_range: Range of ports to scan (start, end)
            
        Returns:
            List of discovered agent definitions
        """
        import requests
        from concurrent.futures import ThreadPoolExecutor
        
        discovered: List[AgentDefinition] = []
        start_port, end_port = port_range
        
        def check_port(port: int) -> Optional[AgentDefinition]:
            """Check a single port for an A2A agent."""
            url = f"{base_url}:{port}"
            agent_url = f"{url}/agent.json"
            
            try:
                response = requests.get(agent_url, timeout=0.5)
                if response.status_code == 200:
                    data = response.json()
                    
                    if isinstance(data, dict) and "name" in data and "description" in data:
                        # Create agent definition
                        agent = AgentDefinition(
                            name=data.get("name", f"Agent on port {port}"),
                            description=data.get("description", ""),
                            url=url,
                            agent_source=AgentSource.REMOTE,
                            agent_type="a2a"
                        )
                        
                        # Add skills if available
                        if "skills" in data and isinstance(data["skills"], list):
                            for skill_data in data["skills"]:
                                if isinstance(skill_data, dict):
                                    skill = AgentSkill(
                                        name=skill_data.get("name", ""),
                                        description=skill_data.get("description", ""),
                                        tags=skill_data.get("tags", []),
                                        examples=skill_data.get("examples", [])
                                    )
                                    agent.skills.append(skill)
                        
                        return agent
            except:
                pass
            
            return None
        
        # Use ThreadPoolExecutor to scan ports in parallel
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(
                check_port, 
                range(start_port, end_port + 1)
            ))
        
        # Filter out None results
        discovered = [agent for agent in results if agent is not None]
        
        # Add discovered agents to registry
        for agent in discovered:
            self.register(agent)
        
        return discovered
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the registry to a dictionary.
        
        Returns:
            Dictionary representation of the registry
        """
        return {
            "agents": [agent.to_dict() for agent in self.agents.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentRegistry':
        """
        Create a registry from a dictionary.
        
        Args:
            data: Dictionary representation of the registry
            
        Returns:
            AgentRegistry instance
        """
        registry = cls()
        
        for agent_data in data.get("agents", []):
            agent = AgentDefinition.from_dict(agent_data)
            registry.register(agent)
        
        return registry