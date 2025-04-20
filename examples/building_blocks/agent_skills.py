#!/usr/bin/env python
"""
A2A Agent Skills

This example demonstrates how to use the @agent and @skill decorators
to create A2A agents with structured skills. These decorators make it
easy to define agent capabilities and create self-documenting agents.

To run:
    python agent_skills.py [--port PORT]

Example:
    python agent_skills.py --port 5000

Requirements:
    pip install "python-a2a[server]"
"""

import sys
import argparse
import socket
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
    parser = argparse.ArgumentParser(description="A2A Agent Skills Example")
    parser.add_argument(
        "--port", type=int, default=None,
        help="Port to run the server on (default: auto-select an available port)"
    )
    parser.add_argument(
        "--run", action="store_true",
        help="Run the server after showing the example"
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
    from python_a2a import A2AServer, skill, agent, run_server, TaskStatus, TaskState
    
    print("\n🌟 A2A Agent Skills 🌟")
    print("This example shows how to use decorators to create structured A2A agents.\n")
    
    # ===============================================================
    # Create a utility agent with various skills using decorators
    # ===============================================================
    
    @agent(
        name="Utility Assistant",
        description="A multi-purpose utility assistant with various helpful tools",
        version="1.0.0",
        url=f"http://localhost:{port}"
    )
    class UtilityAgent(A2AServer):
        """A utility agent with calculator, converter, and time tools"""
        
        @skill(
            name="Calculator",
            description="Perform basic math operations",
            tags=["math", "calculator"],
            examples=["Calculate 5 + 3", "What is 10 * 7?"]
        )
        def calculate(self, operation, a, b):
            """
            Perform a math operation on two numbers.
            
            Args:
                operation: The operation to perform (add, subtract, multiply, divide)
                a: The first number
                b: The second number
                
            Returns:
                The result of the operation
            """
            a, b = float(a), float(b)
            
            if operation == "add":
                return f"{a} + {b} = {a + b}"
            elif operation == "subtract":
                return f"{a} - {b} = {a - b}"
            elif operation == "multiply":
                return f"{a} * {b} = {a * b}"
            elif operation == "divide":
                if b == 0:
                    return "Error: Division by zero"
                return f"{a} / {b} = {a / b}"
            else:
                return f"Unknown operation: {operation}"
        
        @skill(
            name="Unit Converter",
            description="Convert between different units of measurement",
            tags=["converter", "units"],
            examples=["Convert 5 kilometers to miles", "How many pounds is 10 kg?"]
        )
        def convert_units(self, value, from_unit, to_unit):
            """
            Convert a value from one unit to another.
            
            Args:
                value: The value to convert
                from_unit: The source unit
                to_unit: The target unit
                
            Returns:
                The converted value
            """
            value = float(value)
            
            # Conversion factors
            conversions = {
                ("km", "miles"): 0.621371,
                ("miles", "km"): 1.60934,
                ("meters", "feet"): 3.28084,
                ("feet", "meters"): 0.3048,
                ("kg", "pounds"): 2.20462,
                ("pounds", "kg"): 0.453592,
                ("celsius", "fahrenheit"): lambda c: c * 9/5 + 32,
                ("fahrenheit", "celsius"): lambda f: (f - 32) * 5/9
            }
            
            # Standardize unit names
            from_unit = from_unit.lower().rstrip("s")
            to_unit = to_unit.lower().rstrip("s")
            
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
        
        @skill(
            name="Date and Time",
            description="Get the current date and time in different formats",
            tags=["time", "date"],
            examples=["What time is it?", "What's today's date?"]
        )
        def get_datetime(self, format_type="full"):
            """
            Get the current date and time.
            
            Args:
                format_type: The format to return (full, date, time, iso)
                
            Returns:
                Formatted date and/or time
            """
            now = datetime.now()
            
            if format_type == "full":
                return f"Current date and time: {now.strftime('%A, %B %d, %Y %H:%M:%S')}"
            elif format_type == "date":
                return f"Today's date: {now.strftime('%B %d, %Y')}"
            elif format_type == "time":
                return f"Current time: {now.strftime('%H:%M:%S')}"
            elif format_type == "iso":
                return f"ISO format: {now.isoformat()}"
            else:
                return f"Unknown format: {format_type}"
        
        @skill(
            name="Text Analyzer",
            description="Analyze text for character and word count",
            tags=["text", "analyzer"],
            examples=["Count words in 'The quick brown fox'", "Analyze 'Hello, world!'"]
        )
        def analyze_text(self, text):
            """
            Analyze text for character and word count.
            
            Args:
                text: The text to analyze
                
            Returns:
                Analysis of the text
            """
            char_count = len(text)
            word_count = len(text.split())
            
            return (
                f"Text analysis:\n"
                f"- Characters: {char_count}\n"
                f"- Words: {word_count}\n"
                f"- Characters per word: {char_count / word_count:.1f}\n"
                f"- First 10 characters: '{text[:10]}...'"
            )
        
        def handle_task(self, task):
            """Process incoming tasks by routing to the appropriate skill"""
            try:
                # Extract message text from task
                message_data = task.message or {}
                content = message_data.get("content", {})
                text = content.get("text", "") if isinstance(content, dict) else ""
                
                # Default response
                response_text = (
                    "I'm a Utility Assistant. I can help with:\n"
                    "- Calculations: 'Calculate 5 + 3'\n"
                    "- Unit conversions: 'Convert 5 km to miles'\n"
                    "- Date and time: 'What time is it?'\n"
                    "- Text analysis: 'Analyze this text'"
                )
                
                # Handle each skill based on keywords
                text_lower = text.lower()
                
                if any(keyword in text_lower for keyword in ["calculate", "math", "+", "-", "*", "/"]):
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
                        
                        response_text = self.calculate(operation, a, b)
                    else:
                        response_text = "I need two numbers to perform a calculation."
                
                elif any(keyword in text_lower for keyword in ["convert", "unit", "km", "miles", "kg", "pounds"]):
                    # This is a conversion request
                    import re
                    
                    # Try to extract value and units
                    value_match = re.search(r"([-+]?\d*\.?\d+)", text)
                    if value_match:
                        value = float(value_match.group(1))
                        
                        # Try to find units
                        units = ["km", "kilometer", "kilometers", "miles", "mile", 
                                "meters", "feet", "kg", "kilogram", "kilograms", "pounds", "pound", 
                                "celsius", "fahrenheit"]
                        
                        found_units = []
                        for unit in units:
                            if unit in text_lower or unit.rstrip("s") in text_lower:
                                found_units.append(unit)
                        
                        if len(found_units) >= 2:
                            from_unit = found_units[0]
                            to_unit = found_units[1]
                            response_text = self.convert_units(value, from_unit, to_unit)
                        else:
                            response_text = "I need both from and to units for conversion."
                    else:
                        response_text = "I need a value to perform a conversion."
                
                elif any(keyword in text_lower for keyword in ["time", "date", "day", "today"]):
                    # This is a time/date request
                    if "date" in text_lower and "time" not in text_lower:
                        format_type = "date"
                    elif "time" in text_lower and "date" not in text_lower:
                        format_type = "time"
                    else:
                        format_type = "full"
                    
                    response_text = self.get_datetime(format_type)
                
                elif any(keyword in text_lower for keyword in ["analyze", "count", "word", "character"]):
                    # This is a text analysis request
                    # First check if there's text in quotes
                    import re
                    quoted_text = re.search(r"['\"](.+?)['\"]", text)
                    
                    if quoted_text:
                        analysis_text = quoted_text.group(1)
                    else:
                        # Use the whole message text
                        analysis_text = text
                    
                    response_text = self.analyze_text(analysis_text)
                
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
    
    # Create an instance of our decorated agent
    utility_agent = UtilityAgent()
    
    # Display agent information from the auto-generated agent card
    print("=== Utility Agent Information ===")
    print(f"Name: {utility_agent.agent_card.name}")
    print(f"Description: {utility_agent.agent_card.description}")
    print(f"Version: {utility_agent.agent_card.version}")
    print(f"URL: {utility_agent.agent_card.url}")
    
    # Display skills information
    print("\n=== Skills Information ===")
    for skill in utility_agent.agent_card.skills:
        print(f"\n{skill.name}: {skill.description}")
        print(f"Tags: {', '.join(skill.tags)}")
        print(f"Examples: {', '.join(skill.examples)}")
    
    # Test the agent with some example inputs
    print("\n=== Testing Agent Skills ===")
    
    test_messages = [
        "Calculate 5 + 10",
        "Convert 25 kg to pounds",
        "What time is it?",
        "Analyze 'The quick brown fox jumps over the lazy dog'"
    ]
    
    for message_text in test_messages:
        # Create a test task
        test_task = type('Task', (), {
            "message": {"content": {"type": "text", "text": message_text}},
            "artifacts": None,
            "status": None
        })
        
        # Process the task
        result = utility_agent.handle_task(test_task)
        
        # Print the result
        print(f"\nInput: {message_text}")
        print(f"Response: {result.artifacts[0]['parts'][0]['text']}")
    
    # Run the server if requested
    if args.run:
        print(f"\n🚀 Starting Utility Agent server on http://localhost:{port}")
        print("Press Ctrl+C to stop the server")
        
        try:
            # Start the server
            run_server(utility_agent, host="0.0.0.0", port=port)
        except KeyboardInterrupt:
            print("\n✅ Server stopped successfully")
        except Exception as e:
            print(f"\n❌ Error starting server: {e}")
            if "Address already in use" in str(e):
                print(f"\nPort {port} is already in use. Try using a different port:")
                print(f"    python agent_skills.py --port {port + 1} --run")
            return 1
    else:
        # Show how to run the server
        print(f"\n=== Running the Server ===")
        print(f"To start the server on http://localhost:{port}, run:")
        print(f"    python agent_skills.py --port {port} --run")
    
    print("\n=== What's Next? ===")
    print("1. Try 'weather_assistant.py' for a more complete application example")
    print("2. Try 'openai_agent.py' to connect this pattern with an LLM")
    print("3. Try 'mcp_tools.py' to extend your agent with external tools")
    
    print("\n🎉 You've learned how to use A2A agent and skill decorators! 🎉")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)