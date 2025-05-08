#!/usr/bin/env python
"""
MCP Tool Workflow Example

This example demonstrates how to create a workflow that uses MCP tools.
It shows:

- Setting up an MCP server with utility tools
- Creating a workflow that integrates these tools
- Running the workflow with different inputs

To run:
    python mcp_workflow.py

Requirements:
    pip install "python-a2a[mcp,all]"
"""

import sys
import os
import json
import time
import socket
import threading
import argparse
import multiprocessing
from datetime import datetime
import requests
from flask import Flask, request, jsonify

from python_a2a.mcp import FastMCP, text_response, create_fastapi_app
import uvicorn

from agent_flow.models.workflow import (
    Workflow, WorkflowNode, WorkflowEdge, NodeType, EdgeType
)
from agent_flow.models.agent import AgentRegistry
from agent_flow.models.tool import ToolRegistry, ToolDefinition, ToolSource, ToolParameter
from agent_flow.engine.executor import WorkflowExecutor


def start_mcp_server(port):
    """Start an MCP server with utility tools."""
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
        # Mock weather data
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
    
    # Run the server
    uvicorn.run(app, host="localhost", port=port)


def find_free_port():
    """Find an available port to use."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('0.0.0.0', 0))
        return s.getsockname()[1]


def create_tool_definitions(mcp_url):
    """Create tool definitions for MCP tools."""
    tool_registry = ToolRegistry()
    
    # Discover tools
    try:
        # Try to use automated discovery
        print(f"Discovering tools from MCP server at {mcp_url}...")
        discovered_tools = tool_registry.discover_tools(mcp_url)
        
        if discovered_tools:
            print(f"Successfully discovered {len(discovered_tools)} tools")
            return tool_registry
        
        print("Automatic discovery failed, creating manual definitions...")
    except:
        print("Automatic discovery failed, creating manual definitions...")
    
    # Calculator tool
    calculator = ToolDefinition(
        name="Calculator",
        description="Perform mathematical calculations",
        url=mcp_url,
        tool_path="tools/calculate",
        tool_source=ToolSource.REMOTE
    )
    
    # Add parameters
    calculator.parameters.append(
        ToolParameter(
            name="operation",
            type_name="string",
            description="Operation to perform (add, subtract, multiply, divide)",
            required=True
        )
    )
    calculator.parameters.append(
        ToolParameter(
            name="a",
            type_name="number",
            description="First number",
            required=True
        )
    )
    calculator.parameters.append(
        ToolParameter(
            name="b",
            type_name="number",
            description="Second number",
            required=True
        )
    )
    
    # Check availability
    calculator.check_availability()
    tool_registry.register(calculator)
    
    # Unit converter tool
    converter = ToolDefinition(
        name="Unit Converter",
        description="Convert between different units of measurement",
        url=mcp_url,
        tool_path="tools/convert_units",
        tool_source=ToolSource.REMOTE
    )
    
    # Add parameters
    converter.parameters.append(
        ToolParameter(
            name="value",
            type_name="number",
            description="Value to convert",
            required=True
        )
    )
    converter.parameters.append(
        ToolParameter(
            name="from_unit",
            type_name="string",
            description="Source unit",
            required=True
        )
    )
    converter.parameters.append(
        ToolParameter(
            name="to_unit",
            type_name="string",
            description="Target unit",
            required=True
        )
    )
    
    # Check availability
    converter.check_availability()
    tool_registry.register(converter)
    
    # Weather tool
    weather = ToolDefinition(
        name="Weather",
        description="Get current weather for a location",
        url=mcp_url,
        tool_path="tools/get_weather",
        tool_source=ToolSource.REMOTE
    )
    
    # Add parameters
    weather.parameters.append(
        ToolParameter(
            name="location",
            type_name="string",
            description="City name",
            required=True
        )
    )
    
    # Check availability
    weather.check_availability()
    tool_registry.register(weather)
    
    # DateTime tool
    date_time = ToolDefinition(
        name="DateTime",
        description="Get current date and time information",
        url=mcp_url,
        tool_path="tools/get_current_time",
        tool_source=ToolSource.REMOTE
    )
    
    # Check availability
    date_time.check_availability()
    tool_registry.register(date_time)
    
    return tool_registry


def create_mcp_workflow(tool_registry):
    """Create a workflow using MCP tools."""
    # Find tools in registry
    calculator = None
    converter = None
    weather = None
    date_time = None
    
    for tool in tool_registry.list_tools():
        if "Calculator" in tool.name:
            calculator = tool
        elif "Converter" in tool.name:
            converter = tool
        elif "Weather" in tool.name:
            weather = tool
        elif "DateTime" in tool.name:
            date_time = tool
    
    # Create a new workflow
    workflow = Workflow(
        name="MCP Tool Workflow",
        description="Workflow demonstrating MCP tool integration"
    )
    
    # Create nodes
    input_node = WorkflowNode(
        name="User Input",
        node_type=NodeType.INPUT,
        config={
            "input_key": "query",
            "default_value": "calculate"
        }
    )
    workflow.add_node(input_node)
    
    # Conditional node to decide which tool to use
    router_node = WorkflowNode(
        name="Query Router",
        node_type=NodeType.CONDITIONAL,
        config={
            "condition_type": "javascript",
            "condition_value": "$input.includes('calculate') || $input.includes('math')"
        }
    )
    workflow.add_node(router_node)
    
    # Calculator branch
    calc_input_node = WorkflowNode(
        name="Calculator Input",
        node_type=NodeType.TRANSFORM,
        config={
            "transform_type": "javascript",
            "transform_config": {
                "code": """
                    const input = $input.toLowerCase();
                    let a = 0, b = 0, operation = "add";
                    
                    // Extract numbers
                    const numbers = input.match(/\\d+(\\.\\d+)?/g);
                    if (numbers && numbers.length >= 2) {
                        a = parseFloat(numbers[0]);
                        b = parseFloat(numbers[1]);
                    }
                    
                    // Determine operation
                    if (input.includes('+') || input.includes('add') || input.includes('sum') || input.includes('plus')) {
                        operation = "add";
                    } else if (input.includes('-') || input.includes('subtract') || input.includes('minus')) {
                        operation = "subtract";
                    } else if (input.includes('*') || input.includes('x') || input.includes('multiply') || input.includes('times')) {
                        operation = "multiply";
                    } else if (input.includes('/') || input.includes('divide') || input.includes('divided by')) {
                        operation = "divide";
                    }
                    
                    return { operation, a, b };
                """
            }
        }
    )
    workflow.add_node(calc_input_node)
    
    calc_node = WorkflowNode(
        name="Calculator",
        node_type=NodeType.TOOL,
        config={
            "tool_id": calculator.id if calculator else ""
        }
    )
    workflow.add_node(calc_node)
    
    # Weather branch
    weather_condition = WorkflowNode(
        name="Check Weather Query",
        node_type=NodeType.CONDITIONAL,
        config={
            "condition_type": "javascript",
            "condition_value": "$input.includes('weather') || $input.includes('forecast')"
        }
    )
    workflow.add_node(weather_condition)
    
    weather_input_node = WorkflowNode(
        name="Weather Input",
        node_type=NodeType.TRANSFORM,
        config={
            "transform_type": "javascript",
            "transform_config": {
                "code": """
                    const input = $input.toLowerCase();
                    let location = "London";
                    
                    // Check for location names
                    const cities = ["london", "paris", "new york", "tokyo", "sydney"];
                    for (const city of cities) {
                        if (input.includes(city)) {
                            location = city;
                            break;
                        }
                    }
                    
                    return { location };
                """
            }
        }
    )
    workflow.add_node(weather_input_node)
    
    weather_node = WorkflowNode(
        name="Weather",
        node_type=NodeType.TOOL,
        config={
            "tool_id": weather.id if weather else ""
        }
    )
    workflow.add_node(weather_node)
    
    # Default branch (datetime)
    time_node = WorkflowNode(
        name="Current Time",
        node_type=NodeType.TOOL,
        config={
            "tool_id": date_time.id if date_time else ""
        }
    )
    workflow.add_node(time_node)
    
    # Output node
    output_node = WorkflowNode(
        name="Response",
        node_type=NodeType.OUTPUT,
        config={
            "output_key": "result"
        }
    )
    workflow.add_node(output_node)
    
    # Connect nodes
    # Input -> Router
    workflow.add_edge(
        input_node.id,
        router_node.id,
        EdgeType.DATA
    )
    
    # Router -> Calculator Input (if calculation query)
    workflow.add_edge(
        router_node.id,
        calc_input_node.id,
        EdgeType.CONDITION_TRUE
    )
    
    # Calculator Input -> Calculator
    workflow.add_edge(
        calc_input_node.id,
        calc_node.id,
        EdgeType.DATA
    )
    
    # Calculator -> Output
    workflow.add_edge(
        calc_node.id,
        output_node.id,
        EdgeType.DATA
    )
    
    # Router -> Weather Condition (if not calculation query)
    workflow.add_edge(
        router_node.id,
        weather_condition.id,
        EdgeType.CONDITION_FALSE
    )
    
    # Weather Condition -> Weather Input (if weather query)
    workflow.add_edge(
        weather_condition.id,
        weather_input_node.id,
        EdgeType.CONDITION_TRUE
    )
    
    # Weather Input -> Weather
    workflow.add_edge(
        weather_input_node.id,
        weather_node.id,
        EdgeType.DATA
    )
    
    # Weather -> Output
    workflow.add_edge(
        weather_node.id,
        output_node.id,
        EdgeType.DATA
    )
    
    # Weather Condition -> Time (if not weather query)
    workflow.add_edge(
        weather_condition.id,
        time_node.id,
        EdgeType.CONDITION_FALSE
    )
    
    # Time -> Output
    workflow.add_edge(
        time_node.id,
        output_node.id,
        EdgeType.DATA
    )
    
    return workflow


def main():
    """Run the MCP workflow example."""
    parser = argparse.ArgumentParser(description="MCP Workflow Example")
    parser.add_argument("query", nargs="?", default="calculate 5 + 3", help="Query to process")
    args = parser.parse_args()
    
    print("=== MCP Workflow Example ===\n")
    
    # Find a free port for the MCP server
    mcp_port = find_free_port()
    
    # Start MCP server
    print(f"Starting MCP server on port {mcp_port}...")
    mcp_process = multiprocessing.Process(
        target=start_mcp_server,
        args=(mcp_port,)
    )
    mcp_process.start()
    
    # Wait for server to start
    print("Waiting for MCP server to initialize...")
    time.sleep(2)
    
    try:
        # Create tool registry
        mcp_url = f"http://localhost:{mcp_port}"
        tool_registry = create_tool_definitions(mcp_url)
        
        # Create workflow
        print("\nCreating MCP tool workflow...")
        workflow = create_mcp_workflow(tool_registry)
        
        # Create executor
        executor = WorkflowExecutor(AgentRegistry(), tool_registry)
        
        # Run workflow
        print(f"\nRunning workflow with query: \"{args.query}\"...")
        try:
            result = executor.execute_workflow(workflow, {"query": args.query})
            
            print("\n=== Workflow Result ===")
            if "result" in result:
                # Extract text content if available
                if isinstance(result["result"], dict) and "content" in result["result"]:
                    content = result["result"]["content"]
                    if isinstance(content, list) and len(content) > 0:
                        text_item = next((item for item in content if "text" in item), None)
                        if text_item:
                            print(text_item["text"])
                            return 0
                
                # Otherwise print raw result
                print(json.dumps(result["result"], indent=2))
            else:
                print("No result returned")
            
        except Exception as e:
            print(f"Error running workflow: {e}")
            return 1
        
        print("\nWorkflow completed successfully!")
        return 0
        
    finally:
        # Clean up
        print("\nStopping MCP server...")
        mcp_process.terminate()
        mcp_process.join()


if __name__ == "__main__":
    sys.exit(main())