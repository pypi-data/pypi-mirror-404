"""Pydantic models for FSM configuration.

These models validate and parse YAML/JSON config into typed structures
before conversion to core State/Transition dataclasses.
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator


# -----------------------------------------------------------------------------
# Delay: int (ms) or str like "5s", "10m", "1h"
# -----------------------------------------------------------------------------

DelaySpec = int | str


# -----------------------------------------------------------------------------
# Meta
# -----------------------------------------------------------------------------


class MetaDef(BaseModel):
    """Top-level metadata."""
    version: str | None = None
    machine_name: str | None = None
    strict_mode: bool = True
    event_normalizer: Literal["lower", "upper"] | None = None
    description: str | None = None

    model_config = {"extra": "allow"}


# -----------------------------------------------------------------------------
# Timeout (state)
# -----------------------------------------------------------------------------


class TimeoutDef(BaseModel):
    """Timeout configuration for a state."""
    seconds: float = Field(..., gt=0)
    destination: str


# -----------------------------------------------------------------------------
# Invoke item (state)
# -----------------------------------------------------------------------------


class InvokeItemDef(BaseModel):
    """Invoked service ref."""
    id: str
    src: str
    on_done: str | None = None


# -----------------------------------------------------------------------------
# Region (parallel state)
# -----------------------------------------------------------------------------


class RegionDef(BaseModel):
    """Region within a parallel state."""
    name: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_.]*$")
    initial: str
    states: list[str] = Field(default_factory=list)
    description: str = ""

    model_config = {"extra": "allow"}


# -----------------------------------------------------------------------------
# State definition
# -----------------------------------------------------------------------------


class StateDef(BaseModel):
    """State definition from config."""
    name: str = Field(..., pattern=r"^[a-zA-Z][a-zA-Z0-9_.]*$")
    type: Literal["initial", "stable", "terminal", "error", "parallel"] = "stable"
    description: str = ""
    parent: str | None = None
    initial_child: str | None = None
    regions: list[RegionDef] = Field(default_factory=list)
    on_enter: str | list[str | dict[str, Any]] = Field(default_factory=list, alias="on_enter")
    on_exit: str | list[str | dict[str, Any]] = Field(default_factory=list, alias="on_exit")
    invoke: list[InvokeItemDef] = Field(default_factory=list)
    timeout: TimeoutDef | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow", "populate_by_name": True}

    @field_validator("on_enter", "on_exit", mode="before")
    @classmethod
    def _normalize_actions(cls, v: Any) -> list[str | dict[str, Any]]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, list):
            return list(v)
        return []


# -----------------------------------------------------------------------------
# Transition definition
# -----------------------------------------------------------------------------


class TransitionDef(BaseModel):
    """Transition definition from config."""
    trigger: str | None = None
    source: str | list[str]
    dest: str
    region: str | None = None
    guards: list[str | dict[str, Any]] = Field(default_factory=list)
    actions: list[str | dict[str, Any]] = Field(default_factory=list)
    after: DelaySpec | None = None
    description: str = ""
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"extra": "allow"}

    @field_validator("guards", "actions", mode="before")
    @classmethod
    def _normalize_to_list(cls, v: Any) -> list[Any]:
        if v is None:
            return []
        if isinstance(v, str):
            return [v]
        if isinstance(v, dict):
            return [v]
        if isinstance(v, list):
            return list(v)
        return []

    @model_validator(mode="after")
    def trigger_or_after(self) -> "TransitionDef":
        """Require either trigger or after."""
        has_trigger = bool(self.trigger and self.trigger.strip())
        has_after = self.after is not None
        if not has_trigger and not has_after:
            raise ValueError("Transition must have either 'trigger' or 'after'")
        return self


# -----------------------------------------------------------------------------
# Error policy, context, events (metadata)
# -----------------------------------------------------------------------------


class ErrorPolicyDef(BaseModel):
    """Error handling configuration."""
    default_fallback: str | None = None
    retry_attempts: int = Field(default=0, ge=0)

    model_config = {"extra": "allow"}


class ContextItemDef(BaseModel):
    """Documented context key (metadata only)."""
    key: str
    type: str | None = None
    description: str | None = None
    default: Any = None

    model_config = {"extra": "allow"}


class EventItemDef(BaseModel):
    """Documented event (metadata only)."""
    name: str
    description: str | None = None
    payload: dict[str, Any] | None = None

    model_config = {"extra": "allow"}


# -----------------------------------------------------------------------------
# Root config
# -----------------------------------------------------------------------------


class MachineConfig(BaseModel):
    """Root FSM configuration."""
    meta: MetaDef = Field(default_factory=MetaDef)
    states: list[StateDef]
    transitions: list[TransitionDef]
    error_policy: ErrorPolicyDef | dict[str, Any] | None = None
    context: list[ContextItemDef] | list[dict[str, Any]] | None = None
    events: list[EventItemDef] | list[dict[str, Any]] | None = None

    model_config = {"extra": "allow"}

    @field_validator("states")
    @classmethod
    def at_least_one_state(cls, v: list[StateDef]) -> list[StateDef]:
        if not v:
            raise ValueError("At least one state is required")
        return v
