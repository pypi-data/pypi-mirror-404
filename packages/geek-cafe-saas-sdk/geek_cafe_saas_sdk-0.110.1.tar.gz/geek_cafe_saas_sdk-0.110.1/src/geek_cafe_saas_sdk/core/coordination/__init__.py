"""
Generic coordination patterns for distributed workflow steps.

This module provides abstractions for coordinating parallel work execution,
such as batch processing, child workflows, or any scenario where a step
dispatches multiple parallel tasks and needs to wait for completion.
"""

from .coordination_strategy import CoordinationStrategy, CoordinationResult
from .batch_coordination_strategy import BatchCoordinationStrategy
from .counter_coordination_strategy import CounterCoordinationStrategy

__all__ = [
    "CoordinationStrategy",
    "CoordinationResult",
    "BatchCoordinationStrategy",
    "CounterCoordinationStrategy",
]
