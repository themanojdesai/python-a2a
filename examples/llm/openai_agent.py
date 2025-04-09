# examples/llm/openai_agent.py
"""
Example of creating an A2A agent powered by OpenAI.
"""

import os
import argparse
from python_a2a import OpenAIA2AServer, run_server

def main():
    parser = argparse.ArgumentParser(description="Start an OpenAI-powered A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5003, help="Port to listen on")
    parser.add_argument("--api-key", help="OpenAI API key (or set OPENAI_API_KEY env var)")
    parser.add_argument("--model", default="gpt-4", help="OpenAI model to use")
    parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    parser.add_argument("--system-prompt", 
                       default="You are a helpful assistant specialized in answering factual questions.",
                       help="System prompt for the agent")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Get API key from args or environment
    api_key = args.api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        print("Error: OpenAI API key is required. Provide it with --api-key or set the OPENAI_API_KEY environment variable.")
        return 1
    
    # Create the OpenAI agent
    agent = OpenAIA2AServer(
        api_key=api_key,
        model=args.model,
        temperature=args.temperature,
        system_prompt=args.system_prompt
    )
    
    print(f"Starting OpenAI A2A Agent on http://{args.host}:{args.port}/a2a")
    print(f"Model: {args.model}")
    print(f"System prompt: {args.system_prompt}")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()