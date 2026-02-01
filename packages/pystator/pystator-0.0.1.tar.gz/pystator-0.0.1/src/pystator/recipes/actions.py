"""Recipe-based action registration.

Register actions from config/dict recipes (log, http) so behavior
can be configured without writing Python. HTTP type requires
httpx (pip install pystator[recipes]).
"""

from __future__ import annotations

import logging
from typing import Any

from pystator.recipes.utils import substitute_dict, substitute_template
from pystator.actions.registry import ActionRegistry

logger = logging.getLogger(__name__)


def _execute_log_recipe(recipe: dict[str, Any], context: dict[str, Any]) -> None:
    """Execute a log recipe: substitute message and log."""
    message = recipe.get("message", "")
    if not isinstance(message, str):
        message = str(message)
    level_name = (recipe.get("level") or "info").upper()
    level = getattr(logging, level_name, logging.INFO)
    msg = substitute_template(message, context)
    logger.log(level, "%s", msg)


def _execute_http_recipe(recipe: dict[str, Any], context: dict[str, Any]) -> None:
    """Execute an HTTP recipe: substitute url/body/headers and send request."""
    try:
        import httpx
    except ImportError as e:
        raise ImportError(
            "Recipe action type 'http' requires httpx. "
            "Install with: pip install pystator[recipes]"
        ) from e
    method = (recipe.get("method") or "GET").upper()
    url = recipe.get("url")
    if not url or not isinstance(url, str):
        raise ValueError("HTTP recipe requires 'url' string")
    url = substitute_template(url, context)
    headers = recipe.get("headers")
    if headers and isinstance(headers, dict):
        headers = substitute_dict(headers, context)
    else:
        headers = None
    body = recipe.get("body")
    if body is not None:
        if isinstance(body, dict):
            body = substitute_dict(body, context)
        elif isinstance(body, str):
            body = substitute_template(body, context)
    kwargs: dict[str, Any] = {"headers": headers} if headers else {}
    if body is not None:
        if isinstance(body, dict):
            kwargs["json"] = body
        else:
            kwargs["content"] = body if isinstance(body, (str, bytes)) else str(body)
    with httpx.Client() as client:
        if method == "GET":
            client.get(url, **kwargs)
        elif method == "POST":
            client.post(url, **kwargs)
        elif method == "PUT":
            client.put(url, **kwargs)
        elif method == "PATCH":
            client.patch(url, **kwargs)
        elif method == "DELETE":
            client.delete(url, **kwargs)
        else:
            client.request(method, url, **kwargs)


def register_action_from_recipe(
    registry: ActionRegistry,
    name: str,
    recipe: dict[str, Any],
) -> None:
    """Register an action from a recipe (config dict).

    Recipe types:
        - log: {"type": "log", "message": "Order {{order_id}} reached {{target_state}}", "level": "info"}
        - http: {"type": "http", "method": "POST", "url": "{{base_url}}/notify", "body": {"entity_id": "{{entity_id}}"}}

    Template substitution: {{key}} is replaced with context.get("key", "").

    Args:
        registry: Action registry to register into.
        name: Action name.
        recipe: Recipe dict with "type" and type-specific keys.

    Raises:
        ValueError: Unknown recipe type or missing required keys.
        ImportError: For "http" type if httpx is not installed.
    """
    if not recipe or not isinstance(recipe, dict):
        raise ValueError("Recipe must be a non-empty dict")
    rtype = recipe.get("type")
    if not rtype:
        raise ValueError("Recipe must have 'type'")
    if rtype == "log":
        message = recipe.get("message", "")
        if not isinstance(message, str):
            message = str(message)
        level = recipe.get("level", "info")

        def action(context: dict[str, Any]) -> None:
            _execute_log_recipe({"type": "log", "message": message, "level": level}, context)

        registry.register(name, action)
    elif rtype == "http":
        # Capture recipe for closure
        http_recipe = dict(recipe)

        def action(context: dict[str, Any]) -> None:
            _execute_http_recipe(http_recipe, context)

        registry.register(name, action)
    else:
        raise ValueError(f"Unknown action recipe type: {rtype!r}")
