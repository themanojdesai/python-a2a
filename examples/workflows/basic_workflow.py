#!/usr/bin/env python
"""
Basic Workflow Example

This example demonstrates the core features of the A2A workflow system:
- Creating agent network with self-contained agents
- Building a workflow with conditional branching
- Executing the workflow to get results automatically

The example is completely self-contained and runs all necessary
components locally, with no external dependencies.

To run:
    python basic_workflow.py [city]

Requirements:
    pip install "python-a2a[all]"
"""

import sys
import threading
import time
import socket
import json
from flask import Flask, request, jsonify

from python_a2a import (
    A2AServer, AgentCard, AgentSkill, 
    Flow, AgentNetwork,
    Task, TaskStatus, TaskState,
    Message, TextContent, MessageRole
)


class WeatherAgent(A2AServer):
    """A simulated weather agent."""
    
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
        """Handle a direct message (for compatibility with older clients)."""
        # Extract the query from the message
        query = ""
        if hasattr(message.content, "text"):
            query = message.content.text
        
        # Extract city from query
        city = self._extract_city(query)
        
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
        """Handle a weather query task."""
        # Extract query from task
        query = self._extract_query(task)
        city = self._extract_city(query)
        
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


class ActivitiesAgent(A2AServer):
    """A simulated activities recommendation agent."""
    
    def __init__(self):
        """Initialize with a basic agent card for identification."""
        agent_card = AgentCard(
            name="Activities Agent",
            description="Recommends activities based on location and weather",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Activity Recommendations",
                    description="Get activity recommendations for a location",
                    tags=["activities", "travel", "recommendations"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message):
        """Handle a direct message (for compatibility with older clients)."""
        # Extract the query from the message
        query = ""
        if hasattr(message.content, "text"):
            query = message.content.text
        
        # Extract information from query
        city = self._extract_city(query)
        weather_type = self._extract_weather_type(query)
        
        # Get recommendations
        recommendations = self._get_recommendations(city, weather_type)
        
        # Create response message
        response = Message(
            content=TextContent(text=recommendations),
            role=MessageRole.AGENT,
            message_id=f"response-{time.time()}",
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
        
        return response
    
    def handle_task(self, task):
        """Handle a task by providing activity recommendations."""
        # Extract query from task
        query = self._extract_query(task)
        city = self._extract_city(query)
        weather_type = self._extract_weather_type(query)
        
        # Generate recommendations based on city and weather
        recommendations = self._get_recommendations(city, weather_type)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": recommendations}]
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
    
    def _extract_weather_type(self, query):
        """Extract weather type from the query."""
        query = query.lower()
        
        if "rain" in query or "rainy" in query:
            return "rainy"
        elif "sun" in query or "sunny" in query:
            return "sunny"
        elif "cloudy" in query:
            return "cloudy"
        
        # Default weather
        return "unknown"
    
    def _get_recommendations(self, city, weather_type):
        """Get activity recommendations based on city and weather."""
        # Indoor activities for rainy weather
        if weather_type == "rainy":
            recommendations = {
                "london": """Indoor activities in London:
1. British Museum
2. National Gallery
3. Tate Modern
4. Natural History Museum
5. Visit Harrods department store""",
                "paris": """Indoor activities in Paris:
1. The Louvre Museum
2. Musée d'Orsay
3. Centre Pompidou
4. Galeries Lafayette shopping
5. Seine river dinner cruise""",
                "new york": """Indoor activities in New York:
1. Metropolitan Museum of Art
2. American Museum of Natural History
3. MoMA (Museum of Modern Art)
4. Shopping at Hudson Yards
5. Broadway show""",
                "tokyo": """Indoor activities in Tokyo:
1. TeamLab Borderless digital art museum
2. Tokyo National Museum
3. Shopping in Ginza
4. Visit a traditional tea house
5. Try indoor cooking class""",
                "sydney": """Indoor activities in Sydney:
1. Art Gallery of New South Wales
2. Australian Museum
3. Sydney Opera House tour
4. Shopping at Queen Victoria Building
5. Sydney Aquarium"""
            }
        # Outdoor activities for good weather
        else:
            recommendations = {
                "london": """Outdoor activities in London:
1. Walk along the Thames
2. Visit Hyde Park
3. Explore Camden Market
4. Take a Thames river cruise
5. Visit the Tower of London""",
                "paris": """Outdoor activities in Paris:
1. Walk up to Sacré-Cœur in Montmartre
2. Picnic in Luxembourg Gardens
3. Explore the Latin Quarter
4. Walk along the Seine
5. Visit the Eiffel Tower""",
                "new york": """Outdoor activities in New York:
1. Walk through Central Park
2. Visit the High Line
3. Walk across Brooklyn Bridge
4. Explore Greenwich Village
5. Take a ferry to the Statue of Liberty""",
                "tokyo": """Outdoor activities in Tokyo:
1. Visit Meiji Shrine
2. Explore Shinjuku Gyoen National Garden
3. Walk around Tsukiji Outer Market
4. See cherry blossoms (seasonal) at Ueno Park
5. Boat ride in Imperial Palace moat""",
                "sydney": """Outdoor activities in Sydney:
1. Walk from Bondi to Coogee
2. Climb Sydney Harbour Bridge
3. Royal Botanic Garden
4. Taronga Zoo
5. Explore Darling Harbour"""
            }
        
        return recommendations.get(city, f"Activity recommendations not available for {city}.")


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


def main():
    """Run the basic workflow example."""
    print("=== Basic Workflow Example ===\n")
    
    # Get the city from command line arguments, or use default
    city = "London"
    if len(sys.argv) > 1:
        city = sys.argv[1]
    
    print(f"Planning activities for {city} based on weather conditions...\n")
    
    # Find available ports
    weather_port = find_free_port()
    activities_port = find_free_port()
    
    # Create agents
    weather_agent = WeatherAgent()
    activities_agent = ActivitiesAgent()
    
    # Events to signal when servers are ready
    weather_ready = threading.Event()
    activities_ready = threading.Event()
    
    # Start agent servers in separate threads
    weather_thread = threading.Thread(
        target=start_agent_server,
        args=(weather_agent, weather_port, weather_ready),
        daemon=True
    )
    
    activities_thread = threading.Thread(
        target=start_agent_server,
        args=(activities_agent, activities_port, activities_ready),
        daemon=True
    )
    
    print("Starting agent servers...")
    weather_thread.start()
    activities_thread.start()
    
    # Wait for servers to be ready
    weather_ready.wait(timeout=5.0)
    activities_ready.wait(timeout=5.0)
    
    print(f"✓ Weather agent running on port {weather_port}")
    print(f"✓ Activities agent running on port {activities_port}")
    
    # Create agent network
    network = AgentNetwork()
    network.add("weather", f"http://localhost:{weather_port}")
    network.add("activities", f"http://localhost:{activities_port}")
    
    print("\nCreating workflow:")
    print("1. Query the weather agent for current conditions")
    print("2. Based on weather, ask for appropriate activities")
    print("3. Return the final recommendations\n")
    
    # Create workflow
    flow = (
        Flow(agent_network=network)
        # First, check the weather in the city
        .ask("weather", f"What's the weather like in {city}?")
        
        # Branch based on weather conditions
        .if_contains("rain")
        # If rainy, get indoor activities
        .ask("activities", f"Recommend indoor activities in {city}")
        .else_branch()
        # Otherwise, get outdoor activities
        .ask("activities", f"Recommend outdoor activities in {city}")
        .end_if()
    )
    
    # Run the workflow
    print("Executing workflow...\n")
    try:
        result = flow.run_sync()
        
        print("=== Workflow Result ===")
        print(result)
        print("\nWorkflow completed successfully!")
        
        # Keep servers running briefly so the user can see the result
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error running workflow: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())