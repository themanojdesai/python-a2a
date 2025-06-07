"""
GitHub MCP Provider

High-level interface to the GitHub MCP server for GitHub API operations.
Provides typed methods for repository management, issue tracking, pull requests,
and other GitHub functionality through the official GitHub MCP server.

Usage:
    from python_a2a.mcp.providers import GitHub
    
    # Using context manager (recommended)
    async with GitHub(token="your-token") as github:
        user = await github.get_user("octocat")
        repos = await github.search_repositories("language:python")
        
    # Manual connection management
    github = GitHub(token="your-token")
    await github.connect()
    try:
        issue = await github.create_issue("owner", "repo", "Title", "Body")
    finally:
        await github.disconnect()
"""

import os
from typing import Dict, List, Optional, Any

from .base import BaseProvider, ProviderToolError
from ..server_config import ServerConfig


class GitHubMCPServer(BaseProvider):
    """
    High-level interface to the GitHub MCP server.
    
    This class provides typed methods for GitHub operations while handling
    the underlying MCP server lifecycle.
    """
    
    def __init__(self, 
                 token: Optional[str] = None,
                 use_docker: bool = True,
                 github_host: Optional[str] = None):
        """
        Initialize GitHub provider.
        
        Args:
            token: GitHub personal access token (can use env vars)
            use_docker: Use Docker (True) or NPX (False) 
            github_host: GitHub Enterprise host (optional)
        """
        # Get token from parameter or environment
        self.token = token or os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_PERSONAL_ACCESS_TOKEN")
        if not self.token:
            raise ValueError(
                "GitHub token required. Set GITHUB_TOKEN or GITHUB_PERSONAL_ACCESS_TOKEN environment variable."
            )
        
        self.use_docker = use_docker
        self.github_host = github_host
        
        # Initialize base provider
        super().__init__()
    
    def _create_config(self) -> ServerConfig:
        """Create GitHub MCP server configuration."""
        if self.use_docker:
            # Docker configuration
            args = ["run", "-i", "--rm", "-e", "GITHUB_PERSONAL_ACCESS_TOKEN"]
            env = {"GITHUB_PERSONAL_ACCESS_TOKEN": self.token}
            
            if self.github_host:
                args.extend(["-e", "GITHUB_HOST"])
                env["GITHUB_HOST"] = self.github_host
            
            args.append("ghcr.io/github/github-mcp-server")
            
            return ServerConfig(command="docker", args=args, env=env)
        else:
            # NPX configuration
            env = {"GITHUB_PERSONAL_ACCESS_TOKEN": self.token}
            if self.github_host:
                env["GITHUB_HOST"] = self.github_host
            
            return ServerConfig(
                command="npx",
                args=["-y", "@github/github-mcp-server"],
                env=env
            )
    
    def _get_provider_name(self) -> str:
        """Get provider name."""
        return "github"
    
    # User Operations
    
    async def get_authenticated_user(self) -> Dict[str, Any]:
        """
        Get information about the authenticated user.
        
        Returns:
            User information including login, name, email, etc.
        """
        return await self._call_tool("get_me", {})
    
    async def get_user(self, username: str) -> Dict[str, Any]:
        """
        Get information about a specific user.
        
        Args:
            username: GitHub username
            
        Returns:
            User information
        """
        return await self._call_tool("get_user", {"username": username})
    
    # Repository Operations
    
    async def search_repositories(self, 
                                 query: str,
                                 sort: str = "updated", 
                                 order: str = "desc",
                                 per_page: int = 30,
                                 page: int = 1) -> Dict[str, Any]:
        """
        Search for repositories.
        
        Args:
            query: Search query (e.g., "language:python", "user:octocat")
            sort: Sort by 'stars', 'forks', 'help-wanted-issues', 'updated'
            order: Sort order 'asc' or 'desc'
            per_page: Number of results per page (max 100)
            page: Page number
            
        Returns:
            Search results with repositories
        """
        return await self._call_tool("search_repositories", {
            "query": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100),  # GitHub API limit
            "page": page
        })
    
    async def get_file_contents(self, 
                               owner: str, 
                               repo: str, 
                               path: str,
                               ref: Optional[str] = None) -> Dict[str, Any]:
        """
        Get file contents from a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            ref: Git reference (branch, tag, commit SHA)
            
        Returns:
            File content and metadata
        """
        params = {"owner": owner, "repo": repo, "path": path}
        if ref:
            params["ref"] = ref
        
        return await self._call_tool("get_file_contents", params)
    
    async def create_repository(self,
                               name: str,
                               description: str = "",
                               private: bool = False,
                               has_issues: bool = True,
                               has_projects: bool = True,
                               has_wiki: bool = True) -> Dict[str, Any]:
        """
        Create a new repository.
        
        Args:
            name: Repository name
            description: Repository description
            private: Whether repository is private
            has_issues: Enable issues
            has_projects: Enable projects
            has_wiki: Enable wiki
            
        Returns:
            Created repository information
        """
        return await self._call_tool("create_repository", {
            "name": name,
            "description": description,
            "private": private,
            "has_issues": has_issues,
            "has_projects": has_projects,
            "has_wiki": has_wiki
        })
    
    async def create_or_update_file(self,
                                   owner: str,
                                   repo: str,
                                   path: str,
                                   content: str,
                                   message: str,
                                   sha: Optional[str] = None,
                                   branch: Optional[str] = None) -> Dict[str, Any]:
        """
        Create or update a single file.
        
        Args:
            owner: Repository owner
            repo: Repository name
            path: File path
            content: File content
            message: Commit message
            sha: Current file SHA (for updates)
            branch: Target branch
            
        Returns:
            File update information
        """
        params = {
            "owner": owner,
            "repo": repo,
            "path": path,
            "content": content,
            "message": message
        }
        if sha:
            params["sha"] = sha
        if branch:
            params["branch"] = branch
        return await self._call_tool("create_or_update_file", params)
    
    async def fork_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Fork a repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Forked repository information
        """
        return await self._call_tool("fork_repository", {"owner": owner, "repo": repo})
    
    async def list_branches(self, owner: str, repo: str) -> List[Dict[str, Any]]:
        """
        List repository branches.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of branches
        """
        result = await self._call_tool("list_branches", {"owner": owner, "repo": repo})
        return result if isinstance(result, list) else []
    
    async def create_branch(self,
                           owner: str,
                           repo: str,
                           branch: str,
                           from_branch: str = "main") -> Dict[str, Any]:
        """
        Create a new branch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            branch: New branch name
            from_branch: Source branch to create from
            
        Returns:
            Branch creation result
        """
        return await self._call_tool("create_branch", {
            "owner": owner,
            "repo": repo,
            "branch": branch,
            "from_branch": from_branch
        })
    
    async def list_commits(self,
                          owner: str,
                          repo: str,
                          sha: Optional[str] = None,
                          path: Optional[str] = None,
                          since: Optional[str] = None,
                          until: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Get repository commits.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: SHA or branch to start listing from
            path: Only commits containing this file path
            since: ISO 8601 date - commits after this date
            until: ISO 8601 date - commits before this date
            
        Returns:
            List of commits
        """
        params = {"owner": owner, "repo": repo}
        if sha:
            params["sha"] = sha
        if path:
            params["path"] = path
        if since:
            params["since"] = since
        if until:
            params["until"] = until
        
        result = await self._call_tool("list_commits", params)
        return result if isinstance(result, list) else []
    
    async def get_commit(self, owner: str, repo: str, sha: str) -> Dict[str, Any]:
        """
        Retrieve commit details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            sha: Commit SHA
            
        Returns:
            Commit details
        """
        return await self._call_tool("get_commit", {
            "owner": owner,
            "repo": repo,
            "sha": sha
        })
    
    async def search_code(self,
                         query: str,
                         sort: str = "indexed",
                         order: str = "desc",
                         per_page: int = 30,
                         page: int = 1) -> Dict[str, Any]:
        """
        Search code across repositories.
        
        Args:
            query: Search query
            sort: Sort by (indexed, blank)
            order: Sort order (asc, desc)
            per_page: Results per page (max 100)
            page: Page number
            
        Returns:
            Search results with items array
        """
        return await self._call_tool("search_code", {
            "query": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100),
            "page": page
        })
    
    async def push_files(self,
                        owner: str,
                        repo: str,
                        files: List[Dict[str, str]],
                        message: str,
                        branch: str = "main") -> Dict[str, Any]:
        """
        Commit multiple files at once.
        
        Args:
            owner: Repository owner
            repo: Repository name
            files: List of files with 'path' and 'content' keys
            message: Commit message
            branch: Target branch
            
        Returns:
            Commit information
        """
        return await self._call_tool("push_files", {
            "owner": owner,
            "repo": repo,
            "files": files,
            "message": message,
            "branch": branch
        })
    
    # Issue Operations
    
    async def list_issues(self,
                         owner: str,
                         repo: str,
                         state: str = "open",
                         labels: Optional[List[str]] = None,
                         sort: str = "created",
                         direction: str = "desc") -> List[Dict[str, Any]]:
        """
        List repository issues.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: Issue state ('open', 'closed', 'all')
            labels: Filter by labels
            sort: Sort by ('created', 'updated', 'comments')
            direction: Sort direction ('asc', 'desc')
            
        Returns:
            List of issues
        """
        params = {
            "owner": owner,
            "repo": repo,
            "state": state,
            "sort": sort,
            "direction": direction
        }
        if labels:
            params["labels"] = ",".join(labels)
        
        result = await self._call_tool("list_issues", params)
        return result if isinstance(result, list) else []
    
    async def get_issue(self, owner: str, repo: str, issue_number: int) -> Dict[str, Any]:
        """
        Get a specific issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            Issue details
        """
        return await self._call_tool("get_issue", {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number
        })
    
    async def create_issue(self,
                          owner: str,
                          repo: str,
                          title: str,
                          body: str = "",
                          labels: Optional[List[str]] = None,
                          assignees: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Create a new issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body
            labels: Issue labels
            assignees: Issue assignees
            
        Returns:
            Created issue information
        """
        params = {
            "owner": owner,
            "repo": repo,
            "title": title,
            "body": body
        }
        if labels:
            params["labels"] = labels
        if assignees:
            params["assignees"] = assignees
        
        return await self._call_tool("create_issue", params)
    
    async def update_issue(self,
                          owner: str,
                          repo: str,
                          issue_number: int,
                          title: Optional[str] = None,
                          body: Optional[str] = None,
                          state: Optional[str] = None,
                          labels: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Update an existing issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            title: New title
            body: New body
            state: New state (open, closed)
            labels: New labels
            
        Returns:
            Updated issue information
        """
        params = {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number
        }
        
        if title is not None:
            params["title"] = title
        if body is not None:
            params["body"] = body
        if state is not None:
            params["state"] = state
        if labels is not None:
            params["labels"] = labels
        
        return await self._call_tool("update_issue", params)
    
    async def add_issue_comment(self,
                               owner: str,
                               repo: str,
                               issue_number: int,
                               body: str) -> Dict[str, Any]:
        """
        Add a comment to an issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            body: Comment body
            
        Returns:
            Created comment information
        """
        return await self._call_tool("add_issue_comment", {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number,
            "body": body
        })
    
    async def get_issue_comments(self,
                               owner: str,
                               repo: str,
                               issue_number: int) -> List[Dict[str, Any]]:
        """
        Get issue comments.
        
        Args:
            owner: Repository owner
            repo: Repository name
            issue_number: Issue number
            
        Returns:
            List of comments
        """
        result = await self._call_tool("get_issue_comments", {
            "owner": owner,
            "repo": repo,
            "issue_number": issue_number
        })
        return result if isinstance(result, list) else []
    
    async def search_issues(self,
                           query: str,
                           sort: str = "created",
                           order: str = "desc",
                           per_page: int = 30,
                           page: int = 1) -> Dict[str, Any]:
        """
        Search for issues.
        
        Args:
            query: Search query
            sort: Sort by ('comments', 'reactions', 'author-date', 'committer-date', 'updated')
            order: Sort order ('asc', 'desc')
            per_page: Number of results per page (max 100)
            page: Page number
            
        Returns:
            Search results with issues
        """
        return await self._call_tool("search_issues", {
            "query": query,
            "sort": sort,
            "order": order,
            "per_page": min(per_page, 100),
            "page": page
        })
    
    # Pull Request Operations
    
    async def list_pull_requests(self,
                                owner: str,
                                repo: str,
                                state: str = "open",
                                head: Optional[str] = None,
                                base: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        List repository pull requests.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state ('open', 'closed', 'all')
            head: Filter by head branch
            base: Filter by base branch
            
        Returns:
            List of pull requests
        """
        params = {"owner": owner, "repo": repo, "state": state}
        if head:
            params["head"] = head
        if base:
            params["base"] = base
        
        result = await self._call_tool("list_pull_requests", params)
        return result if isinstance(result, list) else []
    
    async def create_pull_request(self,
                                 owner: str,
                                 repo: str,
                                 title: str,
                                 head: str,
                                 base: str,
                                 body: str = "",
                                 draft: bool = False) -> Dict[str, Any]:
        """
        Create a new pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Source branch
            base: Target branch
            body: PR body
            draft: Create as draft PR
            
        Returns:
            Created pull request information
        """
        return await self._call_tool("create_pull_request", {
            "owner": owner,
            "repo": repo,
            "title": title,
            "head": head,
            "base": base,
            "body": body,
            "draft": draft
        })
    
    async def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """
        Retrieve PR details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            Pull request details
        """
        return await self._call_tool("get_pull_request", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        })
    
    async def update_pull_request(self,
                                 owner: str,
                                 repo: str,
                                 pull_number: int,
                                 title: Optional[str] = None,
                                 body: Optional[str] = None,
                                 state: Optional[str] = None,
                                 base: Optional[str] = None) -> Dict[str, Any]:
        """
        Modify an existing pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            title: New title
            body: New body
            state: New state (open, closed)
            base: New base branch
            
        Returns:
            Updated pull request information
        """
        params = {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        }
        if title is not None:
            params["title"] = title
        if body is not None:
            params["body"] = body
        if state is not None:
            params["state"] = state
        if base is not None:
            params["base"] = base
        
        return await self._call_tool("update_pull_request", params)
    
    async def merge_pull_request(self,
                                owner: str,
                                repo: str,
                                pull_number: int,
                                commit_title: Optional[str] = None,
                                commit_message: Optional[str] = None,
                                merge_method: str = "merge") -> Dict[str, Any]:
        """
        Merge a pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            commit_title: Title for merge commit
            commit_message: Message for merge commit
            merge_method: Merge method (merge, squash, rebase)
            
        Returns:
            Merge result information
        """
        params = {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number,
            "merge_method": merge_method
        }
        if commit_title:
            params["commit_title"] = commit_title
        if commit_message:
            params["commit_message"] = commit_message
        
        return await self._call_tool("merge_pull_request", params)
    
    async def get_pull_request_files(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """
        List files changed in a PR.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            List of changed files
        """
        result = await self._call_tool("get_pull_request_files", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        })
        return result if isinstance(result, list) else []
    
    async def get_pull_request_status(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """
        Get PR status checks.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            Status check information
        """
        return await self._call_tool("get_pull_request_status", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        })
    
    async def update_pull_request_branch(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """
        Update PR branch.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            Branch update information
        """
        return await self._call_tool("update_pull_request_branch", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        })
    
    async def get_pull_request_comments(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """
        Get PR review comments.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            List of review comments
        """
        result = await self._call_tool("get_pull_request_comments", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        })
        return result if isinstance(result, list) else []
    
    async def add_pull_request_review_comment(self,
                                            owner: str,
                                            repo: str,
                                            pull_number: int,
                                            body: str,
                                            commit_sha: str,
                                            path: str,
                                            line: int) -> Dict[str, Any]:
        """
        Add a review comment.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            body: Comment body
            commit_sha: SHA of the commit
            path: File path
            line: Line number
            
        Returns:
            Created comment information
        """
        return await self._call_tool("add_pull_request_review_comment", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number,
            "body": body,
            "commit_sha": commit_sha,
            "path": path,
            "line": line
        })
    
    async def get_pull_request_reviews(self, owner: str, repo: str, pull_number: int) -> List[Dict[str, Any]]:
        """
        Get PR reviews.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            List of reviews
        """
        result = await self._call_tool("get_pull_request_reviews", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        })
        return result if isinstance(result, list) else []
    
    async def create_pull_request_review(self,
                                       owner: str,
                                       repo: str,
                                       pull_number: int,
                                       body: str = "",
                                       event: str = "COMMENT",
                                       comments: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
        """
        Create a PR review.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            body: Review body
            event: Review event (APPROVE, REQUEST_CHANGES, COMMENT)
            comments: Review comments
            
        Returns:
            Created review information
        """
        params = {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number,
            "body": body,
            "event": event
        }
        if comments:
            params["comments"] = comments
        
        return await self._call_tool("create_pull_request_review", params)
    
    async def request_copilot_review(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """
        Request Copilot PR review (experimental).
        
        Args:
            owner: Repository owner
            repo: Repository name
            pull_number: Pull request number
            
        Returns:
            Review request information
        """
        return await self._call_tool("request_copilot_review", {
            "owner": owner,
            "repo": repo,
            "pull_number": pull_number
        })