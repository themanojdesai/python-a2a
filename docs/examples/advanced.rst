Advanced Examples
=================

This page provides more complex examples of using Python A2A.

Multi-Agent Weather Information System
------------------------------------

This example demonstrates a multi-agent system where different agents collaborate to provide weather-related information and travel recommendations:

1. Weather Data Agent - Provides weather information
2. Travel Recommendation Agent - Recommends destinations based on weather
3. User Interface Agent - Orchestrates the other agents

First, create the Weather Data Agent:

.. code-block:: python

    # weather_agent.py
    from python_a2a import A2AServer, skill, agent, run_server
    from python_a2a import TaskStatus, TaskState
    import random
    
    @agent(
        name="Weather API",
        description="Provides weather information for locations",
        version="1.0.0"
    )
    class WeatherAgent(A2AServer):
        
        def __init__(self):
            super().__init__()
            # Mock weather data
            self.weather_data = {
                "new york": {"temp": 72, "condition": "Sunny", "humidity": 45},
                "london": {"temp": 60, "condition": "Cloudy", "humidity": 80},
                "tokyo": {"temp": 75, "condition": "Rainy", "humidity": 85},
                "paris": {"temp": 68, "condition": "Partly Cloudy", "humidity": 60},
                "sydney": {"temp": 82, "condition": "Sunny", "humidity": 50},
                "cairo": {"temp": 95, "condition": "Sunny", "humidity": 30},
                "rio": {"temp": 88, "condition": "Sunny", "humidity": 70},
                "bangkok": {"temp": 90, "condition": "Thunderstorms", "humidity": 95},
                "moscow": {"temp": 45, "condition": "Snowy", "humidity": 70},
                "dubai": {"temp": 105, "condition": "Sunny", "humidity": 20}
            }
        
        @skill(
            name="Get Weather",
            description="Get current weather for a location",
            tags=["weather", "current"]
        )
        def get_weather(self, location):
            """
            Get the current weather for a location.
            
            Args:
                location: The location to get weather for
                
            Returns:
                Weather information
            """
            location = location.lower()
            if location in self.weather_data:
                return self.weather_data[location]
            
            # Generate random weather for unknown locations
            return {
                "temp": random.randint(50, 90),
                "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]),
                "humidity": random.randint(30, 90)
            }
        
        @skill(
            name="Get Forecast",
            description="Get 5-day forecast for a location",
            tags=["weather", "forecast"]
        )
        def get_forecast(self, location):
            """
            Get a 5-day forecast for a location.
            
            Args:
                location: The location to get forecast for
                
            Returns:
                5-day forecast
            """
            base_weather = self.get_weather(location)
            
            # Generate a simple 5-day forecast
            forecast = []
            for day in range(1, 6):
                temp_change = random.randint(-10, 10)
                forecast.append({
                    "day": day,
                    "temp": base_weather["temp"] + temp_change,
                    "condition": random.choice(["Sunny", "Cloudy", "Rainy", "Partly Cloudy"]),
                    "humidity": base_weather["humidity"] + random.randint(-20, 20)
                })
            
            return forecast
        
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Initialize response
            response_text = "I can provide weather information. Try asking for the weather or forecast in a specific location."
            
            # Check for location in the query
            location = None
            if "in" in text.lower():
                location = text.lower().split("in", 1)[1].strip().rstrip("?.")
            
            # Check for forecast vs current weather
            if location:
                if "forecast" in text.lower():
                    forecast = self.get_forecast(location)
                    response_text = f"5-day forecast for {location.title()}:\n"
                    for day in forecast:
                        response_text += f"Day {day['day']}: {day['temp']}°F, {day['condition']}, {day['humidity']}% humidity\n"
                else:
                    weather = self.get_weather(location)
                    response_text = f"Current weather in {location.title()}: {weather['temp']}°F, {weather['condition']}, {weather['humidity']}% humidity"
            
            # Create response artifact
            task.artifacts = [{
                "parts": [{"type": "text", "text": response_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task
    
    # Run the server
    if __name__ == "__main__":
        agent = WeatherAgent()
        run_server(agent, port=5001)

Next, create the Travel Recommendation Agent:

.. code-block:: python

    # travel_agent.py
    from python_a2a import A2AServer, skill, agent, run_server, A2AClient
    from python_a2a import TaskStatus, TaskState
    import json
    
    @agent(
        name="Travel Advisor",
        description="Provides travel recommendations based on weather",
        version="1.0.0"
    )
    class TravelAgent(A2AServer):
        
        def __init__(self):
            super().__init__()
            # Connect to the weather agent
            self.weather_client = A2AClient("http://localhost:5001")
            
            # Destination information
            self.destinations = {
                "new york": {"activities": ["Central Park", "Museums", "Broadway Shows"]},
                "london": {"activities": ["Big Ben", "Museums", "Thames River Cruise"]},
                "tokyo": {"activities": ["Temples", "Shopping", "Cherry Blossoms"]},
                "paris": {"activities": ["Eiffel Tower", "Louvre", "Cafes"]},
                "sydney": {"activities": ["Opera House", "Beaches", "Harbour Bridge"]},
                "cairo": {"activities": ["Pyramids", "Nile Cruise", "Markets"]},
                "rio": {"activities": ["Beaches", "Christ the Redeemer", "Samba"]},
                "bangkok": {"activities": ["Temples", "Street Food", "Markets"]},
                "moscow": {"activities": ["Red Square", "Museums", "Ballet"]},
                "dubai": {"activities": ["Shopping", "Desert Safari", "Burj Khalifa"]}
            }
        
        @skill(
            name="Recommend Destination",
            description="Recommend a destination based on weather preferences",
            tags=["travel", "recommendation"]
        )
        def recommend_destination(self, weather_pref, activity_pref=None):
            """
            Recommend a destination based on weather and activity preferences.
            
            Args:
                weather_pref: Weather preference (warm, cool, etc.)
                activity_pref: Optional activity preference
                
            Returns:
                Destination recommendation
            """
            # Get weather for all destinations
            destinations = []
            for dest in self.destinations.keys():
                try:
                    weather = eval(self.weather_client.ask(f"What's the weather in {dest}?"))
                    destinations.append({
                        "name": dest,
                        "weather": weather,
                        "activities": self.destinations[dest]["activities"]
                    })
                except:
                    # Skip if we can't get weather
                    continue
            
            # Filter by weather preference
            filtered = []
            if weather_pref.lower() == "warm" or weather_pref.lower() == "hot":
                filtered = [d for d in destinations if d["weather"]["temp"] > 75]
            elif weather_pref.lower() == "cool" or weather_pref.lower() == "cold":
                filtered = [d for d in destinations if d["weather"]["temp"] < 60]
            elif weather_pref.lower() == "moderate" or weather_pref.lower() == "mild":
                filtered = [d for d in destinations if 60 <= d["weather"]["temp"] <= 75]
            else:
                filtered = destinations
            
            # Filter by activity preference if provided
            if activity_pref:
                activity_filtered = []
                for dest in filtered:
                    for activity in dest["activities"]:
                        if activity_pref.lower() in activity.lower():
                            activity_filtered.append(dest)
                            break
                filtered = activity_filtered
            
            # Return results
            if filtered:
                return filtered
            else:
                return "No destinations match your preferences."
        
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Initialize response
            response_text = "I can recommend destinations based on weather and activities. Try asking for recommendations for warm or cool places."
            
            # Extract preferences
            weather_pref = None
            activity_pref = None
            
            if "warm" in text.lower() or "hot" in text.lower():
                weather_pref = "warm"
            elif "cool" in text.lower() or "cold" in text.lower():
                weather_pref = "cool"
            elif "moderate" in text.lower() or "mild" in text.lower():
                weather_pref = "moderate"
            
            # Check for activities
            common_activities = ["beach", "museum", "food", "shopping", "nature", "cruise", "show"]
            for activity in common_activities:
                if activity in text.lower():
                    activity_pref = activity
                    break
            
            # Generate recommendations if preferences found
            if weather_pref:
                try:
                    recommendations = self.recommend_destination(weather_pref, activity_pref)
                    
                    if isinstance(recommendations, str):
                        response_text = recommendations
                    else:
                        response_text = f"Here are some {weather_pref} destinations"
                        if activity_pref:
                            response_text += f" with {activity_pref} activities"
                        response_text += ":\n\n"
                        
                        for dest in recommendations[:3]:  # Limit to top 3
                            response_text += f"- {dest['name'].title()}: {dest['weather']['temp']}°F, {dest['weather']['condition']}\n"
                            response_text += f"  Activities: {', '.join(dest['activities'])}\n\n"
                except Exception as e:
                    response_text = f"Sorry, I couldn't generate recommendations: {str(e)}"
            
            # Create response artifact
            task.artifacts = [{
                "parts": [{"type": "text", "text": response_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task
    
    # Run the server
    if __name__ == "__main__":
        agent = TravelAgent()
        run_server(agent, port=5002)

Finally, create the User Interface Agent:

.. code-block:: python

    # ui_agent.py
    from python_a2a import A2AServer, skill, agent, run_server, A2AClient
    from python_a2a import TaskStatus, TaskState
    
    @agent(
        name="Travel Assistant",
        description="Your personal travel assistant",
        version="1.0.0"
    )
    class AssistantAgent(A2AServer):
        
        def __init__(self):
            super().__init__()
            # Connect to other agents
            self.weather_client = A2AClient("http://localhost:5001")
            self.travel_client = A2AClient("http://localhost:5002")
        
        def handle_task(self, task):
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Initialize response
            response_text = "I'm your travel assistant. I can help with weather information and travel recommendations."
            
            # Determine which agent to route to
            if "weather" in text.lower() or "forecast" in text.lower() or "temperature" in text.lower():
                # Route to weather agent
                response_text = self.weather_client.ask(text)
            elif "recommend" in text.lower() or "suggest" in text.lower() or "destination" in text.lower() or "where should" in text.lower():
                # Route to travel agent
                response_text = self.travel_client.ask(text)
            elif text.lower() in ["hi", "hello", "hey"]:
                # Greeting
                response_text = "Hello! I'm your travel assistant. I can help with weather information and travel recommendations. Try asking about the weather in a city or for recommendations for warm places with beaches."
            elif "help" in text.lower() or "what can you do" in text.lower():
                # Help message
                response_text = """I can help you with:
                
                1. Weather information: "What's the weather in Paris?" or "Get me the forecast for Tokyo"
                2. Travel recommendations: "Recommend warm destinations" or "Suggest cool places with museums"
                
                Just let me know what you're interested in!"""
            
            # Create response artifact
            task.artifacts = [{
                "parts": [{"type": "text", "text": response_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task
    
    # Run the server
    if __name__ == "__main__":
        agent = AssistantAgent()
        run_server(agent, port=5000)

To run this multi-agent system:

1. Start the weather agent: `python weather_agent.py`
2. Start the travel agent: `python travel_agent.py`
3. Start the UI agent: `python ui_agent.py`

You can then interact with the UI agent at `http://localhost:5000`.

MCP Integration with LLM
----------------------

This example demonstrates how to integrate an LLM-based agent with MCP tools:

.. code-block:: python

    # llm_mcp_agent.py
    import os
    from python_a2a import A2AServer, A2AMCPAgent, run_server, AgentCard
    from python_a2a import OpenAIA2AServer, TaskStatus, TaskState
    from python_a2a.mcp import FastMCP, text_response
    
    # Create MCP server with calculation tools
    calculator_mcp = FastMCP(
        name="Calculator MCP",
        description="Provides calculation functions"
    )
    
    @calculator_mcp.tool()
    def add(a: float, b: float) -> float:
        """Add two numbers together."""
        return a + b
    
    @calculator_mcp.tool()
    def subtract(a: float, b: float) -> float:
        """Subtract b from a."""
        return a - b
    
    @calculator_mcp.tool()
    def multiply(a: float, b: float) -> float:
        """Multiply two numbers together."""
        return a * b
    
    @calculator_mcp.tool()
    def divide(a: float, b: float) -> float:
        """Divide a by b."""
        if b == 0:
            return "Cannot divide by zero"
        return a / b
    
    # Create MCP server with data lookup tools
    data_mcp = FastMCP(
        name="Data MCP",
        description="Provides data lookup functions"
    )
    
    @data_mcp.tool()
    def get_country_capital(country: str) -> str:
        """
        Get the capital city of a country.
        
        Args:
            country: The country to look up
            
        Returns:
            The capital city
        """
        capitals = {
            "usa": "Washington, D.C.",
            "uk": "London",
            "france": "Paris",
            "germany": "Berlin",
            "japan": "Tokyo",
            "china": "Beijing",
            "india": "New Delhi",
            "brazil": "Brasília",
            "australia": "Canberra",
            "canada": "Ottawa"
        }
        
        country = country.lower()
        if country in capitals:
            return capitals[country]
        elif country == "united states" or country == "united states of america":
            return capitals["usa"]
        elif country == "united kingdom":
            return capitals["uk"]
        else:
            return f"I don't know the capital of {country}"
    
    @data_mcp.tool()
    def get_country_population(country: str) -> str:
        """
        Get the population of a country.
        
        Args:
            country: The country to look up
            
        Returns:
            The population (approximate, as of 2023)
        """
        populations = {
            "usa": "331 million",
            "uk": "67 million",
            "france": "65 million",
            "germany": "83 million",
            "japan": "126 million",
            "china": "1.4 billion",
            "india": "1.38 billion",
            "brazil": "212 million",
            "australia": "25 million",
            "canada": "38 million"
        }
        
        country = country.lower()
        if country in populations:
            return populations[country]
        elif country == "united states" or country == "united states of america":
            return populations["usa"]
        elif country == "united kingdom":
            return populations["uk"]
        else:
            return f"I don't know the population of {country}"
    
    # Create the OpenAI-based MCP-enabled agent
    class SmartAssistant(OpenAIA2AServer, A2AMCPAgent):
        def __init__(self, api_key):
            # Create agent card
            agent_card = AgentCard(
                name="Smart Assistant",
                description="A smart assistant that can calculate and look up information",
                url="http://localhost:5000",
                version="1.0.0"
            )
            
            # Initialize OpenAI A2A server
            OpenAIA2AServer.__init__(
                self,
                api_key=api_key,
                model="gpt-4",
                system_prompt="""You are a helpful assistant that can calculate and look up information.
                
                When a user asks for calculations, use the calculator tools to perform the calculation.
                When a user asks for country information, use the data lookup tools.
                
                Make your responses concise and helpful."""
            )
            
            # Initialize MCP agent
            A2AMCPAgent.__init__(
                self,
                name="Smart Assistant",
                description="A smart assistant that can calculate and look up information",
                mcp_servers={
                    "calc": calculator_mcp,
                    "data": data_mcp
                }
            )
        
        async def handle_message_async(self, message):
            """Route all messages through OpenAI but add MCP capabilities"""
            try:
                # First try normal OpenAI processing
                response = OpenAIA2AServer.handle_message(self, message)
                
                # Check if the response is a function call
                if response.content.type == "function_call":
                    # Use our MCP handler to execute the function call
                    return await super().handle_message_async(message)
                
                return response
            except Exception as e:
                # Fall back to default handling
                return await super().handle_message_async(message)
        
        def handle_message(self, message):
            """Override to use our async handler"""
            import asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.handle_message_async(message))
        
        async def handle_task_async(self, task):
            """Handle a task by converting to message and back"""
            # Convert task to message
            message_data = task.message or {}
            
            # Create a Message object
            from python_a2a import Message, TextContent, MessageRole
            message = Message(
                content=TextContent(text=message_data.get("content", {}).get("text", "")),
                role=MessageRole.USER,
                conversation_id=task.id
            )
            
            # Process with handle_message
            response = await self.handle_message_async(message)
            
            # Convert response to task
            if response.content.type == "text":
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response.content.text}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            elif response.content.type == "function_response":
                task.artifacts = [{
                    "parts": [{"type": "text", "text": str(response.content.response)}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            else:
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"Response type: {response.content.type}"}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task
        
        def handle_task(self, task):
            """Override to use our async handler"""
            import asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.handle_task_async(task))
    
    # Run the agent
    if __name__ == "__main__":
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("Please set the OPENAI_API_KEY environment variable.")
        
        agent = SmartAssistant(api_key)
        run_server(agent, port=5000)

This agent can:

1. Answer questions using OpenAI's LLM
2. Perform calculations using the calculator MCP
3. Look up country information using the data MCP

Example interactions:

- "What is 125 × 37?"
- "What is the capital of France?"
- "What is the population of China?"

Next Steps
---------

These advanced examples demonstrate the power and flexibility of Python A2A. You can:

- Build complex multi-agent systems
- Integrate LLMs with external tools and data
- Create specialized agents for different tasks

For even more examples, check out the [GitHub repository](https://github.com/themanojdesai/python-a2a/tree/main/examples).