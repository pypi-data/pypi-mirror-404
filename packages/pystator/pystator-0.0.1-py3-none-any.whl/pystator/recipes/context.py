"""Context flattening helper for guard expressions.

Guard expressions (inline and named) receive a flat namespace. This module
provides a small helper to build a guard-friendly flat dict from nested or
domain-specific context before calling machine.process() or when providing
context from a state store adapter.
"""

from __future__ import annotations

from typing import Any


def flatten_context_for_guards(
    context: dict[str, Any],
    *,
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a flat dict suitable for guard evaluation.

    Copies context and applies optional overrides. Guard expressions see this
    flat namespace (e.g. ``fill_qty >= order_qty``, ``len(positions) < max_positions``).

    If your context is nested (e.g. ``trading_context`` with ``positions``,
    ``buying_power``), either:
    - Pass an already-flat dict built in your application (e.g. add
      ``position_count = len(trading_context["positions"])`` before calling
      process), or
    - Use overrides to inject derived values::
        flatten_context_for_guards(
            context,
            overrides={"position_count": len(context.get("trading_context", {}).get("positions", []))},
        )

    Args:
        context: Variables available to guards (can be nested).
        overrides: Optional key-value overrides merged on top of the copy.

    Returns:
        Shallow copy of context with overrides applied. Safe to pass to
        machine.process(..., context=result) and guard evaluation.
    """
    flat = dict(context)
    if overrides:
        flat.update(overrides)
    return flat
