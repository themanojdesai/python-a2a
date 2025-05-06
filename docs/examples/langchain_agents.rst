LangChain Agents with Tools Examples
=================================

This page provides examples of how to use LangChain agents with tools and convert them to A2A servers.

Basic LangChain Agent with Tools
-------------------------------

The following example demonstrates how to create a LangChain agent with standard tools, convert it to an A2A server, and enable streaming:

.. code-block:: python

    #!/usr/bin/env python
    """
    LangChain Agent with Tools Example

    This example demonstrates how to create a LangChain agent with various tools
    and convert it to an A2A server with streaming support.
    """
    # Import required components
    from python_a2a import run_server, AgentCard, AgentSkill, A2AClient
    from python_a2a.langchain import to_a2a_server
    
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_community.tools import DuckDuckGoSearchRun, WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.tools import BaseTool
    
    # Step 1: Create a custom calculator tool
    class CalculatorTool(BaseTool):
        name = "calculator"
        description = "Useful for performing mathematical calculations."
        
        def _run(self, query: str) -> str:
            """Calculate the result of a mathematical expression."""
            try:
                return str(eval(query))
            except Exception as e:
                return f"Error evaluating expression: {str(e)}"
        
        async def _arun(self, query: str) -> str:
            """Run calculator asynchronously."""
            return self._run(query)
    
    # Step 2: Create all tools
    wikipedia_tool = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    search_tool = DuckDuckGoSearchRun()
    calculator_tool = CalculatorTool()
    
    tools = [calculator_tool, wikipedia_tool, search_tool]
    
    # Step 3: Create the LLM and agent
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        streaming=True  # Enable streaming
    )
    
    # Create prompt - agent_scratchpad is required for the agent to track tool usage
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a helpful assistant with tools."),
        ("human", "{input}"),
        ("ai", "{agent_scratchpad}")
    ])
    
    # Create agent and executor
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        handle_parsing_errors=True
    )
    
    # Step 4: Convert to A2A server
    a2a_server = to_a2a_server(agent_executor)
    
    # Step 5: Add agent card for better API discovery
    a2a_server.agent_card = AgentCard(
        name="Research Assistant",
        description="An assistant with research capabilities",
        url="http://localhost:5000",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Web Research",
                description="Find information on the internet",
                examples=["What is quantum computing?"]
            ),
            AgentSkill(
                name="Calculations",
                description="Perform mathematical calculations",
                examples=["Calculate 15% of 67.50"]
            )
        ],
        capabilities={"streaming": True}
    )
    
    # Step 6: Run the server
    run_server(a2a_server, host="0.0.0.0", port=5000)

To use this example, run the following command:

.. code-block:: bash

    export OPENAI_API_KEY=your_api_key
    python langchain_agent_with_tools.py

Client Code to Interact with the Agent
-------------------------------------

The following code demonstrates how to interact with the agent using the A2A client:

.. code-block:: python

    from python_a2a import A2AClient
    
    # Create client
    client = A2AClient("http://localhost:5000")
    
    # Regular query
    response = client.ask("What is quantum computing?")
    print(f"Response: {response}")
    
    # Test streaming
    async def test_streaming(client, query):
        """Test streaming with the A2A client"""
        from python_a2a.models import Message, TextContent, MessageRole
        
        message = Message(
            content=TextContent(text=query),
            role=MessageRole.USER
        )
        
        print(f"Query: {query}")
        print("Streaming response:")
        
        collected_response = ""
        
        # Stream the response
        async for chunk in client.stream_response(message):
            # Handle dictionary chunks
            if isinstance(chunk, dict) and 'content' in chunk:
                chunk_text = chunk['content']
            elif isinstance(chunk, str):
                chunk_text = chunk
            else:
                chunk_text = str(chunk)
                
            print(chunk_text, end="", flush=True)
            collected_response += chunk_text
        
        print("\n")
        return collected_response
    
    # Run streaming test
    import asyncio
    loop = asyncio.get_event_loop()
    loop.run_until_complete(
        test_streaming(client, "What were the major achievements of Nikola Tesla?")
    )

Advanced Agent with Specialized Tools
------------------------------------

For more sophisticated use cases, you can create specialized tools and integrate them with a LangChain agent:

.. code-block:: python

    #!/usr/bin/env python
    """
    Advanced LangChain Agent with Specialized Tools
    """
    from python_a2a import run_server, AgentCard, AgentSkill, A2AClient
    from python_a2a.langchain import to_a2a_server
    
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain.memory import ConversationBufferMemory
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.tools import tool
    
    # Create specialized tools
    @tool
    def get_weather(location: str) -> str:
        """Get current weather for a location."""
        # In a real application, this would call a weather API
        return f"Weather in {location}: 72°F, Partly Cloudy"
    
    @tool
    def get_stock_price(symbol: str) -> str:
        """Get current stock price for a symbol."""
        # In a real application, this would call a finance API
        return f"Stock price for {symbol}: $178.72"
    
    # Collect tools
    tools = [get_weather, get_stock_price]
    
    # Create LLM with streaming
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0,
        streaming=True
    )
    
    # Add conversation memory
    memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True
    )
    
    # Create prompt with memory and agent_scratchpad for tool tracking
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an intelligent assistant with specialized tools."),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        ("ai", "{agent_scratchpad}")
    ])
    
    # Create agent with memory
    agent = create_openai_functions_agent(llm, tools, prompt)
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        memory=memory
    )
    
    # Convert to A2A server
    a2a_server = to_a2a_server(agent_executor)
    
    # Add agent card
    a2a_server.agent_card = AgentCard(
        name="Specialized Assistant",
        description="Assistant with weather and stock tools",
        url="http://localhost:5000",
        capabilities={"streaming": True, "memory": True}
    )
    
    # Run server
    run_server(a2a_server)

Key Components Explained
-----------------------

1. **LangChain Tools**
   
   LangChain provides several ways to create tools:
   
   * Using the ``BaseTool`` class:
     
     .. code-block:: python
     
         class CalculatorTool(BaseTool):
             name = "calculator"
             description = "Performs calculations"
             
             def _run(self, query: str) -> str:
                 return str(eval(query))
             
             async def _arun(self, query: str) -> str:
                 return self._run(query)
   
   * Using the ``@tool`` decorator:
     
     .. code-block:: python
     
         @tool
         def get_weather(location: str) -> str:
             """Get weather for a location."""
             # Call weather API
             return f"Weather in {location}: 72°F"

2. **Creating the Agent**
   
   LangChain provides multiple agent types:
   
   * OpenAI Functions agent (recommended):
     
     .. code-block:: python
     
         agent = create_openai_functions_agent(llm, tools, prompt)
   
   * ReAct agent:
     
     .. code-block:: python
     
         agent = create_react_agent(llm, tools, prompt)

3. **Converting to A2A Server**
   
   Use the ``to_a2a_server`` function to convert a LangChain agent to an A2A server:
   
   .. code-block:: python
   
       a2a_server = to_a2a_server(agent_executor)

4. **Adding Agent Card**
   
   Enhance the A2A server with an agent card for better API discovery:
   
   .. code-block:: python
   
       a2a_server.agent_card = AgentCard(
           name="Assistant Name",
           description="Description of capabilities",
           skills=[...],
           capabilities={"streaming": True}
       )

5. **Streaming Support**
   
   To enable streaming:
   
   * Set ``streaming=True`` when creating the LLM
   * Use ``client.stream_response()`` on the client side

6. **Adding Memory**
   
   Add conversation memory to your agent:
   
   .. code-block:: python
   
       memory = ConversationBufferMemory(
           memory_key="chat_history",
           return_messages=True
       )
       
       # Include memory in the prompt
       prompt = ChatPromptTemplate.from_messages([
           ("system", "System prompt"),
           MessagesPlaceholder(variable_name="chat_history"),
           ("human", "{input}")
       ])
       
       # Add memory to agent executor
       agent_executor = AgentExecutor(
           agent=agent,
           tools=tools,
           memory=memory
       )

For more examples, check out the `examples/langchain` directory in the GitHub repository.