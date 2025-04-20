#!/usr/bin/env python
"""
AI-Powered Agent Workflow Example

This example demonstrates how to use Python A2A with OpenAI and Anthropic agents
to create powerful AI-driven workflows that can:
- Leverage specialized language models for different tasks
- Intelligently route requests to the appropriate AI model
- Use models with different capabilities and costs effectively

To run:
    python agents_workflow.py [--model MODEL_NAME] [--query QUESTION]

Requirements:
    pip install "python-a2a[all,openai,anthropic]"

Notes:
    - You need to set OPENAI_API_KEY and/or ANTHROPIC_API_KEY environment variables
    - Either key works, the example will use the available model(s)
"""

import sys
import os
import argparse
import time
import json
from typing import List, Dict, Any, Optional

from python_a2a import (
    Flow, AgentNetwork, A2AServer, AgentCard, AgentSkill,
    Message, TextContent, MessageRole,
    Task, TaskStatus, TaskState
)


def check_api_keys():
    """Check which API keys are available and return available models."""
    available_models = []
    
    # Check for OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        try:
            # Try to import OpenAI client to confirm it's installed
            from python_a2a.client.llm import OpenAIA2AClient
            available_models.append(("openai", "gpt-4"))
            available_models.append(("openai", "gpt-3.5-turbo"))
            print("✓ OpenAI API key found")
        except ImportError:
            print("✗ OpenAI package not installed. Install with: pip install 'python-a2a[openai]'")
    else:
        print("✗ OpenAI API key not found. Set the OPENAI_API_KEY environment variable.")
    
    # Check for Anthropic API key
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        try:
            # Try to import Anthropic client to confirm it's installed
            from python_a2a.client.llm import AnthropicA2AClient
            available_models.append(("anthropic", "claude-3-opus-20240229"))
            available_models.append(("anthropic", "claude-3-sonnet-20240229"))
            print("✓ Anthropic API key found")
        except ImportError:
            print("✗ Anthropic package not installed. Install with: pip install 'python-a2a[anthropic]'")
    else:
        print("✗ Anthropic API key not found. Set the ANTHROPIC_API_KEY environment variable.")
    
    return available_models


def create_llm_agent(provider, model, system_prompt=None):
    """Create an LLM agent from specified provider and model."""
    if provider == "openai":
        try:
            from python_a2a.client.llm import OpenAIA2AClient
            
            api_key = os.environ.get("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OpenAI API key not found in environment variables")
            
            # Create an OpenAI agent with the specified model
            agent = OpenAIA2AClient(
                api_key=api_key,
                model=model,
                temperature=0.7,
                # Add system prompt if provided
                system_prompt=system_prompt or "You are a helpful AI assistant."
            )
            
            return agent
            
        except ImportError:
            raise ImportError("OpenAI package not installed. Install with: pip install 'python-a2a[openai]'")
            
    elif provider == "anthropic":
        try:
            from python_a2a.client.llm import AnthropicA2AClient
            
            api_key = os.environ.get("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("Anthropic API key not found in environment variables")
            
            # Create an Anthropic agent with the specified model
            agent = AnthropicA2AClient(
                api_key=api_key,
                model=model,
                temperature=0.7,
                max_tokens=1000,
                # Add system prompt if provided
                system_prompt=system_prompt or "You are a helpful AI assistant."
            )
            
            return agent
            
        except ImportError:
            raise ImportError("Anthropic package not installed. Install with: pip install 'python-a2a[anthropic]'")
            
    else:
        raise ValueError(f"Unsupported provider: {provider}")


def extract_entities(text):
    """Extract entities like people, places, and organizations from text."""
    # This would normally use an NLP model, but we'll simulate it
    entities = []
    
    # Simple pattern matching for people (just for demonstration)
    people = ["John", "Mary", "James", "David", "Sarah", "Michael", "Elizabeth"]
    for person in people:
        if person in text:
            entities.append({"type": "PERSON", "text": person})
    
    # Simple pattern matching for places
    places = ["London", "New York", "Paris", "Tokyo", "Sydney", "Berlin", "Rome"]
    for place in places:
        if place in text:
            entities.append({"type": "PLACE", "text": place})
    
    # Simple pattern matching for organizations
    orgs = ["Google", "Microsoft", "Apple", "Amazon", "Facebook", "Netflix", "Tesla"]
    for org in orgs:
        if org in text:
            entities.append({"type": "ORGANIZATION", "text": org})
    
    return entities


def create_multi_agent_workflow(agents, query, task_type="general"):
    """
    Create a workflow that routes the query to the appropriate agent based on the task type.
    
    Args:
        agents: Dictionary mapping agent names to client objects
        query: User query to process
        task_type: Type of task (general, creative, technical, etc.)
        
    Returns:
        Flow object with the defined workflow
    """
    network = AgentNetwork()
    
    # Add each agent to the network
    for name, agent in agents.items():
        network.add(name, agent)
    
    # Create workflow with different branches based on task type
    flow = Flow(agent_network=network)
    
    # Define a workflow that routes to different agents based on task type
    if task_type == "creative":
        # Creative tasks go to Claude model if available
        if "claude" in agents:
            return (
                flow
                .ask("claude", query)
            )
        # Fall back to GPT-4 if Claude isn't available
        elif "gpt4" in agents:
            return (
                flow
                .ask("gpt4", query)
            )
        # Last resort is GPT-3.5
        else:
            return (
                flow
                .ask("gpt35", query)
            )
            
    elif task_type == "technical":
        # Technical tasks go to GPT-4 if available
        if "gpt4" in agents:
            return (
                flow
                .ask("gpt4", query)
            )
        # Fall back to Claude if GPT-4 isn't available
        elif "claude" in agents:
            return (
                flow
                .ask("claude", query)
            )
        # Last resort is GPT-3.5
        else:
            return (
                flow
                .ask("gpt35", query)
            )
            
    elif task_type == "analysis":
        # First, get entities from the query (simulated)
        entities = extract_entities(query)
        
        if entities:
            # If entities were found, create a more specific query
            entity_desc = ", ".join([f"{e['text']} ({e['type']})" for e in entities])
            enhanced_query = f"{query}\n\nPlease specifically address these entities in your response: {entity_desc}"
            
            # Send the enhanced query to a powerful model
            if "gpt4" in agents:
                return (
                    flow
                    .ask("gpt4", enhanced_query)
                )
            elif "claude" in agents:
                return (
                    flow
                    .ask("claude", enhanced_query)
                )
            else:
                return (
                    flow
                    .ask("gpt35", enhanced_query)
                )
        else:
            # No entities found, regular analysis
            if "gpt4" in agents:
                return (
                    flow
                    .ask("gpt4", query)
                )
            elif "claude" in agents:
                return (
                    flow
                    .ask("claude", query)
                )
            else:
                return (
                    flow
                    .ask("gpt35", query)
                )
    
    else:  # Default case for general tasks
        # For general tasks, first check the query complexity
        if len(query.split()) > 30:  # Longer, more complex queries
            # Use a more powerful model
            if "gpt4" in agents:
                return (
                    flow
                    .ask("gpt4", query)
                )
            elif "claude" in agents:
                return (
                    flow
                    .ask("claude", query)
                )
            else:
                return (
                    flow
                    .ask("gpt35", query)
                )
        else:  # Shorter, simpler queries
            # Use a faster, cheaper model
            if "gpt35" in agents:
                return (
                    flow
                    .ask("gpt35", query)
                )
            elif "claude" in agents:
                return (
                    flow
                    .ask("claude", query)
                )
            else:
                return (
                    flow
                    .ask("gpt4", query)
                )


def determine_task_type(query):
    """
    Determine the type of task based on the query.
    
    Args:
        query: User query to analyze
        
    Returns:
        Task type classification (general, creative, technical, analysis)
    """
    query = query.lower()
    
    # Creative tasks
    creative_keywords = [
        "write", "story", "poem", "creative", "imagine", "fiction", "narrative", 
        "compose", "invent", "art", "design", "generate ideas"
    ]
    
    # Technical tasks
    technical_keywords = [
        "code", "programming", "software", "algorithm", "function", "class",
        "technical", "engineering", "framework", "library", "api", "database"
    ]
    
    # Analysis tasks
    analysis_keywords = [
        "analyze", "analysis", "research", "compare", "evaluate", "assess",
        "trends", "data", "statistics", "study", "investigate", "report"
    ]
    
    # Count keyword matches
    creative_score = sum(1 for word in creative_keywords if word in query)
    technical_score = sum(1 for word in technical_keywords if word in query)
    analysis_score = sum(1 for word in analysis_keywords if word in query)
    
    # Determine task type based on highest score
    max_score = max(creative_score, technical_score, analysis_score)
    
    if max_score == 0:
        return "general"  # No strong matches, default to general
    elif max_score == creative_score:
        return "creative"
    elif max_score == technical_score:
        return "technical"
    else:
        return "analysis"


def main():
    """Run the AI-powered workflow example."""
    print("=== AI-Powered Agent Workflow Example ===\n")
    
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="AI-Powered Agent Workflow Example")
    parser.add_argument("--model", type=str, help="Specify a model to use (e.g., gpt-4, claude-3-opus)")
    parser.add_argument("--query", type=str, default="Explain how neural networks work and give me a simple Python example.", 
                        help="Query to send to the agents")
    args = parser.parse_args()
    
    # Check which API keys and models are available
    available_models = check_api_keys()
    
    if not available_models:
        print("\nError: No API keys found. Set either OPENAI_API_KEY or ANTHROPIC_API_KEY environment variables.")
        return 1
    
    # Initialize agents based on available models
    agents = {}
    
    # If user specified a model, try to use it
    if args.model:
        specific_model = None
        for provider, model in available_models:
            if args.model.lower() in model.lower():
                specific_model = (provider, model)
                break
        
        if specific_model:
            provider, model = specific_model
            print(f"\nUsing specified model: {model} from {provider}")
            
            try:
                # Create the agent with the specified model
                agent_name = f"{model.replace('-', '').replace('.', '')}"
                agents[agent_name] = create_llm_agent(provider, model)
            except Exception as e:
                print(f"Error creating agent with {model}: {e}")
                return 1
        else:
            print(f"\nSpecified model '{args.model}' not available or not supported.")
            print("Using available models instead.")
            # Fall through to use available models
    
    # If no specific model was requested or found, use available models
    if not agents:
        print("\nInitializing agents with available models:")
        
        # Start with more powerful models
        for provider, model in available_models:
            if "gpt-4" in model:
                print(f"- Adding {model} from {provider}")
                agents["gpt4"] = create_llm_agent(
                    provider, 
                    model,
                    "You are a very knowledgeable AI assistant with expertise in many domains."
                )
            elif "claude-3-opus" in model:
                print(f"- Adding {model} from {provider}")
                agents["claude"] = create_llm_agent(
                    provider, 
                    model,
                    "You are a very knowledgeable AI assistant with expertise in many domains."
                )
        
        # Add a faster model for simpler tasks if available
        for provider, model in available_models:
            if "gpt-3.5" in model:
                print(f"- Adding {model} from {provider}")
                agents["gpt35"] = create_llm_agent(
                    provider, 
                    model,
                    "You are a helpful AI assistant that provides concise responses."
                )
            elif "claude-3-sonnet" in model and "claude" not in agents:
                print(f"- Adding {model} from {provider}")
                agents["claude"] = create_llm_agent(
                    provider, 
                    model,
                    "You are a helpful AI assistant that provides concise responses."
                )
    
    if not agents:
        print("\nError: Failed to initialize any agents.")
        return 1
    
    # Get the query
    query = args.query
    print(f"\nQuery: {query}")
    
    # Determine task type
    task_type = determine_task_type(query)
    print(f"Detected task type: {task_type}\n")
    
    # Create workflow based on task type
    flow = create_multi_agent_workflow(agents, query, task_type)
    
    print("Executing workflow...")
    start_time = time.time()
    
    try:
        # Run the workflow
        result = flow.run_sync()
        
        # Calculate execution time
        execution_time = time.time() - start_time
        
        # Print the result
        print("\n=== Workflow Result ===")
        print(result)
        print(f"\nExecution completed in {execution_time:.2f} seconds")
        
    except Exception as e:
        print(f"\nError executing workflow: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())