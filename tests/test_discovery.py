"""
Test agent discovery functionality.
"""

import unittest
import time
import threading
import asyncio
from unittest.mock import patch, MagicMock

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False

from python_a2a import AgentCard, A2AServer
from python_a2a.discovery import AgentRegistry, enable_discovery, DiscoveryClient, run_registry
from python_a2a.models.message import Message, MessageRole, TextContent


class TestAgentDiscovery(unittest.TestCase):
    """Test agent discovery functionality."""
    
    def setUp(self):
        """Set up test environment."""
        # Create registry
        self.registry = AgentRegistry(name="Test Registry")
        
        # Create test agent cards
        self.agent1_card = AgentCard(
            name="Test Agent 1",
            description="Test agent 1",
            url="http://localhost:5001",
            version="1.0.0"
        )
        
        self.agent2_card = AgentCard(
            name="Test Agent 2",
            description="Test agent 2",
            url="http://localhost:5002",
            version="1.0.0"
        )
    
    def test_registry_init(self):
        """Test registry initialization."""
        self.assertEqual(self.registry.agent_card.name, "Test Registry")
        self.assertTrue(self.registry.agent_card.capabilities.get("agent_discovery"))
        self.assertTrue(self.registry.agent_card.capabilities.get("registry"))
    
    def test_registry_register_unregister(self):
        """Test agent registration and unregistration."""
        # Register agents
        result1 = self.registry.register_agent(self.agent1_card)
        result2 = self.registry.register_agent(self.agent2_card)
        
        self.assertTrue(result1)
        self.assertTrue(result2)
        self.assertEqual(len(self.registry.agents), 2)
        
        # Check if agents were registered
        all_agents = self.registry.get_all_agents()
        self.assertEqual(len(all_agents), 2)
        
        # Check specific agent
        agent1 = self.registry.get_agent("http://localhost:5001")
        self.assertEqual(agent1.name, "Test Agent 1")
        
        # Unregister agent
        result = self.registry.unregister_agent("http://localhost:5001")
        self.assertTrue(result)
        self.assertEqual(len(self.registry.agents), 1)
        
        # Check non-existent agent
        result = self.registry.unregister_agent("http://localhost:9999")
        self.assertFalse(result)
    
    def test_registry_prune(self):
        """Test pruning inactive agents."""
        # Register agents
        self.registry.register_agent(self.agent1_card)
        self.registry.register_agent(self.agent2_card)
        
        # Modify last_seen for one agent to be older
        self.registry.last_seen["http://localhost:5001"] = time.time() - 400  # 400 seconds ago
        
        # Prune inactive agents (default max_age is 300 seconds)
        pruned = self.registry.prune_inactive_agents()
        self.assertEqual(pruned, 1)
        self.assertEqual(len(self.registry.agents), 1)
        self.assertNotIn("http://localhost:5001", self.registry.agents)
    
    @unittest.skipIf(not HAS_REQUESTS, "requests not installed")
    def test_discovery_client(self):
        """Test discovery client functionality."""
        # Create test discovery client
        client = DiscoveryClient(self.agent1_card)
        
        # Add registry
        client.add_registry("http://localhost:8000")
        self.assertEqual(len(client.registry_urls), 1)
        
        # Remove registry
        result = client.remove_registry("http://localhost:8000")
        self.assertTrue(result)
        self.assertEqual(len(client.registry_urls), 0)
        
        # Test non-existent registry
        result = client.remove_registry("http://localhost:9999")
        self.assertFalse(result)
    
    @unittest.skipIf(not HAS_REQUESTS, "requests not installed")
    @patch('requests.post')
    def test_client_register(self, mock_post):
        """Test client registration with mock."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        # Create client and register
        client = DiscoveryClient(self.agent1_card)
        client.add_registry("http://localhost:8000")
        results = client.register()
        
        # Check results
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"])
        
        # Check mock call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:8000/registry/register")
        self.assertEqual(kwargs["json"], self.agent1_card.to_dict())
    
    @unittest.skipIf(not HAS_REQUESTS, "requests not installed")
    @patch('requests.post')
    def test_client_heartbeat(self, mock_post):
        """Test client heartbeat with mock."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"success": True}
        mock_post.return_value = mock_response
        
        # Create client and send heartbeat
        client = DiscoveryClient(self.agent1_card)
        client.add_registry("http://localhost:8000")
        results = client.heartbeat()
        
        # Check results
        self.assertEqual(len(results), 1)
        self.assertTrue(results[0]["success"])
        
        # Check mock call
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(args[0], "http://localhost:8000/registry/heartbeat")
        self.assertEqual(kwargs["json"]["url"], self.agent1_card.url)
    
    @unittest.skipIf(not HAS_REQUESTS, "requests not installed")
    @patch('requests.get')
    def test_client_discover(self, mock_get):
        """Test client discovery with mock."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            self.agent1_card.to_dict(),
            self.agent2_card.to_dict()
        ]
        mock_get.return_value = mock_response
        
        # Create client and discover
        client = DiscoveryClient(self.agent1_card)
        client.add_registry("http://localhost:8000")
        agents = client.discover()
        
        # Check results
        self.assertEqual(len(agents), 2)
        self.assertEqual(agents[0].name, "Test Agent 1")
        self.assertEqual(agents[1].name, "Test Agent 2")
        
        # Check mock call
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        self.assertEqual(args[0], "http://localhost:8000/registry/agents")
    
    def test_enable_discovery(self):
        """Test enabling discovery on an agent."""
        # Create test agent
        agent = A2AServer(agent_card=self.agent1_card)
        
        # Enable discovery
        client = enable_discovery(agent)
        
        # Check that capabilities were added
        self.assertTrue(agent.agent_card.capabilities.get("agent_discovery"))
        
        # Check that discovery client was attached
        self.assertTrue(hasattr(agent, "discovery_client"))
        self.assertIs(agent.discovery_client, client)
        
        # Check that setup_routes was enhanced
        self.assertTrue(hasattr(agent, "setup_routes"))
        self.assertTrue(hasattr(agent, "_original_setup_routes"))


class TestDiscoveryIntegration(unittest.TestCase):
    """Integration tests for agent discovery."""
    
    @unittest.skipIf(not HAS_REQUESTS, "requests not installed")
    def test_full_discovery_flow(self):
        """
        Test full discovery flow with real HTTP requests.
        
        This test starts a registry server and tests the full discovery flow.
        """
        # Use a timeout for the whole test (to avoid hanging)
        import threading
        done_event = threading.Event()
        
        def registry_thread():
            """Run the registry server in a thread."""
            try:
                # Create registry
                registry = AgentRegistry(name="Integration Test Registry")
                
                # Run registry (will be stopped after test)
                registry.run(host="localhost", port=8765, debug=False)
            except Exception as e:
                print(f"Error in registry thread: {e}")
            finally:
                done_event.set()
        
        # Start registry server in separate thread
        thread = threading.Thread(target=registry_thread)
        thread.daemon = True
        thread.start()
        
        # Give registry time to start
        time.sleep(1)
        
        try:
            # Create test agent
            agent_card = AgentCard(
                name="Integration Test Agent",
                description="Test agent for integration tests",
                url="http://localhost:8766",
                version="1.0.0"
            )
            
            # Create discovery client
            client = DiscoveryClient(agent_card)
            client.add_registry("http://localhost:8765")
            
            # Register with registry
            results = client.register()
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].get("success", False))
            
            # Discover agents
            agents = client.discover()
            self.assertEqual(len(agents), 1)
            self.assertEqual(agents[0].name, "Integration Test Agent")
            
            # Send heartbeat
            results = client.heartbeat()
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].get("success", False))
            
            # Unregister
            results = client.unregister()
            self.assertEqual(len(results), 1)
            self.assertTrue(results[0].get("success", False))
            
        except Exception as e:
            self.fail(f"Integration test failed: {e}")
        finally:
            # Stop registry server
            requests.get("http://localhost:8765/exit")
            done_event.wait(timeout=5)


if __name__ == "__main__":
    unittest.main()