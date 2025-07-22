"""
MCP protocol conversions for LangChain integration.

This module provides functions to convert between LangChain tools and MCP servers/tools.
"""

import logging
import asyncio
import inspect
import json
import requests
from typing import Any, Dict, List, Optional, Union, Callable, Type, get_type_hints
import traceback

logger = logging.getLogger(__name__)

# Import custom exceptions
from .exceptions import (
    LangChainNotInstalledError,
    LangChainToolConversionError,
    MCPToolConversionError,
    MCPNotInstalledError
)

# Check for LangChain availability without failing
try:
    # Try to import LangChain components
    try:
        from langchain_core.tools import BaseTool, ToolException, tool
    except ImportError:
        # Fall back to older LangChain structure
        from langchain.tools import BaseTool, ToolException
    
    HAS_LANGCHAIN = True
except ImportError:
    HAS_LANGCHAIN = False
    # Create stub classes for type hints
    class BaseTool:
        name: str
        description: str
    
    class ToolException(Exception):
        pass

# Check for MCP availability without failing
try:
    from mcp import ClientSession, Tool as MCPTool
    from mcp.client.streamable_http import streamablehttp_client
    HAS_MCP = True
except ImportError:
    HAS_MCP = False

# Utility for mapping between Python types and MCP types
class TypeMapper:
    """Maps between Python types and MCP parameter types."""
    
    # Map Python types to MCP types
    PYTHON_TO_MCP = {
        str: "string",
        int: "integer",
        float: "number",
        bool: "boolean",
        list: "array",
        dict: "object",
        None: "string"  # Default
    }
    
    # Map MCP types to Python types
    MCP_TO_PYTHON = {
        "string": str,
        "integer": int,
        "number": float,
        "boolean": bool,
        "array": list,
        "object": dict
    }
    
    @classmethod
    def to_mcp_type(cls, python_type: Type) -> str:
        """Convert Python type to MCP type string."""
        # Handle generic types like List[str]
        origin = getattr(python_type, "__origin__", None)
        if origin is not None:
            # Map the origin type
            if origin in cls.PYTHON_TO_MCP:
                return cls.PYTHON_TO_MCP[origin]
            # Fall back to string for unknown generics
            return "string"
        
        # Handle direct type mappings
        return cls.PYTHON_TO_MCP.get(python_type, "string")
    
    @classmethod
    def to_python_type(cls, mcp_type: str) -> Type:
        """Convert MCP type string to Python type."""
        return cls.MCP_TO_PYTHON.get(mcp_type, str)


class ParameterExtractor:
    """Extracts parameter information from LangChain tools."""
    
    @classmethod
    def extract_from_tool(cls, tool: Any) -> List[Dict[str, Any]]:
        """Extract parameters from a LangChain tool using multiple strategies."""
        # Use multiple strategies in order of preference
        
        # Strategy 1: Try to get from args_schema
        parameters = cls._extract_from_args_schema(tool)
        if parameters:
            return parameters
        
        # Strategy 2: Try to get from _run method signature
        if hasattr(tool, "_run"):
            parameters = cls._extract_from_method(tool._run)
            if parameters:
                return parameters
        
        # Strategy 3: Try to get from func attribute
        if hasattr(tool, "func") and callable(tool.func):
            parameters = cls._extract_from_method(tool.func)
            if parameters:
                return parameters
        
        # Strategy 4: Fall back to default single parameter
        return cls._default_parameter(tool)
    
    @classmethod
    def _extract_from_args_schema(cls, tool: Any) -> List[Dict[str, Any]]:
        """Extract parameters from tool's args_schema attribute."""
        if not hasattr(tool, "args_schema") or not tool.args_schema:
            return []
        
        parameters = []
        schema_cls = tool.args_schema
        
        if hasattr(schema_cls, "__annotations__"):
            for field_name, field_type in schema_cls.__annotations__.items():
                # Determine required status and description
                required = True
                description = f"Parameter: {field_name}"
                
                # Try to get field info from different Pydantic versions
                if hasattr(schema_cls, "__fields__"):  # Pydantic v1
                    field_info = schema_cls.__fields__.get(field_name)
                    if field_info and hasattr(field_info, "field_info"):
                        required = not field_info.allow_none
                        field_desc = getattr(field_info.field_info, "description", None)
                        if field_desc:
                            description = field_desc
                
                elif hasattr(schema_cls, "model_fields"):  # Pydantic v2
                    field_info = schema_cls.model_fields.get(field_name)
                    if field_info:
                        required = not getattr(field_info, "allow_none", False)
                        field_desc = getattr(field_info, "description", None)
                        if field_desc:
                            description = field_desc
                
                # Create parameter schema
                parameters.append({
                    "name": field_name,
                    "type": TypeMapper.to_mcp_type(field_type),
                    "description": description,
                    "required": required
                })
        
        return parameters
    
    @classmethod
    def _extract_from_method(cls, method: Callable) -> List[Dict[str, Any]]:
        """Extract parameters from a method signature."""
        parameters = []
        
        try:
            sig = inspect.signature(method)
            type_hints = get_type_hints(method)
            
            for param_name, param in sig.parameters.items():
                if param_name == "self":
                    continue
                if param_name == "config":  # Skip config parameter for LangChain tools
                    continue
                
                param_type = type_hints.get(param_name, str)
                param_required = param.default == inspect.Parameter.empty
                
                parameters.append({
                    "name": param_name,
                    "type": TypeMapper.to_mcp_type(param_type),
                    "description": f"Parameter: {param_name}",
                    "required": param_required
                })
        except Exception as e:
            logger.debug(f"Error extracting parameters from method: {e}")
        
        return parameters
    
    @classmethod
    def _default_parameter(cls, tool: Any) -> List[Dict[str, Any]]:
        """Create a default single parameter for tools."""
        return [{
            "name": "input",
            "type": "string",
            "description": f"Input for {tool.name}",
            "required": True
        }]


class ToolUtil:
    """Utility functions for working with LangChain tools."""
    
    @staticmethod
    def normalize_input(tool: Any, **kwargs) -> Any:
        """Normalize input data for a tool based on its expected format."""
        # Check for single string input pattern
        single_string_input = getattr(tool, "expects_string_input", False)
        if single_string_input:
            if len(kwargs) == 1:
                # If only one parameter, pass its value directly
                return next(iter(kwargs.values()))
            # Otherwise, serialize to JSON
            return json.dumps(kwargs)
        
        # Check signature of _run method
        if hasattr(tool, "_run"):
            sig = inspect.signature(tool._run)
            params = list(sig.parameters.values())
            
            # If only one non-self parameter and it's not **kwargs
            if len(params) == 2 and params[1].name != "kwargs" and params[1].kind != inspect.Parameter.VAR_KEYWORD:
                # If we have just the expected parameter, pass its value
                if len(kwargs) == 1 and next(iter(kwargs.keys())) == params[1].name:
                    return next(iter(kwargs.values()))
                # Otherwise, pass all kwargs as a single param if possible
                if len(kwargs) == 1:
                    return next(iter(kwargs.values()))
        
        # Check signature of func attribute if available
        if hasattr(tool, "func") and callable(tool.func):
            try:
                sig = inspect.signature(tool.func)
                param_names = set()
                for param_name, param in sig.parameters.items():
                    if param_name != "self" and param_name != "config":
                        param_names.add(param_name)
                
                # Filter kwargs to only include parameters that exist in the function signature
                filtered_kwargs = {}
                for key, value in kwargs.items():
                    if key in param_names:
                        filtered_kwargs[key] = value
                
                if filtered_kwargs:
                    return filtered_kwargs
            except Exception as e:
                logger.debug(f"Error analyzing func signature: {e}")
        
        # Default: return kwargs as is
        return kwargs
    
    @staticmethod
    def normalize_output(result: Any) -> Dict[str, Any]:
        """Normalize tool output to MCP response format."""
        # Already in MCP format with text or error key
        if isinstance(result, dict) and ("text" in result or "error" in result):
            return result
        
        # String result
        if isinstance(result, str):
            return {"text": result}
        
        # Error result
        if isinstance(result, Exception):
            return {"error": str(result)}
        
        # None result
        if result is None:
            return {"text": ""}
        
        # Any other type, convert to string
        return {"text": str(result)}


def to_mcp_server(langchain_tools):
    """
    Create an MCP server that exposes LangChain tools.
    
    Args:
        langchain_tools: Single tool or list of LangChain tools
    
    Returns:
        MCP server instance
    
    Example:
        >>> from langchain.tools import Tool
        >>> calculator = Tool(name="calculator", func=lambda x: eval(x))
        >>> server = to_mcp_server([calculator])
        >>> server.run(port=8000)
        
    Raises:
        LangChainNotInstalledError: If LangChain is not installed
        LangChainToolConversionError: If tool conversion fails
    """
    if not HAS_LANGCHAIN:
        raise LangChainNotInstalledError()
    
    try:
        from python_a2a.mcp import FastMCP
        
        # Create server instance with explicit name and description
        server = FastMCP(
            name="LangChain Tools",
            description="MCP server exposing LangChain tools"
        )
        
        # Store tools map in the server for later reference
        server.tools_map = {}
        
        # Handle single tool case
        if not isinstance(langchain_tools, list):
            langchain_tools = [langchain_tools]
        
        # Register each tool with the server
        for tool in langchain_tools:
            # Validate tool
            if not hasattr(tool, "name"):
                raise LangChainToolConversionError("Tool must have a name attribute")
            
            # Check for execution method (one of them must exist)
            executable = (hasattr(tool, "_run") or hasattr(tool, "func") or 
                          (hasattr(tool, "__call__") and callable(tool)))
            if not executable:
                raise LangChainToolConversionError(
                    f"Tool '{tool.name}' has no execution method (_run, func, or __call__)"
                )
            
            # Get tool information
            tool_name = tool.name
            tool_description = getattr(tool, "description", f"Tool: {tool_name}")
            
            # Store the tool for later reference
            server.tools_map[tool_name] = tool
            
            # Extract parameter information
            parameters = ParameterExtractor.extract_from_tool(tool)
            
            # Create a wrapper function for this tool
            def create_tool_wrapper(current_tool_name, current_tool):
                # Create the async wrapper function
                async def wrapper(**kwargs):
                    """Wrapper that calls the LangChain tool."""
                    try:
                        # Extract parameters for the specific tool being called
                        input_data = kwargs
                        
                        # Get parameters specific to this tool's function
                        if hasattr(current_tool, "func") and callable(current_tool.func):
                            try:
                                sig = inspect.signature(current_tool.func)
                                valid_params = {}
                                
                                # Only include parameters that exist in the function signature
                                for param_name, param in sig.parameters.items():
                                    if param_name in kwargs:
                                        valid_params[param_name] = kwargs[param_name]
                                
                                if valid_params:
                                    input_data = valid_params
                            except Exception as e:
                                logger.debug(f"Error analyzing func signature: {e}")
                        
                        # Try using func directly first if available
                        result = None
                        if hasattr(current_tool, "func") and callable(current_tool.func):
                            loop = asyncio.get_event_loop()
                            try:
                                if isinstance(input_data, dict):
                                    result = await loop.run_in_executor(
                                        None, 
                                        lambda: current_tool.func(**input_data)
                                    )
                                else:
                                    result = await loop.run_in_executor(
                                        None, 
                                        lambda: current_tool.func(input_data)
                                    )
                            except Exception as e:
                                logger.debug(f"Error using func directly: {e}")
                                # Continue to other methods
                        
                        # If no result yet, try _run with config parameter
                        if result is None and hasattr(current_tool, "_run"):
                            loop = asyncio.get_event_loop()
                            try:
                                if isinstance(input_data, dict):
                                    result = await loop.run_in_executor(
                                        None, 
                                        lambda: current_tool._run(config={}, **input_data)
                                    )
                                else:
                                    result = await loop.run_in_executor(
                                        None, 
                                        lambda: current_tool._run(input_data, config={})
                                    )
                            except TypeError as e:
                                if "config" in str(e):
                                    # Try without config for older versions
                                    try:
                                        if isinstance(input_data, dict):
                                            result = await loop.run_in_executor(
                                                None, 
                                                lambda: current_tool._run(**input_data)
                                            )
                                        else:
                                            result = await loop.run_in_executor(
                                                None, 
                                                lambda: current_tool._run(input_data)
                                            )
                                    except Exception as inner_e:
                                        logger.debug(f"Error in _run without config: {inner_e}")
                                else:
                                    logger.debug(f"TypeError in _run: {e}")
                            except Exception as e:
                                logger.debug(f"Error in _run: {e}")
                        
                        # If we still have no result, raise an error
                        if result is None:
                            return {"error": f"Failed to execute tool {current_tool_name} with the provided parameters"}
                        
                        # Normalize the output
                        return ToolUtil.normalize_output(result)
                    
                    except ToolException as e:
                        # Handle LangChain tool exceptions
                        logger.warning(f"Tool exception in {current_tool_name}: {e}")
                        return {"error": str(e)}
                    except Exception as e:
                        # Handle any other exceptions
                        logger.exception(f"Error calling tool {current_tool_name}")
                        return {"error": f"Error: {str(e)}"}
                
                return wrapper
            
            # Create and register wrapper for this specific tool
            wrapper_func = create_tool_wrapper(tool_name, tool)
            
            # Use decorator pattern to register the tool with FastMCP
            server.tool(
                name=tool_name,
                description=tool_description
            )(wrapper_func)
            
            logger.debug(f"Registered tool: {tool_name}")
        
        return server
        
    except Exception as e:
        logger.exception("Failed to create MCP server from LangChain tools")
        raise LangChainToolConversionError(f"Failed to convert LangChain tools: {str(e)}")
    


async def get_tool(available_tool: MCPTool, mcp_url: str):
    """
    Get langchain tool function for a mentioned MCP Tool from MCP Server
    """
    tool_name = available_tool.name
    if not tool_name:
        logger.exception("Tool Name not found in the tool")
        raise LangChainToolConversionError("Tool Name not found in the tool")
    parameters = available_tool.inputSchema["properties"].values()
    args = [i["title"].lower() for i in parameters]
    args = [i.replace(" ", "_") for i in args]
    arg_names = ", ".join(args)
    func_def_str = f"""
@tool
async def {tool_name}({arg_names}):
    '''Call MCP tool function'''
    args2 = "{arg_names}".split(", ")
    body = {{}}
    for a in args2:
        body[a] = locals()[a]
    try:
        async with streamablehttp_client("{mcp_url}") as (
            read_stream, write_stream, _,
            ):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.call_tool("{tool_name}", body)
                if "error" in result:
                    return f"Error: {{result['error']}}"
                
                # Process content in response
                if "content" in result:
                    content = result.get("content", [])
                    if content and isinstance(content, list) and "text" in content[0]:
                        return content[0]["text"]
                
                # If no structured content, return the raw result
                return str(result)

    except BaseException as e:
        return f"Error while calling tool: {{e}}"                        
                """
    dynamic_scope = {}

    exec(func_def_str, globals(), dynamic_scope)
    the_tool = dynamic_scope[tool_name]
    return the_tool


async def to_langchain_tool(mcp_url, tool_name=None):
    """
    Get Convert MCP server tool(s) & Convert them to LangChain tool(s).
    
    Args:
        mcp_url: URL of the MCP server
        tool_name: Optional specific tool to convert (if None, converts all tools)
    
    Returns:
        LangChain tool or list of tools
    
    Example:
        >>> # Convert a specific tool
        >>> calculator_tool = await to_langchain_tool("http://localhost:8080/mcp", "calculator")
        >>> #or
        >>> calculator_tool = asyncio.run(to_langchain_tool("http://localhost:8080/mcp", "calculator"))
        >>> # Convert all tools from a server
        >>> tools = await to_langchain_tool("http://localhost:8080/mcp")
        >>> #or
        >>> tools = asyncio.run(to_langchain_tool("http://localhost:8080/mcp"))
        
    Raises:
        LangChainNotInstalledError: If LangChain is not installed
        MCPToolConversionError: If tool conversion fails
    """
    if not HAS_LANGCHAIN:
        raise LangChainNotInstalledError()
    
    if not HAS_MCP:
        raise MCPNotInstalledError()
        
    try:        
        # Get available tools from MCP server
        langchain_tools = []
        try:
            async with streamablehttp_client(f"{mcp_url}") as (
                read_stream, write_stream, _,
            ):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    available_tools = await session.list_tools()

                    if tool_name:
                        available_tool = [t for t in available_tools.tools if t.name == tool_name][0]
                        the_tool = await get_tool(available_tool, mcp_url)
                        return the_tool
                    
                    all_available_tools = [t for t in available_tools.tools ]
                    for a_tool in all_available_tools:
                        the_tool = await get_tool(a_tool, mcp_url)
                        langchain_tools.append(the_tool)
                    return langchain_tools
        except Exception as e:
            logger.error(f"Error getting tools from MCP server: {e}")
            raise MCPToolConversionError(f"Failed to get tools from MCP server: {str(e)}")
        
        # Filter tools if a specific tool is requested
        
    except MCPToolConversionError:
        # Re-raise without wrapping
        raise
    except Exception as e:
        logger.exception("Failed to convert MCP tool to LangChain format")
        raise MCPToolConversionError(f"Failed to convert MCP tool: {str(e)}")
