Basic Concepts
=============

This guide introduces the basic concepts of the A2A protocol and how they're implemented in Python A2A.

What is the A2A Protocol?
-------------------------

The Agent-to-Agent (A2A) protocol is a standard communication format developed by Google that enables AI agents to interact regardless of their underlying implementation. It establishes a common language for agents to exchange information, make requests, and share responses.

Key components of the A2A protocol include:

- **Messages**: Units of communication between agents
- **Tasks**: Units of work that agents can perform
- **Agent Cards**: Descriptions of agents and their capabilities
- **Skills**: Specific abilities that agents can provide

Messages
--------

Messages are the basic units of communication in the A2A protocol. They consist of:

- **Content**: The actual content of the message (text, function call, etc.)
- **Role**: Who sent the message (user, agent, system)
- **IDs**: Unique identifiers for the message, its parent, and the conversation

Here's how to create a simple text message in Python A2A:

.. code-block:: python

    from python_a2a import Message, TextContent, MessageRole
    
    message = Message(
        content=TextContent(text="What's the weather in Paris?"),
        role=MessageRole.USER
    )

Tasks
-----

Tasks represent units of work in the A2A protocol. They include:

- **Message**: The input message for the task
- **Status**: The current state of the task (submitted, completed, etc.)
- **Artifacts**: The outputs produced by the task

Here's how to create and complete a task:

.. code-block:: python

    from python_a2a import Task, TaskStatus, TaskState
    
    # Create a task
    task = Task(message=message.to_dict())
    
    # Complete the task with a response
    task.artifacts = [{
        "parts": [{
            "type": "text",
            "text": "It's sunny and 72°F in Paris"
        }]
    }]
    task.status = TaskStatus(state=TaskState.COMPLETED)

Agent Cards
----------

Agent cards describe agents and their capabilities. They include:

- **Name**: The name of the agent
- **Description**: What the agent does
- **URL**: Where the agent can be accessed
- **Skills**: The skills the agent provides

Here's how to create an agent card:

.. code-block:: python

    from python_a2a import AgentCard, AgentSkill
    
    agent_card = AgentCard(
        name="Weather API",
        description="Get weather information for locations",
        url="http://localhost:5000",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Get Weather",
                description="Get current weather for a location",
                tags=["weather", "current"],
                examples=["What's the weather in New York?"]
            )
        ]
    )

Creating an A2A Server
---------------------

To create an A2A server, you need to implement the ``handle_task`` method:

.. code-block:: python

    from python_a2a import A2AServer, TaskStatus, TaskState
    
    class WeatherAgent(A2AServer):
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Respond to the message
            response_text = f"It's sunny today!"
            
            # Create artifact with response
            task.artifacts = [{
                "parts": [{"type": "text", "text": response_text}]
            }]
            
            # Mark as completed
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task

Using the A2A Client
-------------------

To connect to an A2A agent, use the ``A2AClient``:

.. code-block:: python

    from python_a2a import A2AClient
    
    # Create a client
    client = A2AClient("http://localhost:5000")
    
    # Send a message
    response = client.ask("What's the weather in Paris?")
    
    # Print the response
    print(response)

The A2A client automatically handles message and task creation, sending requests, and parsing responses.

Next Steps
---------

Now that you understand the basic concepts, you can:

- Learn about :doc:`advanced` concepts
- Explore :doc:`mcp` integration
- Check out the :doc:`../examples/index`