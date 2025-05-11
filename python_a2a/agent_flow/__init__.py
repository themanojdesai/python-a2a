"""
Agent Flow: An n8n-like workflow system based on Python A2A

This package provides a workflow system for creating, managing, and executing
agent networks. It allows users to connect agents together, define data flow,
and create complex workflows with minimal code.
"""

__version__ = "0.1.0"

# Import main components for easier access
from .models.workflow import Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
from .models.agent import AgentRegistry, AgentDefinition, AgentStatus
from .models.tool import ToolRegistry, ToolDefinition, ToolStatus
from .engine.executor import WorkflowExecutor
from .storage.workflow_storage import FileWorkflowStorage

# Import server components if available
try:
    from .server.web import run_web_server
    from .server.api import create_app
    HAS_SERVER = True
except ImportError:
    HAS_SERVER = False

# Define what gets imported with "from agent_flow import *"
__all__ = [
    # Version
    '__version__',

    # Models
    'Workflow',
    'WorkflowNode',
    'WorkflowEdge',
    'NodeType',
    'EdgeType',
    'AgentRegistry',
    'AgentDefinition',
    'AgentStatus',
    'ToolRegistry',
    'ToolDefinition',
    'ToolStatus',

    # Engine
    'WorkflowExecutor',

    # Storage
    'FileWorkflowStorage',
]

# Add server components if available
if HAS_SERVER:
    __all__.extend([
        'run_web_server',
        'create_app',
    ])