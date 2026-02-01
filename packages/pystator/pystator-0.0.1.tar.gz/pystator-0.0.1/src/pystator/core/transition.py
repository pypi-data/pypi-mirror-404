"""Transition definitions for PyStator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pystator.core.errors import FSMError


@dataclass(frozen=True, slots=True)
class GuardSpec:
    """Guard specification - either a named function or inline expression.
    
    Attributes:
        name: Guard function name (if using named guard).
        expr: Inline boolean expression (if using expression guard).
    """
    name: str | None = None
    expr: str | None = None
    
    def __post_init__(self) -> None:
        if self.name is None and self.expr is None:
            raise ValueError("GuardSpec must have either 'name' or 'expr'")
        if self.name is not None and self.expr is not None:
            raise ValueError("GuardSpec cannot have both 'name' and 'expr'")
    
    @property
    def is_expression(self) -> bool:
        """Check if this is an inline expression guard."""
        return self.expr is not None
    
    @classmethod
    def from_config(cls, config: str | dict[str, Any]) -> "GuardSpec":
        """Create from config (string name or dict with expr)."""
        if isinstance(config, str):
            return cls(name=config)
        if isinstance(config, dict) and "expr" in config:
            return cls(expr=config["expr"])
        raise ValueError(f"Invalid guard config: {config}")


@dataclass(frozen=True, slots=True)
class ActionSpec:
    """Action specification - either a named function or parameterized action.
    
    Attributes:
        name: Action function name.
        params: Optional parameters to pass to the action.
    """
    name: str
    params: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        if not self.name:
            raise ValueError("ActionSpec must have a 'name'")
    
    @property
    def has_params(self) -> bool:
        """Check if this action has parameters."""
        return bool(self.params)
    
    @classmethod
    def from_config(cls, config: str | dict[str, Any]) -> "ActionSpec":
        """Create from config (string name or dict with name+params)."""
        if isinstance(config, str):
            return cls(name=config)
        if isinstance(config, dict) and "name" in config:
            return cls(name=config["name"], params=config.get("params", {}))
        raise ValueError(f"Invalid action config: {config}")


def parse_delay(value: int | str) -> int:
    """Parse delay value to milliseconds.
    
    Args:
        value: Integer (milliseconds) or string with unit (e.g., "5s", "10m", "1h").
    
    Returns:
        Delay in milliseconds.
    """
    if isinstance(value, int):
        return value
    
    if isinstance(value, str):
        value = value.strip()
        if value.endswith("h"):
            return int(value[:-1]) * 3600 * 1000
        elif value.endswith("m"):
            return int(value[:-1]) * 60 * 1000
        elif value.endswith("s"):
            return int(value[:-1]) * 1000
        else:
            return int(value)
    
    raise ValueError(f"Invalid delay value: {value}")


@dataclass(frozen=True, slots=True)
class Transition:
    """Immutable transition definition between states.

    Transitions define the valid paths through the state machine. Each
    transition is triggered by an event and can have guards (conditions)
    that must be satisfied and actions to execute on completion.

    For parallel states, transitions can be scoped to a specific region.
    For delayed transitions, use the `after` field to specify a delay.

    Attributes:
        trigger: Event name that triggers this transition.
        source: Set of valid source state names for this transition.
        dest: Target state name after transition completes.
        region: Optional region name for transitions within parallel states.
        guards: Guard specifications (named functions or inline expressions).
        actions: Action specifications (named functions or parameterized).
        after: Delay in milliseconds before transition fires (for scheduling).
        description: Human-readable description of this transition.
        metadata: Additional user-defined metadata.

    Example (standard transition):
        >>> transition = Transition(
        ...     trigger="execution_report",
        ...     source=frozenset({"OPEN", "PARTIALLY_FILLED"}),
        ...     dest="FILLED",
        ...     guards=(GuardSpec(name="is_full_fill"),),
        ...     actions=(ActionSpec(name="update_positions"),),
        ... )

    Example (delayed transition):
        >>> delayed = Transition(
        ...     trigger="timeout",
        ...     source=frozenset({"waiting"}),
        ...     dest="retry",
        ...     after=5000,  # 5 seconds
        ... )

    Example (inline guard expression):
        >>> expr_transition = Transition(
        ...     trigger="fill",
        ...     source=frozenset({"open"}),
        ...     dest="filled",
        ...     guards=(GuardSpec(expr="fill_qty >= order_qty"),),
        ... )
    """

    trigger: str
    source: frozenset[str]
    dest: str
    region: str | None = None
    guards: tuple[GuardSpec, ...] = ()
    actions: tuple[ActionSpec, ...] = ()
    after: int | None = None  # Delay in milliseconds
    description: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trigger:
            raise ValueError("Transition trigger cannot be empty")
        if not self.source:
            raise ValueError("Transition must have at least one source state")
        if not self.dest:
            raise ValueError("Transition destination cannot be empty")
        if self.after is not None and self.after < 0:
            raise ValueError("Transition delay must be non-negative")

    @property
    def is_region_transition(self) -> bool:
        """Check if this is a region-scoped transition (for parallel states)."""
        return self.region is not None
    
    @property
    def is_delayed(self) -> bool:
        """Check if this is a delayed transition."""
        return self.after is not None and self.after > 0
    
    @property
    def guard_names(self) -> tuple[str, ...]:
        """Get named guard function names (for backward compatibility)."""
        return tuple(g.name for g in self.guards if g.name is not None)
    
    @property
    def action_names(self) -> tuple[str, ...]:
        """Get action function names."""
        return tuple(a.name for a in self.actions)

    @classmethod
    def from_single_source(
        cls,
        trigger: str,
        source: str,
        dest: str,
        region: str | None = None,
        guards: tuple[GuardSpec, ...] = (),
        actions: tuple[ActionSpec, ...] = (),
        after: int | None = None,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "Transition":
        """Create a transition with a single source state."""
        return cls(
            trigger=trigger,
            source=frozenset({source}),
            dest=dest,
            region=region,
            guards=guards,
            actions=actions,
            after=after,
            description=description,
            metadata=metadata or {},
        )

    def matches_source(self, state: str) -> bool:
        """Check if the given state is a valid source for this transition."""
        return state in self.source

    def has_guards(self) -> bool:
        """Check if this transition has guard conditions."""
        return len(self.guards) > 0
    
    def has_expression_guards(self) -> bool:
        """Check if this transition has any inline expression guards."""
        return any(g.is_expression for g in self.guards)


@dataclass(frozen=True, slots=True)
class TransitionResult:
    """Immutable result of a transition computation.

    This is the output of the FSM engine's process() method. It contains
    all information needed to:
    1. Persist the state change (if successful)
    2. Execute side effects (actions)
    3. Handle errors (if unsuccessful)

    The FSM itself does NOT execute actions or persist state - it only
    computes what SHOULD happen. The caller is responsible for:
    - Persisting the state change atomically
    - Executing actions AFTER successful persistence

    Attributes:
        success: Whether the transition was successful.
        source_state: The state before the transition attempt.
        target_state: The new state (None if transition failed).
        trigger: The event that triggered this transition.
        actions_to_execute: Transition action specs to run after persistence.
        on_exit_actions: Exit action specs from the source state.
        on_enter_actions: Entry action specs for the target state.
        error: Error details if transition failed.
        metadata: Additional context (e.g., guard results, timing).

    Example:
        >>> result = machine.process("OPEN", "execution_report", context)
        >>> if result.success:
        ...     db.update_state(order_id, result.target_state)
        ...     for action_spec in result.all_action_specs:
        ...         action_registry.execute_action_spec(action_spec, context)
    """

    success: bool
    source_state: str
    target_state: str | None
    trigger: str
    actions_to_execute: tuple[ActionSpec, ...] = ()
    on_exit_actions: tuple[ActionSpec, ...] = ()
    on_enter_actions: tuple[ActionSpec, ...] = ()
    error: "FSMError | None" = None
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def all_action_specs(self) -> tuple[ActionSpec, ...]:
        """Get all action specs in execution order: exit -> transition -> enter."""
        return self.on_exit_actions + self.actions_to_execute + self.on_enter_actions

    @property
    def all_actions(self) -> tuple[str, ...]:
        """Action names in execution order (for backward compatibility / logging)."""
        return tuple(a.name for a in self.all_action_specs)

    @property
    def is_self_transition(self) -> bool:
        """Check if this is a self-transition (source == target)."""
        return self.success and self.source_state == self.target_state

    @property
    def state_changed(self) -> bool:
        """Check if the state actually changed."""
        return self.success and self.source_state != self.target_state

    @classmethod
    def success_result(
        cls,
        source_state: str,
        target_state: str,
        trigger: str,
        actions: tuple[ActionSpec, ...] = (),
        on_exit: tuple[ActionSpec, ...] = (),
        on_enter: tuple[ActionSpec, ...] = (),
        metadata: dict[str, Any] | None = None,
    ) -> "TransitionResult":
        """Create a successful transition result."""
        return cls(
            success=True,
            source_state=source_state,
            target_state=target_state,
            trigger=trigger,
            actions_to_execute=actions,
            on_exit_actions=on_exit,
            on_enter_actions=on_enter,
            error=None,
            metadata=metadata or {},
        )

    @classmethod
    def failure_result(
        cls,
        source_state: str,
        trigger: str,
        error: "FSMError",
        metadata: dict[str, Any] | None = None,
    ) -> "TransitionResult":
        """Create a failed transition result."""
        return cls(
            success=False,
            source_state=source_state,
            target_state=None,
            trigger=trigger,
            actions_to_execute=(),
            on_exit_actions=(),
            on_enter_actions=(),
            error=error,
            metadata=metadata or {},
        )

    @classmethod
    def no_op_result(
        cls,
        current_state: str,
        trigger: str,
        metadata: dict[str, Any] | None = None,
    ) -> "TransitionResult":
        """Create a no-op result (stay in same state, no actions). Used in non-strict mode."""
        return cls(
            success=True,
            source_state=current_state,
            target_state=current_state,
            trigger=trigger,
            actions_to_execute=(),
            on_exit_actions=(),
            on_enter_actions=(),
            error=None,
            metadata=dict(metadata or {}, no_op=True, reason="no_matching_transition"),
        )
