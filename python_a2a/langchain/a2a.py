"""
A2A protocol conversions for LangChain integration.

This module provides functions to convert between LangChain agents and A2A servers/agents.
"""

import logging
import asyncio
import inspect
from typing import Any, Dict, List, Optional, Union, Callable, Type, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

# Import custom exceptions
from .exceptions import (
    LangChainNotInstalledError,
    LangChainAgentConversionError,
    A2AAgentConversionError
)

# Check for LangChain availability without failing
try:
    # Try to import LangChain components
    try:
        from langchain_core.language_models import BaseLanguageModel
        from langchain_core.tools import BaseTool
        from langchain_core.runnables import Runnable
        from langchain.agents import AgentExecutor
    except ImportError:
        # Fall back to older LangChain structure
        from langchain.base_language import BaseLanguageModel
        from langchain.tools import BaseTool
        try:
            from langchain.chains import Chain as Runnable
        except ImportError:
            class Runnable:
                pass
        try:
            from langchain.agents import AgentExecutor
        except ImportError:
            class AgentExecutor:
                pass
    
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Create stub classes for type hints
    class BaseLanguageModel:
        pass
    
    class BaseTool:
        pass
    
    class Runnable:
        pass
    
    class AgentExecutor:
        pass


@runtime_checkable
class Invocable(Protocol):
    """Protocol for components with an invoke method."""
    def invoke(self, inputs: Any, **kwargs) -> Any: ...

@runtime_checkable
class RunnableProtocol(Protocol):
    """Protocol for components with a run method."""
    def run(self, inputs: Any, **kwargs) -> Any: ...

@runtime_checkable
class LLM(Protocol):
    """Protocol for language model components."""
    def generate(self, prompts: List[str], **kwargs) -> Any: ...
    def predict(self, text: str, **kwargs) -> str: ...

@runtime_checkable
class ChainLike(Protocol):
    """Protocol for chain-like components."""
    @property
    def input_keys(self) -> List[str]: ...
    @property
    def output_keys(self) -> List[str]: ...
    def _call(self, inputs: Dict[str, Any]) -> Dict[str, Any]: ...


class ComponentAdapter:
    """Base adapter for LangChain components."""
    
    def __init__(self, component: Any):
        """Initialize with a component."""
        self.component = component
        self.name = self._get_component_name()
    
    def _get_component_name(self) -> str:
        """Get the name of the component."""
        if hasattr(self.component, "name"):
            return getattr(self.component, "name")
        return type(self.component).__name__
    
    def can_adapt(self) -> bool:
        """Check if this adapter can adapt the component."""
        raise NotImplementedError("Subclasses must implement this method")
    
    async def process_message(self, text: str) -> str:
        """Process a message with the component."""
        raise NotImplementedError("Subclasses must implement this method")


class InvocableAdapter(ComponentAdapter):
    """Adapter for components with invoke method."""
    
    def can_adapt(self) -> bool:
        """Check if component has invoke method."""
        return isinstance(self.component, Invocable) or hasattr(self.component, "invoke")
    
    async def process_message(self, text: str) -> str:
        """Process message using the invoke method."""
        try:
            # Prepare input format
            input_data = self._prepare_input(text)
            
            # Call invoke with appropriate method
            result = await self._invoke(input_data)
            
            # Process output format
            return self._process_output(result)
        except Exception as e:
            logger.exception(f"Error invoking component '{self.name}'")
            return f"Error: {str(e)}"
    
    def _prepare_input(self, text: str) -> Any:
        """Prepare input for the component based on its expected format."""
        # Try to determine expected input format
        if hasattr(self.component, "input_keys") and self.component.input_keys:
            return {self.component.input_keys[0]: text}
        
        # Check method signature
        try:
            sig = inspect.signature(self.component.invoke)
            first_param = next(iter(sig.parameters.values()), None)
            # If first parameter is positional or doesn't have default, use text directly
            if first_param and first_param.default == inspect.Parameter.empty:
                return text
        except (ValueError, TypeError, StopIteration):
            pass
        
        # Default to dict format
        return {"input": text}
    
    async def _invoke(self, input_data: Any) -> Any:
        """Invoke the component with appropriate async/sync handling."""
        if asyncio.iscoroutinefunction(self.component.invoke):
            # Try direct invocation
            try:
                return await self.component.invoke(input_data)
            except (TypeError, ValueError):
                # Fall back to dict format if direct invocation fails
                if not isinstance(input_data, dict):
                    return await self.component.invoke({"input": input_data})
                raise
        else:
            # Run synchronously in executor
            loop = asyncio.get_event_loop()
            try:
                return await loop.run_in_executor(
                    None, lambda: self.component.invoke(input_data)
                )
            except (TypeError, ValueError):
                # Fall back to dict format if direct invocation fails
                if not isinstance(input_data, dict):
                    return await loop.run_in_executor(
                        None, lambda: self.component.invoke({"input": input_data})
                    )
                raise
    
    def _process_output(self, result: Any) -> str:
        """Process the output from the component to a string."""
        if result is None:
            return ""
        
        if isinstance(result, str):
            return result
        
        if isinstance(result, dict):
            # Check common keys in a sensible order
            for key in ["output", "text", "result", "response", "answer", "content"]:
                if key in result:
                    value = result[key]
                    return str(value) if value is not None else ""
            
            # If component has output_keys, try the first one
            if hasattr(self.component, "output_keys") and self.component.output_keys:
                key = self.component.output_keys[0]
                if key in result:
                    value = result[key]
                    return str(value) if value is not None else ""
        
        # Default to string representation
        return str(result)


class RunnableAdapter(ComponentAdapter):
    """Adapter for components with run method."""
    
    def can_adapt(self) -> bool:
        """Check if component has run method."""
        return isinstance(self.component, RunnableProtocol) or hasattr(self.component, "run")
    
    async def process_message(self, text: str) -> str:
        """Process message using the run method."""
        try:
            # Call run with appropriate method
            if asyncio.iscoroutinefunction(self.component.run):
                result = await self.component.run(text)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.component.run, text)
            
            # Process result
            if result is None:
                return ""
            return str(result)
        except Exception as e:
            logger.exception(f"Error running component '{self.name}'")
            return f"Error: {str(e)}"


class LLMAdapter(ComponentAdapter):
    """Adapter for language model components."""
    
    def can_adapt(self) -> bool:
        """Check if component is a language model."""
        return (isinstance(self.component, (BaseLanguageModel, LLM)) or
                hasattr(self.component, "predict") or
                hasattr(self.component, "generate"))
    
    async def process_message(self, text: str) -> str:
        """Process message using LLM methods."""
        try:
            # Try predict if available
            if hasattr(self.component, "predict"):
                if asyncio.iscoroutinefunction(self.component.predict):
                    result = await self.component.predict(text=text)
                else:
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        None, lambda: self.component.predict(text=text)
                    )
                return result if result is not None else ""
            
            # Fall back to generate
            if hasattr(self.component, "generate"):
                if asyncio.iscoroutinefunction(self.component.generate):
                    generation = await self.component.generate([text])
                else:
                    loop = asyncio.get_event_loop()
                    generation = await loop.run_in_executor(
                        None, lambda: self.component.generate([text])
                    )
                
                # Extract text from generation
                if hasattr(generation, "generations") and generation.generations:
                    return generation.generations[0][0].text
                return str(generation)
            
            raise ValueError(f"Component '{self.name}' has no predict or generate method")
        except Exception as e:
            logger.exception(f"Error using LLM '{self.name}'")
            return f"Error: {str(e)}"


class CallableAdapter(ComponentAdapter):
    """Adapter for callable components."""
    
    def can_adapt(self) -> bool:
        """Check if component is callable."""
        return callable(self.component)
    
    async def process_message(self, text: str) -> str:
        """Process message by calling the component."""
        try:
            # Call the component
            if asyncio.iscoroutinefunction(self.component.__call__):
                result = await self.component(text)
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, self.component, text)
            
            # Process result
            if result is None:
                return ""
            return str(result)
        except Exception as e:
            logger.exception(f"Error calling component '{self.name}'")
            return f"Error: {str(e)}"


class AdapterRegistry:
    """Registry for component adapters."""
    
    def __init__(self):
        """Initialize the registry."""
        self._adapters = []
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register the default set of adapters."""
        # Order matters - more specific adapters should be registered first
        self.register(LLMAdapter)
        self.register(InvocableAdapter)
        self.register(RunnableAdapter)
        self.register(CallableAdapter)
    
    def register(self, adapter_class: Type[ComponentAdapter]):
        """Register an adapter class."""
        self._adapters.append(adapter_class)
    
    def get_adapter(self, component: Any) -> Optional[ComponentAdapter]:
        """Get the first compatible adapter for a component."""
        for adapter_class in self._adapters:
            adapter = adapter_class(component)
            if adapter.can_adapt():
                return adapter
        return None


def to_a2a_server(langchain_component: Any):
    """
    Convert a LangChain component to an A2A server.
    
    Args:
        langchain_component: A LangChain component (agent, chain, LLM, etc.)
        
    Returns:
        An A2A server instance that wraps the LangChain component
        
    Raises:
        LangChainNotInstalledError: If LangChain is not installed
        LangChainAgentConversionError: If the component cannot be converted
    """
    if not HAS_LANGCHAIN:
        raise LangChainNotInstalledError()
    
    try:
        # Import A2A components
        from python_a2a.server import A2AServer
        from python_a2a.models import Message, TaskStatus, TaskState, TextContent, MessageRole
        
        # Get adapter for the component
        registry = AdapterRegistry()
        adapter = registry.get_adapter(langchain_component)
        
        if not adapter:
            raise LangChainAgentConversionError(
                f"No suitable adapter found for component type: {type(langchain_component)}"
            )
        
        class LangChainServer(A2AServer):
            """A2A server that wraps a LangChain component."""
            
            def __init__(self, component, adapter):
                """Initialize with a LangChain component and adapter."""
                super().__init__()
                self.component = component
                self.adapter = adapter
                self.name = adapter.name
            
            async def handle_message_async(self, message):
                """Handle an incoming A2A message."""
                # Extract text from message
                if hasattr(message.content, 'text'):
                    text = message.content.text
                elif hasattr(message.content, '__str__'):
                    text = str(message.content)
                else:
                    text = repr(message.content)
                
                # Process with adapter
                result = await self.adapter.process_message(text)
                
                # Create response message
                return Message(
                    content=TextContent(text=result),
                    role=MessageRole.AGENT,
                    parent_message_id=message.message_id,
                    conversation_id=message.conversation_id
                )
            
            def handle_task(self, task):
                """Process an A2A task."""
                # Extract text from task
                message_data = task.message or {}
                content = message_data.get("content", {})
                
                if isinstance(content, dict) and "text" in content:
                    text = content["text"]
                elif hasattr(content, '__str__'):
                    text = str(content)
                else:
                    text = repr(content) if content else ""
                
                if not text:
                    task.status = TaskStatus(
                        state=TaskState.INPUT_REQUIRED,
                        message="Please provide a text query."
                    )
                    return task
                
                try:
                    # Process with adapter
                    result = asyncio.run(self.adapter.process_message(text))
                    
                    # Create response
                    task.artifacts = [{
                        "parts": [{"type": "text", "text": result}]
                    }]
                    task.status = TaskStatus(state=TaskState.COMPLETED)
                except Exception as e:
                    logger.exception("Error processing task")
                    task.status = TaskStatus(
                        state=TaskState.FAILED,
                        message=f"Error: {str(e)}"
                    )
                
                return task
        
        # Create and return the server
        return LangChainServer(langchain_component, adapter)
        
    except Exception as e:
        logger.exception("Failed to create A2A server from LangChain component")
        raise LangChainAgentConversionError(f"Failed to convert LangChain component: {str(e)}")


def to_langchain_agent(a2a_url):
    """
    Create a LangChain agent that connects to an A2A agent.
    
    Args:
        a2a_url: URL of the A2A agent
        
    Returns:
        A LangChain agent that communicates with the A2A agent
        
    Raises:
        LangChainNotInstalledError: If LangChain is not installed
        A2AAgentConversionError: If the agent cannot be converted
    """
    if not HAS_LANGCHAIN:
        raise LangChainNotInstalledError()
    
    try:
        # Import A2A client
        from python_a2a.client import A2AClient
        
        # Create client to connect to A2A agent
        client = A2AClient(a2a_url)
        
        # Create a simple non-Pydantic wrapper
        class A2AAgentWrapper:
            """Simple wrapper for A2A agent with LangChain compatibility."""
            
            def __init__(self, client):
                """Initialize with A2A client."""
                self.client = client
                self.name = "A2A Agent"
                
                # Try to get agent info
                try:
                    agent_info = client.get_agent_info()
                    self.name = agent_info.get("name", self.name)
                except Exception:
                    pass
                
                # LangChain compatibility attributes
                self.memory = None
                self.verbose = False
                self.callbacks = None
                self.tags = []
                self.metadata = {}
                self.input_keys = ["input"]
                self.output_keys = ["output"]
            
            def run(self, query):
                """Run the agent on the query."""
                return self.client.ask(self._extract_query(query))
            
            async def arun(self, query):
                """Run the agent asynchronously."""
                query_text = self._extract_query(query)
                if hasattr(self.client, 'ask_async'):
                    return await self.client.ask_async(query_text)
                else:
                    loop = asyncio.get_event_loop()
                    return await loop.run_in_executor(None, self.client.ask, query_text)
            
            def _call(self, inputs):
                """Legacy Chain interface."""
                query = self._extract_query(inputs)
                result = self.client.ask(query)
                return {"output": result}
            
            async def _acall(self, inputs):
                """Legacy Chain async interface."""
                query = self._extract_query(inputs)
                result = await self.arun(query)
                return {"output": result}
            
            def invoke(self, input_data, config=None, **kwargs):
                """Modern LangChain interface."""
                query = self._extract_query(input_data)
                result = self.run(query)
                return {"output": result}
            
            def _extract_query(self, input_data):
                """Extract query from various input formats."""
                if isinstance(input_data, str):
                    return input_data
                elif isinstance(input_data, dict):
                    # Try common keys for the query text
                    for key in ["input", "query", "question", "text", "content"]:
                        if key in input_data:
                            return input_data[key]
                    # No recognized keys, use string representation
                    return str(input_data)
                else:
                    # Any other type, convert to string
                    return str(input_data)
            
            # Make the wrapper callable
            def __call__(self, input_data):
                """Make this object callable."""
                return self.run(self._extract_query(input_data))
            
            # Dictionary-like interface for LangChain
            def get(self, key, default=None):
                """Dictionary-like accessor."""
                return getattr(self, key, default)
            
            def __getitem__(self, key):
                """Dictionary-like item access."""
                if hasattr(self, key):
                    return getattr(self, key)
                raise KeyError(f"No attribute {key}")
            
            # Support for pipe operator
            def __or__(self, other):
                """Implement pipe operator for chains."""
                if callable(other):
                    def pipe_wrapper(x):
                        response = self.invoke(x)
                        return other(response["output"])
                    return pipe_wrapper
                raise ValueError(f"Cannot pipe with {type(other)}")
        
        # Create and return the wrapper
        return A2AAgentWrapper(client)
    
    except Exception as e:
        logger.exception("Failed to create LangChain agent from A2A agent")
        raise A2AAgentConversionError(f"Failed to convert A2A agent: {str(e)}")