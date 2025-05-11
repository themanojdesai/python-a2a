Quick Start
===========

This guide will help you get started with Python A2A quickly. We'll cover the basics of creating and connecting to A2A agents.

Creating a Simple A2A Agent
--------------------------

Let's create a simple A2A agent that responds to weather queries:

.. code-block:: python

    from python_a2a import A2AServer, skill, agent, run_server
    from python_a2a import TaskStatus, TaskState

    @agent(
        name="Weather Agent",
        description="Provides weather information",
        version="1.0.0"
    )
    class WeatherAgent(A2AServer):
        
        @skill(
            name="Get Weather",
            description="Get current weather for a location",
            tags=["weather", "forecast"]
        )
        def get_weather(self, location):
            """Get weather for a location."""
            # Mock implementation
            return f"It's sunny and 75°F in {location}"
        
        def handle_task(self, task):
            # Extract location from message
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            if "weather" in text.lower() and "in" in text.lower():
                location = text.split("in", 1)[1].strip().rstrip("?.")
                
                # Get weather and create response
                weather_text = self.get_weather(location)
                task.artifacts = [{
                    "parts": [{"type": "text", "text": weather_text}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else:
                task.status = TaskStatus(
                    state=TaskState.INPUT_REQUIRED,
                    message={"role": "agent", "content": {"type": "text", 
                            "text": "Please ask about weather in a specific location."}}
                )
            return task

    # Run the server
    if __name__ == "__main__":
        agent = WeatherAgent()
        run_server(agent, port=5000)

Save this code in a file (e.g., ``weather_agent.py``) and run it with ``python weather_agent.py``. This will start an A2A server on port 5000.

Connecting to an A2A Agent
-------------------------

Now let's create a client to connect to our agent:

.. code-block:: python

    from python_a2a import A2AClient

    # Create a client connected to an A2A-compatible agent
    client = A2AClient("http://localhost:5000")

    # View agent information
    print(f"Connected to: {client.agent_card.name}")
    print(f"Description: {client.agent_card.description}")
    print(f"Skills: {[skill.name for skill in client.agent_card.skills]}")

    # Ask a question
    response = client.ask("What's the weather in Paris?")
    print(f"Response: {response}")

Save this code in a file (e.g., ``weather_client.py``) and run it with ``python weather_client.py`` while the agent is running.

Creating an LLM-Powered Agent
---------------------------

Let's create an agent powered by a large language model:

.. code-block:: python

    import os
    from python_a2a import OpenAIA2AServer, run_server

    # Create an agent powered by OpenAI
    agent = OpenAIA2AServer(
        api_key=os.environ["OPENAI_API_KEY"],
        model="gpt-4",
        system_prompt="You are a helpful AI assistant specialized in explaining complex topics simply."
    )

    # Run the server
    if __name__ == "__main__":
        run_server(agent, host="0.0.0.0", port=5000)

Save this code in a file (e.g., ``llm_agent.py``), set your OpenAI API key as an environment variable, and run it with ``python llm_agent.py``.

Using Decorators
--------------

Python A2A provides decorators for easy agent and skill creation:

.. code-block:: python

    from python_a2a import agent, skill, A2AServer, run_server
    from python_a2a import TaskStatus, TaskState

    @agent(
        name="Calculator",
        description="Performs calculations",
        version="1.0.0"
    )
    class CalculatorAgent(A2AServer):
        
        @skill(
            name="Add",
            description="Add two numbers",
            tags=["math", "addition"]
        )
        def add(self, a, b):
            """
            Add two numbers together.
            
            Examples:
                "What is 5 + 3?"
                "Add 10 and 20"
            """
            return float(a) + float(b)
        
        def handle_task(self, task):
            # Implementation details...
            pass

    # Run the server
    if __name__ == "__main__":
        calculator = CalculatorAgent()
        run_server(calculator, port=5000)

Using the Agent Flow UI
--------------------

Python A2A includes a visual workflow editor for building agent networks:

.. code-block:: bash

    # Start the Agent Flow UI
    a2a ui

The UI will open in your browser at http://localhost:8080.

You can use the UI to:

- Discover and connect to agents
- Build visual workflows with drag-and-drop
- Run and monitor workflows
- Save and load workflows

For more details on using the Agent Flow UI, see :doc:`guides/agent_flow`.

Next Steps
---------

Now that you've seen the basics, check out the following sections to learn more:

- :doc:`guides/index` - For more detailed explanations
- :doc:`guides/agent_flow` - For details on using the Agent Flow UI
- :doc:`api/index` - For API reference
- :doc:`examples/index` - For more complete examples