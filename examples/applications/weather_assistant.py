#!/usr/bin/env python
"""
Weather Assistant Example

A complete weather assistant application that provides current weather,
forecasts, and activity recommendations based on weather conditions.

To run:
    python weather_assistant.py

Requirements:
    pip install "python-a2a[server]"
"""

import sys
import os
import argparse
import socket
import time
import json
from datetime import datetime, timedelta
import random

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import python_a2a
        import flask
        print("✅ Dependencies installed correctly")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("Please install required packages:")
        print("    pip install \"python-a2a[server]\"")
        return False

def find_available_port(start_port=5000, max_tries=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_tries):
        try:
            # Try to create a socket on the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            # Port is already in use, try the next one
            continue
    
    # If we get here, no ports were available
    print(f"⚠️  Could not find an available port in range {start_port}-{start_port + max_tries - 1}")
    return start_port + 100  # Return something high as fallback

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Weather Assistant Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select)"
    )
    parser.add_argument(
        "--no-test", action="store_true",
        help="Don't run test queries automatically"
    )
    return parser.parse_args()

# Define our weather data
class WeatherData:
    """Class to manage weather data and forecasts"""
    
    def __init__(self):
        # Initialize with some default cities and weather data
        self.cities = {
            "new york": {"lat": 40.7128, "lon": -74.0060},
            "london": {"lat": 51.5074, "lon": -0.1278},
            "tokyo": {"lat": 35.6762, "lon": 139.6503},
            "paris": {"lat": 48.8566, "lon": 2.3522},
            "sydney": {"lat": -33.8688, "lon": 151.2093},
            "berlin": {"lat": 52.5200, "lon": 13.4050},
            "moscow": {"lat": 55.7558, "lon": 37.6173},
            "cairo": {"lat": 30.0444, "lon": 31.2357},
            "rio de janeiro": {"lat": -22.9068, "lon": -43.1729},
            "dubai": {"lat": 25.2048, "lon": 55.2708},
        }
        
        # Weather conditions with temperature ranges (°F) and probability
        self.conditions = [
            {"name": "Sunny", "temp_range": (75, 95), "humidity_range": (30, 60), "prob": 0.25},
            {"name": "Partly Cloudy", "temp_range": (65, 85), "humidity_range": (40, 70), "prob": 0.25},
            {"name": "Cloudy", "temp_range": (60, 75), "humidity_range": (50, 80), "prob": 0.2},
            {"name": "Rainy", "temp_range": (55, 70), "humidity_range": (70, 95), "prob": 0.15},
            {"name": "Thunderstorm", "temp_range": (65, 85), "humidity_range": (75, 95), "prob": 0.05},
            {"name": "Snowy", "temp_range": (20, 35), "humidity_range": (80, 95), "prob": 0.05},
            {"name": "Foggy", "temp_range": (50, 65), "humidity_range": (75, 95), "prob": 0.05},
        ]
        
        # Activity recommendations based on weather conditions
        self.activities = {
            "Sunny": [
                "Go to the beach",
                "Have a picnic in the park",
                "Go hiking",
                "Visit an outdoor cafe",
                "Go cycling",
                "Play outdoor sports",
                "Visit a botanical garden",
                "Go to a farmer's market",
            ],
            "Partly Cloudy": [
                "Go for a walk",
                "Visit outdoor attractions",
                "Go to a street festival",
                "Do some gardening",
                "Eat at an outdoor restaurant",
                "Go to a zoo or wildlife park",
                "Take a photography tour",
            ],
            "Cloudy": [
                "Visit a museum",
                "Go shopping",
                "Take a city tour",
                "Visit historical sites",
                "Go to a local market",
                "Visit an art gallery",
                "Go to a bookstore or library",
            ],
            "Rainy": [
                "Visit a museum",
                "Go to a movie theater",
                "Visit a cafe and read a book",
                "Go to a shopping mall",
                "Visit an aquarium",
                "Take a cooking class",
                "Go to a spa",
            ],
            "Thunderstorm": [
                "Stay home and watch movies",
                "Go to a comedy club",
                "Visit an indoor gaming center",
                "Go to a restaurant with indoor seating",
                "Visit a science museum",
                "Take a virtual museum tour",
            ],
            "Snowy": [
                "Go skiing or snowboarding",
                "Build a snowman",
                "Go sledding",
                "Enjoy hot chocolate at a cafe",
                "Visit a winter festival",
                "Take winter photographs",
                "Go ice skating",
            ],
            "Foggy": [
                "Visit a cozy cafe",
                "Go to a local brewery",
                "Visit an indoor market",
                "Go to a theater performance",
                "Visit a hot spring or spa",
                "Explore a haunted house or ghost tour",
            ],
        }
        
        # Generate and cache current weather data for all cities
        self.current_weather = {}
        for city in self.cities:
            self.current_weather[city] = self._generate_weather()
    
    def _generate_weather(self, condition=None):
        """Generate random weather data"""
        if condition is None:
            # Pick a condition based on probability
            r = random.random()
            cumulative = 0
            for cond in self.conditions:
                cumulative += cond["prob"]
                if r <= cumulative:
                    condition = cond["name"]
                    temp_range = cond["temp_range"]
                    humidity_range = cond["humidity_range"]
                    break
        else:
            # Find the specified condition
            for cond in self.conditions:
                if cond["name"] == condition:
                    temp_range = cond["temp_range"]
                    humidity_range = cond["humidity_range"]
                    break
            else:
                # Default if condition not found
                temp_range = (60, 80)
                humidity_range = (40, 80)
        
        # Generate weather details
        temperature = round(random.uniform(*temp_range))
        humidity = round(random.uniform(*humidity_range))
        wind_speed = round(random.uniform(0, 20))
        
        return {
            "condition": condition,
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": wind_speed,
            "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    def get_current_weather(self, location):
        """Get current weather for a location"""
        location = location.lower()
        
        if location in self.current_weather:
            return self.current_weather[location]
        else:
            # Generate weather for unknown locations
            return self._generate_weather()
    
    def get_forecast(self, location, days=5):
        """Get a weather forecast for a location"""
        location = location.lower()
        
        # Start with current weather as baseline
        if location in self.current_weather:
            current = self.current_weather[location]
            current_condition = current["condition"]
            current_temp = current["temperature"]
        else:
            # Generate baseline for unknown locations
            current = self._generate_weather()
            current_condition = current["condition"]
            current_temp = current["temperature"]
        
        # Generate forecast for the specified number of days
        forecast = [current]
        
        # List of possible next-day conditions based on current condition
        condition_transitions = {
            "Sunny": ["Sunny", "Partly Cloudy"],
            "Partly Cloudy": ["Sunny", "Partly Cloudy", "Cloudy"],
            "Cloudy": ["Partly Cloudy", "Cloudy", "Rainy"],
            "Rainy": ["Cloudy", "Rainy", "Thunderstorm"],
            "Thunderstorm": ["Rainy", "Cloudy"],
            "Snowy": ["Snowy", "Cloudy"],
            "Foggy": ["Foggy", "Cloudy", "Partly Cloudy"],
        }
        
        # Generate each day's forecast based on previous day
        prev_condition = current_condition
        for i in range(1, days):
            # Determine next day's condition based on previous day
            possible_conditions = condition_transitions.get(prev_condition, ["Partly Cloudy", "Cloudy"])
            next_condition = random.choice(possible_conditions)
            
            # Generate random temperature change but maintain reasonable progression
            temp_change = random.uniform(-5, 5)
            next_temp = current_temp + temp_change * i
            
            # Ensure temperature is reasonable for the condition
            for cond in self.conditions:
                if cond["name"] == next_condition:
                    min_temp, max_temp = cond["temp_range"]
                    if next_temp < min_temp:
                        next_temp = min_temp + random.uniform(0, 5)
                    elif next_temp > max_temp:
                        next_temp = max_temp - random.uniform(0, 5)
                    break
            
            # Create the forecast day
            forecast_day = self._generate_weather(next_condition)
            forecast_day["temperature"] = round(next_temp)
            forecast_day["date"] = (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            
            forecast.append(forecast_day)
            prev_condition = next_condition
        
        return forecast
    
    def get_recommendations(self, location):
        """Get activity recommendations based on weather"""
        location = location.lower()
        
        # Get current weather for the location
        if location in self.current_weather:
            current = self.current_weather[location]
        else:
            current = self._generate_weather()
        
        condition = current["condition"]
        
        # Get activities for this condition
        if condition in self.activities:
            # Choose a subset of activities
            activities = self.activities[condition]
            num_activities = min(5, len(activities))
            chosen = random.sample(activities, num_activities)
            
            return {
                "weather": current,
                "recommendations": chosen
            }
        else:
            return {
                "weather": current,
                "recommendations": ["Visit local attractions", "Explore the city", "Try local cuisine"]
            }
    
    def find_nearest_city(self, partial_name):
        """Find the closest city name match"""
        partial_name = partial_name.lower()
        
        # Check for exact match
        if partial_name in self.cities:
            return partial_name
        
        # Check for substring match
        matches = [city for city in self.cities if partial_name in city]
        if matches:
            return matches[0]
        
        # Check for cities that share at least 3 characters with input
        for city in self.cities:
            city_words = city.split()
            for word in city_words:
                if len(partial_name) >= 3 and len(word) >= 3:
                    if partial_name[:3] == word[:3]:
                        return city
        
        # Default to a random city if no match found
        return random.choice(list(self.cities.keys()))

def test_client(port):
    """Run test queries against the weather assistant"""
    from python_a2a import A2AClient
    
    # Wait for server to start
    time.sleep(2)
    
    print("\n🔍 Testing the Weather Assistant...")
    client = A2AClient(f"http://localhost:{port}")
    
    # Test queries
    test_queries = [
        "What's the weather in New York?",
        "Give me a 3-day forecast for Tokyo",
        "What activities do you recommend in London today?"
    ]
    
    for query in test_queries:
        try:
            print(f"\n💬 Query: {query}")
            response = client.ask(query)
            print(f"🌤️  Response: {response}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Test completed! Your Weather Assistant is ready to use.")
    print(f"💻 Server running at: http://localhost:{port}")
    print("📝 Try asking questions like: 'Weather in Paris', 'Forecast for Tokyo', 'What should I do in London today?'")
    print("🛑 Press Ctrl+C in the server terminal to stop.")

def main():
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Find an available port if none was specified
    if args.port is None:
        port = find_available_port()
        print(f"🔍 Auto-selected port: {port}")
    else:
        port = args.port
        print(f"🔍 Using specified port: {port}")
    
    # Import after checking dependencies
    from python_a2a import A2AServer, run_server, TaskStatus, TaskState
    from python_a2a import AgentCard, AgentSkill, skill, agent
    
    print("\n🌤️  Weather Assistant Example 🌤️")
    print("A complete weather information and recommendations assistant")
    
    # Initialize weather data
    weather_data = WeatherData()
    
    # Create the Weather Assistant agent
    @agent(
        name="Weather Assistant",
        description="Get weather information and activity recommendations",
        version="1.0.0"
    )
    class WeatherAssistant(A2AServer):
        """
        A weather assistant that provides current weather, forecasts, and
        activity recommendations for cities around the world.
        """
        def __init__(self, weather_data):
            # Initialize with our agent card
            super().__init__(agent_card=AgentCard(
                name="Weather Assistant",
                description="Get weather information and activity recommendations",
                url=f"http://localhost:{port}",
                version="1.0.0",
                skills=[
                    AgentSkill(
                        name="Current Weather",
                        description="Get current weather for a location",
                        examples=["What's the weather in New York?", "Current weather in Paris"]
                    ),
                    AgentSkill(
                        name="Weather Forecast",
                        description="Get a multi-day weather forecast for a location",
                        examples=["Forecast for Tokyo", "5-day forecast for London"]
                    ),
                    AgentSkill(
                        name="Activity Recommendations",
                        description="Get weather-appropriate activity recommendations",
                        examples=["What should I do in Tokyo today?", "Activities for Paris weather"]
                    )
                ]
            ))
            self.weather_data = weather_data
        
        @skill(
            name="Current Weather",
            description="Get current weather for a location"
        )
        def get_current_weather(self, location):
            """
            Get the current weather for a location.
            
            Args:
                location: The city to get weather for
                
            Returns:
                Current weather information
            """
            # Find nearest city match
            city = self.weather_data.find_nearest_city(location)
            weather = self.weather_data.get_current_weather(city)
            
            response = (
                f"Current weather in {city.title()}:\n"
                f"Condition: {weather['condition']}\n"
                f"Temperature: {weather['temperature']}°F\n"
                f"Humidity: {weather['humidity']}%\n"
                f"Wind Speed: {weather['wind_speed']} mph\n"
                f"Updated: {weather['updated']}"
            )
            
            return response
        
        @skill(
            name="Weather Forecast",
            description="Get a multi-day weather forecast for a location"
        )
        def get_forecast(self, location, days=3):
            """
            Get a weather forecast for a location.
            
            Args:
                location: The city to get forecast for
                days: Number of days for the forecast (default: 3)
                
            Returns:
                Multi-day weather forecast
            """
            # Find nearest city match
            city = self.weather_data.find_nearest_city(location)
            forecast = self.weather_data.get_forecast(city, days)
            
            response = f"Weather forecast for {city.title()}:\n\n"
            
            for i, day in enumerate(forecast):
                day_name = "Today" if i == 0 else (
                    "Tomorrow" if i == 1 else 
                    datetime.strptime(day['date'], "%Y-%m-%d").strftime("%A")
                )
                
                response += (
                    f"{day_name}:\n"
                    f"  Condition: {day['condition']}\n"
                    f"  Temperature: {day['temperature']}°F\n"
                    f"  Humidity: {day['humidity']}%\n"
                    f"  Wind Speed: {day['wind_speed']} mph\n\n"
                )
            
            return response
        
        @skill(
            name="Activity Recommendations",
            description="Get weather-appropriate activity recommendations"
        )
        def get_recommendations(self, location):
            """
            Get activity recommendations based on current weather.
            
            Args:
                location: The city to get recommendations for
                
            Returns:
                Weather-appropriate activity recommendations
            """
            # Find nearest city match
            city = self.weather_data.find_nearest_city(location)
            result = self.weather_data.get_recommendations(city)
            
            weather = result["weather"]
            activities = result["recommendations"]
            
            response = (
                f"Activity recommendations for {city.title()}:\n"
                f"Current weather: {weather['condition']}, {weather['temperature']}°F\n\n"
                f"Recommended activities:\n"
            )
            
            for i, activity in enumerate(activities, 1):
                response += f"{i}. {activity}\n"
            
            return response
        
        def handle_task(self, task):
            """Process incoming tasks by routing to the appropriate skill"""
            try:
                # Extract message text from task
                message_data = task.message or {}
                content = message_data.get("content", {})
                text = content.get("text", "") if isinstance(content, dict) else ""
                
                # Default response
                response_text = (
                    "I'm a Weather Assistant. I can help with:\n"
                    "- Current weather (e.g., 'What's the weather in Tokyo?')\n"
                    "- Weather forecasts (e.g., 'Forecast for London')\n"
                    "- Activity recommendations (e.g., 'What should I do in Paris today?')"
                )
                
                # Process the message based on content
                text_lower = text.lower()
                
                # Extract location from the message if present
                import re
                location_match = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)(?:\?|$|\.)", text_lower)
                location = location_match.group(1).strip() if location_match else None
                
                if not location:
                    # Try to find any capitalized city names
                    words = text.split()
                    for word in words:
                        if word[0].isupper() and len(word) > 3:
                            potential_city = self.weather_data.find_nearest_city(word)
                            if potential_city:
                                location = potential_city
                                break
                
                if not location:
                    # No location found, use default response
                    pass
                elif "forecast" in text_lower:
                    # This is a forecast request
                    days = 3  # Default to 3-day forecast
                    days_match = re.search(r"(\d+)[\s-]*day", text_lower)
                    if days_match:
                        days = min(int(days_match.group(1)), 7)  # Limit to 7 days
                    
                    response_text = self.get_forecast(location, days)
                    
                elif any(word in text_lower for word in ["do", "activity", "activities", "recommend", "suggestion"]):
                    # This is an activity recommendation request
                    response_text = self.get_recommendations(location)
                    
                elif any(word in text_lower for word in ["weather", "temperature", "condition", "how is"]):
                    # This is a current weather request
                    response_text = self.get_current_weather(location)
                
                # Create artifact with response
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response_text}]
                }]
                
                # Mark as completed
                task.status = TaskStatus(state=TaskState.COMPLETED)
                
                return task
                
            except Exception as e:
                # Handle errors gracefully
                error_message = f"Sorry, I encountered an error: {str(e)}"
                task.artifacts = [{
                    "parts": [{"type": "text", "text": error_message}]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
                return task
    
    # Create the weather assistant
    weather_assistant = WeatherAssistant(weather_data)
    
    # Print the agent information
    print("\n=== Weather Assistant Information ===")
    print(f"Name: {weather_assistant.agent_card.name}")
    print(f"Description: {weather_assistant.agent_card.description}")
    print(f"URL: {weather_assistant.agent_card.url}")
    
    print("\n=== Available Skills ===")
    for skill in weather_assistant.agent_card.skills:
        print(f"- {skill.name}: {skill.description}")
        if hasattr(skill, "examples") and skill.examples:
            print(f"  Examples: {', '.join(skill.examples)}")
    
    print("\n=== Cities with Weather Data ===")
    print(", ".join(city.title() for city in weather_data.cities.keys()))
    
    # Start test client in a separate process if testing is enabled
    import multiprocessing
    client_process = None
    
    if not args.no_test:
        client_process = multiprocessing.Process(target=test_client, args=(port,))
        client_process.start()
    
    # Start the server
    print(f"\n🚀 Starting Weather Assistant on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        from python_a2a import run_server
        run_server(weather_assistant, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        if "Address already in use" in str(e):
            print(f"\nPort {port} is already in use. Try using a different port:")
            print(f"    python weather_assistant.py --port {port + 1}")
        return 1
    finally:
        # Clean up client process
        if client_process:
            client_process.terminate()
            client_process.join()
    
    print("\n=== What's Next? ===")
    print("1. Try connecting to the server with a client:")
    print(f"    python -c \"from python_a2a import A2AClient; print(A2AClient('http://localhost:{port}').ask('Weather in Tokyo'))\"")
    print("2. Try the 'travel_planner.py' example for a more advanced multi-agent system")
    print("3. Try connecting an LLM to your assistant with 'openai_mcp_agent.py'")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)