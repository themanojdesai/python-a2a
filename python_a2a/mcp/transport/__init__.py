"""
Transport backends for FastMCP.

This module provides different transport backends for FastMCP servers.
"""

# Import for easy access
from .fastapi import create_fastapi_app

__all__ = [
    "create_fastapi_app"
]