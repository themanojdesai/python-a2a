# examples/chain/planning_agent.py
"""
A specialized agent that provides trip planning assistance.
"""

import os
import argparse
import json
import random
from datetime import datetime, timedelta
from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, 
    FunctionCallContent, FunctionResponseContent,
    FunctionParameter, MessageRole, run_server
)

class PlanningAgent(A2AServer):
    """An agent that plans trips and consults with a weather agent for recommendations."""
    
    def __init__(self, weather_endpoint=None):
        """
        Initialize the planning agent.
        
        Args:
            weather_endpoint: Optional endpoint for a weather agent to consult
        """
        self.weather_endpoint = weather_endpoint
        
        # If we have a weather endpoint, create a client for it
        self.weather_client = None
        if weather_endpoint:
            self.weather_client = A2AClient(weather_endpoint)
    
    def handle_message(self, message):
        """Process incoming A2A messages for trip planning."""
        if message.content.type == "text":
            # Look for trip planning request
            text = message.content.text.lower()
            
            if "trip" in text or "travel" in text or "visit" in text or "plan" in text:
                # Extract location from the text message
                location = None
                for city in ["new york", "london", "tokyo", "paris", "sydney"]:
                    if city in text:
                        location = city.title()
                        break
                
                if not location:
                    return Message(
                        content=TextContent(
                            text="I can help you plan a trip to cities like New York, London, Tokyo, Paris, and Sydney. "
                                "Please specify a destination in your query."
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                # Generate a trip plan
                plan = self._generate_trip_plan(location)
                
                # Check weather if we have a weather agent
                weather_info = ""
                if self.weather_client:
                    try:
                        # Ask weather agent about the destination
                        weather_query = Message(
                            content=FunctionCallContent(
                                name="get_weather",
                                parameters=[
                                    FunctionParameter(name="location", value=location),
                                    FunctionParameter(name="unit", value="celsius")
                                ]
                            ),
                            role=MessageRole.USER
                        )
                        
                        weather_response = self.weather_client.send_message(weather_query)
                        
                        if weather_response.content.type == "function_response":
                            weather_data = weather_response.content.response
                            weather_info = (
                                f"\n\nWeather Forecast:\n"
                                f"Temperature: {weather_data['temperature']}°C\n"
                                f"Conditions: {weather_data['conditions']}\n"
                                f"Humidity: {weather_data['humidity']}%\n"
                                f"Wind: {weather_data['wind_speed']} km/h\n\n"
                            )
                            
                            # Add packing recommendations based on weather
                            weather_info += "Packing Recommendations:\n"
                            if weather_data['temperature'] < 10:
                                weather_info += "- Heavy jacket and warm layers\n"
                                weather_info += "- Winter accessories (gloves, scarf, hat)\n"
                            elif weather_data['temperature'] < 20:
                                weather_info += "- Light jacket or sweater\n"
                                weather_info += "- Long pants and long-sleeve shirts\n"
                            else:
                                weather_info += "- Light clothing\n"
                                weather_info += "- Sun protection (hat, sunglasses, sunscreen)\n"
                            
                            if "Rain" in weather_data['conditions'] or "Thunder" in weather_data['conditions']:
                                weather_info += "- Umbrella and waterproof jacket\n"
                                weather_info += "- Waterproof shoes\n"
                    except Exception as e:
                        weather_info = f"\n\nNote: I tried to get weather information, but encountered an error: {str(e)}"
                
                # Combine plan with weather info
                response_text = plan + weather_info
                
                return Message(
                    content=TextContent(text=response_text),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            else:
                return Message(
                    content=TextContent(
                        text="I'm a trip planning agent. I can help you plan trips to various destinations. "
                             "Just ask me to plan a trip to a specific city!"
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        else:
            return Message(
                content=TextContent(
                    text="I'm a trip planning agent. I can help you plan trips to various destinations. "
                         "Just ask me to plan a trip to a specific city!"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def _generate_trip_plan(self, location):
        """Generate a trip plan for a location."""
        # Start date is randomly 2-4 weeks from now
        start_date = datetime.now() + timedelta(days=random.randint(14, 28))
        end_date = start_date + timedelta(days=random.randint(3, 7))
        
        start_str = start_date.strftime("%A, %B %d, %Y")
        end_str = end_date.strftime("%A, %B %d, %Y")
        
        # Sample attractions for each city
        attractions = {
            "New York": ["Central Park", "Statue of Liberty", "Empire State Building", "Metropolitan Museum of Art", "Broadway"],
            "London": ["British Museum", "Tower of London", "Buckingham Palace", "London Eye", "Hyde Park"],
            "Tokyo": ["Tokyo Skytree", "Meiji Shrine", "Tsukiji Fish Market", "Senso-ji Temple", "Shibuya Crossing"],
            "Paris": ["Eiffel Tower", "Louvre Museum", "Notre-Dame Cathedral", "Montmartre", "Champs-Élysées"],
            "Sydney": ["Sydney Opera House", "Bondi Beach", "Sydney Harbour Bridge", "Royal Botanic Garden", "Taronga Zoo"]
        }
        
        # Sample hotels for each city
        hotels = {
            "New York": ["The Plaza", "Park Hyatt", "The Standard", "Ace Hotel", "The Ritz-Carlton"],
            "London": ["The Savoy", "Claridge's", "The Ritz London", "The Dorchester", "The Langham"],
            "Tokyo": ["Park Hyatt Tokyo", "The Ritz-Carlton Tokyo", "Imperial Hotel", "Cerulean Tower Tokyu Hotel", "Aman Tokyo"],
            "Paris": ["Le Meurice", "Hôtel Plaza Athénée", "Shangri-La Hotel", "The Ritz Paris", "Four Seasons Hotel George V"],
            "Sydney": ["Park Hyatt Sydney", "Four Seasons Hotel Sydney", "The Langham Sydney", "InterContinental Sydney", "Shangri-La Hotel Sydney"]
        }
        
        # Generate a random selection of attractions and a hotel
        selected_attractions = random.sample(attractions.get(location, ["Local sightseeing"]), 3)
        selected_hotel = random.choice(hotels.get(location, ["Local hotel"]))
        
        # Create the trip plan
        plan = (
            f"Trip Plan to {location}\n"
            f"=====================\n\n"
            f"Travel Dates: {start_str} to {end_str}\n\n"
            f"Accommodation: {selected_hotel}\n\n"
            f"Recommended Activities:\n"
        )
        
        for i, attraction in enumerate(selected_attractions, 1):
            plan += f"{i}. Visit {attraction}\n"
        
        plan += (
            f"\nTravel Tips for {location}:\n"
            f"- Book flights early for better rates\n"
            f"- Consider getting a city pass for attractions\n"
            f"- Reserve restaurant tables in advance\n"
        )
        
        return plan
    
    def get_metadata(self):
        """Get metadata about this agent."""
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "PlanningAgent",
            "capabilities": ["text"],
            "supported_locations": ["New York", "London", "Tokyo", "Paris", "Sydney"],
            "connected_to_weather": self.weather_endpoint is not None
        })
        return metadata

def main():
    parser = argparse.ArgumentParser(description="Start a planning A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5002, help="Port to listen on")
    parser.add_argument("--weather-endpoint", default=None, help="Endpoint for weather agent")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the planning agent
    agent = PlanningAgent(weather_endpoint=args.weather_endpoint)
    
    print(f"Starting Planning A2A Agent on http://{args.host}:{args.port}/a2a")
    if args.weather_endpoint:
        print(f"Connected to Weather Agent at {args.weather_endpoint}")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()