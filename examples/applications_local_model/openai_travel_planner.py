#!/usr/bin/env python
"""
OpenAI Travel Planner Example

A complete travel planning system powered by OpenAI and A2A. 
This example demonstrates how to build a practical travel planner
that uses OpenAI's capabilities combined with specialized agents.

To run:
    export OPENAI_API_KEY=your_api_key
    python openai_travel_planner.py

Requirements:
    pip install "python-a2a[openai,server]"
"""

import os
import sys
import time
import argparse
import socket
import multiprocessing
import re
import json


# Check dependencies
try:
    import python_a2a
    import openai
    import flask
except ImportError as e:
    module_name = getattr(e, 'name', str(e))
    print(f"❌ Missing dependency: {module_name}")
    print("Please install required packages:")
    print("    pip install \"python-a2a[openai,server]\"")
    sys.exit(1)

# Import all necessary A2A components
# The decorators might be in the main package
from python_a2a import A2AServer, run_server, AgentCard, AgentSkill, TaskStatus, TaskState
from python_a2a import OpenAIA2AServer, A2AClient

# Try to get the decorators from the main package
try:
    from python_a2a import skill, agent
except ImportError:
    # Define our own simplified versions if they're not available
    print("⚠️ Could not import skill and agent decorators, using simplified versions")
    
    def skill(name=None, description=None, tags=None, examples=None):
        """Simplified skill decorator"""
        def decorator(func):
            func._skill_info = {
                "name": name or func.__name__,
                "description": description or func.__doc__ or "",
                "tags": tags or [],
                "examples": examples or []
            }
            return func
        return decorator
    
    def agent(name=None, description=None, version=None, url=None):
        """Simplified agent decorator"""
        def decorator(cls):
            return cls
        return decorator

def find_available_port(start_port=5000, max_tries=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_tries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    
    return start_port + 100  # Return something high as fallback

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="OpenAI Travel Planner Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port for the Travel Planner (default: auto-select)"
    )
    parser.add_argument(
        "--model", type=str, default="gpt-4o-mini",
        help="OpenAI model to use (default: gpt-4o-mini)"
    )
    parser.add_argument(
        "--no-test", action="store_true",
        help="Don't run test queries automatically"
    )
    return parser.parse_args()

class TravelKnowledgeBase:
    """Knowledge base of travel information to supplement OpenAI's knowledge"""
    
    def __init__(self):
        # Basic visa rules for popular destinations
        self.visa_rules = {
            "usa": "Tourist visa (B-2) required for most countries. ESTA for Visa Waiver Program countries.",
            "uk": "Standard Visitor visa required for many countries. EU citizens had visa-free access before Brexit.",
            "eu": "Schengen visa required for many non-EU citizens. 90 days in 180-day period limit.",
            "japan": "Visa exemption for many countries for stays up to 90 days.",
            "australia": "eVisitor or ETA for short visits. Longer stays require a proper visa.",
            "canada": "eTA for visa-exempt foreign nationals flying to Canada. Visa required for others.",
            "china": "Almost all foreigners require a visa before arrival.",
            "thailand": "Visa-free for many countries for 30 days. Longer stays require visa.",
            "uae": "Visa on arrival for many nationalities. Others require pre-arranged visa.",
            "singapore": "Visa-free entry for many countries for stays of 30-90 days."
        }
        
        # Travel health advisories
        self.health_advisories = {
            "general": "Always ensure routine vaccinations are up to date before travel.",
            "tropical": "Consider vaccinations for Hepatitis A, Typhoid, and Yellow Fever when traveling to tropical regions.",
            "malaria": "Take antimalarial medication when traveling to regions with malaria risk.",
            "covid": "Check current COVID-19 requirements including testing and vaccination for each destination.",
            "water": "In many developing countries, drink only bottled or boiled water and avoid ice.",
            "altitude": "When traveling to high altitudes, allow time for acclimatization to prevent altitude sickness.",
            "insurance": "Always obtain comprehensive travel health insurance before traveling internationally."
        }
        
        # General travel tips
        self.travel_tips = [
            "Make digital and physical copies of important documents like passports and IDs.",
            "Register with your country's embassy or consulate at your destination.",
            "Research local customs and laws before visiting a new country.",
            "Learn a few basic phrases in the local language of your destination.",
            "Inform your bank and credit card companies about your travel plans.",
            "Pack a basic first aid kit for minor emergencies.",
            "Use transportation apps that work internationally like Uber or local equivalents.",
            "Consider getting a local SIM card or international data plan for your phone.",
            "Check if your destination has any safety concerns or restricted areas.",
            "Research typical scams targeting tourists in your destination."
        ]
    
    def get_visa_info(self, country):
        """Get visa information for a country"""
        country = country.lower()
        # Try direct match
        if country in self.visa_rules:
            return self.visa_rules[country]
        
        # Try partial matches
        for key, value in self.visa_rules.items():
            if key in country or country in key:
                return value
        
        return "Please check with the embassy or consulate of the destination country for specific visa requirements."
    
    def get_health_advisory(self, region=None):
        """Get health advisory for a region"""
        if region and region.lower() in self.health_advisories:
            return self.health_advisories[region.lower()]
        
        # Return general advice
        return self.health_advisories["general"]
    
    def get_travel_tips(self, count=3):
        """Get random travel tips"""
        import random
        return random.sample(self.travel_tips, min(count, len(self.travel_tips)))

def test_client(port):
    """Run test queries against the travel planner"""
    # Wait for server to start
    time.sleep(3)
    
    print("\n🧪 Testing the Travel Planner...")
    client = A2AClient(f"http://localhost:{port}")
    
    # Test queries
    test_queries = [
        "Plan a 3-day trip to Tokyo",
        "What are the visa requirements for visiting France?",
        "Suggest some activities for a family vacation in London"
    ]
    
    for query in test_queries:
        try:
            print(f"\n💬 Query: {query}")
            response = client.ask(query)
            print(f"✈️ Response: {response}")
            time.sleep(1)
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Test completed! Your Travel Planner is ready to use.")
    print(f"💻 Server running at: http://localhost:{port}")
    print("📝 Try asking questions like: 'Plan a weekend in Paris', 'Best time to visit Thailand', or 'What to pack for a beach vacation'")
    print("🛑 Press Ctrl+C in the server terminal to stop.")

def main():
    # Parse command line arguments
    args = parse_arguments()

    #  Load configuration
    with open("config.json") as f:
        config = json.load(f)
    model_name = config["model_name"]
    base_url = config["base_url"]
    api_key = config["api_key"]
    
    # Auto-select port if not specified
    if args.port is None:
        port = find_available_port()
        print(f"🔍 Auto-selected port: {port}")
    else:
        port = args.port
        print(f"🔍 Using specified port: {port}")
    
    print("\n✈️ OpenAI Travel Planner ✈️")
    print(f"A complete travel planning system powered by OpenAI {model_name}")
    
    # Initialize knowledge base
    kb = TravelKnowledgeBase()
    
    # Create the OpenAI-powered Travel Planner
    class TravelPlanner(A2AServer):
        """
        An OpenAI-powered travel planner that creates itineraries,
        provides travel information, and offers recommendations.
        """
        def __init__(self, knowledge_base, openai_model,base_url, api_key):
            # Initialize with our agent card
            super().__init__(AgentCard(
                name="Travel Planner",
                description="An AI travel assistant that helps plan trips, find information, and provide recommendations",
                url=f"http://localhost:{port}",
                version="1.0.0",
                skills=[
                    AgentSkill(
                        name="Trip Planning",
                        description="Create detailed trip itineraries based on preferences and duration",
                        examples=["Plan a 3-day trip to Tokyo", "Plan a weekend in Paris with kids"]
                    ),
                    AgentSkill(
                        name="Travel Information",
                        description="Provide specific travel information like visa requirements, health advisories, etc.",
                        examples=["Visa requirements for Japan", "Health advice for Thailand"]
                    ),
                    AgentSkill(
                        name="Recommendations",
                        description="Provide customized recommendations for activities, accommodations, and restaurants",
                        examples=["Things to do in London", "Best restaurants in Rome for families"]
                    )
                ]
            ))
            
            # Store knowledge base
            self.kb = knowledge_base
            
            # Initialize OpenAI backend with travel-specific system prompt
            self.openai = OpenAIA2AServer(
                api_key=api_key,
                model=openai_model,
                base_url=base_url,
                temperature=0.7,
                system_prompt="""
                You are an expert travel assistant specializing in trip planning, destination information, 
                and travel recommendations. Your goal is to help users plan enjoyable, safe, and 
                realistic trips based on their preferences and constraints.
                
                When providing information:
                - Be specific and practical with your advice
                - Consider seasonality, budget constraints, and travel logistics
                - Highlight cultural experiences and authentic local activities
                - Include practical travel tips relevant to the destination
                - Format information clearly with headings and bullet points when appropriate
                
                For itineraries:
                - Create realistic day-by-day plans that account for travel time between attractions
                - Balance popular tourist sites with off-the-beaten-path experiences
                - Include approximate timing and practical logistics
                - Suggest meal options highlighting local cuisine
                - Consider weather, local events, and opening hours in your planning
                
                Always maintain a helpful, enthusiastic but realistic tone and acknowledge 
                any limitations in your knowledge when appropriate.
                """
            )
        
        def plan_trip(self, destination, duration=3, interests=None, budget=None):
            """
            Create a custom trip itinerary.
            
            Args:
                destination: Travel destination city/country
                duration: Number of days for the trip (default: 3)
                interests: Optional list of traveler interests
                budget: Optional budget level (low, medium, high)
                
            Returns:
                A detailed day-by-day itinerary
            """
            # Format query for OpenAI
            if interests and budget:
                query = f"Create a detailed {duration}-day itinerary for {destination}. Interests: {interests}. Budget: {budget}."
            elif interests:
                query = f"Create a detailed {duration}-day itinerary for {destination}. Interests: {interests}."
            elif budget:
                query = f"Create a detailed {duration}-day itinerary for {destination}. Budget: {budget}."
            else:
                query = f"Create a detailed {duration}-day itinerary for {destination}."
            
            # Get response from OpenAI
            from python_a2a import Message, TextContent, MessageRole
            message = Message(content=TextContent(text=query), role=MessageRole.USER)
            response = self.openai.handle_message(message)
            
            # Add some travel tips from our knowledge base
            tips = self.kb.get_travel_tips(3)
            tips_text = "\n\nUSEFUL TRAVEL TIPS:\n" + "\n".join(f"- {tip}" for tip in tips)
            
            return response.content.text + tips_text
        
        def get_travel_info(self, country, topic):
            """
            Get specific travel information for a destination.
            
            Args:
                country: Destination country
                topic: Information topic (visa, health, safety, etc.)
                
            Returns:
                Relevant travel information
            """
            # Check for visa information from our knowledge base
            if "visa" in topic.lower():
                kb_info = self.kb.get_visa_info(country)
                # Format query for OpenAI to expand on our knowledge
                query = f"What are the visa requirements for visiting {country}? Add more details to this information: {kb_info}"
            elif "health" in topic.lower():
                kb_info = self.kb.get_health_advisory()
                query = f"What health considerations should I know when visiting {country}? Consider this advice: {kb_info}"
            else:
                # General query for other topics
                query = f"What should I know about {topic} when traveling to {country}?"
            
            # Get response from OpenAI
            from python_a2a import Message, TextContent, MessageRole
            message = Message(content=TextContent(text=query), role=MessageRole.USER)
            response = self.openai.handle_message(message)
            
            return response.content.text
        
        def get_recommendations(self, destination, category, preferences=None):
            """
            Get personalized travel recommendations.
            
            Args:
                destination: Travel destination
                category: Type of recommendation (activities, restaurants, hotels, etc.)
                preferences: Optional preferences for more tailored recommendations
                
            Returns:
                A list of recommendations with descriptions
            """
            # Format query for OpenAI
            if preferences:
                query = f"Recommend {category} in {destination} suitable for someone who likes {preferences}."
            else:
                query = f"Recommend the best {category} in {destination}."
            
            # Get response from OpenAI
            from python_a2a import Message, TextContent, MessageRole
            message = Message(content=TextContent(text=query), role=MessageRole.USER)
            response = self.openai.handle_message(message)
            
            return response.content.text
        
        def handle_task(self, task):
            """Process incoming tasks by identifying intent and routing to the appropriate skill"""
            try:
                # Extract message text from task
                message_data = task.message or {}
                content = message_data.get("content", {})
                text = content.get("text", "") if isinstance(content, dict) else ""
                
                # Determine the intent of the message
                intent, params = self._analyze_intent(text)
                
                # Route to the appropriate skill based on intent
                if intent == "trip_planning":
                    response_text = self.plan_trip(**params)
                elif intent == "travel_info":
                    response_text = self.get_travel_info(**params)
                elif intent == "recommendations":
                    response_text = self.get_recommendations(**params)
                else:
                    # For general inquiries, pass directly to OpenAI
                    from python_a2a import Message, TextContent, MessageRole
                    message = Message(content=TextContent(text=text), role=MessageRole.USER)
                    response = self.openai.handle_message(message)
                    response_text = response.content.text
                
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
        
        def _analyze_intent(self, text):
            """
            Analyze the user's message to determine intent and extract parameters.
            This uses simple pattern matching, but could be enhanced with NLP in a real system.
            """
            text_lower = text.lower()
            
            # Extract potential destination
            destination_match = re.search(r"(?:in|to|for|visit(?:ing)?)\s+([A-Z][a-zA-Z\s]+)(?:\.|\?|$|\s+)", text)
            destination = destination_match.group(1) if destination_match else None
            
            # Extract potential duration
            duration_match = re.search(r"(\d+)[\s-]*(day|week|month)", text_lower)
            duration = None
            if duration_match:
                value = int(duration_match.group(1))
                unit = duration_match.group(2)
                if unit == "week":
                    duration = value * 7
                elif unit == "month":
                    duration = value * 30
                else:
                    duration = value
            
            # Check for trip planning intent
            if any(phrase in text_lower for phrase in ["plan", "itinerary", "schedule", "trip to"]):
                params = {"destination": destination or "popular destination"}
                if duration:
                    params["duration"] = duration
                
                # Extract interests
                interests_match = re.search(r"(?:interest(?:ed)? in|enjoy|like)\s+([^.?!]+)", text_lower)
                if interests_match:
                    params["interests"] = interests_match.group(1).strip()
                
                # Extract budget
                if "budget" in text_lower:
                    budget_match = re.search(r"(?:low|medium|high|cheap|luxury)\s+budget", text_lower)
                    if budget_match:
                        params["budget"] = budget_match.group(0)
                    
                return "trip_planning", params
            
            # Check for travel information intent
            elif any(phrase in text_lower for phrase in ["visa", "require", "health", "safety", "currency", "language"]):
                # Identify the information topic
                topics = ["visa", "health", "safety", "currency", "language", "transport", "weather"]
                topic = next((t for t in topics if t in text_lower), "general information")
                
                return "travel_info", {
                    "country": destination or "general",
                    "topic": topic
                }
            
            # Check for recommendations intent
            elif any(phrase in text_lower for phrase in ["recommend", "suggest", "best", "top", "where to"]):
                # Identify the category
                categories = ["restaurant", "hotel", "attraction", "activity", "shop", "museum", "beach", "park"]
                category = next((c for c in categories if c in text_lower or c+"s" in text_lower), "attractions")
                
                params = {
                    "destination": destination or "popular destination",
                    "category": category
                }
                
                # Extract preferences
                pref_match = re.search(r"(?:who likes|prefer|into|fan of)\s+([^.?!]+)", text_lower)
                if pref_match:
                    params["preferences"] = pref_match.group(1).strip()
                
                return "recommendations", params
            
            # Default to general inquiry
            return "general", {}
    
    # Create the travel planner
    travel_planner = TravelPlanner(kb, model_name,base_url,api_key)
    
    # Print the agent information
    print("\n=== Travel Planner Information ===")
    print(f"Name: {travel_planner.agent_card.name}")
    print(f"Description: {travel_planner.agent_card.description}")
    print(f"URL: {travel_planner.agent_card.url}")
    print(f"OpenAI Model: {model_name}")
    
    print("\n=== Available Skills ===")
    for skill in travel_planner.agent_card.skills:
        print(f"- {skill.name}: {skill.description}")
    
    # Start test client in a separate process if testing is enabled
    client_process = None
    if not args.no_test:
        client_process = multiprocessing.Process(target=test_client, args=(port,))
        client_process.start()
    
    # Start the server
    print(f"\n🚀 Starting Travel Planner on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        run_server(travel_planner, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        if "Address already in use" in str(e):
            print(f"\nPort {port} is already in use. Try using a different port:")
            print(f"    python openai_travel_planner.py --port {port + 1}")
        return 1
    finally:
        # Clean up client process
        if client_process:
            client_process.terminate()
            client_process.join()
    
    print("\n=== What's Next? ===")
    print("1. Try the 'openai_mcp_agent.py' example to add tool capabilities")
    print("2. Try the 'knowledge_base.py' example to create a system with your own data")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)