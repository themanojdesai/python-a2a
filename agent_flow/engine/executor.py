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
                
                # Add node to execution queue if not already there
                if target_node_id not in self.execution_queue and target_node_id not in self.completed_nodes:
                    self.execution_queue.append(target_node_id)
                
                # Pass output as input to target node
                target_execution = self.node_executions[target_node_id]
                target_execution.input_values[edge.id] = node_execution.output_value
            
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
            if not self.execute_step():
                break
            steps += 1
        
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
        
        # Extract the text content from the message
        text = str(input_message.content)
        
        # Send the message to the agent
        response = agent.send_message(text)
        if response is None:
            raise RuntimeError(f"Agent request failed: {agent.error_message}")
        
        # Clean up and normalize the response
        cleaned_response = response
        
        # Extract text content if needed
        if isinstance(response, dict) and 'content' in response:
            # Handle nested content structure
            cleaned_response = response['content']
        elif isinstance(response, dict) and 'text' in response:
            # Handle text field directly
            cleaned_response = response['text']
        
        logger.info(f"💬 Agent response received: {str(cleaned_response)[:100]}...")
            
        # Create output message
        output_message = MessageValue(
            content=cleaned_response,
            content_type="text",
            source_node_id=node.id,
            metadata={"agent_id": agent_id}
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
        
        # Get input message
        input_message = None
        for edge_id, message in execution.input_values.items():
            # Just use the first available message for now
            input_message = message
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
        
        # Store the result
        self.results[output_key] = content
        
        # Pass through the message (with cleaned content)
        execution.output_value = input_message
    
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