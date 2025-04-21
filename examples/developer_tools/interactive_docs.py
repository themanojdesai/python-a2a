#!/usr/bin/env python
"""
Interactive Documentation Generator

This example demonstrates how to generate beautiful, interactive API documentation
for A2A agents. You can use this to document your agents' capabilities, making
them more accessible to users and developers.

To run:
    python interactive_docs.py [--output-dir OUTPUT_DIR]

Example:
    python interactive_docs.py --output-dir ./docs

Requirements:
    pip install "python-a2a[server]"
"""

import os
import sys
import argparse
import json
import webbrowser
from datetime import datetime

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import python_a2a
        print("✅ Dependencies installed correctly")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e.name}")
        print("Please install required packages:")
        print("    pip install \"python-a2a[server]\"")
        return False

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Interactive Documentation Generator")
    parser.add_argument(
        "--output-dir", type=str, default="./a2a_docs",
        help="Directory to save generated documentation (default: ./a2a_docs)"
    )
    parser.add_argument(
        "--open-browser", action="store_true", default=True,
        help="Automatically open documentation in browser"
    )
    parser.add_argument(
        "--no-open-browser", action="store_false", dest="open_browser",
        help="Don't open documentation in browser"
    )
    return parser.parse_args()

def generate_html_template():
    """Generate a basic HTML template for the documentation"""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{title}}</title>
    <style>
        :root {
            --primary-color: #4b6cb7;
            --secondary-color: #182848;
            --text-color: #333;
            --background-color: #f9f9f9;
            --card-color: #fff;
            --border-color: #e0e0e0;
            --highlight-color: #eef2ff;
            --code-background: #f5f7ff;
            --dark-text: #555;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: var(--text-color);
            background-color: var(--background-color);
            margin: 0;
            padding: 0;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        header {
            background: linear-gradient(to right, var(--primary-color), var(--secondary-color));
            color: white;
            padding: 30px 0;
            margin-bottom: 30px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        header .container {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            display: flex;
            align-items: center;
        }
        
        .logo svg {
            width: 40px;
            height: 40px;
            margin-right: 15px;
        }
        
        .logo-text {
            font-size: 24px;
            font-weight: bold;
        }
        
        .meta {
            font-size: 14px;
            opacity: 0.8;
        }
        
        h1 {
            font-size: 32px;
            margin: 0;
            font-weight: 600;
        }
        
        h2 {
            font-size: 24px;
            margin-top: 40px;
            margin-bottom: 20px;
            padding-bottom: 10px;
            border-bottom: 2px solid var(--primary-color);
            color: var(--secondary-color);
        }
        
        h3 {
            font-size: 20px;
            margin-top: 30px;
            color: var(--primary-color);
        }
        
        h4 {
            font-size: 18px;
            margin-top: 25px;
            color: var(--secondary-color);
        }
        
        .desc {
            font-size: 18px;
            max-width: 800px;
            margin: 20px 0;
            color: var(--dark-text);
        }
        
        .card {
            background-color: var(--card-color);
            border-radius: 6px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
            margin-bottom: 25px;
            padding: 20px;
            border: 1px solid var(--border-color);
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .card:hover {
            transform: translateY(-3px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
        }
        
        .skill-card {
            border-left: 4px solid var(--primary-color);
        }
        
        .skill-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .skill-name {
            font-size: 20px;
            font-weight: 600;
            color: var(--secondary-color);
            margin: 0;
        }
        
        .tag-list {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 10px 0;
        }
        
        .tag {
            background-color: var(--highlight-color);
            color: var(--primary-color);
            font-size: 12px;
            padding: 4px 8px;
            border-radius: 20px;
            font-weight: 500;
        }
        
        .example-list {
            background-color: var(--code-background);
            border-radius: 4px;
            padding: 12px 15px;
            margin: 15px 0;
            font-family: 'Consolas', monospace;
            font-size: 14px;
        }
        
        .example-title {
            font-weight: 600;
            margin-bottom: 8px;
            color: var(--secondary-color);
        }
        
        .example-item {
            background-color: white;
            border: 1px solid #e6e6e6;
            border-radius: 4px;
            padding: 8px 12px;
            margin-bottom: 8px;
        }
        
        .agent-meta {
            display: flex;
            flex-wrap: wrap;
            gap: 20px;
            margin: 20px 0;
        }
        
        .meta-item {
            display: flex;
            align-items: center;
            padding: 8px 15px;
            background-color: var(--highlight-color);
            border-radius: 20px;
            font-size: 14px;
        }
        
        .meta-item i {
            margin-right: 8px;
            color: var(--primary-color);
        }
        
        .api-section {
            margin-top: 40px;
        }
        
        .endpoint {
            display: flex;
            align-items: center;
            margin: 10px 0;
            font-family: 'Consolas', monospace;
            background-color: var(--code-background);
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
        }
        
        .http-method {
            font-weight: bold;
            color: #1a73e8;
            margin-right: 10px;
        }
        
        .url-path {
            color: #333;
        }
        
        .table-container {
            overflow-x: auto;
            margin: 20px 0;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 14px;
        }
        
        th, td {
            text-align: left;
            padding: 10px;
            border-bottom: 1px solid var(--border-color);
        }
        
        th {
            background-color: var(--highlight-color);
            color: var(--secondary-color);
            font-weight: 600;
        }
        
        tr:hover {
            background-color: #f5f5f5;
        }
        
        pre {
            background-color: var(--code-background);
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
            margin: 15px 0;
            font-family: 'Consolas', monospace;
            position: relative;
        }
        
        .copy-btn {
            position: absolute;
            top: 5px;
            right: 5px;
            background-color: rgba(255, 255, 255, 0.8);
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 4px 8px;
            font-size: 12px;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s;
        }
        
        pre:hover .copy-btn {
            opacity: 1;
        }
        
        footer {
            text-align: center;
            margin-top: 60px;
            padding: 20px;
            color: var(--dark-text);
            font-size: 14px;
            border-top: 1px solid var(--border-color);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            header .container {
                flex-direction: column;
                text-align: center;
            }
            
            .meta {
                margin-top: 15px;
            }
            
            .agent-meta {
                flex-direction: column;
                gap: 10px;
            }
        }
    </style>
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">
                <svg viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path d="M12 2C6.48 2 2 6.48 2 12C2 17.52 6.48 22 12 22C17.52 22 22 17.52 22 12C22 6.48 17.52 2 12 2ZM17 13H13V17H11V13H7V11H11V7H13V11H17V13Z" fill="white"/>
                </svg>
                <span class="logo-text">A2A API Documentation</span>
            </div>
            <div class="meta">
                Generated on {{generation_date}}
            </div>
        </div>
    </header>
    
    <div class="container">
        <h1>{{agent_name}}</h1>
        <p class="desc">{{agent_description}}</p>
        
        <div class="agent-meta">
            <div class="meta-item">
                <i>🔖</i> Version: {{agent_version}}
            </div>
            <div class="meta-item">
                <i>🔗</i> URL: <a href="{{agent_url}}" target="_blank">{{agent_url}}</a>
            </div>
            {{#if agent_provider}}
            <div class="meta-item">
                <i>🏢</i> Provider: {{agent_provider}}
            </div>
            {{/if}}
        </div>
        
        <h2>Available Skills</h2>
        
        <div class="skills-container">
            {{#each skills}}
            <div class="card skill-card">
                <div class="skill-header">
                    <h3 class="skill-name">{{this.name}}</h3>
                </div>
                
                <p>{{this.description}}</p>
                
                {{#if this.tags}}
                <div class="tag-list">
                    {{#each this.tags}}
                    <span class="tag">{{this}}</span>
                    {{/each}}
                </div>
                {{/if}}
                
                {{#if this.examples}}
                <div class="example-list">
                    <div class="example-title">Examples:</div>
                    {{#each this.examples}}
                    <div class="example-item">{{this}}</div>
                    {{/each}}
                </div>
                {{/if}}
            </div>
            {{/each}}
        </div>
        
        <h2>API Endpoints</h2>
        
        <div class="api-section">
            <h3>Agent Information</h3>
            <div class="endpoint">
                <span class="http-method">GET</span>
                <span class="url-path">{{agent_url}}/.well-known/agent.json</span>
            </div>
            <p>Returns information about the agent, including its capabilities and available skills.</p>
            
            <h4>Response Example</h4>
            <pre><code id="agent-json">{{agent_json}}</code><button class="copy-btn" onclick="copyToClipboard('agent-json')">Copy</button></pre>
        </div>
        
        <div class="api-section">
            <h3>Send Task</h3>
            <div class="endpoint">
                <span class="http-method">POST</span>
                <span class="url-path">{{agent_url}}/tasks/send</span>
            </div>
            <p>Send a task to the agent for processing.</p>
            
            <h4>Request Example</h4>
            <pre><code id="request-json">{
  "message": {
    "role": "user",
    "content": {
      "type": "text",
      "text": "Example query to the agent"
    }
  }
}</code><button class="copy-btn" onclick="copyToClipboard('request-json')">Copy</button></pre>
            
            <h4>Response Example</h4>
            <pre><code id="response-json">{
  "id": "task-1234",
  "artifacts": [
    {
      "parts": [
        {
          "type": "text",
          "text": "Response from the agent"
        }
      ]
    }
  ],
  "status": {
    "state": "completed",
    "timestamp": "2025-04-20T12:34:56Z"
  }
}</code><button class="copy-btn" onclick="copyToClipboard('response-json')">Copy</button></pre>
        </div>
        
        <h2>Client Usage</h2>
        
        <h3>Python Example</h3>
        <pre><code id="python-example">from python_a2a import A2AClient

# Connect to the agent
client = A2AClient("{{agent_url}}")

# Send a query and get a response
response = client.ask("Example query to the agent")
print(f"Response: {response}")

# Get information about the agent
agent_info = client.agent_card
print(f"Agent name: {agent_info.name}")
print(f"Available skills: {[skill.name for skill in agent_info.skills]}")</code><button class="copy-btn" onclick="copyToClipboard('python-example')">Copy</button></pre>
        
        <h3>JavaScript Example</h3>
        <pre><code id="js-example">// Example using fetch
async function queryAgent(message) {
  const response = await fetch('{{agent_url}}/tasks/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      message: {
        role: 'user',
        content: {
          type: 'text',
          text: message
        }
      }
    })
  });
  
  return await response.json();
}

// Example usage
queryAgent('Example query to the agent')
  .then(result => console.log('Response:', result))
  .catch(error => console.error('Error:', error));</code><button class="copy-btn" onclick="copyToClipboard('js-example')">Copy</button></pre>
    </div>
    
    <footer>
        <p>Documentation generated using A2A Documentation Generator</p>
        <p>Powered by the Python A2A Framework</p>
    </footer>
    
    <script>
        function copyToClipboard(elementId) {
            const element = document.getElementById(elementId);
            const text = element.textContent;
            
            navigator.clipboard.writeText(text).then(() => {
                const button = element.nextElementSibling;
                const originalText = button.textContent;
                button.textContent = 'Copied!';
                
                setTimeout(() => {
                    button.textContent = originalText;
                }, 2000);
            });
        }
        
        // Simple template engine for replacing placeholders
        function replaceTemplate() {
            const template = document.body.innerHTML;
            const data = {
                title: '{{title}}',
                generation_date: '{{generation_date}}',
                agent_name: '{{agent_name}}',
                agent_description: '{{agent_description}}',
                agent_version: '{{agent_version}}',
                agent_url: '{{agent_url}}',
                agent_provider: '{{agent_provider}}',
                agent_json: JSON.stringify({{agent_json_object}}, null, 2)
            };
            
            document.body.innerHTML = template.replace(/{{(\w+)}}/g, (match, key) => {
                return data[key] || match;
            });
        }
        
        // Replace Handlebars-style syntax
        document.addEventListener('DOMContentLoaded', replaceTemplate);
    </script>
</body>
</html>
"""

def main():
    # Check dependencies
    if not check_dependencies():
        return 1
    
    # Parse command line arguments
    args = parse_arguments()
    
    # Import after checking dependencies
    from python_a2a import AgentCard, AgentSkill, generate_a2a_docs, generate_html_docs
    
    print("\n📚 Interactive Documentation Generator 📚")
    print("Create beautiful documentation for your A2A agents")
    
    # Ensure output directory exists
    output_dir = args.output_dir
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created output directory: {output_dir}")
    
    # Define our example Weather Assistant agent
    print("\nCreating example agent card...")
    agent_card = AgentCard(
        name="Weather Assistant",
        description="A comprehensive weather information and recommendation service",
        url="https://api.example.com/a2a/weather",
        version="1.0.0",
        provider="A2A Examples",
        skills=[
            AgentSkill(
                name="Current Weather",
                description="Get current weather conditions for a location",
                tags=["weather", "current"],
                examples=[
                    "What's the weather in New York?",
                    "Current weather in Paris"
                ]
            ),
            AgentSkill(
                name="Weather Forecast",
                description="Get multi-day weather forecasts for a location",
                tags=["weather", "forecast"],
                examples=[
                    "5-day forecast for Tokyo",
                    "Weather forecast for London"
                ]
            ),
            AgentSkill(
                name="Activity Recommendations",
                description="Get weather-appropriate activity recommendations",
                tags=["activities", "recommendations"],
                examples=[
                    "What should I do in Tokyo today?",
                    "Recommend activities for Paris weather"
                ]
            )
        ],
        capabilities={
            "streaming": True,
            "stateTransitionHistory": True,
            "pushNotifications": False
        }
    )
    
    # Step 1: Generate OpenAPI specification
    print("\nGenerating OpenAPI specification...")
    
    try:
        openapi_spec = generate_a2a_docs(agent_card, output_dir)
        openapi_file = os.path.join(output_dir, "openapi.json")
        
        # Save OpenAPI spec to file
        with open(openapi_file, "w") as f:
            json.dump(openapi_spec, f, indent=2)
        
        print(f"✅ OpenAPI specification saved to: {openapi_file}")
    except Exception as e:
        print(f"❌ Error generating OpenAPI specification: {e}")
        # If the built-in function fails, create a simpler OpenAPI spec
        print("Creating basic OpenAPI specification instead...")
        
        openapi_spec = {
            "openapi": "3.0.0",
            "info": {
                "title": agent_card.name,
                "description": agent_card.description,
                "version": agent_card.version
            },
            "servers": [
                {
                    "url": agent_card.url
                }
            ],
            "paths": {
                "/.well-known/agent.json": {
                    "get": {
                        "summary": "Get agent information",
                        "description": "Returns information about the agent, including its capabilities and skills",
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {}
                                }
                            }
                        }
                    }
                },
                "/tasks/send": {
                    "post": {
                        "summary": "Send a task to the agent",
                        "description": "Sends a task for the agent to process",
                        "requestBody": {
                            "required": True,
                            "content": {
                                "application/json": {}
                            }
                        },
                        "responses": {
                            "200": {
                                "description": "Successful response",
                                "content": {
                                    "application/json": {}
                                }
                            }
                        }
                    }
                }
            },
            "components": {
                "schemas": {}
            }
        }
        
        # Save OpenAPI spec to file
        openapi_file = os.path.join(output_dir, "openapi.json")
        with open(openapi_file, "w") as f:
            json.dump(openapi_spec, f, indent=2)
        
        print(f"✅ Basic OpenAPI specification saved to: {openapi_file}")
    
    # Step 2: Generate HTML documentation
    print("\nGenerating HTML documentation...")
    
    try:
        html_doc = generate_html_docs(openapi_spec)
        html_file = os.path.join(output_dir, "index.html")
        
        with open(html_file, "w") as f:
            f.write(html_doc)
        
        print(f"✅ HTML documentation saved to: {html_file}")
    except Exception as e:
        print(f"❌ Error generating HTML documentation: {e}")
        print("Creating custom HTML documentation instead...")
        
        # Generate custom HTML doc from our template
        html_template = generate_html_template()
        
        # Prepare data for template
        today = datetime.now().strftime("%B %d, %Y at %H:%M:%S")
        agent_json = agent_card.to_dict()
        
        # Replace template placeholders
        html_doc = html_template.replace("{{title}}", f"{agent_card.name} - API Documentation")
        html_doc = html_doc.replace("{{generation_date}}", today)
        html_doc = html_doc.replace("{{agent_name}}", agent_card.name)
        html_doc = html_doc.replace("{{agent_description}}", agent_card.description)
        html_doc = html_doc.replace("{{agent_version}}", agent_card.version)
        html_doc = html_doc.replace("{{agent_url}}", agent_card.url)
        html_doc = html_doc.replace("{{agent_provider}}", agent_card.provider or "")
        html_doc = html_doc.replace("{{agent_json_object}}", json.dumps(agent_json))
        
        # Handle skills loop (simple replacement for Handlebars #each)
        skills_html = ""
        for skill in agent_card.skills:
            skill_html = '<div class="card skill-card">'
            skill_html += f'<div class="skill-header"><h3 class="skill-name">{skill.name}</h3></div>'
            skill_html += f'<p>{skill.description}</p>'
            
            if hasattr(skill, 'tags') and skill.tags:
                skill_html += '<div class="tag-list">'
                for tag in skill.tags:
                    skill_html += f'<span class="tag">{tag}</span>'
                skill_html += '</div>'
            
            if hasattr(skill, 'examples') and skill.examples:
                skill_html += '<div class="example-list"><div class="example-title">Examples:</div>'
                for example in skill.examples:
                    skill_html += f'<div class="example-item">{example}</div>'
                skill_html += '</div>'
            
            skill_html += '</div>'
            skills_html += skill_html
        
        # Replace skills placeholder
        html_doc = html_doc.replace("{{#each skills}}", "")
        html_doc = html_doc.replace("{{/each}}", "")
        html_doc = html_doc.replace('<div class="skills-container">\n            \n        </div>', 
                                   f'<div class="skills-container">\n            {skills_html}\n        </div>')
        
        # Handle conditional content
        if agent_card.provider:
            html_doc = html_doc.replace("{{#if agent_provider}}", "")
            html_doc = html_doc.replace("{{/if}}", "")
        else:
            # Remove the provider section if not present
            html_doc = html_doc.replace("{{#if agent_provider}}\n            <div class=\"meta-item\">\n                <i>🏢</i> Provider: {{agent_provider}}\n            </div>\n            {{/if}}", "")
        
        # Save the HTML file
        html_file = os.path.join(output_dir, "index.html")
        with open(html_file, "w") as f:
            f.write(html_doc)
        
        print(f"✅ Custom HTML documentation saved to: {html_file}")
    
    # Step 3: Save agent card as JSON
    print("\nSaving agent card as JSON...")
    agent_file = os.path.join(output_dir, "agent_card.json")
    
    with open(agent_file, "w") as f:
        json.dump(agent_card.to_dict(), f, indent=2)
    
    print(f"✅ Agent card saved to: {agent_file}")
    
    # Step 4: Open documentation in browser if requested
    if args.open_browser:
        html_path = os.path.abspath(os.path.join(output_dir, "index.html"))
        print(f"\nOpening documentation in browser: {html_path}")
        try:
            webbrowser.open(f"file://{html_path}")
        except Exception as e:
            print(f"❌ Error opening browser: {e}")
            print(f"You can manually open the file at: {html_path}")
    
    print("\n=== Documentation Generated ===")
    print(f"Agent Name: {agent_card.name}")
    print(f"Number of Skills: {len(agent_card.skills)}")
    print(f"Output Directory: {os.path.abspath(output_dir)}")
    
    print("\n=== Files Generated ===")
    print(f"- OpenAPI Specification: {os.path.abspath(openapi_file)}")
    print(f"- HTML Documentation: {os.path.abspath(html_file)}")
    print(f"- Agent Card JSON: {os.path.abspath(agent_file)}")
    
    print("\n=== What's Next? ===")
    print("1. Try customizing the agent card with your own skills and capabilities")
    print("2. Deploy the generated documentation to a web server for sharing")
    print("3. Try the 'testing_agents.py' example to learn about agent testing")
    
    print("\n📚 Documentation generation complete! 📚")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n✅ Program interrupted by user")
        sys.exit(0)