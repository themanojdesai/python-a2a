#!/usr/bin/env python
"""
A2A Function Calling Example

This example demonstrates how to build an A2A server with function calling
capabilities. The server can perform math operations and convert units.

To run:
    python function_calling.py [--port PORT]

Example:
    python function_calling.py --port 5000

Requirements:
    pip install "python-a2a[server]"
"""

import sys
import argparse
import socket
import json
from datetime import datetime

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
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required dependencies:")
        print("    pip install \"python-a2a[server]\"")
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
    parser = argparse.ArgumentParser(description="A2A Function Calling Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    return parser.parse_args()

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
    from python_a2a import (
        A2AServer, run_server, AgentCard, AgentSkill,
        Message, TaskStatus, TaskState,
        FunctionCallContent, FunctionParameter, FunctionResponseContent
    )
    
    print("\n🌟 Creating an A2A Server with Function Calling 🌟")
    
    # Create an agent card with skills information
    agent_card = AgentCard(
        name="Function Server",
        description="An A2A server that can perform calculations and conversions",
        url=f"http://localhost:{port}",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Calculate",
                description="Perform math operations",
                examples=["Calculate 5 + 3", "What is 10 * 4?"]
            ),
            AgentSkill(
                name="Convert",
                description="Convert between units",
                examples=["Convert 5 kilometers to miles", "How many pounds is 10 kg?"]
            ),
            AgentSkill(
                name="Get Time",
                description="Get the current time",
                examples=["What time is it?", "Current time"]
            )
        ]
    )
    
    # Create a custom A2A server with function calling
    class FunctionServer(A2AServer):
        def __init__(self):
            # Initialize with our agent card
            super().__init__(agent_card=agent_card)
            
            # Define available functions
            self.functions = {
                "calculate": self._calculate,
                "convert": self._convert,
                "get_time": self._get_time
            }
        
        def _calculate(self, operation, a, b):
            """Perform a math operation"""
            a, b = float(a), float(b)
            
            if operation == "add":
                result = a + b
                text = f"{a} + {b} = {result}"
            elif operation == "subtract":
                result = a - b
                text = f"{a} - {b} = {result}"
            elif operation == "multiply":
                result = a * b
                text = f"{a} * {b} = {result}"
            elif operation == "divide":
                if b == 0:
                    return "Error: Division by zero"
                result = a / b
                text = f"{a} / {b} = {result}"
            else:
                return f"Unknown operation: {operation}"
            
            return text
        
        def _convert(self, value, from_unit, to_unit):
            """Convert between units"""
            value = float(value)
            
            # Conversion factors for common units
            conversions = {
                ("km", "miles"): 0.621371,
                ("miles", "km"): 1.60934,
                ("kg", "pounds"): 2.20462,
                ("pounds", "kg"): 0.453592,
                ("celsius", "fahrenheit"): lambda c: c * 9/5 + 32,
                ("fahrenheit", "celsius"): lambda f: (f - 32) * 5/9
            }
            
            # Standardize unit names
            from_unit = from_unit.lower().rstrip("s")  # Remove plural 's'
            to_unit = to_unit.lower().rstrip("s")  # Remove plural 's'
            
            # Handle aliases
            unit_aliases = {
                "kilometer": "km",
                "mile": "miles",
                "kilogram": "kg",
                "pound": "pounds",
                "c": "celsius",
                "f": "fahrenheit"
            }
            
            from_unit = unit_aliases.get(from_unit, from_unit)
            to_unit = unit_aliases.get(to_unit, to_unit)
            
            # Perform the conversion
            conversion_key = (from_unit, to_unit)
            if conversion_key in conversions:
                factor = conversions[conversion_key]
                if callable(factor):
                    result = factor(value)
                else:
                    result = value * factor
                
                return f"{value} {from_unit} = {result:.2f} {to_unit}"
            else:
                return f"Sorry, I don't know how to convert from {from_unit} to {to_unit}"
        
        def _get_time(self):
            """Get the current time"""
            now = datetime.now()
            return f"The current time is {now.strftime('%H:%M:%S')}"
        
        def handle_task(self, task):
            """Process incoming tasks with function calling"""
            try:
                # Extract message text or content
                message_data = task.message or {}
                
                # Check if we received a function call directly
                if isinstance(message_data, dict) and message_data.get("content", {}).get("type") == "function_call":
                    # Extract function call details
                    content = message_data.get("content", {})
                    function_name = content.get("name", "")
                    parameters = content.get("parameters", [])
                    
                    # Convert parameters to dictionary
                    params = {}
                    for param in parameters:
                        params[param.get("name")] = param.get("value")
                    
                    # Call the function
                    if function_name in self.functions:
                        result = self.functions[function_name](**params)
                        task.artifacts = [{
                            "parts": [{
                                "type": "function_response",
                                "name": function_name,
                                "content": {
                                    "result": result
                                }
                            }]
                        }]
                    else:
                        response = f"Unknown function: {function_name}"
                        task.artifacts = [{
                            "parts": [{"type": "text", "text": response}]
                        }]
                else:
                    # Extract text from message
                    content = message_data.get("content", {})
                    text = content.get("text", "") if isinstance(content, dict) else ""
                    
                    # Analyze text to determine intent
                    text_lower = text.lower()
                    
                    if "calculate" in text_lower or any(op in text_lower for op in ["+", "-", "*", "/"]):
                        # This is a calculation request
                        import re
                        
                        # Try to extract numbers and operation
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
                            
                            # Return function call instead of direct result
                            task.artifacts = [{
                                "parts": [{
                                    "type": "function_call",
                                    "name": "calculate",
                                    "parameters": [
                                        {"name": "operation", "value": operation},
                                        {"name": "a", "value": a},
                                        {"name": "b", "value": b}
                                    ]
                                }]
                            }]
                            task.status = TaskStatus(state=TaskState.COMPLETED)
                            return task
                        else:
                            response = "I need two numbers to perform a calculation."
                    
                    elif "convert" in text_lower or any(unit in text_lower for unit in ["km", "miles", "kg", "pounds"]):
                        # This is a conversion request
                        import re
                        
                        # Try to extract value and units
                        value_match = re.search(r"([-+]?\d*\.?\d+)", text)
                        if value_match:
                            value = float(value_match.group(1))
                            
                            # Try to find units
                            units = ["km", "kilometer", "kilometers", "miles", "mile", 
                                    "kg", "kilogram", "kilograms", "pounds", "pound", 
                                    "celsius", "fahrenheit"]
                            
                            found_units = []
                            for unit in units:
                                if unit in text_lower or unit.rstrip("s") in text_lower:
                                    found_units.append(unit)
                            
                            if len(found_units) >= 2:
                                from_unit = found_units[0]
                                to_unit = found_units[1]
                                
                                # Return function call
                                task.artifacts = [{
                                    "parts": [{
                                        "type": "function_call",
                                        "name": "convert",
                                        "parameters": [
                                            {"name": "value", "value": value},
                                            {"name": "from_unit", "value": from_unit},
                                            {"name": "to_unit", "value": to_unit}
                                        ]
                                    }]
                                }]
                                task.status = TaskStatus(state=TaskState.COMPLETED)
                                return task
                            else:
                                response = "I need both from and to units for conversion."
                        else:
                            response = "I need a value to perform a conversion."
                    
                    elif "time" in text_lower or "clock" in text_lower:
                        # This is a time request
                        task.artifacts = [{
                            "parts": [{
                                "type": "function_call",
                                "name": "get_time",
                                "parameters": []
                            }]
                        }]
                        task.status = TaskStatus(state=TaskState.COMPLETED)
                        return task
                    
                    else:
                        # Default response with help
                        response = (
                            "I'm a function calling server that can:\n"
                            "1. Calculate math operations (e.g., 'Calculate 5 + 3')\n"
                            "2. Convert between units (e.g., 'Convert 5 km to miles')\n"
                            "3. Tell you the current time (e.g., 'What time is it?')\n\n"
                            "Try one of these examples!"
                        )
                
                # Create artifact with response
                task.artifacts = [{
                    "parts": [{"type": "text", "text": response}]
                }]
                
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
    
    # Create the server
    function_server = FunctionServer()
    
    print("\n=== Server Information ===")
    print(f"Name: {function_server.agent_card.name}")
    print(f"Description: {function_server.agent_card.description}")
    print(f"URL: http://localhost:{port}")
    print("\nSkills:")
    for skill in function_server.agent_card.skills:
        print(f"- {skill.name}: {skill.description}")
    
    # Test the server with some examples
    print("\n=== Testing Function Calls Locally ===")
    
    # Test calculation
    test_message = {
        "content": {
            "type": "function_call",
            "name": "calculate",
            "parameters": [
                {"name": "operation", "value": "add"},
                {"name": "a", "value": 5},
                {"name": "b", "value": 3}
            ]
        },
        "role": "user"
    }
    test_task = type('Task', (), {"message": test_message, "artifacts": None, "status": None})
    result = function_server.handle_task(test_task)
    print("\nTest: Calculate 5 + 3")
    if result.artifacts:
        print(f"Response: {result.artifacts[0]['parts'][0]['type']}")
        print(f"Result: {result.artifacts[0]['parts'][0].get('text', 'Function call returned')}")
    
    # Test conversion
    test_message = {
        "content": {
            "type": "function_call",
            "name": "convert",
            "parameters": [
                {"name": "value", "value": 10},
                {"name": "from_unit", "value": "km"},
                {"name": "to_unit", "value": "miles"}
            ]
        },
        "role": "user"
    }
    test_task = type('Task', (), {"message": test_message, "artifacts": None, "status": None})
    result = function_server.handle_task(test_task)
    print("\nTest: Convert 10 km to miles")
    if result.artifacts:
        print(f"Response: {result.artifacts[0]['parts'][0]['type']}")
        print(f"Result: {result.artifacts[0]['parts'][0].get('text', 'Function call returned')}")
    
    print("\n🚀 Starting server on http://localhost:{port}")
    print("Press Ctrl+C to stop the server")
    
    try:
        # Start the server
        run_server(function_server, host="0.0.0.0", port=port)
    except KeyboardInterrupt:
        print("\n✅ Server stopped successfully")
    except Exception as e:
        print(f"\n❌ Error starting server: {e}")
        if "Address already in use" in str(e):
            print(f"\nPort {port} is already in use. Try using a different port:")
            print(f"    python function_calling.py --port {port + 1}")
        return 1
    
    print("\n=== What's Next? ===")
    print("1. Connect to this server using simple_client.py:")
    print(f"    python simple_client.py http://localhost:{port}")
    print("2. Try the 'weather_assistant.py' example for a complete application")
    print("3. Explore the 'mcp_tools.py' example to use the Model Context Protocol")
    
    print("\n🎉 You've created an A2A server with function calling! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)
