Installation
============

Basic Installation
-----------------

Install the base package with minimal dependencies:

.. code-block:: bash

    pip install python-a2a

This will install the core functionality with only the ``requests`` library as a dependency.

Installation Options
-------------------

Python A2A is designed to be modular. You can install just what you need:

For Flask-based server support:

.. code-block:: bash

    pip install "python-a2a[server]"

For OpenAI integration:

.. code-block:: bash

    pip install "python-a2a[openai]"

For Anthropic Claude integration:

.. code-block:: bash

    pip install "python-a2a[anthropic]"

For AWS Bedrock integration:

.. code-block:: bash

    pip install "python-a2a[bedrock]"

For MCP support (Model Context Protocol):

.. code-block:: bash

    pip install "python-a2a[mcp]"

For all optional dependencies:

.. code-block:: bash

    pip install "python-a2a[all]"

Development Installation
-----------------------

If you want to contribute to the project or run tests, install the development dependencies:

.. code-block:: bash

    git clone https://github.com/themanojdesai/python-a2a.git
    cd python-a2a
    pip install -e ".[dev]"

Requirements
-----------

Python A2A requires:

- Python 3.9 or higher
- requests >= 2.25.0

Optional dependencies depend on the features you're using:

- **Server**: Flask >= 2.0.0
- **OpenAI**: openai >= 1.0.0
- **Anthropic**: anthropic >= 0.3.0
- **Bedrock**: boto3 >= 1.26.0
- **MCP**: httpx, fastapi, uvicorn, pydantic

Verifying Installation
---------------------

You can verify your installation by running:

.. code-block:: python

    import python_a2a
    print(python_a2a.__version__)

This should print the current version of the package.