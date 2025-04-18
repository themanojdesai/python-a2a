"""
Example showing an A2A server with integrated FastAPI-style documentation.
"""

from flask import Flask, Response
from python_a2a import (
    A2AServer, 
    AgentCard, 
    AgentSkill, 
    Task, 
    TaskStatus, 
    TaskState,
    generate_a2a_docs, 
    generate_html_docs, 
    run_server
)


class DocumentedA2AServer(A2AServer):
    """
    A2A server with integrated FastAPI-style documentation
    """
    
    def __init__(self, agent_card, enable_docs=True):
        """
        Initialize the server with an agent card and documentation
        
        Args:
            agent_card: The agent card for the server
            enable_docs: Whether to enable documentation endpoint
        """
        super().__init__(agent_card=agent_card)
        self.enable_docs = enable_docs
    
    def setup_routes(self, app):
        """Setup Flask routes including documentation"""
        # Call parent method to set up regular routes
        super().setup_routes(app)
        
        # Add documentation endpoints if enabled
        if self.enable_docs:
            @app.route("/docs", methods=["GET"])
            def get_docs():
                """Serve interactive API documentation"""
                # Generate OpenAPI spec from agent card
                spec = generate_a2a_docs(self.agent_card)
                
                # Convert to HTML documentation
                html = generate_html_docs(spec)
                
                return Response(html, mimetype="text/html")
            
            @app.route("/openapi.json", methods=["GET"])
            def get_openapi():
                """Serve OpenAPI specification"""
                spec = generate_a2a_docs(self.agent_card)
                return spec.spec
    
    def handle_task(self, task):
        """Process an A2A task (example implementation)"""
        # Extract message text if available
        message_data = task.message or {}
        content = message_data.get("content", {})
        text = content.get("text", "") if isinstance(content, dict) else ""
        
        # Create a simple response
        if text:
            response_text = f"You said: {text}"
        else:
            response_text = "Hello! I'm a documented A2A server."
        
        # Create artifact with the response
        task.artifacts = [{
            "parts": [{
                "type": "text",
                "text": response_text
            }]
        }]
        
        # Mark as completed
        task.status = TaskStatus(state=TaskState.COMPLETED)
        return task


def main():
    # Create an agent card
    agent_card = AgentCard(
        name="Documented API",
        description="Example A2A server with FastAPI-style documentation",
        url="http://localhost:5000",
        version="1.0.0",
        skills=[
            AgentSkill(
                name="Echo",
                description="Echo back the user's message",
                tags=["echo", "test"],
                examples=["Hello, world!", "Echo this message"]
            )
        ]
    )
    
    # Create the server
    server = DocumentedA2AServer(agent_card, enable_docs=True)
    
    # Run the server
    print("Starting documented A2A server...")
    print("Server will be available at http://localhost:5000")
    print("Documentation will be available at http://localhost:5000/docs")
    print("OpenAPI specification will be available at http://localhost:5000/openapi.json")
    run_server(server, host="0.0.0.0", port=5003)


if __name__ == "__main__":
    main()