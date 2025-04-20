"""
Flow-based API for defining agent workflows.

This module provides the core Flow class for defining complex agent workflows
using a fluent interface with method chaining.
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional, Callable, Union, Set
import copy
import uuid
import time

from ..client.router import AIAgentRouter
from .steps import (
    WorkflowStep, 
    QueryStep, 
    AutoRouteStep, 
    FunctionStep,
    ConditionalBranch, 
    ConditionStep, 
    ParallelStep
)

logger = logging.getLogger(__name__)


class WorkflowContext:
    """Context object for workflow execution."""
    
    def __init__(self, initial_data: Optional[Dict[str, Any]] = None):
        """
        Initialize workflow context.
        
        Args:
            initial_data: Optional initial context data
        """
        self.data = initial_data or {}
        self.results = {}
        self.history = []
        self.errors = []
        self.start_time = time.time()
    
    def update(self, key: str, value: Any) -> None:
        """Update context with new data."""
        self.data[key] = value
    
    def add_result(self, step_id: str, result: Any) -> None:
        """Add a step result to the context."""
        self.results[step_id] = result
        # Also add the latest result as a special key
        self.data["latest_result"] = result
    
    def add_to_history(self, step_info: Dict[str, Any]) -> None:
        """Add step execution info to history."""
        self.history.append(step_info)
    
    def add_error(self, step_id: str, error: Exception) -> None:
        """Add an error to the context."""
        error_info = {
            "step_id": step_id,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "timestamp": time.time()
        }
        self.errors.append(error_info)
    
    @property
    def last_result(self) -> Any:
        """Get the most recent result."""
        if not self.results:
            return None
        return next(iter(reversed(self.results.values())))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to a dictionary."""
        return {
            "data": self.data,
            "results": self.results,
            "history": self.history,
            "errors": self.errors,
            "execution_time": time.time() - self.start_time
        }


class Flow:
    """
    Fluent API for building and executing agent workflows.
    
    This class provides a simple interface for defining complex agent workflows
    with conditional branching, parallel execution, and automatic agent routing.
    """
    
    def __init__(
        self, 
        agent_network: 'AgentNetwork',
        router: Optional[AIAgentRouter] = None,
        name: str = "Workflow"
    ):
        """
        Initialize a workflow.
        
        Args:
            agent_network: Network of available agents
            router: Optional AI router for agent selection
            name: Workflow name
        """
        self.agent_network = agent_network
        self.router = router
        self.name = name
        self.steps = []
        self.current_branch = self.steps
        self.branch_stack = []
        self.condition_steps = []
    
    def ask(self, agent_name: str, query: str, **options) -> 'Flow':
        """
        Add a step to ask an agent a question.
        
        Args:
            agent_name: Name of the agent to query
            query: The query to send to the agent
            **options: Additional options for the step
            
        Returns:
            Self for method chaining
        """
        step = QueryStep(
            agent_name=agent_name,
            query=query,
            agent_network=self.agent_network,
            retries=options.get('retries', 0),
            timeout=options.get('timeout')
        )
        self.current_branch.append(step)
        return self
    
    def auto_route(self, query: str, **options) -> 'Flow':
        """
        Add a step to automatically route a query to the best agent.
        
        Args:
            query: The query to route and send
            **options: Additional options for the step
            
        Returns:
            Self for method chaining
        """
        if not self.router:
            # Create a default router if none provided
            from ..client.router import AIAgentRouter
            self.router = AIAgentRouter(
                # Use the first agent's client for simplicity
                llm_client=next(iter(self.agent_network.agents.values())),
                agent_network=self.agent_network
            )
        
        step = AutoRouteStep(
            query=query,
            agent_network=self.agent_network,
            router=self.router,
            retries=options.get('retries', 0),
            timeout=options.get('timeout')
        )
        self.current_branch.append(step)
        return self
    
    def execute_function(self, func: Callable, *args, **kwargs) -> 'Flow':
        """
        Add a step to execute a custom function.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Self for method chaining
        """
        options = {}
        if 'retries' in kwargs:
            options['retries'] = kwargs.pop('retries')
        if 'timeout' in kwargs:
            options['timeout'] = kwargs.pop('timeout')
        
        step = FunctionStep(
            func=func,
            args=args,
            kwargs=kwargs,
            retries=options.get('retries', 0),
            timeout=options.get('timeout')
        )
        self.current_branch.append(step)
        return self
    
    def if_contains(self, text: str) -> 'Flow':
        """
        Start a conditional branch if the result contains text.
        
        Args:
            text: Text to check for
            
        Returns:
            Self for method chaining
        """
        # Define the condition function
        def condition_func(result):
            if result is None:
                return False
            return text.lower() in str(result).lower()
        
        # Create a new branch
        new_branch = []
        condition_branch = ConditionalBranch(condition_func, new_branch)
        
        # Save the current branch for when we end the condition
        self.branch_stack.append((self.current_branch, self.condition_steps))
        
        # Create a new condition step if needed
        if not self.condition_steps:
            condition_step = ConditionStep([condition_branch])
            self.current_branch.append(condition_step)
            self.condition_steps = [condition_branch]
        else:
            # Add to the existing condition step
            self.condition_steps.append(condition_branch)
        
        # Set the current branch to the new branch
        self.current_branch = new_branch
        
        return self
    
    def else_if_contains(self, text: str) -> 'Flow':
        """
        Add an else-if branch if the result contains text.
        
        Args:
            text: Text to check for
            
        Returns:
            Self for method chaining
        """
        # Make sure we're in a condition block
        if not self.branch_stack:
            raise ValueError("else_if_contains() called without matching if_contains()")
        
        # Define the condition function
        def condition_func(result):
            if result is None:
                return False
            return text.lower() in str(result).lower()
        
        # Create a new branch
        new_branch = []
        condition_branch = ConditionalBranch(condition_func, new_branch)
        
        # Add to the existing condition step
        self.condition_steps.append(condition_branch)
        
        # Set the current branch to the new branch
        self.current_branch = new_branch
        
        return self
    
    def else_branch(self) -> 'Flow':
        """
        Add an else branch for the current condition.
        
        Returns:
            Self for method chaining
        """
        # Make sure we're in a condition block
        if not self.branch_stack:
            raise ValueError("else_branch() called without matching if_contains()")
        
        # Get the current condition step
        parent_branch, _ = self.branch_stack[-1]
        condition_step = parent_branch[-1]
        
        # Create a new branch for the else case
        new_branch = []
        condition_step.else_steps = new_branch
        
        # Set the current branch to the new branch
        self.current_branch = new_branch
        
        return self
    
    def end_if(self) -> 'Flow':
        """
        End the current conditional block.
        
        Returns:
            Self for method chaining
        """
        # Make sure we're in a condition block
        if not self.branch_stack:
            raise ValueError("end_if() called without matching if_contains()")
        
        # Restore the previous branch
        self.current_branch, self.condition_steps = self.branch_stack.pop()
        
        return self
    
    def parallel(self) -> 'ParallelBuilder':
        """
        Start a parallel execution block.
        
        Returns:
            ParallelBuilder for building parallel steps
        """
        return ParallelBuilder(self)
    
    async def run(self, initial_context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute the workflow.
        
        Args:
            initial_context: Optional initial context data
            
        Returns:
            Result of the workflow
        """
        # Create workflow context
        context = WorkflowContext(initial_context)
        
        # Execute each step in sequence
        result = None
        for step in self.steps:
            try:
                step_result = await step.execute(context)
                context.add_result(step.id, step_result)
                result = step_result
            except Exception as e:
                logger.error(f"Error executing workflow step {step.id}: {e}")
                context.add_error(step.id, e)
                raise
        
        return result
    
    def run_sync(self, initial_context: Optional[Dict[str, Any]] = None) -> Any:
        """
        Execute the workflow synchronously.
        
        Args:
            initial_context: Optional initial context data
            
        Returns:
            Result of the workflow
        """
        # Create and run an event loop if necessary
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            # No event loop in this thread, create one
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # Run the workflow
        return loop.run_until_complete(self.run(initial_context))


class ParallelBuilder:
    """Builder for parallel execution steps."""
    
    def __init__(self, flow: Flow):
        """
        Initialize parallel builder.
        
        Args:
            flow: Parent flow
        """
        self.flow = flow
        self.branches = []
        self.current_branch = []
        self.branches.append(self.current_branch)
    
    def branch(self) -> 'ParallelBuilder':
        """
        Add a new parallel branch.
        
        Returns:
            Self for method chaining
        """
        self.current_branch = []
        self.branches.append(self.current_branch)
        return self
    
    def ask(self, agent_name: str, query: str, **options) -> 'ParallelBuilder':
        """
        Add a step to ask an agent a question.
        
        Args:
            agent_name: Name of the agent to query
            query: The query to send to the agent
            **options: Additional options for the step
            
        Returns:
            Self for method chaining
        """
        step = QueryStep(
            agent_name=agent_name,
            query=query,
            agent_network=self.flow.agent_network,
            retries=options.get('retries', 0),
            timeout=options.get('timeout')
        )
        self.current_branch.append(step)
        return self
    
    def auto_route(self, query: str, **options) -> 'ParallelBuilder':
        """
        Add a step to automatically route a query to the best agent.
        
        Args:
            query: The query to route and send
            **options: Additional options for the step
            
        Returns:
            Self for method chaining
        """
        if not self.flow.router:
            # Create a default router if none provided
            from ..client.router import AIAgentRouter
            self.flow.router = AIAgentRouter(
                # Use the first agent's client for simplicity
                llm_client=next(iter(self.flow.agent_network.agents.values())),
                agent_network=self.flow.agent_network
            )
        
        step = AutoRouteStep(
            query=query,
            agent_network=self.flow.agent_network,
            router=self.flow.router,
            retries=options.get('retries', 0),
            timeout=options.get('timeout')
        )
        self.current_branch.append(step)
        return self
    
    def execute_function(self, func: Callable, *args, **kwargs) -> 'ParallelBuilder':
        """
        Add a step to execute a custom function.
        
        Args:
            func: Function to execute
            *args: Positional arguments for the function
            **kwargs: Keyword arguments for the function
            
        Returns:
            Self for method chaining
        """
        options = {}
        if 'retries' in kwargs:
            options['retries'] = kwargs.pop('retries')
        if 'timeout' in kwargs:
            options['timeout'] = kwargs.pop('timeout')
        
        step = FunctionStep(
            func=func,
            args=args,
            kwargs=kwargs,
            retries=options.get('retries', 0),
            timeout=options.get('timeout')
        )
        self.current_branch.append(step)
        return self
    
    def end_parallel(self, max_concurrency: Optional[int] = None) -> Flow:
        """
        End the parallel block and return to the main flow.
        
        Args:
            max_concurrency: Maximum number of branches to execute concurrently
            
        Returns:
            Parent flow for method chaining
        """
        # Convert branches to steps
        steps = []
        for branch in self.branches:
            if not branch:  # Skip empty branches
                continue
                
            if len(branch) == 1:
                # Single step, add directly
                steps.append(branch[0])
            else:
                # Multiple steps, create a sequential wrapper
                # This is a simplification; we could create a proper sequence step class
                steps.extend(branch)
        
        # Create parallel step
        parallel_step = ParallelStep(steps, max_concurrency=max_concurrency)
        self.flow.current_branch.append(parallel_step)
        
        return self.flow