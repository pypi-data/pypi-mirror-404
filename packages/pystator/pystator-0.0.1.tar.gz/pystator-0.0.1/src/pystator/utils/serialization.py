"""Serialization utilities for PyStator FSM objects."""

from __future__ import annotations

from typing import Any

from pystator.core.state import State, StateType, Timeout
from pystator.core.transition import ActionSpec, TransitionResult


def _action_spec_to_dict(spec: ActionSpec) -> dict[str, Any]:
    """Serialize ActionSpec to dict."""
    d: dict[str, Any] = {"name": spec.name}
    if spec.params:
        d["params"] = spec.params
    return d


def _dict_to_action_spec(d: Any) -> ActionSpec:
    """Deserialize dict to ActionSpec."""
    if isinstance(d, str):
        return ActionSpec(name=d)
    return ActionSpec.from_config(d)


def serialize_state(state: State) -> dict[str, Any]:
    """Serialize a State object to a dictionary.

    Args:
        state: The State object to serialize.

    Returns:
        Dictionary representation of the state.
    """
    data: dict[str, Any] = {
        "name": state.name,
        "type": state.type.value,
        "description": state.description,
    }

    if state.on_enter:
        data["on_enter"] = [_action_spec_to_dict(s) for s in state.on_enter]

    if state.on_exit:
        data["on_exit"] = [_action_spec_to_dict(s) for s in state.on_exit]

    if state.timeout:
        data["timeout"] = {
            "seconds": state.timeout.seconds,
            "destination": state.timeout.destination,
        }

    if state.metadata:
        data["metadata"] = state.metadata

    return data


def deserialize_state(data: dict[str, Any]) -> State:
    """Deserialize a dictionary to a State object.

    Args:
        data: Dictionary representation of a state.

    Returns:
        State object.
    """
    timeout = None
    if "timeout" in data:
        timeout = Timeout(
            seconds=float(data["timeout"]["seconds"]),
            destination=data["timeout"]["destination"],
        )

    on_enter = tuple(_dict_to_action_spec(s) for s in data.get("on_enter", []))
    on_exit = tuple(_dict_to_action_spec(s) for s in data.get("on_exit", []))

    return State(
        name=data["name"],
        type=StateType(data.get("type", "stable")),
        description=data.get("description", ""),
        on_enter=on_enter,
        on_exit=on_exit,
        timeout=timeout,
        metadata=data.get("metadata", {}),
    )


def serialize_transition_result(result: TransitionResult) -> dict[str, Any]:
    """Serialize a TransitionResult to a dictionary.

    Useful for storing results in databases, sending over APIs,
    or logging.

    Args:
        result: The TransitionResult to serialize.

    Returns:
        Dictionary representation of the result.
    """
    data: dict[str, Any] = {
        "success": result.success,
        "source_state": result.source_state,
        "target_state": result.target_state,
        "trigger": result.trigger,
        "actions_to_execute": [_action_spec_to_dict(s) for s in result.actions_to_execute],
        "on_exit_actions": [_action_spec_to_dict(s) for s in result.on_exit_actions],
        "on_enter_actions": [_action_spec_to_dict(s) for s in result.on_enter_actions],
        "metadata": result.metadata,
    }

    if result.error:
        data["error"] = result.error.to_dict()

    return data


def deserialize_transition_result(data: dict[str, Any]) -> TransitionResult:
    """Deserialize a dictionary to a TransitionResult.

    Note: Error objects are not fully reconstructed - they become
    dictionaries in the metadata.

    Args:
        data: Dictionary representation of a transition result.

    Returns:
        TransitionResult object.
    """
    # Handle error - we can't fully reconstruct the error object,
    # so we store it in metadata
    metadata = dict(data.get("metadata", {}))
    if "error" in data and data["error"]:
        metadata["_serialized_error"] = data["error"]

    actions_to_execute = tuple(
        _dict_to_action_spec(s) for s in data.get("actions_to_execute", [])
    )
    on_exit_actions = tuple(
        _dict_to_action_spec(s) for s in data.get("on_exit_actions", [])
    )
    on_enter_actions = tuple(
        _dict_to_action_spec(s) for s in data.get("on_enter_actions", [])
    )

    return TransitionResult(
        success=data["success"],
        source_state=data["source_state"],
        target_state=data.get("target_state"),
        trigger=data["trigger"],
        actions_to_execute=actions_to_execute,
        on_exit_actions=on_exit_actions,
        on_enter_actions=on_enter_actions,
        error=None,  # Can't reconstruct error objects
        metadata=metadata,
    )


def result_to_audit_entry(
    result: TransitionResult,
    entity_id: str,
    timestamp: str | None = None,
) -> dict[str, Any]:
    """Convert a TransitionResult to an audit log entry.

    Useful for creating audit trails of state changes.

    Args:
        result: The transition result.
        entity_id: ID of the entity that changed state.
        timestamp: Optional timestamp (ISO format). Defaults to now.

    Returns:
        Dictionary suitable for audit logging.
    """
    from datetime import datetime, timezone

    if timestamp is None:
        timestamp = datetime.now(timezone.utc).isoformat()

    return {
        "entity_id": entity_id,
        "timestamp": timestamp,
        "success": result.success,
        "trigger": result.trigger,
        "source_state": result.source_state,
        "target_state": result.target_state,
        "state_changed": result.state_changed,
        "actions": list(result.all_actions),
        "error_type": result.error.__class__.__name__ if result.error else None,
        "error_message": result.error.message if result.error else None,
        "metadata": result.metadata,
    }
