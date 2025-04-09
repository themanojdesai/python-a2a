# examples/function_calling/calculator_agent.py
"""
An agent that provides mathematical calculation functions.
"""

import os
import argparse
import math
from python_a2a import (
    A2AServer, Message, TextContent, FunctionCallContent, 
    FunctionResponseContent, FunctionParameter, MessageRole, run_server
)

class CalculatorAgent(A2AServer):
    """An agent that provides mathematical calculation functions."""
    
    def handle_message(self, message):
        """Process incoming A2A messages for calculations."""
        if message.content.type == "text":
            return Message(
                content=TextContent(
                    text="I'm a calculator agent. You can call my calculation functions:\n"
                         "- calculate: Performs basic arithmetic (operation, a, b)\n"
                         "- sqrt: Calculates square root (value)\n"
                         "- power: Calculates exponents (base, exponent)\n"
                         "- sin/cos/tan: Trigonometric functions (angle_degrees)"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
            
        elif message.content.type == "function_call":
            function_name = message.content.name
            params = {p.name: p.value for p in message.content.parameters}
            
            try:
                if function_name == "calculate":
                    operation = params.get("operation", "add")
                    a = float(params.get("a", 0))
                    b = float(params.get("b", 0))
                    
                    if operation == "add":
                        result = a + b
                    elif operation == "subtract":
                        result = a - b
                    elif operation == "multiply":
                        result = a * b
                    elif operation == "divide":
                        if b == 0:
                            raise ValueError("Division by zero")
                        result = a / b
                    else:
                        raise ValueError(f"Unknown operation: {operation}")
                    
                    return Message(
                        content=FunctionResponseContent(
                            name="calculate",
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                elif function_name == "sqrt":
                    value = float(params.get("value", 0))
                    if value < 0:
                        raise ValueError("Cannot calculate square root of negative number")
                    
                    result = math.sqrt(value)
                    return Message(
                        content=FunctionResponseContent(
                            name="sqrt",
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                elif function_name == "power":
                    base = float(params.get("base", 0))
                    exponent = float(params.get("exponent", 0))
                    result = math.pow(base, exponent)
                    
                    return Message(
                        content=FunctionResponseContent(
                            name="power",
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                elif function_name in ["sin", "cos", "tan"]:
                    angle_degrees = float(params.get("angle_degrees", 0))
                    angle_radians = math.radians(angle_degrees)
                    
                    if function_name == "sin":
                        result = math.sin(angle_radians)
                    elif function_name == "cos":
                        result = math.cos(angle_radians)
                    else:  # tan
                        result = math.tan(angle_radians)
                    
                    return Message(
                        content=FunctionResponseContent(
                            name=function_name,
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                else:
                    raise ValueError(f"Unknown function: {function_name}")
                
            except Exception as e:
                return Message(
                    content=FunctionResponseContent(
                        name=function_name,
                        response={"error": str(e)}
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        else:
            return Message(
                content=TextContent(
                    text="I'm a calculator agent. I can perform various mathematical calculations. "
                         "Please call one of my calculation functions."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def get_metadata(self):
        """Get metadata about this agent."""
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "CalculatorAgent",
            "capabilities": ["function_calling"],
            "functions": ["calculate", "sqrt", "power", "sin", "cos", "tan"]
        })
        return metadata

def main():
    parser = argparse.ArgumentParser(description="Start a calculator A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5004, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the calculator agent
    agent = CalculatorAgent()
    
    print(f"Starting Calculator A2A Agent on http://{args.host}:{args.port}/a2a")
    
    # Run the server
# examples/function_calling/calculator_agent.py
"""
An agent that provides mathematical calculation functions.
"""

import os
import argparse
import math
from python_a2a import (
    A2AServer, Message, TextContent, FunctionCallContent, 
    FunctionResponseContent, FunctionParameter, MessageRole, run_server
)

class CalculatorAgent(A2AServer):
    """An agent that provides mathematical calculation functions."""
    
    def handle_message(self, message):
        """Process incoming A2A messages for calculations."""
        if message.content.type == "text":
            return Message(
                content=TextContent(
                    text="I'm a calculator agent. You can call my calculation functions:\n"
                         "- calculate: Performs basic arithmetic (operation, a, b)\n"
                         "- sqrt: Calculates square root (value)\n"
                         "- power: Calculates exponents (base, exponent)\n"
                         "- sin/cos/tan: Trigonometric functions (angle_degrees)"
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
            
        elif message.content.type == "function_call":
            function_name = message.content.name
            params = {p.name: p.value for p in message.content.parameters}
            
            try:
                if function_name == "calculate":
                    operation = params.get("operation", "add")
                    a = float(params.get("a", 0))
                    b = float(params.get("b", 0))
                    
                    if operation == "add":
                        result = a + b
                    elif operation == "subtract":
                        result = a - b
                    elif operation == "multiply":
                        result = a * b
                    elif operation == "divide":
                        if b == 0:
                            raise ValueError("Division by zero")
                        result = a / b
                    else:
                        raise ValueError(f"Unknown operation: {operation}")
                    
                    return Message(
                        content=FunctionResponseContent(
                            name="calculate",
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                elif function_name == "sqrt":
                    value = float(params.get("value", 0))
                    if value < 0:
                        raise ValueError("Cannot calculate square root of negative number")
                    
                    result = math.sqrt(value)
                    return Message(
                        content=FunctionResponseContent(
                            name="sqrt",
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                elif function_name == "power":
                    base = float(params.get("base", 0))
                    exponent = float(params.get("exponent", 0))
                    result = math.pow(base, exponent)
                    
                    return Message(
                        content=FunctionResponseContent(
                            name="power",
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                elif function_name in ["sin", "cos", "tan"]:
                    angle_degrees = float(params.get("angle_degrees", 0))
                    angle_radians = math.radians(angle_degrees)
                    
                    if function_name == "sin":
                        result = math.sin(angle_radians)
                    elif function_name == "cos":
                        result = math.cos(angle_radians)
                    else:  # tan
                        result = math.tan(angle_radians)
                    
                    return Message(
                        content=FunctionResponseContent(
                            name=function_name,
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                
                else:
                    raise ValueError(f"Unknown function: {function_name}")
                
            except Exception as e:
                return Message(
                    content=FunctionResponseContent(
                        name=function_name,
                        response={"error": str(e)}
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        else:
            return Message(
                content=TextContent(
                    text="I'm a calculator agent. I can perform various mathematical calculations. "
                         "Please call one of my calculation functions."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
    
    def get_metadata(self):
        """Get metadata about this agent."""
        metadata = super().get_metadata()
        metadata.update({
            "agent_type": "CalculatorAgent",
            "capabilities": ["function_calling"],
            "functions": ["calculate", "sqrt", "power", "sin", "cos", "tan"]
        })
        return metadata

def main():
    parser = argparse.ArgumentParser(description="Start a calculator A2A agent")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=5004, help="Port to listen on")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    
    args = parser.parse_args()
    
    # Create the calculator agent
    agent = CalculatorAgent()
    
    print(f"Starting Calculator A2A Agent on http://{args.host}:{args.port}/a2a")
    
    # Run the server
    run_server(agent, host=args.host, port=args.port, debug=args.debug)

if __name__ == "__main__":  
    main()