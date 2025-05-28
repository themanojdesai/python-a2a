"""
Ollama-based server implementation for the A2A protocol.
"""

import requests
from typing import Optional, Dict, Any, List, Union, AsyncGenerator

try:
    from openai import OpenAI
    from openai import AsyncOpenAI
except ImportError:
    OpenAI = None
    AsyncOpenAI = None

from .openai import OpenAIA2AServer

from ...exceptions import A2AImportError, A2AConnectionError, A2AStreamingError


class OllamaA2AServer(OpenAIA2AServer):
    """
    An A2A server that uses OpenAI's API on Ollama server to process messages.

    This server converts incoming A2A messages to OpenAI's format, processes them
    using OpenAI's API on Ollama server, and converts the responses back to A2A format.
    """

    def __init__(
        self,
        api_url: str,
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize the Ollama A2A server

        Args:
            api_url: Ollama API URL
            model: Ollama model to use
            temperature: Generation temperature (default: 0.7)
            system_prompt: Optional system prompt to use for all conversations
            functions: Optional list of function definitions for function calling

        Raises:
            A2AImportError: If the OpenAI package is not installed
        """
        super().__init__(
            model=model,
            api_key=None,
            temperature=temperature,
            system_prompt=system_prompt,
            functions=functions,
        )

        if OpenAI is None:
            raise A2AImportError(
                "OpenAI package is not installed. "
                "Install it with 'pip install openai'"
            )

        # Initialize OpenAI compatible client
        self.__api_url = api_url
        self.function_role = "tool"  # Ollama uses "tool" as the function role

        try:
            self.__models = self.list_models()
        except Exception as err:
            raise A2AImportError(
                f"Ollama API is not available. Please check your installation. {err}"
            )

        if model not in self.__models:
            raise A2AImportError(f"Model '{model}' is not available in the Ollama API.")

        # Create an async client for streaming
        if AsyncOpenAI is not None:
            self.client = OpenAI(base_url=f"{api_url}/v1", api_key="ollama")
            self.async_client = AsyncOpenAI(base_url=f"{api_url}/v1", api_key="ollama")
        else:
            self.async_client = None

    def list_models(self) -> List[str]:
        """
        List available models from the Ollama API.

        Returns:
            List of model names.
        """
        try:
            result = requests.get(f"{self.__api_url}/api/tags")
            jsondata = result.json()
            return [m.get("model") for m in jsondata.get("models") if m.get("model")]
        except requests.RequestException as err:
            raise A2AConnectionError(
                f"Failed to connect to Ollama API at {self.__api_url}"
            ) from err
        except ValueError as err:
            raise ValueError(
                f"Failed to parse response from Ollama API at {self.__api_url}"
            ) from err
        except Exception as err:
            raise A2AConnectionError(
                f"An unexpected error occurred while connecting to Ollama API at {self.__api_url}"
            ) from err
