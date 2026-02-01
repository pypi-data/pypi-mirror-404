"""Optional order lifecycle FSM and default guards/actions.

Pre-built order FSM (PENDING_NEW -> OPEN -> FILLED/REJECTED/CANCELED/etc.)
and stub or recipe-based guard/action defaults. Override with your own
implementations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from pystator import StateMachine, GuardRegistry, ActionRegistry

logger = logging.getLogger(__name__)

ORDER_FSM_FILENAME = "order_fsm.yaml"


def _default_order_fsm_path() -> Path:
    from importlib.resources import files
    return Path(files("pystator.contrib.order")) / "fsm" / ORDER_FSM_FILENAME


def load_order_fsm(path: str | Path | None = None) -> StateMachine:
    """Load the order lifecycle FSM from YAML.

    Args:
        path: Path to YAML file. If None, loads the bundled contrib FSM.

    Returns:
        StateMachine instance.
    """
    if path is None:
        path = _default_order_fsm_path()
    return StateMachine.from_yaml(path)


def register_order_guard_defaults(registry: GuardRegistry) -> None:
    """Register default guards for the order FSM.

    Uses recipe-based guards (is_full_fill, is_partial_fill) if
    pystator.recipes is available; otherwise registers stubs that
    log and return False (so apps must override with real implementations).
    """
    try:
        from pystator.recipes.guards import register_guard_from_recipe
        register_guard_from_recipe(
            registry, "is_full_fill",
            {"type": "expr", "expr": "fill_qty + filled_qty >= order_qty"},
        )
        register_guard_from_recipe(
            registry, "is_partial_fill",
            {"type": "expr", "expr": "0 < fill_qty + filled_qty < order_qty"},
        )
    except ImportError:
        def _stub_full(ctx: dict[str, Any]) -> bool:
            logger.debug("is_full_fill stub: override with your implementation")
            return False
        def _stub_partial(ctx: dict[str, Any]) -> bool:
            logger.debug("is_partial_fill stub: override with your implementation")
            return False
        registry.register("is_full_fill", _stub_full)
        registry.register("is_partial_fill", _stub_partial)

    def is_cancellable(ctx: dict[str, Any]) -> bool:
        return not ctx.get("in_flight", False)
    if not registry.has("is_cancellable"):
        registry.register("is_cancellable", is_cancellable)


def register_order_action_defaults(registry: ActionRegistry) -> None:
    """Register default (stub) actions for the order FSM.

    Registers no-op stubs that log at debug. Override with your own
    implementations (e.g. update_positions, release_buying_power).
    """
    _order_action_names = [
        "update_order_id", "record_rejection_reason", "update_positions",
        "release_buying_power", "decrement_remaining_qty", "send_cancel_to_exchange",
        "notify_ui_open", "log_audit_trail",
    ]
    for name in _order_action_names:
        if registry.has(name):
            continue
        def _stub(ctx: dict[str, Any], n: str = name) -> None:
            logger.debug("Order action %s stub: override with your implementation", n)
        registry.register(name, _stub)


__all__ = [
    "load_order_fsm",
    "register_order_guard_defaults",
    "register_order_action_defaults",
    "ORDER_FSM_FILENAME",
]
