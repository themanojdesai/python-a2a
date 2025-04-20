#!/usr/bin/env python
"""
MCP Agent Example

This example demonstrates how to create an A2A agent that can use MCP tools.
It shows how to connect to MCP servers and use their tools to extend the
agent's capabilities.

To run:
    python mcp_agent.py --auto-mcp

Requirements:
    pip install "python-a2a[mcp,server]"
"""

import sys
import os
import argparse
import socket
import time
import multiprocessing
from datetime import datetime
import re
import requests

# Mock data for direct implementations
MOCK_WEATHER_DATA = {
    "new york": {"condition": "Partly Cloudy", "temperature": 72, "humidity": 65},
    "london": {"condition": "Rainy", "temperature": 60, "humidity": 80},
    "tokyo": {"condition": "Sunny", "temperature": 75, "humidity": 60},
    "paris": {"condition": "Clear", "temperature": 68, "humidity": 55},
    "sydney": {"condition": "Sunny", "temperature": 80, "humidity": 45}
}

# Conversion factors for direct implementations
CONVERSION_FACTORS = {
    ("km", "miles"): 0.621371,
    ("miles", "km"): 1.60934,
    ("meters", "feet"): 3.28084,
    ("feet", "meters"): 0.3048,
    ("kg", "pounds"): 2.20462,
    ("pounds", "kg"): 0.453592,
}

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import python_a2a
    except ImportError:
        missing_deps.append("python-a2a")
    
    try:
        import flask
    except ImportError:
        missing_deps.append("flask")
    
    try:
        import fastapi
    except ImportError:
        missing_deps.append("fastapi")
    
    try:
        import uvicorn
    except ImportError:
        missing_deps.append("uvicorn")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required dependencies:")
        print("    pip install \"python-a2a[mcp,server]\"")
        print("\nThen run this example again.")
        return False
    
    print("✅ All dependencies are installed correctly!")
    return True

def find_available_port(start_port=5000, max_tries=10):
    """Find an available port starting from start_port"""
    for port in range(start_port, start_port + max_tries):
        try:
            # Try to create a socket on the port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            # Port is already in use, try the next one
            continue
    
    # If we get here, no ports were available
    print(f"⚠️  Could not find an available port in range {start_port}-{start_port + max_tries - 1}")
    return start_port  # Return the start port as default

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="MCP Agent Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the A2A agent on (default: auto-select)"
    )
    parser.add_argument(
        "--mcp-port", type=int, default=None,
        help="Port of the MCP server to connect to (default: auto-select)"
    )
    parser.add_argument(
        "--auto-mcp", action="store_true",
        help="Automatically start an MCP server with tools"
    )
    return parser.parse_args()

def start_mcp_server(port):
    """Start an MCP server with utility tools"""
    from python_a2a.mcp import FastMCP, text_response, create_fastapi_app
    import uvicorn
    
    # Create an MCP server with utility tools
    utility_mcp = FastMCP(
        name="Utility Tools",
        description="A collection of useful utility tools",
        version="1.0.0"
    )
    
    # 1. Calculator Tool
    @utility_mcp.tool(
        name="calculate",
        description="Perform math operations on two numbers"
    )
    def calculate(operation: str, a: float, b: float):
        """
        Perform a math operation on two numbers.
        
        Args:
            operation: Operation to perform (add, subtract, multiply, divide)
            a: First number
            b: Second number
            
        Returns:
            Result of the calculation
        """
        if operation == "add":
            result = a + b
            return text_response(f"{a} + {b} = {result}")
        
        elif operation == "subtract":
            result = a - b
            return text_response(f"{a} - {b} = {result}")
        
        elif operation == "multiply":
            result = a * b
            return text_response(f"{a} * {b} = {result}")
        
        elif operation == "divide":
            if b == 0:
                return text_response("Error: Cannot divide by zero")
            result = a / b
            return text_response(f"{a} / {b} = {result}")
        
        else:
            return text_response(f"Error: Unknown operation '{operation}'")
    
    # 2. Unit Converter Tool
    @utility_mcp.tool(
        name="convert_units",
        description="Convert between different units of measurement"
    )
    def convert_units(value: float, from_unit: str, to_unit: str):
        """
        Convert a value from one unit to another.
        
        Args:
            value: The value to convert
            from_unit: The source unit
            to_unit: The target unit
            
        Returns:
            The converted value
        """
        # Unit conversion factors
        conversions = {
            ("km", "miles"): 0.621371,
            ("miles", "km"): 1.60934,
            ("meters", "feet"): 3.28084,
            ("feet", "meters"): 0.3048,
            ("kg", "pounds"): 2.20462,
            ("pounds", "kg"): 0.453592,
        }
        
        # Temperature conversions (special case)
        def c_to_f(c):
            return c * 9/5 + 32
            
        def f_to_c(f):
            return (f - 32) * 5/9
        
        # Normalize units
        from_unit = from_unit.lower().rstrip("s")  # Remove plural 's'
        to_unit = to_unit.lower().rstrip("s")  # Remove plural 's'
        
        # Handle temperature conversions
        if from_unit in ["celsius", "c"] and to_unit in ["fahrenheit", "f"]:
            result = c_to_f(value)
            return text_response(f"{value}°C = {result:.2f}°F")
        
        if from_unit in ["fahrenheit", "f"] and to_unit in ["celsius", "c"]:
            result = f_to_c(value)
            return text_response(f"{value}°F = {result:.2f}°C")
        
        # Handle regular conversions
        conversion_key = (from_unit, to_unit)
        if conversion_key in conversions:
            factor = conversions[conversion_key]
            result = value * factor
            return text_response(f"{value} {from_unit} = {result:.2f} {to_unit}")
        
        # Unknown conversion
        return text_response(f"Sorry, I don't know how to convert from {from_unit} to {to_unit}")
    
    # 3. Weather Information Tool
    @utility_mcp.tool(
        name="get_weather",
        description="Get current weather for a location"
    )
    def get_weather(location: str):
        """
        Get the current weather for a location.
        
        Args:
            location: The city name
            
        Returns:
            Current weather information
        """
        # Mock weather data for demo purposes
        weather_data = {
            "new york": {"condition": "Partly Cloudy", "temperature": 72, "humidity": 65},
            "london": {"condition": "Rainy", "temperature": 60, "humidity": 80},
            "tokyo": {"condition": "Sunny", "temperature": 75, "humidity": 60},
            "paris": {"condition": "Clear", "temperature": 68, "humidity": 55},
            "sydney": {"condition": "Sunny", "temperature": 80, "humidity": 45}
        }
        
        # Normalize location name
        location_key = location.lower()
        
        # Get weather data
        if location_key in weather_data:
            data = weather_data[location_key]
            response = (
                f"Current weather in {location.title()}:\n"
                f"Condition: {data['condition']}\n"
                f"Temperature: {data['temperature']}°F\n"
                f"Humidity: {data['humidity']}%"
            )
            return text_response(response)
        else:
            # Return default data for unknown locations
            return text_response(
                f"Weather data for {location} not found. Here's a default forecast:\n"
                f"Condition: Partly Cloudy\n"
                f"Temperature: 70°F\n"
                f"Humidity: 60%"
            )
    
    # 4. DateTime Tool
    @utility_mcp.tool(
        name="get_current_time",
        description="Get the current date and time information"
    )
    def get_current_time():
        """
        Get the current date and time information.
        
        Returns:
            Current date and time information
        """
        now = datetime.now()
        
        response = (
            f"Current Date and Time:\n"
            f"Date: {now.strftime('%B %d, %Y')}\n"
            f"Time: {now.strftime('%H:%M:%S')}\n"
            f"Day of Week: {now.strftime('%A')}\n"
            f"Timezone: {time.tzname[0]}"
        )
        return text_response(response)
    
    # Create FastAPI app from MCP server
    app = create_fastapi_app(utility_mcp)
    
    # Print server info
    print(f"🔌 Starting MCP server on http://localhost:{port}")
    
    # Run the server
    uvicorn.run(app, host="localhost", port=port)

def start_client_process(port):
    """Start a client process to test the agent"""
    from python_a2a import A2AClient
    import time
    
    # Wait a bit for the server to start
    time.sleep(2)
    
    try:
        # Connect to the server
        print(f"\n🔌 Connecting to A2A agent at: http://localhost:{port}")
        client = A2AClient(f"http://localhost:{port}")
        
        # Send some test messages
        test_questions = [
            "What's 15 * 27?",
            "Convert 5 kilometers to miles",
            "What's the weather in Tokyo?",
            "What time is it now?"
        ]
        
        for question in test_questions:
            print(f"\n💬 Question: {question}")
            try:
                # Use client.ask() which sends a simple text message
                response = client.ask(question)
                print(f"🤖 Response: {response}")
            except Exception as e:
                print(f"❌ Error: {e}")
                print("Check the server logs for details.")
            
            # Short pause between questions
            time.sleep(1)
        
        print("\n✅ Test completed successfully!")
        print("Press Ctrl+C in the server terminal to stop the server.")
        
    except Exception as e:
        print(f"\n❌ Error connecting to agent: {e}")

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Find available ports if none specified
    if args.port is None:
        agent_port = find_available_port()
        print(f"🔍 Auto-selected agent port: {agent_port}")
    else:
        agent_port = args.port
        print(f"🔍 Using specified agent port: {agent_port}")
    
    if args.auto_mcp and args.mcp_port is None:
        mcp_port = find_available_port(agent_port + 1)  # Try to find port after agent port
        print(f"🔍 Auto-selected MCP port: {mcp_port}")
    elif args.mcp_port is not None:
        mcp_port = args.mcp_port
        print(f"🔍 Using specified MCP port: {mcp_port}")
    else:
        mcp_port = None
    
    # Import after checking dependencies
    from python_a2a import A2AServer, run_server, TaskStatus, TaskState
    from python_a2a import AgentCard, AgentSkill
    
    print("\n🌟 MCP Agent Example 🌟")
    print("This example demonstrates how to create an A2A agent that uses MCP tools.\n")
    
    # Start MCP server in a separate process if requested
    mcp_server_process = None
    if args.auto_mcp:
        print("Starting MCP server automatically...")
        mcp_server_process = multiprocessing.Process(target=start_mcp_server, args=(mcp_port,))
        mcp_server_process.start()
        print(f"MCP server started on port {mcp_port}")
        print("Waiting for MCP server to initialize...")
        time.sleep(2)  # Give the server time to start
    
    # Create MCP server connections
    mcp_servers = {}
    mcp_url = None
    if mcp_port is not None:
        mcp_url = f"http://localhost:{mcp_port}"
        mcp_servers["utility"] = mcp_url
        print(f"Added MCP server 'utility' at {mcp_url}")
    
    # Create an Agent Card
    agent_card = AgentCard(
        name="MCP-Enabled Assistant",
        description="An A2A agent that uses external tools via MCP",
        url=f"http://localhost:{agent_port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Calculator",
                description="Perform calculations using the calculator tool",
                examples=["What's 15 * 27?", "Calculate 125 / 5"]
            ),
            AgentSkill(
                name="Unit Converter",
                description="Convert between units of measurement",
                examples=["Convert 5 kilometers to miles", "How many pounds is 10 kg?"]
            ),
            AgentSkill(
                name="Weather Information",
                description="Get current weather for a location",
                examples=["What's the weather in Tokyo?", "Current weather in Paris"]
            ),
            AgentSkill(
                name="Date and Time",
                description="Get current date and time information",
                examples=["What time is it now?", "What's today's date?"]
            )
        ]
    )
    
    # Create the A2A agent with direct MCP client integration
    class MCPAgent(A2AServer):
        """An A2A agent that directly calls MCP tools using requests"""
        
        def __init__(self, agent_card, mcp_url=None):
            super().__init__(agent_card=agent_card)
            self.mcp_url = mcp_url
        
        def handle_task(self, task):
            """Process incoming tasks"""
            try:
                # Extract message text
                message_data = task.message or {}
                content = message_data.get("content", {})
                text = content.get("text", "") if isinstance(content, dict) else ""
                
                # Default response
                response_text = (
                    "I'm an MCP-enabled assistant. I can help with:\n"
                    "- Calculations (e.g., 'What's 5 * 3?')\n"
                    "- Unit conversions (e.g., 'Convert 10 km to miles')\n"
                    "- Weather information (e.g., 'Weather in Tokyo')\n"
                    "- Date and time (e.g., 'What time is it?')"
                )
                
                # Process the message based on content
                text_lower = text.lower()
                
                if any(word in text_lower for word in ["add", "subtract", "multiply", "divide", "calculate", "what is", "what's"]) and any(c.isdigit() for c in text):
                    # This is a calculation request
                    numbers = re.findall(r"[-+]?\d*\.?\d+", text)
                    if len(numbers) >= 2:
                        a, b = float(numbers[0]), float(numbers[1])
                        
                        # Determine operation
                        if "+" in text or "add" in text_lower or "sum" in text_lower or "plus" in text_lower:
                            operation = "add"
                        elif "-" in text or "subtract" in text_lower or "minus" in text_lower:
                            operation = "subtract"
                        elif "*" in text or "x" in text or "multiply" in text_lower or "product" in text_lower or "times" in text_lower:
                            operation = "multiply"
                        elif "/" in text or "divide" in text_lower:
                            operation = "divide"
                        else:
                            operation = "add"  # Default to addition
                        
                        try:
                            # Call the MCP tool directly using requests
                            if self.mcp_url:
                                result = self.call_tool_directly("calculate", {
                                    "operation": operation,
                                    "a": a,
                                    "b": b
                                })
                                response_text = result
                            else:
                                # Fallback: do calculation directly
                                if operation == "add":
                                    result = a + b
                                    response_text = f"{a} + {b} = {result}"
                                elif operation == "subtract":
                                    result = a - b
                                    response_text = f"{a} - {b} = {result}"
                                elif operation == "multiply":
                                    result = a * b
                                    response_text = f"{a} * {b} = {result}"
                                elif operation == "divide":
                                    if b == 0:
                                        response_text = "Error: Cannot divide by zero"
                                    else:
                                        result = a / b
                                        response_text = f"{a} / {b} = {result}"
                        except Exception as e:
                            print(f"Error in calculation: {e}")
                            # Fallback: do calculation directly
                            if operation == "add":
                                result = a + b
                                response_text = f"{a} + {b} = {result}"
                            elif operation == "subtract":
                                result = a - b
                                response_text = f"{a} - {b} = {result}"
                            elif operation == "multiply":
                                result = a * b
                                response_text = f"{a} * {b} = {result}"
                            elif operation == "divide":
                                if b == 0:
                                    response_text = "Error: Cannot divide by zero"
                                else:
                                    result = a / b
                                    response_text = f"{a} / {b} = {result}"
                    else:
                        response_text = "I need two numbers to perform a calculation."
                
                elif any(word in text_lower for word in ["convert", "kilometers", "km", "miles", "kg", "pounds", "celsius", "fahrenheit"]):
                    # This is a conversion request
                    value_match = re.search(r"([-+]?\d*\.?\d+)", text)
                    
                    if value_match:
                        value = float(value_match.group(1))
                        
                        # Units to check for
                        units = [
                            "km", "kilometer", "kilometers", 
                            "miles", "mile",
                            "kg", "kilogram", "kilograms",
                            "pounds", "pound",
                            "celsius", "fahrenheit"
                        ]
                        
                        # Find mentioned units
                        found_units = []
                        for unit in units:
                            if unit in text_lower:
                                found_units.append(unit)
                        
                        if len(found_units) >= 2:
                            # Usually the first unit mentioned is the from_unit
                            from_unit_indices = [text_lower.find(unit) for unit in found_units]
                            from_unit = found_units[from_unit_indices.index(min(from_unit_indices))]
                            to_unit = found_units[from_unit_indices.index(max(from_unit_indices))]
                            
                            try:
                                # Call the MCP tool directly using requests
                                if self.mcp_url:
                                    result = self.call_tool_directly("convert_units", {
                                        "value": value,
                                        "from_unit": from_unit,
                                        "to_unit": to_unit
                                    })
                                    response_text = result
                                else:
                                    # Fallback: do conversion directly
                                    from_unit = from_unit.lower().rstrip("s")
                                    to_unit = to_unit.lower().rstrip("s")
                                    
                                    # Handle temperature conversions
                                    if from_unit in ["celsius", "c"] and to_unit in ["fahrenheit", "f"]:
                                        result = value * 9/5 + 32
                                        response_text = f"{value}°C = {result:.2f}°F"
                                    elif from_unit in ["fahrenheit", "f"] and to_unit in ["celsius", "c"]:
                                        result = (value - 32) * 5/9
                                        response_text = f"{value}°F = {result:.2f}°C"
                                    else:
                                        # Regular conversion
                                        conversion_key = (from_unit, to_unit)
                                        if conversion_key in CONVERSION_FACTORS:
                                            factor = CONVERSION_FACTORS[conversion_key]
                                            result = value * factor
                                            response_text = f"{value} {from_unit} = {result:.2f} {to_unit}"
                                        else:
                                            response_text = f"Sorry, I don't know how to convert from {from_unit} to {to_unit}"
                            except Exception as e:
                                print(f"Error in conversion: {e}")
                                # Fallback: do conversion directly
                                from_unit = from_unit.lower().rstrip("s")
                                to_unit = to_unit.lower().rstrip("s")
                                
                                # Handle temperature conversions
                                if from_unit in ["celsius", "c"] and to_unit in ["fahrenheit", "f"]:
                                    result = value * 9/5 + 32
                                    response_text = f"{value}°C = {result:.2f}°F"
                                elif from_unit in ["fahrenheit", "f"] and to_unit in ["celsius", "c"]:
                                    result = (value - 32) * 5/9
                                    response_text = f"{value}°F = {result:.2f}°C"
                                else:
                                    # Regular conversion
                                    conversion_key = (from_unit, to_unit)
                                    if conversion_key in CONVERSION_FACTORS:
                                        factor = CONVERSION_FACTORS[conversion_key]
                                        result = value * factor
                                        response_text = f"{value} {from_unit} = {result:.2f} {to_unit}"
                                    else:
                                        response_text = f"Sorry, I don't know how to convert from {from_unit} to {to_unit}"
                        else:
                            response_text = "I need both from and to units for conversion."
                    else:
                        response_text = "I need a value to perform a conversion."
                
                elif any(word in text_lower for word in ["weather", "temperature", "forecast"]):
                    # This is a weather request
                    location_match = re.search(r"(?:in|for)\s+([a-zA-Z\s]+)(?:\?|$|\.)", text)
                    
                    if location_match:
                        location = location_match.group(1).strip()
                    else:
                        # Try to find any capitalized words
                        words = text.split()
                        capitalized_words = [word for word in words if word and word[0].isupper()]
                        location = capitalized_words[0] if capitalized_words else "New York"
                    
                    try:
                        # Call the MCP tool directly using requests
                        if self.mcp_url:
                            result = self.call_tool_directly("get_weather", {"location": location})
                            response_text = result
                        else:
                            # Fallback: use mock weather data
                            location_key = location.lower()
                            if location_key in MOCK_WEATHER_DATA:
                                data = MOCK_WEATHER_DATA[location_key]
                                response_text = (
                                    f"Current weather in {location.title()}:\n"
                                    f"Condition: {data['condition']}\n"
                                    f"Temperature: {data['temperature']}°F\n"
                                    f"Humidity: {data['humidity']}%"
                                )
                            else:
                                response_text = (
                                    f"Weather data for {location} not found. Here's a default forecast:\n"
                                    f"Condition: Partly Cloudy\n"
                                    f"Temperature: 70°F\n"
                                    f"Humidity: 60%"
                                )
                    except Exception as e:
                        print(f"Error getting weather: {e}")
                        # Fallback: use mock weather data
                        location_key = location.lower()
                        if location_key in MOCK_WEATHER_DATA:
                            data = MOCK_WEATHER_DATA[location_key]
                            response_text = (
                                f"Current weather in {location.title()}:\n"
                                f"Condition: {data['condition']}\n"
                                f"Temperature: {data['temperature']}°F\n"
                                f"Humidity: {data['humidity']}%"
                            )
                        else:
                            response_text = (
                                f"Weather data for {location} not found. Here's a default forecast:\n"
                                f"Condition: Partly Cloudy\n"
                                f"Temperature: 70°F\n"
                                f"Humidity: 60%"
                            )
                
                elif any(word in text_lower for word in ["time", "date", "day", "today"]):
                    # This is a date/time request
                    try:
                        # Call the MCP tool directly using requests
                        if self.mcp_url:
                            result = self.call_tool_directly("get_current_time", {})
                            response_text = result
                        else:
                            # Fallback: generate time directly
                            now = datetime.now()
                            response_text = (
                                f"Current Date and Time:\n"
                                f"Date: {now.strftime('%B %d, %Y')}\n"
                                f"Time: {now.strftime('%H:%M:%S')}\n"
                                f"Day of Week: {now.strftime('%A')}\n"
                                f"Timezone: {time.tzname[0]}"
                            )
                    except Exception as e:
                        print(f"Error getting date/time: {e}")
                        # Fallback: generate time directly
                        now = datetime.now()
                        response_text = (
                            f"Current Date and Time:\n"
                            f"Date: {now.strftime('%B %d, %Y')}\n"
                            f"Time: {now.strftime('%H:%M:%S')}\n"
                            f"Day of Week: {now.strftime('%A')}\n"
                            f"Timezone: {time.tzname[0]}"
                        )
                
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
        
        def call_tool_directly(self, tool_name, parameters):
            """Call an MCP tool directly using HTTP requests"""
            if not self.mcp_url:
                raise ValueError("No MCP URL configured")
            
            # Build the URL for the tool
            tool_url = f"{self.mcp_url}/tools/{tool_name}"
            
            # Make the POST request
            try:
                response = requests.post(
                    tool_url, 
                    json=parameters,
                    headers={"Content-Type": "application/json"}
                )
                response.raise_for_status()
                
                # Parse the response
                result = response.json()
                
                # Extract the text content
                if "content" in result and len(result["content"]) > 0:
                    if "text" in result["content"][0]:
                        return result["content"][0]["text"]
                
                # Return the raw response if we couldn't extract text
                return str(result)
                
            except Exception as e:
                print(f"Error calling MCP tool {tool_name}: {e}")
                raise
    
    # Create the MCP-enabled agent
    mcp_agent = MCPAgent(agent_card, mcp_url)
    
    # Print agent information
    print("\n=== MCP-Enabled Agent Information ===")
    print(f"Name: {mcp_agent.agent_card.name}")
    print(f"Description: {mcp_agent.agent_card.description}")
    print(f"MCP URL: {mcp_url or 'Not configured, using fallback implementations'}")
    
    # Print skills information
    print("\n=== Agent Skills ===")
    for skill in mcp_agent.agent_card.skills:
        print(f"- {skill.name}: {skill.description}")
        print(f"  Examples: {', '.join(skill.examples)}")
    
    # Start the A2A server
    print(f"\n🚀 Starting MCP-enabled agent on http://localhost:{agent_port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start a client process to test the agent
        client_process = multiprocessing.Process(target=start_client_process, args=(agent_port,))
        client_process.start()
        
        # Run the server
        run_server(mcp_agent, host="0.0.0.0", port=agent_port)
    except KeyboardInterrupt:
        print("\n✅ Server stopped")
        # Clean up processes
        if 'client_process' in locals():
            client_process.terminate()
            client_process.join()
    except Exception as e:
        print(f"\n❌ Error starting agent server: {e}")
        if "Address already in use" in str(e):
            print(f"\nPort {agent_port} is already in use. Try using a different port:")
            print(f"    python mcp_agent.py --port {agent_port + 1}")
        return 1
    finally:
        # Always clean up MCP server if we started one
        if mcp_server_process:
            print("\nStopping MCP server...")
            mcp_server_process.terminate()
            mcp_server_process.join()
            print("MCP server stopped")
    
    print("\n=== What's Next? ===")
    print("1. Try 'mcp_tools.py' to explore the tools in more detail")
    print("2. Try 'openai_agent.py' with function calling to use LLMs with tools")
    print("3. Try 'weather_assistant.py' for a complete application example")
    
    print("\n🎉 You've created an MCP-enabled A2A agent! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)