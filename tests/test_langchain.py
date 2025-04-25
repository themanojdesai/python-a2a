"""
Tests for the LangChain integration module.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock

try:
    import langchain
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Skip tests if LangChain is not installed
pytestmark = pytest.mark.skipif(not LANGCHAIN_AVAILABLE, reason="LangChain not installed")

# Import the components to test
from python_a2a.langchain import ToolServer, LangChainBridge, AgentFlow


class TestToolServer:
    """Tests for the ToolServer class."""
    
    def test_initialization(self):
        """Test initializing a ToolServer."""
        # Create a mock BaseTool
        mock_tool = Mock()
        mock_tool.name = "test_tool"
        mock_tool.description = "A test tool"
        mock_tool._run = Mock(return_value="Tool result")
        
        # Initialize a ToolServer
        server = ToolServer(name="Test Server", description="Test Description")
        
        # Check basic properties
        assert server.name == "Test Server"
        assert server.description == "Test Description"
        
        # Register the mock tool
        server.register_tool(mock_tool)
        
        # Check if tool was registered
        assert mock_tool.name in server.tools_map
        assert server.tools_map[mock_tool.name] == mock_tool
    
    def test_from_tools(self):
        """Test creating a ToolServer from a list of tools."""
        # Create mock tools
        mock_tool1 = Mock()
        mock_tool1.name = "tool1"
        mock_tool1.description = "Tool 1"
        mock_tool1._run = Mock(return_value="Tool 1 result")
        
        mock_tool2 = Mock()
        mock_tool2.name = "tool2"
        mock_tool2.description = "Tool 2"
        mock_tool2._run = Mock(return_value="Tool 2 result")
        
        # Create ToolServer from tools
        server = ToolServer.from_tools(
            [mock_tool1, mock_tool2],
            name="Tools Server",
            description="Server with tools"
        )
        
        # Check if both tools were registered
        assert mock_tool1.name in server.tools_map
        assert mock_tool2.name in server.tools_map
        assert len(server.tools_map) == 2


class TestLangChainBridge:
    """Tests for the LangChainBridge class."""
    
    def test_agent_to_a2a(self):
        """Test converting a LangChain agent to an A2A agent."""
        # Create a mock AgentExecutor
        mock_agent = Mock()
        mock_agent.run = Mock(return_value="Agent response")
        
        # Convert to A2A
        with patch('python_a2a.server.A2AServer'):
            a2a_agent = LangChainBridge.agent_to_a2a(mock_agent, name="Test Agent")
            
            # Check basic properties
            assert a2a_agent.name == "Test Agent"
            assert a2a_agent.agent_executor == mock_agent
    
    def test_agent_to_tool(self):
        """Test converting an A2A agent to a LangChain tool."""
        # Mock the A2AClient
        with patch('python_a2a.client.A2AClient') as mock_client_class:
            # Configure the mock
            mock_client = Mock()
            mock_client.get_agent_info = Mock(return_value={
                "name": "Mock Agent",
                "description": "A mock agent"
            })
            mock_client.ask = Mock(return_value="Agent response")
            mock_client_class.return_value = mock_client
            
            # Convert to LangChain tool
            tool = LangChainBridge.agent_to_tool("http://localhost:5000")
            
            # Check basic properties
            assert tool.name == "Mock Agent"
            assert tool.description == "A mock agent"
            
            # Test the tool
            result = tool._run("test query")
            assert result == "Agent response"
            mock_client.ask.assert_called_once_with("test query")


class TestAgentFlow:
    """Tests for the AgentFlow class."""
    
    def test_initialization(self):
        """Test initializing an AgentFlow."""
        # Create a mock AgentNetwork
        mock_network = Mock()
        mock_network.name = "Test Network"
        
        # Initialize AgentFlow
        flow = AgentFlow(agent_network=mock_network, name="Test Flow")
        
        # Check basic properties
        assert flow.name == "Test Flow"
        assert flow.agent_network == mock_network
    
    @pytest.mark.asyncio
    async def test_add_langchain_step(self):
        """Test adding a LangChain step to a flow."""
        # Create a mock LangChain component
        mock_chain = Mock()
        mock_chain.run = Mock(return_value="Chain result")
        
        # Create a mock agent network
        mock_network = Mock()
        
        # Create flow
        flow = AgentFlow(agent_network=mock_network, name="Test Flow")
        
        # Add LangChain step
        result_flow = flow.add_langchain_step(mock_chain, "test input {var}")
        
        # Verify method chaining works
        assert result_flow == flow
        
        # Verify step was added
        assert len(flow.steps) == 1
        assert flow.steps[0].type == "FUNCTION"
    
    @pytest.mark.asyncio
    async def test_add_tool_step(self):
        """Test adding a tool step to a flow."""
        # Create a mock agent network
        mock_network = Mock()
        
        # Create flow
        flow = AgentFlow(agent_network=mock_network, name="Test Flow")
        
        # Add tool step
        result_flow = flow.add_tool_step("server.tool", param1="value1")
        
        # Verify method chaining works
        assert result_flow == flow
        
        # Verify step was added
        assert len(flow.steps) == 1
        assert flow.steps[0].type == "FUNCTION"


if __name__ == "__main__":
    pytest.main(["-xvs", __file__])