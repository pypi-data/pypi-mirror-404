"""Recipe-based guards and actions (optional).

Register guards and actions from config/dict recipes so behavior can be
configured without writing Python. Install with: pip install pystator[recipes]

Guard recipes: {"type": "expr", "expr": "fill_qty + filled_qty >= order_qty"}
Action recipes: {"type": "log", "message": "..."} or {"type": "http", "method": "POST", "url": "..."}
"""

from pystator.recipes.guards import register_guard_from_recipe
from pystator.recipes.actions import register_action_from_recipe
from pystator.recipes.utils import substitute_template, substitute_dict
from pystator.recipes.context import flatten_context_for_guards

__all__ = [
    "register_guard_from_recipe",
    "register_action_from_recipe",
    "substitute_template",
    "substitute_dict",
    "flatten_context_for_guards",
]
