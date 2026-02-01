"""Utilities for recipe-based guards and actions."""

from __future__ import annotations

import re
from typing import Any


def substitute_template(template: str, context: dict[str, Any]) -> str:
    """Replace {{key}} placeholders with context values.

    Args:
        template: String containing {{key}} placeholders.
        context: Dictionary of values. Keys are used for substitution.
                 Non-string values are converted to str.

    Returns:
        String with placeholders replaced. Missing keys become empty string.
    """
    if not template:
        return template

    def repl(match: re.Match[str]) -> str:
        key = match.group(1).strip()
        value = context.get(key, "")
        return str(value) if value is not None else ""

    return re.sub(r"\{\{\s*([^}]+)\s*\}\}", repl, template)


def substitute_dict(
    data: dict[str, Any], context: dict[str, Any]
) -> dict[str, Any]:
    """Recursively substitute {{key}} in string values of a dict.

    Args:
        data: Dict that may contain string values with {{key}} placeholders.
        context: Context for substitution.

    Returns:
        New dict with placeholders replaced. Nested dicts and list string
        values are processed recursively.
    """
    result: dict[str, Any] = {}
    for k, v in data.items():
        if isinstance(v, str):
            result[k] = substitute_template(v, context)
        elif isinstance(v, dict):
            result[k] = substitute_dict(v, context)
        elif isinstance(v, list):
            result[k] = [
                substitute_template(x, context) if isinstance(x, str) else x
                for x in v
            ]
        else:
            result[k] = v
    return result
