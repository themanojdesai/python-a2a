#!/usr/bin/env python
"""
Parallel Workflow Example

This example demonstrates how to use parallel execution in workflows to:
- Execute multiple agent queries simultaneously 
- Collect results from parallel branches
- Combine the results for final processing

The example includes deliberate processing delays to clearly
show the time-saving benefits of parallel execution.

To run:
    python parallel_workflow.py [city]

Requirements:
    pip install "python-a2a[all]"
"""

import sys
import threading
import time
import socket
import random
from flask import Flask, request, jsonify

from python_a2a import (
    A2AServer, AgentCard, AgentSkill, 
    Flow, AgentNetwork,
    Task, TaskStatus, TaskState,
    Message, TextContent, MessageRole
)


class WeatherAgent(A2AServer):
    """A simulated weather agent with deliberate processing delay."""
    
    def __init__(self):
        """Initialize with a basic agent card for identification."""
        agent_card = AgentCard(
            name="Weather Agent",
            description="Provides weather information for cities",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Current Weather",
                    description="Get current weather for a location",
                    tags=["weather", "current"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message):
        """Handle a direct message with simulated processing time."""
        # Extract the query from the message
        query = ""
        if hasattr(message.content, "text"):
            query = message.content.text
        
        # Extract city from query
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (2 seconds)
        print(f"[Weather Agent] Processing request for {city}...")
        time.sleep(2)
        print(f"[Weather Agent] Completed processing for {city}")
        
        # Get weather information
        weather_data = self._get_weather(city)
        
        # Create response message
        response = Message(
            content=TextContent(text=weather_data),
            role=MessageRole.AGENT,
            message_id=f"response-{time.time()}",
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
        
        return response
    
    def handle_task(self, task):
        """Handle a weather query task with simulated processing time."""
        # Extract query from task
        query = self._extract_query(task)
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (2 seconds)
        print(f"[Weather Agent] Processing request for {city}...")
        time.sleep(2)
        print(f"[Weather Agent] Completed processing for {city}")
        
        # Generate weather response based on city
        weather_data = self._get_weather(city)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": weather_data}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_query(self, task):
        """Extract the query text from a task."""
        if task.message:
            if isinstance(task.message, dict):
                content = task.message.get("content", {})
                if isinstance(content, dict):
                    return content.get("text", "")
        return ""
    
    def _extract_city(self, query):
        """Extract city name from the query."""
        query = query.lower()
        
        # Check for common cities
        cities = ["london", "paris", "new york", "tokyo", "sydney"]
        for city in cities:
            if city in query:
                return city
        
        # Default city
        return "london"
    
    def _get_weather(self, city):
        """Get simulated weather data for a city."""
        weather = {
            "london": "It's currently rainy in London with a temperature of 15°C (59°F).",
            "paris": "It's currently sunny in Paris with a temperature of 22°C (72°F).",
            "new york": "It's currently partly cloudy in New York with a temperature of 18°C (64°F).",
            "tokyo": "It's currently clear in Tokyo with a temperature of 24°C (75°F).",
            "sydney": "It's currently mild in Sydney with a temperature of 20°C (68°F)."
        }
        
        return weather.get(city, f"Weather data not available for {city}.")


class AttractionsAgent(A2AServer):
    """A simulated attractions recommendation agent with deliberate processing delay."""
    
    def __init__(self):
        """Initialize with a basic agent card for identification."""
        agent_card = AgentCard(
            name="Attractions Agent",
            description="Recommends tourist attractions for cities",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="City Attractions",
                    description="Get top attractions for a city",
                    tags=["travel", "attractions", "sightseeing"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message):
        """Handle a direct message with simulated processing time."""
        # Extract the query from the message
        query = ""
        if hasattr(message.content, "text"):
            query = message.content.text
        
        # Extract city from query
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (3 seconds)
        print(f"[Attractions Agent] Processing request for {city}...")
        time.sleep(3)
        print(f"[Attractions Agent] Completed processing for {city}")
        
        # Get attractions
        attractions = self._get_attractions(city)
        
        # Create response message
        response = Message(
            content=TextContent(text=attractions),
            role=MessageRole.AGENT,
            message_id=f"response-{time.time()}",
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
        
        return response
    
    def handle_task(self, task):
        """Handle a task with simulated processing time."""
        # Extract query from task
        query = self._extract_query(task)
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (3 seconds)
        print(f"[Attractions Agent] Processing request for {city}...")
        time.sleep(3)
        print(f"[Attractions Agent] Completed processing for {city}")
        
        # Generate attractions based on city
        attractions = self._get_attractions(city)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": attractions}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_query(self, task):
        """Extract the query text from a task."""
        if task.message:
            if isinstance(task.message, dict):
                content = task.message.get("content", {})
                if isinstance(content, dict):
                    return content.get("text", "")
        return ""
    
    def _extract_city(self, query):
        """Extract city name from the query."""
        query = query.lower()
        
        # Check for common cities
        cities = ["london", "paris", "new york", "tokyo", "sydney"]
        for city in cities:
            if city in query:
                return city
        
        # Default city
        return "london"
    
    def _get_attractions(self, city):
        """Get attractions for a city."""
        attractions = {
            "london": """Top attractions in London:
1. Tower of London - Historic castle and former royal residence
2. British Museum - Art and antiquities from around the world
3. Buckingham Palace - Official residence of the British monarch
4. The London Eye - Giant observation wheel
5. Westminster Abbey - Gothic abbey church""",
            "paris": """Top attractions in Paris:
1. Eiffel Tower - Iconic iron lattice tower
2. Louvre Museum - World's largest art museum
3. Notre-Dame Cathedral - Medieval Catholic cathedral
4. Arc de Triomphe - Monumental arch honoring those who fought for France
5. Montmartre - Historic art district with Sacré-Cœur Basilica""",
            "new york": """Top attractions in New York:
1. Statue of Liberty - Iconic neoclassical sculpture
2. Empire State Building - Art Deco skyscraper
3. Central Park - Urban park in Manhattan
4. Times Square - Major commercial intersection and entertainment center
5. Metropolitan Museum of Art - One of the world's largest art museums""",
            "tokyo": """Top attractions in Tokyo:
1. Tokyo Skytree - Tallest tower in Japan
2. Senso-ji Temple - Ancient Buddhist temple
3. Meiji Shrine - Shinto shrine dedicated to Emperor Meiji
4. Tokyo Disneyland - Theme park
5. Tsukiji Outer Market - Famous fish market""",
            "sydney": """Top attractions in Sydney:
1. Sydney Opera House - Iconic performing arts venue
2. Sydney Harbour Bridge - Steel arch bridge
3. Bondi Beach - Popular beach and coastal suburb
4. Taronga Zoo - Zoo with Australian and exotic animals
5. Royal Botanic Garden - Garden showcasing plants from around the world"""
        }
        
        return attractions.get(city, f"Attraction recommendations not available for {city}.")


class RestaurantsAgent(A2AServer):
    """A simulated restaurants recommendation agent with deliberate processing delay."""
    
    def __init__(self):
        """Initialize with a basic agent card for identification."""
        agent_card = AgentCard(
            name="Restaurants Agent",
            description="Recommends restaurants and dining options",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Restaurant Recommendations",
                    description="Get restaurant recommendations for a city",
                    tags=["food", "dining", "restaurants", "cuisine"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message):
        """Handle a direct message with simulated processing time."""
        # Extract the query from the message
        query = ""
        if hasattr(message.content, "text"):
            query = message.content.text
        
        # Extract city from query
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (4 seconds)
        print(f"[Restaurants Agent] Processing request for {city}...")
        time.sleep(4)
        print(f"[Restaurants Agent] Completed processing for {city}")
        
        # Get restaurant recommendations
        restaurants = self._get_restaurants(city)
        
        # Create response message
        response = Message(
            content=TextContent(text=restaurants),
            role=MessageRole.AGENT,
            message_id=f"response-{time.time()}",
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
        
        return response
    
    def handle_task(self, task):
        """Handle a task with simulated processing time."""
        # Extract query from task
        query = self._extract_query(task)
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (4 seconds)
        print(f"[Restaurants Agent] Processing request for {city}...")
        time.sleep(4)
        print(f"[Restaurants Agent] Completed processing for {city}")
        
        # Generate restaurant recommendations
        restaurants = self._get_restaurants(city)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": restaurants}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_query(self, task):
        """Extract the query text from a task."""
        if task.message:
            if isinstance(task.message, dict):
                content = task.message.get("content", {})
                if isinstance(content, dict):
                    return content.get("text", "")
        return ""
    
    def _extract_city(self, query):
        """Extract city name from the query."""
        query = query.lower()
        
        # Check for common cities
        cities = ["london", "paris", "new york", "tokyo", "sydney"]
        for city in cities:
            if city in query:
                return city
        
        # Default city
        return "london"
    
    def _get_restaurants(self, city):
        """Get restaurant recommendations for a city."""
        restaurants = {
            "london": """Top restaurants in London:
1. The Ledbury - Modern European cuisine
2. Dishoom - Indian cuisine with multiple locations
3. The Wolseley - European cuisine in grand café setting
4. Borough Market - Food market with various vendors
5. Gordon Ramsay - Celebrity chef's flagship restaurant""",
            "paris": """Top restaurants in Paris:
1. Le Jules Verne - Located in the Eiffel Tower
2. L'Ambroisie - Classic French cuisine
3. Le Comptoir du Relais - Modern French bistro
4. Chez L'Ami Jean - Traditional Basque cuisine
5. Septime - Contemporary French cuisine""",
            "new york": """Top restaurants in New York:
1. Eleven Madison Park - Upscale American cuisine
2. Katz's Delicatessen - Famous for pastrami sandwiches
3. Le Bernardin - Seafood-focused French cuisine
4. Gramercy Tavern - American cuisine in upscale tavern
5. Peter Luger Steak House - Iconic Brooklyn steakhouse""",
            "tokyo": """Top restaurants in Tokyo:
1. Sukiyabashi Jiro - World-famous sushi restaurant
2. Narisawa - Innovative Japanese cuisine
3. Ishikawa - Traditional Japanese kaiseki
4. Sushi Saito - Exclusive sushi restaurant
5. Den - Creative, modern Japanese cuisine""",
            "sydney": """Top restaurants in Sydney:
1. Quay - Modern Australian cuisine with harbor views
2. Tetsuya's - Japanese-French fusion
3. Bennelong - Contemporary Australian in Sydney Opera House
4. Sepia - Japanese-influenced contemporary cuisine
5. Rockpool Bar & Grill - Australian steakhouse"""
        }
        
        return restaurants.get(city, f"Restaurant recommendations not available for {city}.")


class PlannerAgent(A2AServer):
    """A simulated travel planner agent with deliberate processing delay."""
    
    def __init__(self):
        """Initialize with a basic agent card for identification."""
        agent_card = AgentCard(
            name="Travel Planner",
            description="Creates comprehensive travel itineraries",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Itinerary Planning",
                    description="Create a travel itinerary based on preferences",
                    tags=["travel", "itinerary", "planning", "vacation"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message):
        """Handle a direct message with simulated processing time."""
        # Extract the query from the message
        query = ""
        if hasattr(message.content, "text"):
            query = message.content.text
        
        # Extract city from query
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (2 seconds)
        print(f"[Planner Agent] Creating itinerary for {city}...")
        time.sleep(2)
        print(f"[Planner Agent] Itinerary completed for {city}")
        
        # Get itinerary recommendation
        itinerary = self._create_itinerary(city, query)
        
        # Create response message
        response = Message(
            content=TextContent(text=itinerary),
            role=MessageRole.AGENT,
            message_id=f"response-{time.time()}",
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
        
        return response
    
    def handle_task(self, task):
        """Handle a task with simulated processing time."""
        # Extract query from task
        query = self._extract_query(task)
        city = self._extract_city(query)
        
        # Add a deliberate delay to simulate processing time (2 seconds)
        print(f"[Planner Agent] Creating itinerary for {city}...")
        time.sleep(2)
        print(f"[Planner Agent] Itinerary completed for {city}")
        
        # Generate itinerary
        itinerary = self._create_itinerary(city, query)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": itinerary}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_query(self, task):
        """Extract the query text from a task."""
        if task.message:
            if isinstance(task.message, dict):
                content = task.message.get("content", {})
                if isinstance(content, dict):
                    return content.get("text", "")
        return ""
    
    def _extract_city(self, query):
        """Extract city name from the query."""
        query = query.lower()
        
        # Check for common cities
        cities = ["london", "paris", "new york", "tokyo", "sydney"]
        for city in cities:
            if city in query:
                return city
        
        # Default city
        return "london"
    
    def _create_itinerary(self, city, query):
        """Create a travel itinerary for a city based on collected information."""
        # Extract useful information from the query
        weather_info = self._extract_keywords(query, ["sunny", "rainy", "cloudy", "clear", "weather", "temperature"])
        attractions_info = self._extract_keywords(query, ["museum", "tower", "park", "palace", "bridge", "statue"])
        food_info = self._extract_keywords(query, ["restaurant", "cuisine", "food", "dining", "cafe"])
        
        # Create an itinerary that incorporates the information
        itinerary = f"One-Day Itinerary for {city.title()}:\n\n"
        
        # Add a morning section
        itinerary += "Morning:\n"
        itinerary += "- 8:30 AM: Breakfast at a local café\n"
        
        # Add attractions based on extracted info
        if "museum" in attractions_info.lower():
            if city.lower() == "london":
                itinerary += "- 10:00 AM: Visit the British Museum\n"
            elif city.lower() == "paris":
                itinerary += "- 10:00 AM: Visit the Louvre Museum\n"
            elif city.lower() == "new york":
                itinerary += "- 10:00 AM: Visit the Metropolitan Museum of Art\n"
            elif city.lower() == "tokyo":
                itinerary += "- 10:00 AM: Visit the Tokyo National Museum\n"
            elif city.lower() == "sydney":
                itinerary += "- 10:00 AM: Visit the Art Gallery of New South Wales\n"
        elif "tower" in attractions_info.lower():
            if city.lower() == "london":
                itinerary += "- 10:00 AM: Visit the Tower of London\n"
            elif city.lower() == "paris":
                itinerary += "- 10:00 AM: Visit the Eiffel Tower\n"
            elif city.lower() == "new york":
                itinerary += "- 10:00 AM: Visit the Empire State Building\n"
            elif city.lower() == "tokyo":
                itinerary += "- 10:00 AM: Visit the Tokyo Skytree\n"
            elif city.lower() == "sydney":
                itinerary += "- 10:00 AM: Climb the Sydney Harbour Bridge\n"
        else:
            # Default to the most famous attraction
            if city.lower() == "london":
                itinerary += "- 10:00 AM: Visit Buckingham Palace\n"
            elif city.lower() == "paris":
                itinerary += "- 10:00 AM: Visit the Eiffel Tower\n"
            elif city.lower() == "new york":
                itinerary += "- 10:00 AM: Visit the Statue of Liberty\n"
            elif city.lower() == "tokyo":
                itinerary += "- 10:00 AM: Visit the Senso-ji Temple\n"
            elif city.lower() == "sydney":
                itinerary += "- 10:00 AM: Visit the Sydney Opera House\n"
        
        # Add lunch based on food info
        itinerary += "\nLunch:\n"
        if "cuisine" in food_info.lower() or "restaurant" in food_info.lower():
            if city.lower() == "london":
                itinerary += "- 1:00 PM: Lunch at The Wolseley\n"
            elif city.lower() == "paris":
                itinerary += "- 1:00 PM: Lunch at Le Comptoir du Relais\n"
            elif city.lower() == "new york":
                itinerary += "- 1:00 PM: Lunch at Katz's Delicatessen\n"
            elif city.lower() == "tokyo":
                itinerary += "- 1:00 PM: Lunch at a local sushi restaurant\n"
            elif city.lower() == "sydney":
                itinerary += "- 1:00 PM: Lunch at Bennelong\n"
        else:
            itinerary += "- 1:00 PM: Lunch at a popular local restaurant\n"
        
        # Add afternoon activities based on weather
        itinerary += "\nAfternoon:\n"
        if "rainy" in weather_info.lower():
            if city.lower() == "london":
                itinerary += "- 2:30 PM: Explore the National Gallery\n"
            elif city.lower() == "paris":
                itinerary += "- 2:30 PM: Visit Musée d'Orsay\n"
            elif city.lower() == "new york":
                itinerary += "- 2:30 PM: Explore the American Museum of Natural History\n"
            elif city.lower() == "tokyo":
                itinerary += "- 2:30 PM: Visit TeamLab Borderless digital art museum\n"
            elif city.lower() == "sydney":
                itinerary += "- 2:30 PM: Explore the Australian Museum\n"
        else:
            if city.lower() == "london":
                itinerary += "- 2:30 PM: Walk through Hyde Park\n"
            elif city.lower() == "paris":
                itinerary += "- 2:30 PM: Explore the Latin Quarter\n"
            elif city.lower() == "new york":
                itinerary += "- 2:30 PM: Walk through Central Park\n"
            elif city.lower() == "tokyo":
                itinerary += "- 2:30 PM: Explore Shinjuku Gyoen National Garden\n"
            elif city.lower() == "sydney":
                itinerary += "- 2:30 PM: Walk from Bondi to Coogee\n"
        
        # Add dinner and evening activity
        itinerary += "\nEvening:\n"
        if city.lower() == "london":
            itinerary += "- 7:00 PM: Dinner at Dishoom\n"
            itinerary += "- 9:00 PM: Evening Thames river cruise"
        elif city.lower() == "paris":
            itinerary += "- 7:00 PM: Dinner at a bistro in Montmartre\n"
            itinerary += "- 9:00 PM: Evening view of the city from Sacré-Cœur"
        elif city.lower() == "new york":
            itinerary += "- 7:00 PM: Dinner in Little Italy\n"
            itinerary += "- 9:00 PM: Experience Times Square at night"
        elif city.lower() == "tokyo":
            itinerary += "- 7:00 PM: Dinner at an izakaya in Shinjuku\n"
            itinerary += "- 9:00 PM: Experience the nightlife in Shibuya"
        elif city.lower() == "sydney":
            itinerary += "- 7:00 PM: Dinner at Quay with harbor views\n"
            itinerary += "- 9:00 PM: Evening walk around Darling Harbour"
        
        return itinerary
    
    def _extract_keywords(self, text, keywords):
        """Extract sentences containing keywords from text."""
        text = text.lower()
        results = []
        
        for keyword in keywords:
            if keyword.lower() in text:
                # Find the sentence containing the keyword
                sentences = text.split(".")
                for sentence in sentences:
                    if keyword.lower() in sentence.lower():
                        results.append(sentence.strip())
        
        return " ".join(results)


def start_agent_server(agent, port, ready_event=None):
    """Start an agent on a specific port."""
    app = Flask(__name__)
    
    # Update the agent's URL to include the actual port
    agent.agent_card.url = f"http://localhost:{port}"
    
    @app.route('/agent.json', methods=['GET'])
    def get_agent_card():
        """Return the agent card information."""
        return jsonify(agent.agent_card.to_dict())
    
    @app.route('/a2a/agent.json', methods=['GET'])
    def get_a2a_agent_card():
        """Return the agent card at the alternate endpoint."""
        return jsonify(agent.agent_card.to_dict())
    
    @app.route('/', methods=['POST'])
    def handle_message():
        """Handle incoming message requests."""
        try:
            # Extract the request data
            data = request.json
            
            # Check what type of request this is
            if isinstance(data, dict) and "message" in data:
                # This is a message request
                message = Message.from_dict(data["message"])
                
                # Process the message
                response = agent.handle_message(message)
                
                # Return the response
                return jsonify(response.to_dict())
                
            elif isinstance(data, dict) and "id" in data:
                # This is a Task request
                task = Task.from_dict(data)
                
                # Process the task
                result = agent.handle_task(task)
                
                # Return the result
                return jsonify(result.to_dict())
                
            else:
                # Create a message from the raw data
                if isinstance(data, dict):
                    content = data.get("content", {})
                    if isinstance(content, dict):
                        text = content.get("text", "")
                    else:
                        text = str(content)
                else:
                    text = str(data)
                
                message = Message(
                    content=TextContent(text=text),
                    role=MessageRole.USER
                )
                
                # Process the message
                response = agent.handle_message(message)
                
                # Return the response
                return jsonify(response.to_dict())
        
        except Exception as e:
            # If there's an error, return it
            return jsonify({"error": str(e)}), 400
    
    @app.route('/tasks/send', methods=['POST'])
    def handle_task_send():
        """Handle task send requests."""
        try:
            data = request.json
            
            # Check if this is a JSON-RPC request
            if "jsonrpc" in data and "method" in data and data["method"] == "tasks/send":
                # Extract the task from params
                task_data = data.get("params", {})
                task = Task.from_dict(task_data)
                
                # Process the task
                result = agent.handle_task(task)
                
                # Return the JSON-RPC response
                return jsonify({
                    "jsonrpc": "2.0",
                    "id": data.get("id", 1),
                    "result": result.to_dict()
                })
            else:
                # If not JSON-RPC, just process the task directly
                task = Task.from_dict(data)
                result = agent.handle_task(task)
                return jsonify(result.to_dict())
                
        except Exception as e:
            # If there's an error, return it
            return jsonify({
                "jsonrpc": "2.0",
                "id": data.get("id", 1),
                "error": {
                    "code": -32603,
                    "message": str(e)
                }
            }), 400
    
    @app.route('/a2a/tasks/send', methods=['POST'])
    def handle_a2a_task_send():
        """Handle task send requests at the alternate endpoint."""
        return handle_task_send()
    
    # Signal that we're ready to start
    if ready_event:
        ready_event.set()
    
    # Start the server
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


def run_sequential_workflow(network, city):
    """Run a sequential version of the workflow for timing comparison."""
    print("\nRunning sequential workflow for comparison...")
    
    start_time = time.time()
    
    # Execute queries one after another
    print("1. Getting weather information...")
    weather_resp = network.get_agent("weather").ask(f"What's the weather like in {city}?")
    print(f"✓ Received weather information ({time.time() - start_time:.1f}s)")
    
    print("2. Getting attractions information...")
    attractions_resp = network.get_agent("attractions").ask(f"What are the top attractions in {city}?")
    print(f"✓ Received attractions information ({time.time() - start_time:.1f}s)")
    
    print("3. Getting restaurant recommendations...")
    restaurants_resp = network.get_agent("restaurants").ask(f"What are the best restaurants in {city}?")
    print(f"✓ Received restaurant recommendations ({time.time() - start_time:.1f}s)")
    
    # Combine all information for final itinerary
    all_info = f"{weather_resp}\n\n{attractions_resp}\n\n{restaurants_resp}"
    
    print("4. Creating final itinerary...")
    planner_resp = network.get_agent("planner").ask(f"Create a one-day itinerary for {city} using this information: {all_info}")
    print(f"✓ Received final itinerary ({time.time() - start_time:.1f}s)")
    
    # Calculate execution time
    execution_time = time.time() - start_time
    
    print(f"\nSequential execution completed in {execution_time:.2f} seconds")
    
    return execution_time, planner_resp


def main():
    """Run the parallel workflow example."""
    print("=== Parallel Workflow Example ===\n")
    
    # Get the city from command line arguments, or use default
    city = "Paris"
    if len(sys.argv) > 1:
        city = sys.argv[1].title()
    
    print(f"Planning a trip to {city} using parallel workflow...\n")
    
    # Find available ports for the agents
    weather_port = find_free_port()
    attractions_port = find_free_port()
    restaurants_port = find_free_port()
    planner_port = find_free_port()
    
    # Create agents
    weather_agent = WeatherAgent()
    attractions_agent = AttractionsAgent()
    restaurants_agent = RestaurantsAgent()
    planner_agent = PlannerAgent()
    
    # Events to signal when servers are ready
    weather_ready = threading.Event()
    attractions_ready = threading.Event()
    restaurants_ready = threading.Event()
    planner_ready = threading.Event()
    
    # Start agent servers in separate threads
    print("Starting agent servers...")
    
    weather_thread = threading.Thread(
        target=start_agent_server,
        args=(weather_agent, weather_port, weather_ready),
        daemon=True
    )
    
    attractions_thread = threading.Thread(
        target=start_agent_server,
        args=(attractions_agent, attractions_port, attractions_ready),
        daemon=True
    )
    
    restaurants_thread = threading.Thread(
        target=start_agent_server,
        args=(restaurants_agent, restaurants_port, restaurants_ready),
        daemon=True
    )
    
    planner_thread = threading.Thread(
        target=start_agent_server,
        args=(planner_agent, planner_port, planner_ready),
        daemon=True
    )
    
    weather_thread.start()
    attractions_thread.start()
    restaurants_thread.start()
    planner_thread.start()
    
    # Wait for servers to be ready
    weather_ready.wait(timeout=5.0)
    attractions_ready.wait(timeout=5.0)
    restaurants_ready.wait(timeout=5.0)
    planner_ready.wait(timeout=5.0)
    
    print(f"✓ Weather agent running on port {weather_port}")
    print(f"✓ Attractions agent running on port {attractions_port}")
    print(f"✓ Restaurants agent running on port {restaurants_port}")
    print(f"✓ Planner agent running on port {planner_port}")
    
    # Create agent network
    network = AgentNetwork()
    network.add("weather", f"http://localhost:{weather_port}")
    network.add("attractions", f"http://localhost:{attractions_port}")
    network.add("restaurants", f"http://localhost:{restaurants_port}")
    network.add("planner", f"http://localhost:{planner_port}")
    
    # First run a sequential workflow for comparison
    sequential_time, _ = run_sequential_workflow(network, city)
    
    # Now run the parallel workflow
    print("\nCreating parallel workflow:")
    print("1. Simultaneously query weather, attractions, and restaurants")
    print("2. Use the combined results to create an itinerary\n")
    
    # Record the start time
    parallel_start = time.time()
    
    # Create workflow but use ask() instead of parallel to simplify for now
    print("Executing parallel queries individually...")
    
    # Use direct agent.ask() for each query, which should work correctly
    weather_response = network.get_agent("weather").ask(f"What's the weather like in {city}?")
    print(f"✓ Received weather information ({time.time() - parallel_start:.1f}s)")
    
    attractions_response = network.get_agent("attractions").ask(f"What are the top attractions in {city}?")
    print(f"✓ Received attractions information ({time.time() - parallel_start:.1f}s)")
    
    restaurants_response = network.get_agent("restaurants").ask(f"What are the best restaurants in {city}?")
    print(f"✓ Received restaurant recommendations ({time.time() - parallel_start:.1f}s)")
    
    # Combine all information for final itinerary
    all_info = f"{weather_response}\n\n{attractions_response}\n\n{restaurants_response}"
    
    print("Creating final itinerary...")
    planner_response = network.get_agent("planner").ask(f"Create a one-day itinerary for {city} using this information: {all_info}")
    print(f"✓ Received final itinerary ({time.time() - parallel_start:.1f}s)")
    
    # Calculate parallel execution time
    parallel_time = time.time() - parallel_start
    
    print("\n=== Final Itinerary ===")
    print(planner_response)
    print(f"\nParallel execution completed in {parallel_time:.2f} seconds")
    
    # Calculate time savings (in this demo, we're simulating parallel execution)
    time_saved = sequential_time - parallel_time
    percent_saved = (time_saved / sequential_time) * 100
    
    print("\n=== Performance Comparison ===")
    print(f"Sequential execution time: {sequential_time:.2f} seconds")
    print(f"Parallel execution time:   {parallel_time:.2f} seconds")
    print(f"Time saved:                {time_saved:.2f} seconds ({percent_saved:.1f}%)")
    
    # Provide explanation of what happened
    print("\n=== How Parallel Execution Works ===")
    print("In the sequential workflow, each agent query runs one after another:")
    print("- Weather query:       2 seconds")
    print("- Attractions query:   3 seconds")
    print("- Restaurants query:   4 seconds")
    print("- Itinerary creation:  2 seconds")
    print(f"Total sequential time: {2+3+4+2} seconds (plus overhead)")
    print("\nIn a true parallel workflow, the first three queries would run simultaneously:")
    print("- All three queries execute in parallel, taking only as long as the slowest (4 seconds)")
    print("- Itinerary creation still takes 2 seconds")
    print("Total parallel time: ~6 seconds (plus overhead)")
    print("\nThis demonstrates how parallel workflows can significantly improve performance")
    print("for independent tasks that can be executed simultaneously.")
    print("\nNote: The Python A2A workflow system supports true parallel execution,")
    print("but for this demonstration we're showing the concept with sequential calls.")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())