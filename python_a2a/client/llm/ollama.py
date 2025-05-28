"""
Ollama-based client implementation for the A2A protocol.
"""

import requests
from typing import Optional, List, Dict, Any

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .openai import OpenAIA2AClient
from ...exceptions import A2AImportError, A2AConnectionError


class OllamaA2AClient(OpenAIA2AClient):
    """A2A client that uses OpenAI's API on Ollama server to process messages."""

    def __init__(
        self,
        api_url: str,
        model: str,
        temperature: float = 0.7,
        system_prompt: Optional[str] = None,
        functions: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Initialize the Ollama A2A client

        Args:
            api_url: Ollama API URL
            model: Ollama model to use
            temperature: Generation temperature (default: 0.7)
            system_prompt: Optional system prompt for all conversations
            functions: Optional list of function definitions for function calling

        Raises:
            A2AImportError: If the ollama package is not installed
        """
        super().__init__(
            model=model,
            api_key=None,
            temperature=temperature,
            system_prompt=system_prompt,
            functions=functions,
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

        self.client = OpenAI(base_url=f"{api_url}/v1", api_key="ollama")

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
