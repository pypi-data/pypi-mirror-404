"""Optional domain modules: order lifecycle and rebalance workflow.

Pre-built FSMs and default guard/action stubs or recipes. Use these
and override with your own implementations.
"""

from pystator.contrib.order import (
    load_order_fsm,
    register_order_guard_defaults,
    register_order_action_defaults,
    ORDER_FSM_FILENAME,
)
from pystator.contrib.rebalance import (
    load_rebalance_fsm,
    register_rebalance_guard_defaults,
    register_rebalance_action_defaults,
    REBALANCE_FSM_FILENAME,
)

__all__ = [
    "load_order_fsm",
    "register_order_guard_defaults",
    "register_order_action_defaults",
    "ORDER_FSM_FILENAME",
    "load_rebalance_fsm",
    "register_rebalance_guard_defaults",
    "register_rebalance_action_defaults",
    "REBALANCE_FSM_FILENAME",
]
