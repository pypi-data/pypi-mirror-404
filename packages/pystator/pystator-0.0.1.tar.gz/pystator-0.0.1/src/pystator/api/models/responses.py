"""Response models for PyStator API."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class MachineResponse(BaseModel):
    """Response for a single stored FSM machine."""

    id: str = Field(..., description="Machine UUID")
    name: str = Field(..., description="Machine name from meta")
    version: str = Field(..., description="Machine version")
    description: str | None = Field(None, description="Machine description")
    strict_mode: bool = Field(True, description="Strict mode from meta")
    config: dict[str, Any] = Field(..., description="Full FSM config (meta, states, transitions, error_policy)")
    created_at: datetime | None = Field(None, description="Created timestamp")
    updated_at: datetime | None = Field(None, description="Updated timestamp")


class MachineListItem(BaseModel):
    """Summary item for machine list."""

    id: str = Field(..., description="Machine UUID")
    name: str = Field(..., description="Machine name")
    version: str = Field(..., description="Machine version")
    description: str | None = Field(None, description="Machine description")


class MachineListResponse(BaseModel):
    """Response for list machines."""

    machines: list[MachineListItem] = Field(default_factory=list)
    count: int = Field(0, description="Total count")


class ActionRef(BaseModel):
    """Action reference with optional params."""

    name: str = Field(..., description="Action name")
    params: dict[str, Any] = Field(default_factory=dict, description="Optional parameters")


class ProcessResponse(BaseModel):
    """Response for process endpoint."""

    success: bool = Field(..., description="Whether the transition succeeded")
    source_state: str = Field(..., description="State before transition")
    target_state: str | None = Field(None, description="State after transition (if success)")
    trigger: str = Field(..., description="Event trigger")
    actions_to_execute: list[ActionRef] = Field(
        default_factory=list,
        description="Transition actions to run after persistence",
    )
    on_exit_actions: list[ActionRef] = Field(
        default_factory=list,
        description="Source state exit actions",
    )
    on_enter_actions: list[ActionRef] = Field(
        default_factory=list,
        description="Target state entry actions",
    )
    error: dict[str, str] | None = Field(
        None,
        description="Error type and message if success is False",
    )
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "source_state": "OPEN",
                "target_state": "FILLED",
                "trigger": "fill",
                "actions_to_execute": [{"name": "update_positions"}],
                "on_exit_actions": [],
                "on_enter_actions": [],
                "error": None,
                "metadata": {},
            }
        }
    }


class MachineInfo(BaseModel):
    """Machine metadata from validated config."""

    machine_name: str = Field(..., description="Machine name")
    version: str = Field(..., description="Machine version")
    state_names: list[str] = Field(..., description="State names")
    trigger_names: list[str] = Field(..., description="Trigger names")
    terminal_states: list[str] = Field(..., description="Terminal state names")


class ValidateResponse(BaseModel):
    """Response for validate endpoint."""

    valid: bool = Field(..., description="Whether the config is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors if invalid")
    info: MachineInfo | None = Field(
        None,
        description="Machine info if valid",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "valid": True,
                "errors": [],
                "info": {
                    "machine_name": "order",
                    "version": "1.0",
                    "state_names": ["OPEN", "FILLED"],
                    "trigger_names": ["fill"],
                    "terminal_states": ["FILLED"],
                },
            }
        }
    }
