"""
FSM service for PyStator API.

Builds machines from config and processes events. Uses pass-through guards
so any config works without requiring guard implementations.
"""

from __future__ import annotations

from typing import Any

from pystator import GuardRegistry, StateMachine
from pystator.core.errors import ConfigurationError


def _collect_guard_names(config: dict[str, Any]) -> set[str]:
    """Collect all guard names referenced in transitions."""
    names: set[str] = set()
    for trans in config.get("transitions", []):
        guards = trans.get("guards", [])
        if isinstance(guards, str):
            names.add(guards)
        else:
            names.update(guards)
    return names


def _build_pass_through_guards(guard_names: set[str]) -> GuardRegistry:
    """Build a registry that passes all listed guard names (no-op for API)."""
    registry = GuardRegistry()
    for name in guard_names:
        registry.register(name, lambda ctx: True)
    return registry


def build_machine_from_config(config: dict[str, Any]) -> StateMachine:
    """
    Build a StateMachine from config with pass-through guards.

    All guards referenced in transitions are registered as no-op (always pass)
    so the API can compute transitions without requiring guard implementations.
    """
    guard_names = _collect_guard_names(config)
    guards = _build_pass_through_guards(guard_names)
    machine = StateMachine.from_dict(config)
    machine.bind_guards(guards)
    return machine


def validate_config(config: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any] | None]:
    """
    Validate FSM config. Returns (valid, errors, info).

    If valid, info contains machine_name, version, state_names, trigger_names.
    """
    errors: list[str] = []
    try:
        machine = StateMachine.from_dict(config)
        info = {
            "machine_name": machine.name,
            "version": machine.version,
            "state_names": machine.state_names,
            "trigger_names": machine.trigger_names,
            "terminal_states": machine.terminal_states,
        }
        return True, [], info
    except ConfigurationError as e:
        errors.append(str(e))
        if e.context:
            for k, v in e.context.items():
                errors.append(f"  {k}: {v}")
        return False, errors, None
    except Exception as e:
        errors.append(str(e))
        return False, errors, None


class FSMService:
    """Service for building machines and processing events."""

    def process(
        self,
        config: dict[str, Any],
        current_state: str,
        trigger: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Build machine from config and process one event.

        Returns a dict suitable for JSON: success, source_state, target_state,
        trigger, actions_to_execute, on_exit_actions, on_enter_actions, error, metadata.
        """
        machine = build_machine_from_config(config)
        ctx = context or {}
        result = machine.process(current_state, trigger, ctx)

        def action_specs_to_list(specs) -> list[dict[str, Any]]:
            return [
                {"name": s.name, **({"params": s.params} if s.params else {})}
                for s in specs
            ]

        out: dict[str, Any] = {
            "success": result.success,
            "source_state": result.source_state,
            "target_state": result.target_state,
            "trigger": result.trigger,
            "actions_to_execute": action_specs_to_list(result.actions_to_execute),
            "on_exit_actions": action_specs_to_list(result.on_exit_actions),
            "on_enter_actions": action_specs_to_list(result.on_enter_actions),
            "metadata": dict(result.metadata),
        }
        if result.error:
            out["error"] = {"type": type(result.error).__name__, "message": str(result.error)}
        else:
            out["error"] = None
        return out

    def validate(self, config: dict[str, Any]) -> tuple[bool, list[str], dict[str, Any] | None]:
        """Validate config. Returns (valid, errors, info)."""
        return validate_config(config)
