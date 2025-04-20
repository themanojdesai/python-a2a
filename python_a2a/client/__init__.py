"""
Client implementations for the A2A protocol.
"""

# Import and re-export client classes for easy access
from .base import BaseA2AClient
from .http import A2AClient

# Import LLM-specific clients
from .llm import OpenAIA2AClient, AnthropicA2AClient

# Import enhanced components
from .network import AgentNetwork
from .router import AIAgentRouter
from .streaming import StreamingClient

# Make everything available at the client level
__all__ = [
    'BaseA2AClient',
    'A2AClient',
    'OpenAIA2AClient',
    'AnthropicA2AClient',
    'AgentNetwork',
    'AIAgentRouter',
    'StreamingClient'
]