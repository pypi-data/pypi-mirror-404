"""Optional rebalance workflow FSM and default guards/actions.

Pre-built rebalance FSM (TARGETS_RECEIVED -> ... -> COMPLETED/FAILED/CANCELED)
and stub or recipe-based guard/action defaults. Override with your own
implementations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pystator import StateMachine, GuardRegistry, ActionRegistry

logger = logging.getLogger(__name__)

REBALANCE_FSM_FILENAME = "rebalance_fsm.yaml"


def _default_rebalance_fsm_path() -> Path:
    from importlib.resources import files
    return Path(files("pystator.contrib.rebalance")) / "fsm" / REBALANCE_FSM_FILENAME


def load_rebalance_fsm(path: str | Path | None = None) -> StateMachine:
    """Load the rebalance workflow FSM from YAML.

    Args:
        path: Path to YAML file. If None, loads the bundled contrib FSM.

    Returns:
        StateMachine instance.
    """
    if path is None:
        path = _default_rebalance_fsm_path()
    return StateMachine.from_yaml(path)


def register_rebalance_guard_defaults(registry: GuardRegistry) -> None:
    """Register default guards for the rebalance FSM.

    Uses recipe-based guard for all_orders_terminal if recipes available;
    otherwise stubs. Other guards (requires_approval, auto_approval_enabled,
    no_orders_needed) are simple callables.
    """
    def requires_approval(ctx: dict[str, Any]) -> bool:
        return ctx.get("require_approval", True)

    def auto_approval_enabled(ctx: dict[str, Any]) -> bool:
        return not ctx.get("require_approval", True)

    def no_orders_needed(ctx: dict[str, Any]) -> bool:
        orders = ctx.get("calculated_orders", [])
        return len(orders) == 0

    def all_orders_terminal(ctx: dict[str, Any]) -> bool:
        order_statuses = ctx.get("order_statuses", [])
        terminal = {"FILLED", "CANCELED", "REJECTED", "TIMED_OUT", "EXPIRED"}
        return all(s in terminal for s in order_statuses)

    for name, fn in [
        ("requires_approval", requires_approval),
        ("auto_approval_enabled", auto_approval_enabled),
        ("no_orders_needed", no_orders_needed),
        ("all_orders_terminal", all_orders_terminal),
    ]:
        if not registry.has(name):
            registry.register(name, fn)


def register_rebalance_action_defaults(registry: ActionRegistry) -> None:
    """Register default (stub) actions for the rebalance FSM.

    Registers no-op stubs that log at debug. Override with your own
    implementations.
    """
    _rebalance_action_names = [
        "log_rebalance_started", "validate_target_weights", "log_positions_fetched",
        "notify_orders_ready", "notify_approval_required", "record_approval",
        "submit_orders", "log_orders_submitted", "log_rebalance_complete",
        "notify_rebalance_complete", "record_completion_time", "log_error",
        "notify_failure", "store_error_details", "log_approval_timeout",
        "notify_approval_timeout", "log_rebalance_canceled", "cancel_pending_orders",
        "log_rejection", "fetch_current_positions", "compute_rebalance_orders",
    ]
    for name in _rebalance_action_names:
        if registry.has(name):
            continue
        def _stub(ctx: dict[str, Any], n: str = name) -> None:
            logger.debug("Rebalance action %s stub: override with your implementation", n)
        registry.register(name, _stub)


__all__ = [
    "load_rebalance_fsm",
    "register_rebalance_guard_defaults",
    "register_rebalance_action_defaults",
    "REBALANCE_FSM_FILENAME",
]
