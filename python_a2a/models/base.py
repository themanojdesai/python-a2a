"""
Base models for the A2A protocol.
"""

import json
from typing import Dict, Any, TypeVar, Type, ClassVar, Optional
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict, field

T = TypeVar('T', bound='BaseModel')

class BaseModel(ABC):
    """Base class for all A2A models"""
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert model to dictionary representation
        
        Returns:
            Dictionary representation of the model
        """
        # The default implementation uses dataclasses.asdict
        # Subclasses can override this for custom serialization
        return asdict(self)
    
    def to_json(self) -> str:
        """
        Convert model to JSON string
        
        Returns:
            JSON string representation of the model
        """
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_dict(cls: Type[T], data: Dict[str, Any]) -> T:
        """
        Create model instance from dictionary
        
        Args:
            data: Dictionary representation of the model
            
        Returns:
            New model instance
        """
        # This is an abstract method that subclasses must implement
        raise NotImplementedError("Subclasses must implement from_dict")
    
    @classmethod
    def from_json(cls: Type[T], json_str: str) -> T:
        """
        Create model instance from JSON string
        
        Args:
            json_str: JSON string representation of the model
            
        Returns:
            New model instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)