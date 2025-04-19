"""
Example of a simple A2A-compatible agent using flask
"""

import os
from flask import Flask, request, jsonify
import sys
import json

# Add parent directory to path to import the library
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from python_a2a import (
    A2AServer, Message, Conversation, TextContent, 
    FunctionResponseContent, MessageRole, Message
)

class SimpleCalculatorAgent(A2AServer):
    """A simple calculator agent that can perform basic math operations"""
    
    def handle_message(self, message: Message) -> Message:
        """Process incoming messages"""
        
        # Handle text messages
        if message.content.type == Message:
            return Message(
                content=TextContent(
                    text="I'm a calculator agent. You can call my 'calculate' function with 'operation', 'a', and 'b' parameters."
                ),
                role=MessageRole.AGENT,
                parent_message_id=message.message_id,
                conversation_id=message.conversation_id
            )
            
        # Handle function calls
        elif message.content.type == Message.FUNCTION_CALL:
            function_name = message.content.name
            
            if function_name == "calculate":
                # Extract parameters
                params = {p.name: p.value for p in message.content.parameters}
                operation = params.get("operation", "")
                a = params.get("a", 0)
                b = params.get("b", 0)
                
                # Perform calculation
                result = None
                error = None
                
                try:
                    if operation == "add":
                        result = a + b
                    elif operation == "subtract":
                        result = a - b
                    elif operation == "multiply":
                        result = a * b
                    elif operation == "divide":
                        if b == 0:
                            error = "Division by zero"
                        else:
                            result = a / b
                    else:
                        error = f"Unknown operation: {operation}"
                except Exception as e:
                    error = str(e)
                
                # Create response
                if error:
                    return Message(
                        content=FunctionResponseContent(
                            name="calculate",
                            response={"error": error}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
                else:
                    return Message(
                        content=FunctionResponseContent(
                            name="calculate",
                            response={"result": result}
                        ),
                        role=MessageRole.AGENT,
                        parent_message_id=message.message_id,
                        conversation_id=message.conversation_id
                    )
            else:
                return Message(
                    content=FunctionResponseContent(
                        name=function_name,
                        response={"error": f"Unknown function: {function_name}"}
                    ),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
        
        # Handle other message types
        return Message(
            content=TextContent(text=f"I don't understand messages of type: {message.content.type}"),
            role=MessageRole.AGENT,
            parent_message_id=message.message_id,
            conversation_id=message.conversation_id
        )


# Create a Flask server to host the agent
app = Flask(__name__)
agent = SimpleCalculatorAgent()

@app.route("/a2a", methods=["POST"])
def handle_a2a():
    """Handle A2A protocol requests"""
    try:
        data = request.json
        
        # Handle either a single message or a conversation
        if "messages" in data:
            # This is a conversation
            conversation = Conversation.from_dict(data)
            response = agent.handle_conversation(conversation)
            return jsonify(response.to_dict())
        else:
            # This is a single message
            message = Message.from_dict(data)
            response = agent.handle_message(message)
            return jsonify(response.to_dict())
    except Exception as e:
        return jsonify({
            "content": {
                "type": "error",
                "message": f"Error processing request: {str(e)}"
            },
            "role": "system"
        }), 500


if __name__ == "__main__":
    print("Starting Simple Calculator A2A Agent on http://localhost:5000/a2a")
    app.run(host="0.0.0.0", port=5005, debug=True)