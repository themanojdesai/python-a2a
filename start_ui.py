#!/usr/bin/env python
"""
A startup script for Agent Flow UI that ensures imports work properly.
"""

import os
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentFlowUI")

# Add the parent directory to the Python path to allow imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Agent Flow UI - Visual workflow editor for agent networks")
    
    parser.add_argument(
        "--port", "-p",
        type=int,
        default=8080,
        help="Port to run the server on (default: 8080)"
    )
    
    parser.add_argument(
        "--host", "-H",
        default="localhost",
        help="Host to bind the server to (default: localhost)"
    )
    
    parser.add_argument(
        "--storage-dir", "-d",
        default=None,
        help="Directory to store workflow files (default: ~/.agent_flow)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Run in debug mode"
    )
    
    return parser.parse_args()

def main():
    """Run the Agent Flow UI application."""
    args = parse_args()
    
    try:
        # Import Agent Flow components
        from agent_flow.models.agent import AgentRegistry
        from agent_flow.models.tool import ToolRegistry
        from agent_flow.storage.workflow_storage import FileWorkflowStorage
        from agent_flow.engine.executor import WorkflowExecutor
        from agent_flow.server.web import run_web_server
        
        # Set up storage directory
        storage_dir = args.storage_dir
        if not storage_dir:
            home_dir = os.path.expanduser("~")
            storage_dir = os.path.join(home_dir, ".agent_flow")
        
        os.makedirs(storage_dir, exist_ok=True)
        logger.info(f"Using storage directory: {storage_dir}")
        
        # Initialize components
        agent_registry = AgentRegistry()
        tool_registry = ToolRegistry()
        workflow_storage = FileWorkflowStorage(
            os.path.join(storage_dir, "workflows")
        )
        workflow_executor = WorkflowExecutor(
            agent_registry, tool_registry
        )
        
        # Start web server
        logger.info(f"Starting web server at http://{args.host}:{args.port}")
        run_web_server(
            agent_registry,
            tool_registry,
            workflow_storage,
            workflow_executor,
            host=args.host,
            port=args.port,
            debug=args.debug
        )
    except ImportError as e:
        logger.error(f"Import error: {e}")
        logger.error("Make sure you're in the correct directory and that Agent Flow is installed.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error starting Agent Flow UI: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()