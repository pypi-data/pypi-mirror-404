"""Exception hierarchy for PyStator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class FSMError(Exception):
    """Base exception for all PyStator errors.

    All PyStator exceptions inherit from this class, making it easy
    to catch any FSM-related error with a single except clause.

    Attributes:
        message: Human-readable error description.
        context: Additional context about the error.
    """

    def __init__(self, message: str, context: dict[str, Any] | None = None) -> None:
        self.message = message
        self.context = context or {}
        super().__init__(message)

    def __str__(self) -> str:
        if self.context:
            ctx_str = ", ".join(f"{k}={v!r}" for k, v in self.context.items())
            return f"{self.message} ({ctx_str})"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Serialize error to dictionary."""
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "context": self.context,
        }


class ConfigurationError(FSMError):
    """Error in FSM configuration (YAML/JSON schema).

    Raised when the FSM definition is invalid, such as:
    - Invalid YAML/JSON syntax
    - Schema validation failures
    - Missing required fields
    - Invalid state or transition definitions
    """

    def __init__(
        self,
        message: str,
        path: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        if path:
            ctx["path"] = path
        super().__init__(message, ctx)
        self.path = path


class InvalidTransitionError(FSMError):
    """Transition is not allowed from the current state.

    Raised when attempting a transition that is not defined for the
    current state, or when the transition exists but is blocked.

    Attributes:
        current_state: The state from which the transition was attempted.
        trigger: The event that triggered the attempted transition.
    """

    def __init__(
        self,
        message: str,
        current_state: str,
        trigger: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        ctx.update({"current_state": current_state, "trigger": trigger})
        super().__init__(message, ctx)
        self.current_state = current_state
        self.trigger = trigger


class GuardRejectedError(InvalidTransitionError):
    """Transition blocked by a guard condition.

    Raised when a transition exists but one or more guard functions
    returned False, preventing the transition.

    Attributes:
        guard_name: The name of the guard that rejected the transition.
        guard_result: Additional information about the guard evaluation.
    """

    def __init__(
        self,
        message: str,
        current_state: str,
        trigger: str,
        guard_name: str,
        guard_result: Any = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        ctx.update({"guard_name": guard_name, "guard_result": guard_result})
        super().__init__(message, current_state, trigger, ctx)
        self.guard_name = guard_name
        self.guard_result = guard_result


class UndefinedStateError(FSMError):
    """Reference to a state that is not defined in the machine.

    Raised when:
    - Processing an event from an undefined state
    - A transition references an undefined destination
    - Checking properties of a non-existent state
    """

    def __init__(
        self,
        message: str,
        state_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        ctx["state_name"] = state_name
        super().__init__(message, ctx)
        self.state_name = state_name


class UndefinedTriggerError(FSMError):
    """Event trigger not defined in the machine (strict mode only).

    Raised in strict mode when an event is received that has no
    matching transitions defined anywhere in the machine.

    Attributes:
        trigger: The undefined event trigger.
        available_triggers: List of valid triggers for reference.
    """

    def __init__(
        self,
        message: str,
        trigger: str,
        available_triggers: list[str] | None = None,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        ctx["trigger"] = trigger
        if available_triggers:
            ctx["available_triggers"] = available_triggers
        super().__init__(message, ctx)
        self.trigger = trigger
        self.available_triggers = available_triggers or []


class TimeoutExpiredError(FSMError):
    """State timeout has expired.

    Raised when checking timeout status and the configured duration
    has been exceeded.

    Attributes:
        state_name: The state that timed out.
        timeout_seconds: The configured timeout duration.
        elapsed_seconds: How long the entity was in the state.
    """

    def __init__(
        self,
        message: str,
        state_name: str,
        timeout_seconds: float,
        elapsed_seconds: float,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        ctx.update(
            {
                "state_name": state_name,
                "timeout_seconds": timeout_seconds,
                "elapsed_seconds": elapsed_seconds,
            }
        )
        super().__init__(message, ctx)
        self.state_name = state_name
        self.timeout_seconds = timeout_seconds
        self.elapsed_seconds = elapsed_seconds


class GuardNotFoundError(FSMError):
    """Guard function not registered.

    Raised when a transition references a guard that has not been
    registered in the GuardRegistry.
    """

    def __init__(
        self,
        message: str,
        guard_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        ctx["guard_name"] = guard_name
        super().__init__(message, ctx)
        self.guard_name = guard_name


class ActionNotFoundError(FSMError):
    """Action function not registered.

    Raised when a transition or state references an action that has
    not been registered in the ActionRegistry.
    """

    def __init__(
        self,
        message: str,
        action_name: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        ctx = context or {}
        ctx["action_name"] = action_name
        super().__init__(message, ctx)
        self.action_name = action_name


class TerminalStateError(InvalidTransitionError):
    """Attempted to transition from a terminal state.

    Terminal states are end states - no outbound transitions are allowed.
    """

    def __init__(
        self,
        current_state: str,
        trigger: str,
        context: dict[str, Any] | None = None,
    ) -> None:
        message = f"Cannot transition from terminal state '{current_state}'"
        super().__init__(message, current_state, trigger, context)


@dataclass
class ErrorPolicy:
    """Configuration for error handling behavior.

    Defines how the FSM should handle errors during transition
    processing.

    Attributes:
        default_fallback: State to transition to on unhandled errors.
        retry_attempts: Number of retries before falling back.
        strict_mode: If True, undefined triggers raise errors.
    """

    default_fallback: str | None = None
    retry_attempts: int = 0
    strict_mode: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def should_fallback(self, error: FSMError) -> bool:
        """Determine if error should trigger fallback transition."""
        return self.default_fallback is not None
