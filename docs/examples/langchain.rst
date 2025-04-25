LangChain Integration Examples
===========================

This page provides examples of how to use the LangChain integration with Python A2A.

Creating a ToolServer from LangChain Tools
----------------------------------------

This example demonstrates how to create an MCP server from LangChain tools:

.. code-block:: python

    """
    Example of creating a ToolServer from LangChain tools.
    """
    from python_a2a.langchain import ToolServer
    from langchain.tools import BaseTool, WikipediaQueryRun
    from langchain.utilities.wikipedia import WikipediaAPIWrapper

    # Define a custom calculator tool
    class Calculator(BaseTool):
        name = "calculator"
        description = "Performs basic calculations"
        
        def _run(self, expression: str):
            """Calculate the result of a mathematical expression."""
            try:
                return eval(expression)
            except Exception as e:
                return f"Error: {str(e)}"
        
        def _arun(self, expression: str):
            """Run calculator asynchronously."""
            return self._run(expression)
    
    # Create a collection of tools
    tools = [
        Calculator(),
        WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    ]
    
    # Create a ToolServer from the tools
    server = ToolServer.from_tools(
        tools=tools,
        name="Research Tools",
        description="MCP server with research and calculator tools"
    )
    
    # Print information about the server
    print(f"Created ToolServer: {server.name}")
    print(f"Description: {server.description}")
    print(f"Registered tools:")
    for tool in server.get_tools():
        print(f"  - {tool['name']}: {tool['description']}")
    
    # Run the server
    server.run(host="0.0.0.0", port=5000)

Converting a LangChain Agent to an A2A Agent
------------------------------------------

This example shows how to convert a LangChain agent to an A2A agent:

.. code-block:: python

    """
    Example of converting a LangChain agent to an A2A agent.
    """
    from python_a2a.langchain import LangChainBridge
    from python_a2a import run_server
    from langchain.agents import AgentExecutor, create_react_agent
    from langchain.tools import WikipediaQueryRun
    from langchain.utilities.wikipedia import WikipediaAPIWrapper
    from langchain_openai import ChatOpenAI
    from langchain.prompts import PromptTemplate
    import os
    
    # Create tools for the agent
    wiki_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    tools = [wiki_tool]
    
    # Create a ChatOpenAI LLM
    llm = ChatOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),
        temperature=0
    )
    
    # Create the agent
    react_prompt = PromptTemplate.from_template("You are a research assistant. {input}")
    agent = create_react_agent(llm, tools, react_prompt)
    agent_executor = AgentExecutor(agent=agent, tools=tools)
    
    # Convert to A2A agent
    a2a_agent = LangChainBridge.agent_to_a2a(
        agent_executor,
        name="Research Assistant",
        description="A research assistant powered by LangChain and OpenAI"
    )
    
    # Run the A2A agent
    run_server(a2a_agent, port=5001)

Creating an A2A Agent with MCP Tool Access
----------------------------------------

Here's how to create an A2A agent that can access LangChain tools through MCP:

.. code-block:: python

    """
    Example of creating an A2A agent with access to LangChain tools via MCP.
    """
    from python_a2a.mcp import A2AMCPAgent, text_response
    from python_a2a import run_server
    from python_a2a.langchain import ToolServer
    from langchain.tools import WikipediaQueryRun
    from langchain.utilities.wikipedia import WikipediaAPIWrapper
    
    # First, create a ToolServer with LangChain tools
    tool_server = ToolServer.from_tools(
        tools=[WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())],
        name="Research Tools",
        description="MCP server with research tools"
    )
    
    # Create an A2A agent with MCP capabilities
    class ResearchAgent(A2AMCPAgent):
        def __init__(self):
            super().__init__(
                name="Research Assistant",
                description="Agent that can search Wikipedia",
                mcp_servers={"research_tools": tool_server}
            )
        
        async def handle_message_async(self, message):
            """Process an incoming message."""
            if message.content.type == "text":
                text = message.content.text
                response = await self.process_query(text)
                return text_response(response)
            else:
                return text_response("Please send a text message.")
        
        async def process_query(self, query: str) -> str:
            """Process a user query."""
            if "search" in query.lower() or "wikipedia" in query.lower():
                # Extract search term from query
                search_term = query.lower().replace("search", "").replace("wikipedia", "").strip()
                
                if search_term:
                    result = await self.call_mcp_tool("research_tools", "wikipediaQueryRun", query=search_term)
                    return f"Here's what I found about '{search_term}':\n\n{result}"
                else:
                    return "What would you like to search for?"
            
            else:
                return "I can help you search Wikipedia. Try asking something like 'search quantum computing'"
    
    # Create the agent
    agent = ResearchAgent()
    
    # Run the agent
    run_server(agent, port=5002)

Creating a Workflow with Mixed Components
---------------------------------------

This example demonstrates how to create a workflow with both A2A and LangChain components:

.. code-block:: python

    """
    Example of creating a workflow with both A2A and LangChain components.
    """
    from python_a2a import AgentNetwork
    from python_a2a.langchain import AgentFlow, LangChainBridge
    from langchain.chains import LLMChain
    from langchain.prompts import PromptTemplate
    from langchain_openai import ChatOpenAI
    import asyncio
    import os
    
    async def main():
        # Create an OpenAI LLM
        llm = ChatOpenAI(
            api_key=os.environ.get("OPENAI_API_KEY"),
            temperature=0.7
        )
        
        # Create LangChain chains
        summarize_prompt = PromptTemplate(
            input_variables=["text"],
            template="Summarize the following text in three bullet points:\n\n{text}"
        )
        
        evaluate_prompt = PromptTemplate(
            input_variables=["text"],
            template="Evaluate the quality of this content. Provide strengths and areas for improvement:\n\n{text}"
        )
        
        summarize_chain = LLMChain(llm=llm, prompt=summarize_prompt)
        evaluate_chain = LLMChain(llm=llm, prompt=evaluate_prompt)
        
        # Create an agent network
        network = AgentNetwork(name="Research Analysis Network")
        
        # Add an A2A agent 
        # In a real scenario, this would be an actual A2A agent
        # For this example, we'll convert a LangChain chain to an A2A agent
        research_chain = LLMChain(
            llm=llm,
            prompt=PromptTemplate(
                input_variables=["topic"],
                template="Research the latest developments in {topic} and provide detailed information."
            )
        )
        
        research_agent = LangChainBridge.agent_to_a2a(research_chain, name="Research Agent")
        network.add("researcher", research_agent)
        
        # Create an AgentFlow
        flow = AgentFlow(agent_network=network, name="Research and Analysis Workflow")
        
        # Define the workflow steps
        flow.ask("researcher", "Research the latest developments in {topic}")
        flow.add_langchain_step(summarize_chain, "{latest_result}")
        flow.add_langchain_step(evaluate_chain, "{latest_result}")
        
        # Execute the workflow with a sample topic
        result = await flow.run({"topic": "quantum computing"})
        
        print("\nWorkflow result:")
        print(result)
    
    if __name__ == "__main__":
        asyncio.run(main())

For more examples, check out the `examples` directory in the GitHub repository.