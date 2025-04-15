#!/usr/bin/env python
"""
A math assistant agent that uses another agent's calculator functions.
"""

import argparse
import json
import logging
import re
import traceback
from typing import Dict, Any, List, Optional, Union

from python_a2a import (
    A2AServer, A2AClient, Message, TextContent, FunctionCallContent, 
    FunctionResponseContent, FunctionParameter, MessageRole, run_server
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("math_assistant_agent")

class MathAssistantAgent(A2AServer):
    """
    A math assistant agent that leverages another agent's calculator functions.
    """
    
    def __init__(self, calculator_endpoint: str):
        """
        Initialize the math assistant agent.
        
        Args:
            calculator_endpoint: Endpoint URL for the calculator agent
        """
        super().__init__()
        self.calculator_client = A2AClient(calculator_endpoint)
        self.calculator_endpoint = calculator_endpoint
        
        # Default calculator functions in case we can't fetch them
        self.calculator_functions = ["add", "subtract", "multiply", "divide", "sqrt"]
        logger.info(f"Using default calculator functions: {self.calculator_functions}")
        
        # Try to get calculator functions info, but don't fail if we can't
        try:
            self._fetch_calculator_capabilities()
        except Exception as e:
            logger.warning(f"Error fetching calculator capabilities: {e}")
        
        logger.info(f"Math Assistant Agent initialized, connected to calculator at {calculator_endpoint}")
    
    def _fetch_calculator_capabilities(self):
        """Fetch capabilities from the calculator agent."""
        try:
            init_msg = Message(
                content=TextContent(text="Hello"),
                role=MessageRole.USER
            )
            
            response = self.calculator_client.send_message(init_msg)
            
            # Extract functions from response text
            if hasattr(response.content, "text"):
                text = response.content.text
                # Parse functions from text using regex
                function_matches = re.findall(r'- (\w+)\(', text)
                if function_matches:
                    self.calculator_functions = function_matches
                    logger.info(f"Detected calculator functions: {self.calculator_functions}")
                    return
        except Exception as e:
            logger.warning(f"Error during capability detection: {e}")
            logger.warning(traceback.format_exc())
            # Continue with default functions
    
    def handle_message(self, message: Message) -> Message:
        """Process incoming A2A messages."""
        try:
            if message.content.type == "text":
                text = message.content.text.lower()
                logger.info(f"Received text message: {text}")
                
                # Handle calculation expressions in natural language
                try:
                    if "add" in text or "sum" in text or "plus" in text or "+" in text:
                        numbers = self._extract_numbers(text)
                        if len(numbers) >= 2:
                            return self._perform_calculation("add", numbers[0], numbers[1], message)
                    
                    elif "subtract" in text or "minus" in text or "difference" in text or "-" in text:
                        numbers = self._extract_numbers(text)
                        if len(numbers) >= 2:
                            return self._perform_calculation("subtract", numbers[0], numbers[1], message)
                    
                    elif "multiply" in text or "times" in text or "product" in text or "*" in text or "×" in text:
                        numbers = self._extract_numbers(text)
                        if len(numbers) >= 2:
                            return self._perform_calculation("multiply", numbers[0], numbers[1], message)
                    
                    elif "divide" in text or "quotient" in text or "/" in text or "÷" in text:
                        numbers = self._extract_numbers(text)
                        if len(numbers) >= 2:
                            return self._perform_calculation("divide", numbers[0], numbers[1], message)
                    
                    elif "sqrt" in text or "square root" in text or "√" in text:
                        numbers = self._extract_numbers(text)
                        if len(numbers) >= 1:
                            return self._perform_calculation("sqrt", numbers[0], None, message)
                    
                    # Handle expression with operator
                    elif any(op in text for op in ["+", "-", "*", "/", "^"]):
                        # Extract expression and evaluate
                        return self._handle_expression(text, message)
                
                except Exception as e:
                    logger.error(f"Error processing calculation: {e}")
                    logger.error(traceback.format_exc())
                
                # Default response
                return Message(
                    content=TextContent(
                        text="I'm a Math Assistant that can perform calculations for you. "
                             "I connect to a calculator agent to compute results. Try asking:\n"
                             "- What is 5 plus 3?\n"
                             "- Calculate 10 minus 7\n"
                             "- Multiply 4 and 9\n"
                             "- Divide 20 by 5\n"
                             "- What's the square root of 16?"
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            else:
                # Only support text messages
                return Message(
                    content=TextContent(
                        text="I only understand text messages. Please describe the calculation you want to perform."
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            logger.error(traceback.format_exc())
            
            return Message(
                content=TextContent(
                    text=f"Sorry, I encountered an error: {str(e)}"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def _extract_numbers(self, text: str) -> List[float]:
        """Extract numbers from text."""
        numbers = re.findall(r"[-+]?\d+(?:\.\d+)?", text)
        return [float(num) for num in numbers]
    
    def _perform_calculation(self, operation: str, a: float, b: Optional[float], original_message: Message) -> Message:
        """Perform a calculation by calling the calculator agent."""
        try:
            # Create parameters based on operation
            if operation == "sqrt":
                parameters = [
                    FunctionParameter(name="value", value=a)
                ]
            else:
                parameters = [
                    FunctionParameter(name="a", value=a),
                    FunctionParameter(name="b", value=b)
                ]
            
            # Create function call message
            calc_request = Message(
                content=FunctionCallContent(
                    name=operation,
                    parameters=parameters
                ),
                role=MessageRole.USER
            )
            
            # Send to calculator agent
            logger.info(f"Calling calculator with function: {operation}")
            calc_response = self.calculator_client.send_message(calc_request)
            
            # Process the response
            if calc_response.content.type == "function_response":
                result = calc_response.content.response.get("result")
                error = calc_response.content.response.get("error")
                
                if result is not None:
                    # Format the result
                    if operation == "add":
                        response_text = f"The sum of {a} and {b} is {result}"
                    elif operation == "subtract":
                        response_text = f"The difference between {a} and {b} is {result}"
                    elif operation == "multiply":
                        response_text = f"The product of {a} and {b} is {result}"
                    elif operation == "divide":
                        response_text = f"The result of dividing {a} by {b} is {result}"
                    elif operation == "sqrt":
                        response_text = f"The square root of {a} is {result}"
                    else:
                        response_text = f"The result is {result}"
                else:
                    response_text = f"Error from calculator: {error}"
            else:
                # Handle text responses or errors
                if hasattr(calc_response.content, "text"):
                    response_text = f"Calculator response: {calc_response.content.text}"
                else:
                    response_text = "Received an unexpected response from the calculator."
            
            # Return response
            return Message(
                content=TextContent(text=response_text),
                role=MessageRole.AGENT,
                parent_message_id=original_message.message_id,
                conversation_id=original_message.conversation_id
            )
            
        except Exception as e:
            error_msg = f"Error performing calculation: {str(e)}"
            logger.error(error_msg)
            logger.error(traceback.format_exc())
            
            return Message(
                content=TextContent(text=error_msg),
                role=MessageRole.AGENT,
                parent_message_id=original_message.message_id,
                conversation_id=original_message.conversation_id
            )
    
    def _handle_expression(self, text: str, original_message: Message) -> Message:
        """Handle mathematical expressions by parsing and decomposing into operations."""
        # Extract the expression
        expression_match = re.search(r'(\d+(?:\.\d+)?)\s*([\+\-\*/])\s*(\d+(?:\.\d+)?)', text)
        
        if not expression_match:
            return Message(
                content=TextContent(text="I couldn't understand the mathematical expression. Please try again."),
                role=MessageRole.AGENT,
                parent_message_id=original_message.message_id,
                conversation_id=original_message.conversation_id
            )
        
        a = float(expression_match.group(1))
        operator = expression_match.group(2)
        b = float(expression_match.group(3))
        
        # Map operator to function
        operation_map = {
            "+": "add",
            "-": "subtract",
            "*": "multiply",
            "/": "divide"
        }
        
        operation = operation_map.get(operator)
        if not operation:
            return Message(
                content=TextContent(text=f"Unsupported operator: {operator}"),
                role=MessageRole.AGENT,
                parent_message_id=original_message.message_id,
                conversation_id=original_message.conversation_id
            )
        
        # Perform the calculation
        return self._perform_calculation(operation, a, b, original_message)
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata about this agent."""
        return {
            "agent_type": "MathAssistantAgent",
            "capabilities": ["text"],
            "uses_calculator": True,
            "calculator_endpoint": self.calculator_endpoint,
            "calculator_functions": self.calculator_functions
        }

def main():
    parser = argparse.ArgumentParser(description="Start a math assistant A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5005, help="Port to listen on")
    parser.add_argument("--calculator", default="http://localhost:5004/a2a", 
                       help="Calculator agent endpoint URL")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the math assistant agent
    agent = MathAssistantAgent(args.calculator)
    
    print(f"Starting Math Assistant A2A Agent on http://{args.host}:{args.port}/a2a")
    print(f"Connected to calculator agent at {args.calculator}")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":
    main()