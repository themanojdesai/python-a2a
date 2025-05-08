"""
Agent Manager module for creating, connecting, and managing a2a agents.

This module provides utilities for easily creating and managing agents,
with auto-registration and status monitoring.
"""

import os
import time
import json
import logging
import threading
import subprocess
from typing import Dict, List, Optional, Any, Tuple, Union

import requests
from python_a2a import AgentCard, AgentSkill, A2AClient

from ..models.agent import AgentDefinition, AgentRegistry, AgentSource, AgentStatus


logger = logging.getLogger("AgentManager")


class AgentManager:
    """
    Manager for creating and controlling A2A agents.
    
    This class provides methods to:
    - Create agents from templates
    - Start agent servers
    - Connect to remote agents
    - Monitor agent health
    - Import/export agent configurations
    """
    
    def __init__(self, agent_registry: AgentRegistry):
        """
        Initialize the agent manager.
        
        Args:
            agent_registry: Registry to use for agent management
        """
        self.registry = agent_registry
        self.running_servers: Dict[str, Dict[str, Any]] = {}
        self.monitor_thread = None
        self.should_monitor = False
    
    def create_from_template(self, template_name: str, port: int, script_path: Optional[str] = None) -> Optional[str]:
        """
        Create an agent from a template and start it.
        
        Args:
            template_name: Name of the template to use
            port: Port to run the agent on
            script_path: Optional path to custom script (for custom_script template)
            
        Returns:
            Agent ID if successful, None otherwise
        """
        # Get template configuration
        template = self.get_template(template_name)
        if not template:
            logger.error(f"Template '{template_name}' not found")
            return None
        
        # Handle command with script path if needed
        command = template.get("command", "")
        if template_name == "custom_script" and script_path:
            command = command.replace("{script_path}", script_path)
        
        # Start agent server
        agent_id = self.start_agent_server(
            command,
            port,
            template.get("name", "Unnamed Agent"),
            template.get("description", "")
        )
        
        return agent_id
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """
        Get a list of available agent templates.
        
        Returns:
            List of template configurations
        """
        templates = [
            {
                "id": "simple_server", 
                "name": "Simple A2A Agent",
                "description": "Basic A2A agent that responds to messages",
                "command": "python3 examples/getting_started/simple_server.py --port {port}"
            },
            {
                "id": "function_calling",
                "name": "Function Calling Agent",
                "description": "A2A agent that supports function calling",
                "command": "python3 examples/getting_started/function_calling.py --port {port}"
            },
            {
                "id": "streaming",
                "name": "Streaming Agent",
                "description": "A2A agent with streaming response support",
                "command": "python3 examples/streaming/basic_streaming.py --port {port}"
            },
            {
                "id": "knowledge",
                "name": "Knowledge Agent",
                "description": "Answers general knowledge questions",
                "command": "python3 examples/building_blocks/agent_skills.py --port {port}"
            },
            {
                "id": "custom_script",
                "name": "Custom Script Agent",
                "description": "Run a custom script as an agent",
                "command": "{script_path} --port {port}"
            }
        ]
        
        # Check for LLM integrations
        try:
            # Try to import OpenAI integration
            from python_a2a.server.llm import OpenAIA2AServer
            templates.append({
                "id": "openai",
                "name": "OpenAI Agent",
                "description": "GPT-powered agent with OpenAI",
                "command": "python3 examples/ai_powered_agents/openai_agent.py --port {port}",
                "requires_api_key": True,
                "api_key_env": "OPENAI_API_KEY"
            })
        except ImportError:
            pass
        
        try:
            # Try to import Anthropic integration
            from python_a2a.server.llm import AnthropicA2AServer
            templates.append({
                "id": "anthropic",
                "name": "Anthropic Claude Agent",
                "description": "Claude-powered agent with Anthropic",
                "command": "python3 examples/ai_powered_agents/anthropic_agent.py --port {port}",
                "requires_api_key": True,
                "api_key_env": "ANTHROPIC_API_KEY"
            })
        except ImportError:
            pass
        
        return templates
    
    def get_template(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific template by ID.
        
        Args:
            template_id: ID of the template to get
            
        Returns:
            Template configuration or None if not found
        """
        templates = self.get_available_templates()
        for template in templates:
            if template["id"] == template_id:
                return template
        return None
    
    def start_agent_server(
        self, 
        command: str, 
        port: int, 
        name: str = "Unnamed Agent",
        description: str = ""
    ) -> Optional[str]:
        """
        Start an agent server with the given command.
        
        Args:
            command: Command to run (with {port} placeholder)
            port: Port to run the agent on
            name: Name for the agent
            description: Description of the agent
            
        Returns:
            Agent ID if started successfully, None otherwise
        """
        # Replace port placeholder
        command = command.replace("{port}", str(port))
        
        try:
            # Log the command being executed
            logger.info(f"Starting agent server with command: {command}")
            
            # Start the server process
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )
            
            # Store process info
            server_id = f"server_{int(time.time())}_{port}"
            self.running_servers[server_id] = {
                "process": process,
                "command": command,
                "port": port,
                "name": name,
                "description": description,
                "start_time": time.time()
            }
            
            # Check for immediate error
            time.sleep(0.5)
            if process.poll() is not None:
                # Process already exited - read error output
                _, stderr = process.communicate()
                logger.error(f"Agent server process exited immediately: {stderr}")
                return None
            
            # Give it time to start
            time.sleep(2)
            
            # Try to connect to it
            agent_url = f"http://localhost:{port}"
            agent = AgentDefinition(
                name=name,
                description=description,
                url=agent_url,
                agent_source=AgentSource.LOCAL
            )
            
            # Try to connect a few times
            for i in range(3):
                if agent.connect():
                    break
                time.sleep(1)
            
            # Register agent
            if agent.status == AgentStatus.CONNECTED:
                self.registry.register(agent)
                self.running_servers[server_id]["agent_id"] = agent.id
                logger.info(f"Started agent server at {agent_url}")
                return agent.id
            else:
                logger.warning(f"Agent server started but couldn't connect. URL: {agent_url}")
                return None
        
        except Exception as e:
            logger.error(f"Error starting agent server: {e}")
            return None
    
    def stop_agent_server(self, server_id: str) -> bool:
        """
        Stop a running agent server.
        
        Args:
            server_id: ID of the server to stop
            
        Returns:
            True if stopped successfully, False otherwise
        """
        if server_id not in self.running_servers:
            return False
        
        server_info = self.running_servers[server_id]
        process = server_info.get("process")
        agent_id = server_info.get("agent_id")
        
        # Terminate the process
        if process:
            try:
                process.terminate()
                process.wait(timeout=5)
                logger.info(f"Stopped agent server {server_id}")
            except Exception as e:
                logger.error(f"Error stopping agent server {server_id}: {e}")
                try:
                    process.kill()
                except:
                    pass
        
        # Unregister the agent
        if agent_id:
            self.registry.unregister(agent_id)
        
        # Remove from running servers
        del self.running_servers[server_id]
        return True
    
    def stop_all_servers(self) -> None:
        """Stop all running agent servers."""
        server_ids = list(self.running_servers.keys())
        for server_id in server_ids:
            self.stop_agent_server(server_id)
    
    def create_openai_agent(self, port: int, model: str = "gpt-4o") -> Optional[str]:
        """
        Create an OpenAI-powered agent.
        
        Args:
            port: Port to run the agent on
            model: OpenAI model to use
            
        Returns:
            Server ID if successful, None otherwise
        """
        # Check if OpenAI API key is set
        if not os.environ.get("OPENAI_API_KEY"):
            logger.warning("OPENAI_API_KEY environment variable not set")
        
        command = f"python3 examples/ai_powered_agents/openai_agent.py --port {port} --model {model}"
        
        # Start the agent server
        return self.start_agent_server(
            command,
            port,
            f"OpenAI {model} Agent",
            f"GPT-powered A2A agent using {model}"
        )
    
    def create_anthropic_agent(self, port: int, model: str = "claude-3-opus") -> Optional[str]:
        """
        Create an Anthropic Claude-powered agent.
        
        Args:
            port: Port to run the agent on
            model: Claude model to use
            
        Returns:
            Server ID if successful, None otherwise
        """
        # Check if Anthropic API key is set
        if not os.environ.get("ANTHROPIC_API_KEY"):
            logger.warning("ANTHROPIC_API_KEY environment variable not set")
        
        command = f"python3 examples/ai_powered_agents/anthropic_agent.py --port {port} --model {model}"
        
        # Start the agent server
        return self.start_agent_server(
            command,
            port,
            f"Claude {model} Agent",
            f"Claude-powered A2A agent using {model}"
        )
    
    def create_bedrock_agent(self, port: int, model: str = "anthropic.claude-3-sonnet-20240229-v1:0") -> Optional[str]:
        """
        Create an AWS Bedrock-powered agent.
        
        Args:
            port: Port to run the agent on
            model: Bedrock model to use
            
        Returns:
            Server ID if successful, None otherwise
        """
        # Check if AWS credentials are set
        if not os.environ.get("AWS_ACCESS_KEY_ID") or not os.environ.get("AWS_SECRET_ACCESS_KEY"):
            logger.warning("AWS credentials not fully set in environment variables")
        
        command = f"python3 examples/ai_powered_agents/bedrock_agent.py --port {port} --model {model}"
        
        # Start the agent server
        return self.start_agent_server(
            command,
            port,
            f"Bedrock {model.split('.')[-1]} Agent",
            f"AWS Bedrock-powered A2A agent using {model}"
        )
    
    def create_custom_agent(self, port: int) -> Optional[str]:
        """
        Create a basic custom agent.
        
        Args:
            port: Port to run the agent on
            
        Returns:
            Server ID if successful, None otherwise
        """
        command = f"python3 examples/getting_started/simple_server.py --port {port}"
        
        # Start the agent server
        return self.start_agent_server(
            command,
            port,
            "Custom Agent",
            "Custom A2A agent"
        )
    
    def create_from_script(self, script_path: str, port: int) -> Optional[str]:
        """
        Create an agent from a custom script.
        
        Args:
            script_path: Path to the script file
            port: Port to run the agent on
            
        Returns:
            Server ID if successful, None otherwise
        """
        # Check if script exists
        if not os.path.exists(script_path):
            logger.error(f"Script file not found: {script_path}")
            return None
        
        command = f"{script_path} --port {port}"
        
        # Start the agent server
        return self.start_agent_server(
            command,
            port,
            "Custom Script Agent",
            f"Agent from custom script: {os.path.basename(script_path)}"
        )
    
    def get_running_servers(self) -> List[Dict[str, Any]]:
        """
        Get a list of running agent servers.
        
        Returns:
            List of server information
        """
        result = []
        for server_id, info in self.running_servers.items():
            # Exclude process object from result
            server_info = {
                k: v for k, v in info.items() 
                if k != "process"
            }
            server_info["id"] = server_id
            
            # Check if process is still running
            process = info.get("process")
            if process:
                server_info["status"] = "running" if process.poll() is None else "stopped"
            else:
                server_info["status"] = "unknown"
            
            result.append(server_info)
        
        return result
    
    def import_agent_collection(self, file_path: str) -> Tuple[int, int]:
        """
        Import a collection of agent definitions from a file.
        
        Args:
            file_path: Path to the JSON file with agent definitions
            
        Returns:
            Tuple of (success_count, fail_count)
        """
        success = 0
        failed = 0
        
        try:
            with open(file_path, "r") as f:
                data = json.load(f)
            
            agents = data.get("agents", [])
            for agent_data in agents:
                try:
                    agent = AgentDefinition.from_dict(agent_data)
                    self.registry.register(agent)
                    success += 1
                except Exception as e:
                    logger.error(f"Error importing agent: {e}")
                    failed += 1
        
        except Exception as e:
            logger.error(f"Error importing agents: {e}")
            failed += 1
        
        return success, failed
    
    def export_agent_collection(self, file_path: str) -> bool:
        """
        Export all registered agents to a file.
        
        Args:
            file_path: Path to save the JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            data = {
                "agents": [
                    agent.to_dict() 
                    for agent in self.registry.list_agents()
                ]
            }
            
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            logger.error(f"Error exporting agents: {e}")
            return False
    
    def start_monitoring(self, interval: int = 30) -> None:
        """
        Start monitoring agent health in the background.
        
        Args:
            interval: Check interval in seconds
        """
        if self.monitor_thread and self.monitor_thread.is_alive():
            return
        
        self.should_monitor = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop,
            args=(interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self) -> None:
        """Stop monitoring agent health."""
        self.should_monitor = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1)
            self.monitor_thread = None
    
    def _monitor_loop(self, interval: int) -> None:
        """
        Background loop for monitoring agent health.
        
        Args:
            interval: Check interval in seconds
        """
        while self.should_monitor:
            # Check server processes
            for server_id, info in list(self.running_servers.items()):
                process = info.get("process")
                if process and process.poll() is not None:
                    # Process has terminated
                    logger.warning(f"Agent server {server_id} has stopped")
                    
                    # Unregister the agent
                    agent_id = info.get("agent_id")
                    if agent_id:
                        self.registry.unregister(agent_id)
                    
                    # Remove from running servers
                    del self.running_servers[server_id]
            
            # Check agent connections
            for agent in self.registry.list_agents():
                if agent.status != AgentStatus.CONNECTED:
                    # Try to reconnect
                    agent.connect()
            
            # Sleep until next check
            for _ in range(interval):
                if not self.should_monitor:
                    break
                time.sleep(1)