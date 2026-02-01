"""Route handlers for FSM config validation, CRUD, and info."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from pystator.api.dependencies import get_db_session, get_fsm_service
from pystator.api.models.requests import MachineCreateRequest, MachineUpdateRequest, ValidateRequest
from pystator.api.models.responses import (
    MachineInfo,
    MachineListItem,
    MachineListResponse,
    MachineResponse,
    ValidateResponse,
)
from pystator.api.services.fsm_service import FSMService
from pystator.db.models import MachineModel

router = APIRouter()


def _config_to_meta(config: dict) -> dict:
    """Extract meta fields from full config for MachineModel."""
    meta = config.get("meta") or {}
    return {
        "name": meta.get("machine_name", "unnamed"),
        "version": meta.get("version", "1.0.0"),
        "description": meta.get("description") or "",
        "strict_mode": meta.get("strict_mode", True),
    }


def _model_to_response(m: MachineModel) -> MachineResponse:
    """Build MachineResponse from MachineModel."""
    strict = m.strict_mode
    if isinstance(strict, str):
        strict = strict.lower() in ("true", "1", "yes")
    return MachineResponse(
        id=str(m.id),
        name=m.name,
        version=m.version,
        description=m.description,
        strict_mode=bool(strict),
        config=m.config_json,
        created_at=m.created_at,
        updated_at=m.updated_at,
    )


@router.post(
    "/validate",
    response_model=ValidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Validate FSM config",
    description="Validate FSM configuration. Returns errors or machine info.",
    responses={
        200: {"description": "Validation result"},
        422: {"description": "Request validation error"},
    },
)
async def validate_config(
    request: ValidateRequest,
    service: Annotated[FSMService, Depends(get_fsm_service)],
) -> ValidateResponse:
    """
    Validate FSM configuration.

    If valid, returns machine_name, version, state_names, trigger_names, terminal_states.
    If invalid, returns list of error messages.
    """
    valid, errors, info = service.validate(request.config)
    if valid and info:
        return ValidateResponse(
            valid=True,
            errors=[],
            info=MachineInfo(**info),
        )
    return ValidateResponse(valid=False, errors=errors, info=None)


@router.get(
    "/machines",
    response_model=MachineListResponse,
    status_code=status.HTTP_200_OK,
    summary="List FSM machines",
    description="List all FSM machines stored in the database",
)
async def list_machines(db: Session = Depends(get_db_session)) -> MachineListResponse:
    """List machines from the database."""
    rows = db.query(MachineModel).order_by(MachineModel.name, MachineModel.version).all()
    items = [
        MachineListItem(id=str(r.id), name=r.name, version=r.version, description=r.description)
        for r in rows
    ]
    return MachineListResponse(machines=items, count=len(items))


@router.get(
    "/machines/{machine_id}",
    response_model=MachineResponse,
    status_code=status.HTTP_200_OK,
    summary="Get FSM machine",
    description="Get a single FSM machine by ID (returns full config).",
)
async def get_machine(
    machine_id: str,
    db: Session = Depends(get_db_session),
) -> MachineResponse:
    """Get machine by ID."""
    try:
        uid = uuid.UUID(machine_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid machine ID: {machine_id}")
    row = db.query(MachineModel).filter(MachineModel.id == uid).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Machine not found: {machine_id}")
    return _model_to_response(row)


@router.post(
    "/machines",
    response_model=MachineResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create FSM machine",
    description="Validate and store an FSM machine in the database.",
)
async def create_machine(
    request: MachineCreateRequest,
    db: Session = Depends(get_db_session),
    service: Annotated[FSMService, Depends(get_fsm_service)] = None,
) -> MachineResponse:
    """Validate config and save machine to database."""
    svc = service if service is not None else FSMService()
    valid, errors, _ = svc.validate(request.config)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid FSM config", "errors": errors},
        )
    meta = _config_to_meta(request.config)
    existing = (
        db.query(MachineModel)
        .filter(MachineModel.name == meta["name"], MachineModel.version == meta["version"])
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Machine '{meta['name']}' version '{meta['version']}' already exists",
        )
    row = MachineModel(
        name=meta["name"],
        version=meta["version"],
        description=meta["description"] or None,
        strict_mode=str(meta["strict_mode"]).lower() if meta["strict_mode"] is not None else "true",
        config_json=request.config,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _model_to_response(row)


@router.put(
    "/machines/{machine_id}",
    response_model=MachineResponse,
    status_code=status.HTTP_200_OK,
    summary="Update FSM machine",
    description="Validate and update an FSM machine in the database.",
)
async def update_machine(
    machine_id: str,
    request: MachineUpdateRequest,
    db: Session = Depends(get_db_session),
    service: Annotated[FSMService, Depends(get_fsm_service)] = None,
) -> MachineResponse:
    """Validate config and update machine in database."""
    svc = service if service is not None else FSMService()
    valid, errors, _ = svc.validate(request.config)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": "Invalid FSM config", "errors": errors},
        )
    try:
        uid = uuid.UUID(machine_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid machine ID: {machine_id}")
    row = db.query(MachineModel).filter(MachineModel.id == uid).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Machine not found: {machine_id}")
    meta = _config_to_meta(request.config)
    row.name = meta["name"]
    row.version = meta["version"]
    row.description = meta["description"] or None
    row.strict_mode = str(meta["strict_mode"]).lower() if meta["strict_mode"] is not None else "true"
    row.config_json = request.config
    db.commit()
    db.refresh(row)
    return _model_to_response(row)


@router.delete(
    "/machines/{machine_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete FSM machine",
    description="Delete an FSM machine from the database.",
)
async def delete_machine(
    machine_id: str,
    db: Session = Depends(get_db_session),
) -> None:
    """Delete machine by ID."""
    try:
        uid = uuid.UUID(machine_id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid machine ID: {machine_id}")
    row = db.query(MachineModel).filter(MachineModel.id == uid).first()
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Machine not found: {machine_id}")
    db.delete(row)
    db.commit()
