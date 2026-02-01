"""Core FSM components for PyStator.

Supports hierarchical states (compound states) and parallel states
(orthogonal regions) for statechart-style modeling.
"""

from __future__ import annotations

from pystator.core.state import State, StateType, Timeout, Region
from pystator.core.state_hierarchy import StateHierarchy
from pystator.core.parallel import ParallelStateConfig, ParallelStateManager
from pystator.core.state_store import (
    AsyncStateStore,
    InMemoryStateStore,
    StateStore,
)
from pystator.core.transition import (
    Transition,
    TransitionResult,
    GuardSpec,
    ActionSpec,
    parse_delay,
)
from pystator.core.event import Event
from pystator.core.invoke import InvokeSpec
from pystator.core.errors import (
    FSMError,
    ConfigurationError,
    InvalidTransitionError,
    GuardRejectedError,
    UndefinedStateError,
    UndefinedTriggerError,
    TimeoutExpiredError,
    GuardNotFoundError,
    ActionNotFoundError,
    TerminalStateError,
    ErrorPolicy,
)

__all__ = [
    # State
    "State",
    "StateType",
    "Timeout",
    "Region",
    # State hierarchy
    "StateHierarchy",
    # Parallel states
    "ParallelStateConfig",
    "ParallelStateManager",
    # State store
    "StateStore",
    "AsyncStateStore",
    "InMemoryStateStore",
    # Transition
    "Transition",
    "TransitionResult",
    "GuardSpec",
    "ActionSpec",
    "parse_delay",
    # Event
    "Event",
    # Invoke
    "InvokeSpec",
    # Errors
    "FSMError",
    "ConfigurationError",
    "InvalidTransitionError",
    "GuardRejectedError",
    "UndefinedStateError",
    "UndefinedTriggerError",
    "TimeoutExpiredError",
    "GuardNotFoundError",
    "ActionNotFoundError",
    "TerminalStateError",
    "ErrorPolicy",
]
