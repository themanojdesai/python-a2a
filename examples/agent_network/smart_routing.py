#!/usr/bin/env python
"""
Intelligent Query Routing Example

This example demonstrates how to use the AIAgentRouter to intelligently route
queries to the most appropriate agent based on query content. It shows:
- Creating specialized agents with different capabilities
- Setting up an AI router using OpenAI to analyze and route queries
- Comparing intelligent routing with baseline methods
- Evaluating routing decisions and accuracy

To run:
    python smart_routing.py [--router-type TYPE] [--query QUERY]

Options:
    --router-type   Type of router (ai, keyword, random) [default: ai]
    --query         Query to test with routing [default: predefined test queries]
    --model         OpenAI model to use [default: gpt-3.5-turbo]
    --compare       Compare all routers side by side [default: false]
    --openai-key    OpenAI API key (or set OPENAI_API_KEY environment variable)

Requirements:
    pip install "python-a2a[all,openai]"
"""

import argparse
import json
import logging
import os
import random
import signal
import socket
import sys
import threading
import time
from typing import Dict, List, Optional, Union, Callable
import re
from flask import Flask, request, jsonify

from python_a2a import (
    A2AServer, AgentCard, AgentSkill, 
    AgentNetwork, Message, TextContent, MessageRole,
    Task, TaskStatus, TaskState
)

# Import OpenAI integrations with proper error handling
try:
    from python_a2a.client.router import AIAgentRouter
    from python_a2a.server.llm import OpenAIA2AServer
    from python_a2a.client.llm import OpenAIA2AClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SmartRouting")

# Global dictionary to track running agents
running_agents = {}


class WeatherAgent(A2AServer):
    """Agent that provides weather information."""
    
    def __init__(self):
        """Initialize the weather agent with its capabilities."""
        agent_card = AgentCard(
            name="Weather Agent",
            description="Provides current weather information and forecasts for locations worldwide",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Current Weather",
                    description="Get current weather conditions for a location",
                    tags=["weather", "current", "temperature", "conditions", "forecast"],
                    examples=["What's the weather in London?", "Is it raining in Tokyo?"]
                ),
                AgentSkill(
                    name="Weather Forecast",
                    description="Get weather forecast for the coming days",
                    tags=["weather", "forecast", "prediction", "upcoming", "future"],
                    examples=["What's the forecast for Paris?", "Will it rain in New York tomorrow?"]
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
        time.sleep(0.5)
        
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
        time.sleep(0.5)
        
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
            }
        }
        
        city_data = weather_data.get(city, {"condition": "Unknown", "temperature": "N/A", "humidity": "N/A", "wind": "N/A"})
        
        return f"""Current Weather in {city}:
Condition: {city_data['condition']}
Temperature: {city_data['temperature']}
Humidity: {city_data['humidity']}
Wind Speed: {city_data['wind']}"""
    
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
        
        return result


class MathAgent(A2AServer):
    """Agent that performs mathematical calculations."""
    
    def __init__(self):
        """Initialize the math agent with its capabilities."""
        agent_card = AgentCard(
            name="Math Agent",
            description="Performs mathematical calculations, conversions, and solves math problems",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Basic Arithmetic",
                    description="Perform basic arithmetic operations like addition, subtraction, multiplication, and division",
                    tags=["math", "arithmetic", "calculate", "computation"],
                    examples=["Calculate 125 * 37", "What is 523 + 982?"]
                ),
                AgentSkill(
                    name="Unit Conversion",
                    description="Convert between different units of measurement (metric, imperial)",
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
        time.sleep(0.3)
        
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
        time.sleep(0.3)
        
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


class TravelAgent(A2AServer):
    """Agent that provides travel recommendations and information."""
    
    def __init__(self):
        """Initialize the travel agent with its capabilities."""
        agent_card = AgentCard(
            name="Travel Agent",
            description="Provides travel recommendations, information about destinations, and trip planning advice",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Destination Information",
                    description="Get information about travel destinations, attractions, and local tips",
                    tags=["travel", "tourism", "destination", "attractions", "sightseeing"],
                    examples=["Tell me about visiting Paris", "Best attractions in Rome", "What to see in Tokyo"]
                ),
                AgentSkill(
                    name="Travel Planning",
                    description="Get advice for planning trips, including itineraries and best times to visit",
                    tags=["travel", "planning", "itinerary", "vacation", "trip"],
                    examples=["Plan a 3-day trip to London", "When is the best time to visit Australia?"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with a travel request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        destination = self._extract_destination(query)
        
        # Add a delay to simulate processing
        logger.info(f"[Travel Agent] Processing travel request for {destination}...")
        time.sleep(0.8)
        
        if self._is_planning_query(query):
            result = self._create_travel_plan(destination, query)
        else:
            result = self._get_destination_info(destination)
        
        logger.info(f"[Travel Agent] Completed travel information for {destination}")
        
        return Message(
            content=TextContent(text=result),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task-based travel request."""
        query = self._extract_query_from_task(task)
        destination = self._extract_destination(query)
        
        # Add a delay to simulate processing
        logger.info(f"[Travel Agent] Processing travel request for {destination}...")
        time.sleep(0.8)
        
        if self._is_planning_query(query):
            result = self._create_travel_plan(destination, query)
        else:
            result = self._get_destination_info(destination)
        
        logger.info(f"[Travel Agent] Completed travel information for {destination}")
        
        # Update task with the travel information
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
    
    def _extract_destination(self, query: str) -> str:
        """Extract destination from the query."""
        destinations = ["paris", "rome", "london", "tokyo", "new york"]
        
        for destination in destinations:
            if destination.lower() in query.lower():
                return destination.title()
        
        return "Paris"  # Default destination
    
    def _is_planning_query(self, query: str) -> bool:
        """Check if the query is about travel planning."""
        planning_keywords = ["plan", "itinerary", "schedule", "visit", "best time"]
        
        return any(keyword in query.lower() for keyword in planning_keywords)
    
    def _get_destination_info(self, destination: str) -> str:
        """Get information about a travel destination."""
        destination_info = {
            "Paris": """Paris, France - Travel Information:
            
Paris, often called the "City of Light," is famous for its art, culture, cuisine, and iconic landmarks.

Top Attractions:
1. Eiffel Tower - The iconic iron lattice tower offering panoramic views
2. Louvre Museum - World's largest art museum, home to the Mona Lisa
3. Notre-Dame Cathedral - Medieval Catholic cathedral (under restoration)
4. Champs-Élysées & Arc de Triomphe - Famous avenue and monument
5. Montmartre & Sacré-Cœur - Historic district with basilica offering views of the city""",

            "Rome": """Rome, Italy - Travel Information:
            
Rome, the "Eternal City," is a living museum of ancient history, Renaissance art, and vibrant street life.

Top Attractions:
1. Colosseum - Ancient Roman amphitheater
2. Vatican City - Independent state home to St. Peter's Basilica and the Vatican Museums
3. Roman Forum - Ancient government buildings and temples
4. Trevi Fountain - Baroque masterpiece and wishing fountain
5. Pantheon - Ancient Roman temple with a magnificent dome"""
        }
        
        return destination_info.get(destination, f"Detailed information for {destination} is currently not available.")
    
    def _create_travel_plan(self, destination: str, query: str) -> str:
        """Create a travel plan or itinerary."""
        # Extract duration from query if available
        days = 3  # Default duration
        duration_match = re.search(r"(\d+)[- ]day", query.lower())
        if duration_match:
            days = int(duration_match.group(1))
            days = min(max(days, 1), 7)  # Limit to 1-7 days
        
        # Create a simple travel plan
        plan = f"{days}-Day Travel Itinerary for {destination}:\n\n"
        
        # Basic itineraries for a few cities
        if destination.lower() == "paris":
            day_plans = [
                "Day 1: Morning: Eiffel Tower - Afternoon: Seine River Cruise - Evening: Dinner in Le Marais",
                "Day 2: Morning: Louvre Museum - Afternoon: Tuileries Garden - Evening: Champs-Élysées walk",
                "Day 3: Morning: Notre-Dame (exterior) - Afternoon: Montmartre - Evening: Dinner with a view"
            ]
        elif destination.lower() == "rome":
            day_plans = [
                "Day 1: Morning: Colosseum - Afternoon: Roman Forum - Evening: Dinner in Trastevere",
                "Day 2: Morning: Vatican Museums - Afternoon: St. Peter's Basilica - Evening: Castel Sant'Angelo",
                "Day 3: Morning: Pantheon - Afternoon: Trevi Fountain & Spanish Steps - Evening: Dinner near Piazza Navona"
            ]
        else:
            # Generic plan for other destinations
            day_plans = [
                f"Day 1: Morning: Top historical attraction - Afternoon: City tour - Evening: Dinner in popular district",
                f"Day 2: Morning: Main museum or gallery - Afternoon: Shopping district - Evening: Local entertainment",
                f"Day 3: Morning: Local neighborhood exploration - Afternoon: Park or garden - Evening: Farewell dinner"
            ]
        
        # Add detailed day plans based on requested duration
        for day in range(min(days, len(day_plans))):
            plan += f"{day_plans[day]}\n\n"
        
        return plan


class KnowledgeAgent(A2AServer):
    """Agent that answers general knowledge questions."""
    
    def __init__(self):
        """Initialize the knowledge agent with its capabilities."""
        agent_card = AgentCard(
            name="Knowledge Agent",
            description="Provides factual information and answers to general knowledge questions across various domains",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Facts and Information",
                    description="Answer factual questions about history, science, geography, and other general topics",
                    tags=["knowledge", "facts", "information", "questions", "general"],
                    examples=["What is the capital of Japan?", "When was the Declaration of Independence signed?"]
                ),
                AgentSkill(
                    name="Definitions and Concepts",
                    description="Explain and define terms, concepts, and ideas",
                    tags=["definition", "meaning", "concept", "explanation", "define"],
                    examples=["What is photosynthesis?", "Define quantum physics"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message with a knowledge request."""
        query = message.content.text if hasattr(message.content, "text") else ""
        
        # Add a delay to simulate processing and research
        logger.info("[Knowledge Agent] Researching information...")
        time.sleep(0.8)
        
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
        
        # Add a delay to simulate processing and research
        logger.info("[Knowledge Agent] Researching information...")
        time.sleep(0.8)
        
        answer = self._answer_question(query)
        
        logger.info("[Knowledge Agent] Answer found")
        
        # Update task with the knowledge information
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
        """Answer a knowledge question with simulated information."""
        query_lower = query.lower()
        
        # Simple knowledge base with a few predefined answers
        knowledge_base = {
            # Geography
            "capital of japan": "The capital of Japan is Tokyo, which is also the largest city in Japan with a population of over 13 million people.",
            "capital of france": "The capital of France is Paris, often called the 'City of Light' (La Ville Lumière).",
            
            # Science
            "photosynthesis": "Photosynthesis is the process used by plants, algae, and certain bacteria to convert light energy, usually from the sun, into chemical energy in the form of glucose or other sugars. The basic equation is: 6CO₂ + 6H₂O + light energy → C₆H₁₂O₆ + 6O₂.",
            
            # Technology
            "artificial intelligence": "Artificial Intelligence (AI) refers to systems or machines that mimic human intelligence to perform tasks and can iteratively improve themselves based on the information they collect. Common AI applications include machine learning, natural language processing, computer vision, and robotics."
        }
        
        # Check for direct matches in the knowledge base
        for key, answer in knowledge_base.items():
            if key in query_lower:
                return answer
        
        # No match found, generate a generic response
        return "I don't have specific information on that question in my knowledge base. As a simulated agent, I have access to only a limited set of predefined answers."


class OpenAIAgent(A2AServer):
    """Agent powered by OpenAI's models."""
    
    def __init__(self, api_key=None, model="gpt-3.5-turbo"):
        """Initialize the OpenAI agent with its capabilities."""
        agent_card = AgentCard(
            name="OpenAI Agent",
            description="General purpose assistant powered by OpenAI's language models",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="General Assistance",
                    description="Provides helpful, accurate, and safe responses to a wide range of queries",
                    tags=["assistant", "general", "information", "help"],
                    examples=["How do I bake a chocolate cake?", "Explain how the stock market works"]
                )
            ]
        )
        
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.model = model
        
        if not OPENAI_AVAILABLE:
            logger.warning("OpenAI package not installed, using basic A2A server.")
            super().__init__(agent_card=agent_card)
            return
            
        if not self.api_key:
            logger.warning("OpenAI API key not found, using basic A2A server.")
            super().__init__(agent_card=agent_card)
            return
            
        try:
            # Create an OpenAI-powered A2A server
            self.openai_server = OpenAIA2AServer(
                api_key=self.api_key,
                model=self.model,
                system_prompt="You are a helpful AI assistant. Provide clear, concise answers to questions."
            )
            self.agent_card = agent_card
        except Exception as e:
            logger.warning(f"Error initializing OpenAI server: {e}. Using basic A2A server.")
            super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle message using OpenAI's capabilities."""
        if hasattr(self, 'openai_server'):
            try:
                return self.openai_server.handle_message(message)
            except Exception as e:
                logger.error(f"Error with OpenAI: {e}")
                return Message(
                    content=TextContent(text=f"Sorry, I encountered an error processing your request: {str(e)}"),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        else:
            return Message(
                content=TextContent(text="I'm an OpenAI agent, but I'm not fully configured. Please check your API key."),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task using OpenAI's capabilities."""
        if hasattr(self, 'openai_server'):
            try:
                return self.openai_server.handle_task(task)
            except Exception as e:
                logger.error(f"Error with OpenAI: {e}")
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"Sorry, I encountered an error processing your request: {str(e)}"}]
                }]
                task.status = TaskStatus(state=TaskState.COMPLETED)
                return task
        else:
            task.artifacts = [{
                "parts": [{"type": "text", "text": "I'm an OpenAI agent, but I'm not fully configured. Please check your API key."}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            return task


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
    
    # Register the server in the running_agents dictionary
    global running_agents
    running_agents[port] = {
        "agent": agent,
        "type": agent.__class__.__name__,
        "name": agent.agent_card.name,
        "url": f"http://localhost:{port}",
        "start_time": time.time()
    }
    
    # Signal that we're ready to start
    if ready_event:
        ready_event.set()
    
    # Disable Flask's default logging
    import logging
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    # Start the server
    try:
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
    except Exception as e:
        logger.error(f"Error starting agent server on port {port}: {e}")
    finally:
        # Remove from running_agents when stopped
        if port in running_agents:
            del running_agents[port]


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


class KeywordRouter:
    """Router that uses simple keyword matching to route queries."""
    
    def __init__(self, agent_network):
        """Initialize the keyword router."""
        self.agent_network = agent_network
        self.keyword_mapping = {}
        
        # Create mappings from agent information
        self._initialize_keyword_mappings()
    
    def _initialize_keyword_mappings(self):
        """Build keyword mappings from agent capabilities."""
        for name, agent in self.agent_network.agents.items():
            agent_card = self.agent_network.get_agent_card(name)
            
            if not agent_card:
                continue
            
            # Extract keywords from agent name and description
            keywords = [name.lower()]
            if hasattr(agent_card, 'name'):
                keywords.extend(agent_card.name.lower().split())
            if hasattr(agent_card, 'description'):
                # Add key phrases from description
                desc = agent_card.description.lower()
                # Split into words and remove common words
                stop_words = {'a', 'an', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'with', 'about'}
                desc_words = [w for w in desc.split() if w not in stop_words and len(w) > 3]
                keywords.extend(desc_words)
            
            # Extract keywords from skills
            if hasattr(agent_card, 'skills'):
                for skill in agent_card.skills:
                    if hasattr(skill, 'tags'):
                        keywords.extend([tag.lower() for tag in skill.tags])
                    if hasattr(skill, 'name'):
                        keywords.extend(skill.name.lower().split())
            
            # Filter unique and useful keywords
            keywords = list(set(keywords))
            
            # Map each keyword to this agent
            for keyword in keywords:
                if keyword not in self.keyword_mapping:
                    self.keyword_mapping[keyword] = []
                self.keyword_mapping[keyword].append(name)
    
    def route_query(self, query, conversation_history=None, use_cache=True):
        """
        Route a query to the most appropriate agent based on keywords.
        
        Args:
            query: The query to route
            conversation_history: Not used by keyword router
            use_cache: Not used by keyword router
            
        Returns:
            A tuple of (agent_name, confidence_score)
        """
        query_lower = query.lower()
        agent_scores = {}
        
        # Calculate scores for each agent based on keyword matches
        for keyword, agents in self.keyword_mapping.items():
            if keyword in query_lower:
                for agent in agents:
                    agent_scores[agent] = agent_scores.get(agent, 0) + 1
        
        # Find the agent with the highest score
        if agent_scores:
            best_agent = max(agent_scores.items(), key=lambda x: x[1])
            agent_name = best_agent[0]
            score = best_agent[1]
            confidence = min(score / 10, 1.0)  # Normalize confidence to [0, 1]
            return agent_name, confidence
        
        # If no keywords match, return a random agent with low confidence
        all_agents = list(self.agent_network.agents.keys())
        if all_agents:
            return random.choice(all_agents), 0.1
        
        # No agents available
        return None, 0.0


class RandomRouter:
    """Router that randomly selects an agent."""
    
    def __init__(self, agent_network):
        """Initialize the random router."""
        self.agent_network = agent_network
    
    def route_query(self, query, conversation_history=None, use_cache=True):
        """
        Route a query to a random agent.
        
        Args:
            query: Not used by random router
            conversation_history: Not used by random router
            use_cache: Not used by random router
            
        Returns:
            A tuple of (agent_name, confidence_score)
        """
        all_agents = list(self.agent_network.agents.keys())
        if not all_agents:
            return None, 0.0
            
        return random.choice(all_agents), 0.5  # Fixed medium confidence


def create_router(router_type, agent_network, openai_client=None):
    """
    Create a router of the specified type.
    
    Args:
        router_type: Type of router to create ('ai', 'keyword', 'random')
        agent_network: Network of available agents
        openai_client: Optional OpenAI client for AI router
        
    Returns:
        Router instance
    """
    if router_type == 'ai':
        if OPENAI_AVAILABLE and openai_client:
            try:
                return AIAgentRouter(
                    llm_client=openai_client,
                    agent_network=agent_network,
                    system_prompt="""You are a router that analyzes user queries and determines which specialized agent would be best suited to handle the request.
Consider the query's topic, intent, and any specific requirements. Your goal is to accurately match each query to the most appropriate agent.
Respond with just the name of the most appropriate agent.""",
                    max_history_tokens=200
                )
            except Exception as e:
                logger.warning(f"Failed to create AIAgentRouter: {e}. Using keyword router instead.")
                return KeywordRouter(agent_network)
        else:
            logger.warning("OpenAI not available, using keyword router")
            return KeywordRouter(agent_network)
    elif router_type == 'keyword':
        return KeywordRouter(agent_network)
    elif router_type == 'random':
        return RandomRouter(agent_network)
    else:
        raise ValueError(f"Unknown router type: {router_type}")


def process_query(query, router, network, show_details=False):
    """
    Process a query using the specified router.
    
    Args:
        query: Query to process
        router: Router to use for agent selection
        network: Agent network
        show_details: Whether to show detailed routing information
        
    Returns:
        The agent's response
    """
    start_time = time.time()
    
    # Route the query to an agent
    routing_start = time.time()
    agent_name, confidence = router.route_query(query)
    routing_time = time.time() - routing_start
    
    if not agent_name:
        return "No suitable agent found for this query."
    
    # Get the agent
    agent = network.get_agent(agent_name)
    
    if not agent:
        return f"Agent '{agent_name}' not found in the network."
    
    # Send the query to the agent
    processing_start = time.time()
    
    try:
        # Send the query
        response = agent.ask(query)
        
        # Calculate timings
        processing_time = time.time() - processing_start
        total_time = time.time() - start_time
        
        # Format the response with timing details if requested
        if show_details:
            result = f"🔀 Routed to: {agent_name} (confidence: {confidence:.2f})\n"
            result += f"⏱️ Routing time: {routing_time:.2f}s | Processing time: {processing_time:.2f}s | Total: {total_time:.2f}s\n\n"
            result += f"📝 Response from {agent_name}:\n{response}"
            return result
        else:
            return response
    
    except Exception as e:
        return f"Error processing query: {str(e)}"


def compare_routers(query, network, test_queries=None):
    """
    Compare different router types on the same query or a set of test queries.
    
    Args:
        query: Single query to test, or None to use test_queries
        network: Agent network to use
        test_queries: List of test queries to use if query is None
        
    Returns:
        Comparison results
    """
    if not test_queries and not query:
        test_queries = [
            "What's the weather like in London today?",
            "Calculate 125 * 37",
            "Tell me about visiting Paris",
            "What is photosynthesis?",
            "What are the top attractions in Tokyo?"
        ]
    elif query:
        test_queries = [query]
    
    # Initialize routers
    openai_client = None
    if OPENAI_AVAILABLE and os.environ.get("OPENAI_API_KEY"):
        try:
            openai_client = OpenAIA2AClient(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model="gpt-3.5-turbo"
            )
        except:
            pass
    
    router_types = ['ai', 'keyword', 'random']
    routers = {}
    for router_type in router_types:
        routers[router_type] = create_router(router_type, network, openai_client)
    
    # Process each query with each router
    results = []
    
    for q in test_queries:
        query_results = {"query": q, "routers": {}}
        
        for router_type, router in routers.items():
            # Route the query
            routing_start = time.time()
            agent_name, confidence = router.route_query(q)
            routing_time = time.time() - routing_start
            
            # Record the result
            query_results["routers"][router_type] = {
                "agent": agent_name,
                "confidence": confidence,
                "routing_time": routing_time
            }
        
        results.append(query_results)
    
    return results


def print_comparison_results(results):
    """
    Print comparison results in a readable format.
    """
    print("\n=== Router Comparison Results ===\n")
    
    for i, result in enumerate(results, 1):
        print(f"Query {i}: \"{result['query']}\"")
        print("-" * 60)
        
        router_results = result["routers"]
        
        # Print header
        print(f"{'Router':<10} | {'Agent':<15} | {'Confidence':<10} | {'Time (ms)':<10}")
        print("-" * 60)
        
        # Print results for each router
        for router_type, router_result in router_results.items():
            agent = router_result.get("agent", "None")
            confidence = router_result.get("confidence", 0)
            routing_time = router_result.get("routing_time", 0) * 1000  # Convert to ms
            
            print(f"{router_type:<10} | {str(agent):<15} | {confidence:.2f}       | {routing_time:.2f} ms")
        
        print("\n")


def print_agent_info(network):
    """
    Print information about agents in the network.
    """
    print("\n=== Agents in Network ===\n")
    
    agents = network.list_agents()
    
    for i, agent in enumerate(agents, 1):
        print(f"{i}. {agent['name']}")
        if "description" in agent:
            print(f"   Description: {agent['description']}")
        if "skills_count" in agent:
            print(f"   Skills: {agent['skills_count']}")
        print("")
    
    if not agents:
        print("No agents found in the network.")
    
    print(f"Total: {len(agents)} agents\n")


def main():
    """Run the smart routing example."""
    parser = argparse.ArgumentParser(description="Smart Routing Example")
    parser.add_argument('--router-type', type=str, default='ai',
                       choices=['ai', 'keyword', 'random'],
                       help='Type of router to use')
    parser.add_argument('--query', type=str, default=None,
                       help='Query to test routing with')
    parser.add_argument('--model', type=str, default='gpt-3.5-turbo',
                       help='OpenAI model to use for AI router')
    parser.add_argument('--compare', action='store_true',
                       help='Compare all router types')
    parser.add_argument('--openai-key', type=str, default=None,
                       help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    
    args = parser.parse_args()
    
    # Set OpenAI API key if provided
    if args.openai_key:
        os.environ["OPENAI_API_KEY"] = args.openai_key
    
    print("=== Smart Routing Example ===")
    
    if not args.query and not args.compare:
        print("""
This example demonstrates intelligent routing of queries to specialized agents using AI.
Use --query to test a specific query, or --compare to see how different routers behave.

Example queries:
- "What's the weather in London today?"
- "Calculate 125 * 37"
- "Tell me about visiting Paris"
- "What is photosynthesis?"
""")
    
    # Create agents for different domains
    weather_agent = WeatherAgent()
    math_agent = MathAgent()
    travel_agent = TravelAgent()
    knowledge_agent = KnowledgeAgent()
    
    # Create OpenAI agent if possible
    openai_agent = None
    if OPENAI_AVAILABLE and (args.openai_key or os.environ.get("OPENAI_API_KEY")):
        openai_agent = OpenAIAgent(
            api_key=os.environ.get("OPENAI_API_KEY"),
            model=args.model
        )
    
    # Find available ports
    weather_port = find_free_port()
    math_port = find_free_port()
    travel_port = find_free_port()
    knowledge_port = find_free_port()
    openai_port = find_free_port() if openai_agent else None
    
    # Start agent servers in separate threads
    ready_events = []
    threads = []
    
    print("Starting agent servers...")
    
    for agent, port in [
        (weather_agent, weather_port),
        (math_agent, math_port),
        (travel_agent, travel_port),
        (knowledge_agent, knowledge_port)
    ] + ([(openai_agent, openai_port)] if openai_agent else []):
        ready_event = threading.Event()
        ready_events.append(ready_event)
        
        thread = threading.Thread(
            target=start_agent_server,
            args=(agent, port, ready_event),
            daemon=True
        )
        threads.append(thread)
        thread.start()
        
        # Small delay to avoid port conflicts
        time.sleep(0.1)
    
    # Wait for all servers to be ready
    for event in ready_events:
        event.wait(timeout=5.0)
    
    # Create agent network
    network = AgentNetwork(name="Smart Routing Network")
    
    # Add agents to the network
    network.add("weather", f"http://localhost:{weather_port}")
    network.add("math", f"http://localhost:{math_port}")
    network.add("travel", f"http://localhost:{travel_port}")
    network.add("knowledge", f"http://localhost:{knowledge_port}")
    if openai_agent:
        network.add("openai", f"http://localhost:{openai_port}")
    
    print(f"✓ Started {len(network.agents)} agents successfully")
    
    # Print agent information
    print_agent_info(network)
    
    # Create router client
    openai_router_client = None
    if OPENAI_AVAILABLE and (args.openai_key or os.environ.get("OPENAI_API_KEY")):
        try:
            openai_router_client = OpenAIA2AClient(
                api_key=os.environ.get("OPENAI_API_KEY"),
                model=args.model
            )
        except Exception as e:
            logger.warning(f"Error creating OpenAI client for router: {e}")
    
    # Create router
    router = create_router(args.router_type, network, openai_router_client)
    
    if args.compare:
        # Run comparison of different router types
        results = compare_routers(args.query, network)
        print_comparison_results(results)
    elif args.query:
        # Process a single query
        print(f"\nQuery: {args.query}")
        print(f"Router: {args.router_type}")
        print("-" * 60)
        
        response = process_query(args.query, router, network, show_details=True)
        print(f"\n{response}")
    else:
        # Interactive mode
        print("\nEnter queries to test routing (type 'exit' to quit):")
        
        while True:
            try:
                user_query = input("\n> ")
                if user_query.lower() in ('exit', 'quit', 'q'):
                    break
                    
                response = process_query(user_query, router, network, show_details=True)
                print(f"\n{response}")
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
    
    print("\nShutting down agent servers...")
    
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nExiting smart routing example...")
        sys.exit(0)