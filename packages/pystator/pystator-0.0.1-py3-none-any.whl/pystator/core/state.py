"""State definitions for PyStator FSM.

Supports hierarchical states (compound states with parent/child) and
parallel states (orthogonal regions) for statechart-style modeling.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from pystator.core.invoke import InvokeSpec
from pystator.core.transition import ActionSpec

_ALLOWED_NAME_CHARS = set(
    "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_."
)


def _validate_name(name: str, kind: str = "name") -> None:
    """Validate identifier: non-empty, starts with letter, only alphanumeric/underscore/dot."""
    if not name:
        raise ValueError(f"{kind.capitalize()} cannot be empty")
    if not (name[0].isalpha() and all(c in _ALLOWED_NAME_CHARS for c in name)):
        raise ValueError(
            f"{kind.capitalize()} must start with a letter and contain only "
            f"letters, digits, underscores, and dots: {name}"
        )


class StateType(str, Enum):
    """Classification of state behavior in the FSM."""

    INITIAL = "initial"
    """The starting state of the machine. Exactly one required."""

    STABLE = "stable"
    """A normal operating state that can transition to other states."""

    TERMINAL = "terminal"
    """An end state. No outbound transitions allowed."""

    ERROR = "error"
    """An error/fallback state for handling failures."""

    PARALLEL = "parallel"
    """A parallel (orthogonal) state containing independent regions."""


@dataclass(frozen=True, slots=True)
class Timeout:
    """Timeout configuration for automatic state transitions.

    When a state has a timeout configured, if the entity remains in that state
    for longer than `seconds`, an automatic transition to `destination` should
    be triggered by the external timeout manager.

    Attributes:
        seconds: Duration in seconds before timeout triggers.
        destination: Target state to transition to on timeout.
    """

    seconds: float
    destination: str

    def __post_init__(self) -> None:
        if self.seconds <= 0:
            raise ValueError("Timeout seconds must be positive")
        if not self.destination:
            raise ValueError("Timeout destination cannot be empty")


@dataclass(frozen=True, slots=True)
class Region:
    """A region within a parallel (orthogonal) state.

    Regions are independent sub-machines within a parallel state. Each region
    has its own initial state and can transition independently of other regions.
    All regions within a parallel state are active simultaneously.

    Attributes:
        name: Unique identifier for this region.
        initial: Initial state name within this region.
        states: State names that belong to this region.
        description: Human-readable description of this region.

    Example:
        >>> region = Region(
        ...     name="trading",
        ...     initial="scanning",
        ...     states=("scanning", "analyzing", "executing", "managing"),
        ...     description="Main trading workflow region",
        ... )
    """

    name: str
    initial: str
    states: tuple[str, ...] = ()
    description: str = ""

    def __post_init__(self) -> None:
        _validate_name(self.name, "region name")
        if not self.initial:
            raise ValueError("Region must have an initial state")
        if self.states and self.initial not in self.states:
            raise ValueError(
                f"Region initial state '{self.initial}' must be in states list"
            )

    def contains(self, state_name: str) -> bool:
        """Check if this region contains the given state."""
        return state_name in self.states


@dataclass(frozen=True, slots=True)
class State:
    """Immutable state definition in the FSM.

    States are the nodes in the state machine graph. Each state has a unique
    name, a type that defines its behavior, and optional hooks for entry/exit
    actions and timeouts.

    Supports three types of composite states:
    - Compound states: Single child active (via initial_child)
    - Parallel states: Multiple regions active simultaneously (via regions)
    - Leaf states: No children (standard states)

    Attributes:
        name: Unique identifier for this state (may contain dots for hierarchy).
        type: Classification of state behavior (initial, stable, terminal, error, parallel).
        description: Human-readable description of what this state represents.
        parent: Optional parent state name for hierarchical (compound) states.
        initial_child: Optional default child state when entering this compound state.
        regions: Tuple of Region objects for parallel states (orthogonal regions).
        on_enter: Action specs (name + optional params) to execute when entering this state.
        on_exit: Action specs (name + optional params) to execute when exiting this state.
        invoke: Optional list of service invocations (id, src, on_done); adapter starts/stops them.
        timeout: Optional timeout configuration for automatic transitions.
        metadata: Additional user-defined metadata for the state.

    Example (simple state):
        >>> state = State(
        ...     name="PENDING_NEW",
        ...     type=StateType.INITIAL,
        ...     description="Order waiting for exchange acknowledgment",
        ...     on_enter=(ActionSpec("log_submission"),),
        ...     timeout=Timeout(seconds=5.0, destination="TIMED_OUT"),
        ... )

    Example (parallel state):
        >>> parallel_state = State(
        ...     name="active",
        ...     type=StateType.PARALLEL,
        ...     regions=(
        ...         Region("trading", "scanning", ("scanning", "analyzing")),
        ...         Region("risk_monitor", "normal", ("normal", "elevated")),
        ...     ),
        ... )
    """

    name: str
    type: StateType = StateType.STABLE
    description: str = ""
    parent: str | None = None
    initial_child: str | None = None
    regions: tuple[Region, ...] = ()
    on_enter: tuple[ActionSpec, ...] = ()
    on_exit: tuple[ActionSpec, ...] = ()
    invoke: tuple[InvokeSpec, ...] = ()
    timeout: Timeout | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        _validate_name(self.name, "state name")
        # Validate parallel state has regions
        if self.type == StateType.PARALLEL and not self.regions:
            raise ValueError(
                f"Parallel state '{self.name}' must have at least one region"
            )
        # Validate non-parallel states don't have regions
        if self.type != StateType.PARALLEL and self.regions:
            raise ValueError(
                f"Non-parallel state '{self.name}' cannot have regions"
            )
        # Validate unique region names
        if self.regions:
            region_names = [r.name for r in self.regions]
            if len(region_names) != len(set(region_names)):
                raise ValueError(
                    f"Parallel state '{self.name}' has duplicate region names"
                )

    @property
    def is_initial(self) -> bool:
        """Check if this is the initial state."""
        return self.type == StateType.INITIAL

    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self.type == StateType.TERMINAL

    @property
    def is_error(self) -> bool:
        """Check if this is an error state."""
        return self.type == StateType.ERROR

    @property
    def is_parallel(self) -> bool:
        """Check if this is a parallel (orthogonal) state."""
        return self.type == StateType.PARALLEL

    @property
    def has_timeout(self) -> bool:
        """Check if this state has a timeout configured."""
        return self.timeout is not None

    @property
    def is_compound(self) -> bool:
        """Check if this state is compound (has an initial child)."""
        return self.initial_child is not None

    @property
    def is_leaf(self) -> bool:
        """Check if this is a leaf state (no children or regions)."""
        return not self.is_compound and not self.is_parallel

    @property
    def region_names(self) -> tuple[str, ...]:
        """Get names of all regions (for parallel states)."""
        return tuple(r.name for r in self.regions)

    def get_region(self, name: str) -> Region | None:
        """Get a region by name."""
        for region in self.regions:
            if region.name == name:
                return region
        return None

    def with_metadata(self, **kwargs: Any) -> "State":
        """Create a new State with additional metadata."""
        new_metadata = {**self.metadata, **kwargs}
        return State(
            name=self.name,
            type=self.type,
            description=self.description,
            parent=self.parent,
            initial_child=self.initial_child,
            regions=self.regions,
            on_enter=self.on_enter,
            on_exit=self.on_exit,
            timeout=self.timeout,
            metadata=new_metadata,
        )
