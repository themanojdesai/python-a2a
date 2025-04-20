#!/usr/bin/env python
"""
Testing A2A Agents Example

This example demonstrates how to properly test A2A agents using various
testing strategies including unit tests, mock clients, and test fixtures.
It shows best practices for verifying agent functionality programmatically.

To run:
    python testing_agents.py

Requirements:
    pip install "python-a2a[server]" pytest

Note: This script includes examples of unit tests that would typically be
run with pytest, but also includes functionality to run them directly.
"""

import sys
import os
import argparse
import unittest
import json
from unittest.mock import MagicMock, patch
import time

def check_dependencies():
    """Check if required dependencies are installed"""
    missing_deps = []
    
    try:
        import python_a2a
    except ImportError:
        missing_deps.append("python-a2a")
    
    try:
        import pytest
    except ImportError:
        missing_deps.append("pytest")
    
    if missing_deps:
        print("❌ Missing dependencies:")
        for dep in missing_deps:
            print(f"  - {dep}")
        
        print("\nPlease install the required packages:")
        print("    pip install \"python-a2a[server]\" pytest")
        print("\nThen run this example again.")
        return False
    
    print("✅ Dependencies installed correctly!")
    return True

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Testing A2A Agents Example")
    parser.add_argument(
        "--run-tests", action="store_true",
        help="Run all tests"
    )
    parser.add_argument(
        "--test-type", type=str, choices=["unit", "mock", "integration", "all"],
        default="all", 
        help="Type of tests to run (default: all)"
    )
    return parser.parse_args()

# --- Define a Simple Calculator Agent for Testing ---

class CalculatorAgent:
    """A simple calculator agent for testing purposes"""
    
    def __init__(self):
        from python_a2a import AgentCard, AgentSkill, A2AServer
        
        # Create an agent card
        self.agent_card = AgentCard(
            name="Calculator Agent",
            description="Performs basic calculations",
            url="http://localhost:5000",
            version="1.0.0",
            skills=[
                AgentSkill(
                    name="Add",
                    description="Add two numbers",
                    examples=["Add 5 and 3", "What is 2 + 2?"]
                ),
                AgentSkill(
                    name="Subtract",
                    description="Subtract one number from another",
                    examples=["Subtract 7 from 10", "What is 20 - 5?"]
                ),
                AgentSkill(
                    name="Multiply",
                    description="Multiply two numbers",
                    examples=["Multiply 4 by 6", "What is 7 * 8?"]
                ),
                AgentSkill(
                    name="Divide",
                    description="Divide one number by another",
                    examples=["Divide 15 by 3", "What is 100 / 5?"]
                )
            ]
        )
    
    def add(self, a, b):
        """Add two numbers"""
        return a + b
    
    def subtract(self, a, b):
        """Subtract b from a"""
        return a - b
    
    def multiply(self, a, b):
        """Multiply two numbers"""
        return a * b
    
    def divide(self, a, b):
        """Divide a by b"""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def handle_task(self, task):
        """Process incoming tasks"""
        from python_a2a import TaskStatus, TaskState
        
        # Extract message text
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        # Default response
        response_text = "I can perform basic calculations. Try asking something like 'Add 5 and 3' or 'What is 7 * 8?'"
        
        # Parse for operation and numbers
        import re
        
        # Extract numbers from the text
        numbers = re.findall(r"[-+]?\d*\.?\d+", text)
        if len(numbers) >= 2:
            a = float(numbers[0])
            b = float(numbers[1])
            
            # Determine operation from text
            text_lower = text.lower()
            
            try:
                if any(op in text_lower for op in ["add", "plus", "sum", "+"]):
                    result = self.add(a, b)
                    response_text = f"{a} + {b} = {result}"
                
                elif any(op in text_lower for op in ["subtract", "minus", "difference", "-"]):
                    result = self.subtract(a, b)
                    response_text = f"{a} - {b} = {result}"
                
                elif any(op in text_lower for op in ["multiply", "times", "product", "*", "x"]):
                    result = self.multiply(a, b)
                    response_text = f"{a} * {b} = {result}"
                
                elif any(op in text_lower for op in ["divide", "quotient", "/"]):
                    result = self.divide(a, b)
                    response_text = f"{a} / {b} = {result}"
            
            except Exception as e:
                response_text = f"Error: {str(e)}"
        
        # Create response artifact
        task.artifacts = [{
            "parts": [{"type": "text", "text": response_text}]
        }]
        
        # Set task status
        task.status = TaskStatus(state=TaskState.COMPLETED)
        
        return task

# --- Unit Tests for Calculator Agent ---

class TestCalculatorAgent(unittest.TestCase):
    """Unit tests for the Calculator Agent"""
    
    def setUp(self):
        """Set up test fixtures"""
        from python_a2a import Task, TaskStatus, TaskState
        
        # Create an instance of the agent
        self.agent = CalculatorAgent()
        
        # Create a mock task for testing
        self.task = MagicMock(spec=Task)
        self.task.artifacts = None
        self.task.status = None
    
    def test_add(self):
        """Test the add method"""
        # Test integer addition
        self.assertEqual(self.agent.add(5, 3), 8)
        
        # Test float addition
        self.assertEqual(self.agent.add(2.5, 3.5), 6.0)
        
        # Test negative numbers
        self.assertEqual(self.agent.add(-5, 10), 5)
    
    def test_subtract(self):
        """Test the subtract method"""
        # Test integer subtraction
        self.assertEqual(self.agent.subtract(10, 4), 6)
        
        # Test float subtraction
        self.assertEqual(self.agent.subtract(5.5, 2.5), 3.0)
        
        # Test negative result
        self.assertEqual(self.agent.subtract(5, 10), -5)
    
    def test_multiply(self):
        """Test the multiply method"""
        # Test integer multiplication
        self.assertEqual(self.agent.multiply(6, 7), 42)
        
        # Test float multiplication
        self.assertEqual(self.agent.multiply(2.5, 4.0), 10.0)
        
        # Test with zero
        self.assertEqual(self.agent.multiply(5, 0), 0)
    
    def test_divide(self):
        """Test the divide method"""
        # Test integer division
        self.assertEqual(self.agent.divide(10, 2), 5)
        
        # Test float division
        self.assertEqual(self.agent.divide(5, 2), 2.5)
        
        # Test division by zero
        with self.assertRaises(ValueError):
            self.agent.divide(5, 0)
    
    def test_handle_task_add(self):
        """Test task handling for addition"""
        # Set up task message
        self.task.message = {"content": {"type": "text", "text": "Add 5 and 3"}}
        
        # Call handle_task
        result = self.agent.handle_task(self.task)
        
        # Check task was updated with correct response
        self.assertIsNotNone(result.artifacts)
        self.assertEqual(len(result.artifacts), 1)
        self.assertEqual(result.artifacts[0]["parts"][0]["text"], "5.0 + 3.0 = 8.0")
        
        # Check task status was updated
        from python_a2a import TaskState
        self.assertEqual(result.status.state, TaskState.COMPLETED)
    
    def test_handle_task_invalid(self):
        """Test task handling for invalid input"""
        # Set up task message without numbers
        self.task.message = {"content": {"type": "text", "text": "Hello, how are you?"}}
        
        # Call handle_task
        result = self.agent.handle_task(self.task)
        
        # Check default response was used
        self.assertIsNotNone(result.artifacts)
        self.assertEqual(len(result.artifacts), 1)
        self.assertTrue("I can perform basic calculations" in result.artifacts[0]["parts"][0]["text"])

# --- Mock Client Tests ---

class TestCalculatorAgentWithMockClient(unittest.TestCase):
    """Tests using a mock A2A client to simulate client interactions"""
    
    def setUp(self):
        """Set up test fixtures"""
        # Create a patched A2AClient
        self.patcher = patch('python_a2a.A2AClient')
        self.mock_client_class = self.patcher.start()
        
        # Create a mock client instance
        self.mock_client = self.mock_client_class.return_value
        
        # Set up agent_card property on the mock
        from python_a2a import AgentCard
        self.mock_client.agent_card = AgentCard(
            name="Calculator Agent",
            description="Performs basic calculations",
            url="http://mock-url",
            version="1.0.0"
        )
    
    def tearDown(self):
        """Clean up after tests"""
        self.patcher.stop()
    
    def test_client_ask_add(self):
        """Test client.ask for addition"""
        # Set up the mock to return a specific response
        self.mock_client.ask.return_value = "5 + 3 = 8"
        
        # Use the mock client
        response = self.mock_client.ask("Add 5 and 3")
        
        # Verify the response
        self.assertEqual(response, "5 + 3 = 8")
        
        # Verify the mock was called with the right argument
        self.mock_client.ask.assert_called_once_with("Add 5 and 3")
    
    def test_client_ask_error(self):
        """Test client error handling"""
        # Set up the mock to raise an exception
        self.mock_client.ask.side_effect = Exception("Connection error")
        
        # Check that the exception is propagated
        with self.assertRaises(Exception):
            response = self.mock_client.ask("Add 5 and 3")

# --- Integration Tests ---

def setup_test_server():
    """Set up a test server with our calculator agent"""
    import multiprocessing
    from python_a2a import A2AServer, run_server
    
    # Create a proper A2A server using our calculator agent
    class A2ACalculatorAgent(A2AServer):
        def __init__(self):
            calculator = CalculatorAgent()
            super().__init__(agent_card=calculator.agent_card)
            self.calculator = calculator
        
        def handle_task(self, task):
            return self.calculator.handle_task(task)
    
    # Find an available port
    import socket
    def find_free_port():
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('localhost', 0))
            return s.getsockname()[1]
    
    port = find_free_port()
    
    # Start the server in a separate process
    server = A2ACalculatorAgent()
    process = multiprocessing.Process(
        target=run_server,
        args=(server,),
        kwargs={"port": port, "host": "localhost"}
    )
    process.start()
    
    # Wait for server to start
    time.sleep(1)
    
    return process, port

def run_integration_tests(port):
    """Run integration tests against a live server"""
    from python_a2a import A2AClient
    
    print("Running integration tests against live server...")
    results = []
    
    try:
        # Create a real client connected to our test server
        client = A2AClient(f"http://localhost:{port}")
        
        # Test 1: Get agent card
        try:
            agent_card = client.agent_card
            if agent_card.name == "Calculator Agent":
                results.append(("Get agent card", "✅ Success"))
            else:
                results.append(("Get agent card", f"❌ Failed - Expected 'Calculator Agent', got '{agent_card.name}'"))
        except Exception as e:
            results.append(("Get agent card", f"❌ Failed - {str(e)}"))
        
        # Test 2: Addition
        try:
            response = client.ask("Add 5 and 3")
            if "5" in response and "3" in response and "8" in response:
                results.append(("Addition", "✅ Success"))
            else:
                results.append(("Addition", f"❌ Failed - Expected response with '8', got '{response}'"))
        except Exception as e:
            results.append(("Addition", f"❌ Failed - {str(e)}"))
        
        # Test 3: Subtraction
        try:
            response = client.ask("What is 10 - 4?")
            if "10" in response and "4" in response and "6" in response:
                results.append(("Subtraction", "✅ Success"))
            else:
                results.append(("Subtraction", f"❌ Failed - Expected response with '6', got '{response}'"))
        except Exception as e:
            results.append(("Subtraction", f"❌ Failed - {str(e)}"))
        
        # Test 4: Multiplication
        try:
            response = client.ask("Multiply 7 by 8")
            if "7" in response and "8" in response and "56" in response:
                results.append(("Multiplication", "✅ Success"))
            else:
                results.append(("Multiplication", f"❌ Failed - Expected response with '56', got '{response}'"))
        except Exception as e:
            results.append(("Multiplication", f"❌ Failed - {str(e)}"))
        
        # Test 5: Division
        try:
            response = client.ask("Divide 20 by 5")
            if "20" in response and "5" in response and "4" in response:
                results.append(("Division", "✅ Success"))
            else:
                results.append(("Division", f"❌ Failed - Expected response with '4', got '{response}'"))
        except Exception as e:
            results.append(("Division", f"❌ Failed - {str(e)}"))
        
        # Test 6: Division by zero
        try:
            response = client.ask("Divide 10 by 0")
            if "error" in response.lower() or "cannot" in response.lower():
                results.append(("Division by zero", "✅ Success - Error handled correctly"))
            else:
                results.append(("Division by zero", f"❌ Failed - Expected error message, got '{response}'"))
        except Exception as e:
            # If this raises an exception, that's also acceptable
            results.append(("Division by zero", "✅ Success - Exception raised as expected"))
        
    except Exception as e:
        results.append(("Client connection", f"❌ Failed - {str(e)}"))
    
    return results

def main():
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Parse command line arguments
    args = parse_arguments()
    
    print("\n🧪 Testing A2A Agents Example 🧪")
    print("Learn how to test A2A agents using various strategies\n")
    
    # Run unit tests
    if args.run_tests and args.test_type in ["unit", "all"]:
        print("\n=== Running Unit Tests ===")
        unittest.TextTestRunner().run(unittest.makeSuite(TestCalculatorAgent))
    else:
        print("\n=== Unit Test Examples ===")
        print("Unit tests for the Calculator Agent methods:")
        print("- test_add: Test addition functionality")
        print("- test_subtract: Test subtraction functionality")
        print("- test_multiply: Test multiplication functionality")
        print("- test_divide: Test division functionality")
        print("- test_handle_task_add: Test handling tasks with addition")
        print("- test_handle_task_invalid: Test handling invalid inputs")
    
    # Run mock client tests
    if args.run_tests and args.test_type in ["mock", "all"]:
        print("\n=== Running Mock Client Tests ===")
        unittest.TextTestRunner().run(unittest.makeSuite(TestCalculatorAgentWithMockClient))
    else:
        print("\n=== Mock Client Test Examples ===")
        print("Tests using mock A2A clients:")
        print("- test_client_ask_add: Test client addition request")
        print("- test_client_ask_error: Test client error handling")
    
    # Run integration tests
    if args.run_tests and args.test_type in ["integration", "all"]:
        print("\n=== Running Integration Tests ===")
        # Set up the test server
        server_process, port = setup_test_server()
        
        try:
            # Run integration tests
            results = run_integration_tests(port)
            
            # Display results
            print("\nIntegration Test Results:")
            for test_name, result in results:
                print(f"{test_name}: {result}")
                
        finally:
            # Clean up the server process
            print("\nStopping test server...")
            server_process.terminate()
            server_process.join(timeout=2)
            print("Test server stopped")
    else:
        print("\n=== Integration Test Examples ===")
        print("Tests against a live A2A server:")
        print("- Get agent card: Verify agent information")
        print("- Addition: Test adding two numbers")
        print("- Subtraction: Test subtracting two numbers")
        print("- Multiplication: Test multiplying two numbers")
        print("- Division: Test dividing two numbers")
        print("- Division by zero: Test error handling for division by zero")
    
    # Show usage patterns
    print("\n=== Test Strategy Best Practices ===")
    print("1. Unit Testing:")
    print("   - Test individual agent methods in isolation")
    print("   - Use unittest or pytest frameworks")
    print("   - Create a test fixture (setUp) with a clean environment")
    
    print("\n2. Mock Testing:")
    print("   - Use unittest.mock to create mock clients")
    print("   - Test client-agent interactions without a live server")
    print("   - Simulate various response scenarios")
    
    print("\n3. Integration Testing:")
    print("   - Test against a live A2A server")
    print("   - Use multiprocessing to manage test servers")
    print("   - Verify end-to-end workflows")
    
    print("\n=== Example Directory Structure ===")
    print("""
project/
├── my_agent/
│   ├── __init__.py
│   ├── agent.py
│   └── skills.py
└── tests/
    ├── __init__.py
    ├── test_agent_methods.py
    ├── test_client_interactions.py
    └── test_integration.py
""")
    
    print("\n=== Example pytest Command ===")
    print("Run all tests with: pytest tests/")
    print("Run specific test file: pytest tests/test_agent_methods.py")
    print("Run with verbose output: pytest -v tests/")
    print("Run with coverage report: pytest --cov=my_agent tests/")
    
    print("\n=== What's Next? ===")
    print("1. Try creating tests for your own A2A agents")
    print("2. Set up continuous integration to run tests automatically")
    print("3. Try the 'cli_tools.py' example to learn about command-line tools")
    
    print("\n🧪 Test exploration complete! 🧪")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)