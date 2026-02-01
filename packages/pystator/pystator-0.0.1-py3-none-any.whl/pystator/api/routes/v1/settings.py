"""
Route handlers for settings and configuration testing.

Mirrors PyCharter's api/routes/v1/settings.py: database config and test-database.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from pystator.api.dependencies.database import get_db_session
from pystator.config import get_database_url
from pystator.db.models import MachineModel

router = APIRouter()


class DatabaseConfigResponse(BaseModel):
    """Response model for database configuration info."""
    configured_url: Optional[str] = None
    actual_url: str
    database_type: str
    is_default: bool
    machine_count: int
    message: str


class DatabaseTestRequest(BaseModel):
    """Request body for testing database connection."""
    connection_string: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    database: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None


class DatabaseTestResponse(BaseModel):
    """Response for database connection test."""
    success: bool
    message: str


def _build_connection_string(
    connection_string: Optional[str] = None,
    host: Optional[str] = None,
    port: Optional[int] = None,
    database: Optional[str] = None,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """Build database connection string from components."""
    if connection_string:
        return connection_string
    if not all([host, database]):
        raise ValueError("Either connection_string or (host and database) must be provided")
    if port is None:
        port = 5432
    if username and password:
        return f"postgresql://{username}:{password}@{host}:{port}/{database}"
    if username:
        return f"postgresql://{username}@{host}:{port}/{database}"
    return f"postgresql://{host}:{port}/{database}"


@router.get(
    "/settings/database-config",
    response_model=DatabaseConfigResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current database configuration",
    description="Get information about the currently configured database connection",
)
async def get_database_config(
    db: Session = Depends(get_db_session),
) -> DatabaseConfigResponse:
    """
    Get current database configuration and connection info.
    Shows which database is actually being used (SQLite vs PostgreSQL).
    """
    configured_url = get_database_url()
    actual_url = str(db.get_bind().url) if hasattr(db, "get_bind") and db.get_bind() else "unknown"
    if actual_url.startswith("sqlite"):
        database_type = "SQLite"
        is_default = configured_url is None
    elif actual_url.startswith(("postgresql", "postgres")):
        database_type = "PostgreSQL"
        is_default = False
    else:
        database_type = "Unknown"
        is_default = False
    try:
        machine_count = db.query(MachineModel).count()
    except Exception:
        machine_count = -1
    if is_default:
        message = (
            "No database URL configured. Using default SQLite. "
            "To use PostgreSQL, set PYSTATOR_DATABASE_URL."
        )
        display_url = None
    else:
        display_url = configured_url
        if configured_url and "@" in configured_url:
            parts = configured_url.split("@", 1)
            if ":" in parts[0] and "://" in parts[0]:
                user_pass = parts[0].split("://", 1)[1]
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    display_url = parts[0].split("://", 1)[0] + "://" + user + ":****@" + parts[1]
        message = f"Using {database_type} database"
    return DatabaseConfigResponse(
        configured_url=display_url,
        actual_url=actual_url.split("@")[-1] if "@" in actual_url else actual_url,
        database_type=database_type,
        is_default=is_default,
        machine_count=machine_count,
        message=message,
    )


@router.post(
    "/settings/test-database",
    response_model=DatabaseTestResponse,
    status_code=status.HTTP_200_OK,
    summary="Test database connection",
    description="Test a database connection using provided credentials",
)
async def test_database(request: DatabaseTestRequest) -> DatabaseTestResponse:
    """Test database connection."""
    try:
        connection_string = _build_connection_string(
            connection_string=request.connection_string,
            host=request.host,
            port=request.port,
            database=request.database,
            username=request.username,
            password=request.password,
        )
        engine = create_engine(connection_string, pool_pre_ping=True)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return DatabaseTestResponse(success=True, message="Database connection successful")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except SQLAlchemyError as e:
        return DatabaseTestResponse(success=False, message=f"Database connection failed: {str(e)}")
    except Exception as e:
        return DatabaseTestResponse(success=False, message=f"Unexpected error: {str(e)}")
