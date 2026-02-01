"""Built-in guard functions for common use cases."""

from __future__ import annotations

from typing import Any

from pystator.guards.registry import GuardRegistry


def always_true(context: dict[str, Any]) -> bool:
    """Guard that always passes.

    Useful as a placeholder or for testing.
    """
    return True


def always_false(context: dict[str, Any]) -> bool:
    """Guard that always fails.

    Useful for temporarily blocking transitions or testing.
    """
    return False


def is_not_none(key: str) -> Any:
    """Create a guard that checks if a context key is not None.

    Args:
        key: The context key to check.

    Returns:
        Guard function.

    Example:
        >>> registry.register("has_user_id", is_not_none("user_id"))
    """

    def guard(context: dict[str, Any]) -> bool:
        return context.get(key) is not None

    guard.__name__ = f"is_not_none_{key}"
    return guard


def is_truthy(key: str) -> Any:
    """Create a guard that checks if a context key is truthy.

    Args:
        key: The context key to check.

    Returns:
        Guard function.
    """

    def guard(context: dict[str, Any]) -> bool:
        return bool(context.get(key))

    guard.__name__ = f"is_truthy_{key}"
    return guard


def equals(key: str, value: Any) -> Any:
    """Create a guard that checks if a context key equals a value.

    Args:
        key: The context key to check.
        value: The expected value.

    Returns:
        Guard function.

    Example:
        >>> registry.register("is_admin", equals("role", "admin"))
    """

    def guard(context: dict[str, Any]) -> bool:
        return context.get(key) == value

    guard.__name__ = f"equals_{key}_{value}"
    return guard


def not_equals(key: str, value: Any) -> Any:
    """Create a guard that checks if a context key does not equal a value.

    Args:
        key: The context key to check.
        value: The value to compare against.

    Returns:
        Guard function.
    """

    def guard(context: dict[str, Any]) -> bool:
        return context.get(key) != value

    guard.__name__ = f"not_equals_{key}_{value}"
    return guard


def greater_than(key: str, threshold: float | int) -> Any:
    """Create a guard that checks if a context key is greater than a threshold.

    Args:
        key: The context key to check.
        threshold: The threshold value.

    Returns:
        Guard function.

    Example:
        >>> registry.register("has_balance", greater_than("balance", 0))
    """

    def guard(context: dict[str, Any]) -> bool:
        value = context.get(key)
        if value is None:
            return False
        return value > threshold

    guard.__name__ = f"greater_than_{key}_{threshold}"
    return guard


def less_than(key: str, threshold: float | int) -> Any:
    """Create a guard that checks if a context key is less than a threshold.

    Args:
        key: The context key to check.
        threshold: The threshold value.

    Returns:
        Guard function.
    """

    def guard(context: dict[str, Any]) -> bool:
        value = context.get(key)
        if value is None:
            return False
        return value < threshold

    guard.__name__ = f"less_than_{key}_{threshold}"
    return guard


def greater_or_equal(key: str, threshold: float | int) -> Any:
    """Create a guard that checks if a context key is >= a threshold.

    Args:
        key: The context key to check.
        threshold: The threshold value.

    Returns:
        Guard function.
    """

    def guard(context: dict[str, Any]) -> bool:
        value = context.get(key)
        if value is None:
            return False
        return value >= threshold

    guard.__name__ = f"greater_or_equal_{key}_{threshold}"
    return guard


def less_or_equal(key: str, threshold: float | int) -> Any:
    """Create a guard that checks if a context key is <= a threshold.

    Args:
        key: The context key to check.
        threshold: The threshold value.

    Returns:
        Guard function.
    """

    def guard(context: dict[str, Any]) -> bool:
        value = context.get(key)
        if value is None:
            return False
        return value <= threshold

    guard.__name__ = f"less_or_equal_{key}_{threshold}"
    return guard


def in_list(key: str, allowed: list[Any] | tuple[Any, ...] | set[Any]) -> Any:
    """Create a guard that checks if a context key is in a list of values.

    Args:
        key: The context key to check.
        allowed: Collection of allowed values.

    Returns:
        Guard function.

    Example:
        >>> registry.register("valid_status", in_list("status", ["active", "pending"]))
    """
    allowed_set = set(allowed)

    def guard(context: dict[str, Any]) -> bool:
        return context.get(key) in allowed_set

    guard.__name__ = f"in_list_{key}"
    return guard


def not_in_list(key: str, forbidden: list[Any] | tuple[Any, ...] | set[Any]) -> Any:
    """Create a guard that checks if a context key is not in a list of values.

    Args:
        key: The context key to check.
        forbidden: Collection of forbidden values.

    Returns:
        Guard function.
    """
    forbidden_set = set(forbidden)

    def guard(context: dict[str, Any]) -> bool:
        return context.get(key) not in forbidden_set

    guard.__name__ = f"not_in_list_{key}"
    return guard


def has_key(key: str) -> Any:
    """Create a guard that checks if a key exists in context.

    Args:
        key: The context key to check.

    Returns:
        Guard function.
    """

    def guard(context: dict[str, Any]) -> bool:
        return key in context

    guard.__name__ = f"has_key_{key}"
    return guard


def all_of(*guards: Any) -> Any:
    """Create a compound guard that requires all sub-guards to pass.

    Args:
        guards: Guard functions to combine.

    Returns:
        Guard function that passes if all sub-guards pass.

    Example:
        >>> registry.register(
        ...     "can_withdraw",
        ...     all_of(is_truthy("is_verified"), greater_than("balance", 0))
        ... )
    """

    def guard(context: dict[str, Any]) -> bool:
        return all(g(context) for g in guards)

    guard.__name__ = "all_of"
    return guard


def any_of(*guards: Any) -> Any:
    """Create a compound guard that requires any sub-guard to pass.

    Args:
        guards: Guard functions to combine.

    Returns:
        Guard function that passes if any sub-guard passes.

    Example:
        >>> registry.register(
        ...     "has_permission",
        ...     any_of(equals("role", "admin"), equals("role", "moderator"))
        ... )
    """

    def guard(context: dict[str, Any]) -> bool:
        return any(g(context) for g in guards)

    guard.__name__ = "any_of"
    return guard


def none_of(*guards: Any) -> Any:
    """Create a compound guard that requires no sub-guards to pass.

    Args:
        guards: Guard functions to combine.

    Returns:
        Guard function that passes if no sub-guards pass.
    """

    def guard(context: dict[str, Any]) -> bool:
        return not any(g(context) for g in guards)

    guard.__name__ = "none_of"
    return guard


def negate(guard_func: Any) -> Any:
    """Create a guard that negates another guard.

    Args:
        guard_func: Guard function to negate.

    Returns:
        Guard function that passes when the original fails.

    Example:
        >>> registry.register("not_admin", negate(equals("role", "admin")))
    """

    def guard(context: dict[str, Any]) -> bool:
        return not guard_func(context)

    guard.__name__ = f"not_{getattr(guard_func, '__name__', 'guard')}"
    return guard


def register_builtins(registry: GuardRegistry) -> None:
    """Register built-in guards with a registry.

    Args:
        registry: The guard registry to populate.

    Registers:
        - always_true: Always passes
        - always_false: Always fails
    """
    registry.register("always_true", always_true)
    registry.register("always_false", always_false)
