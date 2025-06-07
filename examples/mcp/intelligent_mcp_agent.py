"""
Intelligent Code Assistant - AI chooses which MCP tools to use

This shows the real power of MCP: the AI agent intelligently decides which tools 
to call based on the user's request. No predefined sequences!

The agent has access to:
- GitHub MCP: Repository operations
- Browserbase MCP: Web browsing  
- Filesystem MCP: File operations
- And the AI decides which ones to use and when!
"""

import asyncio
import logging
import os
from python_a2a.client.llm import OpenAIA2AClient
from python_a2a.mcp.providers import GitHubMCPServer, BrowserbaseMCPServer, FilesystemMCPServer
from python_a2a import create_text_message, create_function_call
import json

# Clean output
logging.getLogger('python_a2a').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)

class IntelligentCodeAssistant:
    """AI agent that intelligently uses MCP tools based on requests"""
    
    def __init__(self):
        # AI agent with access to tools - using GPT-4 for better reasoning
        self.ai = OpenAIA2AClient(
            api_key=os.getenv('OPENAI_API_KEY', 'your-openai-key'),
            model="gpt-4o"  # Using GPT-4 for better tool understanding
        )
        
        # MCP providers
        self.github = GitHubMCPServer(token=os.getenv('GITHUB_TOKEN', 'your-github-token'))
        self.browser = BrowserbaseMCPServer(
            api_key=os.getenv('BROWSERBASE_API_KEY', 'your-browserbase-key'),
            project_id=os.getenv('BROWSERBASE_PROJECT_ID', 'your-project-id')
        )
        current_dir = os.getcwd()
        self.files = FilesystemMCPServer(allowed_directories=[current_dir])
        
        # Tools will be discovered automatically from MCP providers
        self.available_tools = []
    
    async def discover_tools(self):
        """Automatically discover available tools from MCP providers"""
        print("🔍 Discovering available MCP tools...")
        
        tools = []
        
        # GitHub MCP tools - get ALL tools with full schema
        try:
            github_tools = await self.github.list_tools()
            for tool in github_tools:
                # Extract parameter schema from inputSchema
                schema = tool.get('inputSchema', {})
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                tools.append({
                    "provider": "github",
                    "name": tool.get('name'),
                    "description": tool.get('description', 'No description'),
                    "schema": schema,
                    "parameters": properties,
                    "required": required
                })
                print(f"   📋 GitHub: {tool.get('name')} ({len(properties)} params)")
        except Exception as e:
            print(f"   ❌ GitHub tools discovery failed: {e}")
        
        # Browserbase MCP tools
        try:
            browser_tools = await self.browser.list_tools()
            for tool in browser_tools:
                schema = tool.get('inputSchema', {})
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                tools.append({
                    "provider": "browserbase", 
                    "name": tool.get('name'),
                    "description": tool.get('description', 'No description'),
                    "schema": schema,
                    "parameters": properties,
                    "required": required
                })
                print(f"   📋 Browserbase: {tool.get('name')} ({len(properties)} params)")
        except Exception as e:
            print(f"   ❌ Browserbase tools discovery failed: {e}")
        
        # Filesystem MCP tools
        try:
            fs_tools = await self.files.list_tools()
            for tool in fs_tools:
                schema = tool.get('inputSchema', {})
                properties = schema.get('properties', {})
                required = schema.get('required', [])
                
                tools.append({
                    "provider": "filesystem",
                    "name": tool.get('name'), 
                    "description": tool.get('description', 'No description'),
                    "schema": schema,
                    "parameters": properties,
                    "required": required
                })
                print(f"   📋 Filesystem: {tool.get('name')} ({len(properties)} params)")
        except Exception as e:
            print(f"   ❌ Filesystem tools discovery failed: {e}")
        
        self.available_tools = tools
        print(f"   ✅ Discovered {len(tools)} tools total")
        return tools
    
    async def execute_tool(self, provider, tool_name, parameters):
        """Execute the chosen MCP tool dynamically"""
        print(f"🔧 Executing: {provider}.{tool_name} with {parameters}")
        
        try:
            if provider == "github":
                result = await self.github._call_tool(tool_name, parameters)
                print(f"   ✓ GitHub: Tool executed successfully")
                
            elif provider == "browserbase":
                result = await self.browser._call_tool(tool_name, parameters)
                print(f"   ✓ Browserbase: Tool executed successfully")
                
            elif provider == "filesystem":
                result = await self.files._call_tool(tool_name, parameters)
                print(f"   ✓ Filesystem: Tool executed successfully")
                
            else:
                return f"Unknown provider: {provider}"
            
            # Truncate long results for display
            if isinstance(result, str) and len(result) > 1000:
                return result[:1000] + "... (truncated)"
            return result
                
        except Exception as e:
            print(f"   ❌ Tool execution failed: {e}")
            return f"Error: {e}"
    
    async def handle_request(self, user_request):
        """Let AI decide which tools to use for the request"""
        print(f"🤖 AI analyzing request: {user_request}")
        
        async with self.github, self.browser, self.files:
            
            # First, discover available tools
            await self.discover_tools()
            
            # Create tool list with dynamic schema information
            tool_descriptions = []
            for tool in self.available_tools:
                tool_desc = {
                    "provider": tool["provider"],
                    "name": tool["name"], 
                    "description": tool["description"],
                    "parameters": tool["parameters"],  # Full parameter schema
                    "required": tool["required"]       # Required parameters
                }
                tool_descriptions.append(tool_desc)
            
            # Ask AI to plan which tools to use
            planning_prompt = f"""
            User request: {user_request}
            
            Available MCP tools with their schemas:
            {json.dumps(tool_descriptions, indent=2)}
            
            Analyze the available tools and their schemas to create a plan. 
            Use the "parameters" object to understand what each tool accepts.
            Use the "required" array to know which parameters are mandatory.
            Match parameter names EXACTLY as shown in the schema.
            
            For multi-step tasks, use {{STEP_N_RESULT}} as placeholder for results from previous steps.
            
            Return a JSON plan in this format:
            {{
                "plan": [
                    {{
                        "step": 1,
                        "provider": "provider_name",
                        "tool": "tool_name",
                        "parameters": {{
                            "param_name": "param_value"
                        }},
                        "output_name": "readme_content",
                        "reason": "why this step is needed"
                    }},
                    {{
                        "step": 2,
                        "provider": "provider_name", 
                        "tool": "tool_name",
                        "parameters": {{
                            "param_name": "{{STEP_1_RESULT}}"
                        }},
                        "process_before_use": "summarize",
                        "reason": "why this step is needed"
                    }}
                ],
                "goal": "overall objective"
            }}
            """
            
            planning_message = create_text_message(planning_prompt)
            plan_response = self.ai.send_message(planning_message)
            
            try:
                # Parse the AI's plan
                plan_text = plan_response.content.text
                json_start = plan_text.find('{')
                json_end = plan_text.rfind('}') + 1
                plan_json = plan_text[json_start:json_end]
                plan = json.loads(plan_json)
                
                print(f"📋 AI Plan: {plan.get('goal', 'Execute request')}")
                print(f"   Steps: {len(plan['plan'])}")
                
                # Execute each step of the plan
                results = []
                step_results = {}  # Store results by step number
                
                for step in plan['plan']:
                    print(f"\n📍 Step {step['step']}: {step['reason']}")
                    
                    # Replace placeholders in parameters with actual values
                    params = step['parameters'].copy()
                    for key, value in params.items():
                        if isinstance(value, str) and '{STEP_' in value:
                            # Extract step reference like {STEP_1_RESULT}
                            import re
                            match = re.search(r'\{STEP_(\d+)_RESULT\}', value)
                            if match:
                                step_num = int(match.group(1))
                                if step_num in step_results:
                                    step_data = step_results[step_num]
                                    
                                    # Process the data if needed
                                    if step.get('process_before_use') == 'summarize':
                                        summary_prompt = f"Summarize this content in 3-5 sentences:\n\n{str(step_data)[:2000]}"
                                        summary_msg = create_text_message(summary_prompt)
                                        summary_resp = self.ai.send_message(summary_msg)
                                        params[key] = summary_resp.content.text
                                    else:
                                        params[key] = str(step_data)
                    
                    result = await self.execute_tool(
                        step['provider'], 
                        step['tool'], 
                        params
                    )
                    
                    # Store result for future steps
                    step_results[step['step']] = result
                    
                    # Store result with success indicator
                    step_result = {
                        "step": step['step'],
                        "provider": step['provider'],
                        "tool": step['tool'],
                        "success": not str(result).startswith("Error:"),
                        "result": str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                    }
                    results.append(step_result)
                    
                    # If this step failed and it's critical, try alternative
                    if not step_result["success"] and step['provider'] == 'github':
                        print(f"   🔄 Trying alternative approach...")
                        # Try with different file paths
                        alt_params = dict(step['parameters'])
                        if 'path' in alt_params and alt_params['path'] == 'README.md':
                            alt_params['path'] = 'README'
                            alt_result = await self.execute_tool(
                                step['provider'], 
                                step['tool'], 
                                alt_params
                            )
                            if not str(alt_result).startswith("Error:"):
                                step_result["result"] = str(alt_result)[:200] + "..."
                                step_result["success"] = True
                                print(f"   ✅ Alternative approach succeeded!")
                
                # Ask AI to create final summary
                summary_prompt = f"""
                Original request: {user_request}
                
                Tools executed and results:
                {json.dumps(results, indent=2)}
                
                Create a concise summary of what was accomplished.
                """
                
                summary_message = create_text_message(summary_prompt)
                final_response = self.ai.send_message(summary_message)
                
                return {
                    "request": user_request,
                    "tools_discovered": len(self.available_tools),
                    "plan_executed": len(plan['plan']),
                    "summary": final_response.content.text,
                    "results": results
                }
                
            except Exception as e:
                print(f"❌ Plan execution failed: {e}")
                return {"error": f"Failed to execute plan: {e}"}

# Demo scenarios
async def demo():
    print("🧠 Intelligent Code Assistant Demo")
    print("AI decides which MCP tools to use!")
    print("=" * 60)
    
    assistant = IntelligentCodeAssistant()
    
    # Test different scenarios
    scenarios = [
        "Get the README.md file from themanojdesai/python-a2a GitHub repository and save a summary to a local file",
        "Check what branches exist in themanojdesai/python-a2a and browse their GitHub page",
        "Get information about themanojdesai/python-a2a repository and save a report"
    ]
    
    for i, request in enumerate(scenarios, 1):
        print(f"\n🎯 Scenario {i}:")
        print(f"Request: {request}")
        print("-" * 40)
        
        result = await assistant.handle_request(request)
        
        if "error" not in result:
            print(f"\n📊 Result Summary:")
            print(f"   Tools discovered: {result['tools_discovered']}")
            print(f"   Steps executed: {result['plan_executed']}")
            print(f"   Final analysis: {result['summary'][:200]}...")
        else:
            print(f"❌ {result['error']}")
        
        print(f"\n✅ Scenario {i} completed!")
        
        # Only run first scenario for demo
        break

if __name__ == "__main__":
    asyncio.run(demo())