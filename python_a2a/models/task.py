"""
Task models for the A2A protocol.
"""

import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, ClassVar
from enum import Enum
from datetime import datetime

from .base import BaseModel
from .message import Message, MessageRole


class TaskState(str, Enum):
    """Possible states for an A2A task"""
    SUBMITTED = "submitted"
    WAITING = "waiting"
    INPUT_REQUIRED = "input-required"
    COMPLETED = "completed"
    CANCELED = "canceled"
    FAILED = "failed"
    UNKNOWN = "unknown"
    
    @classmethod
    def from_google_a2a(cls, state: str) -> 'TaskState':
        """Convert a Google A2A task state to TaskState
        
        Args:
            state: Google A2A task state string
            
        Returns:
            Corresponding TaskState
        """
        state_map = {
            "submitted": cls.SUBMITTED,
            "waiting": cls.WAITING,
            "input-required": cls.INPUT_REQUIRED,
            "completed": cls.COMPLETED,
            "canceled": cls.CANCELED,
            "failed": cls.FAILED,
            "unknown": cls.UNKNOWN
        }
        return state_map.get(state.lower(), cls.UNKNOWN)


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
    
    def to_google_a2a(self) -> Dict[str, Any]:
        """Convert to Google A2A format dictionary
        
        Returns:
            A dictionary in Google A2A format
        """
        # Google A2A format is very similar to python_a2a for TaskStatus
        return self.to_dict()

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
    
    @classmethod
    def from_google_a2a(cls, data: Dict[str, Any]) -> 'TaskStatus':
        """Create a TaskStatus from a Google A2A format dictionary
        
        Args:
            data: A dictionary in Google A2A format
            
        Returns:
            A TaskStatus object
        """
        state_value = data.get("state", "unknown")
        state = TaskState.from_google_a2a(state_value)
        
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
    
    # Add a class variable to track protocol compatibility mode
    _GOOGLE_A2A_COMPATIBILITY: ClassVar[bool] = False

    def __post_init__(self):
        if self.session_id is None:
            self.session_id = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        # Use google format if compatibility mode is enabled
        if self._GOOGLE_A2A_COMPATIBILITY:
            return self.to_google_a2a()
        
        # Standard python_a2a format
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
    
    def to_google_a2a(self) -> Dict[str, Any]:
        """Convert to Google A2A format dictionary
        
        Returns:
            A dictionary in Google A2A format
        """
        # Convert status to Google A2A format
        status = self.status.to_google_a2a() if hasattr(self.status, 'to_google_a2a') else self.status.to_dict()
        
        # Convert message if it's a Message object or dict with python_a2a format
        message_data = None
        if self.message:
            if isinstance(self.message, dict):
                # Check if it contains python_a2a format fields
                if "content" in self.message and "role" in self.message:
                    # Try to convert from python_a2a format to Google A2A format
                    try:
                        from .message import Message
                        message = Message.from_dict(self.message)
                        message_data = message.to_google_a2a()
                    except Exception:
                        # If conversion fails, use as-is to maintain backward compatibility
                        message_data = self.message
                else:
                    # Already might be in Google A2A format or custom format
                    message_data = self.message
            elif hasattr(self.message, 'to_google_a2a'):
                # It's a Message object with to_google_a2a method
                message_data = self.message.to_google_a2a()
            elif hasattr(self.message, 'to_dict'):
                # It's a BaseModel object with to_dict method
                message_dict = self.message.to_dict()
                # Check if it contains python_a2a format fields
                if "content" in message_dict and "role" in message_dict:
                    # Try to convert from python_a2a format to Google A2A format
                    try:
                        from .message import Message
                        message = Message.from_dict(message_dict)
                        message_data = message.to_google_a2a()
                    except Exception:
                        # If conversion fails, use as-is
                        message_data = message_dict
                else:
                    message_data = message_dict
        
        # Convert artifacts
        google_artifacts = []
        for artifact in self.artifacts:
            google_artifact = {}
            
            # Convert parts if present
            if "parts" in artifact:
                # Check if parts need conversion from python_a2a format
                parts = artifact["parts"]
                google_parts = []
                
                for part in parts:
                    if isinstance(part, dict):
                        if "type" in part:
                            if part["type"] == "text":
                                # Text part - already in Google A2A format
                                google_parts.append(part)
                            elif part["type"] == "function_call":
                                # Convert function_call to data part
                                google_parts.append({
                                    "type": "data",
                                    "data": {
                                        "function_call": {
                                            "name": part.get("name", ""),
                                            "parameters": part.get("parameters", [])
                                        }
                                    }
                                })
                            elif part["type"] == "function_response":
                                # Convert function_response to data part
                                google_parts.append({
                                    "type": "data",
                                    "data": {
                                        "function_response": {
                                            "name": part.get("name", ""),
                                            "response": part.get("response", {})
                                        }
                                    }
                                })
                            elif part["type"] == "error":
                                # Convert error to data part
                                google_parts.append({
                                    "type": "data",
                                    "data": {
                                        "error": part.get("message", "")
                                    }
                                })
                            else:
                                # Unknown type, add as-is
                                google_parts.append(part)
                        else:
                            # No type field, add as-is
                            google_parts.append(part)
                
                google_artifact["parts"] = google_parts
            else:
                # No parts field, add artifact as-is
                google_artifact = artifact.copy()
            
            google_artifacts.append(google_artifact)
        
        # Create the Google A2A task dict
        result = {
            "id": self.id,
            "sessionId": self.session_id,
            "status": status
        }
        
        if message_data:
            result["message"] = message_data
            
        if self.history:
            result["history"] = self.history
            
        if google_artifacts:
            result["artifacts"] = google_artifacts
            
        if self.metadata:
            result["metadata"] = self.metadata
            
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Task':
        """Create a Task from a dictionary"""
        # Check if this is Google A2A format with careful detection
        # Only detect as Google A2A if very clear indicators are present
        is_google_format = False
        
        if "status" in data and isinstance(data["status"], dict) and "state" in data["status"]:
            # Look deeper for Google A2A indicators in message or artifacts
            message_data = data.get("message", {})
            if message_data and "parts" in message_data and "role" in message_data and not "content" in message_data:
                is_google_format = True
            
            artifacts = data.get("artifacts", [])
            if not is_google_format and artifacts and isinstance(artifacts, list):
                for artifact in artifacts:
                    if "parts" in artifact and isinstance(artifact["parts"], list):
                        for part in artifact["parts"]:
                            if isinstance(part, dict) and "type" in part:
                                if (part["type"] == "text" and "text" in part) or (
                                    part["type"] == "data" and "data" in part and isinstance(part["data"], dict)):
                                    is_google_format = True
                                    break
        
        # Use appropriate parsing based on format
        if is_google_format:
            return cls.from_google_a2a(data)
        
        # Standard python_a2a format
        status_data = data.get("status", {})
        status = TaskStatus.from_dict(status_data) if status_data else TaskStatus(state=TaskState.SUBMITTED)
        
        # CRITICAL: Preserve message format exactly as it was
        # This is essential for backward compatibility
        message = data.get("message")
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            session_id=data.get("sessionId"),
            status=status,
            message=message,  # Keep original message format
            history=data.get("history", []),
            artifacts=data.get("artifacts", []),
            metadata=data.get("metadata", {})
        )
    
    @classmethod
    def from_google_a2a(cls, data: Dict[str, Any]) -> 'Task':
        """Create a Task from a Google A2A format dictionary
        
        Args:
            data: A dictionary in Google A2A format
            
        Returns:
            A Task object
        """
        # Parse status
        status_data = data.get("status", {})
        status = TaskStatus.from_google_a2a(status_data) if status_data else TaskStatus(state=TaskState.SUBMITTED)
        
        # Process message - CRITICAL: Convert Google A2A format to python_a2a format to maintain compatibility
        message_data = data.get("message")
        python_message = None
        
        if message_data and "parts" in message_data and "role" in message_data and not "content" in message_data:
            # Convert Google A2A message to python_a2a format
            try:
                from .message import Message
                message = Message.from_google_a2a(message_data)
                python_message = message.to_dict()
            except Exception:
                # If conversion fails, keep as-is
                python_message = message_data
        else:
            # Not in Google A2A format, use as-is
            python_message = message_data
        
        # Process artifacts - Convert any Google A2A format parts to python_a2a format for compatibility
        python_artifacts = []
        for artifact in data.get("artifacts", []):
            python_artifact = {}
            
            # Convert parts if present
            if "parts" in artifact and isinstance(artifact["parts"], list):
                parts = artifact["parts"]
                python_parts = []
                
                for part in parts:
                    if isinstance(part, dict) and "type" in part:
                        if part["type"] == "text":
                            # Text part - already compatible
                            python_parts.append(part)
                        elif part["type"] == "data" and "data" in part and isinstance(part["data"], dict):
                            data_content = part["data"]
                            
                            # Check for function call
                            if "function_call" in data_content:
                                func_data = data_content["function_call"]
                                python_parts.append({
                                    "type": "function_call",
                                    "name": func_data.get("name", ""),
                                    "parameters": func_data.get("parameters", [])
                                })
                            # Check for function response
                            elif "function_response" in data_content:
                                func_data = data_content["function_response"]
                                python_parts.append({
                                    "type": "function_response",
                                    "name": func_data.get("name", ""),
                                    "response": func_data.get("response", {})
                                })
                            # Check for error
                            elif "error" in data_content:
                                python_parts.append({
                                    "type": "error",
                                    "message": data_content.get("error", "")
                                })
                            else:
                                # Unknown data type, keep as-is
                                python_parts.append(part)
                        else:
                            # Other part types, keep as-is
                            python_parts.append(part)
                    else:
                        # Unknown part format, keep as-is
                        python_parts.append(part)
                
                python_artifact["parts"] = python_parts
            else:
                # No parts field, add artifact as-is
                python_artifact = artifact.copy()
            
            python_artifacts.append(python_artifact)
        
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            session_id=data.get("sessionId"),
            status=status,
            message=python_message,  # Use converted message
            history=data.get("history", []),
            artifacts=python_artifacts,  # Use converted artifacts
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
    
    @classmethod
    def enable_google_a2a_compatibility(cls, enable: bool = True) -> None:
        """Enable or disable Google A2A compatibility mode
        
        When enabled, to_dict() will output Google A2A format
        
        Args:
            enable: Whether to enable compatibility mode
        """
        cls._GOOGLE_A2A_COMPATIBILITY = enable
        
        # Also update Message class
        from .message import Message
        Message.enable_google_a2a_compatibility(enable)

    @classmethod
    def is_google_a2a_compatibility_enabled(cls) -> bool:
        """Check if Google A2A compatibility mode is enabled
        
        Returns:
            True if enabled, False otherwise
        """
        return cls._GOOGLE_A2A_COMPATIBILITY