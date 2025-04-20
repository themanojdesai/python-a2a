"""
Workflow step implementations for agent workflows.

This module provides various step implementations for the workflow system,
including query steps, function execution steps, and conditional branching steps.
"""

import logging
import asyncio
import copy
from typing import Dict, List, Any, Optional, Callable, Union, Set
from enum import Enum
import uuid
import time

from ..client.base import BaseA2AClient

logger = logging.getLogger(__name__)


class StepType(str, Enum):
    """Types of workflow steps."""
    QUERY = "query"
    FUNCTION = "function"
    CONDITION = "condition"
    PARALLEL = "parallel"
    IF_BRANCH = "if_branch"
    ELSE_BRANCH = "else_branch"


class WorkflowStep:
    """Base class for all workflow steps."""
    
    def __init__(
        self, 
        id: Optional[str] = None, 
        type: StepType = StepType.QUERY,
        retries: int = 0,
        timeout: Optional[float] = None
    ):
        """
        Initialize a workflow step.
        
        Args:
            id: Unique identifier for the step
            type: Type of step
            retries: Number of retry attempts if the step fails
            timeout: Maximum execution time in seconds
        """
        self.id = id or str(uuid.uuid4())
        self.type = type
        self.retries = retries
        self.timeout = timeout
    
    async def execute(self, context) -> Any:
        """
        Execute the workflow step.
        
        Args:
            context: Current workflow context
            
        Returns:
            Step result
        """
        raise NotImplementedError("Subclasses must implement this method")


class QueryStep(WorkflowStep):
    """Step for querying an agent."""
    
    def __init__(
        self,
        agent_name: str,
        query: str,
        agent_network,
        id: Optional[str] = None,
        retries: int = 0,
        timeout: Optional[float] = None
    ):
        """
        Initialize a query step.
        
        Args:
            agent_name: Name of the agent to query
            query: The query to send to the agent
            agent_network: Network of available agents
            id: Unique identifier for the step
            retries: Number of retry attempts if the step fails
            timeout: Maximum execution time in seconds
        """
        super().__init__(id, StepType.QUERY, retries, timeout)
        self.agent_name = agent_name
        self.query_template = query
        self.agent_network = agent_network
    
    async def execute(self, context) -> Any:
        """
        Execute the query step.
        
        Args:
            context: Current workflow context
            
        Returns:
            Agent response
        """
        # Substitute context variables in the query
        query = self.query_template
        for key, value in context.data.items():
            placeholder = f"{{{key}}}"
            if placeholder in query and isinstance(value, str):
                query = query.replace(placeholder, value)
        
        # Get the agent
        agent = self.agent_network.get_agent(self.agent_name)
        if not agent:
            raise ValueError(f"Agent '{self.agent_name}' not found in network")
        
        # Execute the query with retries
        attempts = 0
        last_error = None
        
        while attempts <= self.retries:
            try:
                # Add timeout if specified
                if self.timeout:
                    # Create a task with timeout
                    coro = asyncio.create_task(self._ask_agent(agent, query))
                    result = await asyncio.wait_for(coro, timeout=self.timeout)
                else:
                    # Execute without timeout
                    result = await self._ask_agent(agent, query)
                
                # Store execution info in context history
                context.add_to_history({
                    "step_id": self.id,
                    "step_type": self.type,
                    "agent": self.agent_name,
                    "query": query,
                    "attempt": attempts + 1,
                    "success": True,
                    "timestamp": time.time()
                })
                
                return result
                
            except Exception as e:
                attempts += 1
                last_error = e
                
                # Store failed attempt in history
                context.add_to_history({
                    "step_id": self.id,
                    "step_type": self.type,
                    "agent": self.agent_name,
                    "query": query,
                    "attempt": attempts,
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                })
                
                # If we have retries left, wait before retrying
                if attempts <= self.retries:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempts * 0.1)
        
        # If we get here, all attempts failed
        if last_error:
            context.add_error(self.id, last_error)
            raise last_error
    
    async def _ask_agent(self, agent: BaseA2AClient, query: str) -> str:
        """Send query to agent and return response."""
        # If the agent has an async API, use it
        if hasattr(agent, 'ask_async'):
            return await agent.ask_async(query)
        
        # Otherwise, use the synchronous API in a thread
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, agent.ask, query)


class AutoRouteStep(WorkflowStep):
    """Step for automatically routing a query to the best agent."""
    
    def __init__(
        self,
        query: str,
        agent_network,
        router,
        id: Optional[str] = None,
        retries: int = 0,
        timeout: Optional[float] = None
    ):
        """
        Initialize an auto-route step.
        
        Args:
            query: The query to route and send
            agent_network: Network of available agents
            router: AI router for agent selection
            id: Unique identifier for the step
            retries: Number of retry attempts if the step fails
            timeout: Maximum execution time in seconds
        """
        super().__init__(id, StepType.QUERY, retries, timeout)
        self.query_template = query
        self.agent_network = agent_network
        self.router = router
    
    async def execute(self, context) -> Any:
        """
        Execute the auto-route step.
        
        Args:
            context: Current workflow context
            
        Returns:
            Agent response
        """
        # Substitute context variables in the query
        query = self.query_template
        for key, value in context.data.items():
            placeholder = f"{{{key}}}"
            if placeholder in query and isinstance(value, str):
                query = query.replace(placeholder, value)
        
        # Get conversation history from context if available
        history = context.data.get("conversation_history", [])
        
        # Route the query to the best agent
        agent_name, confidence = self.router.route_query(query, history)
        
        # Get the agent
        agent = self.agent_network.get_agent(agent_name)
        if not agent:
            raise ValueError(f"Agent '{agent_name}' not found in network")
        
        # Create a query step with the selected agent
        query_step = QueryStep(
            agent_name=agent_name,
            query=query,
            agent_network=self.agent_network,
            id=self.id,
            retries=self.retries,
            timeout=self.timeout
        )
        
        # Add routing info to context
        context.update("selected_agent", agent_name)
        context.update("routing_confidence", confidence)
        
        # Execute the query step
        result = await query_step.execute(context)
        
        # Update conversation history
        if "conversation_history" not in context.data:
            context.data["conversation_history"] = []
        
        context.data["conversation_history"].append({
            "role": "user",
            "content": {"text": query}
        })
        
        context.data["conversation_history"].append({
            "role": "agent",
            "content": {"text": result if isinstance(result, str) else str(result)}
        })
        
        return result


class FunctionStep(WorkflowStep):
    """Step for executing a custom function."""
    
    def __init__(
        self,
        func: Callable[..., Any],
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        id: Optional[str] = None,
        retries: int = 0,
        timeout: Optional[float] = None
    ):
        """
        Initialize a function step.
        
        Args:
            func: Function to execute
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            id: Unique identifier for the step
            retries: Number of retry attempts if the step fails
            timeout: Maximum execution time in seconds
        """
        super().__init__(id, StepType.FUNCTION, retries, timeout)
        self.func = func
        self.args = args or []
        self.kwargs = kwargs or {}
    
    async def execute(self, context) -> Any:
        """
        Execute the function step.
        
        Args:
            context: Current workflow context
            
        Returns:
            Function result
        """
        # Substitute context variables in args and kwargs
        processed_args = []
        for arg in self.args:
            if isinstance(arg, str) and arg.startswith("{") and arg.endswith("}"):
                key = arg[1:-1]
                if key in context.data:
                    processed_args.append(context.data[key])
                else:
                    processed_args.append(arg)
            else:
                processed_args.append(arg)
        
        processed_kwargs = {}
        for k, v in self.kwargs.items():
            if isinstance(v, str) and v.startswith("{") and v.endswith("}"):
                key = v[1:-1]
                if key in context.data:
                    processed_kwargs[k] = context.data[key]
                else:
                    processed_kwargs[k] = v
            else:
                processed_kwargs[k] = v
        
        # Add context as a special keyword argument if the function accepts it
        import inspect
        sig = inspect.signature(self.func)
        if "context" in sig.parameters:
            processed_kwargs["context"] = context
        
        # Execute the function with retries
        attempts = 0
        last_error = None
        
        while attempts <= self.retries:
            try:
                # Check if function is async
                if asyncio.iscoroutinefunction(self.func):
                    # Execute with timeout if specified
                    if self.timeout:
                        coro = self.func(*processed_args, **processed_kwargs)
                        result = await asyncio.wait_for(coro, timeout=self.timeout)
                    else:
                        result = await self.func(*processed_args, **processed_kwargs)
                else:
                    # Run synchronous function in executor
                    loop = asyncio.get_event_loop()
                    if self.timeout:
                        coro = loop.run_in_executor(
                            None, lambda: self.func(*processed_args, **processed_kwargs))
                        result = await asyncio.wait_for(coro, timeout=self.timeout)
                    else:
                        result = await loop.run_in_executor(
                            None, lambda: self.func(*processed_args, **processed_kwargs))
                
                # Store execution info in context history
                context.add_to_history({
                    "step_id": self.id,
                    "step_type": self.type,
                    "function": self.func.__name__,
                    "attempt": attempts + 1,
                    "success": True,
                    "timestamp": time.time()
                })
                
                return result
                
            except Exception as e:
                attempts += 1
                last_error = e
                
                # Store failed attempt in history
                context.add_to_history({
                    "step_id": self.id,
                    "step_type": self.type,
                    "function": self.func.__name__,
                    "attempt": attempts,
                    "success": False,
                    "error": str(e),
                    "timestamp": time.time()
                })
                
                # If we have retries left, wait before retrying
                if attempts <= self.retries:
                    # Exponential backoff
                    await asyncio.sleep(2 ** attempts * 0.1)
        
        # If we get here, all attempts failed
        if last_error:
            context.add_error(self.id, last_error)
            raise last_error


class ConditionalBranch:
    """Represents a conditional branch in the workflow."""
    
    def __init__(self, condition_func: Callable[[Any], bool], steps: List[WorkflowStep]):
        """
        Initialize a conditional branch.
        
        Args:
            condition_func: Function that evaluates the condition
            steps: Steps to execute if condition is true
        """
        self.condition_func = condition_func
        self.steps = steps


class ConditionStep(WorkflowStep):
    """Step for conditional branching."""
    
    def __init__(
        self,
        branches: List[ConditionalBranch],
        else_steps: Optional[List[WorkflowStep]] = None,
        id: Optional[str] = None
    ):
        """
        Initialize a condition step.
        
        Args:
            branches: List of conditional branches
            else_steps: Steps to execute if no conditions are met
            id: Unique identifier for the step
        """
        super().__init__(id, StepType.CONDITION)
        self.branches = branches
        self.else_steps = else_steps or []
    
    async def execute(self, context) -> Any:
        """
        Execute the condition step.
        
        Args:
            context: Current workflow context
            
        Returns:
            Result of the executed branch
        """
        # Get the latest result from context
        latest_result = context.last_result
        
        # Evaluate each condition
        for branch in self.branches:
            try:
                # Check if condition is met
                condition_met = branch.condition_func(latest_result)
                if condition_met:
                    # Execute branch steps
                    branch_result = None
                    for step in branch.steps:
                        step_result = await step.execute(context)
                        context.add_result(step.id, step_result)
                        branch_result = step_result
                    
                    return branch_result
            except Exception as e:
                # Log condition evaluation error
                logger.warning(f"Error evaluating condition in step {self.id}: {e}")
                context.add_error(self.id, e)
        
        # If no conditions were met, execute else steps
        else_result = None
        for step in self.else_steps:
            step_result = await step.execute(context)
            context.add_result(step.id, step_result)
            else_result = step_result
        
        return else_result


class ParallelStep(WorkflowStep):
    """Step for parallel execution of multiple steps."""
    
    def __init__(
        self,
        steps: List[WorkflowStep],
        id: Optional[str] = None,
        max_concurrency: Optional[int] = None
    ):
        """
        Initialize a parallel step.
        
        Args:
            steps: Steps to execute in parallel
            id: Unique identifier for the step
            max_concurrency: Maximum number of steps to execute concurrently
        """
        super().__init__(id, StepType.PARALLEL)
        self.steps = steps
        self.max_concurrency = max_concurrency
    
    async def execute(self, context) -> Dict[str, Any]:
        """
        Execute multiple steps in parallel.
        
        Args:
            context: Current workflow context
            
        Returns:
            Dictionary mapping step IDs to results
        """
        # Create a new context for each parallel branch
        contexts = {step.id: copy.deepcopy(context) for step in self.steps}
        
        # Execute steps concurrently
        if self.max_concurrency:
            # Use semaphore to limit concurrency
            semaphore = asyncio.Semaphore(self.max_concurrency)
            
            async def execute_with_semaphore(step, step_context):
                async with semaphore:
                    return await step.execute(step_context)
            
            tasks = [
                asyncio.create_task(execute_with_semaphore(step, contexts[step.id]))
                for step in self.steps
            ]
        else:
            # Execute all steps concurrently
            tasks = [
                asyncio.create_task(step.execute(contexts[step.id]))
                for step in self.steps
            ]
        
        # Wait for all tasks to complete
        results = {}
        step_id_map = {id(task): step.id for task, step in zip(tasks, self.steps)}
        step_map = {id(task): step for task, step in zip(tasks, self.steps)}
        
        for completed_task in asyncio.as_completed(tasks):
            step_id = step_id_map[id(completed_task)]
            step = step_map[id(completed_task)]
            try:
                result = await completed_task
                results[step_id] = result
                context.add_result(step_id, result)
                
                # Merge step context back into main context
                for key, value in contexts[step_id].data.items():
                    if key not in context.data:
                        context.data[key] = value
                
                # Merge history
                context.history.extend(contexts[step_id].history)
                
            except Exception as e:
                logger.error(f"Error in parallel step {step_id}: {e}")
                context.add_error(step_id, e)
                results[step_id] = None
        
        return results