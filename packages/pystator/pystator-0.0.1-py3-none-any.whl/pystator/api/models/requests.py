"""Request models for PyStator API."""

from typing import Any

from pydantic import BaseModel, Field


class ProcessRequest(BaseModel):
    """Request body for processing an FSM event."""

    config: dict[str, Any] = Field(
        ...,
        description="FSM configuration (meta, states, transitions, optional error_policy)",
    )
    current_state: str = Field(
        ...,
        description="Current state name of the entity",
    )
    trigger: str = Field(
        ...,
        description="Event trigger name",
    )
    context: dict[str, Any] | None = Field(
        default=None,
        description="Runtime context for guards (e.g. fill_qty, order_qty)",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "config": {
                    "meta": {"machine_name": "order", "version": "1.0"},
                    "states": [
                        {"name": "OPEN", "type": "initial"},
                        {"name": "FILLED", "type": "terminal"},
                    ],
                    "transitions": [
                        {"trigger": "fill", "source": "OPEN", "dest": "FILLED"},
                    ],
                },
                "current_state": "OPEN",
                "trigger": "fill",
                "context": {"fill_qty": 100, "order_qty": 100},
            }
        }
    }


class MachineCreateRequest(BaseModel):
    """Request body for creating/storing an FSM machine in the database."""

    config: dict[str, Any] = Field(
        ...,
        description="Full FSM configuration (meta, states, transitions, error_policy)",
    )


class MachineUpdateRequest(BaseModel):
    """Request body for updating an FSM machine."""

    config: dict[str, Any] = Field(
        ...,
        description="Full FSM configuration to replace existing",
    )


class ValidateRequest(BaseModel):
    """Request body for validating FSM config."""

    config: dict[str, Any] = Field(
        ...,
        description="FSM configuration to validate",
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "config": {
                    "meta": {"machine_name": "order", "version": "1.0"},
                    "states": [
                        {"name": "OPEN", "type": "initial"},
                        {"name": "FILLED", "type": "terminal"},
                    ],
                    "transitions": [
                        {"trigger": "fill", "source": "OPEN", "dest": "FILLED"},
                    ],
                },
            }
        }
    }
