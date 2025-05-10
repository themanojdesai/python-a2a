"""
RESTful API for the Agent Flow workflow system.

This module provides a Flask-based REST API for interacting with the
Agent Flow workflow system.
"""

import os
import json
import logging
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

try:
    from flask import Flask, request, jsonify, Blueprint, current_app
    from werkzeug.exceptions import NotFound, BadRequest
except ImportError:
    raise ImportError("Flask is required to run the API server. Install with: pip install flask")

from ..models.workflow import (
    Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
)
from ..models.agent import AgentRegistry, AgentDefinition, AgentSource, AgentStatus
from ..models.tool import ToolRegistry, ToolDefinition, ToolSource, ToolStatus
from ..engine.executor import WorkflowExecutor
from ..storage.workflow_storage import WorkflowStorage

# Import Python A2A server components
from python_a2a.server.a2a_server import A2AServer
from python_a2a.server.http import run_server as a2a_run_server


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentFlowAPI")


def create_app(
    agent_registry: AgentRegistry,
    tool_registry: ToolRegistry,
    workflow_storage: WorkflowStorage,
    workflow_executor: WorkflowExecutor
):
    """
    Create a Flask application for the Agent Flow API.
    
    Args:
        agent_registry: Registry of available agents
        tool_registry: Registry of available tools
        workflow_storage: Storage service for workflows
        workflow_executor: Executor for running workflows
        
    Returns:
        Flask application
    """
    app = Flask(__name__)
    
    # Configure CORS
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        logger.warning("Flask-CORS not installed. CORS support disabled.")
    
    # Store registries and services in application context
    app.config['AGENT_REGISTRY'] = agent_registry
    app.config['TOOL_REGISTRY'] = tool_registry
    app.config['WORKFLOW_STORAGE'] = workflow_storage
    app.config['WORKFLOW_EXECUTOR'] = workflow_executor
    
    # Register blueprints
    app.register_blueprint(create_agent_blueprint(), url_prefix='/api/agents')
    app.register_blueprint(create_tool_blueprint(), url_prefix='/api/tools')
    app.register_blueprint(create_workflow_blueprint(), url_prefix='/api/workflows')
    app.register_blueprint(create_execution_blueprint(), url_prefix='/api/executions')
    
    # Error handlers
    @app.errorhandler(NotFound)
    def handle_not_found(e):
        return jsonify({"error": "Not found"}), 404
    
    @app.errorhandler(BadRequest)
    def handle_bad_request(e):
        return jsonify({"error": str(e)}), 400
    
    @app.errorhandler(Exception)
    def handle_exception(e):
        logger.exception("Unhandled exception")
        return jsonify({"error": "Internal server error"}), 500
    
    # Home route
    @app.route('/')
    def home():
        return jsonify({
            "name": "Agent Flow API",
            "version": "0.1.0",
            "description": "RESTful API for the Agent Flow workflow system",
            "endpoints": [
                "/api/agents",
                "/api/tools",
                "/api/workflows",
                "/api/executions"
            ]
        })
    
    return app


def create_agent_blueprint():
    """Create blueprint for agent-related endpoints."""
    blueprint = Blueprint('agents', __name__)
    
    @blueprint.route('/', methods=['GET'])
    def list_agents():
        """List all registered agents."""
        registry = current_app.config['AGENT_REGISTRY']
        agents = registry.list_agents()
        
        # Convert to serializable format
        result = []
        for agent in agents:
            result.append({
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "url": agent.url,
                "agent_type": agent.agent_type,
                "agent_source": agent.agent_source.name,
                "status": agent.status.name,
                "skills_count": len(agent.skills)
            })
        
        return jsonify(result)
    
    @blueprint.route('/<agent_id>', methods=['GET'])
    def get_agent(agent_id):
        """Get details of a specific agent."""
        registry = current_app.config['AGENT_REGISTRY']
        agent = registry.get(agent_id)
        
        if not agent:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        # Full agent details
        result = agent.to_dict()
        
        return jsonify(result)
    
    @blueprint.route('/', methods=['POST'])
    def add_agent():
        """Add a new agent."""
        registry = current_app.config['AGENT_REGISTRY']
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        if 'url' not in data:
            return jsonify({"error": "URL is required"}), 400
        
        # Extract agent properties
        name = data.get('name', f"Agent {data['url']}")
        description = data.get('description', "")
        url = data['url']
        agent_type = data.get('agent_type', "a2a")
        agent_source_name = data.get('agent_source', "REMOTE")
        
        try:
            agent_source = AgentSource[agent_source_name]
        except KeyError:
            return jsonify({"error": f"Invalid agent source: {agent_source_name}"}), 400
        
        # Create agent definition
        agent = AgentDefinition(
            name=name,
            description=description,
            url=url,
            agent_source=agent_source,
            agent_type=agent_type
        )
        
        # Try to connect to the agent
        if data.get('connect', True):
            connect_result = agent.connect()
            if not connect_result:
                return jsonify({
                    "warning": f"Could not connect to agent: {agent.error_message}",
                    "id": agent.id
                }), 201
        
        # Register the agent
        registry.register(agent)
        
        return jsonify({"id": agent.id, "status": agent.status.name}), 201
    
    @blueprint.route('/<agent_id>', methods=['DELETE'])
    def remove_agent(agent_id):
        """Remove an agent."""
        registry = current_app.config['AGENT_REGISTRY']
        
        if registry.unregister(agent_id):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
    
    @blueprint.route('/<agent_id>/connect', methods=['POST'])
    def connect_agent(agent_id):
        """Connect to an agent."""
        registry = current_app.config['AGENT_REGISTRY']
        agent = registry.get(agent_id)
        
        if not agent:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        connect_result = agent.connect()
        
        if connect_result:
            return jsonify({
                "status": agent.status.name,
                "skills_count": len(agent.skills)
            })
        else:
            return jsonify({
                "error": f"Could not connect to agent: {agent.error_message}",
                "status": agent.status.name
            }), 400
    
    @blueprint.route('/<agent_id>/disconnect', methods=['POST'])
    def disconnect_agent(agent_id):
        """Disconnect from an agent."""
        registry = current_app.config['AGENT_REGISTRY']
        agent = registry.get(agent_id)
        
        if not agent:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        agent.disconnect()
        
        return jsonify({"status": agent.status.name})
    
    @blueprint.route('/discover', methods=['POST'])
    def discover_agents():
        """Discover agents."""
        registry = current_app.config['AGENT_REGISTRY']
        data = request.json or {}
        
        base_url = data.get('base_url', "http://localhost")
        port_min = data.get('port_min', 8000)
        port_max = data.get('port_max', 9000)
        
        agents = registry.discover_agents(base_url, (port_min, port_max))
        
        # Convert to serializable format
        result = []
        for agent in agents:
            result.append({
                "id": agent.id,
                "name": agent.name,
                "description": agent.description,
                "url": agent.url,
                "agent_type": agent.agent_type,
                "agent_source": agent.agent_source.name,
                "status": agent.status.name,
                "skills_count": len(agent.skills)
            })
        
        return jsonify(result)
    
    @blueprint.route('/<agent_id>/message', methods=['POST'])
    def send_message(agent_id):
        """Send a message to an agent."""
        registry = current_app.config['AGENT_REGISTRY']
        agent = registry.get(agent_id)
        
        if not agent:
            return jsonify({"error": f"Agent {agent_id} not found"}), 404
        
        data = request.json
        
        if not data or 'message' not in data:
            return jsonify({"error": "Message is required"}), 400
        
        # Ensure agent is connected
        if agent.status != AgentStatus.CONNECTED:
            connect_result = agent.connect()
            if not connect_result:
                return jsonify({
                    "error": f"Could not connect to agent: {agent.error_message}"
                }), 400
        
        # Send the message
        message = data['message']
        response = agent.send_message(message)
        
        if response is None:
            return jsonify({
                "error": f"Failed to send message: {agent.error_message}"
            }), 400
        
        return jsonify({"response": response})
    
    return blueprint


def create_tool_blueprint():
    """Create blueprint for tool-related endpoints."""
    blueprint = Blueprint('tools', __name__)
    
    @blueprint.route('/', methods=['GET'])
    def list_tools():
        """List all registered tools."""
        registry = current_app.config['TOOL_REGISTRY']
        tools = registry.list_tools()
        
        # Convert to serializable format
        result = []
        for tool in tools:
            result.append({
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "url": tool.url,
                "tool_path": tool.tool_path,
                "tool_source": tool.tool_source.name,
                "status": tool.status.name,
                "parameters_count": len(tool.parameters)
            })
        
        return jsonify(result)
    
    @blueprint.route('/<tool_id>', methods=['GET'])
    def get_tool(tool_id):
        """Get details of a specific tool."""
        registry = current_app.config['TOOL_REGISTRY']
        tool = registry.get(tool_id)
        
        if not tool:
            return jsonify({"error": f"Tool {tool_id} not found"}), 404
        
        # Full tool details
        result = tool.to_dict()
        
        return jsonify(result)
    
    @blueprint.route('/', methods=['POST'])
    def add_tool():
        """Add a new tool."""
        registry = current_app.config['TOOL_REGISTRY']
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        if 'url' not in data:
            return jsonify({"error": "URL is required"}), 400
        
        # Extract tool properties
        name = data.get('name', f"Tool {data['url']}")
        description = data.get('description', "")
        url = data['url']
        tool_path = data.get('tool_path', "")
        tool_source_name = data.get('tool_source', "REMOTE")
        
        try:
            tool_source = ToolSource[tool_source_name]
        except KeyError:
            return jsonify({"error": f"Invalid tool source: {tool_source_name}"}), 400
        
        # Create tool definition
        tool = ToolDefinition(
            name=name,
            description=description,
            url=url,
            tool_path=tool_path,
            tool_source=tool_source
        )
        
        # Add parameters if provided
        parameters = data.get('parameters', [])
        for param_data in parameters:
            if isinstance(param_data, dict):
                from ..models.tool import ToolParameter
                param = ToolParameter.from_dict(param_data)
                tool.parameters.append(param)
        
        # Check availability
        if data.get('check_availability', True):
            available = tool.check_availability()
            if not available:
                return jsonify({
                    "warning": f"Tool is not available: {tool.error_message}",
                    "id": tool.id
                }), 201
        
        # Register the tool
        registry.register(tool)
        
        return jsonify({"id": tool.id, "status": tool.status.name}), 201
    
    @blueprint.route('/<tool_id>', methods=['DELETE'])
    def remove_tool(tool_id):
        """Remove a tool."""
        registry = current_app.config['TOOL_REGISTRY']
        
        if registry.unregister(tool_id):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": f"Tool {tool_id} not found"}), 404
    
    @blueprint.route('/<tool_id>/check', methods=['POST'])
    def check_tool(tool_id):
        """Check if a tool is available."""
        registry = current_app.config['TOOL_REGISTRY']
        tool = registry.get(tool_id)
        
        if not tool:
            return jsonify({"error": f"Tool {tool_id} not found"}), 404
        
        available = tool.check_availability()
        
        if available:
            return jsonify({
                "status": tool.status.name
            })
        else:
            return jsonify({
                "error": f"Tool is not available: {tool.error_message}",
                "status": tool.status.name
            }), 400
    
    @blueprint.route('/discover', methods=['POST'])
    def discover_tools():
        """Discover tools from an MCP server."""
        registry = current_app.config['TOOL_REGISTRY']
        data = request.json or {}
        
        if 'url' not in data:
            return jsonify({"error": "URL is required"}), 400
        
        mcp_url = data['url']
        
        tools = registry.discover_tools(mcp_url)
        
        # Convert to serializable format
        result = []
        for tool in tools:
            result.append({
                "id": tool.id,
                "name": tool.name,
                "description": tool.description,
                "url": tool.url,
                "tool_path": tool.tool_path,
                "tool_source": tool.tool_source.name,
                "status": tool.status.name,
                "parameters_count": len(tool.parameters)
            })
        
        return jsonify(result)
    
    @blueprint.route('/<tool_id>/execute', methods=['POST'])
    def execute_tool(tool_id):
        """Execute a tool."""
        registry = current_app.config['TOOL_REGISTRY']
        tool = registry.get(tool_id)
        
        if not tool:
            return jsonify({"error": f"Tool {tool_id} not found"}), 404
        
        data = request.json or {}
        
        # Check availability
        available = tool.check_availability()
        if not available:
            return jsonify({
                "error": f"Tool is not available: {tool.error_message}"
            }), 400
        
        # Execute the tool
        try:
            result = tool.execute(data)
            return jsonify(result)
        except ValueError as e:
            return jsonify({"error": str(e)}), 400
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 500
    
    return blueprint


def create_workflow_blueprint():
    """Create blueprint for workflow-related endpoints."""
    blueprint = Blueprint('workflows', __name__)
    
    # Add a new endpoint for running networks from the UI
    @blueprint.route('/run-network', methods=['POST'])
    def run_network_from_ui():
        """Run a network directly from the UI."""
        executor = current_app.config['WORKFLOW_EXECUTOR']
        agent_registry = current_app.config['AGENT_REGISTRY']
        tool_registry = current_app.config['TOOL_REGISTRY']
        data = request.json

        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Check if required fields are present
        if 'nodes' not in data or 'connections' not in data:
            return jsonify({"error": "Invalid network data: missing nodes or connections"}), 400

        if 'input' not in data:
            return jsonify({"error": "No input provided"}), 400

        try:
            # Validate agents and tools in the network
            validation_errors = validate_network_nodes(data, agent_registry, tool_registry)
            if validation_errors:
                return jsonify({"error": "Network validation failed", "errors": validation_errors}), 400

            # Store the network data for future reference if it has an ID
            if 'id' in data:
                network_storage = current_app.config.get('NETWORK_STORAGE', {})
                if not current_app.config.get('NETWORK_STORAGE'):
                    current_app.config['NETWORK_STORAGE'] = {}
                    network_storage = current_app.config['NETWORK_STORAGE']

                # Store the latest version
                network_storage[data['id']] = data
                logger.info(f"Stored network configuration with ID: {data['id']}")

            # Configure agents if needed
            configured_network = configure_network_agents(data, agent_registry)

            # Convert the UI network format to a Workflow object
            workflow = convert_network_data_to_workflow(configured_network)
            
            # Get input data
            input_data = {'input': data['input']}
            
            # Log start of execution
            logger.info(f"🔄 Starting execution of network with {len(workflow.nodes)} nodes")
            
            # Execute the workflow with proper timing
            import time
            start_time = time.time()
            
            # Execute the workflow
            results = executor.execute_workflow(workflow, input_data, wait=True)
            
            # Calculate execution time
            execution_time = time.time() - start_time
            logger.info(f"⏱️ Network execution completed in {execution_time:.2f} seconds")
            
            # Look for output from output nodes
            output = None
            output_type = "text"  # Default output type
            
            if results:
                # First check for 'output' key
                if 'output' in results:
                    output = results['output']
                    # Try to determine the output type
                    if isinstance(output, dict) and 'type' in output:
                        output_type = output['type']
                        output = output.get('content', output)
                # Then check for any output node result
                elif results:
                    # Use the first output node result we find
                    for key, value in results.items():
                        output = value
                        # Try to determine if this is a specialized output
                        if isinstance(value, dict) and 'type' in value:
                            output_type = value['type']
                            output = value.get('content', value)
                        break
            
            logger.info(f"Network execution completed successfully with results: {results}")
            
            # Process output based on type for better rendering
            formatted_output = {
                "result": output if output is not None else "Execution completed but no output was generated.",
                "type": output_type
            }
            
            # Add additional formatting based on output type
            if output_type == "markdown" and isinstance(output, str):
                # Keep the raw markdown for client-side rendering
                formatted_output["format"] = "markdown"
            elif output_type == "json" or isinstance(output, (dict, list)):
                # Structure as JSON with indentation preserved
                formatted_output["format"] = "json"
            elif output_type == "image" and isinstance(output, str) and (
                output.startswith("data:image/") or output.startswith("http")
            ):
                # Image URL or data URL
                formatted_output["format"] = "image"
            elif output_type == "html" and isinstance(output, str):
                # HTML content
                formatted_output["format"] = "html"
                
            # Return the formatted result
            return jsonify(formatted_output)
        except Exception as e:
            logger.exception("Error executing network")
            return jsonify({"error": f"Error executing network: {str(e)}"}), 500
    
    @blueprint.route('/', methods=['GET'])
    def list_workflows():
        """List all workflows."""
        storage = current_app.config['WORKFLOW_STORAGE']
        workflows = storage.list_workflows()
        
        return jsonify(workflows)
    
    @blueprint.route('/<workflow_id>', methods=['GET'])
    def get_workflow(workflow_id):
        """Get details of a specific workflow."""
        storage = current_app.config['WORKFLOW_STORAGE']
        workflow = storage.load_workflow(workflow_id)
        
        if not workflow:
            return jsonify({"error": f"Workflow {workflow_id} not found"}), 404
        
        # Full workflow details
        result = workflow.to_dict()
        
        return jsonify(result)
    
    @blueprint.route('/', methods=['POST'])
    def create_workflow():
        """Create a new workflow."""
        storage = current_app.config['WORKFLOW_STORAGE']
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        try:
            # Create workflow from data
            workflow = Workflow.from_dict(data)
            
            # Validate the workflow
            valid, errors = workflow.validate()
            if not valid and not data.get('force', False):
                return jsonify({
                    "error": "Invalid workflow",
                    "errors": errors
                }), 400
            
            # Save the workflow
            workflow_id = storage.save_workflow(workflow)
            
            return jsonify({"id": workflow_id}), 201
        
        except Exception as e:
            return jsonify({"error": f"Error creating workflow: {str(e)}"}), 400
    
    @blueprint.route('/<workflow_id>', methods=['PUT'])
    def update_workflow(workflow_id):
        """Update an existing workflow."""
        storage = current_app.config['WORKFLOW_STORAGE']
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        # Check if workflow exists
        existing_workflow = storage.load_workflow(workflow_id)
        if not existing_workflow:
            return jsonify({"error": f"Workflow {workflow_id} not found"}), 404
        
        try:
            # Create workflow from data
            workflow = Workflow.from_dict(data)
            
            # Ensure ID matches
            if workflow.id != workflow_id:
                workflow.id = workflow_id
            
            # Validate the workflow
            valid, errors = workflow.validate()
            if not valid and not data.get('force', False):
                return jsonify({
                    "error": "Invalid workflow",
                    "errors": errors
                }), 400
            
            # Save the workflow
            storage.save_workflow(workflow)
            
            return jsonify({"id": workflow_id}), 200
        
        except Exception as e:
            return jsonify({"error": f"Error updating workflow: {str(e)}"}), 400
    
    @blueprint.route('/<workflow_id>', methods=['DELETE'])
    def delete_workflow(workflow_id):
        """Delete a workflow."""
        storage = current_app.config['WORKFLOW_STORAGE']
        
        if storage.delete_workflow(workflow_id):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": f"Workflow {workflow_id} not found"}), 404
    
    @blueprint.route('/<workflow_id>/run', methods=['POST'])
    def run_workflow(workflow_id):
        """Run a workflow."""
        storage = current_app.config['WORKFLOW_STORAGE']
        executor = current_app.config['WORKFLOW_EXECUTOR']
        
        # Check if workflow exists
        workflow = storage.load_workflow(workflow_id)
        if not workflow:
            return jsonify({"error": f"Workflow {workflow_id} not found"}), 404
        
        # Get input data if provided
        input_data = request.json
        
        # Check if async execution is requested
        async_mode = request.args.get('async', 'false').lower() == 'true'
        
        try:
            if async_mode:
                # Run asynchronously
                execution_id = executor.execute_workflow(
                    workflow, input_data, wait=False
                )
                return jsonify({
                    "execution_id": execution_id,
                    "status": "RUNNING"
                })
            else:
                # Run synchronously
                results = executor.execute_workflow(
                    workflow, input_data, wait=True
                )
                return jsonify({"results": results})
        
        except Exception as e:
            return jsonify({"error": f"Error executing workflow: {str(e)}"}), 500
    
    return blueprint


def validate_network_nodes(data, agent_registry, tool_registry):
    """
    Validate nodes in the network to ensure they have proper configuration.
    
    Args:
        data: Network data from the UI
        agent_registry: Agent registry for validating agents
        tool_registry: Tool registry for validating tools
        
    Returns:
        List of error messages, or empty list if validation passes
    """
    errors = []
    
    # Check for nodes
    if 'nodes' not in data or not data['nodes']:
        errors.append("Network has no nodes")
        return errors
    
    # Check for input and output nodes
    input_nodes = [node for node in data['nodes'] if node['type'] == 'input']
    output_nodes = [node for node in data['nodes'] if node['type'] == 'output']
    
    if not input_nodes:
        errors.append("Network must have at least one input node")
    
    if not output_nodes:
        errors.append("Network must have at least one output node")
    
    # Validate agent nodes
    for node in data['nodes']:
        if node['type'] == 'agent':
            agent_type = node.get('subType')
            config = node.get('config', {})
            
            # Validate agent configuration based on type
            if agent_type == 'openai':
                if not config.get('apiKey'):
                    errors.append(f"OpenAI agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing API key")
                if not config.get('model'):
                    errors.append(f"OpenAI agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing model selection")
            
            elif agent_type == 'anthropic':
                if not config.get('apiKey'):
                    errors.append(f"Anthropic Claude agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing API key")
                if not config.get('model'):
                    errors.append(f"Anthropic Claude agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing model selection")
            
            elif agent_type == 'bedrock':
                if not config.get('accessKey') or not config.get('secretKey'):
                    errors.append(f"AWS Bedrock agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing AWS credentials")
                if not config.get('region'):
                    errors.append(f"AWS Bedrock agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing AWS region")
                if not config.get('model'):
                    errors.append(f"AWS Bedrock agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing model selection")
            
            elif agent_type == 'custom':
                # For custom agents, we need either port or endpoint
                if not config.get('port') and not config.get('endpoint'):
                    errors.append(f"Custom agent '{node.get('config', {}).get('name', 'Unnamed')}' is missing port or endpoint")
        
        # Validate tool nodes - can be added in the future
        elif node['type'] == 'tool':
            tool_type = node.get('subType')
            config = node.get('config', {})
            
            # Tool validation logic would go here
    
    return errors


def configure_network_agents(data, agent_registry):
    """
    Configure agents in the network and register them in the agent registry.

    Args:
        data: Network data from the UI
        agent_registry: Agent registry for registering configured agents

    Returns:
        Updated network data with configured agent references
    """
    from ..models.agent import AgentDefinition, AgentSource, AgentStatus
    import copy
    import time
    import hashlib

    # Create a deep copy of the data to avoid modifying the original
    network = copy.deepcopy(data)

    # Persistent agent storage - use agent config hash to identify and reuse agents
    network_storage = getattr(current_app.config, 'NETWORK_STORAGE', {})
    agent_cache = getattr(current_app.config, 'AGENT_CACHE', {})

    # Initialize agent cache if it doesn't exist
    if not hasattr(current_app.config, 'AGENT_CACHE'):
        current_app.config['AGENT_CACHE'] = {}
        agent_cache = current_app.config['AGENT_CACHE']

    # Configure and register agents
    for node in network['nodes']:
        if node['type'] == 'agent':
            agent_type = node.get('subType')
            config = node.get('config', {})

            # Generate a unique hash for this configuration to identify identical configs
            config_hash = None

            if agent_type == 'openai':
                # Generate a hash of the important configuration parameters
                config_key = f"{agent_type}_{config.get('name', '')}_{config.get('model', '')}_{config.get('apiKey', '')}_{config.get('systemMessage', '')}"
                config_hash = hashlib.md5(config_key.encode()).hexdigest()

                # Check if we already have this agent configured
                if config_hash in agent_cache:
                    cached_agent = agent_cache[config_hash]
                    cached_agent_obj = agent_registry.get(cached_agent['agent_id'])

                    if cached_agent_obj and cached_agent_obj.status == AgentStatus.CONNECTED:
                        # Reuse the existing agent
                        logger.info(f"Reusing existing agent configuration: {cached_agent['name']}")
                        node['config']['agent_id'] = cached_agent['agent_id']
                        continue

                # If not cached or not available, create a new agent
                from python_a2a.server.llm.openai import OpenAIA2AServer
                from python_a2a.server.a2a_server import A2AServer

                # Import necessary components
                from python_a2a.models.agent import AgentCard, AgentSkill

                # Create agent card
                agent_card = AgentCard(
                    name=config.get('name', 'OpenAI Agent'),
                    description=f"OpenAI powered agent using {config.get('model', 'gpt-4')}",
                    url=f"http://localhost:0",  # Will be updated after port is determined
                    version="1.0.0",
                    skills=[
                        AgentSkill(
                            name="General Assistance",
                            description="Provide helpful responses to various queries",
                            examples=["How can I improve my productivity?", "Explain how batteries work"]
                        )
                    ]
                )

                # Create server instance
                openai_server = OpenAIA2AServer(
                    api_key=config.get('apiKey', ''),
                    model=config.get('model', 'gpt-4'),
                    temperature=0.7,
                    system_prompt=config.get('systemMessage', 'You are a helpful AI assistant.')
                )

                # Create a properly wrapped OpenAI agent
                class OpenAIAgent(A2AServer):
                    def __init__(self, openai_server, agent_card):
                        super().__init__(agent_card=agent_card)
                        self.openai_server = openai_server

                    def handle_message(self, message):
                        # Process the message with the OpenAI server
                        return self.openai_server.handle_message(message)

                # Create the wrapped agent
                server = OpenAIAgent(openai_server, agent_card)

                # Start server on a random port
                import socket
                sock = socket.socket()
                sock.bind(('', 0))
                port = sock.getsockname()[1]
                sock.close()

                # Update agent card URL with the actual port
                agent_card.url = f"http://localhost:{port}"

                # Register server with its URL
                agent_url = f"http://localhost:{port}"

                # Create agent definition
                agent = AgentDefinition(
                    name=config.get('name', 'OpenAI Agent'),
                    description=f"OpenAI powered agent using {config.get('model', 'gpt-4')}",
                    url=agent_url,
                    agent_source=AgentSource.LLM,
                    agent_type="openai",
                    config={
                        "apiKey": config.get('apiKey', ''),
                        "model": config.get('model', 'gpt-4'),
                        "temperature": 0.7,
                        "systemMessage": config.get('systemMessage', 'You are a helpful AI assistant.'),
                        "server": server,
                        "port": port
                    }
                )

                # Register the agent
                agent_registry.register(agent)

                # Update the node config with agent_id
                node['config']['agent_id'] = agent.id

                # Cache this agent configuration for future reuse
                agent_cache[config_hash] = {
                    'agent_id': agent.id,
                    'name': config.get('name', 'OpenAI Agent'),
                    'type': agent_type,
                    'model': config.get('model', 'gpt-4'),
                    'port': port,
                    'created_at': time.time()
                }

                # Start the server in a background thread
                import threading
                def run_server():
                    logger.info(f"Starting agent server on port {port}")
                    try:
                        a2a_run_server(server, host="0.0.0.0", port=port)
                    except Exception as e:
                        logger.error(f"Error starting agent server: {e}")

                server_thread = threading.Thread(target=run_server, daemon=True)
                server_thread.start()

            elif agent_type == 'anthropic':
                # Generate a hash of the important configuration parameters
                config_key = f"{agent_type}_{config.get('name', '')}_{config.get('model', '')}_{config.get('apiKey', '')}_{config.get('systemMessage', '')}"
                config_hash = hashlib.md5(config_key.encode()).hexdigest()

                # Check if we already have this agent configured
                if config_hash in agent_cache:
                    cached_agent = agent_cache[config_hash]
                    cached_agent_obj = agent_registry.get(cached_agent['agent_id'])

                    if cached_agent_obj and cached_agent_obj.status == AgentStatus.CONNECTED:
                        # Reuse the existing agent
                        logger.info(f"Reusing existing agent configuration: {cached_agent['name']}")
                        node['config']['agent_id'] = cached_agent['agent_id']
                        continue

                # If not cached or not available, create a new agent
                from python_a2a.server.llm.anthropic import AnthropicA2AServer
                from python_a2a.server.a2a_server import A2AServer

                # Import necessary components
                from python_a2a.models.agent import AgentCard, AgentSkill

                # Create agent card
                agent_card = AgentCard(
                    name=config.get('name', 'Claude Agent'),
                    description=f"Anthropic Claude powered agent using {config.get('model', 'claude-3-opus')}",
                    url=f"http://localhost:0",  # Will be updated after port is determined
                    version="1.0.0",
                    skills=[
                        AgentSkill(
                            name="General Assistance",
                            description="Provide helpful responses to various queries",
                            examples=["How can I improve my productivity?", "Explain how batteries work"]
                        )
                    ]
                )

                # Create server instance
                anthropic_server = AnthropicA2AServer(
                    api_key=config.get('apiKey', ''),
                    model=config.get('model', 'claude-3-opus'),
                    system_prompt=config.get('systemMessage', 'You are Claude, an AI assistant by Anthropic.')
                )

                # Create a properly wrapped Anthropic agent
                class AnthropicAgent(A2AServer):
                    def __init__(self, anthropic_server, agent_card):
                        super().__init__(agent_card=agent_card)
                        self.anthropic_server = anthropic_server

                    def handle_message(self, message):
                        # Process the message with the Anthropic server
                        return self.anthropic_server.handle_message(message)

                # Create the wrapped agent
                server = AnthropicAgent(anthropic_server, agent_card)

                # Start server on a random port
                import socket
                sock = socket.socket()
                sock.bind(('', 0))
                port = sock.getsockname()[1]
                sock.close()

                # Update agent card URL with the actual port
                agent_card.url = f"http://localhost:{port}"

                # Register server with its URL
                agent_url = f"http://localhost:{port}"

                # Create agent definition
                agent = AgentDefinition(
                    name=config.get('name', 'Claude Agent'),
                    description=f"Anthropic Claude powered agent using {config.get('model', 'claude-3-opus')}",
                    url=agent_url,
                    agent_source=AgentSource.LLM,
                    agent_type="anthropic",
                    config={
                        "apiKey": config.get('apiKey', ''),
                        "model": config.get('model', 'claude-3-opus'),
                        "systemMessage": config.get('systemMessage', 'You are Claude, an AI assistant by Anthropic.'),
                        "server": server,
                        "port": port
                    }
                )

                # Register the agent
                agent_registry.register(agent)

                # Update the node config with agent_id
                node['config']['agent_id'] = agent.id

                # Cache this agent configuration for future reuse
                agent_cache[config_hash] = {
                    'agent_id': agent.id,
                    'name': config.get('name', 'Claude Agent'),
                    'type': agent_type,
                    'model': config.get('model', 'claude-3-opus'),
                    'port': port,
                    'created_at': time.time()
                }

                # Start the server in a background thread
                import threading
                def run_server():
                    logger.info(f"Starting agent server on port {port}")
                    try:
                        a2a_run_server(server, host="0.0.0.0", port=port)
                    except Exception as e:
                        logger.error(f"Error starting agent server: {e}")

                server_thread = threading.Thread(target=run_server, daemon=True)
                server_thread.start()
                
            elif agent_type == 'bedrock':
                # Generate a hash of the important configuration parameters
                config_key = f"{agent_type}_{config.get('name', '')}_{config.get('model', '')}_{config.get('accessKey', '')}_{config.get('secretKey', '')}_{config.get('region', '')}_{config.get('systemMessage', '')}"
                config_hash = hashlib.md5(config_key.encode()).hexdigest()

                # Check if we already have this agent configured
                if config_hash in agent_cache:
                    cached_agent = agent_cache[config_hash]
                    cached_agent_obj = agent_registry.get(cached_agent['agent_id'])

                    if cached_agent_obj and cached_agent_obj.status == AgentStatus.CONNECTED:
                        # Reuse the existing agent
                        logger.info(f"Reusing existing agent configuration: {cached_agent['name']}")
                        node['config']['agent_id'] = cached_agent['agent_id']
                        continue

                # If not cached or not available, create a new agent
                from python_a2a.server.llm.bedrock import BedrockA2AServer
                from python_a2a.server.a2a_server import A2AServer

                # Import necessary components
                from python_a2a.models.agent import AgentCard, AgentSkill

                # Create agent card
                agent_card = AgentCard(
                    name=config.get('name', 'Bedrock Agent'),
                    description=f"AWS Bedrock powered agent using {config.get('model', 'anthropic.claude-3-sonnet')}",
                    url=f"http://localhost:0",  # Will be updated after port is determined
                    version="1.0.0",
                    skills=[
                        AgentSkill(
                            name="General Assistance",
                            description="Provide helpful responses to various queries",
                            examples=["How can I improve my productivity?", "Explain how batteries work"]
                        )
                    ]
                )

                # Create server instance
                bedrock_server = BedrockA2AServer(
                    aws_access_key_id=config.get('accessKey', ''),
                    aws_secret_access_key=config.get('secretKey', ''),
                    aws_region=config.get('region', 'us-east-1'),
                    model_id=config.get('model', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                    system_prompt=config.get('systemMessage', 'You are an AI assistant.')
                )

                # Create a properly wrapped Bedrock agent
                class BedrockAgent(A2AServer):
                    def __init__(self, bedrock_server, agent_card):
                        super().__init__(agent_card=agent_card)
                        self.bedrock_server = bedrock_server

                    def handle_message(self, message):
                        # Process the message with the Bedrock server
                        return self.bedrock_server.handle_message(message)

                # Create the wrapped agent
                server = BedrockAgent(bedrock_server, agent_card)

                # Start server on a random port
                import socket
                sock = socket.socket()
                sock.bind(('', 0))
                port = sock.getsockname()[1]
                sock.close()

                # Update agent card URL with the actual port
                agent_card.url = f"http://localhost:{port}"

                # Register server with its URL
                agent_url = f"http://localhost:{port}"

                # Create agent definition
                agent = AgentDefinition(
                    name=config.get('name', 'Bedrock Agent'),
                    description=f"AWS Bedrock powered agent using {config.get('model', 'anthropic.claude-3-sonnet')}",
                    url=agent_url,
                    agent_source=AgentSource.LLM,
                    agent_type="bedrock",
                    config={
                        "accessKey": config.get('accessKey', ''),
                        "secretKey": config.get('secretKey', ''),
                        "region": config.get('region', 'us-east-1'),
                        "model": config.get('model', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                        "systemMessage": config.get('systemMessage', 'You are an AI assistant.'),
                        "server": server,
                        "port": port
                    }
                )

                # Register the agent
                agent_registry.register(agent)

                # Update the node config with agent_id
                node['config']['agent_id'] = agent.id

                # Cache this agent configuration for future reuse
                agent_cache[config_hash] = {
                    'agent_id': agent.id,
                    'name': config.get('name', 'Bedrock Agent'),
                    'type': agent_type,
                    'model': config.get('model', 'anthropic.claude-3-sonnet-20240229-v1:0'),
                    'port': port,
                    'created_at': time.time()
                }

                # Start the server in a background thread
                import threading
                def run_server():
                    logger.info(f"Starting agent server on port {port}")
                    try:
                        a2a_run_server(server, host="0.0.0.0", port=port)
                    except Exception as e:
                        logger.error(f"Error starting agent server: {e}")

                server_thread = threading.Thread(target=run_server, daemon=True)
                server_thread.start()
                
            elif agent_type == 'custom':
                # Generate a hash of the important configuration parameters
                config_key = f"{agent_type}_{config.get('name', '')}_{config.get('endpoint', '')}_{config.get('port', '')}"
                config_hash = hashlib.md5(config_key.encode()).hexdigest()

                # Check if we already have this agent configured
                if config_hash in agent_cache:
                    cached_agent = agent_cache[config_hash]
                    cached_agent_obj = agent_registry.get(cached_agent['agent_id'])

                    if cached_agent_obj and cached_agent_obj.status == AgentStatus.CONNECTED:
                        # Reuse the existing agent
                        logger.info(f"Reusing existing agent configuration: {cached_agent['name']}")
                        node['config']['agent_id'] = cached_agent['agent_id']
                        continue

                # For custom agents, use the provided endpoint
                endpoint = config.get('endpoint')
                port = config.get('port')

                if endpoint:
                    agent_url = endpoint
                elif port:
                    agent_url = f"http://localhost:{port}"
                else:
                    # Skip if neither is provided
                    continue

                # Create agent definition
                agent = AgentDefinition(
                    name=config.get('name', 'Custom Agent'),
                    description="Custom agent implementation",
                    url=agent_url,
                    agent_source=AgentSource.CUSTOM,
                    agent_type="custom"
                )

                # Register the agent
                agent_registry.register(agent)

                # Update the node config with agent_id
                node['config']['agent_id'] = agent.id

                # Cache this agent configuration for future reuse
                agent_cache[config_hash] = {
                    'agent_id': agent.id,
                    'name': config.get('name', 'Custom Agent'),
                    'type': agent_type,
                    'endpoint': endpoint,
                    'port': port,
                    'created_at': time.time()
                }

                # For custom agents, we don't need to start a server
                # as they are already running somewhere else
    
    return network


def convert_network_data_to_workflow(data):
    """
    Convert network data from the UI format to a Workflow object.
    
    Args:
        data: Dictionary containing nodes and connections
        
    Returns:
        Workflow: The created workflow object
    """
    # Create a new workflow with a generated ID
    workflow_id = str(uuid.uuid4())
    workflow_name = data.get('name', 'Network from UI')
    workflow = Workflow(
        id=workflow_id,
        name=workflow_name,
        description=f"Workflow created from UI on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    )
    
    # Process nodes
    node_map = {}  # Map UI node IDs to workflow node IDs
    
    for ui_node in data.get('nodes', []):
        # Determine node type
        if ui_node['type'] == 'input':
            node_type = NodeType.INPUT
        elif ui_node['type'] == 'output':
            node_type = NodeType.OUTPUT
        elif ui_node['type'] == 'agent':
            node_type = NodeType.AGENT
        elif ui_node['type'] == 'tool':
            node_type = NodeType.TOOL
        elif ui_node['type'] == 'conditional':
            node_type = NodeType.CONDITIONAL
        elif ui_node['type'] == 'transform':
            node_type = NodeType.TRANSFORM
        else:
            # Default to AGENT if type is unknown
            node_type = NodeType.AGENT
            logger.warning(f"Unknown node type: {ui_node['type']}, defaulting to AGENT")
        
        # Create workflow node
        node_id = str(uuid.uuid4())
        
        # Create node configuration with UI node ID for tracking
        node_config = ui_node.get('config', {}).copy()
        
        # Store the UI node ID in the config for tracking purposes
        node_config['ui_node_id'] = ui_node['id']
        
        node = WorkflowNode(
            id=node_id,
            name=node_config.get('name', f"Node {ui_node['id']}"),
            node_type=node_type,
            config=node_config,
            position=ui_node.get('position', {"x": 0, "y": 0})
        )
        
        # Add subtype information if present
        if 'subType' in ui_node:
            node.config['subType'] = ui_node['subType']
        
        # Add to workflow
        workflow.add_node(node)
        
        # Store mapping
        node_map[ui_node['id']] = node_id
    
    # Process connections
    for ui_conn in data.get('connections', []):
        # Get source and target node IDs
        source_id = node_map.get(ui_conn['sourceNode'])
        target_id = node_map.get(ui_conn['targetNode'])
        
        if source_id and target_id:
            # Add edge to workflow
            workflow.add_edge(
                source_node_id=source_id,
                target_node_id=target_id,
                edge_type=EdgeType.DATA,
                config={}
            )
    
    return workflow


def create_execution_blueprint():
    """Create blueprint for execution-related endpoints."""
    blueprint = Blueprint('executions', __name__)
    
    @blueprint.route('/', methods=['GET'])
    def list_executions():
        """List all workflow executions."""
        executor = current_app.config['WORKFLOW_EXECUTOR']
        executions = executor.get_all_executions()
        
        return jsonify(executions)
    
    @blueprint.route('/<execution_id>', methods=['GET'])
    def get_execution(execution_id):
        """Get details of a specific execution."""
        executor = current_app.config['WORKFLOW_EXECUTOR']
        
        try:
            status = executor.get_execution_status(execution_id)
            return jsonify(status)
        except ValueError:
            return jsonify({"error": f"Execution {execution_id} not found"}), 404
    
    @blueprint.route('/<execution_id>/cancel', methods=['POST'])
    def cancel_execution(execution_id):
        """Cancel a workflow execution."""
        executor = current_app.config['WORKFLOW_EXECUTOR']
        
        if executor.cancel_execution(execution_id):
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": f"Execution {execution_id} not found or not running"}), 404
    
    @blueprint.route('/<execution_id>/continue', methods=['POST'])
    def continue_execution(execution_id):
        """Continue a workflow execution."""
        executor = current_app.config['WORKFLOW_EXECUTOR']
        data = request.json or {}
        
        max_steps = data.get('max_steps', 10)
        
        if executor.continue_execution(execution_id, max_steps):
            return jsonify({"status": "RUNNING"}), 200
        else:
            try:
                status = executor.get_execution_status(execution_id)
                return jsonify({"status": status["status"]}), 200
            except ValueError:
                return jsonify({"error": f"Execution {execution_id} not found"}), 404
    
    return blueprint