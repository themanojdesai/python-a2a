#!/usr/bin/env python
"""
Example of integrating FastMCP with A2A agents.

This example demonstrates how to create an A2A agent that uses FastMCP to
provide powerful capabilities to clients.
"""

import argparse
import asyncio
import logging
import math
import random
import traceback
from datetime import datetime
from typing import Dict, Any, List, Optional

from python_a2a import (
    A2AServer, Message, TextContent, FunctionCallContent, 
    FunctionResponseContent, MessageRole, run_server
)
from python_a2a.mcp import (
    FastMCP, FastMCPAgent, A2AMCPAgent, text_response
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("a2a_integration_example")

# Step 1: Create a FastMCP math server
math_mcp = FastMCP(
    name="Math Server",
    version="1.0.0",
    description="A server providing mathematical functions."
)

@math_mcp.tool()
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

@math_mcp.tool()
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

@math_mcp.tool()
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

@math_mcp.tool()
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

# Step 2: Create a FastMCP utility server
util_mcp = FastMCP(
    name="Utility Server",
    version="1.0.0",
    description="A server providing utility functions."
)

@util_mcp.tool()
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

@util_mcp.tool()
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

@util_mcp.tool()
def current_time() -> str:
    """
    Get the current time.
    
    Returns:
        Current time in ISO format
    """
    return datetime.now().isoformat()

# Step 3: Create an A2A agent that uses these MCP servers
class MathUtilAgent(A2AServer, FastMCPAgent):
    """
    An A2A agent that uses FastMCP to provide mathematical and utility functions.
    
    This agent demonstrates how to integrate FastMCP with A2A by inheriting from
    both A2AServer and FastMCPAgent.
    """
    
    def __init__(self, math_mcp: FastMCP, util_mcp: FastMCP):
        """
        Initialize the agent with MCP servers.
        
        Args:
            math_mcp: Math MCP server
            util_mcp: Utility MCP server
        """
        # Initialize A2A server
        A2AServer.__init__(self)
        
        # Initialize FastMCPAgent with MCP servers
        FastMCPAgent.__init__(
            self,
            mcp_servers={
                "math": math_mcp,
                "util": util_mcp
            }
        )
        
        logger.info("Math & Utility Agent initialized with MCP servers")
    
    async def handle_message_async(self, message: Message) -> Message:
        """
        Process incoming A2A messages asynchronously.
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The agent's response message
        """
        try:
            if message.content.type == "text":
                # Extract operation from text
                text = message.content.text.lower()
                
                # Check for simple math operations in text
                if "add" in text or "sum" in text or "plus" in text:
                    # Try to extract numbers
                    import re
                    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
                    if len(numbers) >= 2:
                        try:
                            a = float(numbers[0])
                            b = float(numbers[1])
                            result = await self.call_mcp_tool("math", "add", a=a, b=b)
                            return Message(
                                content=TextContent(text=f"The sum of {a} and {b} is {result}"),
                                role=MessageRole.AGENT,
                                parent_message_id=message.message_id,
                                conversation_id=message.conversation_id
                            )
                        except Exception as e:
                            logger.error(f"Error during add operation: {e}")
                            logger.error(traceback.format_exc())
                
                elif "subtract" in text or "minus" in text or "difference" in text:
                    # Try to extract numbers
                    import re
                    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
                    if len(numbers) >= 2:
                        try:
                            a = float(numbers[0])
                            b = float(numbers[1])
                            result = await self.call_mcp_tool("math", "subtract", a=a, b=b)
                            return Message(
                                content=TextContent(text=f"The difference between {a} and {b} is {result}"),
                                role=MessageRole.AGENT,
                                parent_message_id=message.message_id,
                                conversation_id=message.conversation_id
                            )
                        except Exception as e:
                            logger.error(f"Error during subtract operation: {e}")
                            logger.error(traceback.format_exc())
                
                elif "multiply" in text or "times" in text or "product" in text:
                    # Try to extract numbers
                    import re
                    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
                    if len(numbers) >= 2:
                        try:
                            a = float(numbers[0])
                            b = float(numbers[1])
                            result = await self.call_mcp_tool("math", "multiply", a=a, b=b)
                            return Message(
                                content=TextContent(text=f"The product of {a} and {b} is {result}"),
                                role=MessageRole.AGENT,
                                parent_message_id=message.message_id,
                                conversation_id=message.conversation_id
                            )
                        except Exception as e:
                            logger.error(f"Error during multiply operation: {e}")
                            logger.error(traceback.format_exc())
                
                elif "divide" in text or "quotient" in text:
                    # Try to extract numbers
                    import re
                    numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
                    if len(numbers) >= 2:
                        try:
                            a = float(numbers[0])
                            b = float(numbers[1])
                            try:
                                result = await self.call_mcp_tool("math", "divide", a=a, b=b)
                                return Message(
                                    content=TextContent(text=f"The result of dividing {a} by {b} is {result}"),
                                    role=MessageRole.AGENT,
                                    parent_message_id=message.message_id,
                                    conversation_id=message.conversation_id
                                )
                            except ValueError as e:
                                return Message(
                                    content=TextContent(text=f"Error: {str(e)}"),
                                    role=MessageRole.AGENT,
                                    parent_message_id=message.message_id,
                                    conversation_id=message.conversation_id
                                )
                        except Exception as e:
                            logger.error(f"Error during divide operation: {e}")
                            logger.error(traceback.format_exc())
                
                elif "random" in text and "number" in text:
                    # Extract range if provided
                    import re
                    range_match = re.search(r"between\s+(\d+)\s+and\s+(\d+)", text)
                    if range_match:
                        min_value = float(range_match.group(1))
                        max_value = float(range_match.group(2))
                        try:
                            result = await self.call_mcp_tool("util", "random_number", min_value=min_value, max_value=max_value)
                            return Message(
                                content=TextContent(text=f"Random number between {min_value} and {max_value}: {result}"),
                                role=MessageRole.AGENT,
                                parent_message_id=message.message_id,
                                conversation_id=message.conversation_id
                            )
                        except Exception as e:
                            logger.error(f"Error during random_number operation: {e}")
                            logger.error(traceback.format_exc())
                    else:
                        # Use default range
                        try:
                            result = await self.call_mcp_tool("util", "random_number")
                            return Message(
                                content=TextContent(text=f"Random number between 0 and 1: {result}"),
                                role=MessageRole.AGENT,
                                parent_message_id=message.message_id,
                                conversation_id=message.conversation_id
                            )
                        except Exception as e:
                            logger.error(f"Error during random_number operation: {e}")
                            logger.error(traceback.format_exc())
                
                elif "fibonacci" in text:
                    # Extract count if provided
                    import re
                    count_match = re.search(r"(\d+)\s+(?:numbers|terms)", text)
                    if count_match:
                        count = int(count_match.group(1))
                    else:
                        count = 10  # Default to 10 numbers
                    
                    try:
                        result = await self.call_mcp_tool("util", "fibonacci", n=count)
                        return Message(
                            content=TextContent(text=f"First {count} Fibonacci numbers: {result}"),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                    except Exception as e:
                        logger.error(f"Error during fibonacci operation: {e}")
                        logger.error(traceback.format_exc())
                
                elif "time" in text:
                    try:
                        result = await self.call_mcp_tool("util", "current_time")
                        return Message(
                            content=TextContent(text=f"Current time: {result}"),
                            role=MessageRole.AGENT,
                            parent_message_id=message.message_id,
                            conversation_id=message.conversation_id
                        )
                    except Exception as e:
                        logger.error(f"Error getting current time: {e}")
                        logger.error(traceback.format_exc())
                
                # Default response if no specific operation detected
                return Message(
                    content=TextContent(
                        text="I'm a Math & Utility Agent that can perform calculations and provide utility functions. "
                             "You can ask me to:\n"
                             "- Add, subtract, multiply, or divide numbers\n"
                             "- Generate random numbers\n"
                             "- Generate Fibonacci sequences\n"
                             "- Get the current time"
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            elif message.content.type == "function_call":
                # Handle function calls by delegating to MCP
                try:
                    result = await self.handle_function_call(message.content)
                    return Message(
                        content=FunctionResponseContent(
                            name=message.content.name,
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                except Exception as e:
                    logger.error(f"Error handling function call: {e}")
                    logger.error(traceback.format_exc())
                    return Message(
                        content=FunctionResponseContent(
                            name=message.content.name,
                            response={"error": str(e)}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
            
            else:
                # Unsupported content type
                return Message(
                    content=TextContent(
                        text=f"I cannot process messages of type {message.content.type}."
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        except Exception as e:
            logger.error(f"Unhandled exception in handle_message_async: {e}")
            logger.error(traceback.format_exc())
            return Message(
                content=TextContent(
                    text=f"I encountered an error processing your request: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_message(self, message: Message) -> Message:
        """
        Process incoming A2A messages by delegating to the async handler.
        
        Args:
            message: The incoming A2A message
            
        Returns:
            The agent's response message
        """
        try:
            # Create a new event loop if necessary
            try:
                loop = asyncio.get_event_loop()
                if loop.is_closed():
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                
            return loop.run_until_complete(self.handle_message_async(message))
        except Exception as e:
            logger.error(f"Error in handle_message: {e}")
            logger.error(traceback.format_exc())
            
            # Return a friendly error message
            return Message(
                content=TextContent(
                    text=f"Sorry, there was an error processing your request: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get metadata about this agent.
        
        Returns:
            A dictionary of metadata about this agent
        """
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "MathUtilAgent",
            "capabilities": ["text", "function_calling"],
            "mcp_servers": list(self.mcp_servers.keys()),
            "functions": [
                "math:add", "math:subtract", "math:multiply", "math:divide",
                "util:random_number", "util:fibonacci", "util:current_time"
            ]
        })
        return metadata


# Step 4: Create a simpler agent using the A2AMCPAgent class
def create_simple_agent():
    """
    Create a simple agent using the A2AMCPAgent class.
    
    This demonstrates the more concise way to create an agent with MCP capabilities.
    """
    try:
        agent = A2AMCPAgent(
            name="Simple Math & Util Agent",
            description="A simple agent that provides math and utility functions.",
            mcp_servers={
                "math": math_mcp,
                "util": util_mcp
            }
        )
        return agent
    except Exception as e:
        logger.error(f"Error creating simple agent: {e}")
        logger.error(traceback.format_exc())
        raise


# Step 5: Main entry point
def main():
    """
    Main entry point for the example.
    """
    parser = argparse.ArgumentParser(description="A2A MCP Integration Example")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5000, help="Port to listen on")
    parser.add_argument("--simple", action="store_true", help="Use the simple agent")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Create the agent
        if args.simple:
            agent = create_simple_agent()
            print(f"Starting Simple Math & Utility A2A Agent on http://{args.host}:{args.port}/a2a")
        else:
            agent = MathUtilAgent(math_mcp, util_mcp)
            print(f"Starting Math & Utility A2A Agent on http://{args.host}:{args.port}/a2a")
        
        # Run the server
        run_server(agent, host=args.host, port=args.port, debug=args.debug)
    except Exception as e:
        logger.error(f"Error starting server: {e}")
        logger.error(traceback.format_exc())
        print(f"Error starting server: {e}")
        return 1

    return 0


if __name__ == "__main__":
    main()