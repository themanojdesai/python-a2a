#!/usr/bin/env python
"""
An A2A agent that uses MCP to provide calculator functionality.
"""

import argparse
import asyncio
import logging
import math
import traceback
from typing import Dict, Any

from python_a2a import (
    A2AServer, Message, TextContent, FunctionCallContent, 
    FunctionResponseContent, MessageRole, run_server
)
from python_a2a.mcp import FastMCP, FastMCPAgent

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("mcp_calculator_agent")

# Create MCP server for calculations
calc_mcp = FastMCP(
    name="Calculator MCP",
    version="1.0.0",
    description="Provides mathematical calculation functions"
)

@calc_mcp.tool()
def add(a: float, b: float) -> float:
    """Add two numbers together."""
    return a + b

@calc_mcp.tool()
def subtract(a: float, b: float) -> float:
    """Subtract b from a."""
    return a - b

@calc_mcp.tool()
def multiply(a: float, b: float) -> float:
    """Multiply two numbers together."""
    return a * b

@calc_mcp.tool()
def divide(a: float, b: float) -> float:
    """Divide a by b."""
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

@calc_mcp.tool()
def sqrt(value: float) -> float:
    """Calculate the square root of a number."""
    if value < 0:
        raise ValueError("Cannot calculate square root of negative number")
    return math.sqrt(value)

class MCP_CalculatorAgent(A2AServer, FastMCPAgent):
    """
    An A2A agent that uses MCP to provide calculator functionality.
    """
    
    def __init__(self):
        """Initialize the agent with MCP server."""
        # Initialize A2A server
        A2AServer.__init__(self)
        
        # Initialize FastMCPAgent with the MCP server
        FastMCPAgent.__init__(
            self,
            mcp_servers={"calc": calc_mcp}
        )
        
        logger.info("MCP Calculator Agent initialized")
    
    async def handle_message_async(self, message: Message) -> Message:
        """Process incoming A2A messages asynchronously."""
        try:
            if message.content.type == "text":
                # Return info about available functions
                logger.info(f"Received text message: {message.content.text}")
                return Message(
                    content=TextContent(
                        text="I'm a calculator agent powered by MCP. You can call these functions:\n"
                             "- add(a, b): Adds two numbers\n"
                             "- subtract(a, b): Subtracts b from a\n"
                             "- multiply(a, b): Multiplies two numbers\n"
                             "- divide(a, b): Divides a by b\n"
                             "- sqrt(value): Calculates square root"
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            elif message.content.type == "function_call":
                function_name = message.content.name
                logger.info(f"Received function call: {function_name}")
                
                # Extract parameters
                params = {p.name: p.value for p in message.content.parameters}
                
                try:
                    # Route to appropriate MCP tool
                    if function_name == "add":
                        result = await self.call_mcp_tool("calc", "add", **params)
                    elif function_name == "subtract":
                        result = await self.call_mcp_tool("calc", "subtract", **params)
                    elif function_name == "multiply":
                        result = await self.call_mcp_tool("calc", "multiply", **params)
                    elif function_name == "divide":
                        result = await self.call_mcp_tool("calc", "divide", **params)
                    elif function_name == "sqrt":
                        result = await self.call_mcp_tool("calc", "sqrt", **params)
                    else:
                        raise ValueError(f"Unknown function: {function_name}")
                    
                    logger.info(f"Calculation result: {result}")
                    
                    # Return result as function response
                    return Message(
                        content=FunctionResponseContent(
                            name=function_name,
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                    
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"Error in function {function_name}: {error_msg}")
                    logger.error(traceback.format_exc())
                    
                    return Message(
                        content=FunctionResponseContent(
                            name=function_name,
                            response={"error": error_msg}
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
            logger.error(f"Error processing message: {e}")
            logger.error(traceback.format_exc())
            
            return Message(
                content=TextContent(
                    text=f"Error processing message: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def handle_message(self, message: Message) -> Message:
        """Process incoming A2A messages by delegating to the async handler."""
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
            
            return Message(
                content=TextContent(
                    text=f"Error processing your request: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this agent."""
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "MCP_CalculatorAgent",
            "capabilities": ["text", "function_calling"],
            "functions": ["add", "subtract", "multiply", "divide", "sqrt"]
        })
        return metadata

def main():
    parser = argparse.ArgumentParser(description="Start an MCP-powered calculator A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5004, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the MCP calculator agent
    agent = MCP_CalculatorAgent()
    
    print(f"Starting MCP Calculator A2A Agent on http://{args.host}:{args.port}/a2a")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()