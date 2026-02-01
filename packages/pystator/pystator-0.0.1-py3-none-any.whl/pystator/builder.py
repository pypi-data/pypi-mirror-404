"""Fluent builder for constructing StateMachine instances."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pystator.config.loader import ConfigLoader
from pystator.core.machine import StateMachine


class StateMachineBuilder:
    """Fluent builder for constructing StateMachine instances.

    Provides a user-friendly API for building state machines programmatically
    or extending existing configurations.

    Example:
        >>> machine = (
        ...     StateMachineBuilder("order_workflow")
        ...     .add_state("PENDING", type="initial")
        ...     .add_state("PROCESSING")
        ...     .add_state("DONE", type="terminal")
        ...     .add_transition("start", "PENDING", "PROCESSING")
        ...     .add_transition("complete", "PROCESSING", "DONE")
        ...     .build()
        ... )

        >>> # Extend existing config
        >>> machine = (
        ...     StateMachineBuilder.from_yaml("base.yaml")
        ...     .add_state("CUSTOM")
        ...     .add_transition("custom", "PROCESSING", "CUSTOM")
        ...     .build()
        ... )
    """

    def __init__(self, name: str = "unnamed", version: str = "1.0") -> None:
        """Initialize a new builder.

        Args:
            name: Machine name.
            version: Machine version.
        """
        self._meta: dict[str, Any] = {"machine_name": name, "version": version}
        self._states: dict[str, dict[str, Any]] = {}
        self._transitions: list[dict[str, Any]] = []
        self._error_policy: dict[str, Any] | None = None

    @classmethod
    def from_yaml(
        cls,
        path: str | Path,
        variables: dict[str, str] | None = None,
    ) -> "StateMachineBuilder":
        """Create a builder from an existing YAML configuration.

        Args:
            path: Path to YAML file.
            variables: Optional variable substitutions.

        Returns:
            Builder initialized with the config.
        """
        loader = ConfigLoader(validate=True, variables=variables)
        config = loader.load(path)
        return cls.from_dict(config)

    @classmethod
    def from_dict(cls, config: dict[str, Any]) -> "StateMachineBuilder":
        """Create a builder from an existing configuration dict.

        Args:
            config: Configuration dictionary.

        Returns:
            Builder initialized with the config.
        """
        meta = config.get("meta", {})
        builder = cls(
            name=meta.get("machine_name", "unnamed"),
            version=meta.get("version", "1.0"),
        )
        builder._meta = dict(meta)

        for state_def in config.get("states", []):
            builder._states[state_def["name"]] = dict(state_def)

        builder._transitions = [dict(t) for t in config.get("transitions", [])]

        if "error_policy" in config:
            builder._error_policy = dict(config["error_policy"])

        return builder

    def add_state(
        self,
        name: str,
        *,
        type: str = "stable",
        description: str = "",
        on_enter: list[str] | str | None = None,
        on_exit: list[str] | str | None = None,
        timeout: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> "StateMachineBuilder":
        """Add or replace a state.

        Args:
            name: State name (uppercase recommended).
            type: State type: "initial", "stable", "terminal", or "error".
            description: Human-readable description.
            on_enter: Action name(s) to execute on entry.
            on_exit: Action name(s) to execute on exit.
            timeout: Timeout config {"seconds": float, "destination": str}.
            metadata: Additional metadata.

        Returns:
            Self for chaining.
        """
        state_def: dict[str, Any] = {"name": name, "type": type}

        if description:
            state_def["description"] = description
        if on_enter:
            state_def["on_enter"] = [on_enter] if isinstance(on_enter, str) else on_enter
        if on_exit:
            state_def["on_exit"] = [on_exit] if isinstance(on_exit, str) else on_exit
        if timeout:
            state_def["timeout"] = timeout
        if metadata:
            state_def["metadata"] = metadata

        self._states[name] = state_def
        return self

    def add_transition(
        self,
        trigger: str,
        source: str | list[str],
        dest: str,
        *,
        guards: list[str] | str | None = None,
        actions: list[str] | str | None = None,
        description: str = "",
        metadata: dict[str, Any] | None = None,
    ) -> "StateMachineBuilder":
        """Add a transition.

        Args:
            trigger: Event name that triggers this transition.
            source: Source state name(s).
            dest: Destination state name.
            guards: Guard name(s) that must pass.
            actions: Action name(s) to execute on transition.
            description: Human-readable description.
            metadata: Additional metadata.

        Returns:
            Self for chaining.
        """
        trans_def: dict[str, Any] = {
            "trigger": trigger,
            "source": source,
            "dest": dest,
        }

        if guards:
            trans_def["guards"] = [guards] if isinstance(guards, str) else guards
        if actions:
            trans_def["actions"] = [actions] if isinstance(actions, str) else actions
        if description:
            trans_def["description"] = description
        if metadata:
            trans_def["metadata"] = metadata

        self._transitions.append(trans_def)
        return self

    def remove_state(self, name: str) -> "StateMachineBuilder":
        """Remove a state by name.

        Args:
            name: State name to remove.

        Returns:
            Self for chaining.

        Raises:
            KeyError: If state doesn't exist.
        """
        del self._states[name]
        return self

    def remove_transition(
        self,
        trigger: str,
        source: str | None = None,
    ) -> "StateMachineBuilder":
        """Remove transitions by trigger (and optionally source).

        Args:
            trigger: Trigger name to match.
            source: If provided, only remove transitions from this source.

        Returns:
            Self for chaining.
        """
        def matches(t: dict) -> bool:
            if t["trigger"] != trigger:
                return False
            if source is None:
                return True
            t_source = t["source"]
            if isinstance(t_source, str):
                return t_source == source
            return source in t_source

        self._transitions = [t for t in self._transitions if not matches(t)]
        return self

    def set_meta(self, key: str, value: Any) -> "StateMachineBuilder":
        """Set a metadata value.

        Args:
            key: Metadata key.
            value: Metadata value.

        Returns:
            Self for chaining.
        """
        self._meta[key] = value
        return self

    def set_error_policy(
        self,
        default_fallback: str | None = None,
        retry_attempts: int = 0,
    ) -> "StateMachineBuilder":
        """Set the error handling policy.

        Args:
            default_fallback: Default state to transition to on error.
            retry_attempts: Number of retry attempts.

        Returns:
            Self for chaining.
        """
        self._error_policy = {}
        if default_fallback:
            self._error_policy["default_fallback"] = default_fallback
        if retry_attempts:
            self._error_policy["retry_attempts"] = retry_attempts
        return self

    def to_dict(self) -> dict[str, Any]:
        """Export the builder configuration as a dict.

        Returns:
            Configuration dictionary.
        """
        config: dict[str, Any] = {
            "meta": dict(self._meta),
            "states": list(self._states.values()),
            "transitions": list(self._transitions),
        }
        if self._error_policy:
            config["error_policy"] = dict(self._error_policy)
        return config

    def to_yaml(self) -> str:
        """Export the builder configuration as YAML.

        Returns:
            YAML string.
        """
        try:
            import yaml
        except ImportError as e:
            raise ImportError("PyYAML is required for to_yaml()") from e

        return yaml.safe_dump(self.to_dict(), default_flow_style=False, sort_keys=False)

    def save_yaml(self, path: str | Path) -> None:
        """Save the configuration to a YAML file.

        Args:
            path: Output file path.
        """
        Path(path).write_text(self.to_yaml(), encoding="utf-8")

    def build(self) -> StateMachine:
        """Build the StateMachine.

        Returns:
            Configured StateMachine instance.

        Raises:
            ConfigurationError: If configuration is invalid.
        """
        return StateMachine.from_dict(self.to_dict())

    @property
    def state_names(self) -> list[str]:
        """Get current state names."""
        return list(self._states.keys())

    @property
    def transition_count(self) -> int:
        """Get current transition count."""
        return len(self._transitions)

    def __repr__(self) -> str:
        return (
            f"StateMachineBuilder(name={self._meta.get('machine_name')!r}, "
            f"states={len(self._states)}, transitions={len(self._transitions)})"
        )
