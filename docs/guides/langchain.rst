LangChain Integration
====================

The LangChain integration module allows you to seamlessly use LangChain components within the A2A ecosystem and vice versa.

Overview
--------

Python A2A provides three main components for LangChain integration:

1. **ToolServer** - For hosting LangChain tools as MCP endpoints
2. **LangChainBridge** - For converting between A2A and LangChain agents
3. **AgentFlow** - For creating workflows with both A2A and LangChain components

These components enable you to leverage the rich ecosystem of LangChain tools and agents while maintaining compatibility with the A2A protocol.

Installation
-----------

LangChain is automatically installed when you install python-a2a:

.. code-block:: bash

    pip install python-a2a

Key Components
-------------

ToolServer
~~~~~~~~~~

The ``ToolServer`` class creates an MCP server that hosts LangChain tools:

.. code-block:: python

    from python_a2a.langchain import ToolServer
    from langchain.tools import BaseTool, WikipediaQueryRun

    # Define a custom tool
    class Calculator(BaseTool):
        name = "calculator"
        description = "Performs calculations"
        
        def _run(self, expression: str):
            return eval(expression)

    # Create a server with LangChain tools
    server = ToolServer.from_tools([
        Calculator(),
        WikipediaQueryRun()
    ])

    # Run the server
    server.run(host="0.0.0.0", port=5000)

This creates an MCP server that exposes the LangChain tools as MCP endpoints, making them available to any A2A agent with MCP capabilities.

LangChainBridge
~~~~~~~~~~~~~~

The ``LangChainBridge`` class provides bidirectional conversion between LangChain and A2A:

.. code-block:: python

    from python_a2a.langchain import LangChainBridge
    from python_a2a import run_server
    from langchain.agents import AgentExecutor, create_react_agent

    # Convert LangChain agent to A2A agent
    a2a_agent = LangChainBridge.agent_to_a2a(agent_executor)
    run_server(a2a_agent, port=5001)

    # Convert A2A agent to LangChain tool
    langchain_tool = LangChainBridge.agent_to_tool("http://localhost:5002")

This allows you to use LangChain agents as A2A agents, or use A2A agents as tools within a LangChain workflow.

AgentFlow
~~~~~~~~

The ``AgentFlow`` class extends the base Flow class with LangChain support:

.. code-block:: python

    from python_a2a import AgentNetwork
    from python_a2a.langchain import AgentFlow

    # Create a workflow with both A2A and LangChain components
    flow = AgentFlow(agent_network=network)

    # Add both types of steps
    flow.ask("researcher", "Research {topic}")
    flow.add_langchain_step(summarize_chain, "{latest_result}")
    flow.add_tool_step("tools.calculator", expression="2+2")

    # Execute the workflow
    result = await flow.run({"topic": "quantum computing"})

This allows you to create complex workflows that combine steps from both ecosystems.

Advanced Usage
-------------

Using LangChain Toolkits
~~~~~~~~~~~~~~~~~~~~~~~

You can easily create MCP servers from LangChain toolkits:

.. code-block:: python

    from langchain.agents import load_tools
    from langchain_openai import ChatOpenAI
    from python_a2a.langchain import ToolServer

    # Load tools from LangChain
    llm = ChatOpenAI()
    tools = load_tools(["serpapi", "llm-math"], llm=llm)

    # Create a server from these tools
    server = ToolServer.from_tools(tools)

LangChain provides numerous toolkits for different domains, which can all be converted to MCP servers.

Integrating with LangChain Agents
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can create complex agent setups that use both ecosystems:

.. code-block:: python

    from langchain.agents import AgentExecutor, create_react_agent
    from langchain_openai import ChatOpenAI
    from python_a2a.langchain import LangChainBridge

    # Create an A2A agent as a LangChain tool
    a2a_tool = LangChainBridge.agent_to_tool("http://localhost:5001")

    # Add it to a LangChain agent
    llm = ChatOpenAI()
    tools = [a2a_tool, search_tool, wiki_tool]
    agent = create_react_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)

    # Use the agent
    result = agent_executor.run("Research quantum computing advances in 2024")

This is particularly useful when you have existing A2A agents that you want to incorporate into a LangChain workflow.

Handling MCP Tools as LangChain Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

You can convert MCP tools to LangChain tools:

.. code-block:: python

    from python_a2a.langchain import LangChainBridge

    # Convert all tools from an MCP server
    langchain_tools = LangChainBridge.mcp_to_tools("http://localhost:5000")

    # Add to a LangChain agent
    agent_executor = AgentExecutor(agent=agent, tools=langchain_tools)

Error Handling
-------------

All components in the LangChain integration include robust error handling:

.. code-block:: python

    try:
        # Create a tool server
        server = ToolServer.from_tools(tools)
        
        # Run the server
        server.run(host="0.0.0.0", port=5000)
    except ImportError:
        print("LangChain is not installed. Install with 'pip install langchain'")
    except Exception as e:
        print(f"Error creating tool server: {str(e)}")

The components will raise appropriate exceptions for missing dependencies or configuration issues.

Best Practices
-------------

1. **Type Hints**: Use proper type hints in LangChain tools for better parameter detection
2. **Error Handling**: Implement proper error handling in your tools
3. **Tool Documentation**: Provide clear descriptions for tools and parameters
4. **Async Support**: Use async methods when possible for better performance
5. **Workflow Design**: Design workflows with clear data flows between components

For more examples, see the :doc:`../examples/langchain` page.