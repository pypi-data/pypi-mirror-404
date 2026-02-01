"""Route handlers for FSM process (transition) operations."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from pystator.api.dependencies import get_fsm_service
from pystator.api.models.requests import ProcessRequest
from pystator.api.models.responses import ProcessResponse
from pystator.api.services.fsm_service import FSMService

router = APIRouter()


@router.post(
    "/process",
    response_model=ProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process FSM event",
    description="Build machine from config and compute transition for one event. "
    "Returns transition result (no side effects). Guards are evaluated as pass-through.",
    responses={
        200: {"description": "Transition computed"},
        400: {"description": "Invalid config or state"},
        422: {"description": "Validation error"},
    },
)
async def process_event(
    request: ProcessRequest,
    service: Annotated[FSMService, Depends(get_fsm_service)],
) -> ProcessResponse:
    """
    Process one FSM event.

    Accepts full FSM config, current state, trigger, and optional context.
    Returns success/failure, target state, and actions to execute.
    The API does not persist state or execute actions; the client does that.
    """
    try:
        result = service.process(
            config=request.config,
            current_state=request.current_state,
            trigger=request.trigger,
            context=request.context,
        )
        return ProcessResponse(**result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e
