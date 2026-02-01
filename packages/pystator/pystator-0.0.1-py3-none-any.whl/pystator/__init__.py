"""PyStator - Configuration-Driven Finite State Machine Library.

PyStator is a pure, stateless FSM library that defines behavioral contracts
through YAML/JSON specifications. It computes state transitions without
holding internal state, making it ideal for distributed systems.

Key Features:
- Configuration-driven state machine definitions
- Pure computation (no side effects during processing)
- Hierarchical states (compound states with parent/child)
- Parallel states (orthogonal regions for concurrent behaviors)
- Async action execution with parallel, sequential, and phased modes
- Guards for conditional transitions
- Actions/hooks for state entry/exit and transitions
- Timeout/TTL support for automatic transitions
- Strict mode for contract enforcement

Example:
    >>> from pystator import StateMachine, GuardRegistry
    >>>
    >>> # Load FSM from YAML
    >>> machine = StateMachine.from_yaml("order_fsm.yaml")
    >>>
    >>> # Register guards
    >>> guards = GuardRegistry()
    >>> guards.register("is_full_fill", lambda ctx: ctx["fill_qty"] >= ctx["order_qty"])
    >>> machine.bind_guards(guards)
    >>>
    >>> # Process an event (pure computation)
    >>> result = machine.process("OPEN", "execution_report", {"fill_qty": 100, "order_qty": 100})
    >>>
    >>> # Handle result
    >>> if result.success:
    ...     print(f"Transition: {result.source_state} -> {result.target_state}")
    ...     print(f"Actions to execute: {result.all_actions}")
"""

from __future__ import annotations

try:
    from importlib.metadata import version

    __version__ = version("pystator")
except Exception:
    __version__ = "0.1.0"

# Core classes
from pystator.core.machine import StateMachine
from pystator.core.state import State, StateType, Timeout, Region
from pystator.core.transition import (
    Transition, 
    TransitionResult,
    GuardSpec,
    ActionSpec,
    parse_delay,
)
from pystator.core.event import Event
from pystator.core.parallel import ParallelStateConfig, ParallelStateManager

# Scheduler adapters
from pystator.scheduler import (
    SchedulerAdapter,
    ScheduledTask,
    TaskStatus,
    AsyncioScheduler,
)

# Builder
from pystator.builder import StateMachineBuilder

# Error classes
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

# Guard system
from pystator.guards.registry import (
    GuardRegistry,
    GuardFunc,
    AsyncGuardFunc,
    AnyGuardFunc,
    GuardResult,
)
from pystator.guards.evaluator import GuardEvaluator
from pystator.guards.builtins import (
    register_builtins,
    always_true,
    always_false,
    is_not_none,
    is_truthy,
    equals,
    not_equals,
    greater_than,
    less_than,
    greater_or_equal,
    less_or_equal,
    in_list,
    not_in_list,
    has_key,
    all_of,
    any_of,
    none_of,
    negate,
)

# Action system
from pystator.actions.registry import (
    ActionRegistry,
    ActionFunc,
    AsyncActionFunc,
    AnyActionFunc,
    ActionResult,
)
from pystator.actions.executor import ActionExecutor, ExecutionResult, ExecutionMode
from pystator.actions.retry import RetryPolicy, RetryResult, RetryExecutor

# Configuration
from pystator.config.loader import ConfigLoader, load_config
from pystator.config.validator import ConfigValidator, validate_config

# Timeout management
from pystator.timeout.manager import (
    TimeoutManager,
    TimeoutInfo,
    check_timeout,
    get_timeout_info,
)

# Visualization
from pystator.visualization import (
    to_mermaid,
    to_mermaid_flowchart,
    to_dot,
    get_statistics,
)

# Observability
from pystator.observability import (
    TransitionMetrics,
    TransitionHook,
    LoggingHook,
    MetricsCollector,
    TransitionObserver,
    with_timing,
)

# Idempotency
from pystator.idempotency import (
    IdempotencyBackend,
    IdempotencyRecord,
    IdempotencyResult,
    IdempotencyChecker,
    InMemoryIdempotencyBackend,
    NoOpIdempotencyBackend,
)

# Orchestration
from pystator.orchestration import Orchestrator
from pystator.core.state_store import (
    AsyncStateStore,
    InMemoryStateStore,
    StateStore,
)

# Utilities
from pystator.utils.serialization import (
    serialize_state,
    deserialize_state,
    serialize_transition_result,
    deserialize_transition_result,
)

__all__ = [
    # Version
    "__version__",
    # Core classes
    "StateMachine",
    "StateMachineBuilder",
    "State",
    "StateType",
    "Timeout",
    "Region",
    "Transition",
    "TransitionResult",
    "GuardSpec",
    "ActionSpec",
    "parse_delay",
    "Event",
    # Parallel states
    "ParallelStateConfig",
    "ParallelStateManager",
    # Scheduler
    "SchedulerAdapter",
    "ScheduledTask",
    "TaskStatus",
    "AsyncioScheduler",
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
    # Guards
    "GuardRegistry",
    "GuardFunc",
    "AsyncGuardFunc",
    "AnyGuardFunc",
    "GuardResult",
    "GuardEvaluator",
    "register_builtins",
    "always_true",
    "always_false",
    "is_not_none",
    "is_truthy",
    "equals",
    "not_equals",
    "greater_than",
    "less_than",
    "greater_or_equal",
    "less_or_equal",
    "in_list",
    "not_in_list",
    "has_key",
    "all_of",
    "any_of",
    "none_of",
    "negate",
    # Actions
    "ActionRegistry",
    "ActionFunc",
    "AsyncActionFunc",
    "AnyActionFunc",
    "ActionResult",
    "ActionExecutor",
    "ExecutionResult",
    "ExecutionMode",
    "RetryPolicy",
    "RetryResult",
    "RetryExecutor",
    # Configuration
    "ConfigLoader",
    "ConfigValidator",
    "load_config",
    "validate_config",
    # Timeout
    "TimeoutManager",
    "TimeoutInfo",
    "check_timeout",
    "get_timeout_info",
    # Visualization
    "to_mermaid",
    "to_mermaid_flowchart",
    "to_dot",
    "get_statistics",
    # Observability
    "TransitionMetrics",
    "TransitionHook",
    "LoggingHook",
    "MetricsCollector",
    "TransitionObserver",
    "with_timing",
    # Idempotency
    "IdempotencyBackend",
    "IdempotencyRecord",
    "IdempotencyResult",
    "IdempotencyChecker",
    "InMemoryIdempotencyBackend",
    "NoOpIdempotencyBackend",
    # Orchestration
    "Orchestrator",
    "StateStore",
    "AsyncStateStore",
    "InMemoryStateStore",
    # Utilities
    "serialize_state",
    "deserialize_state",
    "serialize_transition_result",
    "deserialize_transition_result",
]
