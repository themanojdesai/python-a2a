#!/usr/bin/env python
"""
Agent Discovery Example

This example demonstrates automatic discovery of A2A agents in a network.
It shows how to:
- Deploy multiple specialized agents on different ports
- Automatically discover available agents through URL scanning
- Filter and verify discovered agents based on capabilities
- Update the agent network dynamically as agents come and go

To run:
    python agent_discovery.py [--scan-range MIN MAX] [--filters FILTER1,FILTER2]

Example:
    python agent_discovery.py --scan-range 8000 8100 --filters weather,math

Available filters:
    weather, math, news, travel, knowledge (filter by agent type)
    all (show all agents)

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
from typing import Dict, List, Optional, Set, Tuple, Union
from flask import Flask, request, jsonify

from python_a2a import (
    A2AServer, AgentCard, AgentSkill,
    AgentNetwork, Message, TextContent, MessageRole,
    Task, TaskStatus, TaskState
)

try:
    from python_a2a.server.llm import OpenAIA2AServer
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("AgentDiscovery")

# Global dictionary to track running agents
running_agents = {}
discovery_active = True


class WeatherAgent(A2AServer):
    """Agent that provides weather information."""
    
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
    
    def handle_task(self, task: Task) -> Task:
        """Handle weather-related tasks."""
        query = self._extract_query_from_task(task)
        city = self._extract_city(query)
        
        # Add a small delay to simulate processing
        time.sleep(0.5)
        
        # Generate weather response
        weather = self._get_weather(city)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": weather}]
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
        cities = ["london", "paris", "new york", "tokyo", "sydney"]
        for city in cities:
            if city.lower() in query.lower():
                return city.title()
        return "London"  # Default city
    
    def _get_weather(self, city: str) -> str:
        """Get simulated weather data for a city."""
        conditions = ["Sunny", "Cloudy", "Rainy", "Partly Cloudy", "Clear", "Stormy"]
        temperature = random.randint(10, 30)
        condition = random.choice(conditions)
        
        return f"Current weather in {city}: {condition}, {temperature}°C / {temperature * 9//5 + 32}°F"
    
    def handle_message(self, message: Message) -> Message:
        """Handle direct messages for compatibility."""
        query = message.content.text if hasattr(message.content, "text") else ""
        city = self._extract_city(query)
        weather = self._get_weather(city)
        
        return Message(
            content=TextContent(text=weather),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


class MathAgent(A2AServer):
    """Agent that performs mathematical calculations."""
    
    def __init__(self):
        """Initialize the math agent with its capabilities."""
        agent_card = AgentCard(
            name="Math Agent",
            description="Performs mathematical calculations and conversions",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Basic Arithmetic",
                    description="Perform basic arithmetic operations (+, -, *, /)",
                    tags=["math", "arithmetic", "calculation"],
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
    
    def handle_task(self, task: Task) -> Task:
        """Handle math-related tasks."""
        query = self._extract_query_from_task(task)
        
        # Add a small delay to simulate processing
        time.sleep(0.2)
        
        # Extract and solve math problem
        result = self._calculate(query)
        
        # Create response
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
    
    def _calculate(self, query: str) -> str:
        """Perform a simple calculation based on the query."""
        import re
        
        # Look for math expressions
        expression = None
        
        # Try to extract a math expression
        exp_match = re.search(r"([\d\s\+\-\*\/\(\)\.\%]+)", query)
        if exp_match:
            expression = exp_match.group(1).strip()
        
        if expression:
            try:
                # Safely evaluate the expression
                result = eval(expression)
                return f"The result of {expression} is {result}"
            except Exception as e:
                return f"Error calculating {expression}: {str(e)}"
        
        return "No valid mathematical expression found in the query."
    
    def handle_message(self, message: Message) -> Message:
        """Handle direct messages for compatibility."""
        query = message.content.text if hasattr(message.content, "text") else ""
        result = self._calculate(query)
        
        return Message(
            content=TextContent(text=result),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


class TravelAgent(A2AServer):
    """Agent that provides travel recommendations."""
    
    def __init__(self):
        """Initialize the travel agent with its capabilities."""
        agent_card = AgentCard(
            name="Travel Agent",
            description="Provides travel recommendations and destination information",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Destination Info",
                    description="Get information about travel destinations",
                    tags=["travel", "destination", "tourism", "sightseeing"],
                    examples=["Tell me about visiting Paris", "What should I see in Tokyo?"]
                ),
                AgentSkill(
                    name="Travel Planning",
                    description="Get travel planning advice",
                    tags=["travel", "planning", "itinerary", "tips"],
                    examples=["Planning a trip to Italy", "Best time to visit Australia"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_task(self, task: Task) -> Task:
        """Handle travel-related tasks."""
        query = self._extract_query_from_task(task)
        destination = self._extract_destination(query)
        
        # Add a delay to simulate processing
        time.sleep(1.0)
        
        # Generate travel information
        info = self._get_destination_info(destination)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": info}]
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
        destinations = ["paris", "tokyo", "new york", "rome", "sydney", "london"]
        for dest in destinations:
            if dest.lower() in query.lower():
                return dest.title()
        return "Paris"  # Default destination
    
    def _get_destination_info(self, destination: str) -> str:
        """Get travel information for a destination."""
        destination_info = {
            "Paris": """Paris, France - Travel Information:
- Top attractions: Eiffel Tower, Louvre Museum, Notre Dame Cathedral
- Best time to visit: April to June and October to November
- Local currency: Euro (€)
- Transportation: Excellent public transit with Metro, buses and RER trains
- Known for: Art, culture, cuisine, fashion, and romantic atmosphere""",
            
            "Tokyo": """Tokyo, Japan - Travel Information:
- Top attractions: Tokyo Skytree, Senso-ji Temple, Shibuya Crossing
- Best time to visit: March to May (spring) and September to November (fall)
- Local currency: Japanese Yen (¥)
- Transportation: Highly efficient subway and train system
- Known for: Technology, anime, shopping, cuisine, and blend of traditional and modern culture""",
            
            "New York": """New York City, USA - Travel Information:
- Top attractions: Times Square, Statue of Liberty, Central Park, Empire State Building
- Best time to visit: April to June and September to November
- Local currency: US Dollar ($)
- Transportation: Extensive subway system, buses and taxis
- Known for: Theatre, art, architecture, shopping, and diverse cuisine""",
            
            "Rome": """Rome, Italy - Travel Information:
- Top attractions: Colosseum, Vatican City, Trevi Fountain, Roman Forum
- Best time to visit: April to June and September to October
- Local currency: Euro (€)
- Transportation: Buses, trams, and metro
- Known for: Ancient history, art, architecture, and excellent cuisine""",
            
            "Sydney": """Sydney, Australia - Travel Information:
- Top attractions: Sydney Opera House, Harbour Bridge, Bondi Beach
- Best time to visit: September to November and March to May
- Local currency: Australian Dollar (AUD)
- Transportation: Trains, buses, ferries
- Known for: Beautiful beaches, harbor, outdoor lifestyle, and diverse culture""",
            
            "London": """London, UK - Travel Information:
- Top attractions: Tower of London, British Museum, Buckingham Palace
- Best time to visit: March to May and September to November
- Local currency: British Pound (£)
- Transportation: Comprehensive Underground (Tube), buses and trains
- Known for: History, theatre, museums, diverse cuisine, and shopping"""
        }
        
        return destination_info.get(destination, f"No detailed information available for {destination}.")
    
    def handle_message(self, message: Message) -> Message:
        """Handle direct messages for compatibility."""
        query = message.content.text if hasattr(message.content, "text") else ""
        destination = self._extract_destination(query)
        info = self._get_destination_info(destination)
        
        return Message(
            content=TextContent(text=info),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


class NewsAgent(A2AServer):
    """Agent that provides simulated news updates."""
    
    def __init__(self):
        """Initialize the news agent with its capabilities."""
        agent_card = AgentCard(
            name="News Agent",
            description="Provides latest news updates on various topics",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Current Headlines",
                    description="Get latest headline news",
                    tags=["news", "headlines", "current events"],
                    examples=["Latest news", "Top headlines today"]
                ),
                AgentSkill(
                    name="Topic News",
                    description="Get news on specific topics",
                    tags=["news", "topics", "categories"],
                    examples=["Technology news", "Sports updates", "Business news"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_task(self, task: Task) -> Task:
        """Handle news-related tasks."""
        query = self._extract_query_from_task(task)
        topic = self._extract_topic(query)
        
        # Add a delay to simulate processing
        time.sleep(1.2)
        
        # Generate news information
        news = self._get_news(topic)
        
        # Create response
        task.artifacts = [{
            "parts": [{"type": "text", "text": news}]
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
    
    def _extract_topic(self, query: str) -> str:
        """Extract news topic from the query."""
        topics = ["technology", "business", "sports", "entertainment", "health", "science"]
        for topic in topics:
            if topic.lower() in query.lower():
                return topic.title()
        return "General"  # Default topic
    
    def _get_news(self, topic: str) -> str:
        """Get simulated news for a topic."""
        # Simulated news headlines with timestamps
        now = time.strftime("%Y-%m-%d")
        
        news_by_topic = {
            "Technology": f"""Technology News Headlines ({now}):
1. New Breakthrough in Quantum Computing Promises Faster Processing
2. Tech Giant Unveils Next-Generation Smartphone with Advanced AI Features
3. Cybersecurity Experts Warn of Rising Ransomware Threats
4. Revolutionary Battery Technology Could Double Electric Vehicle Range
5. Major Cloud Service Provider Announces Global Infrastructure Expansion""",
            
            "Business": f"""Business News Headlines ({now}):
1. Global Markets Rally on Positive Economic Data
2. Major Merger Announced Between Two Industry Leaders
3. Supply Chain Innovations Helping Companies Reduce Costs
4. New Regulatory Framework Proposed for Financial Technology Sector
5. Renewable Energy Investments Reach Record High in First Quarter""",
            
            "Sports": f"""Sports News Headlines ({now}):
1. Underdog Team Clinches Championship in Thrilling Final Match
2. Star Athlete Signs Record-Breaking Contract Extension
3. Olympic Committee Announces New Events for Next Summer Games
4. Sports League Expands with Two New Franchise Teams
5. Technological Innovations Changing How Athletes Train and Recover""",
            
            "Entertainment": f"""Entertainment News Headlines ({now}):
1. Blockbuster Film Breaks Opening Weekend Box Office Records
2. Acclaimed Director Announces Ambitious New Project
3. Streaming Platform's Original Series Wins Multiple Awards
4. Music Festival Announces Impressive Lineup for Next Year
5. Virtual Reality Entertainment Experiences Gaining Mainstream Popularity""",
            
            "Health": f"""Health News Headlines ({now}):
1. Promising Results in Clinical Trials for New Treatment Approach
2. Health Authorities Update Guidelines on Preventive Care
3. Research Reveals New Benefits of Mediterranean Diet
4. Mental Health Awareness Campaign Launches Nationwide
5. Wearable Health Technology Market Continues Rapid Growth""",
            
            "Science": f"""Science News Headlines ({now}):
1. Astronomers Discover Potentially Habitable Exoplanet
2. Major Breakthrough in Clean Energy Technology Announced
3. New Species Discovered in Deep Ocean Exploration
4. Climate Research Offers More Precise Models for Future Changes
5. International Space Mission Prepares for Historic Launch""",
            
            "General": f"""Top Headlines ({now}):
1. World Leaders Gather for Climate Summit to Discuss New Initiatives
2. Economic Report Shows Stronger Than Expected Growth This Quarter
3. New Transportation Infrastructure Plan Unveiled for Major Urban Centers
4. Breakthrough Medical Research Could Transform Treatment Approaches
5. Technology Innovation Reshaping Multiple Industries, Report Finds"""
        }
        
        return news_by_topic.get(topic, news_by_topic["General"])
    
    def handle_message(self, message: Message) -> Message:
        """Handle direct messages for compatibility."""
        query = message.content.text if hasattr(message.content, "text") else ""
        topic = self._extract_topic(query)
        news = self._get_news(topic)
        
        return Message(
            content=TextContent(text=news),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


class KnowledgeAgent(A2AServer):
    """Agent that answers general knowledge questions."""
    
    def __init__(self):
        """Initialize the knowledge agent with its capabilities."""
        agent_card = AgentCard(
            name="Knowledge Agent",
            description="Answers general knowledge questions across various domains",
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="General Questions",
                    description="Answer factual questions",
                    tags=["knowledge", "facts", "information", "questions"],
                    examples=["What is the capital of Japan?", "Who invented the telephone?"]
                ),
                AgentSkill(
                    name="Definitions",
                    description="Provide definitions for terms and concepts",
                    tags=["definition", "meaning", "concept", "term"],
                    examples=["Define photosynthesis", "What is artificial intelligence?"]
                )
            ]
        )
        super().__init__(agent_card=agent_card)
    
    def handle_task(self, task: Task) -> Task:
        """Handle knowledge-related tasks."""
        query = self._extract_query_from_task(task)
        
        # Add a delay to simulate processing
        time.sleep(1.5)
        
        # Generate response
        answer = self._answer_question(query)
        
        # Create response
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
            "capital": {
                "japan": "The capital of Japan is Tokyo.",
                "france": "The capital of France is Paris.",
                "australia": "The capital of Australia is Canberra."
            },
            "invention": {
                "telephone": "The telephone was invented by Alexander Graham Bell in 1876.",
                "light bulb": "The first practical incandescent light bulb was invented by Thomas Edison in 1879."
            },
            "definition": {
                "photosynthesis": "Photosynthesis is the process by which plants and some other organisms convert light energy into chemical energy.",
                "artificial intelligence": "Artificial Intelligence (AI) refers to systems or machines that mimic human intelligence to perform tasks and can iteratively improve themselves based on the information they collect."
            }
        }
        
        # Check for capital questions
        if "capital" in query_lower:
            for country, answer in knowledge_base["capital"].items():
                if country in query_lower:
                    return answer
        
        # Check for invention questions
        if "invent" in query_lower or "who created" in query_lower:
            for item, answer in knowledge_base["invention"].items():
                if item in query_lower:
                    return answer
        
        # Check for definition questions
        if "define" in query_lower or "what is" in query_lower or "meaning of" in query_lower:
            for term, answer in knowledge_base["definition"].items():
                if term in query_lower:
                    return answer
        
        # Default response for unknown questions
        return "I don't have specific information on that question in my limited knowledge base."
    
    def handle_message(self, message: Message) -> Message:
        """Handle direct messages for compatibility."""
        query = message.content.text if hasattr(message.content, "text") else ""
        answer = self._answer_question(query)
        
        return Message(
            content=TextContent(text=answer),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


class OpenAIAgent(A2AServer):
    """Agent powered by OpenAI models."""
    
    def __init__(self, api_key=None, model="gpt-3.5-turbo", expertise=None):
        """Initialize the OpenAI agent with its capabilities."""
        
        # Set the expertise specialization
        self.expertise = expertise or "general"
        description = f"OpenAI-powered agent specializing in {self.expertise} topics"
        examples = ["Tell me about " + self.expertise, f"Can you explain {self.expertise}?"]
        
        skills = [
            AgentSkill(
                name=f"{self.expertise.capitalize()} Expert",
                description=f"Provides detailed information about {self.expertise} topics",
                tags=[self.expertise, "information", "expert", "knowledge"],
                examples=examples
            )
        ]
        
        # Create the agent card
        agent_card = AgentCard(
            name=f"OpenAI {self.expertise.capitalize()} Agent",
            description=description,
            url="http://localhost:0",  # Will be updated when server starts
            version="1.0.0",
            skills=skills
        )
        
        # Setup the underlying OpenAI A2A server
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
            self.openai_server = OpenAIA2AServer(
                api_key=self.api_key,
                model=self.model,
                system_prompt=f"You are a helpful AI assistant specializing in {self.expertise} topics. Provide accurate, concise information about {self.expertise}."
            )
            # Set the agent card
            self.agent_card = agent_card
        except Exception as e:
            logger.warning(f"Failed to create OpenAI server: {e}. Using basic A2A server.")
            super().__init__(agent_card=agent_card)
    
    def handle_message(self, message: Message) -> Message:
        """Handle incoming message using OpenAI."""
        if hasattr(self, 'openai_server'):
            return self.openai_server.handle_message(message)
        else:
            # Fallback response if OpenAI is not configured
            return Message(
                content=TextContent(text=f"I'm an OpenAI {self.expertise} agent, but I'm not fully configured. Please check your API key and OpenAI package installation."),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_task(self, task: Task) -> Task:
        """Handle task using OpenAI."""
        if hasattr(self, 'openai_server'):
            return self.openai_server.handle_task(task)
        else:
            # Fallback response if OpenAI is not configured
            task.artifacts = [{
                "parts": [{
                    "type": "text", 
                    "text": f"I'm an OpenAI {self.expertise} agent, but I'm not fully configured. Please check your API key and OpenAI package installation."
                }]
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
        
    # Add health check endpoint to verify agent is alive
    @app.route('/health', methods=['GET'])
    def health_check():
        """Simple health check endpoint."""
        return jsonify({"status": "ok", "agent": agent.agent_card.name})
    
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


def scan_port_for_agent(url, timeout=0.5):
    """
    Check if there's an A2A agent at the provided URL.
    
    Args:
        url: URL to check for agent
        timeout: Connection timeout in seconds
        
    Returns:
        Agent card dictionary if agent found, None otherwise
    """
    import requests
    
    # Try to fetch agent card
    agent_card_endpoints = [
        f"{url}/agent.json",
        f"{url}/a2a/agent.json"
    ]
    
    for endpoint in agent_card_endpoints:
        try:
            response = requests.get(endpoint, timeout=timeout)
            if response.status_code == 200:
                try:
                    agent_card = response.json()
                    
                    # Verify this is actually an agent card by checking for required fields
                    if isinstance(agent_card, dict) and "name" in agent_card and "description" in agent_card:
                        logger.debug(f"Found agent at {endpoint}")
                        return agent_card
                except:
                    pass
        except:
            pass
    
    # Try health check endpoint
    try:
        response = requests.get(f"{url}/health", timeout=timeout)
        if response.status_code == 200:
            try:
                health_data = response.json()
                if "status" in health_data and health_data["status"] == "ok":
                    return {"name": health_data.get("agent", "Unknown Agent"), 
                            "description": "Agent discovered via health check"}
            except:
                pass
    except:
        pass
    
    return None


def check_agent_capabilities(agent_card, required_capabilities=None):
    """
    Check if an agent has the required capabilities.
    
    Args:
        agent_card: Agent card dictionary
        required_capabilities: List of capability names to check for
        
    Returns:
        True if agent has all required capabilities, False otherwise
    """
    if not required_capabilities:
        return True
    
    # Check agent name and description for required capabilities
    agent_text = f"{agent_card.get('name', '')} {agent_card.get('description', '')}".lower()
    
    for capability in required_capabilities:
        capability_lower = capability.lower()
        if capability_lower not in agent_text:
            # Also check skills if available
            skills = agent_card.get("skills", [])
            skill_match = False
            
            for skill in skills:
                if isinstance(skill, dict):
                    skill_text = f"{skill.get('name', '')} {skill.get('description', '')}".lower()
                    if capability_lower in skill_text:
                        skill_match = True
                        break
            
            if not skill_match:
                return False
    
    return True


def discover_agents(urls, required_capabilities=None, timeout=0.5):
    """
    Discover agents at the provided URLs.
    
    Args:
        urls: List of URLs to check for agents
        required_capabilities: List of capability names to check for
        timeout: Connection timeout in seconds
        
    Returns:
        Dictionary mapping agent URLs to agent cards
    """
    found_agents = {}
    total_urls = len(urls)
    
    print(f"Scanning {total_urls} URLs for A2A agents...")
    
    for i, url in enumerate(urls):
        # Show progress periodically
        if i % 20 == 0 or i == total_urls - 1:
            progress = (i + 1) / total_urls * 100
            print(f"Progress: {progress:.1f}% ({i+1}/{total_urls})")
        
        agent_card = scan_port_for_agent(url, timeout)
        
        if agent_card:
            # Check if agent has required capabilities
            if check_agent_capabilities(agent_card, required_capabilities):
                found_agents[url] = agent_card
                print(f"✓ Found agent: {agent_card.get('name')} at {url}")
    
    return found_agents


def continuous_discovery(network, port_range, required_capabilities=None, interval=30, max_retries=3):
    """
    Continuously discover agents and update the network.
    
    Args:
        network: AgentNetwork to update
        port_range: Tuple of (min_port, max_port) to scan
        required_capabilities: List of capability names to check for
        interval: Seconds between discovery scans
        max_retries: Maximum number of retries for unreachable agents
    """
    global discovery_active
    
    # Track unreachable agents and retry counts
    unreachable = {}
    
    min_port, max_port = port_range
    
    while discovery_active:
        # Generate URLs for the port range
        urls = [f"http://localhost:{port}" for port in range(min_port, max_port + 1)]
        
        # Discover agents
        found_agents = discover_agents(urls, required_capabilities)
        
        # Update the network
        for url, agent_card in found_agents.items():
            agent_name = agent_card.get("name", "Unknown Agent")
            formatted_name = agent_name.lower().replace(" ", "_")
            
            if not network.has_agent(formatted_name):
                # New agent found, add to network
                try:
                    network.add(formatted_name, url)
                    print(f"✓ Added {agent_name} to network")
                    # Reset retry count if this was previously unreachable
                    if url in unreachable:
                        del unreachable[url]
                except Exception as e:
                    print(f"× Error adding {agent_name} to network: {e}")
        
        # Check for agents that have disappeared
        for name in list(network.agents.keys()):
            agent_url = network.agent_urls.get(name)
            if agent_url and agent_url not in found_agents:
                # Agent is missing, increment retry count
                unreachable[agent_url] = unreachable.get(agent_url, 0) + 1
                
                if unreachable[agent_url] > max_retries:
                    # Remove from network after max retries
                    print(f"× Agent {name} is unreachable. Removing from network.")
                    network.remove(name)
                    del unreachable[agent_url]
                else:
                    print(f"! Agent {name} is unreachable. Will retry ({unreachable[agent_url]}/{max_retries})")
        
        # Wait for the next scan
        print(f"\nNetwork currently has {len(network.agents)} agents")
        print(f"Next discovery scan in {interval} seconds...")
        print("Press Ctrl+C to stop discovery\n")
        
        # Sleep in small increments to allow for quicker shutdown
        for _ in range(interval):
            if not discovery_active:
                break
            time.sleep(1)


def shutdown_handler(signal_num, frame):
    """Handle shutdown signals gracefully."""
    global discovery_active
    print("\nShutting down agent discovery...")
    discovery_active = False
    
    # Give some time for threads to clean up
    time.sleep(1)
    sys.exit(0)


def main():
    """Run the agent discovery example."""
    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Agent Discovery Example")
    parser.add_argument('--scan-range', nargs=2, type=int, default=[8000, 8100],
                       help='Port range to scan (min max)')
    parser.add_argument('--filters', type=str, default='all',
                       help='Filter agents by capabilities (comma-separated)')
    parser.add_argument('--interval', type=int, default=30,
                       help='Discovery scan interval in seconds')
    parser.add_argument('--openai-key', type=str, default=None,
                       help='OpenAI API key (or set OPENAI_API_KEY environment variable)')
    
    args = parser.parse_args()
    
    # Process filters
    if args.filters.lower() == 'all':
        capability_filters = None
    else:
        capability_filters = [cap.strip() for cap in args.filters.split(',')]
    
    print("=== Agent Discovery Example ===")
    
    # Set OpenAI API key if provided
    if args.openai_key:
        os.environ["OPENAI_API_KEY"] = args.openai_key
    
    # Create different agent types
    weather_agent = WeatherAgent()
    math_agent = MathAgent()
    travel_agent = TravelAgent()
    news_agent = NewsAgent()
    knowledge_agent = KnowledgeAgent()
    
    # Create OpenAI-powered agents if possible
    openai_agents = []
    if OPENAI_AVAILABLE and (args.openai_key or os.environ.get("OPENAI_API_KEY")):
        print("Creating OpenAI-powered agents...")
        openai_agents = [
            OpenAIAgent(expertise="science", model="gpt-3.5-turbo"),
            OpenAIAgent(expertise="history", model="gpt-3.5-turbo"),
            OpenAIAgent(expertise="technology", model="gpt-3.5-turbo")
        ]
    
    # Find available ports
    min_port, max_port = args.scan_range
    print(f"Starting agents on random ports in range {min_port}-{max_port}...")
    
    try:
        # Find ports within the specified range
        available_ports = []
        while len(available_ports) < 5 + len(openai_agents):
            port = random.randint(min_port, max_port)
            if port not in available_ports:
                available_ports.append(port)
        
        # Basic agents
        weather_port, math_port, travel_port, news_port, knowledge_port = available_ports[:5]
        
        # OpenAI agent ports
        openai_ports = available_ports[5:5+len(openai_agents)]
        
        # Start agent servers in separate threads
        ready_events = []
        agent_threads = []
        
        # Start basic agents
        for agent, port in [
            (weather_agent, weather_port),
            (math_agent, math_port),
            (travel_agent, travel_port),
            (news_agent, news_port),
            (knowledge_agent, knowledge_port)
        ]:
            ready_event = threading.Event()
            ready_events.append(ready_event)
            
            thread = threading.Thread(
                target=start_agent_server,
                args=(agent, port, ready_event),
                daemon=True
            )
            agent_threads.append(thread)
            thread.start()
            
            # Add small delay to avoid port conflicts
            time.sleep(0.1)
        
        # Start OpenAI agents if available
        for agent, port in zip(openai_agents, openai_ports):
            ready_event = threading.Event()
            ready_events.append(ready_event)
            
            thread = threading.Thread(
                target=start_agent_server,
                args=(agent, port, ready_event),
                daemon=True
            )
            agent_threads.append(thread)
            thread.start()
            
            # Add small delay to avoid port conflicts
            time.sleep(0.1)
        
        # Wait for all servers to be ready
        for event in ready_events:
            event.wait(timeout=5.0)
        
        # Create an empty agent network
        network = AgentNetwork(name="Discovered Agent Network")
        
        # Print the ports where agents are running
        print("\nStarted agents on these ports:")
        for port, agent_info in running_agents.items():
            print(f"- {agent_info['name']} on port {port}")
        
        # Explain the discovery process
        print("\nStarting agent discovery process:")
        if capability_filters:
            print(f"Filtering for agents with these capabilities: {', '.join(capability_filters)}")
        else:
            print("No capability filters applied - will find all agents")
        
        print(f"Will scan ports {min_port} through {max_port}")
        print(f"Discovery scan will repeat every {args.interval} seconds")
        print("Network will be automatically updated as agents come and go")
        
        # Start continuous discovery in a separate thread
        discovery_thread = threading.Thread(
            target=continuous_discovery,
            args=(network, (min_port, max_port), capability_filters, args.interval),
            daemon=True
        )
        discovery_thread.start()
        
        # Wait for user to stop the program
        discovery_thread.join()
        
    except Exception as e:
        print(f"Error in agent discovery: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Run with exception handling for cleaner output
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        shutdown_handler(None, None)