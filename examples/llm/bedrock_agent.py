# examples/llm/bedrock_agent.py
"""
Example of creating an A2A agent powered by AWS Bedrock.
"""

import os
import argparse
from python_a2a import BedrockA2AServer, run_server

def main():
    parser = argparse.ArgumentParser(description="Start an AWS Bedrock-powered A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5004, help="Port to listen on")
    parser.add_argument("--aws-access-key-id", help="AWS Access Key ID (or set AWS_ACCESS_KEY_ID env var)")
    parser.add_argument("--aws-secret-access-key", help="AWS Secret Access Key (or set AWS_SECRET_ACCESS_KEY env var)")
    parser.add_argument("--aws-region", help="AWS Region (or set AWS_REGION env var)")
    parser.add_argument("--model-id", default="anthropic.claude-3-7-sonnet-20250219-v1:0", 
                       help="Bedrock model ID to use")
    parser.add_argument("--temperature", type=float, default=0.7, help="Generation temperature")
    parser.add_argument("--system-prompt", 
                       default="You are a helpful assistant specialized in answering factual questions.",
                       help="System prompt for the agent")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Get AWS credentials from args or environment
    aws_access_key_id = args.aws_access_key_id or os.environ.get("AWS_ACCESS_KEY_ID")
    aws_secret_access_key = args.aws_secret_access_key or os.environ.get("AWS_SECRET_ACCESS_KEY")
    aws_region = args.aws_region or os.environ.get("AWS_REGION")
    
    if not all([aws_access_key_id, aws_secret_access_key, aws_region]):
        print("Error: AWS credentials are required. Provide them with --aws-access-key-id, --aws-secret-access-key, "
              "--aws-region or set the corresponding environment variables.")
        return 1
    
    # Create the Bedrock agent
    agent = BedrockA2AServer(
        aws_access_key_id=aws_access_key_id,
        aws_secret_access_key=aws_secret_access_key,
        aws_region=aws_region,
        model_id=args.model_id,
        temperature=args.temperature,
        system_prompt=args.system_prompt
    )
    
    print(f"Starting AWS Bedrock A2A Agent on http://{args.host}:{args.port}/a2a")
    print(f"Model: {args.model_id}")
    print(f"Region: {aws_region}")
    print(f"System prompt: {args.system_prompt}")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main() 