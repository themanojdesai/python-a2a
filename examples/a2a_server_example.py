"""
Example A2A server implementation using python-a2a.
"""

from python_a2a import (
    A2AServer, 
    AgentCard, 
    AgentSkill, 
    Task, 
    TaskStatus, 
    TaskState,
    skill, 
    agent, 
    run_server
)
from flask import Flask


@agent(
    name="Weather Agent",
    description="Provides weather information for locations worldwide",
    version="1.0.0",
    capabilities={"streaming": True}
)
class WeatherAgent(A2AServer):
    
    def __init__(self):
        # Create agent card using the decorator metadata
        agent_card = AgentCard(
            name=getattr(self.__class__, "name", "Weather Agent"),
            description=getattr(self.__class__, "description", "Weather information agent"),
            url="http://localhost:5001",
            version=getattr(self.__class__, "version", "1.0.0"),
            capabilities=getattr(self.__class__, "capabilities", {"streaming": True}),
            skills=[
                AgentSkill(
                    name="Get Weather",
                    description="Get current weather for a location",
                    tags=["weather", "current"],
                    examples=["What's the weather in Seattle?", "Weather for Tokyo"]
                ),
                AgentSkill(
                    name="Get Forecast",
                    description="Get 5-day weather forecast for a location",
                    tags=["weather", "forecast"],
                    examples=["5-day forecast for Paris", "Forecast for New York"]
                )
            ]
        )
        
        # Initialize with the agent card
        super().__init__(agent_card=agent_card)
    
    @skill(
        name="Get Weather",
        description="Get current weather for a location",
        tags=["weather", "current"]
    )
    def get_weather(self, location):
        """
        Get current weather for a location.
        
        Examples:
            "What's the weather in Seattle?"
            "Weather for Tokyo"
        """
        # Simple mock implementation
        import random
        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Snowy"]
        condition = random.choice(conditions)
        temp = random.randint(50, 85)
        
        return f"Current weather in {location}: {condition}, {temp}°F"
    
    @skill(
        name="Get Forecast",
        description="Get 5-day weather forecast for a location",
        tags=["weather", "forecast"]
    )
    def get_forecast(self, location):
        """
        Get 5-day weather forecast for a location.
        
        Examples:
            "5-day forecast for Paris"
            "Forecast for New York"
        """
        # Simple mock implementation
        import random
        conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Rainy", "Snowy"]
        forecast = []
        
        for i in range(5):
            condition = random.choice(conditions)
            high = random.randint(60, 90)
            low = random.randint(40, high - 10)
            forecast.append(f"Day {i+1}: {condition}, High: {high}°F, Low: {low}°F")
        
        result = f"5-day forecast for {location}:\n" + "\n".join(forecast)
        return result
    
    def handle_task(self, task):
        """Process an A2A task"""
        # Extract message text if available
        message_data = task.message or {}
        
        # Try to extract content in different formats
        text = ""
        if isinstance(message_data, dict):
            # Try to get text from content object
            content = message_data.get("content", {})
            if isinstance(content, dict):
                text = content.get("text", "")
            elif isinstance(content, str):
                text = content
            
            # If not found in content, try direct message text
            if not text and "text" in message_data:
                text = message_data["text"]
        elif isinstance(message_data, str):
            text = message_data
        
        if not text:
            # No text provided, request input
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": "Please ask about the weather or forecast for a location."
                    }
                }
            )
            return task
        
        # Determine if this is a weather or forecast request
        text_lower = text.lower()
        is_forecast = "forecast" in text_lower or "5-day" in text_lower or "5 day" in text_lower
        
        # Extract location (simple approach)
        location = None
        if "in" in text_lower:
            location = text.split("in", 1)[1].strip().rstrip("?.,;!").strip()
        elif "for" in text_lower:
            location = text.split("for", 1)[1].strip().rstrip("?.,;!").strip()
        
        if not location:
            # No location found, request clarification
            task.status = TaskStatus(
                state=TaskState.INPUT_REQUIRED,
                message={
                    "role": "agent",
                    "content": {
                        "type": "text",
                        "text": "Please specify a location for the weather information."
                    }
                }
            )
            return task
        
        # Get weather or forecast
        if is_forecast:
            result = self.get_forecast(location)
        else:
            result = self.get_weather(location)
        
        # Create artifact with the result
        task.artifacts = [{
            "parts": [{
                "type": "text",
                "text": result
            }]
        }]
        
        # Mark as completed
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task


# Run the server if executed directly
if __name__ == "__main__":
    agent = WeatherAgent()
    run_server(agent, host="0.0.0.0", port=5001)
    print("Weather Agent is running at http://localhost:5001")
    print("Agent card is available at http://localhost:5001/agent.json")