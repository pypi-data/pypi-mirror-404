"""Observability hooks for PyStator FSM.

Provides hooks for metrics, tracing, and logging integration.
"""

from __future__ import annotations

import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Protocol, TYPE_CHECKING, runtime_checkable

if TYPE_CHECKING:
    from pystator.core.event import Event
    from pystator.core.transition import TransitionResult

logger = logging.getLogger(__name__)


@dataclass
class TransitionMetrics:
    """Metrics for a single transition.

    Attributes:
        source_state: State before transition.
        target_state: State after transition (or same if failed).
        trigger: Event trigger that caused the transition.
        success: Whether transition succeeded.
        duration_ms: Time taken for transition computation.
        guards_evaluated: Number of guards evaluated.
        guards_passed: Number of guards that passed.
        timestamp: When the transition occurred.
        machine_name: Name of the state machine.
        metadata: Additional context.
    """

    source_state: str
    target_state: str
    trigger: str
    success: bool
    duration_ms: float
    guards_evaluated: int = 0
    guards_passed: int = 0
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    machine_name: str = "unknown"
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class TransitionHook(Protocol):
    """Protocol for transition lifecycle hooks.

    Implement this protocol to receive notifications about transitions.
    """

    def on_transition_start(
        self,
        current_state: str,
        trigger: str,
        context: dict[str, Any],
    ) -> None:
        """Called before transition computation begins.

        Args:
            current_state: The current state.
            trigger: The event trigger.
            context: The context dictionary.
        """
        ...

    def on_transition_complete(
        self,
        result: "TransitionResult",
        duration_ms: float,
        context: dict[str, Any],
    ) -> None:
        """Called after transition computation completes.

        Args:
            result: The transition result.
            duration_ms: Time taken for the transition.
            context: The context dictionary.
        """
        ...

    def on_transition_error(
        self,
        error: Exception,
        current_state: str,
        trigger: str,
        context: dict[str, Any],
    ) -> None:
        """Called when transition computation raises an exception.

        Args:
            error: The exception that was raised.
            current_state: The current state.
            trigger: The event trigger.
            context: The context dictionary.
        """
        ...


class LoggingHook:
    """Transition hook that logs transition details.

    Example:
        >>> hook = LoggingHook(log_level=logging.INFO)
        >>> observer = TransitionObserver()
        >>> observer.add_hook(hook)
    """

    def __init__(
        self,
        log_level: int = logging.DEBUG,
        logger_name: str = "pystator.transitions",
    ) -> None:
        """Initialize the logging hook.

        Args:
            log_level: Log level for transition messages.
            logger_name: Name of the logger to use.
        """
        self.log_level = log_level
        self.logger = logging.getLogger(logger_name)

    def on_transition_start(
        self,
        current_state: str,
        trigger: str,
        context: dict[str, Any],
    ) -> None:
        """Log transition start."""
        self.logger.log(
            self.log_level,
            "Transition starting: state=%s trigger=%s",
            current_state,
            trigger,
        )

    def on_transition_complete(
        self,
        result: "TransitionResult",
        duration_ms: float,
        context: dict[str, Any],
    ) -> None:
        """Log transition completion."""
        if result.success:
            self.logger.log(
                self.log_level,
                "Transition completed: %s -> %s (trigger=%s, duration=%.2fms)",
                result.source_state,
                result.target_state,
                result.trigger,
                duration_ms,
            )
        else:
            self.logger.log(
                self.log_level,
                "Transition failed: state=%s trigger=%s error=%s (duration=%.2fms)",
                result.source_state,
                result.trigger,
                result.error,
                duration_ms,
            )

    def on_transition_error(
        self,
        error: Exception,
        current_state: str,
        trigger: str,
        context: dict[str, Any],
    ) -> None:
        """Log transition error."""
        self.logger.exception(
            "Transition error: state=%s trigger=%s error=%s",
            current_state,
            trigger,
            error,
        )


class MetricsCollector:
    """Collects and aggregates transition metrics.

    Provides counters and histograms for transition statistics.

    Example:
        >>> collector = MetricsCollector()
        >>> observer = TransitionObserver()
        >>> observer.add_hook(collector)
        >>>
        >>> # After some transitions...
        >>> print(collector.get_summary())
    """

    def __init__(self) -> None:
        """Initialize the metrics collector."""
        self._transitions: list[TransitionMetrics] = []
        self._counters: dict[str, int] = {
            "total": 0,
            "success": 0,
            "failure": 0,
            "errors": 0,
        }
        self._by_trigger: dict[str, int] = {}
        self._by_source_state: dict[str, int] = {}
        self._by_target_state: dict[str, int] = {}
        self._durations: list[float] = []

    def on_transition_start(
        self,
        current_state: str,
        trigger: str,
        context: dict[str, Any],
    ) -> None:
        """Track transition start."""
        pass  # Metrics are collected on complete

    def on_transition_complete(
        self,
        result: "TransitionResult",
        duration_ms: float,
        context: dict[str, Any],
    ) -> None:
        """Collect metrics for completed transition."""
        self._counters["total"] += 1

        if result.success:
            self._counters["success"] += 1
        else:
            self._counters["failure"] += 1

        # Track by trigger
        self._by_trigger[result.trigger] = self._by_trigger.get(result.trigger, 0) + 1

        # Track by state
        self._by_source_state[result.source_state] = (
            self._by_source_state.get(result.source_state, 0) + 1
        )
        if result.success:
            self._by_target_state[result.target_state] = (
                self._by_target_state.get(result.target_state, 0) + 1
            )

        # Track duration
        self._durations.append(duration_ms)

        # Store full metrics
        metrics = TransitionMetrics(
            source_state=result.source_state,
            target_state=result.target_state,
            trigger=result.trigger,
            success=result.success,
            duration_ms=duration_ms,
        )
        self._transitions.append(metrics)

    def on_transition_error(
        self,
        error: Exception,
        current_state: str,
        trigger: str,
        context: dict[str, Any],
    ) -> None:
        """Track transition error."""
        self._counters["errors"] += 1

    def get_summary(self) -> dict[str, Any]:
        """Get summary of collected metrics.

        Returns:
            Dictionary with aggregated statistics.
        """
        total = self._counters["total"]
        success_rate = self._counters["success"] / total if total > 0 else 0.0

        duration_stats = {}
        if self._durations:
            sorted_durations = sorted(self._durations)
            duration_stats = {
                "min_ms": min(self._durations),
                "max_ms": max(self._durations),
                "avg_ms": sum(self._durations) / len(self._durations),
                "p50_ms": sorted_durations[len(sorted_durations) // 2],
                "p95_ms": sorted_durations[int(len(sorted_durations) * 0.95)],
                "p99_ms": sorted_durations[int(len(sorted_durations) * 0.99)],
            }

        return {
            "total_transitions": total,
            "successful": self._counters["success"],
            "failed": self._counters["failure"],
            "errors": self._counters["errors"],
            "success_rate": success_rate,
            "by_trigger": dict(self._by_trigger),
            "by_source_state": dict(self._by_source_state),
            "by_target_state": dict(self._by_target_state),
            "duration": duration_stats,
        }

    def reset(self) -> None:
        """Reset all collected metrics."""
        self._transitions.clear()
        self._counters = {"total": 0, "success": 0, "failure": 0, "errors": 0}
        self._by_trigger.clear()
        self._by_source_state.clear()
        self._by_target_state.clear()
        self._durations.clear()


class TransitionObserver:
    """Manages transition lifecycle hooks.

    Coordinates multiple hooks and provides timing measurements.

    Example:
        >>> observer = TransitionObserver()
        >>> observer.add_hook(LoggingHook())
        >>> observer.add_hook(MetricsCollector())
        >>>
        >>> # Wrap state machine processing
        >>> observer.before_transition("OPEN", "execution_report", context)
        >>> result = machine.process("OPEN", "execution_report", context)
        >>> observer.after_transition(result, context)
    """

    def __init__(self) -> None:
        """Initialize the observer."""
        self._hooks: list[TransitionHook] = []
        self._start_time: float | None = None
        self._current_state: str | None = None
        self._current_trigger: str | None = None

    def add_hook(self, hook: TransitionHook) -> "TransitionObserver":
        """Add a transition hook.

        Args:
            hook: Hook to add.

        Returns:
            Self for method chaining.
        """
        self._hooks.append(hook)
        return self

    def remove_hook(self, hook: TransitionHook) -> None:
        """Remove a transition hook.

        Args:
            hook: Hook to remove.
        """
        self._hooks.remove(hook)

    def before_transition(
        self,
        current_state: str,
        trigger: str,
        context: dict[str, Any],
    ) -> None:
        """Call before processing a transition.

        Args:
            current_state: The current state.
            trigger: The event trigger.
            context: The context dictionary.
        """
        self._start_time = time.perf_counter()
        self._current_state = current_state
        self._current_trigger = trigger

        for hook in self._hooks:
            try:
                hook.on_transition_start(current_state, trigger, context)
            except Exception as e:
                logger.warning("Hook on_transition_start failed: %s", e)

    def after_transition(
        self,
        result: "TransitionResult",
        context: dict[str, Any],
    ) -> None:
        """Call after processing a transition.

        Args:
            result: The transition result.
            context: The context dictionary.
        """
        duration_ms = 0.0
        if self._start_time is not None:
            duration_ms = (time.perf_counter() - self._start_time) * 1000
            self._start_time = None

        for hook in self._hooks:
            try:
                hook.on_transition_complete(result, duration_ms, context)
            except Exception as e:
                logger.warning("Hook on_transition_complete failed: %s", e)

    def on_error(
        self,
        error: Exception,
        context: dict[str, Any],
    ) -> None:
        """Call when transition raises an exception.

        Args:
            error: The exception that was raised.
            context: The context dictionary.
        """
        current_state = self._current_state or "unknown"
        trigger = self._current_trigger or "unknown"

        for hook in self._hooks:
            try:
                hook.on_transition_error(error, current_state, trigger, context)
            except Exception as e:
                logger.warning("Hook on_transition_error failed: %s", e)


# Callback-based alternative for simpler use cases

TransitionCallback = Callable[["TransitionResult", float, dict[str, Any]], None]


def with_timing(
    callback: TransitionCallback,
) -> Callable[[Callable[..., "TransitionResult"]], Callable[..., "TransitionResult"]]:
    """Decorator that adds timing and callback to transition processing.

    Example:
        >>> def log_transition(result, duration_ms, context):
        ...     print(f"Transition took {duration_ms:.2f}ms")
        >>>
        >>> @with_timing(log_transition)
        >>> def my_process(machine, state, trigger, context):
        ...     return machine.process(state, trigger, context)
    """

    def decorator(
        func: Callable[..., "TransitionResult"],
    ) -> Callable[..., "TransitionResult"]:
        def wrapper(*args: Any, **kwargs: Any) -> "TransitionResult":
            start = time.perf_counter()
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start) * 1000

            # Extract context from kwargs or use empty dict
            context = kwargs.get("context", {})

            try:
                callback(result, duration_ms, context)
            except Exception as e:
                logger.warning("Timing callback failed: %s", e)

            return result

        return wrapper

    return decorator
