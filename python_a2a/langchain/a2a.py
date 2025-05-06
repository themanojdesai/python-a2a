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
    
    async def process_stream(self, text: str):
        """
        Process a message with streaming support.
        
        Args:
            text: The text message to process
            
        Yields:
            Chunks of the response as they arrive
            
        By default, falls back to non-streaming processing.
        Subclasses should override this if they can provide streaming.
        """
        # Default implementation: fall back to non-streaming
        result = await self.process_message(text)
        yield result


class InvocableAdapter(ComponentAdapter):
    """Adapter for components with invoke method."""
    
    def can_adapt(self) -> bool:
        """Check if component has invoke method."""
        # Check for Invocable protocol or invoke attribute
        has_invoke = isinstance(self.component, Invocable) or hasattr(self.component, "invoke")
        
        # Check for LCEL/pipe operator components (modern LangChain)
        is_pipe_component = hasattr(self.component, "__or__") and hasattr(self.component, "__ror__")
        
        return has_invoke or is_pipe_component
    
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
    
    async def process_stream(self, text: str):
        """
        Process message using streaming capabilities if available.
        
        Args:
            text: The text message to process
            
        Yields:
            Chunks of the response as they arrive
        """
        # 1. Try modern streaming interfaces in priority order
        
        # Check for stream_invoke method (newest LangChain interface)
        if hasattr(self.component, "stream_invoke") and callable(self.component.stream_invoke):
            try:
                # Prepare input format
                input_data = self._prepare_input(text)
                
                # Check if stream_invoke is async
                if asyncio.iscoroutinefunction(self.component.stream_invoke):
                    try:
                        # Try with prepared input
                        async for chunk in self.component.stream_invoke(input_data):
                            yield self._process_chunk(chunk)
                        return  # Successfully used stream_invoke
                    except (TypeError, ValueError):
                        # Try with simple dictionary input
                        if not isinstance(input_data, dict):
                            async for chunk in self.component.stream_invoke({"input": input_data}):
                                yield self._process_chunk(chunk)
                            return  # Successfully used stream_invoke
                else:
                    # Sync stream_invoke
                    try:
                        # Try with prepared input
                        for chunk in self.component.stream_invoke(input_data):
                            yield self._process_chunk(chunk)
                        return  # Successfully used stream_invoke
                    except (TypeError, ValueError):
                        # Try with simple dictionary input
                        if not isinstance(input_data, dict):
                            for chunk in self.component.stream_invoke({"input": input_data}):
                                yield self._process_chunk(chunk)
                            return  # Successfully used stream_invoke
            except Exception as e:
                logger.warning(f"Error using stream_invoke for '{self.name}': {e}")
                # Continue to next method
        
        # Check for astream_invoke method (async streaming in newer LangChain)
        if hasattr(self.component, "astream_invoke") and callable(self.component.astream_invoke):
            try:
                # Prepare input format
                input_data = self._prepare_input(text)
                
                try:
                    # Try with prepared input
                    async for chunk in self.component.astream_invoke(input_data):
                        yield self._process_chunk(chunk)
                    return  # Successfully used astream_invoke
                except (TypeError, ValueError):
                    # Try with simple dictionary input
                    if not isinstance(input_data, dict):
                        async for chunk in self.component.astream_invoke({"input": input_data}):
                            yield self._process_chunk(chunk)
                        return  # Successfully used astream_invoke
            except Exception as e:
                logger.warning(f"Error using astream_invoke for '{self.name}': {e}")
                # Continue to next method
        
        # 2. Try standard stream methods
        if hasattr(self.component, "stream") and callable(self.component.stream):
            try:
                # Prepare input format
                input_data = self._prepare_input(text)
                
                # Check if stream is async
                if asyncio.iscoroutinefunction(self.component.stream):
                    try:
                        # Try with prepared input
                        async for chunk in self.component.stream(input_data):
                            yield self._process_chunk(chunk)
                        return  # Successfully used stream
                    except (TypeError, ValueError):
                        # Try with simple dictionary input
                        if not isinstance(input_data, dict):
                            async for chunk in self.component.stream({"input": input_data}):
                                yield self._process_chunk(chunk)
                            return  # Successfully used stream
                else:
                    # Sync stream
                    try:
                        # Try with prepared input
                        for chunk in self.component.stream(input_data):
                            yield self._process_chunk(chunk)
                        return  # Successfully used stream
                    except (TypeError, ValueError):
                        # Try with simple dictionary input
                        if not isinstance(input_data, dict):
                            for chunk in self.component.stream({"input": input_data}):
                                yield self._process_chunk(chunk)
                            return  # Successfully used stream
            except Exception as e:
                logger.warning(f"Error using stream for '{self.name}': {e}")
                # Continue to next method
                
        # Check for astream method (older LangChain async streaming)
        if hasattr(self.component, "astream") and callable(self.component.astream):
            try:
                # Prepare input format
                input_data = self._prepare_input(text)
                
                try:
                    # Try with prepared input
                    async for chunk in self.component.astream(input_data):
                        yield self._process_chunk(chunk)
                    return  # Successfully used astream
                except (TypeError, ValueError):
                    # Try with simple dictionary input
                    if not isinstance(input_data, dict):
                        async for chunk in self.component.astream({"input": input_data}):
                            yield self._process_chunk(chunk)
                        return  # Successfully used astream
            except Exception as e:
                logger.warning(f"Error using astream for '{self.name}': {e}")
                # Continue to next method
                
        # 3. Check older or custom interfaces
        if hasattr(self.component, "invoke_stream") and callable(self.component.invoke_stream):
            try:
                # Prepare input format
                input_data = self._prepare_input(text)
                
                # Check if invoke_stream is async
                if asyncio.iscoroutinefunction(self.component.invoke_stream):
                    try:
                        # Try with prepared input
                        async for chunk in self.component.invoke_stream(input_data):
                            yield self._process_chunk(chunk)
                        return  # Successfully used invoke_stream
                    except (TypeError, ValueError):
                        # Try with simple dictionary input
                        if not isinstance(input_data, dict):
                            async for chunk in self.component.invoke_stream({"input": input_data}):
                                yield self._process_chunk(chunk)
                            return  # Successfully used invoke_stream
                else:
                    # Sync invoke_stream
                    try:
                        # Try with prepared input
                        for chunk in self.component.invoke_stream(input_data):
                            yield self._process_chunk(chunk)
                        return  # Successfully used invoke_stream
                    except (TypeError, ValueError):
                        # Try with simple dictionary input
                        if not isinstance(input_data, dict):
                            for chunk in self.component.invoke_stream({"input": input_data}):
                                yield self._process_chunk(chunk)
                            return  # Successfully used invoke_stream
            except Exception as e:
                logger.warning(f"Error using invoke_stream for '{self.name}': {e}")
                # Continue to next method
                
        # 4. Try event-based streaming methods
        # Check for astream_events method (event-based streaming in newer LangChain)
        if hasattr(self.component, "astream_events") and callable(self.component.astream_events):
            try:
                # Prepare input format
                input_data = self._prepare_input(text)
                
                try:
                    # Try with prepared input
                    async for event in self.component.astream_events(input_data):
                        # Extract useful content from events
                        if hasattr(event, "event"):
                            if event.event == "on_llm_new_token":
                                # Token event - extract text
                                if hasattr(event, "data") and hasattr(event.data, "token"):
                                    yield event.data.token
                                elif hasattr(event, "token"):
                                    yield event.token
                            elif event.event in ["on_chat_model_stream", "on_llm_stream"]:
                                # Chunk event - extract content
                                if hasattr(event, "data") and hasattr(event.data, "chunk"):
                                    yield self._process_chunk(event.data.chunk)
                                elif hasattr(event, "chunk"):
                                    yield self._process_chunk(event.chunk)
                        elif hasattr(event, "data"):
                            # Generic event with data
                            yield self._process_chunk(event.data)
                        else:
                            # Unknown event type, convert to string
                            yield str(event)
                    return  # Successfully used astream_events
                except (TypeError, ValueError):
                    # Try with simple dictionary input
                    if not isinstance(input_data, dict):
                        async for event in self.component.astream_events({"input": input_data}):
                            # Extract useful content from events
                            if hasattr(event, "event"):
                                if event.event == "on_llm_new_token":
                                    # Token event - extract text
                                    if hasattr(event, "data") and hasattr(event.data, "token"):
                                        yield event.data.token
                                    elif hasattr(event, "token"):
                                        yield event.token
                                elif event.event in ["on_chat_model_stream", "on_llm_stream"]:
                                    # Chunk event - extract content
                                    if hasattr(event, "data") and hasattr(event.data, "chunk"):
                                        yield self._process_chunk(event.data.chunk)
                                    elif hasattr(event, "chunk"):
                                        yield self._process_chunk(event.chunk)
                            elif hasattr(event, "data"):
                                # Generic event with data
                                yield self._process_chunk(event.data)
                            else:
                                # Unknown event type, convert to string
                                yield str(event)
                        return  # Successfully used astream_events
            except Exception as e:
                logger.warning(f"Error using astream_events for '{self.name}': {e}")
                # Continue to next method
                
        # Fall back to non-streaming if none of the methods worked
        logger.info(f"No compatible streaming method found for '{self.name}', using non-streaming fallback")
        result = await self.process_message(text)
        yield result
    
    def _process_chunk(self, chunk: Any) -> str:
        """
        Process a streaming chunk to extract the text content.
        
        Args:
            chunk: A chunk from a streaming response
            
        Returns:
            The extracted text content as a string
        """
        if chunk is None:
            return ""
        
        # String chunks
        if isinstance(chunk, str):
            return chunk
        
        # Object with content attribute (common in LLM responses)
        if hasattr(chunk, "content"):
            return str(chunk.content) if chunk.content is not None else ""
            
        # Dictionary format - check common keys in a sensible order
        if isinstance(chunk, dict):
            for key in ["output", "text", "content", "token", "result", "response", "answer"]:
                if key in chunk:
                    value = chunk[key]
                    if value is None:
                        continue
                        
                    # Handle nested content
                    if isinstance(value, dict) and "content" in value:
                        return str(value["content"])
                    elif isinstance(value, dict) and "text" in value:
                        return str(value["text"])
                    elif hasattr(value, "content"):
                        return str(value.content)
                    else:
                        return str(value)
            
            # If no recognized keys are found, convert the whole dict
            return str(chunk)
        
        # Default to string representation for any other object
        return str(chunk)
    
    def _prepare_input(self, text: str) -> Any:
        """
        Prepare input for the component based on its expected format.
        
        Args:
            text: The text input to process
            
        Returns:
            Input in the format expected by the component
        """
        # Try to determine expected input format
        if hasattr(self.component, "input_keys") and self.component.input_keys:
            # Use the first input key for components with input_keys
            return {self.component.input_keys[0]: text}
        
        # Check method signature for invoke
        try:
            sig = inspect.signature(self.component.invoke)
            first_param = next(iter(sig.parameters.values()), None)
            # If first parameter is positional or doesn't have default, use text directly
            if first_param and first_param.default == inspect.Parameter.empty:
                return text
        except (ValueError, TypeError, StopIteration):
            pass
        
        # Check for specific input formats based on component type
        if hasattr(self.component, "__class__") and hasattr(self.component.__class__, "__name__"):
            component_class = self.component.__class__.__name__
            # Handle common LangChain components
            if component_class in ["ChatPromptTemplate", "PromptTemplate"]:
                return {"input": text}
            elif component_class in ["ChatOpenAI", "OpenAI", "ChatAnthropic", "Anthropic"]:
                return text
        
        # Default to dict format with "input" key
        return {"input": text}
    
    async def _invoke(self, input_data: Any) -> Any:
        """
        Invoke the component with appropriate async/sync handling.
        
        Args:
            input_data: The prepared input data for the component
            
        Returns:
            The result from the component
        """
        # Check for ainvoke method first (async invoke)
        if hasattr(self.component, "ainvoke") and asyncio.iscoroutinefunction(self.component.ainvoke):
            # Try direct invocation
            try:
                return await self.component.ainvoke(input_data)
            except (TypeError, ValueError):
                # Fall back to dict format if direct invocation fails
                if not isinstance(input_data, dict):
                    return await self.component.ainvoke({"input": input_data})
                raise
        
        # Fall back to synchronous invoke
        if asyncio.iscoroutinefunction(self.component.invoke):
            # Async invoke
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
        """
        Process the output from the component to a string.
        
        Args:
            result: The result from the component
            
        Returns:
            The extracted text content as a string
        """
        if result is None:
            return ""
        
        # String results
        if isinstance(result, str):
            return result
        
        # Process dictionary results
        if isinstance(result, dict):
            # Check common keys in a sensible order
            for key in ["output", "text", "result", "response", "answer", "content"]:
                if key in result:
                    value = result[key]
                    if value is None:
                        continue
                        
                    # Handle nested content
                    if isinstance(value, dict) and "content" in value:
                        return str(value["content"])
                    elif isinstance(value, dict) and "text" in value:
                        return str(value["text"])
                    elif hasattr(value, "content"):
                        return str(value.content)
                    else:
                        return str(value)
            
            # If component has output_keys, try the first one
            if hasattr(self.component, "output_keys") and self.component.output_keys:
                key = self.component.output_keys[0]
                if key in result:
                    value = result[key]
                    return str(value) if value is not None else ""
        
        # Handle common LangChain output types
        if hasattr(result, "content"):
            return str(result.content)
        
        # Default to string representation for any other object
        return str(result)


class AgentAdapter(ComponentAdapter):
    """Adapter for LangChain agent executors."""
    
    def can_adapt(self) -> bool:
        """Check if component is a LangChain agent executor."""
        # Check if it's an AgentExecutor or has expected agent properties
        agent_executor_type = False
        try:
            agent_executor_type = isinstance(self.component, AgentExecutor)
        except Exception:
            pass
        
        # More strict check for agent properties to avoid false positives
        has_agent_attrs = (
            hasattr(self.component, 'agent') and 
            hasattr(self.component, 'tools') and
            hasattr(self.component, 'run') and
            # Additional check: must have the agent attribute actually set
            getattr(self.component, 'agent', None) is not None and
            # Additional check: must have tools as a list or tuple
            isinstance(getattr(self.component, 'tools', None), (list, tuple))
        )
                         
        return agent_executor_type or has_agent_attrs
    
    async def process_message(self, text: str) -> str:
        """Process message using agent run method."""
        try:
            # AgentExecutor expects input in key-value format
            # Get the input key
            input_key = getattr(self.component, 'input_key', 'input')
            
            # Run the agent with the proper input formatting
            if asyncio.iscoroutinefunction(self.component.run):
                result = await self.component.run(**{input_key: text})
            else:
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(
                    None, lambda: self.component.run(**{input_key: text})
                )
            
            # Handle various result formats
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                # Agent outputs often have an 'output' key
                if 'output' in result:
                    return str(result['output'])
                else:
                    # If no output key, convert the dict to string
                    return str(result)
            else:
                return str(result)
        except Exception as e:
            logger.exception(f"Error running agent '{self.name}'")
            return f"Error: {str(e)}"
    
    async def process_stream(self, text: str):
        """Process streaming with agent."""
        # Check if the agent supports streaming
        if hasattr(self.component, 'stream') and callable(self.component.stream):
            try:
                # Get the input key
                input_key = getattr(self.component, 'input_key', 'input')
                
                # Stream with proper input format
                if asyncio.iscoroutinefunction(self.component.stream):
                    async for chunk in self.component.stream(**{input_key: text}):
                        yield self._extract_chunk_content(chunk) 
                else:
                    for chunk in self.component.stream(**{input_key: text}):
                        yield self._extract_chunk_content(chunk)
            except Exception as e:
                logger.exception(f"Error streaming from agent '{self.name}': {e}")
                # Fall back to non-streaming
                result = await self.process_message(text)
                yield result
        else:
            # Fall back to non-streaming if stream method not available
            result = await self.process_message(text)
            yield result
    
    def _extract_chunk_content(self, chunk):
        """Extract content from streaming chunks."""
        if isinstance(chunk, str):
            return chunk
        elif hasattr(chunk, 'content'):
            return chunk.content
        elif isinstance(chunk, dict):
            if 'output' in chunk:
                return str(chunk['output'])
            elif 'content' in chunk:
                return str(chunk['content'])
            elif 'text' in chunk:
                return str(chunk['text'])
        return str(chunk)


class RunnableAdapter(ComponentAdapter):
    """Adapter for components with run method."""
    
    def can_adapt(self) -> bool:
        """Check if component has run method."""
        return (
            isinstance(self.component, RunnableProtocol) or 
            isinstance(self.component, Runnable) or 
            hasattr(self.component, "run")
        )
    
    async def process_message(self, text: str) -> str:
        """
        Process message using the run method.
        
        For Runnable objects, tries to use invoke or ainvoke methods first,
        then falls back to run method.
        """
        try:
            # First try invoke/ainvoke for modern LangChain Runnables
            if isinstance(self.component, Runnable) or hasattr(self.component, "invoke"):
                if hasattr(self.component, "ainvoke") and asyncio.iscoroutinefunction(self.component.ainvoke):
                    try:
                        # Try with direct input
                        result = await self.component.ainvoke(text)
                    except (TypeError, ValueError):
                        # Try with dictionary input
                        result = await self.component.ainvoke({"input": text})
                else:
                    # Use synchronous invoke
                    loop = asyncio.get_event_loop()
                    try:
                        result = await loop.run_in_executor(
                            None, lambda: self.component.invoke(text)
                        )
                    except (TypeError, ValueError):
                        # Try with dictionary input
                        result = await loop.run_in_executor(
                            None, lambda: self.component.invoke({"input": text})
                        )
                
                # Extract result from various formats
                if isinstance(result, str):
                    return result
                elif isinstance(result, dict):
                    for key in ["output", "text", "result", "content", "answer"]:
                        if key in result:
                            return str(result[key])
                return str(result)
                
            # Fall back to run method
            if asyncio.iscoroutinefunction(self.component.run):
                try:
                    # Try direct run
                    result = await self.component.run(text)
                except (TypeError, ValueError):
                    # Try with dictionary input
                    result = await self.component.run({"input": text})
            else:
                # Run synchronously
                loop = asyncio.get_event_loop()
                try:
                    result = await loop.run_in_executor(None, self.component.run, text)
                except (TypeError, ValueError):
                    # Try with dictionary input
                    result = await loop.run_in_executor(
                        None, lambda: self.component.run({"input": text})
                    )
            
            # Process result
            if result is None:
                return ""
            
            # Extract text from result
            if isinstance(result, str):
                return result
            elif isinstance(result, dict):
                for key in ["output", "text", "result", "content", "answer"]:
                    if key in result:
                        return str(result[key])
            
            return str(result)
        except Exception as e:
            logger.exception(f"Error running component '{self.name}'")
            return f"Error: {str(e)}"
    
    async def process_stream(self, text: str):
        """
        Process message using streaming support if available.
        
        Args:
            text: The text message to process
            
        Yields:
            Chunks of the response as they arrive
        """
        # Try all modern LangChain streaming interfaces in priority order
        
        # 1. First check for modern Runnable streaming interfaces
        if isinstance(self.component, Runnable) or hasattr(self.component, "stream"):
            # astream is preferred for async streaming (modern LangChain)
            if hasattr(self.component, "astream") and callable(self.component.astream):
                try:
                    # Try various input formats
                    try:
                        # Direct input
                        async for chunk in self.component.astream(text):
                            yield self._extract_chunk_content(chunk)
                    except (TypeError, ValueError):
                        # Dictionary input
                        async for chunk in self.component.astream({"input": text}):
                            yield self._extract_chunk_content(chunk)
                    return  # Successfully used astream
                except Exception as e:
                    logger.warning(f"Error using astream for '{self.name}': {e}")
                    # Continue to next method
                    
            # Try stream method (synchronous streaming)
            if hasattr(self.component, "stream") and callable(self.component.stream):
                try:
                    # Try with direct input
                    try:
                        if asyncio.iscoroutinefunction(self.component.stream):
                            # Async implementation
                            async for chunk in self.component.stream(text):
                                yield self._extract_chunk_content(chunk)
                        else:
                            # Sync implementation
                            for chunk in self.component.stream(text):
                                yield self._extract_chunk_content(chunk)
                        return  # Successfully used stream
                    except (TypeError, ValueError):
                        # Try with dictionary input
                        if asyncio.iscoroutinefunction(self.component.stream):
                            # Async implementation
                            async for chunk in self.component.stream({"input": text}):
                                yield self._extract_chunk_content(chunk)
                        else:
                            # Sync implementation
                            for chunk in self.component.stream({"input": text}):
                                yield self._extract_chunk_content(chunk)
                        return  # Successfully used stream
                except Exception as e:
                    logger.warning(f"Error using stream for '{self.name}': {e}")
                    # Continue to next method
        
        # 2. Check for advanced streaming interfaces like astream_events and astream_log
        if hasattr(self.component, "astream_events") and callable(self.component.astream_events):
            try:
                # Try with direct input
                try:
                    async for event in self.component.astream_events(text):
                        # Process event types (end, tokens, etc.)
                        if hasattr(event, "event") and event.event == "on_llm_new_token":
                            if hasattr(event, "data") and hasattr(event.data, "token"):
                                yield event.data.token
                            elif hasattr(event, "token"):
                                yield event.token
                            elif hasattr(event, "data"):
                                yield str(event.data)
                        elif hasattr(event, "event") and event.event in ["on_chat_model_stream", "on_llm_stream"]:
                            if hasattr(event, "data") and hasattr(event.data, "chunk"):
                                yield self._extract_chunk_content(event.data.chunk)
                            elif hasattr(event, "chunk"):
                                yield self._extract_chunk_content(event.chunk)
                            elif hasattr(event, "data"):
                                yield str(event.data)
                except (TypeError, ValueError):
                    # Try with dictionary input
                    async for event in self.component.astream_events({"input": text}):
                        # Process event types
                        if hasattr(event, "event") and event.event == "on_llm_new_token":
                            if hasattr(event, "data") and hasattr(event.data, "token"):
                                yield event.data.token
                            elif hasattr(event, "token"):
                                yield event.token
                            elif hasattr(event, "data"):
                                yield str(event.data)
                        elif hasattr(event, "event") and event.event in ["on_chat_model_stream", "on_llm_stream"]:
                            if hasattr(event, "data") and hasattr(event.data, "chunk"):
                                yield self._extract_chunk_content(event.data.chunk)
                            elif hasattr(event, "chunk"):
                                yield self._extract_chunk_content(event.chunk)
                            elif hasattr(event, "data"):
                                yield str(event.data)
                return  # Successfully used astream_events
            except Exception as e:
                logger.warning(f"Error using astream_events for '{self.name}': {e}")
                # Continue to next method
                
        # Check for astream_log method (contains full intermediate steps)
        if hasattr(self.component, "astream_log") and callable(self.component.astream_log):
            try:
                # Try with direct input
                try:
                    async for log_entry in self.component.astream_log(text):
                        # Extract text from log entries
                        if isinstance(log_entry, str):
                            yield log_entry
                        elif isinstance(log_entry, dict):
                            if "output" in log_entry:
                                # Yield the output field
                                yield self._extract_chunk_content(log_entry["output"])
                            elif "final_output" in log_entry:
                                # Yield the final output
                                yield self._extract_chunk_content(log_entry["final_output"])
                            elif "intermediate_steps" in log_entry:
                                # Try to get something useful from intermediate steps
                                for step in log_entry["intermediate_steps"]:
                                    if hasattr(step, "output") or (isinstance(step, tuple) and len(step) > 1):
                                        output = step.output if hasattr(step, "output") else step[1]
                                        yield self._extract_chunk_content(output)
                except (TypeError, ValueError):
                    # Try with dictionary input
                    async for log_entry in self.component.astream_log({"input": text}):
                        # Extract text from log entries
                        if isinstance(log_entry, str):
                            yield log_entry
                        elif isinstance(log_entry, dict):
                            if "output" in log_entry:
                                # Yield the output field
                                yield self._extract_chunk_content(log_entry["output"])
                            elif "final_output" in log_entry:
                                # Yield the final output
                                yield self._extract_chunk_content(log_entry["final_output"])
                            elif "intermediate_steps" in log_entry:
                                # Try to get something useful from intermediate steps
                                for step in log_entry["intermediate_steps"]:
                                    if hasattr(step, "output") or (isinstance(step, tuple) and len(step) > 1):
                                        output = step.output if hasattr(step, "output") else step[1]
                                        yield self._extract_chunk_content(output)
                return  # Successfully used astream_log
            except Exception as e:
                logger.warning(f"Error using astream_log for '{self.name}': {e}")
                # Continue to next method
                
        # 3. Check for older or custom interfaces
        # Check for run_stream method (used by some LangChain Runnables)
        if hasattr(self.component, "run_stream") and callable(self.component.run_stream):
            try:
                # Check if run_stream is async
                if asyncio.iscoroutinefunction(self.component.run_stream):
                    try:
                        # Try with direct text
                        async for chunk in self.component.run_stream(text):
                            yield self._extract_chunk_content(chunk)
                    except (TypeError, ValueError):
                        # Try with dictionary
                        async for chunk in self.component.run_stream({"input": text}):
                            yield self._extract_chunk_content(chunk)
                else:
                    # Sync run_stream
                    try:
                        # Try with direct text
                        for chunk in self.component.run_stream(text):
                            yield self._extract_chunk_content(chunk)
                    except (TypeError, ValueError):
                        # Try with dictionary
                        for chunk in self.component.run_stream({"input": text}):
                            yield self._extract_chunk_content(chunk)
                return  # Successfully used run_stream
            except Exception as e:
                logger.warning(f"Error using run_stream for '{self.name}': {e}")
                # Continue to next method
                
        # If we get here, none of the streaming methods worked
        # Fall back to non-streaming
        logger.info(f"No compatible streaming method found for '{self.name}', using non-streaming fallback")
        result = await self.process_message(text)
        yield result
    
    def _extract_chunk_content(self, chunk: Any) -> str:
        """
        Extract text content from various chunk formats.
        
        Args:
            chunk: A chunk from a streaming response, could be string, dict, or object
            
        Returns:
            The extracted text content as a string
        """
        # String chunks
        if isinstance(chunk, str):
            return chunk
            
        # Object with content attribute
        if hasattr(chunk, "content"):
            return str(chunk.content)
            
        # Dictionary format with content
        if isinstance(chunk, dict):
            if "content" in chunk:
                return str(chunk["content"])
            elif "text" in chunk:
                return str(chunk["text"])
            elif "token" in chunk:
                return str(chunk["token"])
            elif "output" in chunk:
                # Try to extract output
                if isinstance(chunk["output"], str):
                    return chunk["output"]
                elif hasattr(chunk["output"], "content"):
                    return str(chunk["output"].content)
                elif isinstance(chunk["output"], dict) and "content" in chunk["output"]:
                    return str(chunk["output"]["content"])
            
            # If we can't extract specific fields, convert the whole dict to string
            return str(chunk)
            
        # Any other object, convert to string
        return str(chunk)


class LLMAdapter(ComponentAdapter):
    """Adapter for language model components."""
    
    def can_adapt(self) -> bool:
        """Check if component is a language model."""
        return (isinstance(self.component, (BaseLanguageModel, LLM)) or
                hasattr(self.component, "predict") or
                hasattr(self.component, "generate") or
                hasattr(self.component, "stream"))
    
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
    
    async def process_stream(self, text: str):
        """
        Process message using LLM streaming methods.
        
        Args:
            text: The text message to process
            
        Yields:
            Chunks of the response as they arrive
        """
        # Check if streaming is supported
        if hasattr(self.component, "stream") and callable(self.component.stream):
            try:
                # Check if stream is async
                if asyncio.iscoroutinefunction(self.component.stream):
                    # Handle streaming with different parameter formats
                    try:
                        # Try the modern parameter format first (text=text)
                        async for chunk in self.component.stream(text=text):
                            # Extract text from chunk based on its type
                            if isinstance(chunk, str):
                                yield chunk
                            elif hasattr(chunk, "content"):
                                yield chunk.content
                            elif isinstance(chunk, dict) and "content" in chunk:
                                yield chunk["content"]
                            elif isinstance(chunk, dict) and "text" in chunk:
                                yield chunk["text"]
                            else:
                                yield str(chunk)
                    except (TypeError, ValueError):
                        # Fall back to direct input (common in older versions)
                        async for chunk in self.component.stream(text):
                            # Extract text from chunk based on its type
                            if isinstance(chunk, str):
                                yield chunk
                            elif hasattr(chunk, "content"):
                                yield chunk.content
                            elif isinstance(chunk, dict) and "content" in chunk:
                                yield chunk["content"]
                            elif isinstance(chunk, dict) and "text" in chunk:
                                yield chunk["text"]
                            else:
                                yield str(chunk)
                else:
                    # Handle synchronous stream method
                    loop = asyncio.get_event_loop()
                    # We need to wrap the generator in an async generator
                    try:
                        # Try the modern parameter format first (text=text)
                        stream_gen = self.component.stream(text=text)
                        for chunk in stream_gen:
                            # Extract text from chunk based on its type
                            if isinstance(chunk, str):
                                yield chunk
                            elif hasattr(chunk, "content"):
                                yield chunk.content
                            elif isinstance(chunk, dict) and "content" in chunk:
                                yield chunk["content"]
                            elif isinstance(chunk, dict) and "text" in chunk:
                                yield chunk["text"]
                            else:
                                yield str(chunk)
                    except (TypeError, ValueError):
                        # Fall back to direct input
                        stream_gen = self.component.stream(text)
                        for chunk in stream_gen:
                            # Extract text from chunk based on its type
                            if isinstance(chunk, str):
                                yield chunk
                            elif hasattr(chunk, "content"):
                                yield chunk.content
                            elif isinstance(chunk, dict) and "content" in chunk:
                                yield chunk["content"]
                            elif isinstance(chunk, dict) and "text" in chunk:
                                yield chunk["text"]
                            else:
                                yield str(chunk)
            except Exception as e:
                logger.exception(f"Error using streaming for LLM '{self.name}': {e}")
                # Fall back to non-streaming
                result = await self.process_message(text)
                yield result
        else:
            # Fall back to non-streaming if stream is not available
            result = await self.process_message(text)
            yield result


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
    
    async def process_stream(self, text: str):
        """
        Process message with streaming support if available.
        
        Args:
            text: The text message to process
            
        Yields:
            Chunks of the response as they arrive
        """
        # Check if component has a stream method
        if hasattr(self.component, "stream") and callable(self.component.stream):
            try:
                # Check if stream is async
                if asyncio.iscoroutinefunction(self.component.stream):
                    async for chunk in self.component.stream(text):
                        # Extract text from chunk
                        if isinstance(chunk, str):
                            yield chunk
                        elif hasattr(chunk, "content"):
                            yield chunk.content
                        elif isinstance(chunk, dict) and "content" in chunk:
                            yield chunk["content"]
                        elif isinstance(chunk, dict) and "text" in chunk:
                            yield chunk["text"]
                        else:
                            yield str(chunk)
                else:
                    # Handle synchronous stream
                    for chunk in self.component.stream(text):
                        # Extract text from chunk
                        if isinstance(chunk, str):
                            yield chunk
                        elif hasattr(chunk, "content"):
                            yield chunk.content
                        elif isinstance(chunk, dict) and "content" in chunk:
                            yield chunk["content"]
                        elif isinstance(chunk, dict) and "text" in chunk:
                            yield chunk["text"]
                        else:
                            yield str(chunk)
            except Exception as e:
                logger.exception(f"Error streaming from component '{self.name}': {e}")
                # Fall back to non-streaming
                result = await self.process_message(text)
                yield result
        # Check for astream method (async streaming)
        elif hasattr(self.component, "astream") and callable(self.component.astream):
            try:
                async for chunk in self.component.astream(text):
                    # Extract text from chunk
                    if isinstance(chunk, str):
                        yield chunk
                    elif hasattr(chunk, "content"):
                        yield chunk.content
                    elif isinstance(chunk, dict) and "content" in chunk:
                        yield chunk["content"]
                    elif isinstance(chunk, dict) and "text" in chunk:
                        yield chunk["text"]
                    else:
                        yield str(chunk)
            except Exception as e:
                logger.exception(f"Error streaming from component '{self.name}': {e}")
                # Fall back to non-streaming
                result = await self.process_message(text)
                yield result
        else:
            # Fall back to non-streaming if streaming methods not available
            result = await self.process_message(text)
            yield result


class AdapterRegistry:
    """Registry for component adapters."""
    
    def __init__(self):
        """Initialize the registry."""
        self._adapters = []
        self._register_default_adapters()
    
    def _register_default_adapters(self):
        """Register the default set of adapters."""
        # Order matters - more specific adapters should be registered first
        # AgentAdapter is registered first, but it's selective enough to avoid false positives
        self.register(AgentAdapter)  # For LangChain AgentExecutor components
        self.register(InvocableAdapter)  # For components with invoke method (modern LangChain)
        self.register(LLMAdapter)  # For LLM components
        self.register(RunnableAdapter)  # For components with run method
        self.register(CallableAdapter)  # For callable components (fallback)
    
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
                
            def get_metadata(self):
                """
                Get metadata about this agent server, including streaming support.
                
                Returns:
                    A dictionary of metadata about this agent
                """
                metadata = super().get_metadata()
                
                # Add streaming capability if the component or adapter supports it
                streaming_support = (
                    hasattr(self.adapter, "process_stream") or
                    hasattr(self.component, "stream") or
                    hasattr(self.component, "astream") or
                    hasattr(self.component, "invoke_stream") or
                    hasattr(self.component, "run_stream")
                )
                
                if streaming_support and "streaming" not in metadata["capabilities"]:
                    metadata["capabilities"].append("streaming")
                
                return metadata
            
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
            
            async def stream_response(self, message):
                """
                Stream a response for the given message.
                
                This method implements streaming support for LangChain components
                by yielding incremental chunks of the response as they are generated.
                
                Args:
                    message: The A2A message to respond to
                    
                Yields:
                    Chunks of the response as they arrive
                """
                # Extract text from message
                if hasattr(message.content, 'text'):
                    text = message.content.text
                elif hasattr(message.content, '__str__'):
                    text = str(message.content)
                else:
                    text = repr(message.content)
                
                # Check if the adapter has a process_stream method
                if hasattr(self.adapter, "process_stream"):
                    try:
                        # Use the adapter's streaming capabilities
                        async for chunk in self.adapter.process_stream(text):
                            # Format chunk as a dictionary to maintain API consistency
                            if isinstance(chunk, str):
                                yield {"content": chunk}
                            elif isinstance(chunk, dict):
                                yield chunk
                            else:
                                yield {"content": str(chunk)}
                    except Exception as e:
                        # Log the error and fall back to non-streaming
                        logger.exception(f"Error streaming from adapter: {e}")
                        # Fall back to the regular message processing
                        result = await self.adapter.process_message(text)
                        yield {"content": result}
                # Direct component streaming fallback
                elif hasattr(self.component, "stream") and callable(self.component.stream):
                    try:
                        # Use LangChain's native streaming capabilities if available
                        if asyncio.iscoroutinefunction(self.component.stream):
                            # Async streaming
                            async for chunk in self.component.stream(text):
                                # Extract text and format as dictionary
                                if isinstance(chunk, str):
                                    yield {"content": chunk}
                                elif hasattr(chunk, "content"):
                                    yield {"content": chunk.content}
                                elif isinstance(chunk, dict) and "content" in chunk:
                                    yield chunk
                                elif isinstance(chunk, dict) and "text" in chunk:
                                    yield {"content": chunk["text"]}
                                else:
                                    yield {"content": str(chunk)}
                        else:
                            # Sync streaming in async context
                            for chunk in self.component.stream(text):
                                # Extract text and format as dictionary
                                if isinstance(chunk, str):
                                    yield {"content": chunk}
                                elif hasattr(chunk, "content"):
                                    yield {"content": chunk.content}
                                elif isinstance(chunk, dict) and "content" in chunk:
                                    yield chunk
                                elif isinstance(chunk, dict) and "text" in chunk:
                                    yield {"content": chunk["text"]}
                                else:
                                    yield {"content": str(chunk)}
                    except Exception as e:
                        # Log the error and fall back to non-streaming
                        logger.exception(f"Error streaming from LangChain component: {e}")
                        result = await self.adapter.process_message(text)
                        yield {"content": result}
                else:
                    # Fall back to non-streaming if no streaming capability is found
                    result = await self.adapter.process_message(text)
                    yield {"content": result}
            
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