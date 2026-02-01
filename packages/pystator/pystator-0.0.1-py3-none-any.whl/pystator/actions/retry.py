"""Action retry mechanism for PyStator FSM.

Provides configurable retry policies with exponential backoff for failed actions.
"""

from __future__ import annotations

import asyncio
import logging
import random
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, TypeVar

from pystator.actions.registry import ActionRegistry, ActionResult

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass(frozen=True)
class RetryPolicy:
    """Configuration for action retry behavior.

    Attributes:
        max_attempts: Maximum number of attempts (including initial attempt).
        base_delay: Base delay in seconds between retries.
        max_delay: Maximum delay in seconds (caps exponential growth).
        exponential_base: Base for exponential backoff (delay = base_delay * base^attempt).
        jitter: If True, add random jitter to delays (prevents thundering herd).
        jitter_factor: Maximum jitter as fraction of delay (0.0 to 1.0).
        retryable_exceptions: Tuple of exception types that should trigger retry.
            Default is (Exception,) which retries all exceptions.
            Set to specific exceptions like (ConnectionError, TimeoutError) for finer control.
    """

    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    exponential_base: float = 2.0
    jitter: bool = True
    jitter_factor: float = 0.25
    retryable_exceptions: tuple[type[Exception], ...] = (Exception,)

    def __post_init__(self) -> None:
        """Validate retry policy parameters."""
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        if self.base_delay < 0:
            raise ValueError("base_delay must be non-negative")
        if self.max_delay < self.base_delay:
            raise ValueError("max_delay must be >= base_delay")
        if self.exponential_base < 1:
            raise ValueError("exponential_base must be >= 1")
        if not 0 <= self.jitter_factor <= 1:
            raise ValueError("jitter_factor must be between 0 and 1")

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: Zero-based attempt number (0 = first retry after initial failure).

        Returns:
            Delay in seconds (with optional jitter applied).
        """
        # Exponential backoff
        delay = self.base_delay * (self.exponential_base ** attempt)

        # Cap at max_delay
        delay = min(delay, self.max_delay)

        # Add jitter
        if self.jitter and delay > 0:
            jitter_amount = delay * self.jitter_factor * random.random()
            delay = delay + jitter_amount

        return delay

    def is_retryable(self, exception: Exception) -> bool:
        """Check if an exception should trigger a retry.

        Args:
            exception: The exception that occurred.

        Returns:
            True if the exception is retryable, False otherwise.
        """
        return isinstance(exception, self.retryable_exceptions)

    @classmethod
    def no_retry(cls) -> "RetryPolicy":
        """Create a policy with no retries (single attempt)."""
        return cls(max_attempts=1)

    @classmethod
    def aggressive(cls) -> "RetryPolicy":
        """Create an aggressive retry policy (many attempts, short delays)."""
        return cls(
            max_attempts=10,
            base_delay=0.1,
            max_delay=5.0,
            exponential_base=1.5,
        )

    @classmethod
    def conservative(cls) -> "RetryPolicy":
        """Create a conservative retry policy (few attempts, longer delays)."""
        return cls(
            max_attempts=3,
            base_delay=5.0,
            max_delay=120.0,
            exponential_base=2.0,
        )


@dataclass
class RetryResult:
    """Result of executing an action with retry.

    Attributes:
        success: Whether the action eventually succeeded.
        action_name: Name of the action.
        attempts: Number of attempts made.
        final_result: The final ActionResult (success or last failure).
        attempt_results: List of all attempt results.
        total_duration_ms: Total time spent including delays.
    """

    success: bool
    action_name: str
    attempts: int
    final_result: ActionResult
    attempt_results: list[ActionResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @property
    def total_duration_ms(self) -> float | None:
        """Get total duration in milliseconds."""
        if self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return delta.total_seconds() * 1000

    @property
    def retries(self) -> int:
        """Get number of retries (attempts - 1)."""
        return max(0, self.attempts - 1)


class RetryExecutor:
    """Executes actions with configurable retry behavior.

    The RetryExecutor wraps an ActionRegistry and provides automatic
    retry capability for failed actions.

    Example:
        >>> registry = ActionRegistry()
        >>> registry.register("send_notification", send_notification_func)
        >>>
        >>> policy = RetryPolicy(max_attempts=3, base_delay=1.0)
        >>> executor = RetryExecutor(registry, default_policy=policy)
        >>>
        >>> # Execute with retry
        >>> result = executor.execute_with_retry("send_notification", context)
        >>> if result.success:
        ...     print(f"Succeeded after {result.attempts} attempts")
        >>> else:
        ...     print(f"Failed after {result.attempts} attempts")
    """

    def __init__(
        self,
        registry: ActionRegistry,
        default_policy: RetryPolicy | None = None,
        log_retries: bool = True,
    ) -> None:
        """Initialize the retry executor.

        Args:
            registry: Action registry containing action functions.
            default_policy: Default retry policy for all actions.
            log_retries: If True, log retry attempts.
        """
        self.registry = registry
        self.default_policy = default_policy or RetryPolicy()
        self.log_retries = log_retries
        self._action_policies: dict[str, RetryPolicy] = {}

    def set_policy(self, action_name: str, policy: RetryPolicy) -> None:
        """Set a specific retry policy for an action.

        Args:
            action_name: Name of the action.
            policy: Retry policy for this action.
        """
        self._action_policies[action_name] = policy

    def get_policy(self, action_name: str) -> RetryPolicy:
        """Get the retry policy for an action.

        Args:
            action_name: Name of the action.

        Returns:
            Action-specific policy or default policy.
        """
        return self._action_policies.get(action_name, self.default_policy)

    def execute_with_retry(
        self,
        action_name: str,
        context: dict[str, Any],
        policy: RetryPolicy | None = None,
    ) -> RetryResult:
        """Execute an action with retry (synchronous).

        Args:
            action_name: Name of the action to execute.
            context: Context dictionary for execution.
            policy: Optional override policy for this execution.

        Returns:
            RetryResult with execution details.
        """
        import time

        effective_policy = policy or self.get_policy(action_name)
        result = RetryResult(
            success=False,
            action_name=action_name,
            attempts=0,
            final_result=ActionResult.fail(action_name, Exception("Not executed")),
            started_at=datetime.now(timezone.utc),
        )

        for attempt in range(effective_policy.max_attempts):
            result.attempts = attempt + 1

            action_result = self.registry.execute(action_name, context)
            result.attempt_results.append(action_result)

            if action_result.success:
                result.success = True
                result.final_result = action_result
                break

            # Check if we should retry
            if action_result.error and not effective_policy.is_retryable(action_result.error):
                if self.log_retries:
                    logger.info(
                        f"Action '{action_name}' failed with non-retryable error: "
                        f"{action_result.error}"
                    )
                result.final_result = action_result
                break

            # If this was the last attempt, don't sleep
            if attempt + 1 >= effective_policy.max_attempts:
                result.final_result = action_result
                break

            # Calculate and apply delay
            delay = effective_policy.calculate_delay(attempt)
            if self.log_retries:
                logger.info(
                    f"Action '{action_name}' failed (attempt {attempt + 1}/"
                    f"{effective_policy.max_attempts}), retrying in {delay:.2f}s: "
                    f"{action_result.error}"
                )
            time.sleep(delay)

        result.completed_at = datetime.now(timezone.utc)

        if self.log_retries:
            if result.success:
                logger.info(
                    f"Action '{action_name}' succeeded after {result.attempts} attempt(s)"
                )
            else:
                logger.warning(
                    f"Action '{action_name}' failed after {result.attempts} attempt(s)"
                )

        return result

    async def async_execute_with_retry(
        self,
        action_name: str,
        context: dict[str, Any],
        policy: RetryPolicy | None = None,
    ) -> RetryResult:
        """Execute an action with retry (asynchronous).

        Works with both sync and async actions.

        Args:
            action_name: Name of the action to execute.
            context: Context dictionary for execution.
            policy: Optional override policy for this execution.

        Returns:
            RetryResult with execution details.
        """
        effective_policy = policy or self.get_policy(action_name)
        result = RetryResult(
            success=False,
            action_name=action_name,
            attempts=0,
            final_result=ActionResult.fail(action_name, Exception("Not executed")),
            started_at=datetime.now(timezone.utc),
        )

        for attempt in range(effective_policy.max_attempts):
            result.attempts = attempt + 1

            action_result = await self.registry.async_execute(action_name, context)
            result.attempt_results.append(action_result)

            if action_result.success:
                result.success = True
                result.final_result = action_result
                break

            # Check if we should retry
            if action_result.error and not effective_policy.is_retryable(action_result.error):
                if self.log_retries:
                    logger.info(
                        f"Action '{action_name}' failed with non-retryable error: "
                        f"{action_result.error}"
                    )
                result.final_result = action_result
                break

            # If this was the last attempt, don't sleep
            if attempt + 1 >= effective_policy.max_attempts:
                result.final_result = action_result
                break

            # Calculate and apply delay
            delay = effective_policy.calculate_delay(attempt)
            if self.log_retries:
                logger.info(
                    f"Action '{action_name}' failed (attempt {attempt + 1}/"
                    f"{effective_policy.max_attempts}), retrying in {delay:.2f}s: "
                    f"{action_result.error}"
                )
            await asyncio.sleep(delay)

        result.completed_at = datetime.now(timezone.utc)

        if self.log_retries:
            if result.success:
                logger.info(
                    f"Action '{action_name}' succeeded after {result.attempts} attempt(s)"
                )
            else:
                logger.warning(
                    f"Action '{action_name}' failed after {result.attempts} attempt(s)"
                )

        return result

    def execute_all_with_retry(
        self,
        actions: list[str] | tuple[str, ...],
        context: dict[str, Any],
        stop_on_error: bool = False,
    ) -> list[RetryResult]:
        """Execute multiple actions with retry (synchronous).

        Args:
            actions: Sequence of action names to execute.
            context: Context dictionary for execution.
            stop_on_error: If True, stop on first action that fails all retries.

        Returns:
            List of RetryResult objects.
        """
        results: list[RetryResult] = []

        for action_name in actions:
            result = self.execute_with_retry(action_name, context)
            results.append(result)

            if not result.success and stop_on_error:
                break

        return results

    async def async_execute_all_with_retry(
        self,
        actions: list[str] | tuple[str, ...],
        context: dict[str, Any],
        stop_on_error: bool = False,
    ) -> list[RetryResult]:
        """Execute multiple actions with retry (asynchronous).

        Args:
            actions: Sequence of action names to execute.
            context: Context dictionary for execution.
            stop_on_error: If True, stop on first action that fails all retries.

        Returns:
            List of RetryResult objects.
        """
        results: list[RetryResult] = []

        for action_name in actions:
            result = await self.async_execute_with_retry(action_name, context)
            results.append(result)

            if not result.success and stop_on_error:
                break

        return results
