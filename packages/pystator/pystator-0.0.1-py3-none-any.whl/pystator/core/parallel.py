"""Parallel state (orthogonal regions) support for PyStator FSM.

Provides state configuration tracking for parallel states with multiple
independent regions that execute concurrently.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pystator.core.state import State, Region


@dataclass(frozen=True, slots=True)
class ParallelStateConfig:
    """Configuration representing active states across all regions of a parallel state.

    When a parallel state is active, each region has exactly one active state.
    This class tracks that configuration and provides utilities for managing
    parallel state transitions.

    Attributes:
        parallel_state: Name of the parallel state.
        region_states: Mapping from region name to active state name within that region.

    Example:
        >>> config = ParallelStateConfig(
        ...     parallel_state="active",
        ...     region_states={
        ...         "trading": "scanning",
        ...         "risk_monitor": "normal",
        ...         "data_feed": "connected",
        ...     }
        ... )
        >>> config.get_region_state("trading")
        'scanning'
        >>> config.is_in_state("scanning")
        True
    """

    parallel_state: str
    region_states: dict[str, str] = field(default_factory=dict)

    def get_region_state(self, region_name: str) -> str | None:
        """Get the active state for a specific region."""
        return self.region_states.get(region_name)

    def is_in_state(self, state_name: str) -> bool:
        """Check if any region is in the given state."""
        return state_name in self.region_states.values()

    def get_all_active(self) -> list[str]:
        """Get all currently active states across all regions."""
        return list(self.region_states.values())

    def with_region_state(self, region_name: str, new_state: str) -> "ParallelStateConfig":
        """Create a new config with an updated region state."""
        new_region_states = dict(self.region_states)
        new_region_states[region_name] = new_state
        return ParallelStateConfig(
            parallel_state=self.parallel_state,
            region_states=new_region_states,
        )

    def contains(self, state_name: str) -> bool:
        """Check if this configuration contains the given state (parallel or region state)."""
        if state_name == self.parallel_state:
            return True
        return state_name in self.region_states.values()

    def to_string(self) -> str:
        """Convert to a string representation for storage/serialization.

        Format: parallel_state:region1=state1,region2=state2,...
        """
        if not self.region_states:
            return self.parallel_state
        region_parts = ",".join(
            f"{region}={state}"
            for region, state in sorted(self.region_states.items())
        )
        return f"{self.parallel_state}:{region_parts}"

    @classmethod
    def from_string(cls, value: str) -> "ParallelStateConfig":
        """Parse from string representation.

        Format: parallel_state:region1=state1,region2=state2,...
        """
        if ":" not in value:
            return cls(parallel_state=value, region_states={})
        parallel_state, region_part = value.split(":", 1)
        region_states = {}
        for pair in region_part.split(","):
            if "=" in pair:
                region, state = pair.split("=", 1)
                region_states[region.strip()] = state.strip()
        return cls(parallel_state=parallel_state, region_states=region_states)


class ParallelStateManager:
    """Manages parallel state configurations and transitions.

    Handles the logic for entering, exiting, and transitioning within
    parallel states. Coordinates with the main StateMachine for transition
    processing.

    Example:
        >>> manager = ParallelStateManager(states)
        >>> config = manager.enter_parallel_state("active")
        >>> new_config = manager.process_region_transition(config, "trading", "analyzing")
    """

    def __init__(self, states: dict[str, State]) -> None:
        """Initialize with state definitions.

        Args:
            states: Dictionary mapping state names to State objects.
        """
        self._states = states
        self._parallel_states = {
            name: state
            for name, state in states.items()
            if state.is_parallel
        }

    def is_parallel_state(self, state_name: str) -> bool:
        """Check if a state is a parallel state."""
        return state_name in self._parallel_states

    def get_parallel_state(self, state_name: str) -> State | None:
        """Get a parallel state by name."""
        return self._parallel_states.get(state_name)

    def enter_parallel_state(self, parallel_state_name: str) -> ParallelStateConfig:
        """Create initial configuration when entering a parallel state.

        Each region is initialized to its initial state.

        Args:
            parallel_state_name: Name of the parallel state being entered.

        Returns:
            ParallelStateConfig with all regions at their initial states.

        Raises:
            ValueError: If state is not a parallel state.
        """
        state = self._parallel_states.get(parallel_state_name)
        if state is None:
            raise ValueError(f"'{parallel_state_name}' is not a parallel state")

        region_states = {
            region.name: region.initial
            for region in state.regions
        }

        return ParallelStateConfig(
            parallel_state=parallel_state_name,
            region_states=region_states,
        )

    def exit_parallel_state(
        self, config: ParallelStateConfig
    ) -> list[str]:
        """Get exit actions when leaving a parallel state.

        Returns states to exit in bottom-up order (region states first,
        then parallel state).

        Args:
            config: Current parallel state configuration.

        Returns:
            List of state names to exit (for on_exit actions).
        """
        exit_order = []
        # Exit region states first
        for state_name in config.get_all_active():
            exit_order.append(state_name)
        # Then exit the parallel state itself
        exit_order.append(config.parallel_state)
        return exit_order

    def process_region_transition(
        self,
        config: ParallelStateConfig,
        region_name: str,
        new_state: str,
    ) -> ParallelStateConfig:
        """Process a transition within a single region.

        Args:
            config: Current parallel state configuration.
            region_name: Name of the region where transition occurs.
            new_state: New state within the region.

        Returns:
            Updated ParallelStateConfig.

        Raises:
            ValueError: If region doesn't exist or state is invalid.
        """
        state = self._parallel_states.get(config.parallel_state)
        if state is None:
            raise ValueError(f"'{config.parallel_state}' is not a parallel state")

        region = state.get_region(region_name)
        if region is None:
            raise ValueError(f"Region '{region_name}' not found in '{config.parallel_state}'")

        if region.states and new_state not in region.states:
            raise ValueError(
                f"State '{new_state}' not valid for region '{region_name}'"
            )

        return config.with_region_state(region_name, new_state)

    def find_region_for_state(
        self,
        parallel_state_name: str,
        state_name: str,
    ) -> str | None:
        """Find which region contains a given state.

        Args:
            parallel_state_name: Name of the parallel state.
            state_name: State name to find.

        Returns:
            Region name containing the state, or None if not found.
        """
        state = self._parallel_states.get(parallel_state_name)
        if state is None:
            return None

        for region in state.regions:
            if region.contains(state_name):
                return region.name

        return None

    def get_region_states(
        self,
        parallel_state_name: str,
        region_name: str,
    ) -> tuple[str, ...]:
        """Get all valid states for a region.

        Args:
            parallel_state_name: Name of the parallel state.
            region_name: Name of the region.

        Returns:
            Tuple of state names in the region.
        """
        state = self._parallel_states.get(parallel_state_name)
        if state is None:
            return ()

        region = state.get_region(region_name)
        if region is None:
            return ()

        return region.states

    def validate_config(self, config: ParallelStateConfig) -> list[str]:
        """Validate a parallel state configuration.

        Args:
            config: Configuration to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        errors: list[str] = []

        state = self._parallel_states.get(config.parallel_state)
        if state is None:
            errors.append(f"'{config.parallel_state}' is not a parallel state")
            return errors

        expected_regions = {r.name for r in state.regions}
        actual_regions = set(config.region_states.keys())

        missing = expected_regions - actual_regions
        if missing:
            errors.append(f"Missing regions: {missing}")

        extra = actual_regions - expected_regions
        if extra:
            errors.append(f"Unknown regions: {extra}")

        for region in state.regions:
            region_state = config.region_states.get(region.name)
            if region_state and region.states and region_state not in region.states:
                errors.append(
                    f"Invalid state '{region_state}' for region '{region.name}'"
                )

        return errors
