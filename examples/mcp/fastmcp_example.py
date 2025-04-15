#!/usr/bin/env python
"""
Example of using FastMCP to create a simple MCP server.

This example demonstrates how to create a simple MCP server using the FastMCP
library in Python A2A.
"""

import argparse
import logging
import math
import random
from datetime import datetime

from python_a2a.mcp import FastMCP, text_response, error_response

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("fastmcp_example")

# Create a FastMCP server
mcp = FastMCP(
    name="Math & Utilities Server",
    version="1.0.0",
    description="A server providing mathematical functions and utilities.",
    dependencies=["math"]
)

# Define some tools using the decorator API

@mcp.tool()
def add(a: float, b: float) -> float:
    """
    Add two numbers together.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Sum of the two numbers
    """
    return a + b

@mcp.tool()
def subtract(a: float, b: float) -> float:
    """
    Subtract one number from another.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Result of subtracting b from a
    """
    return a - b

@mcp.tool()
def multiply(a: float, b: float) -> float:
    """
    Multiply two numbers.
    
    Args:
        a: First number
        b: Second number
        
    Returns:
        Product of the two numbers
    """
    return a * b

@mcp.tool()
def divide(a: float, b: float) -> float:
    """
    Divide one number by another.
    
    Args:
        a: First number (dividend)
        b: Second number (divisor)
        
    Returns:
        Result of dividing a by b
        
    Raises:
        ValueError: If b is zero
    """
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@mcp.tool()
def square_root(x: float) -> float:
    """
    Calculate the square root of a number.
    
    Args:
        x: Number to calculate square root of
        
    Returns:
        Square root of x
        
    Raises:
        ValueError: If x is negative
    """
    if x < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(x)

@mcp.tool()
def power(base: float, exponent: float) -> float:
    """
    Calculate a number raised to a power.
    
    Args:
        base: The base number
        exponent: The exponent
        
    Returns:
        Base raised to the exponent
    """
    return math.pow(base, exponent)

@mcp.tool()
def random_number(min_value: float = 0, max_value: float = 1) -> float:
    """
    Generate a random number in the given range.
    
    Args:
        min_value: Minimum value (inclusive)
        max_value: Maximum value (inclusive)
        
    Returns:
        Random number between min_value and max_value
    """
    return random.uniform(min_value, max_value)

@mcp.tool()
def fibonacci(n: int) -> list:
    """
    Generate the first n numbers in the Fibonacci sequence.
    
    Args:
        n: Number of Fibonacci numbers to generate
        
    Returns:
        List of the first n Fibonacci numbers
    """
    if n <= 0:
        return []
    if n == 1:
        return [0]
    if n == 2:
        return [0, 1]
    
    fib = [0, 1]
    for i in range(2, n):
        fib.append(fib[i-1] + fib[i-2])
    
    return fib

# Define some resources

@mcp.resource("math://constants/pi")
def pi_constant() -> str:
    """Get the value of pi"""
    return str(math.pi)

@mcp.resource("math://constants/e")
def e_constant() -> str:
    """Get the value of e (Euler's number)"""
    return str(math.e)

@mcp.resource("math://constants/phi")
def phi_constant() -> str:
    """Get the value of phi (golden ratio)"""
    return str((1 + math.sqrt(5)) / 2)

@mcp.resource("util://time/now")
def current_time() -> str:
    """Get the current time"""
    return datetime.now().isoformat()

@mcp.resource("util://random/{count}")
def random_numbers(count: int) -> str:
    """
    Get a list of random numbers.
    
    Args:
        count: Number of random numbers to generate
    """
    try:
        count = int(count)
        if count <= 0 or count > 1000:
            return f"Count must be between 1 and 1000, got {count}"
        
        numbers = [random.random() for _ in range(count)]
        return "\n".join(str(num) for num in numbers)
    except ValueError:
        return f"Invalid count: {count}"

def main():
    """Run the MCP server."""
    parser = argparse.ArgumentParser(description="Start a FastMCP example server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    print(f"Starting FastMCP example server at http://{args.host}:{args.port}")
    print(f"Available tools: {', '.join(mcp.tools.keys())}")
    print(f"Available resources: {', '.join(mcp.resources.keys())}")
    
    # Run the server using FastAPI transport
    mcp.run(transport="fastapi", host=args.host, port=args.port)

if __name__ == "__main__":
    main()