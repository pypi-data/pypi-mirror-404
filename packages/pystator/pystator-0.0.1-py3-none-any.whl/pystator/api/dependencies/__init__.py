"""API dependency injection."""

from pystator.api.dependencies.core import get_fsm_service
from pystator.api.dependencies.database import get_db_session

__all__ = ["get_fsm_service", "get_db_session"]
