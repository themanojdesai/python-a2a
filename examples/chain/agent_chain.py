# examples/chain/agent_chain.py
"""
An example showing how to chain multiple A2A agents together to solve a complex task.
"""

import argparse
import json
from python_a2a import A2AClient, Message, TextContent, MessageRole
from python_a2a.utils import pretty_print_message, pretty_print_conversation

def main():
    parser = argparse.ArgumentParser(description="Chain multiple A2A agents")
    parser.add_argument("--weather-endpoint", required=True, help="Endpoint for weather agent")
    parser.add_argument("--planning-endpoint", required=True, help="Endpoint for planning agent")
    parser.add_argument("--location", default="New York", help="Location to plan a trip for")
    
    args = parser.parse_args()
    
    # Create clients for each agent
    weather_client = A2AClient(args.weather_endpoint)
    planning_client = A2AClient(args.planning_endpoint)
    
    print(f"Planning a trip to {args.location} using multiple agents...")
    print(f"Weather Agent: {args.weather_endpoint}")
    print(f"Planning Agent: {args.planning_endpoint}")
    print("-" * 50)
    
    # Step 1: Get weather information
    print("Step 1: Consulting weather agent...")
    weather_message = Message(
        content=TextContent(text=f"What's the weather like in {args.location}?"),
        role=MessageRole.USER
    )
    
    weather_response = weather_client.send_message(weather_message)
    print("Weather information received:")
    pretty_print_message(weather_response)
    
    # Step 2: Plan the trip using weather information
    print("\nStep 2: Consulting planning agent...")
    planning_message = Message(
        content=TextContent(
            text=f"Plan a trip to {args.location}. "
                 f"Weather information: {weather_response.content.text}"
        ),
        role=MessageRole.USER
    )
    
    planning_response = planning_client.send_message(planning_message)
    print("Trip plan received:")
    pretty_print_message(planning_response)
    
    print("\nFinal Result:")
    print("=" * 50)
    print(planning_response.content.text)
    print("=" * 50)
    
    print("\nThis example demonstrates how multiple specialized A2A agents can be chained together")
    print("to solve complex tasks that require different capabilities.")

if __name__ == "__main__":
    main()