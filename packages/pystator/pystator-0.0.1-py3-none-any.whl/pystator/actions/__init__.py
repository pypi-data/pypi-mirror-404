"""Action system for PyStator FSM side effects.

Supports both sequential and parallel action execution with async support.
"""

from __future__ import annotations

from pystator.actions.registry import (
    ActionRegistry,
    ActionFunc,
    AsyncActionFunc,
    AnyActionFunc,
    ActionResult,
)
from pystator.actions.executor import (
    ActionExecutor,
    ExecutionResult,
    ExecutionMode,
    ACTION_PARAMS_KEY,
)
from pystator.actions.retry import RetryPolicy, RetryResult, RetryExecutor

__all__ = [
    # Registry
    "ActionRegistry",
    "ActionFunc",
    "AsyncActionFunc",
    "AnyActionFunc",
    "ActionResult",
    # Executor
    "ActionExecutor",
    "ExecutionResult",
    "ExecutionMode",
    "ACTION_PARAMS_KEY",
    # Retry
    "RetryPolicy",
    "RetryResult",
    "RetryExecutor",
]
