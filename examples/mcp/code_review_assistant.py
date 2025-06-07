"""
Code Review Assistant - MCP Integration Example

This example demonstrates how to integrate multiple MCP providers with AI to create
a practical code review assistant. It shows:

1. GitHub MCP - Fetch code from repositories
2. OpenAI Integration - AI-powered code analysis
3. Browserbase MCP - Check repository documentation  
4. Filesystem MCP - Save review reports

Usage:
    python code_review_assistant.py

Requirements:
    - OpenAI API key (set OPENAI_API_KEY environment variable)
    - GitHub token (set GITHUB_TOKEN environment variable)  
    - Browserbase credentials (set BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID)
"""

import asyncio
import logging
import os
from python_a2a.client.llm import OpenAIA2AClient
from python_a2a.mcp.providers import GitHubMCPServer, BrowserbaseMCPServer, FilesystemMCPServer
from python_a2a import create_text_message

# Hide INFO logs for cleaner output
logging.getLogger('python_a2a').setLevel(logging.ERROR)
logging.getLogger('httpx').setLevel(logging.WARNING)

class CodeReviewAssistant:
    """AI-powered code review assistant using multiple MCP providers"""
    
    def __init__(self, openai_api_key=None, github_token=None, browserbase_api_key=None, browserbase_project_id=None):
        # Get credentials from environment variables or parameters
        openai_key = openai_api_key or os.getenv('OPENAI_API_KEY')
        github_token = github_token or os.getenv('GITHUB_TOKEN')
        browserbase_key = browserbase_api_key or os.getenv('BROWSERBASE_API_KEY') 
        browserbase_project = browserbase_project_id or os.getenv('BROWSERBASE_PROJECT_ID')
        
        if not openai_key:
            raise ValueError("OpenAI API key required. Set OPENAI_API_KEY environment variable or pass openai_api_key parameter.")
        if not github_token:
            raise ValueError("GitHub token required. Set GITHUB_TOKEN environment variable or pass github_token parameter.")
        if not browserbase_key or not browserbase_project:
            raise ValueError("Browserbase credentials required. Set BROWSERBASE_API_KEY and BROWSERBASE_PROJECT_ID environment variables.")
        
        # AI reviewer
        self.ai = OpenAIA2AClient(api_key=openai_key)
        
        # MCP providers - clean and simple
        self.github = GitHubMCPServer(token=github_token)
        self.browser = BrowserbaseMCPServer(
            api_key=browserbase_key,
            project_id=browserbase_project
        )
        # Allow filesystem access to current directory
        current_dir = os.getcwd()
        self.files = FilesystemMCPServer(allowed_directories=[current_dir])
    
    async def review_code(self, repo_owner, repo_name, file_path):
        """Review a specific file in a repository"""
        
        async with self.github, self.browser, self.files:
            
            # 1. GitHub MCP: Get code from repository
            print(f"🐙 GitHub MCP: Fetching {file_path} from {repo_owner}/{repo_name}")
            code = await self.github.get_file_contents(repo_owner, repo_name, file_path)
            print(f"   ✓ Retrieved {len(str(code))} characters of code")
            
            # 2. OpenAI: AI reviews the code
            print("🤖 OpenAI: Analyzing code quality...")
            review_message = create_text_message(f"""
            Review this code for quality, bugs, and improvements:
            
            {code}
            
            Give me 3 key points: issues, suggestions, rating (1-10).
            """)
            response = self.ai.send_message(review_message)
            review = response.content.text
            print(f"   ✓ AI analysis completed")
            
            # 3. Browserbase MCP: Check repository documentation
            print("🌐 Browserbase MCP: Checking repository documentation...")
            await self.browser.navigate(f"https://github.com/{repo_owner}/{repo_name}")
            await self.browser.wait_time(1)
            readme_text = await self.browser.get_text("article")
            has_docs = "readme" in readme_text.lower()
            print(f"   ✓ Documentation {'found' if has_docs else 'not found'}")
            
            # 4. Filesystem MCP: Save review report to current directory
            print("📁 Filesystem MCP: Saving review report...")
            report = f"""# Code Review: {repo_owner}/{repo_name}/{file_path}

## AI Review
{review}

## Documentation Status
{'✅ Has README documentation' if has_docs else '❌ Missing documentation'}

## Summary
- Repository: {repo_owner}/{repo_name}
- File reviewed: {file_path}
- Code length: {len(str(code))} characters
- Documentation: {'Present' if has_docs else 'Missing'}
"""
            
            # Save to current directory for easy access
            current_dir = os.getcwd()
            report_filename = f"review_{repo_name}_{file_path.replace('/', '_')}.md"
            report_path = f"{current_dir}/{report_filename}"
            await self.files.write_file(report_path, report)
            print(f"   ✓ Report saved as: {report_filename} (in current directory)")
            
            return {
                "repository": f"{repo_owner}/{repo_name}",
                "file_reviewed": file_path,
                "code_length": len(str(code)),
                "ai_rating": "Analysis completed",
                "documentation_status": "Present" if has_docs else "Missing",
                "report_file": report_filename
            }

# Demo
async def demo():
    """Demo the code review assistant"""
    print("🚀 Code Review Assistant Demo")
    print("=" * 50)
    
    try:
        assistant = CodeReviewAssistant()
        
        # Review a file from a public repository
        result = await assistant.review_code("octocat", "Hello-World", "README")
        
        print("\n📊 Review Summary:")
        print("=" * 30)
        print(f"Repository: {result['repository']}")
        print(f"File: {result['file_reviewed']}")
        print(f"Code length: {result['code_length']} characters")
        print(f"Documentation: {result['documentation_status']}")
        print(f"Report: {result['report_file']}")
        
        print(f"\n✅ Complete! All MCP providers worked together seamlessly.")
        print(f"📄 Check {result['report_file']} for the full AI analysis.")
        
    except ValueError as e:
        print(f"❌ Configuration error: {e}")
        print("\n📋 Setup required:")
        print("export OPENAI_API_KEY='your-openai-key'")
        print("export GITHUB_TOKEN='your-github-token'") 
        print("export BROWSERBASE_API_KEY='your-browserbase-key'")
        print("export BROWSERBASE_PROJECT_ID='your-project-id'")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(demo())