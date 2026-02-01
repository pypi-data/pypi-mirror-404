"""Timeout tracking and management for PyStator FSM."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

from pystator.core.errors import TimeoutExpiredError, UndefinedStateError
from pystator.core.transition import TransitionResult

if TYPE_CHECKING:
    from pystator.core.machine import StateMachine


@dataclass(frozen=True)
class TimeoutInfo:
    """Information about a state's timeout configuration.

    Attributes:
        state_name: Name of the state.
        has_timeout: Whether the state has a timeout configured.
        timeout_seconds: Timeout duration (None if no timeout).
        destination: Target state on timeout (None if no timeout).
        entered_at: When the state was entered (None if not provided).
        expires_at: When the timeout expires (None if no timeout or entered_at).
        is_expired: Whether the timeout has expired.
        remaining_seconds: Seconds until expiry (None if expired or no timeout).
    """

    state_name: str
    has_timeout: bool
    timeout_seconds: float | None = None
    destination: str | None = None
    entered_at: datetime | None = None
    expires_at: datetime | None = None
    is_expired: bool = False
    remaining_seconds: float | None = None

    @classmethod
    def no_timeout(cls, state_name: str) -> "TimeoutInfo":
        """Create info for a state without timeout."""
        return cls(state_name=state_name, has_timeout=False)

    @classmethod
    def with_timeout(
        cls,
        state_name: str,
        timeout_seconds: float,
        destination: str,
        entered_at: datetime | None = None,
        now: datetime | None = None,
    ) -> "TimeoutInfo":
        """Create info for a state with timeout.

        Args:
            state_name: Name of the state.
            timeout_seconds: Timeout duration in seconds.
            destination: Target state on timeout.
            entered_at: When the state was entered.
            now: Current time (defaults to UTC now).

        Returns:
            TimeoutInfo with computed expiry information.
        """
        if now is None:
            now = datetime.now(timezone.utc)

        expires_at = None
        is_expired = False
        remaining_seconds = None

        if entered_at is not None:
            # Ensure entered_at has timezone info
            if entered_at.tzinfo is None:
                entered_at = entered_at.replace(tzinfo=timezone.utc)

            expires_at = entered_at + timedelta(seconds=timeout_seconds)
            elapsed = (now - entered_at).total_seconds()
            is_expired = elapsed >= timeout_seconds
            remaining_seconds = max(0.0, timeout_seconds - elapsed) if not is_expired else None

        return cls(
            state_name=state_name,
            has_timeout=True,
            timeout_seconds=timeout_seconds,
            destination=destination,
            entered_at=entered_at,
            expires_at=expires_at,
            is_expired=is_expired,
            remaining_seconds=remaining_seconds,
        )


class TimeoutManager:
    """Manages timeout checking for state machine states.

    The TimeoutManager provides utilities for checking and handling
    state timeouts. It does NOT track time internally - timing data
    must be provided externally (from your database, cache, etc.).

    This design maintains PyStator's stateless architecture:
    - You track when entities enter states
    - You call the manager to check if timeouts have expired
    - You handle the timeout transitions in your application

    Example:
        >>> manager = TimeoutManager(machine)
        >>>
        >>> # Check for timeout
        >>> info = manager.get_timeout_info("PENDING_NEW", entered_at)
        >>> if info.is_expired:
        ...     result = manager.create_timeout_transition("PENDING_NEW", entered_at)
        ...     if result.success:
        ...         db.update_state(order_id, result.target_state)
    """

    def __init__(self, machine: "StateMachine") -> None:
        """Initialize the timeout manager.

        Args:
            machine: The state machine to manage timeouts for.
        """
        self.machine = machine

    def get_timeout_info(
        self,
        state_name: str,
        entered_at: datetime | None = None,
        now: datetime | None = None,
    ) -> TimeoutInfo:
        """Get timeout information for a state.

        Args:
            state_name: Name of the state to check.
            entered_at: When the state was entered.
            now: Current time (defaults to UTC now).

        Returns:
            TimeoutInfo with timeout details.

        Raises:
            UndefinedStateError: If state is not defined.
        """
        state = self.machine.get_state(state_name)

        if state.timeout is None:
            return TimeoutInfo.no_timeout(state_name)

        return TimeoutInfo.with_timeout(
            state_name=state_name,
            timeout_seconds=state.timeout.seconds,
            destination=state.timeout.destination,
            entered_at=entered_at,
            now=now,
        )

    def check_timeout(
        self,
        state_name: str,
        entered_at: datetime,
        now: datetime | None = None,
        raise_on_expired: bool = False,
    ) -> TimeoutInfo:
        """Check if a state's timeout has expired.

        Args:
            state_name: Name of the state to check.
            entered_at: When the state was entered.
            now: Current time (defaults to UTC now).
            raise_on_expired: If True, raise TimeoutExpiredError when expired.

        Returns:
            TimeoutInfo with current status.

        Raises:
            UndefinedStateError: If state is not defined.
            TimeoutExpiredError: If raise_on_expired=True and timeout expired.
        """
        info = self.get_timeout_info(state_name, entered_at, now)

        if raise_on_expired and info.is_expired:
            elapsed = info.timeout_seconds  # We know it's >= timeout
            if info.entered_at and info.timeout_seconds:
                if now is None:
                    now = datetime.now(timezone.utc)
                if info.entered_at.tzinfo is None:
                    entered_at_tz = info.entered_at.replace(tzinfo=timezone.utc)
                else:
                    entered_at_tz = info.entered_at
                elapsed = (now - entered_at_tz).total_seconds()

            raise TimeoutExpiredError(
                f"State '{state_name}' timeout expired",
                state_name=state_name,
                timeout_seconds=info.timeout_seconds or 0.0,
                elapsed_seconds=elapsed or 0.0,
            )

        return info

    def create_timeout_transition(
        self,
        state_name: str,
        entered_at: datetime,
        now: datetime | None = None,
    ) -> TransitionResult:
        """Create a timeout transition result if timeout has expired.

        This method creates a TransitionResult for an automatic timeout
        transition. It should only be called when you've determined that
        a timeout has occurred.

        Args:
            state_name: Name of the current state.
            entered_at: When the state was entered.
            now: Current time (defaults to UTC now).

        Returns:
            TransitionResult for the timeout transition.
            Returns failure result if no timeout configured or not expired.
        """
        info = self.get_timeout_info(state_name, entered_at, now)

        if not info.has_timeout:
            return TransitionResult.failure_result(
                source_state=state_name,
                trigger="_timeout",
                error=TimeoutExpiredError(
                    f"State '{state_name}' has no timeout configured",
                    state_name=state_name,
                    timeout_seconds=0.0,
                    elapsed_seconds=0.0,
                ),
                metadata={"reason": "no_timeout_configured"},
            )

        if not info.is_expired:
            return TransitionResult.failure_result(
                source_state=state_name,
                trigger="_timeout",
                error=TimeoutExpiredError(
                    f"State '{state_name}' timeout not yet expired",
                    state_name=state_name,
                    timeout_seconds=info.timeout_seconds or 0.0,
                    elapsed_seconds=0.0,
                ),
                metadata={
                    "reason": "not_expired",
                    "remaining_seconds": info.remaining_seconds,
                },
            )

        # Get source and target states for hooks
        source_state = self.machine.get_state(state_name)
        target_state = self.machine.get_state(info.destination or "")

        return TransitionResult.success_result(
            source_state=state_name,
            target_state=info.destination or "",
            trigger="_timeout",
            actions=(),  # Timeouts typically don't have actions
            on_exit=source_state.on_exit,
            on_enter=target_state.on_enter,
            metadata={
                "timeout_seconds": info.timeout_seconds,
                "entered_at": info.entered_at.isoformat() if info.entered_at else None,
                "expired_at": info.expires_at.isoformat() if info.expires_at else None,
            },
        )

    def get_states_with_timeouts(self) -> list[str]:
        """Get all state names that have timeouts configured.

        Returns:
            List of state names with timeouts.
        """
        return [
            state.name
            for state in self.machine.states.values()
            if state.has_timeout
        ]

    def get_shortest_timeout(self) -> float | None:
        """Get the shortest timeout duration across all states.

        Useful for setting up polling intervals.

        Returns:
            Shortest timeout in seconds, or None if no timeouts.
        """
        timeouts = [
            state.timeout.seconds
            for state in self.machine.states.values()
            if state.timeout is not None
        ]
        return min(timeouts) if timeouts else None


def check_timeout(
    machine: "StateMachine",
    state_name: str,
    entered_at: datetime,
    now: datetime | None = None,
) -> TransitionResult | None:
    """Check if timeout expired and return transition result if so.

    Convenience function for quick timeout checking.

    Args:
        machine: The state machine.
        state_name: Current state name.
        entered_at: When the state was entered.
        now: Current time (defaults to UTC now).

    Returns:
        TransitionResult if timeout expired, None otherwise.
    """
    manager = TimeoutManager(machine)
    info = manager.get_timeout_info(state_name, entered_at, now)

    if info.is_expired:
        return manager.create_timeout_transition(state_name, entered_at, now)

    return None


def get_timeout_info(
    machine: "StateMachine",
    state_name: str,
    entered_at: datetime | None = None,
    now: datetime | None = None,
) -> TimeoutInfo:
    """Get timeout information for a state.

    Convenience function for quick timeout info lookup.

    Args:
        machine: The state machine.
        state_name: State name to check.
        entered_at: When the state was entered.
        now: Current time (defaults to UTC now).

    Returns:
        TimeoutInfo with timeout details.
    """
    manager = TimeoutManager(machine)
    return manager.get_timeout_info(state_name, entered_at, now)
