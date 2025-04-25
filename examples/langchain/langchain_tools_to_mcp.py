#!/usr/bin/env python
"""
LangChain to MCP Conversion Example

Demonstrates converting LangChain tools (including pre-built ones) to MCP endpoints.
Run with: python fixed_tool_names.py
"""

import sys
import time
import threading
import socket
import requests
from typing import Dict, Any, List

def find_available_port(start_port=5000, max_tries=10):
    """Find an available port"""
    for port in range(start_port, start_port + max_tries):
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(('localhost', port))
            sock.close()
            return port
        except OSError:
            continue
    return start_port + 1000

def run_server(server, port):
    """Run MCP server in a thread"""
    def server_thread():
        print(f"Starting MCP server on port {port}...")
        server.run(host="0.0.0.0", port=port)
    
    thread = threading.Thread(target=server_thread, daemon=True)
    thread.start()
    time.sleep(2)  # Allow server to start
    return thread

def main():
    # Import required components
    try:
        from langchain.tools import Tool
        from langchain_core.tools import BaseTool
        # Import pre-built LangChain tools
        from langchain_community.tools import DuckDuckGoSearchRun, DuckDuckGoSearchResults
        from langchain_community.tools import WikipediaQueryRun
        from langchain_community.utilities import WikipediaAPIWrapper
        from python_a2a.langchain import to_mcp_server
    except ImportError as e:
        print(f"Error importing components: {e}")
        print('Install with: pip install "python-a2a[langchain,mcp]" langchain langchain-core langchain-community wikipedia duckduckgo-search')
        return 1
    
    print("\n🚀 LangChain to MCP Example with Pre-built Tools")
    
    # Find available port
    port = find_available_port()
    print(f"Using port: {port}")
    
    # 1. Create LangChain tools
    print("\n1. Creating LangChain tools...")
    
    # Custom calculator tool
    def calculator(expression: str) -> str:
        """Evaluate a mathematical expression"""
        try:
            result = eval(expression)
            return f"Result: {expression} = {result}"
        except Exception as e:
            return f"Error: {e}"
    
    calculator_tool = Tool(
        name="calculator",
        description="Evaluate a mathematical expression",
        func=calculator
    )
    
    # Pre-built DuckDuckGo tool (search run)
    ddg_search = DuckDuckGoSearchRun()
    # Store original name for later reference
    ddg_search_name = ddg_search.name
    
    # Pre-built DuckDuckGo tool (search results)
    ddg_results = DuckDuckGoSearchResults(output_format="list")
    # Store original name for later reference
    ddg_results_name = ddg_results.name
    
    # Pre-built Wikipedia tool
    wikipedia = WikipediaQueryRun(api_wrapper=WikipediaAPIWrapper())
    # Store original name for later reference
    wikipedia_name = wikipedia.name
    
    # Create a list of tools
    tools = [calculator_tool, ddg_search, ddg_results, wikipedia]
    print(f"Created {len(tools)} tools: 1 custom, 3 pre-built")
    
    # Print actual tool names for reference
    print("Tool names for reference:")
    for tool in tools:
        print(f"  • {tool.name}: {tool.description}")
    
    # 2. Convert to MCP server
    print("\n2. Converting to MCP server...")
    try:
        mcp_server = to_mcp_server(tools)
        print("Conversion successful")
        
        # Print tools
        mcp_tools = mcp_server.get_tools()
        print(f"Available MCP tools: {len(mcp_tools)}")
        for tool in mcp_tools:
            print(f"  • {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"Conversion failed: {e}")
        return 1
    
    # 3. Start the server
    print("\n3. Starting MCP server...")
    server_thread = run_server(mcp_server, port)
    server_url = f"http://localhost:{port}"
    
    # 4. Test the tools
    print("\n4. Testing MCP tools...")
    
    # Test calculator
    print("\nTesting calculator tool:")
    try:
        calc_resp = requests.post(
            f"{server_url}/tools/calculator",
            json={"expression": "2 + 3 * 4"}
        )
        if calc_resp.status_code == 200:
            content = calc_resp.json().get("content", [])
            text = content[0].get("text") if content else "No content"
            print(f"Success! Result: {text}")
        else:
            print(f"Failed: {calc_resp.status_code} - {calc_resp.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test DuckDuckGo search run using actual name
    print(f"\nTesting DuckDuckGo search run tool (name: {ddg_search_name}):")
    try:
        ddg_resp = requests.post(
            f"{server_url}/tools/{ddg_search_name}",
            json={"query": "Obama's first name"}
        )
        if ddg_resp.status_code == 200:
            content = ddg_resp.json().get("content", [])
            text = content[0].get("text") if content else "No content"
            print(f"Success! Result snippet: {text[:100]}...")
        else:
            print(f"Failed: {ddg_resp.status_code} - {ddg_resp.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test DuckDuckGo search results using actual name
    print(f"\nTesting DuckDuckGo search results tool (name: {ddg_results_name}):")
    try:
        ddg_results_resp = requests.post(
            f"{server_url}/tools/{ddg_results_name}",
            json={"query": "Python programming"}
        )
        if ddg_results_resp.status_code == 200:
            content = ddg_results_resp.json().get("content", [])
            text = content[0].get("text") if content else "No content"
            print(f"Success! Results snippet: {text[:100]}...")
        else:
            print(f"Failed: {ddg_results_resp.status_code} - {ddg_results_resp.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test Wikipedia tool using actual name
    print(f"\nTesting Wikipedia tool (name: {wikipedia_name}):")
    try:
        wiki_resp = requests.post(
            f"{server_url}/tools/{wikipedia_name}",
            json={"query": "Hunter X Hunter"}
        )
        if wiki_resp.status_code == 200:
            content = wiki_resp.json().get("content", [])
            text = content[0].get("text") if content else "No content"
            print(f"Success! Result snippet: {text[:100]}...")
        else:
            print(f"Failed: {wiki_resp.status_code} - {wiki_resp.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # 5. Python client example
    print("\n5. Example Python client usage:")
    print(f"""
from python_a2a.mcp import MCPClient
import asyncio

async def main():
    client = MCPClient("http://localhost:5000")  # Update port as needed
    
    # Calculator
    result = await client.call_tool("calculator", expression="2 + 3 * 4")
    print(f"Calculator result: {{result}}")
    
    # DuckDuckGo search
    result = await client.call_tool("{ddg_search_name}", query="Obama's first name")
    print(f"Search result (snippet): {{result[:100]}}...")
    
    # DuckDuckGo search results
    result = await client.call_tool("{ddg_results_name}", query="Python programming")
    print(f"Search results: {{result[:100]}}...")
    
    # Wikipedia
    result = await client.call_tool("{wikipedia_name}", query="Hunter X Hunter")
    print(f"Wikipedia result (snippet): {{result[:100]}}...")

asyncio.run(main())
    """)
    
    # Keep server running for a brief period
    print(f"\nMCP server running at http://localhost:{port}")
    print("Press Ctrl+C to stop (auto-stops after 60 seconds)")
    try:
        time.sleep(60)
    except KeyboardInterrupt:
        print("\nStopping server...")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nProgram interrupted")
        sys.exit(0)