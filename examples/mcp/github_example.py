"""
GitHub MCP Server Example

This example demonstrates how to use the GitHub MCP server with python-a2a.
It shows basic GitHub operations like authentication, repository access, and file operations.
"""

import asyncio
import os
from python_a2a.mcp.providers import GitHubMCPServer


async def main():
    # Check for GitHub token
    token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
    if not token:
        print("Please set GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN environment variable")
        return

    print("🚀 GitHub MCP Server Example")
    print("=" * 60)
    print("This example demonstrates GitHub MCP server integration:")
    print("- Authentication and user operations")
    print("- Repository and file operations")
    print("- Branch and issue management\n")

    # Create GitHub MCP server instance
    github = GitHubMCPServer(token=token, use_docker=True)

    # Use context manager for resource management
    async with github:
        print("🔌 GitHub MCP server connected successfully!\n")

        # List all available tools
        print("🛠️  Available GitHub MCP Tools:")
        print("-" * 40)
        try:
            tools = await github.list_tools()
            
            # Group tools by category for better display
            tool_categories = {
                "User Operations": [],
                "Repository Operations": [],
                "Issue Operations": [],
                "Pull Request Operations": [],
                "Search Operations": []
            }
            
            for tool in tools:
                tool_name = tool.get('name', 'Unknown') if isinstance(tool, dict) else str(tool)
                
                if any(keyword in tool_name for keyword in ['user', 'me']):
                    tool_categories["User Operations"].append(tool_name)
                elif any(keyword in tool_name for keyword in ['repository', 'repo', 'file', 'branch', 'commit', 'fork']):
                    tool_categories["Repository Operations"].append(tool_name)
                elif 'issue' in tool_name:
                    tool_categories["Issue Operations"].append(tool_name)
                elif any(keyword in tool_name for keyword in ['pull', 'review']):
                    tool_categories["Pull Request Operations"].append(tool_name)
                elif 'search' in tool_name:
                    tool_categories["Search Operations"].append(tool_name)
                else:
                    tool_categories["Repository Operations"].append(tool_name)  # Default
            
            total_tools = 0
            for category, category_tools in tool_categories.items():
                if category_tools:
                    print(f"\n📂 {category}:")
                    for tool in sorted(category_tools):
                        print(f"   • {tool}")
                        total_tools += 1
            
            print(f"\n📊 Total available tools: {total_tools}")
            
        except Exception as e:
            print(f"❌ Failed to list tools: {e}")

        # Authentication test
        print(f"\n👤 Authentication Test:")
        print("-" * 30)
        user = await github.get_authenticated_user()
        if user:
            print(f"✅ Authenticated as: {user.get('login')} ({user.get('name')})")
            print(f"   📊 Public repos: {user.get('public_repos')}")
            print(f"   👥 Followers: {user.get('followers')}")
            print(f"   📍 Location: {user.get('location', 'Not set')}")
        else:
            print("❌ Authentication failed")
            return

        # File operations test
        print(f"\n📁 File Operations Test:")
        print("-" * 30)
        try:
            # Test file access on a known public repository
            file_content = await github.get_file_contents("octocat", "Hello-World", "README")
            if file_content:
                print("✅ File access working")
                print(f"   📄 File type: {file_content.get('type', 'unknown')}")
                print(f"   📏 Content size: {len(file_content.get('content', ''))} chars")
                print(f"   🔗 Download URL available: {'download_url' in file_content}")
            else:
                print("❌ No file content returned")
        except Exception as e:
            print(f"❌ File access failed: {e}")

        # Branch operations test  
        print(f"\n🌿 Branch Operations Test:")
        print("-" * 30)
        try:
            branches = await github.list_branches("octocat", "Hello-World")
            if branches:
                print(f"✅ Found {len(branches)} branches:")
                for branch in branches[:3]:  # Show first 3 branches
                    branch_name = branch.get('name', 'unknown')
                    print(f"   🌳 {branch_name}")
                    if branch.get('protected'):
                        print(f"      🔒 Protected branch")
            else:
                print("❌ No branches found")
        except Exception as e:
            print(f"❌ Branch listing failed: {e}")

        # Performance note
        print(f"\n⚠️  Performance Notes:")
        print("-" * 30)
        print("• Some operations may timeout due to response size limits")
        print("• Search operations work best with specific queries")
        print("• Large repository operations may need pagination")
        print("• File operations work well for individual files")

        # Available method categories
        print(f"\n🎯 Available Python Methods:")
        print("-" * 30)
        method_categories = {
            "🔍 Search & Discovery": [
                "search_repositories()", "search_issues()"
            ],
            "📁 Repository Management": [
                "create_repository()", "fork_repository()", "get_file_contents()",
                "list_branches()", "create_branch()"
            ],
            "🐛 Issue Management": [
                "list_issues()", "get_issue()", "create_issue()"
            ],
            "🔄 Pull Request Management": [
                "list_pull_requests()", "create_pull_request()"
            ],
            "👤 User Operations": [
                "get_authenticated_user()", "get_user()"
            ]
        }
        
        for category, methods in method_categories.items():
            print(f"\n{category}:")
            for method in methods:
                print(f"   • github.{method}")

        print("\n" + "=" * 60)
        print("🎉 GitHub MCP Integration Complete!")
        print("📚 Context manager handled connection lifecycle")
        print("🔌 MCP server automatically disconnected")


if __name__ == "__main__":
    asyncio.run(main())