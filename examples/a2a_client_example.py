"""
Example A2A client usage with python-a2a.
"""

from python_a2a import A2AClient


def main():
    # Create a client connected to an A2A-compatible agent
    # Make sure to use the correct port where your server is running
    client = A2AClient("http://localhost:5001")
    
    # Print agent information
    print(f"Connected to: {client.agent_card.name}")
    print(f"Description: {client.agent_card.description}")
    print(f"Version: {client.agent_card.version}")
    print(f"Capabilities: {client.agent_card.capabilities}")
    
    if hasattr(client.agent_card, 'skills') and client.agent_card.skills:
        print("\nAvailable skills:")
        for skill in client.agent_card.skills:
            print(f"  - {skill.name}: {skill.description}")
    
    print("\n" + "-" * 50)
    
    # Basic usage: ask a question
    print("\nAsking a question:")
    response = client.ask("Hello, A2A!")
    print(f"Response: {response}")
    
    print("\nDemo completed!")


if __name__ == "__main__":
    main()