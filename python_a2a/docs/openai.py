"""
Documentation utilities for A2A Protocol.
"""

# Simple stub for now - we'll implement full docs later
def generate_a2a_docs(agent_card, output_dir=None):
    """
    Generate OpenAPI documentation for A2A API
    
    Args:
        agent_card: The agent card to document
        output_dir: Optional directory to save documentation
        
    Returns:
        API specification object
    """
    # Simple implementation that just returns the agent card info
    spec = {
        "openapi": "3.0.3",
        "info": {
            "title": f"{agent_card.name} API",
            "version": agent_card.version,
            "description": agent_card.description
        },
        "paths": {
            "/agent.json": {
                "get": {
                    "summary": "Get agent card",
                    "responses": {
                        "200": {
                            "description": "Agent card"
                        }
                    }
                }
            },
            "/tasks/send": {
                "post": {
                    "summary": "Send a task",
                    "responses": {
                        "200": {
                            "description": "Task result"
                        }
                    }
                }
            }
        }
    }
    
    return spec


def generate_html_docs(spec):
    """
    Generate HTML documentation from API specification
    
    Args:
        spec: API specification
        
    Returns:
        HTML documentation string
    """
    # Simple implementation that returns basic HTML
    import json
    
    html = f"""<!DOCTYPE html>
    <html>
      <head>
        <title>A2A API Documentation</title>
        <meta charset="utf-8"/>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
          body {{ font-family: sans-serif; margin: 0; padding: 20px; }}
          h1 {{ color: #333; }}
          .endpoint {{ margin-bottom: 20px; padding: 10px; border: 1px solid #ddd; border-radius: 4px; }}
          .method {{ display: inline-block; padding: 4px 8px; border-radius: 4px; color: white; }}
          .get {{ background-color: #61affe; }}
          .post {{ background-color: #49cc90; }}
        </style>
      </head>
      <body>
        <h1>{spec['info']['title']}</h1>
        <p>{spec['info']['description']}</p>
        <h2>Version: {spec['info']['version']}</h2>
        
        <h2>Endpoints</h2>
        <div class="endpoints">
    """
    
    # Add endpoints
    for path, methods in spec['paths'].items():
        for method, details in methods.items():
            html += f"""
            <div class="endpoint">
              <span class="method {method}">{method.upper()}</span>
              <span class="path">{path}</span>
              <p>{details.get('summary', '')}</p>
            </div>
            """
    
    html += """
        </div>
      </body>
    </html>
    """
    
    return html