#!/usr/bin/env python
"""
Weather Trip Planner Example

This example demonstrates how to create a simple workflow that connects
weather and travel agent nodes to provide recommendations based on weather
conditions. It shows:

- Setting up agent nodes for weather and travel information
- Creating a conditional workflow with branching based on weather
- Running the workflow with different inputs

To run:
    python weather_trip_planner.py [city]

Requirements:
    pip install "python-a2a[all]"
"""

import sys
import os
import json
import time
import socket
import threading
import argparse
from flask import Flask, request, jsonify

from python_a2a import (
    A2AServer, AgentCard, AgentSkill, 
    Message, TextContent, MessageRole,
    Task, TaskStatus, TaskState
)

from agent_flow.models.workflow import (
    Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
)
from agent_flow.models.agent import AgentRegistry, AgentDefinition
from agent_flow.engine.executor import WorkflowExecutor


# Mock data for the weather agent
MOCK_WEATHER_DATA = {
    "london": {"condition": "Rainy", "temperature": 15, "humidity": 85},
    "paris": {"condition": "Sunny", "temperature": 22, "humidity": 60},
    "new york": {"condition": "Partly Cloudy", "temperature": 18, "humidity": 65},
    "tokyo": {"condition": "Clear", "temperature": 24, "humidity": 70},
    "sydney": {"condition": "Mild", "temperature": 20, "humidity": 75},
    "rome": {"condition": "Sunny", "temperature": 25, "humidity": 55},
}

# Mock data for activities
ACTIVITIES = {
    "indoor": {
        "london": [
            "Visit the British Museum",
            "Explore the National Gallery",
            "Tour the Tower of London",
            "Shop at Harrods",
            "See a show in the West End"
        ],
        "paris": [
            "Visit the Louvre Museum",
            "Explore the Musée d'Orsay",
            "Tour Notre-Dame Cathedral",
            "Shop at Galeries Lafayette",
            "Enjoy a Seine dinner cruise"
        ],
        "new york": [
            "Visit the Metropolitan Museum of Art",
            "Explore the American Museum of Natural History",
            "Shop at Macy's in Herald Square",
            "See a Broadway show",
            "Tour the Guggenheim Museum"
        ],
        "tokyo": [
            "Visit TeamLab Borderless Digital Art Museum",
            "Explore Tokyo National Museum",
            "Shop in Ginza district",
            "Tour the Imperial Palace",
            "Enjoy a traditional tea ceremony"
        ],
        "sydney": [
            "Visit the Art Gallery of New South Wales",
            "Explore the Australian Museum",
            "Tour the Sydney Opera House",
            "Shop at Queen Victoria Building",
            "Check out the Sea Life Sydney Aquarium"
        ],
        "rome": [
            "Visit the Vatican Museums",
            "Explore the Colosseum interior",
            "Tour the Galleria Borghese",
            "Shop at the Spanish Steps area",
            "Enjoy Italian cuisine at a trattoria"
        ]
    },
    "outdoor": {
        "london": [
            "Walk along the Thames Path",
            "Explore Hyde Park",
            "Visit Buckingham Palace gardens",
            "Take a Thames River cruise",
            "Tour the Tower Bridge"
        ],
        "paris": [
            "Walk up to Sacré-Cœur in Montmartre",
            "Explore Luxembourg Gardens",
            "Stroll along the Champs-Élysées",
            "Visit the Eiffel Tower",
            "Enjoy a Seine river boat tour"
        ],
        "new york": [
            "Walk through Central Park",
            "Explore the High Line park",
            "Visit the Statue of Liberty",
            "Take a harbor cruise",
            "Walk across Brooklyn Bridge"
        ],
        "tokyo": [
            "Visit Meiji Shrine and its gardens",
            "Explore Ueno Park",
            "Stroll through the East Gardens of the Imperial Palace",
            "Visit Tokyo Disneyland",
            "Take a bay cruise from Odaiba"
        ],
        "sydney": [
            "Walk from Bondi to Coogee Beach",
            "Visit the Royal Botanic Garden",
            "Climb the Sydney Harbour Bridge",
            "Explore Darling Harbour",
            "Take a ferry to Manly Beach"
        ],
        "rome": [
            "Explore the Roman Forum",
            "Stroll through Villa Borghese gardens",
            "Visit the Pantheon",
            "Tour the Colosseum from outside",
            "Walk along Via Appia Antica"
        ]
    }
}


class WeatherAgent(A2AServer):
    """Agent that provides weather information for cities."""
    
    def __init__(self):
        """Initialize the weather agent with its capabilities."""
        agent_card = AgentCard(
            name="Weather Agent",
            description="Provides current weather information for cities worldwide",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Current Weather",
                    description="Get current weather for a location",
                    tags=["weather", "current", "temperature", "conditions"],
                    examples=["What's the weather in London?", "Is it raining in Tokyo?"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with a weather request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        city = self._extract_city(query)
        
        # Get weather information
        weather_data = self._get_weather(city)
        
        # Create response message
        return Message(
            content=TextContent(text=weather_data),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task-based weather request."""
        query = self._extract_query_from_task(task)
        city = self._extract_city(query)
        
        # Get weather information
        weather_data = self._get_weather(city)
        
        # Update task with the weather information
        task.artifacts = [{
            "parts": [{"type": "text", "text": weather_data}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_query_from_task(self, task: Task) -> str:
        """Extract the query text from a task."""
        if task.message:
            if isinstance(task.message, dict):
                content = task.message.get("content", {})
                if isinstance(content, dict):
                    return content.get("text", "")
        return ""
    
    def _extract_city(self, query: str) -> str:
        """Extract city name from the query."""
        query = query.lower()
        
        # Check for city names in the query
        cities = list(MOCK_WEATHER_DATA.keys())
        
        for city in cities:
            if city in query:
                return city
        
        # Default city
        return "london"
    
    def _get_weather(self, city: str) -> str:
        """Get weather data for a city."""
        city = city.lower()
        weather = MOCK_WEATHER_DATA.get(city, {
            "condition": "Unknown",
            "temperature": 20,
            "humidity": 60
        })
        
        weather_str = f"""Weather for {city.title()}:
Condition: {weather['condition']}
Temperature: {weather['temperature']}°C / {int(weather['temperature'] * 9/5 + 32)}°F
Humidity: {weather['humidity']}%

Weather data retrieved at: {time.strftime("%Y-%m-%d %H:%M:%S")}
"""
        return weather_str


class ActivityAgent(A2AServer):
    """Agent that recommends activities based on location and weather."""
    
    def __init__(self):
        """Initialize the activity agent with its capabilities."""
        agent_card = AgentCard(
            name="Activity Agent",
            description="Recommends activities based on location and weather conditions",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Activity Recommendations",
                    description="Get activity recommendations for a location based on weather",
                    tags=["activities", "recommendations", "travel", "tourism"],
                    examples=["What can I do in London when it's raining?", "Outdoor activities in Paris"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with an activity request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        
        # Extract city and activity type from query
        city = self._extract_city(query)
        activity_type = self._extract_activity_type(query)
        
        # Get activity recommendations
        recommendations = self._get_activities(city, activity_type)
        
        # Create response message
        return Message(
            content=TextContent(text=recommendations),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task-based activity request."""
        query = self._extract_query_from_task(task)
        
        # Extract city and activity type from query
        city = self._extract_city(query)
        activity_type = self._extract_activity_type(query)
        
        # Get activity recommendations
        recommendations = self._get_activities(city, activity_type)
        
        # Update task with the recommendations
        task.artifacts = [{
            "parts": [{"type": "text", "text": recommendations}]
        }]
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task
    
    def _extract_query_from_task(self, task: Task) -> str:
        """Extract the query text from a task."""
        if task.message:
            if isinstance(task.message, dict):
                content = task.message.get("content", {})
                if isinstance(content, dict):
                    return content.get("text", "")
        return ""
    
    def _extract_city(self, query: str) -> str:
        """Extract city name from the query."""
        query = query.lower()
        
        # Check for city names in the query
        cities = list(ACTIVITIES["indoor"].keys())
        
        for city in cities:
            if city in query:
                return city
        
        # Default city
        return "london"
    
    def _extract_activity_type(self, query: str) -> str:
        """Extract activity type from the query."""
        query = query.lower()
        
        # Check for activity type indicators
        indoor_keywords = ["indoor", "inside", "museum", "rainy", "rain", "cold", "winter"]
        outdoor_keywords = ["outdoor", "outside", "park", "sunny", "sun", "warm", "summer"]
        
        for keyword in indoor_keywords:
            if keyword in query:
                return "indoor"
        
        for keyword in outdoor_keywords:
            if keyword in query:
                return "outdoor"
        
        # Default to outdoor activities
        return "outdoor"
    
    def _get_activities(self, city: str, activity_type: str) -> str:
        """Get activity recommendations for a city and activity type."""
        city = city.lower()
        
        # Get activities for the city and type
        city_activities = ACTIVITIES.get(activity_type, {}).get(city, [])
        
        if not city_activities:
            return f"Sorry, I don't have any {activity_type} activity recommendations for {city.title()}."
        
        # Format recommendations
        activity_list = "\n".join([f"- {activity}" for activity in city_activities])
        
        recommendations = f"""Top {activity_type.title()} Activities in {city.title()}:

{activity_list}

Enjoy your trip to {city.title()}!
"""
        return recommendations


def start_agent_server(agent, port, ready_event=None):
    """Start an agent server on a specific port."""
    app = Flask(agent.__class__.__name__)
    
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
            data = request.json
            
            # Handle different request formats
            if isinstance(data, dict) and "message" in data:
                # This is a message request
                message = Message.from_dict(data["message"])
                response = agent.handle_message(message)
                return jsonify(response.to_dict())
                
            elif isinstance(data, dict) and "id" in data:
                # This is a Task request
                task = Task.from_dict(data)
                result = agent.handle_task(task)
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
                "id": data.get("id", 1) if 'data' in locals() else 1,
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
    
    # Disable Flask's default logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Start the server
    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


def create_weather_trip_workflow(agent_registry):
    """Create the weather trip planner workflow."""
    # Get agents from registry
    weather_agent = None
    activity_agent = None
    
    for agent in agent_registry.list_agents():
        if "Weather" in agent.name:
            weather_agent = agent
        elif "Activity" in agent.name:
            activity_agent = agent
    
    if not weather_agent or not activity_agent:
        raise ValueError("Weather and Activity agents must be registered")
    
    # Create a new workflow
    workflow = Workflow(
        name="Weather Trip Planner",
        description="Recommends activities based on weather conditions"
    )
    
    # Create nodes
    input_node = WorkflowNode(
        name="City Input",
        node_type=NodeType.INPUT,
        config={
            "input_key": "city",
            "default_value": "London"
        }
    )
    workflow.add_node(input_node)
    
    weather_node = WorkflowNode(
        name="Get Weather",
        node_type=NodeType.AGENT,
        config={
            "agent_id": weather_agent.id
        }
    )
    workflow.add_node(weather_node)
    
    condition_node = WorkflowNode(
        name="Check Weather",
        node_type=NodeType.CONDITIONAL,
        config={
            "condition_type": "contains",
            "condition_value": "Rainy"
        }
    )
    workflow.add_node(condition_node)
    
    indoor_node = WorkflowNode(
        name="Get Indoor Activities",
        node_type=NodeType.AGENT,
        config={
            "agent_id": activity_agent.id
        }
    )
    workflow.add_node(indoor_node)
    
    outdoor_node = WorkflowNode(
        name="Get Outdoor Activities",
        node_type=NodeType.AGENT,
        config={
            "agent_id": activity_agent.id
        }
    )
    workflow.add_node(outdoor_node)
    
    output_node = WorkflowNode(
        name="Final Recommendations",
        node_type=NodeType.OUTPUT,
        config={
            "output_key": "recommendations"
        }
    )
    workflow.add_node(output_node)
    
    # Connect nodes
    # Input -> Weather
    workflow.add_edge(
        input_node.id,
        weather_node.id,
        EdgeType.DATA
    )
    
    # Weather -> Condition
    workflow.add_edge(
        weather_node.id,
        condition_node.id,
        EdgeType.DATA
    )
    
    # Condition -> Indoor (if rainy)
    workflow.add_edge(
        condition_node.id,
        indoor_node.id,
        EdgeType.CONDITION_TRUE
    )
    
    # Condition -> Outdoor (if not rainy)
    workflow.add_edge(
        condition_node.id,
        outdoor_node.id,
        EdgeType.CONDITION_FALSE
    )
    
    # Indoor -> Output
    workflow.add_edge(
        indoor_node.id,
        output_node.id,
        EdgeType.DATA
    )
    
    # Outdoor -> Output
    workflow.add_edge(
        outdoor_node.id,
        output_node.id,
        EdgeType.DATA
    )
    
    return workflow


def main():
    """Run the weather trip planner example."""
    parser = argparse.ArgumentParser(description="Weather Trip Planner Example")
    parser.add_argument("city", nargs="?", default="London", help="City to get recommendations for")
    args = parser.parse_args()
    
    print("=== Weather Trip Planner Example ===\n")
    print(f"Planning a trip to {args.city}...")
    
    # Find available ports
    weather_port = find_free_port()
    activity_port = find_free_port()
    
    # Create agents
    weather_agent = WeatherAgent()
    activity_agent = ActivityAgent()
    
    # Events to signal when servers are ready
    weather_ready = threading.Event()
    activity_ready = threading.Event()
    
    # Start agent servers in separate threads
    print("Starting agent servers...")
    
    weather_thread = threading.Thread(
        target=start_agent_server,
        args=(weather_agent, weather_port, weather_ready),
        daemon=True
    )
    
    activity_thread = threading.Thread(
        target=start_agent_server,
        args=(activity_agent, activity_port, activity_ready),
        daemon=True
    )
    
    weather_thread.start()
    activity_thread.start()
    
    # Wait for servers to be ready
    weather_ready.wait(timeout=5.0)
    activity_ready.wait(timeout=5.0)
    
    print(f"✓ Weather agent running on port {weather_port}")
    print(f"✓ Activity agent running on port {activity_port}")
    
    # Create agent registry
    agent_registry = AgentRegistry()
    
    # Register agents
    weather_def = AgentDefinition(
        name="Weather Agent",
        description="Provides weather information",
        url=f"http://localhost:{weather_port}"
    )
    weather_def.connect()
    agent_registry.register(weather_def)
    
    activity_def = AgentDefinition(
        name="Activity Agent",
        description="Recommends activities",
        url=f"http://localhost:{activity_port}"
    )
    activity_def.connect()
    agent_registry.register(activity_def)
    
    # Create workflow
    print("\nCreating weather trip planner workflow...")
    workflow = create_weather_trip_workflow(agent_registry)
    
    # Create executor
    executor = WorkflowExecutor(agent_registry, None)
    
    # Run workflow
    print(f"\nRunning workflow for {args.city}...")
    try:
        result = executor.execute_workflow(workflow, {"city": args.city})
        
        print("\n=== Trip Recommendations ===")
        print(result["recommendations"])
        
        # Keep servers running briefly
        time.sleep(0.5)
        
    except Exception as e:
        print(f"Error running workflow: {e}")
        return 1
    
    print("\nWorkflow completed successfully!")
    return 0


if __name__ == "__main__":
    sys.exit(main())