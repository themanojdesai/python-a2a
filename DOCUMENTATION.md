# Documentation

This document provides comprehensive information about Python A2A's documentation system and recent updates.

## 📖 Documentation Overview

Documentation for Python A2A is available at [ReadTheDocs](https://python-a2a.readthedocs.io/). The documentation covers:

- **Getting Started**: Installation, quick start examples, and basic concepts
- **API Reference**: Complete API documentation with type hints
- **User Guides**: In-depth tutorials and best practices
- **Examples**: Real-world examples and use cases
- **Migration Guides**: Upgrading between versions

## 🆕 Recent Documentation Updates

### MCP Provider Architecture (v0.5.X)

The documentation has been comprehensively updated to reflect the new MCP provider architecture:

#### New Provider Documentation
- **GitHub MCP Provider**: Complete GitHub integration via official GitHub MCP server
- **Browserbase MCP Provider**: Browser automation and web scraping capabilities
- **Filesystem MCP Provider**: Secure file operations with sandboxing

#### Updated Guides
- **[MCP Integration Guide](docs/guides/mcp.rst)**: Completely rewritten to showcase the provider architecture
- **[README.md](README.md)**: Updated with new provider examples and architecture overview
- **[Examples README](examples/README.md)**: Added comprehensive MCP provider examples

#### Architecture Documentation
- **Provider vs Server Separation**: Clear documentation of external MCP servers (providers) vs internal tools
- **Type Safety**: Documentation of comprehensive type hints and error handling
- **Production Deployment**: Enterprise-ready configuration and best practices

### Key Documentation Features

#### Provider Architecture Overview
```python
# New provider-based architecture
from python_a2a.mcp.providers import GitHubMCPServer, BrowserbaseMCPServer, FilesystemMCPServer

# GitHub integration
async with GitHubMCPServer(token="your-token") as github:
    user = await github.get_authenticated_user()
    repo = await github.create_repository("my-project", "Description")

# Browser automation
async with BrowserbaseMCPServer(api_key="key", project_id="id") as browser:
    await browser.navigate("https://example.com")
    screenshot = await browser.take_screenshot()

# File operations
async with FilesystemMCPServer(allowed_directories=["/tmp"]) as fs:
    content = await fs.read_file("/tmp/data.txt")
    await fs.write_file("/tmp/output.txt", "Hello World")
```

#### Migration Documentation
Clear migration paths from the previous `servers_*.py` pattern to the new provider architecture:

```python
# Old way (deprecated)
from python_a2a.mcp.servers_github import GitHubMCPServer

# New way (provider architecture)
from python_a2a.mcp.providers import GitHubMCPServer
```

## 🏗️ Building Documentation Locally

### Prerequisites

1. Install the required dependencies:

```bash
# Install the package with all dependencies
pip install -e ".[all]"

# Install documentation-specific requirements
pip install -r docs/requirements.txt
```

### Building Process

2. Navigate to the `docs` directory:

```bash
cd docs
```

3. Build the HTML documentation:

```bash
make html
```

4. Open the generated documentation in your browser:

```bash
# On macOS
open _build/html/index.html

# On Linux
xdg-open _build/html/index.html

# On Windows
start _build/html/index.html
```

### Documentation Structure

```
docs/
├── conf.py                 # Sphinx configuration
├── index.rst              # Main documentation index
├── installation.rst       # Installation instructions
├── quickstart.rst         # Quick start guide
├── guides/                 # User guides
│   ├── index.rst
│   ├── basics.rst
│   ├── advanced.rst
│   ├── mcp.rst            # MCP provider guide (updated)
│   ├── langchain.rst
│   └── agent_flow.rst
├── examples/              # Example documentation
│   ├── index.rst
│   ├── simple.rst
│   ├── advanced.rst
│   └── langchain.rst
└── requirements.txt       # Documentation dependencies
```

## 🤝 Contributing to Documentation

### Documentation Standards

When contributing to documentation, please follow these standards:

#### Content Guidelines
- **Accuracy**: All examples must be tested and work with the current version
- **Completeness**: Cover all major features and use cases
- **Clarity**: Write for developers of all skill levels
- **Production Focus**: Include enterprise deployment considerations

#### Format Guidelines
- Use reStructuredText (.rst) format
- Follow the existing structure and style
- Include code examples with proper syntax highlighting
- Add cross-references between related sections

#### Example Quality Standards
```python
# Good: Complete, tested example
from python_a2a.mcp.providers import GitHubMCPServer

async def github_example():
    """Complete example with error handling and context management."""
    async with GitHubMCPServer(token="your-token") as github:
        try:
            user = await github.get_authenticated_user()
            print(f"Authenticated as: {user['login']}")
        except Exception as e:
            print(f"Error: {e}")

# Bad: Incomplete example without context
github = GitHubMCPServer()
user = github.get_user()  # Missing token, no error handling
```

### Documentation Update Process

1. **Identify Changes**: Determine what needs to be documented
2. **Update Relevant Files**: Modify the appropriate .rst files
3. **Test Examples**: Ensure all code examples work correctly
4. **Build Locally**: Test the documentation builds without errors
5. **Review**: Check for accuracy and completeness
6. **Submit**: Create a pull request with your changes

### Key Documentation Areas

#### API Reference
- Automatically generated from docstrings
- Must include complete type hints
- Should have usage examples for complex methods

#### User Guides
- Step-by-step tutorials for major features
- Real-world examples and use cases
- Best practices and common pitfalls

#### Migration Guides
- Clear paths between versions
- Breaking changes and their solutions
- Updated examples for new features

## 📋 Documentation Checklist

When updating documentation, ensure:

- [ ] All code examples are tested and working
- [ ] New features are documented with examples
- [ ] Migration paths are clearly explained
- [ ] Cross-references are updated
- [ ] API documentation matches the actual implementation
- [ ] Examples follow production-ready patterns
- [ ] Error handling is demonstrated
- [ ] Security considerations are included

## 🚀 Documentation Deployment

The documentation is automatically built and deployed to ReadTheDocs when changes are pushed to the main branch. The deployment process:

1. **Automatic Trigger**: Push to main branch triggers rebuild
2. **Sphinx Build**: ReadTheDocs runs `sphinx-build` with our configuration
3. **Deployment**: Successfully built documentation is deployed
4. **Notification**: Contributors are notified of build status

### Manual Documentation Updates

For urgent documentation fixes:

1. Update the relevant files
2. Test locally to ensure builds work
3. Create a pull request with clear description
4. After merge, documentation will auto-deploy

## 🔍 Documentation Quality Assurance

### Regular Review Process
- **Monthly Reviews**: Check for outdated examples and links
- **Version Updates**: Update documentation with each release
- **User Feedback**: Incorporate feedback from GitHub issues and discussions

### Quality Metrics
- **Accuracy**: All examples must work with current version
- **Completeness**: Cover all public APIs and major features
- **Usability**: Clear navigation and searchable content
- **Performance**: Fast loading and responsive design

## 📞 Documentation Support

If you need help with documentation:

- **[GitHub Issues](https://github.com/themanojdesai/python-a2a/issues)**: Report documentation bugs or request improvements
- **[GitHub Discussions](https://github.com/themanojdesai/python-a2a/discussions)**: Ask questions about documentation
- **[Contributing Guide](CONTRIBUTING.md)**: Learn how to contribute to the project

## 📄 License

All documentation is released under the MIT License, same as the project code.