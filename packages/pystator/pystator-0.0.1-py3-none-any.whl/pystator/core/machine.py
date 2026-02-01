"""State Machine engine for PyStator FSM.

Supports hierarchical states (compound states with parent/child) and
parallel states (orthogonal regions) for statechart-style modeling.
"""

from __future__ import annotations

import itertools
from pathlib import Path
from typing import Any, Literal

from pystator.config.loader import ConfigLoader
from pystator.core.errors import (
    ConfigurationError,
    ErrorPolicy,
    InvalidTransitionError,
    TerminalStateError,
    UndefinedStateError,
    UndefinedTriggerError,
)
from pystator.core.event import Event
from pystator.core.state import State, StateType
from pystator.core.state_hierarchy import StateHierarchy
from pystator.core.parallel import ParallelStateConfig, ParallelStateManager
from pystator.core.transition import ActionSpec, Transition, TransitionResult
from pystator.guards.evaluator import GuardEvaluator
from pystator.guards.registry import GuardRegistry


def _normalize_event(event: str | Event) -> tuple[str, Event]:
    """Normalize event to (trigger, Event)."""
    if isinstance(event, str):
        return event, Event(trigger=event)
    return event.trigger, event


def _build_context(context: dict[str, Any] | None, event_obj: Event) -> dict[str, Any]:
    """Merge event payload and _event into context."""
    ctx = context or {}
    return {**ctx, **event_obj.payload, "_event": event_obj}


class StateMachine:
    """Pure, stateless finite state machine engine with parallel state support.

    The StateMachine is the core of PyStator. It takes a state and event
    as input and computes the resulting state and actions - without
    holding any internal state or executing side effects.

    This design enables:
    - Horizontal scaling (no shared state)
    - Testability (pure functions)
    - Determinism (same input -> same output)
    - Separation of concerns (compute vs persist vs execute)

    The machine is configured via YAML/JSON definitions that specify:
    - States (with types, timeouts, hooks)
    - Parallel states (orthogonal regions)
    - Transitions (with guards and actions)
    - Error policies

    State Types:
    - Simple states: Standard leaf states
    - Compound states: Hierarchical states with initial_child
    - Parallel states: Orthogonal regions with independent sub-machines

    Example (simple usage):
        >>> machine = StateMachine.from_yaml("order_fsm.yaml")
        >>> machine.bind_guards(guard_registry)
        >>>
        >>> # Compute transition (pure, no side effects)
        >>> result = machine.process("OPEN", "execution_report", context)
        >>>
        >>> if result.success:
        ...     db.update_state(order_id, result.target_state)  # Persist
        ...     for action in result.all_actions:               # Execute
        ...         action_registry.execute(action, context)

    Example (parallel states):
        >>> # Parallel state configuration tracks multiple active regions
        >>> config = machine.enter_parallel_state("active")
        >>> # config.region_states = {"trading": "scanning", "risk": "normal"}
        >>>
        >>> # Process region-scoped transition
        >>> result = machine.process_parallel(config, "signal_detected", context)
    """

    def __init__(
        self,
        states: dict[str, State],
        transitions: list[Transition],
        meta: dict[str, Any] | None = None,
        error_policy: ErrorPolicy | None = None,
    ) -> None:
        """Initialize the state machine.

        Args:
            states: Dictionary mapping state names to State objects.
            transitions: List of Transition objects.
            meta: Optional metadata (version, machine_name, etc.).
            error_policy: Optional error handling configuration.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        self._states = states
        self._transitions = transitions
        self._meta = meta or {}
        self._error_policy = error_policy or ErrorPolicy()
        self._event_normalizer: Literal["lower", "upper"] | None = self._meta.get("event_normalizer")

        # Build transition lookup index (source -> trigger -> transitions)
        self._transition_index: dict[tuple[str, str], list[Transition]] = {}
        self._build_transition_index()

        # Build state hierarchy (validates one root initial, no cycles, refs)
        self._hierarchy = StateHierarchy(self._states)
        root_initial = next(
            name for name in self._hierarchy.roots
            if self._states[name].is_initial
        )
        self._initial_leaf: str = self._hierarchy.resolve_initial_leaf(root_initial)

        # Parallel state manager
        self._parallel_manager = ParallelStateManager(self._states)

        # Guard evaluator (initialized when guards are bound)
        self._guard_registry: GuardRegistry | None = None
        self._guard_evaluator: GuardEvaluator | None = None

        # Validate transition refs and timeouts
        self._validate()

    def _normalize_trigger(self, trigger: str) -> str:
        """Normalize trigger for matching when meta.event_normalizer is set."""
        if self._event_normalizer == "lower":
            return trigger.lower()
        if self._event_normalizer == "upper":
            return trigger.upper()
        return trigger

    def _build_transition_index(self) -> None:
        """Build index for fast transition lookup."""
        for transition in self._transitions:
            for source in transition.source:
                key = (source, transition.trigger)
                if key not in self._transition_index:
                    self._transition_index[key] = []
                self._transition_index[key].append(transition)

    def _validate(self) -> None:
        """Validate the state machine configuration (transition refs, timeouts). Hierarchy validated by StateHierarchy."""
        # Validate transition references
        for trans in self._transitions:
            for source in trans.source:
                if source not in self._states:
                    raise ConfigurationError(
                        f"Transition references undefined source state: {source}",
                        context={"transition": trans.trigger, "source": source},
                    )
            if trans.dest not in self._states:
                raise ConfigurationError(
                    f"Transition references undefined destination state: {trans.dest}",
                    context={"transition": trans.trigger, "dest": trans.dest},
                )

        # Validate timeout destinations
        for state in self._states.values():
            if state.timeout and state.timeout.destination not in self._states:
                raise ConfigurationError(
                    f"State timeout references undefined destination: {state.timeout.destination}",
                    context={"state": state.name},
                )

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        validate: bool = True,
        variables: dict[str, str] | None = None,
    ) -> "StateMachine":
        """Create a StateMachine from a YAML configuration file.

        Args:
            path: Path to the YAML configuration file.
            validate: If True, validate configuration against schema.
            variables: Optional variables for substitution.

        Returns:
            Configured StateMachine instance.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        loader = ConfigLoader(validate=validate, variables=variables)
        config = loader.load(path)
        return cls.from_dict(config)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "StateMachine":
        """Create a StateMachine from a configuration dictionary.

        Args:
            config: Configuration dictionary matching the schema.

        Returns:
            Configured StateMachine instance.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        loader = ConfigLoader(validate=False)
        states, transitions, meta = loader.parse(config)

        # Parse error policy
        error_policy = None
        if "error_policy" in config:
            ep = config["error_policy"]
            error_policy = ErrorPolicy(
                default_fallback=ep.get("default_fallback"),
                retry_attempts=ep.get("retry_attempts", 0),
                strict_mode=meta.get("strict_mode", True),
            )
        else:
            error_policy = ErrorPolicy(strict_mode=meta.get("strict_mode", True))

        return cls(states, transitions, meta, error_policy)

    def bind_guards(self, registry: GuardRegistry) -> "StateMachine":
        """Bind a guard registry to the machine.

        Guards are evaluated during transition processing to determine
        if transitions should be allowed.

        Args:
            registry: Guard registry containing guard functions.

        Returns:
            Self for method chaining.
        """
        self._guard_registry = registry
        self._guard_evaluator = GuardEvaluator(
            registry,
            strict=self._error_policy.strict_mode,
        )
        return self

    def process(
        self,
        current_state: str,
        event: str | Event,
        context: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """Process an event and compute the resulting transition.

        This is the main entry point for the FSM. It takes the current
        state and event, evaluates guards, and returns the transition
        result - WITHOUT executing any side effects.

        The caller is responsible for:
        1. Persisting the state change (if successful)
        2. Executing actions (after persistence)

        Args:
            current_state: The current state name.
            event: Event trigger (string) or Event object.
            context: Optional context dictionary for guards.

        Returns:
            TransitionResult with the computed transition.

        Raises:
            UndefinedStateError: If current_state is not defined.
        """
        # Normalize event
        if isinstance(event, str):
            trigger = event
            event_obj = Event(trigger=trigger)
        else:
            trigger = event.trigger
            event_obj = event
        trigger = self._normalize_trigger(trigger)

        # Merge event payload into context
        ctx = context or {}
        ctx = {**ctx, **event_obj.payload, "_event": event_obj}

        # Validate current state exists
        if current_state not in self._states:
            raise UndefinedStateError(
                f"State '{current_state}' is not defined",
                state_name=current_state,
            )

        state = self._states[current_state]

        # Check if terminal state
        if state.is_terminal:
            return TransitionResult.failure_result(
                source_state=current_state,
                trigger=trigger,
                error=TerminalStateError(current_state, trigger),
                metadata={"reason": "terminal_state"},
            )

        # Find matching transitions
        candidates = self._find_transitions(current_state, trigger)

        # Handle no matching transitions
        if not candidates:
            return self._handle_no_transition(current_state, trigger)

        # Evaluate guards and find first valid transition
        for transition in candidates:
            if self._evaluate_guards(transition, current_state, ctx):
                return self._create_success_result(
                    state, transition, trigger, ctx
                )

        # All guards failed
        return self._handle_guard_failure(current_state, trigger, candidates)

    async def async_process(
        self,
        current_state: str,
        event: str | Event,
        context: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """Process an event asynchronously and compute the resulting transition.

        This is the async entry point for the FSM. It works like `process()` but
        supports async guards that can call external services (databases, APIs).

        Use this when:
        - Guards need to call external APIs (e.g., check buying power from broker)
        - Guards need to query databases
        - You want to support both sync and async guards

        The caller is responsible for:
        1. Persisting the state change (if successful)
        2. Executing actions (after persistence) - use ActionExecutor.async_execute()

        Args:
            current_state: The current state name.
            event: Event trigger (string) or Event object.
            context: Optional context dictionary for guards.

        Returns:
            TransitionResult with the computed transition.

        Raises:
            UndefinedStateError: If current_state is not defined.
        """
        trigger, event_obj = _normalize_event(event)
        trigger = self._normalize_trigger(trigger)
        ctx = _build_context(context, event_obj)

        if current_state not in self._states:
            raise UndefinedStateError(
                f"State '{current_state}' is not defined",
                state_name=current_state,
            )

        state = self._states[current_state]
        if state.is_terminal:
            return TransitionResult.failure_result(
                source_state=current_state,
                trigger=trigger,
                error=TerminalStateError(current_state, trigger),
                metadata={"reason": "terminal_state"},
            )

        candidates = self._find_transitions(current_state, trigger)
        if not candidates:
            return self._handle_no_transition(current_state, trigger)

        for transition in candidates:
            if await self._async_evaluate_guards(transition, current_state, ctx):
                return self._create_success_result(
                    state, transition, trigger, ctx
                )

        return self._handle_guard_failure(current_state, trigger, candidates)

    async def _async_evaluate_guards(
        self,
        transition: Transition,
        current_state: str,
        context: dict[str, Any],
    ) -> bool:
        """Evaluate guards for a transition asynchronously."""
        if not transition.guards:
            return True

        if self._guard_evaluator is None:
            # No guard registry bound - guards pass by default in non-strict mode
            if self._error_policy.strict_mode:
                raise ConfigurationError(
                    "Guards referenced but no guard registry bound. "
                    "Call bind_guards() before processing events.",
                    context={"guards": transition.guards},
                )
            return True

        # Use async evaluation from the registry
        result = await self._guard_registry.async_evaluate_all(  # type: ignore[union-attr]
            transition.guards, context
        )
        return result.passed

    def _find_transitions(
        self, current_state: str, trigger: str
    ) -> list[Transition]:
        """Find all transitions matching current (leaf) state and trigger. Uses hierarchy: transition source matches if it is self or any ancestor. Candidates ordered by specificity (leaf match first). Trigger and config triggers are normalized when meta.event_normalizer is set."""
        normalized_trigger = self._normalize_trigger(trigger)
        ancestors = self._hierarchy.ancestors(current_state)
        ancestors_set = set(ancestors)
        candidates: list[Transition] = []
        for trans in self._transitions:
            if self._normalize_trigger(trans.trigger) != normalized_trigger:
                continue
            if not (trans.source & ancestors_set):
                continue
            candidates.append(trans)
        # Sort by specificity: transition whose source is earliest in ancestors (closest to leaf) first
        def specificity(trans: Transition) -> int:
            indices = [ancestors.index(s) for s in trans.source if s in ancestors_set]
            return min(indices) if indices else len(ancestors)
        candidates.sort(key=specificity)
        return candidates

    def _evaluate_guards(
        self,
        transition: Transition,
        current_state: str,
        context: dict[str, Any],
    ) -> bool:
        """Evaluate guards for a transition."""
        if not transition.guards:
            return True

        if self._guard_evaluator is None:
            # No guard registry bound - guards pass by default in non-strict mode
            if self._error_policy.strict_mode:
                raise ConfigurationError(
                    "Guards referenced but no guard registry bound. "
                    "Call bind_guards() before processing events.",
                    context={"guards": transition.guards},
                )
            return True

        result = self._guard_evaluator.can_transition(transition, context)
        return result.passed

    def _create_success_result(
        self,
        source_state: State,
        transition: Transition,
        trigger: str,
        context: dict[str, Any],
    ) -> TransitionResult:
        """Create a successful transition result. Uses hierarchy for exit/enter chains (LCA order)."""
        current_leaf = source_state.name
        target_leaf = self._hierarchy.effective_target_leaf(transition.dest)
        lca = self._hierarchy.lca(current_leaf, target_leaf)
        exit_chain = self._hierarchy.exit_chain(current_leaf, lca)
        enter_chain = self._hierarchy.enter_chain(lca, target_leaf)
        on_exit_actions = tuple(
            itertools.chain.from_iterable(
                self._states[s].on_exit for s in exit_chain
            )
        )
        on_enter_actions = tuple(
            itertools.chain.from_iterable(
                self._states[s].on_enter for s in enter_chain
            )
        )
        return TransitionResult.success_result(
            source_state=current_leaf,
            target_state=target_leaf,
            trigger=trigger,
            actions=transition.actions,
            on_exit=on_exit_actions,
            on_enter=on_enter_actions,
            metadata={
                "transition_description": transition.description,
            },
        )

    def _handle_no_transition(
        self, current_state: str, trigger: str
    ) -> TransitionResult:
        """Handle case where no transition matches."""
        if self._error_policy.strict_mode:
            # Check if trigger exists anywhere in machine (compare normalized)
            normalized_trigger = self._normalize_trigger(trigger)
            all_triggers = {self._normalize_trigger(t.trigger) for t in self._transitions}
            if normalized_trigger not in all_triggers:
                error = UndefinedTriggerError(
                    f"Trigger '{trigger}' is not defined in this machine",
                    trigger=trigger,
                    available_triggers=sorted(all_triggers),
                )
            else:
                error = InvalidTransitionError(
                    f"No transition for trigger '{trigger}' from state '{current_state}'",
                    current_state=current_state,
                    trigger=trigger,
                )
            return TransitionResult.failure_result(
                source_state=current_state,
                trigger=trigger,
                error=error,
            )

        return TransitionResult.no_op_result(current_state, trigger)

    def _handle_guard_failure(
        self,
        current_state: str,
        trigger: str,
        candidates: list[Transition],
    ) -> TransitionResult:
        """Handle case where all guard conditions failed."""
        error = InvalidTransitionError(
            f"All guards failed for trigger '{trigger}' from state '{current_state}'",
            current_state=current_state,
            trigger=trigger,
            context={
                "candidate_count": len(candidates),
                "reason": "guards_failed",
            },
        )
        return TransitionResult.failure_result(
            source_state=current_state,
            trigger=trigger,
            error=error,
            metadata={"reason": "guards_failed"},
        )

    # -------------------------------------------------------------------------
    # Query Methods
    # -------------------------------------------------------------------------

    def get_state(self, name: str) -> State:
        """Get a state by name.

        Args:
            name: State name.

        Returns:
            State object.

        Raises:
            UndefinedStateError: If state is not defined.
        """
        if name not in self._states:
            raise UndefinedStateError(f"State '{name}' is not defined", state_name=name)
        return self._states[name]

    def get_initial_state(self) -> State:
        """Get the initial state (resolved to leaf when root is compound)."""
        return self._states[self._initial_leaf]

    def get_available_transitions(self, current_state: str) -> list[Transition]:
        """Get all transitions available from a state.

        Args:
            current_state: Current state name.

        Returns:
            List of available transitions.
        """
        if current_state not in self._states:
            raise UndefinedStateError(
                f"State '{current_state}' is not defined",
                state_name=current_state,
            )

        ancestors_set = set(self._hierarchy.ancestors(current_state))
        available: list[Transition] = []
        for trans in self._transitions:
            if trans.source & ancestors_set:
                available.append(trans)
        return available

    def get_available_triggers(self, current_state: str) -> list[str]:
        """Get all triggers available from a state.

        Args:
            current_state: Current state name.

        Returns:
            List of available trigger names.
        """
        transitions = self.get_available_transitions(current_state)
        return sorted(set(t.trigger for t in transitions))

    def validate_state(self, state: str) -> bool:
        """Check if a state is defined.

        Args:
            state: State name to check.

        Returns:
            True if state is defined, False otherwise.
        """
        return state in self._states

    def is_terminal(self, state: str) -> bool:
        """Check if a state is terminal.

        Args:
            state: State name to check.

        Returns:
            True if state is terminal, False otherwise.

        Raises:
            UndefinedStateError: If state is not defined.
        """
        return self.get_state(state).is_terminal

    def is_initial(self, state: str) -> bool:
        """Check if a state is the initial state.

        Args:
            state: State name to check.

        Returns:
            True if state is initial, False otherwise.

        Raises:
            UndefinedStateError: If state is not defined.
        """
        return self.get_state(state).is_initial

    def can_transition(
        self,
        current_state: str,
        trigger: str,
        context: dict[str, Any] | None = None,
    ) -> bool:
        """Check if a transition is possible.

        This is a convenience method that processes the event and
        returns whether it would succeed.

        Args:
            current_state: Current state name.
            trigger: Event trigger.
            context: Optional context for guard evaluation.

        Returns:
            True if transition would succeed, False otherwise.
        """
        try:
            result = self.process(current_state, trigger, context)
            return result.success
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------

    @property
    def name(self) -> str:
        """Get the machine name from metadata."""
        return self._meta.get("machine_name", "unnamed")

    @property
    def version(self) -> str:
        """Get the machine version from metadata."""
        return self._meta.get("version", "0.0.0")

    @property
    def strict_mode(self) -> bool:
        """Check if strict mode is enabled."""
        return self._error_policy.strict_mode

    @property
    def states(self) -> dict[str, State]:
        """Get all states (read-only view)."""
        return dict(self._states)

    @property
    def transitions(self) -> list[Transition]:
        """Get all transitions (read-only view)."""
        return list(self._transitions)

    @property
    def state_names(self) -> list[str]:
        """Get all state names."""
        return list(self._states.keys())

    @property
    def trigger_names(self) -> list[str]:
        """Get all unique trigger names."""
        return sorted(set(t.trigger for t in self._transitions))

    @property
    def terminal_states(self) -> list[str]:
        """Get all terminal state names."""
        return [s.name for s in self._states.values() if s.is_terminal]

    @property
    def parallel_states(self) -> list[str]:
        """Get all parallel state names."""
        return [s.name for s in self._states.values() if s.is_parallel]

    @property
    def meta(self) -> dict[str, Any]:
        """Get machine metadata."""
        return dict(self._meta)

    # -------------------------------------------------------------------------
    # Parallel State Methods
    # -------------------------------------------------------------------------

    def is_parallel_state(self, state_name: str) -> bool:
        """Check if a state is a parallel (orthogonal) state.

        Args:
            state_name: State name to check.

        Returns:
            True if state is parallel, False otherwise.
        """
        return self._parallel_manager.is_parallel_state(state_name)

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
        return self._parallel_manager.enter_parallel_state(parallel_state_name)

    def process_parallel(
        self,
        config: ParallelStateConfig,
        event: str | Event,
        context: dict[str, Any] | None = None,
    ) -> tuple[ParallelStateConfig, list[TransitionResult]]:
        """Process an event for a parallel state configuration.

        Events may trigger transitions in one or more regions. Each region
        is checked independently, and matching transitions are processed.

        Args:
            config: Current parallel state configuration.
            event: Event trigger (string) or Event object.
            context: Optional context dictionary for guards.

        Returns:
            Tuple of (updated_config, list_of_transition_results).
            Each result corresponds to a region that had a matching transition.
        """
        trigger, event_obj = _normalize_event(event)
        trigger = self._normalize_trigger(trigger)
        ctx = _build_context(context, event_obj)

        results: list[TransitionResult] = []
        updated_config = config

        for region_name, current_state in config.region_states.items():
            region_transitions = self._find_region_transitions(
                config.parallel_state, region_name, current_state, trigger
            )

            if not region_transitions:
                continue

            # Evaluate guards and find first valid transition
            for transition in region_transitions:
                if self._evaluate_guards(transition, current_state, ctx):
                    # Create result for this region transition
                    result = self._create_region_transition_result(
                        config.parallel_state,
                        region_name,
                        current_state,
                        transition,
                        trigger,
                        ctx,
                    )
                    results.append(result)

                    if result.success:
                        updated_config = updated_config.with_region_state(
                            region_name, result.target_state  # type: ignore
                        )
                    break

        return updated_config, results

    async def async_process_parallel(
        self,
        config: ParallelStateConfig,
        event: str | Event,
        context: dict[str, Any] | None = None,
    ) -> tuple[ParallelStateConfig, list[TransitionResult]]:
        """Process an event for a parallel state configuration asynchronously.

        Async version of process_parallel that supports async guards.

        Args:
            config: Current parallel state configuration.
            event: Event trigger (string) or Event object.
            context: Optional context dictionary for guards.

        Returns:
            Tuple of (updated_config, list_of_transition_results).
        """
        trigger, event_obj = _normalize_event(event)
        trigger = self._normalize_trigger(trigger)
        ctx = _build_context(context, event_obj)

        results: list[TransitionResult] = []
        updated_config = config

        for region_name, current_state in config.region_states.items():
            region_transitions = self._find_region_transitions(
                config.parallel_state, region_name, current_state, trigger
            )

            if not region_transitions:
                continue

            # Evaluate guards asynchronously
            for transition in region_transitions:
                if await self._async_evaluate_guards(transition, current_state, ctx):
                    result = self._create_region_transition_result(
                        config.parallel_state,
                        region_name,
                        current_state,
                        transition,
                        trigger,
                        ctx,
                    )
                    results.append(result)

                    if result.success:
                        updated_config = updated_config.with_region_state(
                            region_name, result.target_state  # type: ignore
                        )
                    break

        return updated_config, results

    def _find_region_transitions(
        self,
        parallel_state: str,
        region_name: str,
        current_state: str,
        trigger: str,
    ) -> list[Transition]:
        """Find transitions for a specific region and state.

        Args:
            parallel_state: Name of the parallel state.
            region_name: Name of the region.
            current_state: Current state within the region.
            trigger: Event trigger.

        Returns:
            List of matching transitions (ordered by specificity).
        """
        candidates: list[Transition] = []
        normalized_trigger = self._normalize_trigger(trigger)

        for trans in self._transitions:
            if self._normalize_trigger(trans.trigger) != normalized_trigger:
                continue

            # Must be a region transition for this region
            if trans.region != region_name:
                continue

            # Source must match current state
            if current_state not in trans.source:
                continue

            candidates.append(trans)

        return candidates

    def _create_region_transition_result(
        self,
        parallel_state: str,
        region_name: str,
        source_state: str,
        transition: Transition,
        trigger: str,
        context: dict[str, Any],
    ) -> TransitionResult:
        """Create a transition result for a region transition.

        Args:
            parallel_state: Name of the parallel state.
            region_name: Name of the region.
            source_state: Source state within the region.
            transition: The matched transition.
            trigger: Event trigger.
            context: Context dictionary.

        Returns:
            TransitionResult for this region transition.
        """
        target_state = transition.dest

        # Get on_exit/on_enter actions from states if they exist
        on_exit_actions: tuple[ActionSpec, ...] = ()
        on_enter_actions: tuple[ActionSpec, ...] = ()

        if source_state in self._states:
            on_exit_actions = self._states[source_state].on_exit

        if target_state in self._states:
            on_enter_actions = self._states[target_state].on_enter

        return TransitionResult.success_result(
            source_state=source_state,
            target_state=target_state,
            trigger=trigger,
            actions=transition.actions,
            on_exit=on_exit_actions,
            on_enter=on_enter_actions,
            metadata={
                "parallel_state": parallel_state,
                "region": region_name,
                "transition_description": transition.description,
            },
        )

    def exit_parallel_state(self, config: ParallelStateConfig) -> list[str]:
        """Get the order of states to exit when leaving a parallel state.

        Returns states in bottom-up order: region states first, then parallel state.

        Args:
            config: Current parallel state configuration.

        Returns:
            List of state names to exit (for collecting on_exit actions).
        """
        return self._parallel_manager.exit_parallel_state(config)

    def get_parallel_exit_actions(self, config: ParallelStateConfig) -> tuple[str, ...]:
        """Get all on_exit actions when leaving a parallel state.

        Args:
            config: Current parallel state configuration.

        Returns:
            Tuple of action names in exit order.
        """
        actions: list[str] = []
        exit_order = self.exit_parallel_state(config)

        for state_name in exit_order:
            if state_name in self._states:
                actions.extend(self._states[state_name].on_exit)

        return tuple(actions)

    def get_parallel_enter_actions(self, parallel_state_name: str) -> tuple[str, ...]:
        """Get all on_enter actions when entering a parallel state.

        Args:
            parallel_state_name: Name of the parallel state.

        Returns:
            Tuple of action names in enter order.
        """
        config = self.enter_parallel_state(parallel_state_name)
        actions: list[str] = []

        # Enter parallel state first
        if parallel_state_name in self._states:
            actions.extend(self._states[parallel_state_name].on_enter)

        # Then enter each region's initial state
        for state_name in config.get_all_active():
            if state_name in self._states:
                actions.extend(self._states[state_name].on_enter)

        return tuple(actions)

    def validate_parallel_config(self, config: ParallelStateConfig) -> list[str]:
        """Validate a parallel state configuration.

        Args:
            config: Configuration to validate.

        Returns:
            List of validation errors (empty if valid).
        """
        return self._parallel_manager.validate_config(config)

    def __repr__(self) -> str:
        parallel_count = len(self.parallel_states)
        return (
            f"StateMachine(name={self.name!r}, "
            f"states={len(self._states)}, "
            f"transitions={len(self._transitions)}, "
            f"parallel={parallel_count})"
        )
