"""
Task models for the A2A protocol.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union
from enum import Enum
from datetime import datetime

from .base import BaseModel


class TaskState(str, Enum):
    """Possible states for an A2A task"""
    SUBMITTED = "submitted"
    WAITING = "waiting"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"


@dataclass
class TaskStatus(BaseModel):
    """Status of an A2A task"""
    state: TaskState
    message: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "state": self.state.value,
            "timestamp": self.timestamp
        }
        
        if self.message:
            result["message"] = self.message
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskStatus':
        """Create a TaskStatus from a dictionary"""
        state_value = data.get("state", TaskState.UNKNOWN.value)
        state = TaskState(state_value) if isinstance(state_value, str) else state_value
        
        return cls(
            state=state,
            message=data.get("message"),
            timestamp=data.get("timestamp", datetime.now().isoformat())
        )


@dataclass
class Task(BaseModel):
    """An A2A task representing a unit of work"""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    session_id: Optional[str] = None
    status: TaskStatus = field(default_factory=lambda: TaskStatus(state=TaskState.SUBMITTED))
    message: Optional[Dict[str, Any]] = None
    history: List[Dict[str, Any]] = field(default_factory=list)
    artifacts: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        result = {
            "id": self.id,
            "sessionId": self.session_id,
            "status": self.status.to_dict()
        }
        
        if self.message:
            result["message"] = self.message
            
        if self.history:
            result["history"] = self.history
            
        if self.artifacts:
            result["artifacts"] = self.artifacts
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a Task from a dictionary"""
        status_data = data.get("status", {})
        status = TaskStatus.from_dict(status_data) if status_data else TaskStatus(state=TaskState.SUBMITTED)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            session_id=data.get("sessionId"),
            status=status,
            message=data.get("message"),
            history=data.get("history", []),
            artifacts=data.get("artifacts", []),
            metadata=data.get("metadata", {})
        )

    def get_text(self) -> str:
        """Get the text content from the most recent artifact"""
        if not self.artifacts:
            return ""
        
        for part in self.artifacts[-1].get("parts", []):
            if part.get("type") == "text":
                return part.get("text", "")
                
        return ""