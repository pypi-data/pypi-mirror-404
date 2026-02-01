"""Guard function registry for PyStator FSM."""

from __future__ import annotations

import asyncio
import inspect
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable, Protocol, Union, runtime_checkable

from pystator.core.errors import GuardNotFoundError


@runtime_checkable
class GuardFunc(Protocol):
    """Protocol for synchronous guard functions.

    Guards are pure functions that take a context dictionary and return
    a boolean indicating whether a transition should be allowed.

    The context typically contains:
    - Event payload data
    - Current entity state
    - Additional runtime context

    Guards must be:
    - Pure (no side effects)
    - Deterministic (same input -> same output)
    - Fast (executed during transition computation)
    """

    def __call__(self, context: dict[str, Any]) -> bool:
        """Evaluate the guard condition.

        Args:
            context: Dictionary containing event data and runtime context.

        Returns:
            True if the transition should be allowed, False otherwise.
        """
        ...


@runtime_checkable
class AsyncGuardFunc(Protocol):
    """Protocol for asynchronous guard functions.

    Async guards can call external services (databases, APIs) during evaluation.
    Use for guards that need to check external state like:
    - Buying power from broker
    - User permissions from auth service
    - Rate limits from Redis

    Example:
        >>> async def check_buying_power(ctx: dict) -> bool:
        ...     account = await broker.get_account()
        ...     return account.buying_power >= ctx["order_value"]
    """

    def __call__(self, context: dict[str, Any]) -> Awaitable[bool]:
        """Evaluate the guard condition asynchronously.

        Args:
            context: Dictionary containing event data and runtime context.

        Returns:
            Awaitable that resolves to True if allowed, False otherwise.
        """
        ...


# Union type for any guard function (sync or async)
AnyGuardFunc = Union[GuardFunc, AsyncGuardFunc, Callable[[dict[str, Any]], Union[bool, Awaitable[bool]]]]


@dataclass
class GuardResult:
    """Result of guard evaluation with details.

    Attributes:
        passed: Whether all guards passed.
        guard_name: Name of the guard (last evaluated if failed).
        message: Optional message explaining the result.
        evaluated_guards: List of (guard_name, passed) tuples.
    """

    passed: bool
    guard_name: str | None = None
    message: str = ""
    evaluated_guards: list[tuple[str, bool]] = field(default_factory=list)

    @classmethod
    def success(cls, evaluated: list[tuple[str, bool]] | None = None) -> "GuardResult":
        """Create a successful result."""
        return cls(passed=True, evaluated_guards=evaluated or [])

    @classmethod
    def failure(
        cls,
        guard_name: str,
        message: str = "",
        evaluated: list[tuple[str, bool]] | None = None,
    ) -> "GuardResult":
        """Create a failure result."""
        return cls(
            passed=False,
            guard_name=guard_name,
            message=message or f"Guard '{guard_name}' rejected transition",
            evaluated_guards=evaluated or [],
        )


class GuardRegistry:
    """Registry for guard functions (sync and async).

    The guard registry stores named guard functions that can be referenced
    in FSM transition definitions. Guards are evaluated during transition
    processing to determine if a transition should be allowed.

    Supports both synchronous and asynchronous guards:
    - Sync guards: evaluated with `evaluate()` or `evaluate_all()`
    - Async guards: evaluated with `async_evaluate()` or `async_evaluate_all()`

    Guards are pure functions: they receive context and return a boolean.
    They should NOT have side effects (except async guards calling read-only APIs).

    Example:
        >>> registry = GuardRegistry()
        >>> registry.register("is_full_fill", lambda ctx: ctx["fill_qty"] >= ctx["order_qty"])
        >>> registry.register("is_cancellable", is_cancellable_func)
        >>>
        >>> # Sync evaluation
        >>> result = registry.evaluate("is_full_fill", {"fill_qty": 100, "order_qty": 100})
        >>> assert result is True
        >>>
        >>> # Async guard
        >>> async def check_buying_power(ctx):
        ...     account = await broker.get_account()
        ...     return account.buying_power >= ctx["order_value"]
        >>> registry.register("check_buying_power", check_buying_power)
        >>>
        >>> # Async evaluation
        >>> result = await registry.async_evaluate("check_buying_power", {"order_value": 1000})
    """

    def __init__(self) -> None:
        """Initialize an empty guard registry."""
        self._guards: dict[str, AnyGuardFunc] = {}
        self._async_guards: set[str] = set()  # Track which guards are async

    def register(
        self,
        name: str,
        func: AnyGuardFunc,
    ) -> None:
        """Register a guard function (sync or async).

        Args:
            name: Unique name for the guard.
            func: Guard function that takes context and returns bool (or awaitable bool).

        Raises:
            ValueError: If name is empty or already registered.
        """
        if not name:
            raise ValueError("Guard name cannot be empty")
        if name in self._guards:
            raise ValueError(f"Guard '{name}' is already registered")
        self._guards[name] = func
        # Track if this is an async guard
        if asyncio.iscoroutinefunction(func) or (
            hasattr(func, "__call__") and asyncio.iscoroutinefunction(func.__call__)
        ):
            self._async_guards.add(name)

    def is_async(self, name: str) -> bool:
        """Check if a guard is async.

        Args:
            name: Name of the guard.

        Returns:
            True if the guard is async, False otherwise.
        """
        return name in self._async_guards

    def unregister(self, name: str) -> None:
        """Unregister a guard function.

        Args:
            name: Name of the guard to remove.

        Raises:
            GuardNotFoundError: If guard is not registered.
        """
        if name not in self._guards:
            raise GuardNotFoundError(f"Guard '{name}' not found", guard_name=name)
        del self._guards[name]
        self._async_guards.discard(name)

    def get(self, name: str) -> AnyGuardFunc:
        """Get a guard function by name.

        Args:
            name: Name of the guard.

        Returns:
            The guard function (sync or async).

        Raises:
            GuardNotFoundError: If guard is not registered.
        """
        if name not in self._guards:
            raise GuardNotFoundError(f"Guard '{name}' not found", guard_name=name)
        return self._guards[name]

    def has(self, name: str) -> bool:
        """Check if a guard is registered.

        Args:
            name: Name of the guard.

        Returns:
            True if registered, False otherwise.
        """
        return name in self._guards

    def evaluate(self, name: str, context: dict[str, Any]) -> bool:
        """Evaluate a single guard.

        Args:
            name: Name of the guard to evaluate.
            context: Context dictionary for evaluation.

        Returns:
            Guard evaluation result.

        Raises:
            GuardNotFoundError: If guard is not registered.
        """
        func = self.get(name)
        return func(context)

    def evaluate_all(
        self,
        guards: tuple[str, ...] | list[str],
        context: dict[str, Any],
        fail_fast: bool = True,
    ) -> GuardResult:
        """Evaluate multiple guards.

        Args:
            guards: Sequence of guard names to evaluate.
            context: Context dictionary for evaluation.
            fail_fast: If True, stop on first failure. If False, evaluate all.

        Returns:
            GuardResult with evaluation details.

        Raises:
            GuardNotFoundError: If any guard is not registered.
        """
        if not guards:
            return GuardResult.success()

        evaluated: list[tuple[str, bool]] = []

        for guard_name in guards:
            result = self.evaluate(guard_name, context)
            evaluated.append((guard_name, result))

            if not result:
                if fail_fast:
                    return GuardResult.failure(guard_name, evaluated=evaluated)

        # Check if any failed (when not fail_fast)
        for name, passed in evaluated:
            if not passed:
                return GuardResult.failure(name, evaluated=evaluated)

        return GuardResult.success(evaluated)

    async def async_evaluate(self, name: str, context: dict[str, Any]) -> bool:
        """Evaluate a single guard asynchronously.

        Works with both sync and async guards. Sync guards are called directly,
        async guards are awaited.

        Args:
            name: Name of the guard to evaluate.
            context: Context dictionary for evaluation.

        Returns:
            Guard evaluation result.

        Raises:
            GuardNotFoundError: If guard is not registered.
        """
        func = self.get(name)
        if self.is_async(name):
            return await func(context)  # type: ignore[misc]
        else:
            return func(context)  # type: ignore[return-value]

    async def async_evaluate_all(
        self,
        guards: tuple[str, ...] | list[str],
        context: dict[str, Any],
        fail_fast: bool = True,
    ) -> GuardResult:
        """Evaluate multiple guards asynchronously.

        Works with both sync and async guards.

        Args:
            guards: Sequence of guard names to evaluate.
            context: Context dictionary for evaluation.
            fail_fast: If True, stop on first failure. If False, evaluate all.

        Returns:
            GuardResult with evaluation details.

        Raises:
            GuardNotFoundError: If any guard is not registered.
        """
        if not guards:
            return GuardResult.success()

        evaluated: list[tuple[str, bool]] = []

        for guard_name in guards:
            result = await self.async_evaluate(guard_name, context)
            evaluated.append((guard_name, result))

            if not result:
                if fail_fast:
                    return GuardResult.failure(guard_name, evaluated=evaluated)

        # Check if any failed (when not fail_fast)
        for name, passed in evaluated:
            if not passed:
                return GuardResult.failure(name, evaluated=evaluated)

        return GuardResult.success(evaluated)

    def has_async_guards(self, guards: tuple[str, ...] | list[str]) -> bool:
        """Check if any of the given guards are async.

        Args:
            guards: Sequence of guard names to check.

        Returns:
            True if any guard is async, False otherwise.
        """
        return any(self.is_async(name) for name in guards if name in self._guards)

    def list_guards(self) -> list[str]:
        """List all registered guard names.

        Returns:
            List of guard names.
        """
        return list(self._guards.keys())

    def clear(self) -> None:
        """Remove all registered guards."""
        self._guards.clear()
        self._async_guards.clear()

    def __len__(self) -> int:
        """Return number of registered guards."""
        return len(self._guards)

    def __contains__(self, name: str) -> bool:
        """Check if guard is registered."""
        return name in self._guards

    def decorator(
        self, name: str | None = None
    ) -> Callable[[AnyGuardFunc], AnyGuardFunc]:
        """Decorator to register a guard function (sync or async).

        Args:
            name: Optional name for the guard. If None, uses function name.

        Returns:
            Decorator function.

        Example:
            >>> registry = GuardRegistry()
            >>> @registry.decorator()
            ... def is_valid(ctx: dict) -> bool:
            ...     return ctx.get("valid", False)
            >>>
            >>> @registry.decorator("check_balance")
            ... async def check_balance_async(ctx: dict) -> bool:
            ...     balance = await get_balance(ctx["account_id"])
            ...     return balance >= ctx["amount"]
        """

        def decorator_inner(func: AnyGuardFunc) -> AnyGuardFunc:
            guard_name = name or func.__name__
            self.register(guard_name, func)
            return func

        return decorator_inner
