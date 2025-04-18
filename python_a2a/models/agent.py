"""
Agent-related models for the A2A protocol.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum

from .base import BaseModel


@dataclass
class AgentSkill(BaseModel):
    """Represents a skill in an A2A agent card"""
    name: str
    description: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    input_modes: List[str] = field(default_factory=lambda: ["text/plain"])
    output_modes: List[str] = field(default_factory=lambda: ["text/plain"])

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "tags": self.tags
        }
        
        if self.examples:
            result["examples"] = self.examples
            
        if self.input_modes:
            result["inputModes"] = self.input_modes
            
        if self.output_modes:
            result["outputModes"] = self.output_modes
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentSkill':
        """Create an AgentSkill from a dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            tags=data.get("tags", []),
            examples=data.get("examples", []),
            input_modes=data.get("inputModes", ["text/plain"]),
            output_modes=data.get("outputModes", ["text/plain"])
        )


@dataclass
class AgentCard(BaseModel):
    """Represents an A2A agent card for discovery"""
    name: str
    description: str
    url: str
    version: str = "1.0.0"
    authentication: Optional[str] = None
    capabilities: Dict[str, Any] = field(default_factory=lambda: {
        "streaming": False,
        "pushNotifications": False,
        "stateTransitionHistory": False
    })
    default_input_modes: List[str] = field(default_factory=lambda: ["text/plain"])
    default_output_modes: List[str] = field(default_factory=lambda: ["text/plain"])
    skills: List[AgentSkill] = field(default_factory=list)
    provider: Optional[str] = None
    documentation_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "version": self.version,
            "capabilities": self.capabilities,
            "defaultInputModes": self.default_input_modes,
            "defaultOutputModes": self.default_output_modes,
            "skills": [skill.to_dict() for skill in self.skills]
        }
        
        if self.authentication:
            result["authentication"] = self.authentication
            
        if self.provider:
            result["provider"] = self.provider
            
        if self.documentation_url:
            result["documentationUrl"] = self.documentation_url
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentCard':
        """Create an AgentCard from a dictionary"""
        skills = [
            AgentSkill.from_dict(skill) 
            for skill in data.get("skills", [])
        ]
        
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            url=data.get("url", ""),
            version=data.get("version", "1.0.0"),
            authentication=data.get("authentication"),
            capabilities=data.get("capabilities", {
                "streaming": False,
                "pushNotifications": False,
                "stateTransitionHistory": False
            }),
            default_input_modes=data.get("defaultInputModes", ["text/plain"]),
            default_output_modes=data.get("defaultOutputModes", ["text/plain"]),
            skills=skills,
            provider=data.get("provider"),
            documentation_url=data.get("documentationUrl")
        )