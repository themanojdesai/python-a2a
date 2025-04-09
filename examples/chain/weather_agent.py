# examples/chain/weather_agent.py
"""
A specialized agent that provides weather information.
"""

import os
import argparse
import json
import random
from datetime import datetime, timedelta
from python_a2a import A2AServer, Message, TextContent, FunctionCallContent, FunctionResponseContent, MessageRole, run_server

class WeatherAgent(A2AServer):
    """An agent that provides weather information for different locations."""
    
    def handle_message(self, message):
        """Process incoming A2A messages requesting weather information."""
        if message.content.type == "text":
            # Extract location from the text message
            text = message.content.text.lower()
            
            # Look for location in the message
            location = None
            for city in ["new york", "london", "tokyo", "paris", "sydney"]:
                if city in text:
                    location = city.title()
                    break
            
            if not location and "weather" in text:
                # Default location if none specified but weather is mentioned
                location = "New York"
            
            if location:
                # Generate weather data for the location
                weather_data = self._generate_weather_data(location)
                
                # Format as text response
                response_text = (
                    f"Weather for {location}:\n"
                    f"Temperature: {weather_data['temperature']}°C\n"
                    f"Conditions: {weather_data['conditions']}\n"
                    f"Humidity: {weather_data['humidity']}%\n"
                    f"Wind: {weather_data['wind_speed']} km/h"
                )
                
                return Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            else:
                return Message(
                    content=TextContent(
                        text="I can provide weather information for cities like New York, London, Tokyo, Paris, and Sydney. "
                             "Please specify a location in your query."
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        elif message.content.type == "function_call" and message.content.name == "get_weather":
            # Handle function call for weather data
            params = {p.name: p.value for p in message.content.parameters}
            location = params.get("location", "New York")
            unit = params.get("unit", "celsius")
            
            # Generate weather data
            weather_data = self._generate_weather_data(location, unit)
            
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
        
        else:
            return Message(
                content=TextContent(
                    text="I'm a weather agent. You can ask me about the weather in different cities, "
                         "or call the get_weather function with location and unit parameters."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def _generate_weather_data(self, location, unit="celsius"):
        """Generate simulated weather data for a location."""
        # Simulated weather data (in a real implementation, this would call a weather API)
        weather_conditions = ["Sunny", "Partly Cloudy", "Cloudy", "Light Rain", "Heavy Rain", "Thunderstorm", "Snow"]
        
        # Generate random but plausible weather data based on location
        if location.lower() in ["new york", "london", "paris"]:
            temp_base = 15
        elif location.lower() in ["tokyo", "sydney"]:
            temp_base = 22
        else:
            temp_base = 18
        
        # Add some randomness
        temperature = temp_base + random.randint(-5, 5)
        
        # Convert to Fahrenheit if requested
        if unit.lower() == "fahrenheit":
            temperature = temperature * 9/5 + 32
        
        return {
            "location": location,
            "temperature": temperature,
            "unit": unit,
            "conditions": random.choice(weather_conditions),
            "humidity": random.randint(30, 90),
            "wind_speed": random.randint(0, 30),
            "date": datetime.now().strftime("%Y-%m-%d")
        }
    
    def get_metadata(self):
        """Get metadata about this agent."""
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "WeatherAgent",
            "capabilities": ["text", "function_calling"],
            "functions": ["get_weather"],
            "supported_locations": ["New York", "London", "Tokyo", "Paris", "Sydney"]
        })
        return metadata

def main():
    parser = argparse.ArgumentParser(description="Start a weather A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5001, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the weather agent
    agent = WeatherAgent()
    
    print(f"Starting Weather A2A Agent on http://{args.host}:{args.port}/a2a")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()