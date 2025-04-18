"""
Example showing how to generate FastAPI-style documentation for an A2A agent.
"""

import os
from python_a2a import AgentCard, AgentSkill, generate_a2a_docs, generate_html_docs


def main():
    # Create an agent card with skills
    agent_card = AgentCard(
        name="Travel Assistant API",
        description="Get travel information and recommendations",
        url="http://localhost:5000",
        version="1.0.0",
        capabilities={
            "streaming": True,
            "pushNotifications": False,
            "stateTransitionHistory": True
        },
        skills=[
            AgentSkill(
                name="Get Weather",
                description="Get weather information for a destination",
                tags=["weather", "travel"],
                examples=["What's the weather in Rome?", "Weather forecast for Tokyo"]
            ),
            AgentSkill(
                name="Find Attractions",
                description="Find popular attractions at a destination",
                tags=["attractions", "tourism", "travel"],
                examples=["Top attractions in Paris", "Things to do in New York"]
            ),
            AgentSkill(
                name="Get Flight Info",
                description="Get flight information between locations",
                tags=["flights", "travel"],
                examples=["Flights from London to Barcelona", "Flight options to Tokyo"]
            )
        ]
    )
    
    # Create output directory
    output_dir = "docs"
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate OpenAPI specification
    print("Generating OpenAPI specification...")
    spec = generate_a2a_docs(agent_card, output_dir)
    print(f"OpenAPI specification saved to {output_dir}/openapi.json")
    
    # Generate HTML documentation
    print("Generating HTML documentation...")
    html = generate_html_docs(spec)
    
    # Save HTML to file
    html_path = os.path.join(output_dir, "index.html")
    with open(html_path, "w") as f:
        f.write(html)
    
    print(f"HTML documentation saved to {html_path}")
    print(f"\nTo view the documentation in a browser, open:\n  file://{os.path.abspath(html_path)}")


if __name__ == "__main__":
    main()