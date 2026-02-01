"""Dependency injection for PyStator API."""

from pystator.api.services.fsm_service import FSMService


def get_fsm_service() -> FSMService:
    """Get FSM service instance (stateless, no singleton needed)."""
    return FSMService()
