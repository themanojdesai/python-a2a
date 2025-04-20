#!/usr/bin/env python
"""
OpenAI MCP Agent Example

A compact example showing how to create an OpenAI-powered agent with MCP tools.
This agent combines the power of GPT with external tools for calculations,
conversions, and getting real-time information.

To run:
    export OPENAI_API_KEY=your_api_key
    python openai_mcp_agent.py --auto-mcp

Requirements:
    pip install "python-a2a[openai,mcp,server]"
"""

import os
import sys
import time
import socket
import argparse
import multiprocessing
from datetime import datetime

# Check for OpenAI API key
if not os.environ.get("OPENAI_API_KEY"):
    print("❌ OPENAI_API_KEY environment variable not set!")
    print("    export OPENAI_API_KEY=your_api_key")
    sys.exit(1)

# Quick dependency check
try:
    import python_a2a
    import openai
    import flask
    import fastapi
    import uvicorn
except ImportError as e:
    print(f"❌ Missing dependency: {e.name}")
    print("    pip install \"python-a2a[openai,mcp,server]\"")
    sys.exit(1)

from python_a2a import OpenAIA2AServer, A2AServer, run_server, TaskStatus, TaskState
from python_a2a import AgentCard, AgentSkill, A2AClient
from python_a2a.mcp import FastMCP, text_response, create_fastapi_app
import requests

# Find available port
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
    return start_port + 100  # Return something far away as fallback

# Parse arguments
parser = argparse.ArgumentParser(description="OpenAI MCP Agent Example")
parser.add_argument("--port", type=int, default=None, help="Agent port (default: auto)")
parser.add_argument("--mcp-port", type=int, default=None, help="MCP port (default: auto)")
parser.add_argument("--no-auto-mcp", action="store_true", help="Don't auto-start MCP server")
parser.add_argument("--no-test", action="store_true", help="Don't run test queries")
parser.add_argument("--model", default="gpt-4o-mini", help="OpenAI model to use")
args = parser.parse_args()

# Auto-select ports if not specified
if args.port is None:
    args.port = find_available_port()
    print(f"🔍 Auto-selected agent port: {args.port}")
else:
    print(f"🔍 Using specified agent port: {args.port}")

if args.mcp_port is None:
    args.mcp_port = find_available_port(args.port + 1)
    print(f"🔍 Auto-selected MCP port: {args.mcp_port}")
else:
    print(f"🔍 Using specified MCP port: {args.mcp_port}")

def start_mcp_server(port):
    """Start a simple MCP server with useful tools"""
    # Create MCP server
    tools = FastMCP(name="Utility Tools", description="Basic utility tools", version="1.0.0")
    
    # Add calculator tool
    @tools.tool(name="calculate", description="Perform math calculations")
    def calculate(expression: str):
        """Safely evaluate a math expression"""
        try:
            # Use safer eval with limited globals/locals
            result = eval(expression, {"__builtins__": {}}, 
                          {"abs": abs, "max": max, "min": min, "pow": pow,
                           "round": round, "sum": sum})
            return text_response(f"{expression} = {result}")
        except Exception as e:
            return text_response(f"Error calculating {expression}: {str(e)}")
    
    # Add time tool
    @tools.tool(name="get_time", description="Get current date and time")
    def get_time():
        """Get current date and time information"""
        now = datetime.now()
        return text_response(
            f"Current time: {now.strftime('%H:%M:%S')}\n"
            f"Today's date: {now.strftime('%A, %B %d, %Y')}"
        )
    
    # Start the server
    app = create_fastapi_app(tools)
    uvicorn.run(app, host="localhost", port=port)

# Create a combined OpenAI+MCP agent
class OpenAIMCPAgent(A2AServer):
    """OpenAI-powered agent with direct MCP tool access"""
    
    def __init__(self, agent_card, openai_model, mcp_url=None):
        super().__init__(agent_card=agent_card)
        self.mcp_url = mcp_url
        
        # Setup OpenAI client but we'll call it directly
        self.openai_client = OpenAIA2AServer(
            api_key=os.environ["OPENAI_API_KEY"],
            model=openai_model,
            temperature=0.7,
            system_prompt=(
                "You are a helpful AI assistant with access to external tools. "
                "When asked questions about calculations or time, use the appropriate tool. "
                "For calculations, format expressions as valid Python (5*3+2)."
            )
        )
    
    def handle_task(self, task):
        """Handle incoming tasks, routing to OpenAI and tools as needed"""
        try:
            # Extract message text
            message_data = task.message or {}
            content = message_data.get("content", {})
            text = content.get("text", "") if isinstance(content, dict) else ""
            
            # Default text to send to OpenAI
            prompt_text = text
            tool_result = None
            
            # Check if we should use a tool based on simple keyword matching
            text_lower = text.lower()
            
            # Handle calculation requests
            if any(kw in text_lower for kw in ["calculate", "compute", "what is", "what's", "solve"]) and \
               any(op in text for op in ["+", "-", "*", "/", "^"]):
                # Extract the mathematical expression
                import re
                # Look for an expression with numbers and operators
                match = re.search(r'[0-9]+\s*[\+\-\*/\^]+\s*[0-9]+[\+\-\*/\^0-9\s\.]*', text)
                if match:
                    expression = match.group(0).replace("^", "**").strip()
                    try:
                        if self.mcp_url:
                            # Call the calculate tool
                            tool_result = self.call_tool("calculate", {"expression": expression})
                            prompt_text = f"{text}\n\nI'll use a calculator tool to solve this.\nCalculator result: {tool_result}"
                    except Exception as e:
                        print(f"Error calling calculator tool: {e}")
            
            # Handle time/date requests
            elif any(kw in text_lower for kw in ["time", "date", "today", "day"]):
                try:
                    if self.mcp_url:
                        # Call the time tool
                        tool_result = self.call_tool("get_time", {})
                        prompt_text = f"{text}\n\nI'll check the current time for you.\nTime result: {tool_result}"
                except Exception as e:
                    print(f"Error calling time tool: {e}")
            
            # Get response from OpenAI
            from python_a2a import Message, TextContent, MessageRole
            
            # Create message for OpenAI
            message = Message(
                content=TextContent(text=prompt_text),
                role=MessageRole.USER
            )
            
            # Get response from OpenAI
            response = self.openai_client.handle_message(message)
            
            # Create response artifact
            response_text = response.content.text
            
            # Update with tool result if we didn't include it in prompt
            if tool_result and "Tool result" not in response_text:
                response_text = f"{response_text}\n\n(Used tool: {tool_result})"
            
            task.artifacts = [{
                "parts": [{"type": "text", "text": response_text}]
            }]
            task.status = TaskStatus(state=TaskState.COMPLETED)
            
            return task
            
        except Exception as e:
            print(f"Error handling task: {e}")
            error_message = f"Sorry, I encountered an error: {str(e)}"
            task.artifacts = [{
                "parts": [{"type": "text", "text": error_message}]
            }]
            task.status = TaskStatus(state=TaskState.FAILED)
            return task
    
    def call_tool(self, tool_name, parameters):
        """Call an MCP tool directly using HTTP requests"""
        if not self.mcp_url:
            raise ValueError("No MCP URL configured")
        
        # Build the URL for the tool
        tool_url = f"{self.mcp_url}/tools/{tool_name}"
        
        # Make the request
        response = requests.post(
            tool_url, 
            json=parameters,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        
        # Parse and extract text content
        result = response.json()
        if "content" in result and len(result["content"]) > 0:
            if "text" in result["content"][0]:
                return result["content"][0]["text"]
        
        return str(result)

def test_agent(port):
    """Run a series of test queries against the agent"""
    time.sleep(3)  # Wait for server to fully start
    
    print("\n🧪 Testing the agent with sample queries...")
    client = A2AClient(f"http://localhost:{port}")
    
    test_queries = [
        "What is 1567 * 423?",
        "What time is it now?",
        "Tell me about Mars in one paragraph"
    ]
    
    for query in test_queries:
        try:
            print(f"\n💬 Query: {query}")
            response = client.ask(query)
            print(f"🤖 Response: {response}")
            time.sleep(1)  # Pause between queries
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n✅ Test completed!")
    print(f"🔗 Agent running at http://localhost:{port}")
    print("🛑 Press Ctrl+C in the server terminal to stop")

def main():
    # Start MCP server if not explicitly disabled
    mcp_server_process = None
    mcp_url = f"http://localhost:{args.mcp_port}"
    
    if not args.no_auto_mcp:
        print(f"🔧 Starting MCP server on port {args.mcp_port}...")
        mcp_server_process = multiprocessing.Process(
            target=start_mcp_server, 
            args=(args.mcp_port,)
        )
        mcp_server_process.start()
        time.sleep(1)  # Give the server time to start
    
    try:
        # Create agent card
        agent_card = AgentCard(
            name="OpenAI + MCP Agent",
            description=f"GPT-powered agent with calculation and time tools",
            url=f"http://localhost:{args.port}",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="GPT-Powered Responses",
                    description="Answer questions using OpenAI's GPT",
                    examples=["Tell me about quantum physics"]
                ),
                AgentSkill(
                    name="Calculations",
                    description="Perform calculations using the calculator tool",
                    examples=["Calculate 1567 * 423", "What is 15% of 340?"]
                ),
                AgentSkill(
                    name="Time Information",
                    description="Get current date and time information",
                    examples=["What time is it?", "What day is today?"]
                ),
            ]
        )
        
        # Create the agent
        print(f"🤖 Starting OpenAI+MCP agent with model {args.model}...")
        agent = OpenAIMCPAgent(
            agent_card=agent_card,
            openai_model=args.model,
            mcp_url=mcp_url if not args.no_auto_mcp else None
        )
        
        # Start test client process if testing is not disabled
        client_process = None
        if not args.no_test:
            client_process = multiprocessing.Process(
                target=test_agent,
                args=(args.port,)
            )
            client_process.start()
        
        # Run the server
        print(f"🚀 Server running at http://localhost:{args.port}")
        print("Example queries: 'What is 1567 * 423?', 'What time is it?', 'Tell me about Mars'")
        print("Press Ctrl+C to stop")
        
        run_server(agent, host="0.0.0.0", port=args.port)
        
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1
    finally:
        # Clean up processes
        if 'client_process' in locals() and client_process:
            client_process.terminate()
            client_process.join()
            
        if mcp_server_process:
            print("Stopping MCP server...")
            mcp_server_process.terminate()
            mcp_server_process.join()
    
    return 0

if __name__ == "__main__":
    sys.exit(main())