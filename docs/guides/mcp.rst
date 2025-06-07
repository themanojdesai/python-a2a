MCP Integration
==============

This guide explains how to use the Model Context Protocol (MCP) integration in Python A2A, featuring the new provider architecture for external MCP servers.

What is MCP?
-----------

The Model Context Protocol (MCP) is a standardized way for AI agents to access external tools and data sources. It allows agents to:

- Call functions and tools on external servers
- Access resources and data from various sources
- Extend their capabilities beyond their built-in knowledge

Python A2A provides comprehensive support for MCP through a provider-based architecture that cleanly separates external MCP servers (providers) from internal tools.

Provider Architecture Overview
-----------------------------

Python A2A features a new provider architecture that offers:

- **Clean Separation**: External MCP servers (providers) vs internal tools (servers)
- **Type Safety**: Full type hints and comprehensive error handling
- **Production Ready**: Designed for enterprise deployment
- **Extensible**: Easy to add new providers following the BaseProvider pattern

Available MCP Providers
-----------------------

GitHub MCP Provider
~~~~~~~~~~~~~~~~~~

Complete GitHub integration via the official GitHub MCP server:

.. code-block:: python

    from python_a2a.mcp.providers import GitHubMCPServer
    
    # Using context manager (recommended)
    async with GitHubMCPServer(token="your-github-token") as github:
        # User operations
        user = await github.get_authenticated_user()
        user_info = await github.get_user("octocat")
        
        # Repository management
        repo = await github.create_repository("my-project", "A new project")
        branches = await github.list_branches("owner", "repo")
        
        # Issue tracking
        issues = await github.list_issues("owner", "repo", state="open")
        issue = await github.create_issue("owner", "repo", "Bug Report", "Description")
        
        # Pull request workflow
        pr = await github.create_pull_request(
            "owner", "repo", "Feature: Add new API", "feature", "main"
        )
        
        # File operations
        content = await github.get_file_contents("owner", "repo", "README.md")
        
    # Manual connection management
    github = GitHubMCPServer(token="your-token")
    await github.connect()
    try:
        user = await github.get_authenticated_user()
    finally:
        await github.disconnect()

**Key Features:**
- Complete GitHub API coverage
- Repository, issue, and pull request management
- File operations and branch management
- User and organization operations
- Search capabilities across repositories, issues, and code

Browserbase MCP Provider
~~~~~~~~~~~~~~~~~~~~~~~~

Browser automation and web scraping capabilities:

.. code-block:: python

    from python_a2a.mcp.providers import BrowserbaseMCPServer
    
    # Using context manager (recommended)
    async with BrowserbaseMCPServer(
        api_key="your-api-key",
        project_id="your-project-id"
    ) as browser:
        # Navigation
        await browser.navigate("https://example.com")
        await browser.navigate_back()
        await browser.navigate_forward()
        
        # Screenshots and snapshots
        screenshot = await browser.take_screenshot()
        snapshot = await browser.create_snapshot()
        
        # Element interactions (requires snapshot refs)
        await browser.click_element("Submit button", "ref_from_snapshot")
        await browser.type_text("Email input", "ref_from_snapshot", "user@example.com")
        await browser.hover_element("Menu item", "ref_from_snapshot")
        
        # Form handling
        await browser.select_option("Country dropdown", "ref_from_snapshot", ["US"])
        await browser.press_key("Enter", "Submit form")
        
        # Data extraction
        title = await browser.get_text("h1")
        page_content = await browser.get_text("body")
        
        # Session management
        context = await browser.create_context()
        session = await browser.create_session()

**Key Features:**
- Cloud-based browser automation
- Element interaction with snapshot-based references
- Screenshot and page analysis capabilities
- Session and context management
- Form handling and data extraction

Filesystem MCP Provider
~~~~~~~~~~~~~~~~~~~~~~~

Secure file operations with sandboxing:

.. code-block:: python

    from python_a2a.mcp.providers import FilesystemMCPServer
    
    # Using context manager (recommended)
    async with FilesystemMCPServer(
        allowed_directories=["/app/data", "/tmp/uploads"]
    ) as fs:
        # File operations
        content = await fs.read_file("/app/data/config.json")
        await fs.write_file("/tmp/output.txt", "Processed data")
        
        # Directory management
        files = await fs.list_directory("/app/data")
        await fs.create_directory("/tmp/new_folder")
        tree = await fs.directory_tree("/app/data")
        
        # Search and metadata
        matches = await fs.search_files("/app/data", "*.json")
        info = await fs.get_file_info("/app/data/large_file.csv")
        
        # Bulk operations
        multiple_files = await fs.read_multiple_files([
            "/app/data/file1.txt", "/app/data/file2.txt"
        ])
        
        # File management
        await fs.move_file("/tmp/old.txt", "/tmp/new.txt")
        
        # Security - check allowed directories
        allowed = await fs.list_allowed_directories()

**Key Features:**
- Sandboxed file operations with explicit directory permissions
- File and directory management
- Search capabilities with pattern matching
- Metadata extraction and file information
- Bulk operations for efficiency

Creating Agents with MCP Providers
----------------------------------

You can easily integrate MCP providers with A2A agents:

.. code-block:: python

    from python_a2a import A2AServer, AgentCard, run_server
    from python_a2a.mcp.providers import GitHubMCPServer, FilesystemMCPServer
    from python_a2a import TaskStatus, TaskState
    
    class DevOpsAgent(A2AServer):
        def __init__(self):
            agent_card = AgentCard(
                name="DevOps Assistant",
                description="Automates development workflows",
                url="http://localhost:5000",
                version="1.0.0"
            )
            super().__init__(agent_card=agent_card)
            
            # Initialize MCP providers
            self.github = GitHubMCPServer(token="your-github-token")
            self.fs = FilesystemMCPServer(allowed_directories=["/tmp", "/app/logs"])
        
        async def handle_task_async(self, task):
            try:
                text = task.message.get("content", {}).get("text", "")
                
                if "create repository" in text.lower():
                    # Use GitHub provider
                    async with self.github:
                        repo = await self.github.create_repository(
                            "new-project", "Automated repository creation"
                        )
                        
                        task.artifacts = [{
                            "parts": [{"type": "text", 
                                     "text": f"Created repository: {repo['html_url']}"}]
                        }]
                        task.status = TaskStatus(state=TaskState.COMPLETED)
                
                elif "backup logs" in text.lower():
                    # Use filesystem provider
                    async with self.fs:
                        log_files = await self.fs.search_files("/app/logs", "*.log")
                        backup_content = ""
                        
                        for log_file in log_files:
                            content = await self.fs.read_file(log_file)
                            backup_content += f"=== {log_file} ===\n{content}\n\n"
                        
                        await self.fs.write_file("/tmp/logs_backup.txt", backup_content)
                        
                        task.artifacts = [{
                            "parts": [{"type": "text", 
                                     "text": f"Backed up {len(log_files)} log files to /tmp/logs_backup.txt"}]
                        }]
                        task.status = TaskStatus(state=TaskState.COMPLETED)
                
                else:
                    task.artifacts = [{
                        "parts": [{"type": "text", 
                                 "text": "I can help with repository creation and log backup operations."}]
                    }]
                    task.status = TaskStatus(state=TaskState.COMPLETED)
                
                return task
                
            except Exception as e:
                task.artifacts = [{
                    "parts": [{"type": "text", "text": f"Error: {str(e)}"}]
                }]
                task.status = TaskStatus(state=TaskState.FAILED)
                return task
        
        def handle_task(self, task):
            import asyncio
            loop = asyncio.get_event_loop()
            return loop.run_until_complete(self.handle_task_async(task))
    
    # Run the agent
    if __name__ == "__main__":
        agent = DevOpsAgent()
        run_server(agent, port=5000)

Provider Configuration Options
-----------------------------

Each provider supports various configuration options:

GitHub Provider Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    github = GitHubMCPServer(
        token="your-github-token",          # Required: GitHub personal access token
        use_docker=True,                    # Use Docker (True) or NPX (False)
        github_host="github.enterprise.com" # Optional: GitHub Enterprise host
    )

Browserbase Provider Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    browser = BrowserbaseMCPServer(
        api_key="your-api-key",           # Required: Browserbase API key
        project_id="your-project-id",     # Required: Browserbase project ID
        use_npx=True,                     # Use NPX to run the server
        context_id="specific-context",    # Optional: Specific context ID
        enable_proxies=False,             # Enable Browserbase proxies
        enable_stealth=False,             # Enable advanced stealth mode
        browser_width=1280,               # Browser viewport width
        browser_height=720                # Browser viewport height
    )

Filesystem Provider Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    fs = FilesystemMCPServer(
        allowed_directories=[              # Required: Allowed directory list
            "/app/data",
            "/tmp/uploads",
            "/home/user/documents"
        ],
        use_npx=True                      # Use NPX to run the server
    )

Error Handling and Best Practices
---------------------------------

Provider Error Handling
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from python_a2a.mcp.providers.base import ProviderToolError
    
    async with GitHubMCPServer(token="your-token") as github:
        try:
            repo = await github.create_repository("existing-repo")
        except ProviderToolError as e:
            print(f"GitHub API error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

Resource Management
~~~~~~~~~~~~~~~~~~

Always use context managers for proper resource cleanup:

.. code-block:: python

    # Good: Using context manager
    async with GitHubMCPServer(token="token") as github:
        result = await github.get_user("octocat")
    # Connection automatically closed
    
    # Acceptable: Manual management
    github = GitHubMCPServer(token="token")
    await github.connect()
    try:
        result = await github.get_user("octocat")
    finally:
        await github.disconnect()

Security Considerations
~~~~~~~~~~~~~~~~~~~~~~

- **API Keys**: Store API keys in environment variables, not in code
- **Directory Permissions**: Filesystem provider only accesses explicitly allowed directories
- **Token Scope**: Use minimal GitHub token permissions for your use case
- **Browser Security**: Browserbase provides isolated browser environments

.. code-block:: python

    import os
    
    # Good: Using environment variables
    github = GitHubMCPServer(token=os.getenv("GITHUB_TOKEN"))
    
    # Good: Limiting filesystem access
    fs = FilesystemMCPServer(allowed_directories=["/app/data"])  # Only this directory

Migration from Previous MCP Implementation
------------------------------------------

Updating Imports
~~~~~~~~~~~~~~~

.. code-block:: python

    # Old way (deprecated)
    from python_a2a.mcp.servers_github import GitHubMCPServer
    
    # New way (provider architecture)
    from python_a2a.mcp.providers import GitHubMCPServer

The usage API remains the same, but you get the benefits of the new provider architecture.

Creating Custom Providers
-------------------------

You can create custom MCP providers by extending the BaseProvider class:

.. code-block:: python

    from python_a2a.mcp.providers.base import BaseProvider
    from python_a2a.mcp.server_config import ServerConfig
    from typing import Dict, Any
    
    class CustomMCPProvider(BaseProvider):
        def __init__(self, api_key: str):
            self.api_key = api_key
            super().__init__()
        
        def _create_config(self) -> ServerConfig:
            """Create MCP server configuration."""
            return ServerConfig(
                command=["npx", "@your-org/custom-mcp-server"],
                env={"API_KEY": self.api_key}
            )
        
        def _get_provider_name(self) -> str:
            """Get provider name."""
            return "custom"
        
        # Add your custom methods
        async def custom_operation(self, param: str) -> Dict[str, Any]:
            """Perform a custom operation."""
            return await self._call_tool("custom_tool", {"param": param})

Advanced Features
----------------

Tool Discovery
~~~~~~~~~~~~~~

All providers support tool discovery:

.. code-block:: python

    async with GitHubMCPServer(token="token") as github:
        tools = await github.list_tools()
        for tool in tools:
            print(f"Tool: {tool['name']} - {tool['description']}")

Multiple Provider Usage
~~~~~~~~~~~~~~~~~~~~~~

Use multiple providers in the same application:

.. code-block:: python

    async def automation_workflow():
        # Use multiple providers concurrently
        async with GitHubMCPServer(token="github-token") as github, \
                   FilesystemMCPServer(allowed_directories=["/tmp"]) as fs:
            
            # Get repository content
            content = await github.get_file_contents("owner", "repo", "data.json")
            
            # Process and save locally
            processed_data = process_data(content)
            await fs.write_file("/tmp/processed.json", processed_data)
            
            # Create an issue with results
            await github.create_issue(
                "owner", "repo", "Data Processing Complete",
                f"Processed data saved to local storage"
            )

Next Steps
---------

Now that you understand the MCP provider architecture, you can:

- Build agents that integrate with external services
- Create custom providers for your specific MCP servers
- Combine multiple providers for complex workflows
- Deploy production-ready agents with external tool access

Check out the :doc:`../examples/index` for complete working examples with all three providers.