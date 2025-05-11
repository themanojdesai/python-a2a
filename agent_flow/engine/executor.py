"""
Workflow execution engine for Agent Flow.

This module provides the execution engine for running workflows,
managing execution state, and handling message flow between nodes.
"""

import json
import time
import uuid
import logging
from datetime import datetime
from enum import Enum, auto
from typing import Dict, List, Optional, Set, Any, Union, Tuple, Callable

from ..models.workflow import (
    Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
)
from ..models.agent import AgentRegistry, AgentDefinition, AgentStatus
from ..models.tool import ToolRegistry, ToolDefinition, ToolStatus


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("WorkflowExecutor")


class ExecutionStatus(Enum):
    """Status of a workflow execution."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    CANCELED = auto()


class NodeExecutionStatus(Enum):
    """Status of a node execution."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    SKIPPED = auto()


class MessageValue:
    """
    Value object for messages passed between nodes.
    
    This represents data flowing through the workflow, including
    message content, metadata, and execution information.
    """
    
    def __init__(
        self,
        id: Optional[str] = None,
        content: Optional[Any] = None,
        content_type: str = "text",
        metadata: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None,
        source_node_id: Optional[str] = None
    ):
        """
        Initialize a message value.
        
        Args:
            id: Unique message identifier
            content: Message content (any serializable value)
            content_type: Type of the content (text, json, binary, etc.)
            metadata: Additional metadata for the message
            timestamp: Creation timestamp
            source_node_id: ID of the node that produced this message
        """
        self.id = id or str(uuid.uuid4())
        self.content = content
        self.content_type = content_type
        self.metadata = metadata or {}
        self.timestamp = timestamp or datetime.now()
        self.source_node_id = source_node_id
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "content": self.content,
            "content_type": self.content_type,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "source_node_id": self.source_node_id
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MessageValue':
        """Create from dictionary representation."""
        timestamp = data.get("timestamp")
        if isinstance(timestamp, str):
            timestamp = datetime.fromisoformat(timestamp)
        
        return cls(
            id=data.get("id"),
            content=data.get("content"),
            content_type=data.get("content_type", "text"),
            metadata=data.get("metadata", {}),
            timestamp=timestamp,
            source_node_id=data.get("source_node_id")
        )
    
    def __str__(self) -> str:
        """String representation of the message."""
        if self.content_type == "text" and isinstance(self.content, str):
            return self.content
        else:
            try:
                return json.dumps(self.content)
            except:
                return str(self.content)


class NodeExecution:
    """
    Execution state for a single node in the workflow.
    
    This tracks the execution of a node, including its inputs, outputs,
    and current status.
    """
    
    def __init__(
        self,
        node_id: str,
        input_values: Optional[Dict[str, MessageValue]] = None,
        output_value: Optional[MessageValue] = None,
        status: NodeExecutionStatus = NodeExecutionStatus.PENDING,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize a node execution.
        
        Args:
            node_id: ID of the node being executed
            input_values: Dictionary of input values keyed by source edge ID
            output_value: Output value produced by the node
            status: Current execution status
            start_time: When execution started
            end_time: When execution completed
            error_message: Error message if execution failed
        """
        self.node_id = node_id
        self.input_values = input_values or {}
        self.output_value = output_value
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.error_message = error_message
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "node_id": self.node_id,
            "input_values": {
                edge_id: value.to_dict()
                for edge_id, value in self.input_values.items()
            },
            "output_value": self.output_value.to_dict() if self.output_value else None,
            "status": self.status.name,
            "start_time": self.start_time.isoformat() if self.start_time else None,
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "error_message": self.error_message
        }


class WorkflowExecution:
    """
    Execution state for a complete workflow.
    
    This manages the execution of a workflow, tracking the state of all nodes,
    handling message flow, and maintaining execution history.
    """
    
    def __init__(
        self,
        workflow: Workflow,
        agent_registry: AgentRegistry,
        tool_registry: ToolRegistry,
        id: Optional[str] = None,
        input_data: Optional[Dict[str, Any]] = None,
        status: ExecutionStatus = ExecutionStatus.PENDING,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        error_message: Optional[str] = None
    ):
        """
        Initialize a workflow execution.
        
        Args:
            workflow: The workflow to execute
            agent_registry: Registry of available agents
            tool_registry: Registry of available tools
            id: Unique execution identifier
            input_data: Initial input data for the workflow
            status: Current execution status
            start_time: When execution started
            end_time: When execution completed
            error_message: Error message if execution failed
        """
        self.id = id or str(uuid.uuid4())
        self.workflow = workflow
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.input_data = input_data or {}
        self.status = status
        self.start_time = start_time
        self.end_time = end_time
        self.error_message = error_message
        
        # Initialize node executions
        self.node_executions: Dict[str, NodeExecution] = {
            node_id: NodeExecution(node_id)
            for node_id in workflow.nodes
        }
        
        # Queue of nodes ready to execute
        self.execution_queue: List[str] = []
        
        # Set of completed nodes
        self.completed_nodes: Set[str] = set()
        
        # Execution results
        self.results: Dict[str, Any] = {}
    
    def start(self, input_data: Optional[Dict[str, Any]] = None) -> bool:
        """
        Start the workflow execution.
        
        Args:
            input_data: Input data for the workflow
            
        Returns:
            True if execution started successfully, False otherwise
        """
        # Update input data if provided
        if input_data is not None:
            self.input_data = input_data
        
        # Initialize execution state
        self.status = ExecutionStatus.RUNNING
        self.start_time = datetime.now()
        self.completed_nodes = set()
        self.results = {}
        
        # Reset node executions
        self.node_executions = {
            node_id: NodeExecution(node_id)
            for node_id in self.workflow.nodes
        }
        
        # Find start nodes (nodes with no incoming edges)
        start_nodes = self.workflow.get_start_nodes()
        if not start_nodes:
            self.status = ExecutionStatus.FAILED
            self.error_message = "Workflow has no start nodes"
            return False
        
        # Add start nodes to execution queue
        self.execution_queue = [node.id for node in start_nodes]
        
        # If we have input data, create input messages for start nodes
        if self.input_data:
            for node in start_nodes:
                input_message = MessageValue(
                    content=self.input_data,
                    content_type="json",
                    source_node_id=None  # External input
                )
                
                # Add as input to the node execution
                node_execution = self.node_executions[node.id]
                node_execution.input_values["input"] = input_message
        
        logger.info(f"Started workflow execution {self.id}")
        return True
    
    def execute_step(self) -> bool:
        """
        Execute the next step in the workflow.
        
        Returns:
            True if a step was executed, False if execution is complete or failed
        """
        if self.status != ExecutionStatus.RUNNING:
            return False
        
        if not self.execution_queue:
            # Check if all nodes have completed
            if len(self.completed_nodes) == len(self.workflow.nodes):
                self.status = ExecutionStatus.COMPLETED
                self.end_time = datetime.now()
                logger.info(f"Workflow execution {self.id} completed successfully")
                
                # Collect results from output nodes
                for node_id, node in self.workflow.nodes.items():
                    if node.node_type == NodeType.OUTPUT and node_id in self.completed_nodes:
                        node_execution = self.node_executions[node_id]
                        if node_execution.output_value:
                            self.results[node.name] = node_execution.output_value.content
            
            return False
        
        # Get the next node to execute
        node_id = self.execution_queue.pop(0)
        node = self.workflow.nodes.get(node_id)
        
        if not node:
            logger.warning(f"Node {node_id} not found in workflow")
            return False
        
        # Get the node execution state
        node_execution = self.node_executions[node_id]
        
        # Skip if already completed
        if node_execution.status in [NodeExecutionStatus.COMPLETED, NodeExecutionStatus.FAILED]:
            return True
        
        # Check if all required inputs are available
        required_inputs = self._get_required_inputs(node)
        available_inputs = set(node_execution.input_values.keys())
        
        missing_inputs = required_inputs - available_inputs
        if missing_inputs:
            # Put back in queue for later execution
            self.execution_queue.append(node_id)
            return True
        
        # Start node execution
        node_execution.status = NodeExecutionStatus.RUNNING
        node_execution.start_time = datetime.now()
        
        try:
            # Execute the node based on its type
            self._execute_node(node, node_execution)
            
            # Mark node as completed
            node_execution.status = NodeExecutionStatus.COMPLETED
            node_execution.end_time = datetime.now()
            self.completed_nodes.add(node_id)
            
            # Queue downstream nodes
            for edge in node.outgoing_edges:
                # Skip conditional edges that don't match
                if not self._should_follow_edge(edge, node_execution.output_value):
                    continue
                
                target_node_id = edge.target_node_id
                target_node = self.workflow.nodes.get(target_node_id)
                
                if not target_node:
                    continue
                
                # Special handling for output nodes - they can receive multiple inputs
                if target_node.node_type == NodeType.OUTPUT:
                    # For output nodes, we add the input but only queue if not already queued

                    # Create a deep copy of the output value to prevent shared references
                    # NEW: Ensure we capture source information and preserve any routing metadata
                    output_copy = MessageValue(
                        id=str(uuid.uuid4()),  # Generate a new unique ID for this message
                        content=node_execution.output_value.content,
                        content_type=node_execution.output_value.content_type,
                        metadata=node_execution.output_value.metadata.copy() if node_execution.output_value.metadata else {},
                        source_node_id=node_execution.node_id  # Explicitly set the source to the current node
                    )

                    # Log the message being sent to the output node for tracking
                    logger.info(f"📨 Sending message to output node {target_node.name} from {node.name} via edge #{edge.id}")

                    # Get the target node execution
                    target_execution = self.node_executions[target_node_id]

                    # Check if output node has already received this exact edge input
                    if edge.id in target_execution.input_values:
                        # NEW: Skip this to avoid potential duplicates
                        logger.warning(f"⚠️ Output node {target_node.name} already has input from edge #{edge.id}, skipping duplicate")
                    else:
                        # NEW: Add a timestamp to the edge for tracking when it was added
                        output_copy.metadata["edge_arrival_time"] = datetime.now().isoformat()

                        # Add the input from this edge
                        target_execution.input_values[edge.id] = output_copy
                        logger.info(f"✅ Added input to output node {target_node.name} via edge #{edge.id}")

                        # Only add output node to queue if:
                        # 1. It's not already in the queue
                        # 2. It's not already completed
                        if (target_node_id not in self.execution_queue and
                            target_node_id not in self.completed_nodes):

                            # Append to execution queue if not already queued
                            self.execution_queue.append(target_node_id)
                            logger.info(f"🔄 Adding output node {target_node.name} to execution queue")

                # For non-output nodes, we use standard processing
                elif target_node_id not in self.completed_nodes:
                    # Add node to execution queue if not already there
                    if target_node_id not in self.execution_queue:
                        self.execution_queue.append(target_node_id)
                        logger.info(f"Adding node {target_node.name} to execution queue")

                    # Create a deep copy of the output value to prevent shared references
                    output_copy = MessageValue(
                        content=node_execution.output_value.content,
                        content_type=node_execution.output_value.content_type,
                        metadata=node_execution.output_value.metadata.copy() if node_execution.output_value.metadata else {},
                        source_node_id=node_execution.output_value.source_node_id
                    )

                    # Pass the copy as input to the target node
                    target_execution = self.node_executions[target_node_id]

                    # Store the input, avoiding duplicates
                    if edge.id not in target_execution.input_values:
                        target_execution.input_values[edge.id] = output_copy
                    else:
                        logger.warning(f"Skipping duplicate input for edge #{edge.id} to node {target_node.name}")
                else:
                    logger.info(f"Skipping already completed node {target_node.name}")
            
            logger.info(f"Executed node {node.name} ({node_id}) successfully")
            return True
            
        except Exception as e:
            # Handle node execution failure
            node_execution.status = NodeExecutionStatus.FAILED
            node_execution.end_time = datetime.now()
            node_execution.error_message = str(e)
            
            logger.error(f"Failed to execute node {node.name} ({node_id}): {e}")
            
            # Try to follow error edges if any
            has_error_edges = False
            for edge in node.outgoing_edges:
                if edge.edge_type == EdgeType.ERROR:
                    has_error_edges = True
                    target_node_id = edge.target_node_id
                    
                    # Add error node to execution queue
                    if target_node_id not in self.execution_queue and target_node_id not in self.completed_nodes:
                        self.execution_queue.append(target_node_id)
                    
                    # Pass error message as input
                    error_message = MessageValue(
                        content=str(e),
                        content_type="text",
                        source_node_id=node_id,
                        metadata={"error": True}
                    )
                    
                    target_execution = self.node_executions[target_node_id]
                    target_execution.input_values[edge.id] = error_message
            
            # If no error edges, propagate failure to workflow
            if not has_error_edges:
                self.status = ExecutionStatus.FAILED
                self.error_message = f"Node {node.name} failed: {e}"
                self.end_time = datetime.now()
                return False
            
            return True
    
    def execute_all(self) -> Dict[str, Any]:
        """
        Execute the workflow until completion.

        Returns:
            Dictionary of workflow results
        """
        if self.status == ExecutionStatus.PENDING:
            self.start()

        max_steps = 1000  # Safety limit
        steps = 0

        # Keep track of node execution counts to detect infinite loops
        node_execution_counts = {node_id: 0 for node_id in self.workflow.nodes}
        max_node_executions = 5  # Maximum times a single node can be executed

        # Dictionary to track UI node IDs for visual tracking
        self.ui_node_tracking = {}
        for node_id, node in self.workflow.nodes.items():
            # Store the UI node ID if it exists in the node config
            if 'ui_node_id' in node.config:
                self.ui_node_tracking[node_id] = {
                    'ui_node_id': node.config['ui_node_id'],
                    'name': node.name,
                    'status': 'PENDING'
                }

        logger.info(f"🚀 Starting execution of workflow: {self.workflow.name} ({self.id})")
        logger.info(f"📊 Total nodes to execute: {len(self.workflow.nodes)}")

        # Create a special field for tracking node execution status that can be queried externally
        self.node_execution_status = {
            node_id: {
                'id': node_id,
                'ui_node_id': self.ui_node_tracking.get(node_id, {}).get('ui_node_id', node_id),
                'name': self.workflow.nodes[node_id].name,
                'status': 'PENDING'
            }
            for node_id in self.workflow.nodes
        }

        while self.status == ExecutionStatus.RUNNING and steps < max_steps:
            next_node_id = self.execution_queue[0] if self.execution_queue else None

            # Improved infinite loop detection with special handling for output nodes
            if next_node_id:
                node = self.workflow.nodes.get(next_node_id)
                # Apply different execution limits based on node type
                type_based_max_executions = max_node_executions

                # Special case: output nodes can execute more times since they collect multiple inputs
                if node and node.node_type == NodeType.OUTPUT:
                    # Allow output nodes higher execution counts - they naturally gather multiple inputs
                    type_based_max_executions = max_node_executions * 2
                    logger.info(f"Output node {node.name} has higher execution limit: {type_based_max_executions}")

                # Check if node has exceeded its execution limit
                if node_execution_counts[next_node_id] >= type_based_max_executions:
                    node_name = self.workflow.nodes[next_node_id].name
                    node_type = self.workflow.nodes[next_node_id].node_type.name if node else "UNKNOWN"

                    logger.warning(f"⚠️ Max executions ({type_based_max_executions}) reached for {node_type} node '{node_name}'")

                    # Log detailed information about what might be causing the loop
                    node_execution = self.node_executions.get(next_node_id)
                    if node_execution and hasattr(node_execution, 'input_values'):
                        input_sources = []
                        for edge_id, message in node_execution.input_values.items():
                            source_id = message.source_node_id
                            source_name = self.workflow.nodes.get(source_id).name if source_id and source_id in self.workflow.nodes else "unknown"
                            input_sources.append(f"{source_name} (edge #{edge_id})")

                        if input_sources:
                            logger.warning(f"Node '{node_name}' has inputs from: {', '.join(input_sources)}")

                    # Mark the over-executed node as completed to break the potential loop
                    self.completed_nodes.add(next_node_id)

                    # Remove it from the execution queue if present multiple times
                    self.execution_queue = [nid for nid in self.execution_queue if nid != next_node_id]

                    # Add a warning but don't fail the workflow
                    logger.info(f"✅ Marked node '{node_name}' as completed to prevent infinite loop")

                    # Log execution counts for all nodes that executed multiple times
                    high_count_nodes = {node_id: count for node_id, count in node_execution_counts.items() if count > 1}
                    if high_count_nodes:
                        node_names = {node_id: self.workflow.nodes[node_id].name for node_id in high_count_nodes.keys()}
                        logger.warning(f"Nodes with multiple executions: {[(node_names[nid], count) for nid, count in high_count_nodes.items()]}")

                    # Skip to the next iteration without executing this node
                    continue

            if not self.execute_step():
                break

            # Increment execution count for the node we just executed
            if next_node_id:
                node_execution_counts[next_node_id] += 1

            steps += 1

            # Log execution counts periodically
            if steps % 10 == 0:
                high_count_nodes = {node_id: count for node_id, count in node_execution_counts.items() if count > 1}
                if high_count_nodes:
                    node_names = {node_id: self.workflow.nodes[node_id].name for node_id in high_count_nodes.keys()}
                    logger.warning(f"Nodes with multiple executions: {[(node_names[nid], count) for nid, count in high_count_nodes.items()]}")

        # Always collect results from ANY output nodes, even if they weren't properly completed
        # This ensures we get results even if the workflow was terminated early
        for node_id, node in self.workflow.nodes.items():
            if node.node_type == NodeType.OUTPUT:
                node_execution = self.node_executions[node_id]

                # Check if there's an output value directly
                if node_execution.output_value:
                    output_key = node.config.get("output_key", "output")
                    self.results[output_key] = node_execution.output_value.content
                    logger.info(f"💾 Collected output from completed node {node.name}: {str(self.results[output_key])[:100]}...")

                # Even if no output_value, check if there are any input values we can use
                elif node_execution.input_values:
                    # Use the first input value we find
                    for edge_id, message in node_execution.input_values.items():
                        content = message.content
                        # Extract text content if needed
                        if isinstance(content, dict) and 'content' in content:
                            content = content['content']
                        elif isinstance(content, dict) and 'text' in content:
                            content = content['text']

                        output_key = node.config.get("output_key", "output")
                        self.results[output_key] = content
                        logger.info(f"💾 Collected output from pending node {node.name} inputs: {str(self.results[output_key])[:100]}...")
                        # Just use the first available input
                        break

        if steps >= max_steps and self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.FAILED
            self.error_message = "Exceeded maximum execution steps"
            self.end_time = datetime.now()
            logger.error(f"❌ Workflow execution failed: exceeded maximum steps ({max_steps})")
        elif self.status == ExecutionStatus.COMPLETED:
            logger.info(f"✨ Workflow execution completed successfully in {steps} steps")
            # Mark all remaining nodes as COMPLETED or SKIPPED
            for node_id, status in self.node_execution_status.items():
                if status['status'] == 'PENDING':
                    status['status'] = 'SKIPPED'
        elif self.status == ExecutionStatus.FAILED:
            logger.error(f"❌ Workflow execution failed: {self.error_message}")
            # If failure was due to infinite loop, include any results we got so far
            if "infinite loop" in self.error_message.lower():
                logger.info("Collecting partial results despite infinite loop detection")

        # Log the final results
        if self.results:
            logger.info(f"Final workflow results: {', '.join(self.results.keys())}")
        else:
            logger.warning("No results were produced by any output nodes")

        logger.info(f"Workflow execution completed with status {self.status.name}")
        return self.results
    
    def cancel(self) -> None:
        """Cancel the workflow execution."""
        if self.status == ExecutionStatus.RUNNING:
            self.status = ExecutionStatus.CANCELED
            self.end_time = datetime.now()
            logger.info(f"Workflow execution {self.id} canceled")
    
    def _get_required_inputs(self, node: WorkflowNode) -> Set[str]:
        """
        Get the set of required input edge IDs for a node.
        
        Args:
            node: The node to check
            
        Returns:
            Set of edge IDs that are required inputs
        """
        # By default, we need all incoming edges
        required_inputs = {edge.id for edge in node.incoming_edges}
        
        # For conditional nodes, not all inputs may be required
        if node.node_type == NodeType.CONDITIONAL:
            # Conditional nodes typically have a config specifying which inputs are required
            required_input_ids = node.config.get("required_inputs", [])
            if required_input_ids:
                required_inputs = {
                    edge.id for edge in node.incoming_edges
                    if edge.id in required_input_ids
                }
        
        return required_inputs
    
    def _should_follow_edge(self, edge: WorkflowEdge, output_value: Optional[MessageValue]) -> bool:
        """
        Determine if an outgoing edge should be followed based on the output.

        Args:
            edge: The edge to check
            output_value: The output value from the source node

        Returns:
            True if the edge should be followed, False otherwise
        """
        # Regular data edges are always followed
        if edge.edge_type == EdgeType.DATA:
            return True

        # Success edges are followed if execution was successful
        if edge.edge_type == EdgeType.SUCCESS:
            return True

        # Error edges are followed only when handling failures (done elsewhere)
        if edge.edge_type == EdgeType.ERROR:
            return False

        # For conditional edges, evaluate the condition
        if edge.edge_type in [EdgeType.CONDITION_TRUE, EdgeType.CONDITION_FALSE]:
            if not output_value:
                return False

            condition_result = self._evaluate_condition(edge.config, output_value)

            # Condition_TRUE edge is followed if condition is true
            if edge.edge_type == EdgeType.CONDITION_TRUE:
                return condition_result

            # Condition_FALSE edge is followed if condition is false
            return not condition_result

        # For router output edges, check if this is the selected port
        if edge.edge_type == EdgeType.ROUTE_OUTPUT:
            # Enhanced router edge validation with comprehensive logging

            # STEP 1: Validate output_value exists and has metadata
            if not output_value:
                logger.warning(f"⚠️ Router edge check failed: No output value for edge #{edge.id}")
                return False

            if not hasattr(output_value, 'metadata') or not output_value.metadata:
                logger.warning(f"⚠️ Router edge check failed: Missing metadata for edge #{edge.id}")
                return False

            # STEP 2: Get and validate the edge port number with clear error handling
            try:
                edge_port = int(edge.config.get("port_number", -1))
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Router edge has invalid port: {edge.config.get('port_number')} for edge #{edge.id}")
                edge_port = -1

            if edge_port < 0:
                logger.warning(f"⚠️ Edge #{edge.id} has no valid port number configuration: {edge.config}")
                return False

            # STEP 3: Get and validate the selected port in message metadata
            try:
                # First look specifically for a numeric selected_port
                if "selected_port" in output_value.metadata:
                    selected_port = int(output_value.metadata.get("selected_port"))
                else:
                    logger.warning(f"⚠️ No 'selected_port' key in metadata for edge #{edge.id}: {output_value.metadata}")
                    selected_port = -1
            except (ValueError, TypeError):
                logger.warning(f"⚠️ Invalid selected port value: {output_value.metadata.get('selected_port')} for edge #{edge.id}")
                selected_port = -1

            # Valid port numbers must be non-negative
            if selected_port < 0:
                logger.warning(f"⚠️ No valid selected port in metadata for edge #{edge.id}: {output_value.metadata}")
                return False

            # STEP 4: Perform exact matching between edge port and selected port
            is_match = (edge_port == selected_port)

            # Add detailed logging with router node info for easier diagnosis
            router_node_id = output_value.metadata.get("router_node_id", "unknown")
            port_name = output_value.metadata.get("port_name", f"Output {selected_port+1}")
            router_timestamp = output_value.metadata.get("router_timestamp", "")

            # Show full context in logs
            logger.info(f"🔍 ROUTER CHECK - Edge #{edge.id}: PORT {edge_port} ↔️ SELECTED {selected_port} [{port_name}] = {'✅' if is_match else '❌'}")
            logger.info(f"🧠 ROUTER CONTEXT - Router: {router_node_id} | Strategy: {output_value.metadata.get('routing_strategy', 'unknown')} | Timestamp: {router_timestamp}")

            if is_match:
                logger.info(f"✅ FOLLOWING EDGE #{edge.id} - Matched port {edge_port}")
            else:
                logger.info(f"❌ SKIPPING EDGE #{edge.id} - Port {edge_port} does not match selected port {selected_port}")

            # Return the exact match result
            return is_match

        return True
    
    def _evaluate_condition(self, condition_config: Dict[str, Any], value: MessageValue) -> bool:
        """
        Evaluate a condition on a message value.
        
        Args:
            condition_config: Configuration for the condition
            value: The value to check the condition against
            
        Returns:
            True if the condition is met, False otherwise
        """
        condition_type = condition_config.get("type", "contains")
        target = condition_config.get("target", "")
        
        # Get the content to check
        content = value.content
        if isinstance(content, dict) and "text" in content:
            content = content["text"]
        
        if not isinstance(content, str):
            try:
                content = str(content)
            except:
                return False
        
        # Evaluate based on condition type
        if condition_type == "contains":
            return target in content
        
        elif condition_type == "equals":
            return content == target
        
        elif condition_type == "starts_with":
            return content.startswith(target)
        
        elif condition_type == "ends_with":
            return content.endswith(target)
        
        elif condition_type == "regex":
            import re
            try:
                return bool(re.search(target, content))
            except:
                return False
        
        return False
    
    def _execute_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """
        Execute a single node.
        
        Args:
            node: The node to execute
            execution: The node execution state
            
        Raises:
            Exception: If node execution fails
        """
        # Log which node is currently executing with more visibility
        logger.info(f"⚙️ Executing node: {node.name} ({node.id}) of type {node.node_type.name}")
        
        # Update node execution status for UI tracking
        if hasattr(self, 'node_execution_status') and node.id in self.node_execution_status:
            self.node_execution_status[node.id]['status'] = 'RUNNING'
            
            # Store additional info that might be helpful for the UI
            self.node_execution_status[node.id]['start_time'] = datetime.now().isoformat()
            self.node_execution_status[node.id]['type'] = node.node_type.name
        
        try:
            # Execute based on node type
            if node.node_type == NodeType.AGENT:
                self._execute_agent_node(node, execution)
            
            elif node.node_type == NodeType.TOOL:
                self._execute_tool_node(node, execution)
            
            elif node.node_type == NodeType.INPUT:
                self._execute_input_node(node, execution)
            
            elif node.node_type == NodeType.OUTPUT:
                self._execute_output_node(node, execution)
            
            elif node.node_type == NodeType.CONDITIONAL:
                self._execute_conditional_node(node, execution)
            
            elif node.node_type == NodeType.TRANSFORM:
                self._execute_transform_node(node, execution)

            elif node.node_type == NodeType.ROUTER:
                self._execute_router_node(node, execution)

            else:
                raise ValueError(f"Unsupported node type: {node.node_type}")
            
            # Log when node execution is complete
            logger.info(f"✅ Completed node: {node.name} ({node.id})")
            
            # Update node execution status for UI tracking
            if hasattr(self, 'node_execution_status') and node.id in self.node_execution_status:
                self.node_execution_status[node.id]['status'] = 'COMPLETED'
                self.node_execution_status[node.id]['end_time'] = datetime.now().isoformat()
        
        except Exception as e:
            # Update node execution status for UI tracking
            if hasattr(self, 'node_execution_status') and node.id in self.node_execution_status:
                self.node_execution_status[node.id]['status'] = 'FAILED'
                self.node_execution_status[node.id]['end_time'] = datetime.now().isoformat()
                self.node_execution_status[node.id]['error'] = str(e)
            
            # Re-raise the exception so it's handled by the caller
            raise
    
    def _execute_agent_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """Execute an agent node."""
        # Get the agent configuration
        agent_id = node.config.get("agent_id")
        if not agent_id:
            raise ValueError(f"Agent node {node.id} is missing agent_id configuration")
        
        # Get the agent from registry
        agent = self.agent_registry.get(agent_id)
        if not agent:
            raise ValueError(f"Agent with ID {agent_id} not found in registry")
        
        # Ensure agent is connected
        if agent.status != AgentStatus.CONNECTED:
            if not agent.connect():
                raise RuntimeError(f"Failed to connect to agent: {agent.error_message}")
        
        # Get the input message to send
        input_message = None
        for edge_id, message in execution.input_values.items():
            # Just use the first available message for now
            # More sophisticated input handling would be needed for multiple inputs
            input_message = message
            break

        if not input_message:
            raise ValueError("No input message available for agent node")

        # Prepare proper A2A message content
        from python_a2a.models import Message, TextContent, MessageRole

        # Extract content from our internal message format
        content = input_message.content

        # Convert to proper A2A message
        a2a_message = None

        # Determine if we need to construct a structured Message object
        if isinstance(content, str):
            # Simple text content
            a2a_message = Message(
                content=TextContent(text=content),
                role=MessageRole.USER
            )
        elif isinstance(content, dict) and 'text' in content:
            # Already has text field
            a2a_message = Message(
                content=TextContent(text=content['text']),
                role=MessageRole.USER
            )
        elif isinstance(content, dict) and 'content' in content:
            # Nested content
            text_content = content['content']
            if isinstance(text_content, dict) and 'text' in text_content:
                text_content = text_content['text']
            elif not isinstance(text_content, str):
                text_content = str(text_content)

            a2a_message = Message(
                content=TextContent(text=text_content),
                role=MessageRole.USER
            )
        else:
            # Fallback to converting whatever we have to string
            a2a_message = Message(
                content=TextContent(text=str(content)),
                role=MessageRole.USER
            )

        # Preserve metadata from original message if needed
        if input_message.metadata:
            # Only copy metadata that would be valid in A2A protocol
            # This prevents future issues with metadata handling
            if 'conversation_id' in input_message.metadata:
                a2a_message.conversation_id = input_message.metadata['conversation_id']

            # You could add more metadata processing here as needed

        logger.info(f"Sending message to agent {agent.name} ({agent_id})")

        # Send the properly formatted A2A message to the agent
        response = agent.send_message(a2a_message)
        if response is None:
            raise RuntimeError(f"Agent request failed: {agent.error_message}")

        # Process the A2A response correctly
        logger.info(f"💬 Agent response received from {agent.name}")

        # Extract content from A2A response based on the response structure
        cleaned_response = None
        content_type = "text"

        if hasattr(response, 'content'):
            if hasattr(response.content, 'text'):
                # Standard A2A text content
                cleaned_response = response.content.text
            elif isinstance(response.content, dict) and 'text' in response.content:
                # Dict with text field
                cleaned_response = response.content['text']
            else:
                # Use whatever content we got
                cleaned_response = response.content
                # Try to determine content type
                if isinstance(response.content, dict):
                    content_type = "json"
        else:
            # Fallback for non-standard responses
            cleaned_response = response

        # Create our internal message representation
        output_message = MessageValue(
            content=cleaned_response,
            content_type=content_type,
            source_node_id=node.id,
            metadata={
                "agent_id": agent_id,
                "agent_name": agent.name
            }
        )
        
        execution.output_value = output_message
    
    def _execute_tool_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """Execute a tool node."""
        # Get the tool configuration
        tool_id = node.config.get("tool_id")
        if not tool_id:
            raise ValueError(f"Tool node {node.id} is missing tool_id configuration")
        
        # Get the tool from registry
        tool = self.tool_registry.get(tool_id)
        if not tool:
            raise ValueError(f"Tool with ID {tool_id} not found in registry")
        
        # Check tool availability
        if not tool.check_availability():
            raise RuntimeError(f"Tool is not available: {tool.error_message}")
        
        # Get the input parameters from node configuration and inputs
        parameters = node.config.get("parameters", {}).copy()
        
        # Parse inputs to override or add parameters
        for edge_id, message in execution.input_values.items():
            content = message.content
            
            # If content is JSON-formatted, extract parameters
            if isinstance(content, dict):
                parameters.update(content)
            elif isinstance(content, str):
                # Try to parse as JSON
                try:
                    parsed = json.loads(content)
                    if isinstance(parsed, dict):
                        parameters.update(parsed)
                except:
                    # Not JSON, use as a single parameter if configured
                    param_name = node.config.get("input_parameter")
                    if param_name:
                        parameters[param_name] = content
        
        # Execute the tool
        result = tool.execute(parameters)
        
        # Create output message
        output_message = MessageValue(
            content=result,
            content_type="json",
            source_node_id=node.id,
            metadata={"tool_id": tool_id}
        )
        
        execution.output_value = output_message
    
    def _execute_input_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """Execute an input node."""
        # Input nodes simply pass through input data or use configured default
        input_key = node.config.get("input_key")
        default_value = node.config.get("default_value")
        
        # Look for input in execution inputs or workflow inputs
        value = None
        
        if input_key and self.input_data:
            value = self.input_data.get(input_key)
        
        # Check for direct inputs
        if not value:
            for edge_id, message in execution.input_values.items():
                value = message.content
                break
        
        # Use default if no value found
        if value is None:
            value = default_value
        
        # Create output message
        output_message = MessageValue(
            content=value,
            content_type="text" if isinstance(value, str) else "json",
            source_node_id=node.id
        )
        
        execution.output_value = output_message
    
    def _execute_output_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """Execute an output node."""
        # Output nodes collect input and store it as a result
        output_key = node.config.get("output_key", "output")

        # Log total number of inputs available for debugging
        logger.info(f"📊 Output node {node.name} has {len(execution.input_values)} inputs")

        # Get input message - use the most recent one based on metadata timestamp
        input_message = None
        latest_timestamp = None

        # First try to find an input with the edge_arrival_time in metadata
        for edge_id, message in execution.input_values.items():
            arrival_time = message.metadata.get("edge_arrival_time") if message.metadata else None

            if arrival_time:
                current_time = arrival_time
                if latest_timestamp is None or current_time > latest_timestamp:
                    latest_timestamp = current_time
                    input_message = message
                    logger.info(f"📌 Selected input from edge #{edge_id} with timestamp {current_time}")

        # If no message with timestamp was found, just use the first one
        if not input_message:
            for edge_id, message in execution.input_values.items():
                input_message = message
                logger.info(f"📌 Selected first available input from edge #{edge_id}")
                break

        if not input_message:
            raise ValueError("No input message available for output node")

        # Get the content and ensure it's in a clean format
        content = input_message.content

        # Extract text content if needed
        if isinstance(content, dict) and 'content' in content:
            # Handle nested content structure
            content = content['content']
        elif isinstance(content, dict) and 'text' in content:
            # Handle text field directly
            content = content['text']

        # Log the output
        logger.info(f"📤 Output node ({node.name}) received: {str(content)[:100]}...")

        # CRITICAL: Store the result with clear logging
        self.results[output_key] = content
        logger.info(f"💾 Stored result in self.results[{output_key}] = {str(content)[:100]}...")

        # Create a new message with cleaned content to avoid reference issues
        output_message = MessageValue(
            content=content,
            content_type=input_message.content_type,
            # NEW: Don't pass along any router metadata to avoid confusion
            metadata={"is_final_output": True, "output_key": output_key},
            source_node_id=node.id
        )

        # IMPORTANT: Clear the input values to prevent reprocessing the same messages
        execution.input_values.clear()

        # Set as the node's output
        execution.output_value = output_message

        # Log the final output for debugging
        logger.info(f"🏁 Final output from node {node.name}: {str(content)[:100]}...")
    
    def _execute_conditional_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """Execute a conditional node."""
        # Conditional nodes evaluate a condition and output true/false
        condition_type = node.config.get("condition_type", "always")
        condition_value = node.config.get("condition_value")
        
        # Get input message
        input_message = None
        for edge_id, message in execution.input_values.items():
            # Just use the first available message for now
            input_message = message
            break
        
        if not input_message and condition_type != "always":
            raise ValueError("No input message available for conditional node")
        
        # Evaluate the condition
        result = False
        
        if condition_type == "always":
            # Always true condition
            result = True
        
        elif condition_type == "contains":
            # Check if input contains a value
            content = str(input_message.content)
            result = condition_value in content
        
        elif condition_type == "equals":
            # Check if input equals a value
            content = input_message.content
            result = content == condition_value
        
        elif condition_type == "javascript":
            # Evaluate a JavaScript expression (simple implementation)
            try:
                # Replace placeholders in the expression
                expr = condition_value
                if input_message:
                    content = input_message.content
                    if isinstance(content, str):
                        expr = expr.replace("$input", json.dumps(content))
                    else:
                        expr = expr.replace("$input", json.dumps(content))
                
                # Very basic evaluation (CAUTION: Not secure for production)
                # A real implementation would use a proper JS engine or safe eval
                result = bool(eval(expr))
            except:
                result = False
        
        # Create output message
        output_message = MessageValue(
            content=result,
            content_type="boolean",
            source_node_id=node.id
        )
        
        execution.output_value = output_message
    
    def _execute_transform_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """Execute a transform node."""
        # Transform nodes modify input data based on transformation type
        transform_type = node.config.get("transform_type", "passthrough")
        transform_config = node.config.get("transform_config", {})

        # Get input message
        input_message = None
        for edge_id, message in execution.input_values.items():
            # Just use the first available message for now
            input_message = message
            break

        if not input_message:
            raise ValueError("No input message available for transform node")

        # Apply the transformation
        result = input_message.content

        if transform_type == "passthrough":
            # Pass the input through unchanged
            pass

        elif transform_type == "extract":
            # Extract a specific field from the input
            field_path = transform_config.get("field_path", "")
            if not field_path:
                # No field specified, return the whole content
                pass
            else:
                # Parse field path
                parts = field_path.split(".")
                temp = result

                try:
                    for part in parts:
                        if isinstance(temp, dict):
                            temp = temp.get(part)
                        elif isinstance(temp, list) and part.isdigit():
                            index = int(part)
                            if 0 <= index < len(temp):
                                temp = temp[index]
                            else:
                                temp = None
                                break
                        else:
                            temp = None
                            break

                    result = temp
                except:
                    result = None

        elif transform_type == "template":
            # Apply a text template with placeholders
            template = transform_config.get("template", "${input}")

            # Very simple placeholder replacement
            # A real implementation would use a proper template engine
            if isinstance(template, str):
                # Replace ${input} with the input content
                try:
                    input_str = str(input_message.content)
                    result = template.replace("${input}", input_str)
                except:
                    result = template

        elif transform_type == "json":
            # Convert to JSON format
            try:
                if isinstance(result, str):
                    # Try to parse as JSON
                    result = json.loads(result)
                else:
                    # Make sure it's serializable
                    result = json.loads(json.dumps(result))
            except:
                # If conversion fails, return the input as-is
                pass

        # Create output message
        output_message = MessageValue(
            content=result,
            content_type="text" if isinstance(result, str) else "json",
            source_node_id=node.id
        )

        execution.output_value = output_message

    def _execute_router_node(self, node: WorkflowNode, execution: NodeExecution) -> None:
        """
        Execute a router node to direct messages to different output ports.

        This implementation has been rewritten to be more robust and reliable,
        ensuring that the router correctly sets its selected port in the metadata
        and properly propagates this information downstream.
        """
        # STEP 1: Extract the input message (always use the first available message)
        input_message = None
        for edge_id, message in execution.input_values.items():
            input_message = message
            break

        # Handle missing input with a clear default
        if not input_message:
            logger.warning(f"Router node {node.name} ({node.id}) has no input message, using default")
            input_message = MessageValue(
                content="No input message",
                content_type="text",
                source_node_id=None
            )

        # STEP 2: Extract configuration with clear defaults
        # Strategy and default port with normalized forms
        routing_strategy = node.config.get("routingStrategy")
        if routing_strategy is None:
            routing_strategy = node.config.get("routing_strategy", "keyword")

        # Ensure we have an integer default_output
        try:
            default_output = int(node.config.get("default_output", 0))
        except (ValueError, TypeError):
            default_output = 0

        # Ensure we have an integer output_ports count
        try:
            output_ports = int(node.config.get("outputPorts", node.config.get("output_ports", 2)))
        except (ValueError, TypeError):
            output_ports = 2

        # STEP 3: Normalize the content for routing
        content = input_message.content
        if isinstance(content, dict) and "text" in content:
            content = content["text"]
        if not isinstance(content, str):
            content = str(content)

        # STEP 4: Route based on strategy (with clean function isolation)
        # Log configuration for debugging
        logger.info(f"Router {node.name}: strategy={routing_strategy}, output_ports={output_ports}")

        # Initial selected port is the default (safe fallback)
        selected_port = default_output

        # Apply routing strategy
        if routing_strategy == "keyword":
            # Extract patterns with clear defaults
            patterns = node.config.get("keywordPatterns", [])
            if not patterns:
                logger.warning(f"Router {node.name}: No keyword patterns found, using default port {default_output}")
            else:
                # Log patterns for debugging
                logger.info(f"Router {node.name}: keyword patterns = {patterns}")

                # Simple loop through patterns for matching
                for pattern in patterns:
                    keyword = pattern.get("keyword", "")
                    port = pattern.get("port", default_output)

                    # Skip empty patterns
                    if not keyword:
                        continue

                    # Direct string matching (most robust approach)
                    if keyword.lower() in content.lower():
                        try:
                            selected_port = int(port)
                            logger.info(f"Router {node.name}: matched keyword '{keyword}', selected port {selected_port}")
                            break  # Stop after first match
                        except (ValueError, TypeError):
                            logger.warning(f"Router {node.name}: Invalid port number {port} for keyword {keyword}")

        elif routing_strategy == "random":
            # Simple random port selection
            import random
            try:
                selected_port = random.randint(0, output_ports - 1)
                logger.info(f"Router {node.name}: randomly selected port {selected_port}")
            except Exception as e:
                logger.error(f"Router {node.name}: Error in random routing: {e}")
                selected_port = default_output

        elif routing_strategy == "content-type" or routing_strategy == "content_type":
            # Get content type mappings
            mappings = node.config.get("contentTypeMappings", [])
            content_type = input_message.content_type.lower()

            if not mappings:
                logger.warning(f"Router {node.name}: No content-type mappings found")
            else:
                # Log patterns for debugging
                logger.info(f"Router {node.name}: content-type mappings = {mappings}")

                # Simple loop through mappings
                for mapping in mappings:
                    mapping_type = mapping.get("contentType", "").lower()
                    port = mapping.get("port", default_output)

                    if content_type == mapping_type:
                        try:
                            selected_port = int(port)
                            logger.info(f"Router {node.name}: matched content-type '{content_type}', selected port {selected_port}")
                            break
                        except (ValueError, TypeError):
                            logger.warning(f"Router {node.name}: Invalid port number {port} for content-type {mapping_type}")

        elif routing_strategy == "ai":
            # AI-based routing is more complex, handle separately
            try:
                api_key = node.config.get("apiKey")
                if not api_key:
                    logger.warning(f"Router {node.name}: No API key for AI routing, using default port")
                else:
                    # Implement minimal AI routing (just the core functionality)
                    from python_a2a.client.llm import OpenAIA2AClient
                    from python_a2a.models import Message, TextContent, MessageRole

                    prompt = f"You are a message router. Choose the best output port (0 to {output_ports-1}) for this message: '{content}'. Respond ONLY with the port number."

                    client = OpenAIA2AClient(
                        api_key=api_key,
                        model=node.config.get("model", "gpt-3.5-turbo"),
                        temperature=0.0
                    )

                    message = Message(
                        content=TextContent(text=prompt),
                        role=MessageRole.USER
                    )

                    response = client.send_message(message)
                    response_text = response.content.text if hasattr(response.content, "text") else str(response.content)

                    # Extract port number using regex
                    import re
                    port_match = re.search(r'\b(\d+)\b', response_text)
                    if port_match:
                        try:
                            port_num = int(port_match.group(1))
                            if 0 <= port_num < output_ports:
                                selected_port = port_num
                                logger.info(f"Router {node.name}: AI selected port {selected_port}")
                        except (ValueError, TypeError):
                            pass
            except Exception as e:
                logger.error(f"Router {node.name}: Error in AI routing: {e}")

        # STEP 5: Ensure selected_port is in valid range
        if not (0 <= selected_port < output_ports):
            logger.warning(f"Router {node.name}: Selected port {selected_port} out of range, using default {default_output}")
            selected_port = default_output

        # Log the final selection clearly
        logger.info(f"Router {node.name}: FINAL SELECTION = port {selected_port} (Output {selected_port + 1})")

        # STEP 6: Create the output message with routing metadata
        # NEW: Create a completely fresh metadata dictionary to avoid reference issues
        metadata = {
            "router_node_id": node.id,
            "selected_port": selected_port,  # Store as integer
            "port_name": f"Output {selected_port + 1}",
            "routing_strategy": routing_strategy,
            "router_timestamp": datetime.now().isoformat()  # Add timestamp for uniqueness
        }

        # Create a fresh output message with new metadata
        output_message = MessageValue(
            content=content,
            content_type=input_message.content_type,
            metadata=metadata,  # Use the completely fresh metadata
            source_node_id=node.id
        )

        # Log the metadata with the selected port for debugging
        logger.info(f"Router {node.name}: Output metadata = {metadata}")

        # Set as the node's output
        execution.output_value = output_message

    def _route_using_ai(self, content, route_config, output_ports, default_output):
        """Route messages using AI-based classification."""
        try:
            # Get AI configuration
            provider = route_config.get("provider", "openai")
            api_key = route_config.get("api_key", "")
            model = route_config.get("model", "")
            system_prompt = route_config.get(
                "system_prompt",
                "You are a message router. Your task is to analyze the message and determine "
                "which category it belongs to. Respond with just the category number."
            )

            # If port options exist, add them to the prompt
            port_descriptions = []

            # Handle case where output_ports is just a count
            if isinstance(output_ports, int):
                num_ports = output_ports
                for i in range(num_ports):
                    port_descriptions.append(f"{i}: Output {i+1}")
            else:
                # This shouldn't happen with the new implementation, but keeping for robustness
                for i, port in enumerate(output_ports):
                    if isinstance(port, dict):
                        port_descriptions.append(f"{i}: {port.get('name', f'Port {i}')} - {port.get('description', 'No description')}")
                    else:
                        port_descriptions.append(f"{i}: Output {i+1}")

            port_options = "\n".join(port_descriptions)

            # If API key is not provided, fall back to keyword routing
            if not api_key:
                logger.warning("AI routing missing API key, falling back to keyword routing")
                return self._route_using_keywords(content, route_config, output_ports, default_output)

            # Call appropriate AI service based on provider
            if provider == "openai":
                # Import here to avoid dependency issues if OpenAI is not available
                try:
                    from python_a2a.client.llm import OpenAIA2AClient
                    from python_a2a.models import Message, TextContent, MessageRole

                    # Create OpenAI client
                    client = OpenAIA2AClient(
                        api_key=api_key,
                        model=model or "gpt-3.5-turbo",
                        temperature=0.0,  # Use deterministic responses for routing
                        system_prompt=f"{system_prompt}\n\nOptions:\n{port_options}\n\nRespond with ONLY the option number."
                    )

                    # Create message
                    message = Message(
                        content=TextContent(text=content),
                        role=MessageRole.USER
                    )

                    # Get response
                    response = client.send_message(message)
                    response_text = response.content.text if hasattr(response.content, "text") else str(response.content)

                    # Extract the port number from the response
                    import re
                    port_match = re.search(r'\b(\d+)\b', response_text)
                    if port_match:
                        try:
                            port_num = int(port_match.group(1))
                            max_ports = output_ports if isinstance(output_ports, int) else len(output_ports)
                            if 0 <= port_num < max_ports:
                                return int(port_num)
                        except (ValueError, TypeError):
                            logger.error(f"Failed to convert port number to integer: {port_match.group(1)}")
                            return int(default_output)

                except Exception as e:
                    logger.error(f"Error in AI routing: {e}")

            elif provider == "anthropic":
                # Add Anthropic (Claude) support
                try:
                    from python_a2a.client.llm import AnthropicA2AClient
                    from python_a2a.models import Message, TextContent, MessageRole

                    # Create Anthropic client
                    client = AnthropicA2AClient(
                        api_key=api_key,
                        model=model or "claude-3-opus-20240229",
                        temperature=0.0,  # Use deterministic responses for routing
                        system_prompt=f"{system_prompt}\n\nOptions:\n{port_options}\n\nRespond with ONLY the option number."
                    )

                    # Create message
                    message = Message(
                        content=TextContent(text=content),
                        role=MessageRole.USER
                    )

                    # Get response
                    response = client.send_message(message)
                    response_text = response.content.text if hasattr(response.content, "text") else str(response.content)

                    # Extract the port number from the response
                    import re
                    port_match = re.search(r'\b(\d+)\b', response_text)
                    if port_match:
                        try:
                            port_num = int(port_match.group(1))
                            max_ports = output_ports if isinstance(output_ports, int) else len(output_ports)
                            if 0 <= port_num < max_ports:
                                return int(port_num)
                        except (ValueError, TypeError):
                            logger.error(f"Failed to convert port number to integer: {port_match.group(1)}")
                            return int(default_output)

                except Exception as e:
                    logger.error(f"Error in AI routing: {e}")

            # If AI routing fails or isn't implemented for the provider, fall back to keyword routing
            logger.warning(f"AI routing with provider {provider} failed, falling back to keyword routing")
            return self._route_using_keywords(content, route_config, output_ports, default_output)

        except Exception as e:
            logger.error(f"Error in AI routing: {e}")
            try:
                return int(default_output)
            except (ValueError, TypeError):
                return 0

    def _route_using_keywords(self, content, route_config, output_ports, default_output):
        """Route messages based on keyword matching."""
        try:
            # Get patterns from route config
            patterns = route_config.get("patterns", [])

            # Check each pattern
            import re
            for pattern in patterns:
                keyword = pattern.get("keyword", "")
                port = pattern.get("port", 0)

                # Skip empty keywords
                if not keyword:
                    continue

                # Try as regex first
                try:
                    if re.search(keyword, content, re.IGNORECASE):
                        try:
                            return int(port)
                        except (ValueError, TypeError):
                            logger.error(f"Failed to convert port number to integer: {port}")
                            continue
                except:
                    # If not a valid regex, do direct string matching
                    if keyword.lower() in content.lower():
                        try:
                            return int(port)
                        except (ValueError, TypeError):
                            logger.error(f"Failed to convert port number to integer: {port}")
                            continue

            # No matches, return default
            try:
                return int(default_output)
            except (ValueError, TypeError):
                logger.error(f"Failed to convert default output to integer: {default_output}")
                return 0

        except Exception as e:
            logger.error(f"Error in keyword routing: {e}")
            try:
                return int(default_output)
            except (ValueError, TypeError):
                return 0

    def _route_randomly(self, route_config, output_ports, default_output):
        """Route messages randomly based on weights."""
        try:
            import random

            # Get weights from route config
            weights_dict = route_config.get("weights", {})

            # Convert integer keys (which could be strings after serialization)
            weights = {}
            for k, v in weights_dict.items():
                try:
                    port = int(k)
                    weights[port] = float(v)
                except (ValueError, TypeError):
                    continue

            # If no weights, create equal weights for all ports
            if not weights:
                if isinstance(output_ports, int):
                    # output_ports is a number
                    for i in range(output_ports):
                        weights[i] = 1.0
                else:
                    # Shouldn't get here if output_ports is a number
                    try:
                        return int(default_output)
                    except (ValueError, TypeError):
                        return 0

            # Convert to list format for random.choices
            ports = list(weights.keys())
            weight_values = [weights[p] for p in ports]

            # If no valid weights, return default port
            if not weight_values or sum(weight_values) <= 0:
                try:
                    return int(default_output)
                except (ValueError, TypeError):
                    return 0

            # Make random weighted selection
            selected_port = random.choices(ports, weights=weight_values, k=1)[0]
            # Make sure we return an integer
            try:
                return int(selected_port)
            except (ValueError, TypeError):
                logger.error(f"Failed to convert selected port to integer: {selected_port}")
                try:
                    return int(default_output)
                except (ValueError, TypeError):
                    return 0

        except Exception as e:
            logger.error(f"Error in random routing: {e}")
            try:
                return int(default_output)
            except (ValueError, TypeError):
                return 0

    def _route_by_content_type(self, message, route_config, output_ports, default_output):
        """Route messages based on content type."""
        try:
            # Get content type of the message
            content_type = message.content_type.lower()

            # Get content type mappings from route config
            mappings = route_config.get("content_types", [])

            # Check each mapping
            for mapping in mappings:
                mapping_type = mapping.get("contentType", "").lower()
                port = mapping.get("port", 0)

                # Skip empty content types
                if not mapping_type:
                    continue

                # If content type matches, route to that port
                if content_type == mapping_type:
                    try:
                        return int(port)
                    except (ValueError, TypeError):
                        logger.error(f"Failed to convert port number to integer: {port}")
                        continue

            # No matches, return default
            try:
                return int(default_output)
            except (ValueError, TypeError):
                logger.error(f"Failed to convert default output to integer: {default_output}")
                return 0

        except Exception as e:
            logger.error(f"Error in content type routing: {e}")
            try:
                return int(default_output)
            except (ValueError, TypeError):
                return 0


class WorkflowExecutor:
    """
    Manager for executing workflows.
    
    The executor manages workflow executions, maintaining a registry of
    running workflows and providing methods to start, monitor, and control
    workflow executions.
    """
    
    def __init__(
        self,
        agent_registry: AgentRegistry,
        tool_registry: ToolRegistry
    ):
        """
        Initialize a workflow executor.
        
        Args:
            agent_registry: Registry of available agents
            tool_registry: Registry of available tools
        """
        self.agent_registry = agent_registry
        self.tool_registry = tool_registry
        self.executions: Dict[str, WorkflowExecution] = {}
    
    def execute_workflow(
        self,
        workflow: Workflow,
        input_data: Optional[Dict[str, Any]] = None,
        wait: bool = True
    ) -> Union[str, Dict[str, Any]]:
        """
        Execute a workflow.
        
        Args:
            workflow: The workflow to execute
            input_data: Input data for the workflow
            wait: If True, wait for execution to complete; if False, return execution ID
            
        Returns:
            If wait=True, returns the execution results
            If wait=False, returns the execution ID
        """
        # Validate the workflow
        valid, errors = workflow.validate()
        if not valid:
            raise ValueError(f"Invalid workflow: {', '.join(errors)}")
        
        # Create execution
        execution = WorkflowExecution(
            workflow=workflow,
            agent_registry=self.agent_registry,
            tool_registry=self.tool_registry,
            input_data=input_data
        )
        
        # Store execution
        self.executions[execution.id] = execution
        
        # Start execution
        if not execution.start():
            raise RuntimeError(f"Failed to start workflow: {execution.error_message}")
        
        if wait:
            # Execute until completion
            result = execution.execute_all()
            return result
        else:
            # Return execution ID for later monitoring
            return execution.id
            
    
    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        """
        Get a workflow execution by ID.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            WorkflowExecution if found, None otherwise
        """
        return self.executions.get(execution_id)
    
    def get_execution_status(self, execution_id: str) -> Dict[str, Any]:
        """
        Get the status of a workflow execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            Dictionary with execution status information
            
        Raises:
            ValueError: If execution not found
        """
        execution = self.executions.get(execution_id)
        if not execution:
            raise ValueError(f"Execution {execution_id} not found")
        
        status_data = {
            "id": execution.id,
            "status": execution.status.name,
            "start_time": execution.start_time.isoformat() if execution.start_time else None,
            "end_time": execution.end_time.isoformat() if execution.end_time else None,
            "error_message": execution.error_message,
            "completed_nodes": len(execution.completed_nodes),
            "total_nodes": len(execution.workflow.nodes),
            "results": execution.results
        }
        
        # Add node execution status information if available
        if hasattr(execution, 'node_execution_status'):
            status_data["node_statuses"] = execution.node_execution_status
            
        return status_data
    
    def cancel_execution(self, execution_id: str) -> bool:
        """
        Cancel a workflow execution.
        
        Args:
            execution_id: ID of the execution
            
        Returns:
            True if canceled, False if not found or already finished
        """
        execution = self.executions.get(execution_id)
        if not execution or execution.status != ExecutionStatus.RUNNING:
            return False
        
        execution.cancel()
        return True
    
    def continue_execution(self, execution_id: str, max_steps: int = 10) -> bool:
        """
        Continue executing a workflow for a limited number of steps.
        
        Args:
            execution_id: ID of the execution
            max_steps: Maximum number of steps to execute
            
        Returns:
            True if execution is still running, False if completed or failed
        """
        execution = self.executions.get(execution_id)
        if not execution or execution.status != ExecutionStatus.RUNNING:
            return False
        
        # Execute limited steps
        for _ in range(max_steps):
            if not execution.execute_step():
                return False
        
        return execution.status == ExecutionStatus.RUNNING
    
    def cleanup_old_executions(self, max_age_seconds: int = 3600) -> int:
        """
        Remove old workflow executions from the registry.
        
        Args:
            max_age_seconds: Maximum age of executions to keep
            
        Returns:
            Number of executions removed
        """
        now = datetime.now()
        to_remove = []
        
        for execution_id, execution in self.executions.items():
            # Skip active executions
            if execution.status == ExecutionStatus.RUNNING:
                continue
            
            # Check if execution is older than max age
            if execution.end_time:
                age = (now - execution.end_time).total_seconds()
                if age > max_age_seconds:
                    to_remove.append(execution_id)
        
        # Remove old executions
        for execution_id in to_remove:
            del self.executions[execution_id]
        
        return len(to_remove)
    
    def get_all_executions(self) -> List[Dict[str, Any]]:
        """
        Get information about all workflow executions.
        
        Returns:
            List of execution status dictionaries
        """
        return [
            self.get_execution_status(execution_id)
            for execution_id in self.executions
        ]