Python A2A: Agent-to-Agent Protocol
=============================

.. image:: https://img.shields.io/pypi/v/python-a2a.svg
   :target: https://pypi.org/project/python-a2a/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/python-a2a.svg
   :target: https://pypi.org/project/python-a2a/
   :alt: Python Versions

.. image:: https://img.shields.io/badge/License-MIT-yellow.svg
   :target: https://opensource.org/licenses/MIT
   :alt: License: MIT

.. image:: https://static.pepy.tech/badge/python-a2a
   :target: https://pepy.tech/project/python-a2a
   :alt: PyPI Downloads

**The Definitive Python Implementation of Google's Agent-to-Agent (A2A) Protocol with Model Context Protocol (MCP) Integration**

Overview
--------

Python A2A is a comprehensive, production-ready library for implementing Google's `Agent-to-Agent (A2A) protocol <https://google.github.io/A2A/>`_ with full support for the `Model Context Protocol (MCP) <https://contextual.ai/introducing-mcp/>`_ and `LangChain <https://github.com/langchain-ai/langchain>`_. It provides everything you need to build interoperable AI agent ecosystems that can collaborate seamlessly to solve complex problems.

The A2A protocol establishes a standard communication format that enables AI agents to interact regardless of their underlying implementation, while MCP extends this capability by providing a standardized way for agents to access external tools and data sources. Python A2A makes these protocols accessible with an intuitive API that developers of all skill levels can use to build sophisticated multi-agent systems.

Key Features
-----------

- **Agent Flow UI**: Visual workflow editor for building agent networks with drag-and-drop interface
- **Complete Implementation**: Fully implements the official A2A specification
- **Agent Discovery**: Built-in support for agent registry and discovery mechanism
- **MCP Integration**: First-class support for Model Context Protocol
- **LangChain Integration**: Seamless interoperability with LangChain tools and agents
- **Enterprise Ready**: Built for production with robust error handling
- **Framework Agnostic**: Works with any Python framework
- **LLM Provider Flexibility**: Native integrations with OpenAI, Anthropic, and more
- **Minimal Dependencies**: Core functionality requires only the ``requests`` library
- **Excellent Developer Experience**: Comprehensive documentation and examples

Getting Started
--------------

.. toctree::
   :maxdepth: 2
   
   installation
   uv-installation
   quickstart
   
User Guides
----------

.. toctree::
   :maxdepth: 2
   
   guides/index
   guides/langchain
   
API Reference
------------

.. toctree::
   :maxdepth: 2
   
   api/index
   
Examples
-------

.. toctree::
   :maxdepth: 2
   
   examples/index

Contributing
-----------

.. toctree::
   :maxdepth: 2
   
   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`