Advanced Techniques
==================

This guide covers advanced techniques for using Python A2A effectively.

Function Calling
--------------

Function calling allows agents to request specific actions from other systems. Here's how to use it:

Creating Function Calls
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from python_a2a import FunctionCallContent, Message, MessageRole, FunctionParameter
    
    # Create a function call message
    message = Message(
        content=FunctionCallContent(
            name="get_weather",
            parameters=[
                FunctionParameter(name="location", value="New York"),
                FunctionParameter(name="unit", value="fahrenheit")
            ]
        ),
        role=MessageRole.AGENT
    )

Handling Function Calls
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from python_a2a import A2AServer, FunctionResponseContent, Message, MessageRole
    
    class WeatherAgent(A2AServer):
        def handle_message(self, message):
            # Check if this is a function call
            if message.content.type == "function_call":
                # Get function name
                function_name = message.content.name
                
                # Get parameters
                parameters = {p.name: p.value for p in message.content.parameters}
                
                # Handle based on function name
                if function_name == "get_weather":
                    location = parameters.get("location", "")
                    unit = parameters.get("unit", "celsius")
                    
                    # Mock weather data
                    weather_data = {"temp": 72, "condition": "Sunny"}
                    
                    # Return function response
                    return Message(
                        content=FunctionResponseContent(
                            name="get_weather",
                            response=weather_data
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
            
            # Default response for non-function calls
            return super().handle_message(message)

Streaming Responses
-----------------

For long-running operations, you can stream responses to provide real-time feedback:

.. code-block:: python

    from python_a2a import A2AServer, TaskStatus, TaskState
    from python_a2a.models import AgentCard
    import time
    
    class StreamingAgent(A2AServer):
        def __init__(self):
            # Create agent card with streaming capability
            agent_card = AgentCard(
                name="Streaming Agent",
                description="Agent with streaming capabilities",
                url="http://localhost:5000",
                version="1.0.0",
                capabilities={"streaming": True}
            )
            super().__init__(agent_card=agent_card)
        
        def handle_task(self, task):
            # Set task to waiting state
            task.status = TaskStatus(state=TaskState.WAITING)
            
            # Create initial artifact
            task.artifacts = [{
                "parts": [{"type": "text", "text": "Processing..."}]
            }]
            
            # In a real implementation, you would use server-sent events or websockets
            # This is a simplified example
            for i in range(5):
                # In a real implementation, this would be sent as an update
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"Processing... {(i+1)*20}%"}]
                }]
                
                # Simulate processing time
                time.sleep(1)
            
            # Final response
            task.artifacts = [{
                "parts": [{"type": "text", "text": "Processing complete!"}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task

Authentication
------------

You can add authentication to your A2A agents to protect them from unauthorized access:

.. code-block:: python

    from python_a2a import A2AServer, TaskStatus, TaskState
    from python_a2a.models import AgentCard
    from flask import request
    
    class AuthenticatedAgent(A2AServer):
        def __init__(self):
            # Create agent card with authentication
            agent_card = AgentCard(
                name="Authenticated Agent",
                description="Agent with authentication",
                url="http://localhost:5000",
                version="1.0.0",
                authentication="bearer"
            )
            super().__init__(agent_card=agent_card)
            
            # API keys
            self.api_keys = {"MY_SECRET_KEY": "user1"}
        
        def setup_routes(self, app):
            # Add authentication middleware
            @app.before_request
            def authenticate():
                # Skip authentication for agent card
                if request.path in ["/", "/a2a", "/agent.json", "/a2a/agent.json"]:
                    return None
                
                # Check for Authorization header
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return {"error": "Unauthorized"}, 401
                
                # Get token
                token = auth_header.split("Bearer ")[1]
                
                # Check if token is valid
                if token not in self.api_keys:
                    return {"error": "Invalid API key"}, 401
                
                # Token is valid
                return None
            
            # Call parent setup_routes
            super().setup_routes(app)
        
        def handle_task(self, task):
            # Get token from request
            auth_header = request.headers.get("Authorization")
            token = auth_header.split("Bearer ")[1]
            
            # Get user from token
            user = self.api_keys.get(token)
            
            # Create response
            task.artifacts = [{
                "parts": [{"type": "text", "text": f"Hello, {user}! This is a protected resource."}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task

Advanced Error Handling
---------------------

Proper error handling ensures robustness in your agents:

.. code-block:: python

    from python_a2a import A2AServer, TaskStatus, TaskState
    
    class RobustAgent(A2AServer):
        def handle_task(self, task):
            try:
                # Extract message text
                message_data = task.message or {}
                content = message_data.get("content", {})
                text = content.get("text", "") if isinstance(content, dict) else ""
                
                # Process the message
                # This might raise exceptions
                result = self.process_message(text)
                
                # Create response artifact
                task.artifacts = [{
                    "parts": [{"type": "text", "text": result}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
                
            except ValueError as e:
                # Handle validation errors
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"Validation error: {str(e)}"}]
                }]
                task.status = TaskStatus(state=TaskState.INPUT_REQUIRED)
                
            except ConnectionError as e:
                # Handle connection errors
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"Service unavailable: {str(e)}"}]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
                
            except Exception as e:
                # Handle unexpected errors
                import traceback
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"An unexpected error occurred: {str(e)}"}]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
                
                # Log the error
                print(f"Error: {str(e)}")
                print(traceback.format_exc())
            
            return task
        
        def process_message(self, text):
            # This is a placeholder for your actual processing logic
            if not text:
                raise ValueError("Empty message")
                
            if "error" in text.lower():
                raise Exception("Simulated error")
                
            return f"Processed: {text}"

Custom Content Types
------------------

You can extend the A2A protocol with custom content types:

.. code-block:: python

    from python_a2a import A2AServer, Message, MessageRole, BaseModel
    from dataclasses import dataclass
    from typing import Dict, Any, List
    
    # Define a custom content type
    @dataclass
    class ChartContent(BaseModel):
        """Chart content type"""
        type: str = "chart"
        title: str = ""
        labels: List[str] = None
        data: List[float] = None
        chart_type: str = "bar"  # bar, line, pie, etc.
        
        def to_dict(self) -> Dict[str, Any]:
            """Convert to dictionary representation"""
            return {
                "type": self.type,
                "title": self.title,
                "labels": self.labels,
                "data": self.data,
                "chart_type": self.chart_type
            }
    
    # Create an agent that uses the custom content type
    class ChartAgent(A2AServer):
        def handle_message(self, message):
            # Generate a chart
            chart_content = ChartContent(
                title="Sample Chart",
                labels=["A", "B", "C", "D"],
                data=[10, 20, 15, 25],
                chart_type="bar"
            )
            
            # Return the chart
            return Message(
                content=chart_content,
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )

Testing A2A Agents
----------------

Here's how to write unit tests for A2A agents:

.. code-block:: python

    import unittest
    from python_a2a import Message, TextContent, MessageRole
    from your_project import YourAgent
    
    class TestYourAgent(unittest.TestCase):
        def setUp(self):
            # Create the agent
            self.agent = YourAgent()
        
        def test_greeting(self):
            # Create a greeting message
            message = Message(
                content=TextContent(text="Hello"),
                role=MessageRole.USER
            )
            
            # Get the response
            response = self.agent.handle_message(message)
            
            # Check the response
            self.assertEqual(response.role, MessageRole.AGENT)
            self.assertEqual(response.content.type, "text")
            self.assertIn("hello", response.content.text.lower())
        
        def test_task_handling(self):
            # Create a task
            from python_a2a import Task
            
            task = Task(
                message={
                    "content": {
                        "type": "text",
                        "text": "Hello"
                    },
                    "role": "user"
                }
            )
            
            # Get the response
            response = self.agent.handle_task(task)
            
            # Check the response
            self.assertEqual(response.status.state, "completed")
            self.assertTrue(response.artifacts)
            self.assertEqual(response.artifacts[0]["parts"][0]["type"], "text")
            self.assertIn("hello", response.artifacts[0]["parts"][0]["text"].lower())
    
    if __name__ == "__main__":
        unittest.main()

Next Steps
---------

Now that you've learned advanced techniques, you can:

- Build more sophisticated agents with robust error handling
- Add authentication to protect your agents
- Create custom content types for specialized applications
- Write tests to ensure your agents work correctly

Check out the :doc:`../examples/advanced` for complete examples of these techniques.