"""
Exceptions for LangChain integration.

This module provides custom exceptions for the LangChain integration.
"""

class LangChainIntegrationError(Exception):
    """Base exception for LangChain integration errors."""
    pass

class LangChainNotInstalledError(LangChainIntegrationError):
    """Raised when LangChain is not installed."""
    
    def __init__(self, message=None):
        self.message = message or "LangChain is not installed. Install it with 'pip install langchain langchain_core'"
        super().__init__(self.message)

class LangChainToolConversionError(LangChainIntegrationError):
    """Raised when a LangChain tool cannot be converted."""
    pass

class MCPToolConversionError(LangChainIntegrationError):
    """Raised when an MCP tool cannot be converted."""
    pass

class LangChainAgentConversionError(LangChainIntegrationError):
    """Raised when a LangChain agent cannot be converted."""
    pass

class A2AAgentConversionError(LangChainIntegrationError):
    """Raised when an A2A agent cannot be converted."""
    pass