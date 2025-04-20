MCP Integration
==============

This guide explains how to use the Model Context Protocol (MCP) integration in Python A2A.

What is MCP?
-----------

The Model Context Protocol (MCP) is a standardized way for AI agents to access external tools and data sources. It allows agents to:

- Call functions and tools
- Access resources and data
- Extend their capabilities beyond their built-in knowledge

Python A2A provides comprehensive support for MCP through the ``FastMCP`` implementation and the ``A2AMCPAgent`` class.

Creating an MCP Server
--------------------

The ``FastMCP`` class makes it easy to create an MCP server with tools:

.. code-block:: python

    from python_a2a.mcp import FastMCP, text_response
    
    # Create an MCP server
    calculator_mcp = FastMCP(
        name="Calculator MCP",
        description="Provides calculation functions"
    )
    
    # Add a tool
    @calculator_mcp.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b
    
    # Add another tool
    @calculator_mcp.tool()
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers together."""
        return a * b
    
    # Run the server
    if __name__ == "__main__":
        calculator_mcp.run(host="0.0.0.0", port=5001)

This creates an MCP server that provides two tools: ``add`` and ``multiply``.

Connecting to an MCP Server
-------------------------

To connect to an MCP server, use the ``MCPClient``:

.. code-block:: python

    from python_a2a.mcp import MCPClient
    
    # Create a client
    client = MCPClient("http://localhost:5001")
    
    # Call a tool
    result = await client.call_tool("add", a=5, b=3)
    print(result)  # 8
    
    # Call another tool
    result = await client.call_tool("multiply", a=5, b=3)
    print(result)  # 15

Creating an A2A Agent with MCP
----------------------------

The ``A2AMCPAgent`` class makes it easy to create an A2A agent that can use MCP tools:

.. code-block:: python

    from python_a2a import A2AServer, A2AMCPAgent, AgentCard, run_server
    from python_a2a import TaskStatus, TaskState
    
    # Create an A2A agent with MCP capabilities
    class CalculatorAgent(A2AServer, A2AMCPAgent):
        def __init__(self):
            # Create the agent card
            agent_card = AgentCard(
                name="Calculator Agent",
                description="An agent that performs calculations",
                url="http://localhost:5000",
                version="1.0.0"
            )
            
            # Initialize A2AServer
            A2AServer.__init__(self, agent_card=agent_card)
            
            # Initialize A2AMCPAgent with MCP servers
            A2AMCPAgent.__init__(
                self, 
                name="Calculator Agent",
                description="An agent that performs calculations",
                mcp_servers={"calc": "http://localhost:5001"}
            )
        
        async def handle_task_async(self, task):
            try:
                # Extract message text
                text = task.message.get("content", {}).get("text", "")
                
                if "add" in text.lower():
                    # Extract numbers
                    import re
                    numbers = [float(n) for n in re.findall(r"[-+]?\d*\.?\d+", text)]
                    
                    if len(numbers) >= 2:
                        # Call MCP tool
                        result = await self.call_mcp_tool("calc", "add", a=numbers[0], b=numbers[1])
                        
                        # Create response
                        task.artifacts = [{
                            "parts": [{"type": "text", "text": f"The sum is {result}"}]
                        }]
                        task.status = TaskStatus(state=TaskState.COMPLETED)
                        return task
                
                # Default response
                task.artifacts = [{
                    "parts": [{"type": "text", "text": "I can help with calculations."}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
                return task
                
            except Exception as e:
                # Handle errors
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"Error: {str(e)}"}]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
                return task
        
        def handle_task(self, task):
            # Convert sync to async
            import asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.handle_task_async(task))
    
    # Run the agent
    if __name__ == "__main__":
        agent = CalculatorAgent()
        run_server(agent, port=5000)

This creates an A2A agent that can call tools on the MCP server we created earlier.

Alternative: Inline MCP Server
----------------------------

You can also create an MCP server inline with your A2A agent:

.. code-block:: python

    from python_a2a import A2AServer, A2AMCPAgent, AgentCard, run_server
    from python_a2a.mcp import FastMCP, text_response
    
    # Create MCP server
    calculator_mcp = FastMCP(
        name="Calculator MCP",
        description="Provides calculation functions"
    )
    
    @calculator_mcp.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b
    
    # Create A2A agent with inline MCP server
    class CalculatorAgent(A2AServer, A2AMCPAgent):
        def __init__(self):
            # Create the agent card
            agent_card = AgentCard(
                name="Calculator Agent",
                description="An agent that performs calculations",
                url="http://localhost:5000",
                version="1.0.0"
            )
            
            # Initialize A2AServer
            A2AServer.__init__(self, agent_card=agent_card)
            
            # Initialize A2AMCPAgent with inline MCP server
            A2AMCPAgent.__init__(
                self, 
                name="Calculator Agent",
                description="An agent that performs calculations",
                mcp_servers={"calc": calculator_mcp}
            )
        
        # ... rest of the implementation

This approach doesn't require running a separate MCP server.

Additional Features
-----------------

MCP supports more advanced features:

- **Resources**: Access to data sources via URIs
- **Streaming**: Stream responses for long-running operations
- **Templates**: Parameterized resource URIs

For more information, refer to the :doc:`../api/mcp` API reference.

Next Steps
---------

Now that you understand MCP integration, you can:

- Build tool-using agents
- Connect agents to external data sources
- Create complex agent ecosystems

Check out the :doc:`../examples/index` for more complete examples.