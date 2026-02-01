"""Recipe-based guard registration.

Register guards from config/dict recipes (e.g. expressions) so behavior
can be configured without writing Python. Requires optional dependency
simpleeval for expression evaluation (pip install pystator[recipes]).
"""

from __future__ import annotations

from typing import Any

from pystator.guards.registry import GuardRegistry


def _eval_expr(expr: str, context: dict[str, Any]) -> bool:
    """Evaluate a boolean expression with context as namespace. Uses simpleeval."""
    try:
        from simpleeval import SimpleEval
    except ImportError as e:
        raise ImportError(
            "Recipe guard type 'expr' requires simpleeval. "
            "Install with: pip install pystator[recipes]"
        ) from e
    s = SimpleEval(names=context)
    result = s.eval(expr)
    if isinstance(result, bool):
        return result
    return bool(result)


def register_guard_from_recipe(
    registry: GuardRegistry,
    name: str,
    recipe: dict[str, Any],
) -> None:
    """Register a guard from a recipe (config dict).

    Recipe types:
        - expr: {"type": "expr", "expr": "fill_qty + filled_qty >= order_qty"}
          Context keys are available as variables. Result is coerced to bool.

    Args:
        registry: Guard registry to register into.
        name: Guard name.
        recipe: Recipe dict with "type" and type-specific keys.

    Raises:
        ValueError: Unknown recipe type or missing required keys.
        ImportError: For "expr" type if simpleeval is not installed.
    """
    if not recipe or not isinstance(recipe, dict):
        raise ValueError("Recipe must be a non-empty dict")
    rtype = recipe.get("type")
    if not rtype:
        raise ValueError("Recipe must have 'type'")
    if rtype == "expr":
        expr = recipe.get("expr")
        if expr is None or not isinstance(expr, str):
            raise ValueError("Recipe type 'expr' requires 'expr' string")
        expr = expr.strip()
        if not expr:
            raise ValueError("Recipe 'expr' cannot be empty")

        def guard(context: dict[str, Any]) -> bool:
            return _eval_expr(expr, context)

        registry.register(name, guard)
    else:
        raise ValueError(f"Unknown guard recipe type: {rtype!r}")
