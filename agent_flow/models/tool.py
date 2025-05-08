"""
Tool models for representing and connecting to MCP tool servers.
"""

import json
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, Union, Tuple, Callable

import requests


class ToolSource(Enum):
    """Source types for tools."""
    LOCAL = auto()   # Local tool (part of this system)
    REMOTE = auto()  # Remote tool server
    CUSTOM = auto()  # Custom tool implementation


class ToolStatus(Enum):
    """Status of a tool connection."""
    AVAILABLE = auto()
    UNAVAILABLE = auto()
    ERROR = auto()


class ToolParameter:
    """Definition of a parameter for a tool."""
    
    def __init__(
        self,
        name: str,
        type_name: str = "string",
        description: str = "",
        required: bool = True,
        default: Any = None,
        enum_values: Optional[List[Any]] = None
    ):
        """
        Initialize a tool parameter.
        
        Args:
            name: Parameter name
            type_name: Type of the parameter (string, number, boolean, etc.)
            description: Description of the parameter
            required: Whether the parameter is required
            default: Default value for the parameter
            enum_values: List of valid values for enum types
        """
        self.name = name
        self.type_name = type_name
        self.description = description
        self.required = required
        self.default = default
        self.enum_values = enum_values or []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "name": self.name,
            "type": self.type_name,
            "description": self.description,
            "required": self.required
        }
        
        if self.default is not None:
            result["default"] = self.default
        
        if self.enum_values:
            result["enum"] = self.enum_values
        
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolParameter':
        """Create from dictionary representation."""
        return cls(
            name=data.get("name", ""),
            type_name=data.get("type", "string"),
            description=data.get("description", ""),
            required=data.get("required", True),
            default=data.get("default"),
            enum_values=data.get("enum")
        )


class ToolDefinition:
    """
    Definition of a tool that can be used in workflows.
    
    This represents a specific tool with its configuration, parameters,
    and connection details.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "Unnamed Tool",
        description: str = "",
        url: str = "",
        tool_path: str = "",
        tool_source: ToolSource = ToolSource.REMOTE,
        config: Optional[Dict[str, Any]] = None,
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a tool definition.
        
        Args:
            id: Unique identifier (generated if not provided)
            name: Human-readable name
            description: Description of the tool's purpose
            url: Base URL where the tool server is accessible
            tool_path: Path to access this specific tool (e.g., "tools/calculator")
            tool_source: Source type of the tool
            config: Configuration parameters for the tool
            created_at: Creation timestamp
            updated_at: Last update timestamp
            metadata: Additional metadata
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.url = url
        self.tool_path = tool_path
        self.tool_source = tool_source
        self.config = config or {}
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.metadata = metadata or {}
        self.parameters: List[ToolParameter] = []
        self.status = ToolStatus.UNAVAILABLE
        self.error_message: Optional[str] = None
        
        # Function for custom tools (ToolSource.CUSTOM)
        self.implementation: Optional[Callable] = None
    
    def execute(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool with the given parameters.
        
        Args:
            parameters: Dictionary of parameter values
            
        Returns:
            Tool execution result
            
        Raises:
            ValueError: If required parameters are missing
            RuntimeError: If tool execution fails
        """
        # Validate parameters
        for param in self.parameters:
            if param.required and param.name not in parameters:
                raise ValueError(f"Required parameter '{param.name}' missing")
        
        # Execute based on source type
        if self.tool_source == ToolSource.CUSTOM and self.implementation:
            try:
                result = self.implementation(**parameters)
                return {"success": True, "result": result}
            except Exception as e:
                self.error_message = str(e)
                raise RuntimeError(f"Tool execution failed: {e}")
        
        elif self.tool_source == ToolSource.REMOTE:
            try:
                # Build full URL
                full_url = f"{self.url.rstrip('/')}/{self.tool_path.lstrip('/')}"
                
                # Make request to the tool server
                response = requests.post(
                    full_url,
                    json=parameters,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                # Parse response
                result = response.json()
                return result
            except Exception as e:
                self.error_message = str(e)
                raise RuntimeError(f"Tool execution failed: {e}")
        
        else:
            raise NotImplementedError(f"Execution not implemented for source {self.tool_source}")
    
    def check_availability(self) -> bool:
        """
        Check if the tool is available.
        
        Returns:
            True if available, False otherwise
        """
        if self.tool_source == ToolSource.CUSTOM:
            # Custom tools are available if they have an implementation
            if self.implementation is not None:
                self.status = ToolStatus.AVAILABLE
                return True
            else:
                self.status = ToolStatus.UNAVAILABLE
                self.error_message = "No implementation provided"
                return False
        
        elif self.tool_source == ToolSource.REMOTE:
            try:
                # Try to access the tool server
                base_url = self.url.rstrip('/')
                response = requests.get(
                    f"{base_url}/health",
                    timeout=2.0
                )
                
                if response.status_code == 200:
                    self.status = ToolStatus.AVAILABLE
                    self.error_message = None
                    return True
                else:
                    self.status = ToolStatus.UNAVAILABLE
                    self.error_message = f"Server returned status {response.status_code}"
                    return False
            except Exception as e:
                self.status = ToolStatus.ERROR
                self.error_message = str(e)
                return False
        
        else:
            self.status = ToolStatus.UNAVAILABLE
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the tool definition to a dictionary.
        
        Returns:
            Dictionary representation of the tool definition
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "url": self.url,
            "tool_path": self.tool_path,
            "tool_source": self.tool_source.name,
            "config": self.config,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
            "parameters": [param.to_dict() for param in self.parameters],
            "status": self.status.name
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolDefinition':
        """
        Create a tool definition from a dictionary.
        
        Args:
            data: Dictionary representation of the tool definition
            
        Returns:
            ToolDefinition instance
        """
        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        # Create tool definition
        tool_def = cls(
            id=data.get("id"),
            name=data.get("name", "Unnamed Tool"),
            description=data.get("description", ""),
            url=data.get("url", ""),
            tool_path=data.get("tool_path", ""),
            tool_source=ToolSource[data.get("tool_source", "REMOTE")],
            config=data.get("config", {}),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {})
        )
        
        # Add parameters
        for param_data in data.get("parameters", []):
            if isinstance(param_data, dict):
                param = ToolParameter.from_dict(param_data)
                tool_def.parameters.append(param)
        
        # Set status
        status_str = data.get("status", "UNAVAILABLE")
        tool_def.status = ToolStatus[status_str]
        
        return tool_def


class ToolRegistry:
    """
    Registry for managing tool definitions.
    
    The registry maintains a collection of available tools that can be
    used in workflows, providing lookup, registration, and connection
    management.
    """
    
    def __init__(self):
        """Initialize the tool registry."""
        self.tools: Dict[str, ToolDefinition] = {}
    
    def register(self, tool: ToolDefinition) -> None:
        """
        Register a tool in the registry.
        
        Args:
            tool: Tool definition to register
        """
        self.tools[tool.id] = tool
    
    def unregister(self, tool_id: str) -> bool:
        """
        Remove a tool from the registry.
        
        Args:
            tool_id: ID of the tool to remove
            
        Returns:
            True if removed, False if not found
        """
        if tool_id in self.tools:
            del self.tools[tool_id]
            return True
        
        return False
    
    def get(self, tool_id: str) -> Optional[ToolDefinition]:
        """
        Get a tool by ID.
        
        Args:
            tool_id: ID of the tool to get
            
        Returns:
            ToolDefinition if found, None otherwise
        """
        return self.tools.get(tool_id)
    
    def list_tools(self) -> List[ToolDefinition]:
        """
        Get all registered tools.
        
        Returns:
            List of all tool definitions
        """
        return list(self.tools.values())
    
    def check_all_availability(self) -> Tuple[int, int]:
        """
        Check availability of all tools in the registry.
        
        Returns:
            Tuple of (available, unavailable) tool counts
        """
        available = 0
        unavailable = 0
        
        for tool in self.tools.values():
            if tool.check_availability():
                available += 1
            else:
                unavailable += 1
        
        return available, unavailable
    
    def discover_tools(self, mcp_url: str) -> List[ToolDefinition]:
        """
        Discover tools from an MCP server.
        
        Args:
            mcp_url: URL of the MCP server
            
        Returns:
            List of discovered tool definitions
        """
        discovered: List[ToolDefinition] = []
        
        try:
            # Normalize URL
            base_url = mcp_url.rstrip('/')
            
            # Fetch tool list
            response = requests.get(f"{base_url}/tools")
            response.raise_for_status()
            
            # Parse tool list
            tools_data = response.json()
            if not isinstance(tools_data, list):
                return discovered
            
            # Create tool definitions
            for tool_data in tools_data:
                if not isinstance(tool_data, dict) or "name" not in tool_data:
                    continue
                
                tool_name = tool_data.get("name", "")
                tool_path = f"tools/{tool_name}"
                
                # Create tool definition
                tool = ToolDefinition(
                    name=tool_name,
                    description=tool_data.get("description", ""),
                    url=base_url,
                    tool_path=tool_path,
                    tool_source=ToolSource.REMOTE
                )
                
                # Add parameters
                for param_name, param_info in tool_data.get("parameters", {}).items():
                    if isinstance(param_info, dict):
                        param_type = param_info.get("type", "string")
                        param_required = param_info.get("required", True)
                        param_desc = param_info.get("description", "")
                        
                        param = ToolParameter(
                            name=param_name,
                            type_name=param_type,
                            description=param_desc,
                            required=param_required
                        )
                        
                        tool.parameters.append(param)
                
                # Add to discovered list
                discovered.append(tool)
                
                # Register the tool
                self.register(tool)
        
        except Exception as e:
            print(f"Error discovering tools: {e}")
        
        return discovered
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the registry to a dictionary.
        
        Returns:
            Dictionary representation of the registry
        """
        return {
            "tools": [tool.to_dict() for tool in self.tools.values()]
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolRegistry':
        """
        Create a registry from a dictionary.
        
        Args:
            data: Dictionary representation of the registry
            
        Returns:
            ToolRegistry instance
        """
        registry = cls()
        
        for tool_data in data.get("tools", []):
            tool = ToolDefinition.from_dict(tool_data)
            registry.register(tool)
        
        return registry