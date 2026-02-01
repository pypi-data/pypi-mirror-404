"""Configuration validation for PyStator FSM definitions."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from pystator.config.models import MachineConfig
from pystator.core.errors import ConfigurationError


class ConfigValidator:
    """Validates FSM configuration with Pydantic and semantic rules.

    Performs two levels of validation:
    1. Pydantic schema validation (structure and types)
    2. Semantic validation (state references, exactly one initial, no transitions from terminal)

    Example:
        >>> validator = ConfigValidator()
        >>> errors = validator.validate(config)
        >>> if errors:
        ...     for error in errors:
        ...         print(f"Error: {error}")
    """

    def __init__(self) -> None:
        """Initialize the validator. Validation uses Pydantic models and semantic rules."""

    def validate(self, config: dict[str, Any]) -> list[str]:
        """Validate configuration.

        Args:
            config: The configuration dictionary to validate.

        Returns:
            List of validation error messages. Empty if valid.
        """
        errors: list[str] = []

        # Pydantic (schema) validation
        try:
            MachineConfig.model_validate(config)
        except ValidationError as e:
            for err in e.errors():
                loc = ".".join(str(p) for p in err.get("loc", ()))
                msg = err.get("msg", "validation error")
                if loc:
                    errors.append(f"[{loc}] {msg}")
                else:
                    errors.append(msg)
            return errors

        # Semantic validation
        errors.extend(self._validate_semantics(config))
        return errors

    def _validate_semantics(self, config: dict[str, Any]) -> list[str]:
        """Validate semantic rules (state refs, one initial, no transitions from terminal)."""
        errors: list[str] = []

        states = config.get("states", [])
        transitions = config.get("transitions", [])

        state_names: set[str] = set()
        initial_states: list[str] = []

        for state in states:
            name = state.get("name", "")
            if name in state_names:
                errors.append(f"Duplicate state name: '{name}'")
            state_names.add(name)
            if state.get("type") == "initial":
                initial_states.append(name)

        if len(initial_states) == 0:
            errors.append("No initial state defined. Exactly one state must have type='initial'")
        elif len(initial_states) > 1:
            errors.append(
                f"Multiple initial states defined: {initial_states}. "
                "Exactly one state must have type='initial'"
            )

        for i, trans in enumerate(transitions):
            trigger = trans.get("trigger") or f"transition[{i}]"
            source = trans.get("source", [])
            if isinstance(source, str):
                source = [source]
            for src in source:
                if src not in state_names:
                    errors.append(f"Transition '{trigger}': source state '{src}' not defined")
            dest = trans.get("dest", "")
            if dest not in state_names:
                errors.append(f"Transition '{trigger}': destination state '{dest}' not defined")

        for state in states:
            timeout = state.get("timeout")
            if timeout:
                dest = timeout.get("destination", "")
                if dest and dest not in state_names:
                    errors.append(
                        f"State '{state.get('name')}': timeout destination '{dest}' not defined"
                    )

        error_policy = config.get("error_policy") or {}
        fallback = error_policy.get("default_fallback")
        if fallback and fallback not in state_names:
            errors.append(f"Error policy: fallback state '{fallback}' not defined")

        terminal_states = {s.get("name") for s in states if s.get("type") == "terminal"}
        for trans in transitions:
            source = trans.get("source", [])
            if isinstance(source, str):
                source = [source]
            for src in source:
                if src in terminal_states:
                    errors.append(
                        f"Transition '{trans.get('trigger')}': "
                        f"cannot have transitions from terminal state '{src}'"
                    )

        return errors

    def validate_strict(self, config: dict[str, Any]) -> None:
        """Validate and raise ConfigurationError if invalid."""
        errors = self.validate(config)
        if errors:
            raise ConfigurationError(
                f"Configuration validation failed with {len(errors)} error(s)",
                context={"errors": errors},
            )


def validate_config(config: dict[str, Any], strict: bool = True) -> list[str]:
    """Validate a configuration dictionary.

    Args:
        config: The configuration dictionary to validate.
        strict: If True, raises ConfigurationError on failure.

    Returns:
        List of validation error messages.

    Raises:
        ConfigurationError: If strict=True and validation fails.
    """
    validator = ConfigValidator()
    if strict:
        validator.validate_strict(config)
        return []
    return validator.validate(config)
