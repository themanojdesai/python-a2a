#!/usr/bin/env python
"""
MCP Tools Example

This example demonstrates how to create MCP (Model Context Protocol) tools
that can be used to extend AI agent capabilities with external functions.
MCP lets you define tools that models can use to access external data or
perform actions they couldn't do otherwise.

To run:
    python mcp_tools.py [--port PORT] [--run]

Example:
    python mcp_tools.py --port 5000 --run

Requirements:
    pip install "python-a2a[mcp,server]"
"""

import sys
import os
import argparse
import socket
import json
import time
import asyncio
from datetime import datetime

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import python_a2a
    except ImportError:
        missing_deps.append("python-a2a")
    
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
    parser = argparse.ArgumentParser(description="MCP Tools Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the MCP server on (default: auto-select an available port)"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Run the MCP server after showing the example"
    )
    return parser.parse_args()

async def test_tools(utility_mcp, port):
    """Test the MCP tools directly"""
    print("\n=== Testing MCP Tools ===")
    
    # Test calculator
    print("\n1. Testing Calculator Tool")
    
    # Addition test
    print("\nTesting addition: 5 + 3")
    add_result = await utility_mcp.call_tool("calculate", {"operation": "add", "a": 5, "b": 3})
    print(f"Result: {add_result.content[0]['text']}")
    
    # Multiplication test
    print("\nTesting multiplication: 7 * 6")
    multiply_result = await utility_mcp.call_tool("calculate", {"operation": "multiply", "a": 7, "b": 6})
    print(f"Result: {multiply_result.content[0]['text']}")
    
    # Test unit converter
    print("\n2. Testing Unit Converter Tool")
    
    # Distance conversion test
    print("\nConverting 10 kilometers to miles")
    km_to_miles = await utility_mcp.call_tool("convert_units", {"value": 10, "from_unit": "km", "to_unit": "miles"})
    print(f"Result: {km_to_miles.content[0]['text']}")
    
    # Temperature conversion test
    print("\nConverting 32 Fahrenheit to Celsius")
    f_to_c = await utility_mcp.call_tool("convert_units", {"value": 32, "from_unit": "fahrenheit", "to_unit": "celsius"})
    print(f"Result: {f_to_c.content[0]['text']}")
    
    # Test weather tool
    print("\n3. Testing Weather Information Tool")
    
    # Get weather for a city
    print("\nGetting weather for New York")
    weather_result = await utility_mcp.call_tool("get_weather", {"location": "New York"})
    print(f"Result: {weather_result.content[0]['text']}")
    
    # Test datetime tool
    print("\n4. Testing DateTime Tool")
    
    # Get current time
    print("\nGetting current time")
    time_result = await utility_mcp.call_tool("get_current_time", {})
    print(f"Result: {time_result.content[0]['text']}")
    
    print("\n✅ Tool testing completed!")
    print(f"\nMCP Server is available at: http://localhost:{port}/")
    print("For OpenAPI documentation, visit: http://localhost:{port}/docs")
    
    # Create a standalone message to demonstrate client usage
    print("\n=== Example Client Usage ===")
    print(f"""
To use these tools in your code with the MCPClient:

```python
from python_a2a.mcp import MCPClient

async def main():
    # Create client connected to the MCP server
    client = MCPClient("http://localhost:{port}")
    
    # Call tools
    result = await client.call_tool("calculate", operation="add", a=5, b=3)
    # The result is returned as a string directly
    print(f"5 + 3 = {{result}}")
    
    # Call another tool
    weather = await client.call_tool("get_weather", location="Paris")
    print(f"Weather in Paris: {{weather}}")

# Run the async function
import asyncio
asyncio.run(main())
```
""")

def main():
    # First, check dependencies
    if not check_dependencies():
        return 1
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Find an available port if none was specified
    if args.port is None:
        port = find_available_port()
        print(f"🔍 Auto-selected port: {port}")
    else:
        port = args.port
        print(f"🔍 Using specified port: {port}")
    
    # Import after checking dependencies
    from python_a2a.mcp import FastMCP, text_response, MCPResponse
    
    print("\n🌟 MCP Tools Example 🌟")
    print("This example demonstrates how to create MCP tools for AI agents.\n")
    
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
    
    # Print information about the MCP server
    print("=== MCP Server Information ===")
    print(f"Name: {utility_mcp.name}")
    print(f"Description: {utility_mcp.description}")
    print(f"Version: {utility_mcp.version}")
    
    # Print information about the available tools
    tools = utility_mcp.get_tools()
    print(f"\nAvailable Tools: {len(tools)}")
    
    for i, tool in enumerate(tools, 1):
        print(f"\n{i}. {tool['name']}: {tool['description']}")
        # Print parameter information
        if "parameters" in tool and "properties" in tool["parameters"]:
            print("   Parameters:")
            for param_name, param_info in tool["parameters"]["properties"].items():
                required = "Required" if param_name in tool["parameters"].get("required", []) else "Optional"
                print(f"   - {param_name} ({param_info.get('type', 'any')}): {param_info.get('description', '')} [{required}]")
    
    # Test the tools
    if not args.run:
        # Run the tool tests in async mode
        loop = asyncio.get_event_loop()
        loop.run_until_complete(test_tools(utility_mcp, port))
        
        # Show how to run the server
        print(f"\n=== Running the Server ===")
        print(f"To start the server on http://localhost:{port}, run:")
        print(f"    python mcp_tools.py --port {port} --run")
    else:
        # Run the server
        from python_a2a.mcp import create_fastapi_app
        import uvicorn
        
        print(f"\n🚀 Starting MCP server on http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        
        # Create a FastAPI app from the MCP server
        app = create_fastapi_app(utility_mcp)
        
        # Run the server
        uvicorn.run(app, host="0.0.0.0", port=port)
    
    print("\n=== What's Next? ===")
    print("1. Try 'mcp_agent.py' to create an agent that uses these tools")
    print("2. Try 'openai_agent.py' to create an OpenAI-powered agent")
    print("3. Try 'weather_assistant.py' for a complete application example")
    
    print("\n🎉 You've created your first MCP tools! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)