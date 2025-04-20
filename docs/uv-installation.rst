Installation with UV
=================

What is UV?
----------

UV (Ultraviolet) is a modern, extremely fast Python package installer and resolver developed by the team at Astral. It provides significant improvements over traditional tools like pip:

- **Speed**: 10-100x faster than pip for installations and dependency resolution
- **Reliability**: Improved dependency resolution algorithms
- **Compatibility**: Compatible with standard Python packaging ecosystem
- **Built-in Caching**: Faster repeated installations
- **Integrated Tools**: Better virtual environment management

Installing UV
------------

You can install UV on your system with the following commands:

On macOS/Linux:

.. code-block:: bash

    curl -LsSf https://astral.sh/uv/install.sh | sh

On Windows (PowerShell):

.. code-block:: powershell

    irm https://astral.sh/uv/install.ps1 | iex

Basic Installation
----------------

To install Python A2A with UV:

.. code-block:: bash

    # Install the base package
    uv pip install python-a2a

Installing with Optional Dependencies
-----------------------------------

UV supports extras syntax for optional features:

.. code-block:: bash

    # For Flask-based server support
    uv pip install "python-a2a[server]"

    # For OpenAI integration
    uv pip install "python-a2a[openai]"

    # For Anthropic Claude integration
    uv pip install "python-a2a[anthropic]"

    # For AWS-Bedrock integration
    uv pip install "python-a2a[bedrock]"

    # For MCP support (Model Context Protocol)
    uv pip install "python-a2a[mcp]"

    # For all optional dependencies
    uv pip install "python-a2a[all]"

Development Setup with UV
-----------------------

For development work, you can install Python A2A in editable mode:

.. code-block:: bash

    # Clone the repository
    git clone https://github.com/themanojdesai/python-a2a.git
    cd python-a2a

    # Create a virtual environment and install in development mode
    uv venv create .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    uv pip install -e ".[dev]"

    # Run tests
    uv pip run pytest

Benefits for Python A2A Development
---------------------------------

Using UV with Python A2A offers several advantages:

1. **Faster Environment Setup**: Setting up a development environment is much quicker
2. **Better Dependency Resolution**: Avoids dependency conflicts
3. **Consistent Environment**: Reproducible builds with ``UVManifest.toml``
4. **Faster CI/CD**: Significantly speeds up continuous integration workflows

Using the Makefile
----------------

The project includes a Makefile with UV-specific commands for common tasks:

.. code-block:: bash

    # Set up development environment
    make setup

    # Run tests
    make test

    # Format code
    make format

    # Lint code
    make lint

Reproducible Builds
-----------------

For reproducible builds, Python A2A includes a ``UVManifest.toml`` file that you can use:

.. code-block:: bash

    # Install with exact versions from UVManifest.toml
    uv pip install --manifest UVManifest.toml

Docker Integration
---------------

For Docker-based deployments, you can use UV in your Dockerfile:

.. code-block:: dockerfile

    FROM python:3.9-slim

    # Install UV
    RUN curl -LsSf https://astral.sh/uv/install.sh | sh

    # Set environment variables
    ENV PATH="/root/.cargo/bin:${PATH}"

    # Install Python A2A
    WORKDIR /app
    COPY . .
    RUN uv pip install ".[all]"

    # Run your application
    CMD ["python", "your_app.py"]

Troubleshooting
-------------

If you encounter issues with UV:

- Make sure UV is correctly installed and in your PATH
- Try clearing the UV cache with ``uv cache clean``
- For dependency resolution issues, try ``uv pip install --skip-lock``
- Check the `UV documentation <https://github.com/astral-sh/uv>`_ for more details

For Python A2A specific issues, please file an issue on our `GitHub repository <https://github.com/themanojdesai/python-a2a/issues>`_.