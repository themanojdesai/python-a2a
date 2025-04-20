"""
Workflow system for orchestrating agent interactions.

This module provides a fluent API for defining complex agent workflows
with conditional branching, parallel execution, and automatic agent routing.
"""

from .flow import (
    Flow,
    WorkflowContext,
    ParallelBuilder
)

from .steps import (
    WorkflowStep,
    QueryStep,
    AutoRouteStep,
    FunctionStep,
    ConditionalBranch,
    ConditionStep,
    ParallelStep,
    StepType,
)

__all__ = [
    'Flow',
    'WorkflowContext',
    'WorkflowStep',
    'QueryStep',
    'AutoRouteStep',
    'FunctionStep',
    'ConditionalBranch',
    'ConditionStep',
    'ParallelStep',
    'ParallelBuilder',
    'StepType',
]