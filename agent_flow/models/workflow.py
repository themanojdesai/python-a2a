"""
Workflow model and related classes for representing workflows in Agent Flow.
"""

import json
import uuid
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, Union, Tuple


class NodeType(Enum):
    """Types of nodes in a workflow."""
    AGENT = auto()
    TOOL = auto()
    INPUT = auto()
    OUTPUT = auto()
    CONDITIONAL = auto()
    TRANSFORM = auto()
    ROUTER = auto()


class EdgeType(Enum):
    """Types of connections between nodes."""
    DATA = auto()  # Regular data flow
    SUCCESS = auto()  # Execute on success
    ERROR = auto()  # Execute on error
    CONDITION_TRUE = auto()  # Conditional branch when true
    CONDITION_FALSE = auto()  # Conditional branch when false
    ROUTE_OUTPUT = auto()  # Router output (used with port number in config)


class WorkflowNode:
    """
    Represents a single node in a workflow.
    
    A node can be an agent, a tool, an input/output node, or a
    conditional/transform node that modifies the flow of data.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "Unnamed Node",
        node_type: NodeType = NodeType.AGENT,
        config: Optional[Dict[str, Any]] = None,
        position: Optional[Dict[str, int]] = None
    ):
        """
        Initialize a workflow node.
        
        Args:
            id: Unique identifier for the node (generated if not provided)
            name: Human-readable name for the node
            node_type: Type of the node (agent, tool, etc.)
            config: Configuration parameters for the node
            position: {x, y} position for visual display
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.node_type = node_type
        self.config = config or {}
        self.position = position or {"x": 0, "y": 0}
        self.incoming_edges: List['WorkflowEdge'] = []
        self.outgoing_edges: List['WorkflowEdge'] = []
    
    def add_incoming_edge(self, edge: 'WorkflowEdge') -> None:
        """Add an incoming edge to the node."""
        self.incoming_edges.append(edge)
    
    def add_outgoing_edge(self, edge: 'WorkflowEdge') -> None:
        """Add an outgoing edge from the node."""
        self.outgoing_edges.append(edge)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the node to a dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "type": self.node_type.name,
            "config": self.config,
            "position": self.position
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowNode':
        """Create a WorkflowNode from a dictionary representation."""
        return cls(
            id=data.get("id"),
            name=data.get("name", "Unnamed Node"),
            node_type=NodeType[data.get("type", "AGENT")],
            config=data.get("config", {}),
            position=data.get("position", {"x": 0, "y": 0})
        )


class WorkflowEdge:
    """
    Represents a connection between two nodes in a workflow.
    
    An edge defines how data flows from one node to another, and can represent
    different types of connections like regular data flow, conditional branches,
    or error handling.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        source_node_id: str = "",
        target_node_id: str = "",
        edge_type: EdgeType = EdgeType.DATA,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a workflow edge.
        
        Args:
            id: Unique identifier for the edge (generated if not provided)
            source_node_id: ID of the source node
            target_node_id: ID of the target node
            edge_type: Type of the connection
            config: Configuration parameters for the edge
        """
        self.id = id or str(uuid.uuid4())
        self.source_node_id = source_node_id
        self.target_node_id = target_node_id
        self.edge_type = edge_type
        self.config = config or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the edge to a dictionary for serialization."""
        return {
            "id": self.id,
            "source": self.source_node_id,
            "target": self.target_node_id,
            "type": self.edge_type.name,
            "config": self.config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowEdge':
        """Create a WorkflowEdge from a dictionary representation."""
        return cls(
            id=data.get("id"),
            source_node_id=data.get("source", ""),
            target_node_id=data.get("target", ""),
            edge_type=EdgeType[data.get("type", "DATA")],
            config=data.get("config", {})
        )


class Workflow:
    """
    Represents a complete workflow with nodes and edges.
    
    A workflow defines a network of connected agents, tools, and control
    nodes that process data and execute tasks.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        name: str = "Unnamed Workflow",
        description: str = "",
        created_at: Optional[datetime] = None,
        updated_at: Optional[datetime] = None,
        version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a workflow.
        
        Args:
            id: Unique identifier for the workflow (generated if not provided)
            name: Human-readable name for the workflow
            description: Description of the workflow
            created_at: Creation timestamp (default: now)
            updated_at: Last update timestamp (default: now)
            version: Version of the workflow
            metadata: Additional metadata for the workflow
        """
        self.id = id or str(uuid.uuid4())
        self.name = name
        self.description = description
        self.created_at = created_at or datetime.now()
        self.updated_at = updated_at or datetime.now()
        self.version = version
        self.metadata = metadata or {}
        
        self.nodes: Dict[str, WorkflowNode] = {}
        self.edges: Dict[str, WorkflowEdge] = {}
    
    def add_node(self, node: WorkflowNode) -> WorkflowNode:
        """
        Add a node to the workflow.
        
        Args:
            node: The node to add
            
        Returns:
            The added node
        """
        self.nodes[node.id] = node
        return node
    
    def get_node(self, node_id: str) -> Optional[WorkflowNode]:
        """
        Get a node by ID.
        
        Args:
            node_id: ID of the node to get
            
        Returns:
            The node if found, None otherwise
        """
        return self.nodes.get(node_id)
    
    def remove_node(self, node_id: str) -> bool:
        """
        Remove a node from the workflow.
        
        Args:
            node_id: ID of the node to remove
            
        Returns:
            True if the node was removed, False if it wasn't found
        """
        if node_id not in self.nodes:
            return False
        
        # Remove any edges connected to this node
        self.edges = {
            edge_id: edge
            for edge_id, edge in self.edges.items()
            if edge.source_node_id != node_id and edge.target_node_id != node_id
        }
        
        # Remove the node itself
        del self.nodes[node_id]
        return True
    
    def add_edge(
        self,
        source_node_id: str,
        target_node_id: str,
        edge_type: EdgeType = EdgeType.DATA,
        config: Optional[Dict[str, Any]] = None
    ) -> Optional[WorkflowEdge]:
        """
        Add an edge connecting two nodes.
        
        Args:
            source_node_id: ID of the source node
            target_node_id: ID of the target node
            edge_type: Type of the edge
            config: Configuration parameters for the edge
            
        Returns:
            The created edge, or None if either node doesn't exist
        """
        source_node = self.nodes.get(source_node_id)
        target_node = self.nodes.get(target_node_id)
        
        if not source_node or not target_node:
            return None
        
        edge = WorkflowEdge(
            source_node_id=source_node_id,
            target_node_id=target_node_id,
            edge_type=edge_type,
            config=config or {}
        )
        
        self.edges[edge.id] = edge
        source_node.add_outgoing_edge(edge)
        target_node.add_incoming_edge(edge)
        
        return edge
    
    def get_edge(self, edge_id: str) -> Optional[WorkflowEdge]:
        """
        Get an edge by ID.
        
        Args:
            edge_id: ID of the edge to get
            
        Returns:
            The edge if found, None otherwise
        """
        return self.edges.get(edge_id)
    
    def remove_edge(self, edge_id: str) -> bool:
        """
        Remove an edge from the workflow.
        
        Args:
            edge_id: ID of the edge to remove
            
        Returns:
            True if the edge was removed, False if it wasn't found
        """
        if edge_id not in self.edges:
            return False
        
        edge = self.edges[edge_id]
        
        # Remove edge from connected nodes
        source_node = self.nodes.get(edge.source_node_id)
        target_node = self.nodes.get(edge.target_node_id)
        
        if source_node:
            source_node.outgoing_edges = [
                e for e in source_node.outgoing_edges if e.id != edge_id
            ]
        
        if target_node:
            target_node.incoming_edges = [
                e for e in target_node.incoming_edges if e.id != edge_id
            ]
        
        # Remove the edge itself
        del self.edges[edge_id]
        return True
    
    def get_start_nodes(self) -> List[WorkflowNode]:
        """
        Get all nodes that have no incoming edges (start nodes).
        
        Returns:
            List of start nodes
        """
        return [
            node for node in self.nodes.values()
            if not node.incoming_edges
        ]
    
    def get_end_nodes(self) -> List[WorkflowNode]:
        """
        Get all nodes that have no outgoing edges (end nodes).
        
        Returns:
            List of end nodes
        """
        return [
            node for node in self.nodes.values()
            if not node.outgoing_edges
        ]
    
    def validate(self) -> Tuple[bool, List[str]]:
        """
        Validate the workflow for correctness.
        
        Returns:
            (is_valid, errors) tuple
        """
        errors = []
        
        # Check for empty workflow
        if not self.nodes:
            errors.append("Workflow has no nodes")
            return False, errors
        
        # Check for orphaned nodes (no connections)
        # Router nodes are valid even if they don't have connections yet
        # Also check if this is a development/testing workflow with a force flag
        orphaned_nodes = [
            node.id for node in self.nodes.values()
            if not node.incoming_edges and not node.outgoing_edges
            and node.node_type != NodeType.ROUTER
            and node.node_type != NodeType.INPUT  # INPUT nodes can exist without incoming edges
            and node.node_type != NodeType.OUTPUT  # OUTPUT nodes can exist during construction
        ]

        if orphaned_nodes and not self.metadata.get("force_validate", False):
            # Only add as warning, not error to support in-progress workflows
            if self.metadata.get("ignore_orphaned", False):
                # Just log it but don't add to errors
                import logging
                logging.getLogger("WorkflowValidator").warning(f"Ignoring orphaned nodes: {', '.join(orphaned_nodes)}")
            else:
                errors.append(f"Orphaned nodes found: {', '.join(orphaned_nodes)}")
        
        # Check for cycles
        try:
            self._detect_cycles()
        except ValueError as e:
            errors.append(str(e))
        
        return len(errors) == 0, errors
    
    def _detect_cycles(self) -> None:
        """
        Detect cycles in the workflow graph.
        
        Raises:
            ValueError: If a cycle is detected
        """
        visited: Set[str] = set()
        path: Set[str] = set()
        
        def dfs(node_id: str) -> None:
            """Depth-first search to detect cycles."""
            if node_id in path:
                raise ValueError(f"Cycle detected involving node {node_id}")
            
            if node_id in visited:
                return
            
            visited.add(node_id)
            path.add(node_id)
            
            node = self.nodes.get(node_id)
            if node:
                for edge in node.outgoing_edges:
                    dfs(edge.target_node_id)
            
            path.remove(node_id)
        
        # Start DFS from all nodes to ensure we catch all cycles
        for node_id in self.nodes:
            if node_id not in visited:
                dfs(node_id)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the workflow to a dictionary for serialization.
        
        Returns:
            Dictionary representation of the workflow
        """
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "version": self.version,
            "metadata": self.metadata,
            "nodes": [node.to_dict() for node in self.nodes.values()],
            "edges": [edge.to_dict() for edge in self.edges.values()]
        }
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """
        Convert the workflow to a JSON string.
        
        Args:
            indent: Number of spaces for indentation (None for compact)
            
        Returns:
            JSON string representing the workflow
        """
        return json.dumps(self.to_dict(), indent=indent, default=str)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Workflow':
        """
        Create a Workflow from a dictionary representation.
        
        Args:
            data: Dictionary representation of the workflow
            
        Returns:
            Workflow instance
        """
        # Parse timestamps
        created_at = data.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at)
        
        # Create workflow instance
        workflow = cls(
            id=data.get("id"),
            name=data.get("name", "Unnamed Workflow"),
            description=data.get("description", ""),
            created_at=created_at,
            updated_at=updated_at,
            version=data.get("version", "1.0"),
            metadata=data.get("metadata", {})
        )
        
        # Add nodes
        for node_data in data.get("nodes", []):
            node = WorkflowNode.from_dict(node_data)
            workflow.nodes[node.id] = node
        
        # Add edges
        for edge_data in data.get("edges", []):
            edge = WorkflowEdge.from_dict(edge_data)
            workflow.edges[edge.id] = edge
            
            # Connect edges to nodes
            source_node = workflow.nodes.get(edge.source_node_id)
            target_node = workflow.nodes.get(edge.target_node_id)
            
            if source_node:
                source_node.add_outgoing_edge(edge)
            
            if target_node:
                target_node.add_incoming_edge(edge)
        
        return workflow
    
    @classmethod
    def from_json(cls, json_str: str) -> 'Workflow':
        """
        Create a Workflow from a JSON string.
        
        Args:
            json_str: JSON string representing the workflow
            
        Returns:
            Workflow instance
        """
        data = json.loads(json_str)
        return cls.from_dict(data)