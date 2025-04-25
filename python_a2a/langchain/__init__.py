"""
LangChain integration for python-a2a.

This module provides functions to convert between LangChain and A2A/MCP components,
enabling interoperability between the two ecosystems.
"""

import importlib.util
import logging

logger = logging.getLogger(__name__)

# Check for LangChain availability
try:
    # Check for core packages
    langchain_spec = importlib.util.find_spec("langchain_core")
    langchain_legacy_spec = importlib.util.find_spec("langchain")
    
    # If at least one is available, we can proceed
    if langchain_spec or langchain_legacy_spec:
        HAS_LANGCHAIN = True
    else:
        HAS_LANGCHAIN = False
        
except ImportError:
    HAS_LANGCHAIN = False

# Import A2A conversions
from .a2a import to_a2a_server, to_langchain_agent

# Import MCP conversions
from .mcp import to_mcp_server, to_langchain_tool

# Import exceptions
from .exceptions import (
    LangChainIntegrationError,
    LangChainNotInstalledError,
    LangChainToolConversionError,
    MCPToolConversionError,
    LangChainAgentConversionError,
    A2AAgentConversionError
)

# Export all conversion functions and exceptions
__all__ = [
    # Conversion functions
    'to_a2a_server',     # Convert LangChain agent to A2A server
    'to_langchain_agent', # Convert A2A agent to LangChain agent
    'to_mcp_server',     # Convert LangChain tools to MCP server
    'to_langchain_tool',  # Convert MCP tool to LangChain tool
    
    # Exceptions
    'LangChainIntegrationError',
    'LangChainNotInstalledError',
    'LangChainToolConversionError',
    'MCPToolConversionError',
    'LangChainAgentConversionError',
    'A2AAgentConversionError',
    
    # Availability flag
    'HAS_LANGCHAIN'
]

# Version
__version__ = "0.1.0"