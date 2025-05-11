"""
Agent Manager API endpoints for the Agent Flow server.

This module provides API endpoints for managing agents using the AgentManager.
"""

import os
import json
import logging
import tempfile
import time
import uuid
from typing import Dict, List, Optional, Any

from flask import Blueprint, request, jsonify, current_app

from ..utils.agent_manager import AgentManager
from ..models.agent import AgentDefinition, AgentSource, AgentStatus
from ..models.tool import ToolDefinition, ToolSource, ToolStatus


# Configure logging
logger = logging.getLogger("AgentManagerAPI")


def create_agent_manager_blueprint():
    """Create blueprint for agent manager API endpoints."""
    blueprint = Blueprint('agent_manager', __name__)
    
    @blueprint.route('/agent_templates', methods=['GET'])
    def get_agent_templates():
        """Get available agent templates."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        if not agent_manager:
            return jsonify({"error": "Agent manager not configured"}), 500
        
        templates = agent_manager.get_available_templates()
        return jsonify(templates)
    
    @blueprint.route('/agent_servers', methods=['GET'])
    def get_running_servers():
        """Get all running agent servers."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        if not agent_manager:
            return jsonify({"error": "Agent manager not configured"}), 500
        
        servers = agent_manager.get_running_servers()
        return jsonify(servers)
    
    @blueprint.route('/agent_servers/<server_id>', methods=['DELETE'])
    def stop_agent_server(server_id):
        """Stop a running agent server."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        if not agent_manager:
            return jsonify({"error": "Agent manager not configured"}), 500
        
        success = agent_manager.stop_agent_server(server_id)
        
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"error": "Server not found or could not be stopped"}), 404
    
    @blueprint.route('/create_agent', methods=['POST'])
    def create_agent():
        """Create a new agent from a template."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        if not agent_manager:
            return jsonify({"error": "Agent manager not configured"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        if 'template_id' not in data:
            return jsonify({"error": "Template ID is required"}), 400
        
        if 'port' not in data:
            return jsonify({"error": "Port is required"}), 400
        
        template_id = data['template_id']
        port = int(data['port'])
        
        # Get the template
        template = agent_manager.get_template(template_id)
        if not template:
            return jsonify({"error": f"Template {template_id} not found"}), 404
        
        # Handle API key if required
        if template.get('requires_api_key', False):
            api_key = data.get('api_key')
            if not api_key:
                return jsonify({"error": "API key is required for this template"}), 400
            
            # Set API key in environment
            os.environ[template['api_key_env']] = api_key
        
        # Handle custom script template
        if template_id == 'custom_script':
            script_path = data.get('script_path')
            if not script_path:
                return jsonify({"error": "Script path is required for custom script template"}), 400
            
            # Store script path for the agent manager to use
            # Note: don't modify the template itself, just pass the script_path in data
        
        # Create the agent (pass script_path if available)
        script_path = data.get('script_path')
        agent_id = agent_manager.create_from_template(template_id, port, script_path)
        
        if not agent_id:
            # Check if there's any error in the agent server logs
            server_id = f"server_{int(time.time())}_{port}"
            # Look for the most recent server that failed
            for sid, info in agent_manager.running_servers.items():
                if sid.endswith(f"_{port}"):
                    server_id = sid
                    break
                
            # Get process output if available
            server_info = agent_manager.running_servers.get(server_id)
            error_msg = "Failed to create agent"
            
            if server_info and server_info.get("process"):
                process = server_info.get("process")
                if process.poll() is not None:
                    _, stderr = process.communicate()
                    if stderr:
                        error_msg = f"Agent server error: {stderr}"
            
            return jsonify({
                "error": error_msg,
                "command": template.get("command").replace("{port}", str(port))
            }), 500
        
        # Get agent details
        agent = agent_manager.registry.get(agent_id)
        
        return jsonify({
            "id": agent_id,
            "name": agent.name,
            "url": agent.url,
            "status": agent.status.name
        })
    
    @blueprint.route('/import_agents', methods=['POST'])
    def import_agents():
        """Import agents from a JSON file."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        if not agent_manager:
            return jsonify({"error": "Agent manager not configured"}), 500
        
        if 'file' not in request.files:
            return jsonify({"error": "No file provided"}), 400
        
        file = request.files['file']
        
        # Save file to temporary location
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            file.save(temp_file.name)
            
            # Import agents
            success, failed = agent_manager.import_agent_collection(temp_file.name)
            
            # Clean up
            os.unlink(temp_file.name)
        
        return jsonify({
            "success": success,
            "failed": failed
        })
    
    @blueprint.route('/export_agents', methods=['POST'])
    def export_agents():
        """Export all registered agents to a JSON file."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        if not agent_manager:
            return jsonify({"error": "Agent manager not configured"}), 500
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            success = agent_manager.export_agent_collection(temp_file.name)
            
            if not success:
                # Clean up and return error
                os.unlink(temp_file.name)
                return jsonify({"error": "Failed to export agents"}), 500
            
            # Read the file
            with open(temp_file.name, 'rb') as f:
                file_data = f.read()
            
            # Clean up
            os.unlink(temp_file.name)
        
        from flask import Response
        response = Response(
            file_data,
            mimetype='application/json',
            headers={
                'Content-Disposition': 'attachment;filename=agent_collection.json'
            }
        )
        
        return response
    
    # Network builder endpoints
    @blueprint.route('/networks', methods=['GET'])
    def list_networks():
        """List all saved networks."""
        network_storage = getattr(current_app.config, 'NETWORK_STORAGE', {})
        networks = list(network_storage.values())
        return jsonify(networks)
    
    @blueprint.route('/networks/<network_id>', methods=['GET'])
    def get_network(network_id):
        """Get a specific network by ID."""
        network_storage = getattr(current_app.config, 'NETWORK_STORAGE', {})
        network = network_storage.get(network_id)
        
        if not network:
            return jsonify({"error": f"Network {network_id} not found"}), 404
        
        return jsonify(network)
    
    @blueprint.route('/networks', methods=['POST'])
    def save_network():
        """Save a network configuration."""
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        if 'name' not in data:
            return jsonify({"error": "Network name is required"}), 400
        
        # Generate a network ID if not provided
        network_id = data.get('id', str(uuid.uuid4()))
        data['id'] = network_id
        
        # Add timestamp
        data['updated_at'] = time.time()
        
        # Store the network
        network_storage = current_app.config.get('NETWORK_STORAGE', {})
        if not current_app.config.get('NETWORK_STORAGE'):
            current_app.config['NETWORK_STORAGE'] = {}
            network_storage = current_app.config['NETWORK_STORAGE']
        
        network_storage[network_id] = data
        
        return jsonify({"id": network_id}), 201
    
    @blueprint.route('/networks/<network_id>', methods=['DELETE'])
    def delete_network(network_id):
        """Delete a network configuration."""
        network_storage = current_app.config.get('NETWORK_STORAGE', {})
        
        if network_id in network_storage:
            del network_storage[network_id]
            return jsonify({"success": True}), 200
        else:
            return jsonify({"error": f"Network {network_id} not found"}), 404
    
    @blueprint.route('/networks/<network_id>/deploy', methods=['POST'])
    def deploy_network(network_id):
        """Deploy a network by creating and connecting all agents."""
        network_storage = current_app.config.get('NETWORK_STORAGE', {})
        agent_manager = current_app.config.get('AGENT_MANAGER')
        agent_registry = current_app.config.get('AGENT_REGISTRY')
        tool_registry = current_app.config.get('TOOL_REGISTRY')
        
        if not agent_manager or not agent_registry or not tool_registry:
            return jsonify({"error": "Agent manager or registries not configured"}), 500
        
        network = network_storage.get(network_id)
        if not network:
            return jsonify({"error": f"Network {network_id} not found"}), 404
        
        # Create agents for each node
        deployed_agents = {}
        deployed_tools = {}
        errors = []
        
        # First pass: create all agents
        for node in network.get('nodes', []):
            try:
                if node.get('type') == 'agent':
                    # Create the agent based on subType
                    agent_type = node.get('subType')
                    config = node.get('config', {})
                    
                    if agent_type == 'openai':
                        # Create OpenAI agent
                        agent = AgentDefinition(
                            name=config.get('name', 'OpenAI Agent'),
                            description=f"OpenAI {config.get('model', 'gpt-4o')} agent",
                            url=f"http://localhost:{config.get('port', 8000)}",
                            agent_source=AgentSource.REMOTE,
                            agent_type="openai"
                        )
                        
                        # Set API key in environment if provided
                        if 'apiKey' in config:
                            os.environ['OPENAI_API_KEY'] = config['apiKey']
                        
                        # Create agent server
                        port = config.get('port', 8000)
                        server_id = agent_manager.create_openai_agent(
                            port=port,
                            model=config.get('model', 'gpt-4o')
                        )
                        
                        if not server_id:
                            errors.append(f"Failed to create OpenAI agent for node {node.get('id')}")
                            continue
                        
                    elif agent_type == 'anthropic':
                        # Create Anthropic agent
                        agent = AgentDefinition(
                            name=config.get('name', 'Claude Agent'),
                            description=f"Anthropic {config.get('model', 'claude-3-opus')} agent",
                            url=f"http://localhost:{config.get('port', 8001)}",
                            agent_source=AgentSource.REMOTE,
                            agent_type="anthropic"
                        )
                        
                        # Set API key in environment if provided
                        if 'apiKey' in config:
                            os.environ['ANTHROPIC_API_KEY'] = config['apiKey']
                        
                        # Create agent server
                        port = config.get('port', 8001)
                        server_id = agent_manager.create_anthropic_agent(
                            port=port,
                            model=config.get('model', 'claude-3-opus')
                        )
                        
                        if not server_id:
                            errors.append(f"Failed to create Anthropic agent for node {node.get('id')}")
                            continue
                        
                    elif agent_type == 'bedrock':
                        # Create Bedrock agent
                        agent = AgentDefinition(
                            name=config.get('name', 'Bedrock Agent'),
                            description=f"AWS Bedrock {config.get('model', '')} agent",
                            url=f"http://localhost:{config.get('port', 8002)}",
                            agent_source=AgentSource.REMOTE,
                            agent_type="bedrock"
                        )
                        
                        # Set AWS credentials in environment if provided
                        if 'accessKey' in config:
                            os.environ['AWS_ACCESS_KEY_ID'] = config['accessKey']
                        if 'secretKey' in config:
                            os.environ['AWS_SECRET_ACCESS_KEY'] = config['secretKey']
                        if 'region' in config:
                            os.environ['AWS_REGION'] = config['region']
                        
                        # Create agent server
                        port = config.get('port', 8002)
                        server_id = agent_manager.create_bedrock_agent(
                            port=port,
                            model=config.get('model', 'anthropic.claude-3-sonnet-20240229-v1:0')
                        )
                        
                        if not server_id:
                            errors.append(f"Failed to create Bedrock agent for node {node.get('id')}")
                            continue
                        
                    elif agent_type == 'custom':
                        # Create custom agent
                        agent = AgentDefinition(
                            name=config.get('name', 'Custom Agent'),
                            description="Custom agent",
                            url=config.get('endpoint', f"http://localhost:{config.get('port', 8003)}"),
                            agent_source=AgentSource.REMOTE,
                            agent_type="custom"
                        )
                        
                        # Create agent server
                        port = config.get('port', 8003)
                        script_path = config.get('script', '')
                        
                        if script_path:
                            server_id = agent_manager.create_from_script(script_path, port)
                        else:
                            server_id = agent_manager.create_custom_agent(port)
                        
                        if not server_id:
                            errors.append(f"Failed to create custom agent for node {node.get('id')}")
                            continue
                    
                    # Register the agent
                    agent_registry.register(agent)
                    deployed_agents[node.get('id')] = agent.id
                    
                elif node.get('type') == 'tool':
                    # Create tool
                    tool_type = node.get('subType')
                    config = node.get('config', {})
                    
                    # Basic tool definition
                    tool = ToolDefinition(
                        name=config.get('name', f"{tool_type.capitalize()} Tool"),
                        description=f"{tool_type.capitalize()} tool functionality",
                        url=config.get('endpoint', "http://localhost:8000"),
                        tool_path=tool_type,
                        tool_source=ToolSource.REMOTE
                    )
                    
                    # Register the tool
                    tool_registry.register(tool)
                    deployed_tools[node.get('id')] = tool.id
            
            except Exception as e:
                errors.append(f"Error creating node {node.get('id')}: {str(e)}")
        
        # Second pass: create connections
        for connection in network.get('connections', []):
            start_node = connection.get('start', {}).get('nodeId')
            end_node = connection.get('end', {}).get('nodeId')
            
            if start_node and end_node:
                # Map to agent/tool IDs
                start_agent_id = deployed_agents.get(start_node)
                end_agent_id = deployed_agents.get(end_node)
                
                # If either end is a tool, handle differently
                if start_node in deployed_tools:
                    start_tool_id = deployed_tools.get(start_node)
                    if end_agent_id:
                        try:
                            # Connect tool to agent
                            agent = agent_registry.get(end_agent_id)
                            tool = tool_registry.get(start_tool_id)
                            if agent and tool:
                                # TODO: Implement tool to agent connection
                                pass
                        except Exception as e:
                            errors.append(f"Error connecting tool {start_node} to agent {end_node}: {str(e)}")
                
                elif end_node in deployed_tools:
                    end_tool_id = deployed_tools.get(end_node)
                    if start_agent_id:
                        try:
                            # Connect agent to tool
                            agent = agent_registry.get(start_agent_id)
                            tool = tool_registry.get(end_tool_id)
                            if agent and tool:
                                # TODO: Implement agent to tool connection
                                pass
                        except Exception as e:
                            errors.append(f"Error connecting agent {start_node} to tool {end_node}: {str(e)}")
                
                else:
                    # Agent to agent connection
                    if start_agent_id and end_agent_id:
                        try:
                            # Create connection between agents
                            start_agent = agent_registry.get(start_agent_id) 
                            end_agent = agent_registry.get(end_agent_id)
                            
                            if start_agent and end_agent:
                                # TODO: Implement agent to agent connection
                                pass
                        except Exception as e:
                            errors.append(f"Error connecting agents {start_node} and {end_node}: {str(e)}")
        
        # Return deployment status
        return jsonify({
            "success": len(errors) == 0,
            "deployed_agents": deployed_agents,
            "deployed_tools": deployed_tools,
            "errors": errors
        })
    
    @blueprint.route('/create_openai_agent', methods=['POST'])
    def create_openai_agent():
        """Create an OpenAI agent with the given configuration."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        agent_registry = current_app.config.get('AGENT_REGISTRY')
        
        if not agent_manager or not agent_registry:
            return jsonify({"error": "Agent manager or registry not configured"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', 'OpenAI Agent')
        api_key = data.get('api_key')
        model = data.get('model', 'gpt-4o')
        port = data.get('port', 8000)
        
        if api_key:
            os.environ['OPENAI_API_KEY'] = api_key
        
        # Create the agent server
        server_id = agent_manager.create_openai_agent(port=port, model=model)
        
        if not server_id:
            return jsonify({"error": "Failed to create OpenAI agent"}), 500
        
        # Create agent definition
        agent = AgentDefinition(
            name=name,
            description=f"OpenAI {model} agent",
            url=f"http://localhost:{port}",
            agent_source=AgentSource.REMOTE,
            agent_type="openai"
        )
        
        # Register the agent
        agent_registry.register(agent)
        
        return jsonify({
            "id": agent.id,
            "name": agent.name,
            "url": agent.url,
            "status": agent.status.name,
            "server_id": server_id
        })
    
    @blueprint.route('/create_anthropic_agent', methods=['POST'])
    def create_anthropic_agent():
        """Create an Anthropic agent with the given configuration."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        agent_registry = current_app.config.get('AGENT_REGISTRY')
        
        if not agent_manager or not agent_registry:
            return jsonify({"error": "Agent manager or registry not configured"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', 'Claude Agent')
        api_key = data.get('api_key')
        model = data.get('model', 'claude-3-opus')
        port = data.get('port', 8001)
        
        if api_key:
            os.environ['ANTHROPIC_API_KEY'] = api_key
        
        # Create the agent server
        server_id = agent_manager.create_anthropic_agent(port=port, model=model)
        
        if not server_id:
            return jsonify({"error": "Failed to create Anthropic agent"}), 500
        
        # Create agent definition
        agent = AgentDefinition(
            name=name,
            description=f"Anthropic {model} agent",
            url=f"http://localhost:{port}",
            agent_source=AgentSource.REMOTE,
            agent_type="anthropic"
        )
        
        # Register the agent
        agent_registry.register(agent)
        
        return jsonify({
            "id": agent.id,
            "name": agent.name,
            "url": agent.url,
            "status": agent.status.name,
            "server_id": server_id
        })
    
    @blueprint.route('/create_bedrock_agent', methods=['POST'])
    def create_bedrock_agent():
        """Create a Bedrock agent with the given configuration."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        agent_registry = current_app.config.get('AGENT_REGISTRY')
        
        if not agent_manager or not agent_registry:
            return jsonify({"error": "Agent manager or registry not configured"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', 'Bedrock Agent')
        access_key = data.get('access_key')
        secret_key = data.get('secret_key')
        region = data.get('region', 'us-east-1')
        model = data.get('model', 'anthropic.claude-3-sonnet-20240229-v1:0')
        port = data.get('port', 8002)
        
        # Set AWS credentials in environment if provided
        if access_key:
            os.environ['AWS_ACCESS_KEY_ID'] = access_key
        if secret_key:
            os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
        if region:
            os.environ['AWS_REGION'] = region
        
        # Create the agent server
        server_id = agent_manager.create_bedrock_agent(port=port, model=model)
        
        if not server_id:
            return jsonify({"error": "Failed to create Bedrock agent"}), 500
        
        # Create agent definition
        agent = AgentDefinition(
            name=name,
            description=f"AWS Bedrock {model} agent",
            url=f"http://localhost:{port}",
            agent_source=AgentSource.REMOTE,
            agent_type="bedrock"
        )
        
        # Register the agent
        agent_registry.register(agent)
        
        return jsonify({
            "id": agent.id,
            "name": agent.name,
            "url": agent.url,
            "status": agent.status.name,
            "server_id": server_id
        })
    
    @blueprint.route('/create_custom_agent', methods=['POST'])
    def create_custom_agent():
        """Create a custom agent with the given configuration."""
        agent_manager = current_app.config.get('AGENT_MANAGER')
        agent_registry = current_app.config.get('AGENT_REGISTRY')
        
        if not agent_manager or not agent_registry:
            return jsonify({"error": "Agent manager or registry not configured"}), 500
        
        data = request.json
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
        
        name = data.get('name', 'Custom Agent')
        port = data.get('port', 8003)
        script_path = data.get('script_path', '')
        endpoint = data.get('endpoint', f"http://localhost:{port}")
        
        # Create the agent server
        if script_path:
            server_id = agent_manager.create_from_script(script_path, port)
        else:
            server_id = agent_manager.create_custom_agent(port)
        
        if not server_id:
            return jsonify({"error": "Failed to create custom agent"}), 500
        
        # Create agent definition
        agent = AgentDefinition(
            name=name,
            description="Custom agent",
            url=endpoint,
            agent_source=AgentSource.REMOTE,
            agent_type="custom"
        )
        
        # Register the agent
        agent_registry.register(agent)
        
        return jsonify({
            "id": agent.id,
            "name": agent.name,
            "url": agent.url,
            "status": agent.status.name,
            "server_id": server_id
        })
    
    return blueprint