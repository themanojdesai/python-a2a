#!/usr/bin/env python
"""
A2A Agent Discovery

This example demonstrates how to create an agent card that describes
your agent's capabilities and skills for discovery by other agents.
It also shows how to interpret agent cards from other agents.

To run:
    python agent_discovery.py

Requirements:
    pip install python-a2a
"""

import sys
import json
import os

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import python_a2a
        print("✅ python-a2a is installed correctly!")
        return True
    except ImportError:
        print("❌ python-a2a is not installed!")
        print("\nPlease install it with:")
        print("    pip install python-a2a")
        print("\nThen run this example again.")
        return False

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Import after checking dependencies
    from python_a2a import AgentCard, AgentSkill
    
    print("\n🌟 A2A Agent Discovery 🌟")
    print("This example shows how to create agent cards and skills for agent discovery.\n")
    
    # Create skills for the travel agent
    print("=== Creating Agent Skills ===")
    
    weather_skill = AgentSkill(
        name="Get Weather",
        description="Provides current weather for a location",
        tags=["weather", "forecast"],
        examples=[
            "What's the weather in New York?", 
            "Paris weather forecast"
        ]
    )
    print(f"Created skill: {weather_skill.name}")
    
    attractions_skill = AgentSkill(
        name="Find Attractions",
        description="Find popular attractions at a destination",
        tags=["travel", "tourism", "attractions"],
        examples=[
            "Top attractions in Tokyo", 
            "What to see in Rome?"
        ]
    )
    print(f"Created skill: {attractions_skill.name}")
    
    itinerary_skill = AgentSkill(
        name="Create Itinerary",
        description="Create a travel itinerary for a destination",
        tags=["travel", "planning", "itinerary"],
        examples=[
            "3-day itinerary for London", 
            "Plan a weekend in Barcelona"
        ]
    )
    print(f"Created skill: {itinerary_skill.name}")
    
    # Create an agent card
    print("\n=== Creating an Agent Card ===")
    agent_card = AgentCard(
        name="Travel Assistant",
        description="Your AI travel companion for planning perfect trips",
        url="http://localhost:5000",  # The URL where this agent would be hosted
        version="1.0.0",
        skills=[weather_skill, attractions_skill, itinerary_skill],
        capabilities={
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True
        },
        default_input_modes=["text/plain", "text/markdown"],
        default_output_modes=["text/plain", "text/markdown"],
        provider="A2A Examples",
        documentation_url="https://example.com/travel-assistant-docs"
    )
    
    print(f"Created agent card: {agent_card.name} v{agent_card.version}")
    print(f"Description: {agent_card.description}")
    print(f"Provider: {agent_card.provider}")
    print(f"Skills: {len(agent_card.skills)}")
    print(f"Capabilities: {', '.join(key for key, value in agent_card.capabilities.items() if value)}")
    
    # Convert agent card to JSON for storage or transmission
    agent_json = agent_card.to_json()
    
    # Save to file
    with open("agent_card.json", "w") as f:
        f.write(agent_json)
    print("\nSaved agent card to agent_card.json")
    
    # Demonstrate pretty printing of the agent card
    print("\n=== Agent Card as Pretty JSON ===")
    pretty_json = json.dumps(json.loads(agent_json), indent=2)
    print(pretty_json)
    
    # Demonstrate how to discover and analyze other agents
    print("\n=== Discovering Other Agents ===")
    
    # Create a second agent to demonstrate discovery
    restaurant_skill = AgentSkill(
        name="Find Restaurants",
        description="Find restaurants near a location",
        tags=["food", "restaurants"],
        examples=["Best restaurants in Paris", "Italian food in New York"]
    )
    
    review_skill = AgentSkill(
        name="Get Reviews",
        description="Get reviews for a restaurant",
        tags=["reviews", "ratings"],
        examples=["Reviews for Eiffel Tower Restaurant", "Ratings for Sushi Nakazawa"]
    )
    
    restaurant_agent = AgentCard(
        name="Restaurant Finder",
        description="Find and get reviews for restaurants worldwide",
        url="http://localhost:5001", 
        version="1.0.0",
        skills=[restaurant_skill, review_skill]
    )
    
    # Save restaurant agent card
    with open("restaurant_agent.json", "w") as f:
        f.write(restaurant_agent.to_json())
    
    # Demonstrate how to load and analyze agent cards
    print("\nLoading agent cards to analyze capabilities:")
    
    agents = []
    for filename in ["agent_card.json", "restaurant_agent.json"]:
        with open(filename, "r") as f:
            agent_data = json.load(f)
            loaded_agent = AgentCard.from_dict(agent_data)
            agents.append(loaded_agent)
            print(f"- Loaded {loaded_agent.name} with {len(loaded_agent.skills)} skills")
    
    # Show how to extract skills by tags
    print("\nFinding travel-related skills across all agents:")
    travel_skills = []
    for agent in agents:
        for skill in agent.skills:
            if any(tag in ["travel", "tourism"] for tag in skill.tags):
                travel_skills.append((agent.name, skill.name))
    
    for agent_name, skill_name in travel_skills:
        print(f"- {agent_name}: {skill_name}")
    
    # Show how to find capabilities
    print("\nFinding agents with streaming capability:")
    streaming_agents = [agent.name for agent in agents 
                        if agent.capabilities.get("streaming")]
    
    for agent_name in streaming_agents:
        print(f"- {agent_name}")
    
    # Create an HTML visualization (optional)
    print("\n=== Creating HTML Visualization ===")
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>A2A Agents Overview</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; }}
            .agent {{ border: 1px solid #ddd; margin: 10px; padding: 15px; border-radius: 5px; }}
            .skills {{ margin-left: 20px; }}
            .skill {{ background: #f5f5f5; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            .tag {{ background: #007bff; color: white; padding: 2px 6px; border-radius: 3px; font-size: 0.8em; margin-right: 5px; }}
            h1, h2, h3 {{ color: #333; }}
        </style>
    </head>
    <body>
        <h1>A2A Agents Overview</h1>
    """
    
    for agent in agents:
        html_content += f"""
        <div class="agent">
            <h2>{agent.name} v{agent.version}</h2>
            <p>{agent.description}</p>
            <p><strong>URL:</strong> {agent.url}</p>
            <p><strong>Provider:</strong> {agent.provider or "Not specified"}</p>
            
            <h3>Skills:</h3>
            <div class="skills">
        """
        
        for skill in agent.skills:
            tags_html = "".join([f'<span class="tag">{tag}</span>' for tag in skill.tags])
            examples_html = ""
            if skill.examples:
                examples_html = "<ul>" + "".join([f"<li>{example}</li>" for example in skill.examples]) + "</ul>"
            
            html_content += f"""
                <div class="skill">
                    <h4>{skill.name}</h4>
                    <p>{skill.description}</p>
                    <p>Tags: {tags_html}</p>
                    {examples_html}
                </div>
            """
        
        html_content += """
            </div>
        </div>
        """
    
    html_content += """
    </body>
    </html>
    """
    
    with open("agents_overview.html", "w") as f:
        f.write(html_content)
    
    print("Created HTML visualization in agents_overview.html")
    
    # Try to automatically open the HTML file in a browser
    try:
        import webbrowser
        webbrowser.open('file://' + os.path.realpath("agents_overview.html"))
        print("Opening visualization in your web browser...")
    except:
        print("Created HTML visualization. Open agents_overview.html in your browser to view it.")
    
    print("\n=== What's Next? ===")
    print("1. Try 'tasks.py' to learn about handling A2A tasks")
    print("2. Try 'agent_skills.py' to learn about the @skill decorator")
    print("3. Try 'simple_server.py' to create a server with this agent card")
    
    print("\n🎉 You've learned how to work with A2A agent discovery! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)