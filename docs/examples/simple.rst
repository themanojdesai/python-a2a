Simple Examples
==============

This page provides simple examples of using Python A2A.

Basic A2A Agent
--------------

Here's a complete example of a basic A2A agent that responds to greetings:

.. code-block:: python

    from python_a2a import A2AServer, skill, agent, run_server
    from python_a2a import TaskStatus, TaskState
    
    @agent(
        name="Greeting Agent",
        description="A simple agent that responds to greetings",
        version="1.0.0"
    )
    class GreetingAgent(A2AServer):
        
        @skill(
            name="Greet",
            description="Respond to a greeting",
            tags=["greeting", "hello"]
        )
        def greet(self, name=None):
            """Respond to a greeting with a friendly message."""
            if name:
                return f"Hello, {name}! How can I help you today?"
            else:
                return "Hello there! How can I help you today?"
        
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Check if it's a greeting
            greeting_words = ["hello", "hi", "hey", "greetings"]
            is_greeting = any(word in text.lower() for word in greeting_words)
            
            if is_greeting:
                # Extract name if present
                name = None
                if "my name is" in text.lower():
                    name = text.lower().split("my name is")[1].strip()
                
                # Create greeting response
                greeting = self.greet(name)
                task.artifacts = [{
                    "parts": [{"type": "text", "text": greeting}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else:
                # Default response
                task.artifacts = [{
                    "parts": [{"type": "text", "text": "I'm a greeting agent. Try saying hello!"}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task
    
    # Run the server
    if __name__ == "__main__":
        agent = GreetingAgent()
        run_server(agent, port=5000)

Save this as ``greeting_agent.py`` and run it with ``python greeting_agent.py``.

Basic A2A Client
--------------

Here's a simple client that connects to the greeting agent:

.. code-block:: python

    from python_a2a import A2AClient
    
    # Create a client
    client = A2AClient("http://localhost:5000")
    
    # Print agent information
    print(f"Connected to: {client.agent_card.name}")
    print(f"Description: {client.agent_card.description}")
    print(f"Skills: {[skill.name for skill in client.agent_card.skills]}")
    
    # Send a greeting
    response = client.ask("Hello there! My name is Alice.")
    print(f"Response: {response}")
    
    # Send another message
    response = client.ask("What can you do?")
    print(f"Response: {response}")

Save this as ``greeting_client.py`` and run it with ``python greeting_client.py`` while the agent is running.

Simple Calculator
---------------

Here's a simple calculator agent:

.. code-block:: python

    from python_a2a import A2AServer, skill, agent, run_server
    from python_a2a import TaskStatus, TaskState
    import re
    
    @agent(
        name="Calculator",
        description="A simple calculator agent",
        version="1.0.0"
    )
    class CalculatorAgent(A2AServer):
        
        @skill(
            name="Add",
            description="Add two numbers",
            tags=["math", "addition"]
        )
        def add(self, a, b):
            """Add two numbers together."""
            return float(a) + float(b)
        
        @skill(
            name="Subtract",
            description="Subtract two numbers",
            tags=["math", "subtraction"]
        )
        def subtract(self, a, b):
            """Subtract b from a."""
            return float(a) - float(b)
        
        @skill(
            name="Multiply",
            description="Multiply two numbers",
            tags=["math", "multiplication"]
        )
        def multiply(self, a, b):
            """Multiply two numbers together."""
            return float(a) * float(b)
        
        @skill(
            name="Divide",
            description="Divide two numbers",
            tags=["math", "division"]
        )
        def divide(self, a, b):
            """Divide a by b."""
            return float(a) / float(b)
        
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Find numbers in the text
            numbers = [float(n) for n in re.findall(r"[-+]?\d*\.?\d+", text)]
            
            # Default response
            response_text = "I can add, subtract, multiply, and divide numbers. Try asking something like 'add 5 and 3' or '10 divided by 2'."
            
            # Check for operation keywords
            if len(numbers) >= 2:
                a, b = numbers[0], numbers[1]
                
                if any(word in text.lower() for word in ["add", "plus", "sum", "+"]):
                    result = self.add(a, b)
                    response_text = f"{a} + {b} = {result}"
                elif any(word in text.lower() for word in ["subtract", "minus", "difference", "-"]):
                    result = self.subtract(a, b)
                    response_text = f"{a} - {b} = {result}"
                elif any(word in text.lower() for word in ["multiply", "times", "product", "*", "x"]):
                    result = self.multiply(a, b)
                    response_text = f"{a} × {b} = {result}"
                elif any(word in text.lower() for word in ["divide", "quotient", "/"]):
                    if b != 0:
                        result = self.divide(a, b)
                        response_text = f"{a} ÷ {b} = {result}"
                    else:
                        response_text = "Cannot divide by zero."
            
            # Create response artifact
            task.artifacts = [{
                "parts": [{"type": "text", "text": response_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task
    
    # Run the server
    if __name__ == "__main__":
        agent = CalculatorAgent()
        run_server(agent, port=5000)

Save this as ``calculator_agent.py`` and run it with ``python calculator_agent.py``.

LLM-Based Agent
-------------

Here's a simple LLM-based agent using OpenAI's API:

.. code-block:: python

    import os
    from python_a2a import OpenAIA2AServer, run_server
    
    # Get API key from environment variable
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("Please set the OPENAI_API_KEY environment variable.")
    
    # Create an OpenAI-based A2A agent
    agent = OpenAIA2AServer(
        api_key=api_key,
        model="gpt-4",
        system_prompt="You are a helpful assistant that specializes in explaining complex concepts simply."
    )
    
    # Run the server
    if __name__ == "__main__":
        print("Starting OpenAI-based A2A agent...")
        run_server(agent, host="0.0.0.0", port=5000)

Save this as ``llm_agent.py``, set your OpenAI API key as an environment variable, and run it with ``python llm_agent.py``.

Next Steps
---------

Now that you've seen some basic examples, check out :doc:`advanced` for more complex examples including multi-agent systems and MCP integration.