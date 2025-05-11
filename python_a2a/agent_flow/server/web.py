"""
Web UI for Agent Flow.

This module provides a Flask-based web interface for creating and managing
agent workflows with a visual drag-and-drop editor.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple, Union

from flask import Flask, request, jsonify, render_template, send_from_directory, Blueprint

from ..models.agent import AgentRegistry, AgentStatus
from ..models.tool import ToolRegistry, ToolStatus
from ..models.workflow import Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
from ..engine.executor import WorkflowExecutor
from ..storage.workflow_storage import WorkflowStorage
from ..utils.agent_manager import AgentManager
from .api import create_agent_blueprint, create_tool_blueprint, create_workflow_blueprint, create_execution_blueprint
from .agent_api import create_agent_manager_blueprint


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentFlowWebUI")


def create_web_app(
    agent_registry: AgentRegistry,
    tool_registry: ToolRegistry,
    workflow_storage: WorkflowStorage,
    workflow_executor: WorkflowExecutor,
    static_folder: Optional[str] = None,
    template_folder: Optional[str] = None
):
    """
    Create a Flask application for the Agent Flow Web UI.
    
    Args:
        agent_registry: Registry of available agents
        tool_registry: Registry of available tools
        workflow_storage: Storage service for workflows
        workflow_executor: Executor for running workflows
        static_folder: Directory for static files
        template_folder: Directory for template files
        
    Returns:
        Flask application
    """
    # Determine static and template folders
    if static_folder is None:
        static_folder = os.path.join(os.path.dirname(__file__), 'static')
    
    if template_folder is None:
        template_folder = os.path.join(os.path.dirname(__file__), 'templates')
    
    app = Flask(
        __name__,
        static_folder=static_folder,
        template_folder=template_folder
    )
    
    # Configure CORS
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        logger.warning("Flask-CORS not installed. CORS support disabled.")
    
    # Create agent manager
    agent_manager = AgentManager(agent_registry)
    
    # Store registries and services in application context
    app.config['AGENT_REGISTRY'] = agent_registry
    app.config['TOOL_REGISTRY'] = tool_registry
    app.config['WORKFLOW_STORAGE'] = workflow_storage
    app.config['WORKFLOW_EXECUTOR'] = workflow_executor
    app.config['AGENT_MANAGER'] = agent_manager
    
    # Register API blueprints
    app.register_blueprint(create_agent_blueprint(), url_prefix='/api/agents')
    app.register_blueprint(create_tool_blueprint(), url_prefix='/api/tools')
    app.register_blueprint(create_workflow_blueprint(), url_prefix='/api/workflows')
    app.register_blueprint(create_execution_blueprint(), url_prefix='/api/executions')
    app.register_blueprint(create_agent_manager_blueprint(), url_prefix='/api')
    
    # Web UI routes
    @app.route('/')
    def index():
        """Render the main workflow editor page."""
        return render_template('index.html')
    
    @app.route('/workflows')
    def workflows_list():
        """Render the workflows list page."""
        return render_template('workflows.html')
    
    @app.route('/agents')
    def agents_list():
        """Render the agents list page."""
        return render_template('agents.html')
    
    @app.route('/tools')
    def tools_list():
        """Render the tools list page."""
        return render_template('tools.html')
    
    @app.route('/executions')
    def executions_list():
        """Render the executions list page."""
        return render_template('executions.html')
    
    @app.route('/favicon.ico')
    def favicon():
        """Serve the favicon."""
        return send_from_directory(
            os.path.join(app.root_path, 'static', 'images'),
            'favicon.ico', mimetype='image/vnd.microsoft.icon'
        )
    
    # Error handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def server_error(e):
        return render_template('500.html'), 500
    
    # Start agent monitoring
    agent_manager.start_monitoring()
    
    return app


def run_web_server(
    agent_registry: AgentRegistry,
    tool_registry: ToolRegistry,
    workflow_storage: WorkflowStorage,
    workflow_executor: WorkflowExecutor,
    host: str = 'localhost',
    port: int = 8080,
    debug: bool = False
):
    """
    Run the web server for the Agent Flow Web UI.
    
    Args:
        agent_registry: Registry of available agents
        tool_registry: Registry of available tools
        workflow_storage: Storage service for workflows
        workflow_executor: Executor for running workflows
        host: Host to bind to
        port: Port to listen on
        debug: Whether to run in debug mode
    """
    app = create_web_app(
        agent_registry,
        tool_registry,
        workflow_storage,
        workflow_executor
    )
    
    logger.info(f"Starting web server at http://{host}:{port}")
    
    try:
        app.run(host=host, port=port, debug=debug)
    finally:
        # Stop all agent servers on shutdown
        agent_manager = app.config.get('AGENT_MANAGER')
        if agent_manager:
            logger.info("Stopping agent monitoring")
            agent_manager.stop_monitoring()
            
            logger.info("Stopping all agent servers")
            agent_manager.stop_all_servers()