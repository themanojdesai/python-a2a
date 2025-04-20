#!/usr/bin/env python
"""
Basic Agent Network Example

This example demonstrates the fundamentals of creating and using an agent network
for coordinating multiple specialized agents. It shows how to:
- Create specialized agents (weather, math, and knowledge)
- Set up an agent network that connects these agents
- Query specific agents for different types of tasks 
- List available agents and their capabilities
- Save and load network configurations

To run:
    python agent_network.py [command] [args]

Available commands:
    list                List all agents in the network
    query weather CITY  Get weather for a city
    query math EXPR     Calculate a math expression
    query knowledge Q   Ask a knowledge question
    save FILE           Save network to a file
    load FILE           Load network from a file
    
Requirements:
    pip install "python-a2a[all]"
"""

import argparse
import json
import logging
import os
import signal
import socket
import sys
import threading
import time
from typing import Dict, List, Optional, Union

from python_a2a import (
    A2AServer, AgentCard, AgentSkill,
    AgentNetwork, Message, TextContent, MessageRole,
    Task, TaskStatus, TaskState
)
from flask import Flask, request, jsonify

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentNetwork")


class WeatherAgent(A2AServer):
    """Agent that provides weather information for cities."""
    
    def __init__(self):
        """Initialize the weather agent with its capabilities."""
        agent_card = AgentCard(
            name="Weather Agent",
            description="Provides current weather and forecasts for cities worldwide",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Current Weather",
                    description="Get current weather for a location",
                    tags=["weather", "current", "temperature", "conditions"],
                    examples=["What's the weather in London?", "Is it raining in Tokyo?"]
                ),
                AgentSkill(
                    name="Weather Forecast",
                    description="Get weather forecast for next few days",
                    tags=["weather", "forecast", "prediction"],
                    examples=["Forecast for Paris this week", "Will it rain in New York tomorrow?"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with a weather request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        city = self._extract_city(query)
        
        # Add a small delay to simulate processing
        logger.info(f"[Weather Agent] Processing weather request for {city}...")
        time.sleep(1.5)  # Simulate API call delay
        
        if "forecast" in query.lower():
            weather_data = self._get_forecast(city)
        else:
            weather_data = self._get_current_weather(city)
        
        logger.info(f"[Weather Agent] Completed processing for {city}")
        
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
        
        # Add a small delay to simulate processing
        logger.info(f"[Weather Agent] Processing weather request for {city}...")
        time.sleep(1.5)  # Simulate API call delay
        
        if "forecast" in query.lower():
            weather_data = self._get_forecast(city)
        else:
            weather_data = self._get_current_weather(city)
        
        logger.info(f"[Weather Agent] Completed processing for {city}")
        
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
        cities = ["london", "paris", "new york", "tokyo", "sydney", 
                 "berlin", "rome", "madrid", "cairo", "mumbai"]
        
        for city in cities:
            if city in query:
                return city.title()
        
        # Default city if none found
        return "London"
    
    def _get_current_weather(self, city: str) -> str:
        """Get current weather for a city (simulated data)."""
        weather_data = {
            "London": {
                "condition": "Rainy",
                "temperature": "15°C (59°F)",
                "humidity": "85%",
                "wind": "18 km/h"
            },
            "Paris": {
                "condition": "Sunny",
                "temperature": "22°C (72°F)",
                "humidity": "60%",
                "wind": "10 km/h"
            },
            "New York": {
                "condition": "Partly Cloudy",
                "temperature": "18°C (64°F)",
                "humidity": "65%",
                "wind": "15 km/h"
            },
            "Tokyo": {
                "condition": "Clear",
                "temperature": "24°C (75°F)",
                "humidity": "70%",
                "wind": "8 km/h"
            },
            "Sydney": {
                "condition": "Mild",
                "temperature": "20°C (68°F)",
                "humidity": "75%",
                "wind": "12 km/h"
            },
            "Berlin": {
                "condition": "Overcast",
                "temperature": "17°C (63°F)",
                "humidity": "78%",
                "wind": "14 km/h"
            },
            "Rome": {
                "condition": "Sunny",
                "temperature": "25°C (77°F)",
                "humidity": "55%",
                "wind": "9 km/h"
            },
            "Madrid": {
                "condition": "Hot",
                "temperature": "28°C (82°F)",
                "humidity": "45%",
                "wind": "7 km/h"
            },
            "Cairo": {
                "condition": "Hot and Dry",
                "temperature": "33°C (91°F)",
                "humidity": "30%",
                "wind": "15 km/h"
            },
            "Mumbai": {
                "condition": "Humid",
                "temperature": "29°C (84°F)",
                "humidity": "88%",
                "wind": "11 km/h"
            }
        }
        
        city_data = weather_data.get(city, {"condition": "Unknown", "temperature": "N/A", "humidity": "N/A", "wind": "N/A"})
        
        return f"""Current Weather in {city}:
Condition: {city_data['condition']}
Temperature: {city_data['temperature']}
Humidity: {city_data['humidity']}
Wind Speed: {city_data['wind']}

Weather data last updated: {time.strftime("%Y-%m-%d %H:%M:%S")}"""
    
    def _get_forecast(self, city: str) -> str:
        """Get a 3-day forecast for a city (simulated data)."""
        # Generate some simulated forecast data
        forecasts = {
            "London": [
                {"day": "Today", "condition": "Rainy", "high": "15°C", "low": "10°C"},
                {"day": "Tomorrow", "condition": "Cloudy", "high": "17°C", "low": "12°C"},
                {"day": "Day 3", "condition": "Partly Cloudy", "high": "18°C", "low": "11°C"}
            ],
            "Paris": [
                {"day": "Today", "condition": "Sunny", "high": "22°C", "low": "14°C"},
                {"day": "Tomorrow", "condition": "Clear", "high": "24°C", "low": "16°C"},
                {"day": "Day 3", "condition": "Partly Cloudy", "high": "21°C", "low": "15°C"}
            ],
            "New York": [
                {"day": "Today", "condition": "Partly Cloudy", "high": "18°C", "low": "12°C"},
                {"day": "Tomorrow", "condition": "Sunny", "high": "20°C", "low": "13°C"},
                {"day": "Day 3", "condition": "Clear", "high": "22°C", "low": "14°C"}
            ],
            "Tokyo": [
                {"day": "Today", "condition": "Clear", "high": "24°C", "low": "18°C"},
                {"day": "Tomorrow", "condition": "Sunny", "high": "26°C", "low": "19°C"},
                {"day": "Day 3", "condition": "Partly Cloudy", "high": "25°C", "low": "18°C"}
            ],
            "Sydney": [
                {"day": "Today", "condition": "Mild", "high": "20°C", "low": "15°C"},
                {"day": "Tomorrow", "condition": "Sunny", "high": "22°C", "low": "16°C"},
                {"day": "Day 3", "condition": "Clear", "high": "23°C", "low": "17°C"}
            ]
        }
        
        # Use default forecast if city not found
        city_forecast = forecasts.get(city, [
            {"day": "Today", "condition": "Unknown", "high": "N/A", "low": "N/A"},
            {"day": "Tomorrow", "condition": "Unknown", "high": "N/A", "low": "N/A"},
            {"day": "Day 3", "condition": "Unknown", "high": "N/A", "low": "N/A"}
        ])
        
        # Format the forecast as text
        result = f"3-Day Weather Forecast for {city}:\n\n"
        for day in city_forecast:
            result += f"{day['day']}: {day['condition']}, High: {day['high']}, Low: {day['low']}\n"
        
        result += f"\nForecast generated on: {time.strftime('%Y-%m-%d %H:%M:%S')}"
        return result


class MathAgent(A2AServer):
    """Agent that performs mathematical calculations."""
    
    def __init__(self):
        """Initialize the math agent with its capabilities."""
        agent_card = AgentCard(
            name="Math Agent",
            description="Performs mathematical calculations and unit conversions",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Basic Arithmetic",
                    description="Perform basic arithmetic operations (+, -, *, /)",
                    tags=["math", "arithmetic", "calculate", "computation"],
                    examples=["Calculate 125 * 37", "What is 523 + 982?"]
                ),
                AgentSkill(
                    name="Unit Conversion",
                    description="Convert between different units of measurement",
                    tags=["conversion", "units", "metric", "imperial"],
                    examples=["Convert 5 kg to pounds", "How many meters in 3 miles?"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with a math request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        
        # Add a small delay to simulate processing
        logger.info("[Math Agent] Processing calculation request...")
        time.sleep(0.5)  # Math calculations are usually quick
        
        if self._is_conversion_query(query):
            result = self._handle_conversion(query)
        else:
            result = self._handle_calculation(query)
        
        logger.info("[Math Agent] Calculation completed")
        
        return Message(
            content=TextContent(text=result),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task-based math request."""
        query = self._extract_query_from_task(task)
        
        # Add a small delay to simulate processing
        logger.info("[Math Agent] Processing calculation request...")
        time.sleep(0.5)  # Math calculations are usually quick
        
        if self._is_conversion_query(query):
            result = self._handle_conversion(query)
        else:
            result = self._handle_calculation(query)
        
        logger.info("[Math Agent] Calculation completed")
        
        # Update task with the calculation result
        task.artifacts = [{
            "parts": [{"type": "text", "text": result}]
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
    
    def _is_conversion_query(self, query: str) -> bool:
        """Check if the query is about unit conversion."""
        conversion_keywords = ["convert", "conversion", "how many", "units"]
        query_lower = query.lower()
        
        # Check for conversion keywords
        if any(keyword in query_lower for keyword in conversion_keywords):
            # Check for unit mentions
            units = ["kg", "pounds", "meters", "feet", "celsius", "fahrenheit", 
                    "liters", "gallons", "kilometers", "miles"]
            return any(unit in query_lower for unit in units)
        
        return False
    
    def _handle_calculation(self, query: str) -> str:
        """Process a calculation query."""
        # Extract the math expression from the query
        import re
        
        # Try to find a mathematical expression in the query
        expression = None
        
        # Look for patterns like "calculate X" or "what is X"
        calculate_match = re.search(r"calculate\s+(.+)", query, re.IGNORECASE)
        what_is_match = re.search(r"what\s+is\s+(.+)", query, re.IGNORECASE)
        
        if calculate_match:
            expression = calculate_match.group(1)
        elif what_is_match:
            expression = what_is_match.group(1)
        else:
            # Just try to extract an expression with numbers and operators
            exp_match = re.search(r"([\d\s\+\-\*\/\(\)\.\%]+)", query)
            if exp_match:
                expression = exp_match.group(1)
        
        if not expression:
            return "I couldn't find a mathematical expression to calculate. Please try again with a clearer expression."
        
        # Remove any trailing punctuation
        expression = expression.rstrip("?.,;:")
        
        # Evaluate the expression
        try:
            # Replace 'x' with '*' for multiplication
            expression = expression.replace("x", "*")
            
            # Safely evaluate the expression
            result = eval(expression)
            
            # Format the result
            if isinstance(result, int) or result.is_integer():
                return f"The result of {expression} is {int(result)}"
            else:
                return f"The result of {expression} is {result:.6f}"
                
        except Exception as e:
            return f"I couldn't calculate '{expression}'. Error: {str(e)}"
    
    def _handle_conversion(self, query: str) -> str:
        """Process a unit conversion query."""
        query_lower = query.lower()
        
        # Define conversion rates
        conversions = {
            ("kg", "pounds"): 2.20462,
            ("pounds", "kg"): 0.453592,
            ("meters", "feet"): 3.28084,
            ("feet", "meters"): 0.3048,
            ("kilometers", "miles"): 0.621371,
            ("miles", "kilometers"): 1.60934,
            ("liters", "gallons"): 0.264172,
            ("gallons", "liters"): 3.78541,
            ("celsius", "fahrenheit"): lambda c: c * 9/5 + 32,
            ("fahrenheit", "celsius"): lambda f: (f - 32) * 5/9
        }
        
        # Extract amount and units
        import re
        
        # Look for patterns like "X unit1 to unit2" or "convert X unit1 to unit2"
        conversion_pattern = r"(?:convert\s+)?(\d+(?:\.\d+)?)\s+(\w+)(?:\s+to\s+|\s+in\s+)(\w+)"
        match = re.search(conversion_pattern, query_lower)
        
        if not match:
            return "I couldn't understand the conversion request. Please use a format like 'convert 5 kg to pounds' or '10 miles in kilometers'."
        
        amount_str, from_unit, to_unit = match.groups()
        try:
            amount = float(amount_str)
        except ValueError:
            return f"I couldn't parse '{amount_str}' as a number."
        
        # Normalize units (remove plurals)
        from_unit = from_unit.rstrip("s")
        to_unit = to_unit.rstrip("s")
        
        # Find the conversion factor
        conversion_key = (from_unit, to_unit)
        if conversion_key in conversions:
            conversion_factor = conversions[conversion_key]
            
            # Apply the conversion
            if callable(conversion_factor):
                result = conversion_factor(amount)
                
                # Special formatting for temperature
                if from_unit in ["celsius", "fahrenheit"]:
                    from_symbol = "°C" if from_unit == "celsius" else "°F"
                    to_symbol = "°F" if to_unit == "fahrenheit" else "°C"
                    return f"{amount}{from_symbol} is equal to {result:.2f}{to_symbol}"
            else:
                result = amount * conversion_factor
            
            # Determine if we should display integer result
            if result.is_integer():
                return f"{amount} {from_unit} is equal to {int(result)} {to_unit}"
            else:
                return f"{amount} {from_unit} is equal to {result:.4f} {to_unit}"
        else:
            return f"I don't know how to convert from {from_unit} to {to_unit}."


class KnowledgeAgent(A2AServer):
    """Agent that answers general knowledge questions."""
    
    def __init__(self):
        """Initialize the knowledge agent with its capabilities."""
        agent_card = AgentCard(
            name="Knowledge Agent",
            description="Answers general knowledge questions and provides factual information",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="General Questions",
                    description="Answer common knowledge questions",
                    tags=["knowledge", "facts", "information", "questions", "general"],
                    examples=["What is the capital of France?", "Who invented the telephone?"]
                ),
                AgentSkill(
                    name="Definitions",
                    description="Provide definitions for terms and concepts",
                    tags=["definition", "meaning", "concept", "define"],
                    examples=["What is photosynthesis?", "Define artificial intelligence"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with a knowledge request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        
        # Add a delay to simulate thinking/database lookup
        logger.info("[Knowledge Agent] Researching answer...")
        time.sleep(2)  # Knowledge lookups take more time
        
        answer = self._answer_question(query)
        
        logger.info("[Knowledge Agent] Answer found")
        
        return Message(
            content=TextContent(text=answer),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task-based knowledge request."""
        query = self._extract_query_from_task(task)
        
        # Add a delay to simulate thinking/database lookup
        logger.info("[Knowledge Agent] Researching answer...")
        time.sleep(2)  # Knowledge lookups take more time
        
        answer = self._answer_question(query)
        
        logger.info("[Knowledge Agent] Answer found")
        
        # Update task with the answer
        task.artifacts = [{
            "parts": [{"type": "text", "text": answer}]
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
    
    def _answer_question(self, query: str) -> str:
        """Answer a knowledge question (simulated knowledge base)."""
        query_lower = query.lower()
        
        # Simple knowledge base
        knowledge_base = {
            "capital of france": "The capital of France is Paris.",
            
            "capital of japan": "The capital of Japan is Tokyo.",
            
            "capital of australia": "The capital of Australia is Canberra, not Sydney as many people believe.",
            
            "telephone inventor": """The telephone was invented by Alexander Graham Bell. He patented the first practical telephone in 1876.
Though there is some historical debate, Bell is generally credited with the invention.""",
            
            "photosynthesis": """Photosynthesis is the process by which green plants, algae, and some bacteria convert light energy, 
usually from the sun, into chemical energy in the form of glucose or other sugars. The process primarily happens in the 
chloroplasts of plant cells, specifically using the green pigment chlorophyll.""",
            
            "artificial intelligence": """Artificial Intelligence (AI) refers to the simulation of human intelligence in machines 
that are programmed to think and learn like humans. It encompasses various technologies including machine learning, 
natural language processing, computer vision, and robotics.""",
            
            "mount everest height": "Mount Everest is the Earth's highest mountain above sea level, with a peak at 8,848.86 meters (29,031.7 feet) above sea level.",
            
            "water boiling point": "Water boils at 100 degrees Celsius (212 degrees Fahrenheit) at standard atmospheric pressure (1 atmosphere).",
            
            "python programming": """Python is a high-level, interpreted programming language known for its readability and simplicity.
It was created by Guido van Rossum and first released in 1991. Python supports multiple programming paradigms and has a comprehensive standard library.""",
            
            "solar system planets": """The eight planets of our solar system in order from the Sun are:
1. Mercury
2. Venus
3. Earth
4. Mars
5. Jupiter
6. Saturn
7. Uranus
8. Neptune
Pluto was reclassified as a dwarf planet in 2006."""
        }
        
        # Check for keywords in the query
        for key, answer in knowledge_base.items():
            if key in query_lower:
                return answer
        
        # Check if it's a definition request
        if "what is" in query_lower or "define" in query_lower or "meaning of" in query_lower:
            for key, answer in knowledge_base.items():
                # Extract potential term being defined
                import re
                match = re.search(r"what is ([\w\s]+)", query_lower)
                if match:
                    term = match.group(1).strip()
                    if term in key:
                        return answer
                
                match = re.search(r"define ([\w\s]+)", query_lower)
                if match:
                    term = match.group(1).strip()
                    if term in key:
                        return answer
        
        # If no specific answer found
        return """I don't have a specific answer for that question in my knowledge base. 
My capabilities are limited to a small set of pre-defined responses. 
For more comprehensive answers, please consider using a search engine or a more advanced AI assistant."""


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
            if isinstance(data, dict) and "messages" in data:
                # This is a conversation, extract the last message
                messages = data["messages"]
                if messages:
                    last_message = Message.from_dict(messages[-1])
                    response = agent.handle_message(last_message)
                    
                    # Update the conversation with the response
                    messages.append(response.to_dict())
                    return jsonify(data)
                    
            elif isinstance(data, dict) and "message" in data:
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
            logger.error(f"Error processing request: {e}")
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
            logger.error(f"Error processing task: {e}")
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


def save_network_to_file(network, filepath):
    """Save network configuration to a file."""
    try:
        # Create a serializable representation of the network
        network_data = {
            "name": network.name,
            "id": network._id,
            "agents": []
        }
        
        # Add information about each agent
        for name, agent in network.agents.items():
            agent_info = {
                "name": name,
                "url": network.agent_urls.get(name, "")
            }
            
            # Add agent card if available
            card = network.agent_cards.get(name)
            if card:
                agent_info["card"] = {
                    "name": card.name,
                    "description": card.description,
                    "version": card.version,
                    "skills_count": len(getattr(card, 'skills', []))
                }
            
            network_data["agents"].append(agent_info)
        
        # Write to file
        with open(filepath, 'w') as f:
            json.dump(network_data, f, indent=2)
        
        return True
    
    except Exception as e:
        logger.error(f"Error saving network to file: {e}")
        return False


def load_network_from_file(filepath):
    """Load network configuration from a file."""
    try:
        # Read network data from file
        with open(filepath, 'r') as f:
            network_data = json.load(f)
        
        # Create new network with saved name
        network = AgentNetwork(name=network_data.get("name", "Loaded Network"))
        
        # Connect to agents from saved URLs
        for agent_info in network_data.get("agents", []):
            name = agent_info.get("name")
            url = agent_info.get("url")
            
            if name and url:
                logger.info(f"Connecting to agent {name} at {url}")
                network.add(name, url)
        
        return network
    
    except Exception as e:
        logger.error(f"Error loading network from file: {e}")
        return None


def list_agents(network):
    """Display information about all agents in the network."""
    agents_info = network.list_agents()
    
    print(f"\n=== Agents in Network: {network.name} ===")
    print(f"Total agents: {len(agents_info)}")
    
    for i, agent in enumerate(agents_info, 1):
        print(f"\n{i}. {agent['name']}")
        print(f"   URL: {agent['url']}")
        
        if "description" in agent:
            print(f"   Description: {agent['description']}")
        
        if "skills_count" in agent:
            print(f"   Skills: {agent['skills_count']}")
        
        # Show specific capabilities for known agent types
        if "weather" in agent["name"].lower():
            print("   Specialization: Weather information and forecasts")
        elif "math" in agent["name"].lower():
            print("   Specialization: Mathematical calculations and conversions")
        elif "knowledge" in agent["name"].lower():
            print("   Specialization: General knowledge and facts")


def query_agent(network, agent_name, query):
    """Send a query to a specific agent in the network."""
    print(f"\nQuerying {agent_name} with: {query}")
    
    agent = network.get_agent(agent_name)
    if not agent:
        print(f"Error: Agent '{agent_name}' not found in the network")
        return
    
    try:
        print("Sending query...")
        start_time = time.time()
        
        # Send the query to the agent
        response = agent.ask(query)
        
        duration = time.time() - start_time
        
        print(f"\n=== Response from {agent_name} (in {duration:.2f}s) ===")
        print(response)
    
    except Exception as e:
        print(f"Error querying agent: {e}")


def main():
    """Run the agent network example."""
    parser = argparse.ArgumentParser(description="Agent Network Example")
    parser.add_argument('command', nargs='?', default='list',
                       choices=['list', 'query', 'save', 'load'],
                       help='Command to execute')
    parser.add_argument('agent', nargs='?', help='Agent to query (weather, math, knowledge)')
    parser.add_argument('args', nargs='*', help='Additional arguments for the command')
    
    args = parser.parse_args()
    
    print("=== Agent Network Example ===")
    print("Setting up the agent network...\n")
    
    # Create agents
    weather_agent = WeatherAgent()
    math_agent = MathAgent()
    knowledge_agent = KnowledgeAgent()
    
    # Find available ports
    weather_port = find_free_port()
    math_port = find_free_port()
    knowledge_port = find_free_port()
    
    # Events to signal when servers are ready
    weather_ready = threading.Event()
    math_ready = threading.Event()
    knowledge_ready = threading.Event()
    
    # Start agent servers in separate threads
    print("Starting agent servers...")
    
    weather_thread = threading.Thread(
        target=start_agent_server,
        args=(weather_agent, weather_port, weather_ready),
        daemon=True
    )
    
    math_thread = threading.Thread(
        target=start_agent_server,
        args=(math_agent, math_port, math_ready),
        daemon=True
    )
    
    knowledge_thread = threading.Thread(
        target=start_agent_server,
        args=(knowledge_agent, knowledge_port, knowledge_ready),
        daemon=True
    )
    
    weather_thread.start()
    math_thread.start()
    knowledge_thread.start()
    
    # Wait for servers to be ready
    weather_ready.wait(timeout=5.0)
    math_ready.wait(timeout=5.0)
    knowledge_ready.wait(timeout=5.0)
    
    print(f"✓ Weather agent running on port {weather_port}")
    print(f"✓ Math agent running on port {math_port}")
    print(f"✓ Knowledge agent running on port {knowledge_port}")
    
    # Create an agent network
    network = AgentNetwork(name="Basic Agent Network")
    
    # Add agents to the network
    print("\nAdding agents to the network...")
    
    # Add by URL for remote agents
    weather_url = f"http://localhost:{weather_port}"
    math_url = f"http://localhost:{math_port}"
    knowledge_url = f"http://localhost:{knowledge_port}"
    
    network.add("weather", weather_url)
    print(f"✓ Added weather agent")
    
    network.add("math", math_url)
    print(f"✓ Added math agent")
    
    network.add("knowledge", knowledge_url)
    print(f"✓ Added knowledge agent")
    
    # Process the command
    if args.command == 'list':
        # List all agents in the network
        list_agents(network)
        
    elif args.command == 'query':
        # Query a specific agent
        if not args.agent:
            print("Error: Must specify an agent to query (weather, math, knowledge)")
            return 1
            
        query_text = ' '.join(args.args)
        if not query_text:
            if args.agent == 'weather':
                query_text = "What's the weather in London?"
            elif args.agent == 'math':
                query_text = "Calculate 123 + 456"
            elif args.agent == 'knowledge':
                query_text = "What is photosynthesis?"
            else:
                print(f"Error: Unknown agent '{args.agent}'")
                return 1
        
        query_agent(network, args.agent, query_text)
        
    elif args.command == 'save':
        # Save network configuration to a file
        if not args.args:
            filepath = "network_config.json"
        else:
            filepath = args.args[0]
        
        print(f"\nSaving network configuration to {filepath}...")
        if save_network_to_file(network, filepath):
            print(f"✓ Network configuration saved successfully")
        else:
            print("× Failed to save network configuration")
            return 1
    
    elif args.command == 'load':
        # Load network configuration from a file
        if not args.args:
            print("Error: Must specify a file to load network from")
            return 1
        
        filepath = args.args[0]
        
        print(f"\nLoading network configuration from {filepath}...")
        loaded_network = load_network_from_file(filepath)
        
        if loaded_network:
            print(f"✓ Network loaded successfully")
            # Display the loaded network
            list_agents(loaded_network)
        else:
            print("× Failed to load network configuration")
            return 1
    
    print("\nNetwork operations completed successfully")
    return 0


if __name__ == "__main__":
    # Catch Ctrl+C to exit gracefully
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nExiting agent network example...")
        sys.exit(0)