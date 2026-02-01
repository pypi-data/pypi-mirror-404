"""
Database session dependency for API routes.

Mirrors PyCharter's api/dependencies/database.py: same behavior for
get_db_session, default SQLite, and auto-initialization.
"""

import os
from pathlib import Path
from typing import Generator

from fastapi import Depends, HTTPException, status
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import Session

from pystator.config import get_database_url, set_database_url
from pystator.db.base import Base, get_session


def _get_migrations_dir() -> Path:
    """Find migrations directory relative to installed package."""
    try:
        import pystator
        migrations_dir = Path(pystator.__file__).parent / "db" / "migrations"
    except (ImportError, AttributeError):
        migrations_dir = Path(__file__).resolve().parent.parent.parent / "db" / "migrations"
    if not migrations_dir.exists():
        cwd_migrations = Path(os.getcwd()) / "pystator" / "db" / "migrations"
        if cwd_migrations.exists():
            return cwd_migrations
        return migrations_dir
    return migrations_dir


def _ensure_sqlite_initialized(db_url: str) -> None:
    """
    Ensure SQLite database is initialized with all tables.
    Auto-initializes SQLite if it doesn't exist or is uninitialized.
    """
    if not db_url.startswith("sqlite://"):
        return
    import logging
    logger = logging.getLogger(__name__)
    try:
        db_path = db_url[10:] if db_url.startswith("sqlite:///") else db_url
        if db_path == ":memory:":
            return
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        engine = create_engine(db_url)
        inspector = inspect(engine)
        if "machines" not in inspector.get_table_names():
            logger.info("Auto-initializing SQLite database: %s", db_url)
            from pystator.db.models import MachineModel
            for table in Base.metadata.tables.values():
                if table.schema == "pystator":
                    table.schema = None
            Base.metadata.create_all(engine)
            try:
                from alembic import command
                from alembic.config import Config
                versions_dir = _get_migrations_dir() / "versions"
                if versions_dir.exists() and any(versions_dir.iterdir()):
                    set_database_url(db_url)
                    cfg = Config()
                    cfg.set_main_option("script_location", str(_get_migrations_dir()))
                    cfg.set_main_option("sqlalchemy.url", db_url)
                    command.upgrade(cfg, "head")
                    logger.info("SQLite database initialized with migrations")
                else:
                    logger.info("SQLite database initialized with base tables")
            except Exception:
                logger.info("SQLite database initialized with base tables")
    except Exception as e:
        logger.warning("Could not auto-initialize SQLite database: %s", e)


def get_db_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.

    Defaults to SQLite (sqlite:///pystator.db) if no database URL is configured.
    Automatically initializes SQLite database if it doesn't exist or is uninitialized.
    """
    import logging
    logger = logging.getLogger(__name__)
    db_url = get_database_url()
    if not db_url:
        default_db_path = Path.cwd() / "pystator.db"
        db_url = f"sqlite:///{default_db_path}"
        logger.warning(
            "No database URL configured. Using default SQLite: %s\n"
            "To use PostgreSQL, set PYSTATOR_DATABASE_URL:\n"
            "  export PYSTATOR_DATABASE_URL='postgresql://user:password@localhost:5432/pystator'",
            db_url,
        )
    else:
        masked_url = db_url
        if "@" in db_url and "://" in db_url:
            parts = db_url.split("@", 1)
            if ":" in parts[0]:
                user_pass = parts[0].split("://", 1)[1]
                if ":" in user_pass:
                    user, _ = user_pass.split(":", 1)
                    masked_url = db_url.split(":", 2)[0] + "://" + user + ":****@" + parts[1]
        logger.info("Using database: %s", masked_url)
    _ensure_sqlite_initialized(db_url)
    session = None
    try:
        session = get_session(db_url)
        session.execute(text("SELECT 1"))
        yield session
    except Exception as e:
        if session:
            try:
                session.rollback()
            except Exception:
                pass
        logger.error("Database session error: %s", e, exc_info=True)
        error_detail = "Failed to connect to database"
        error_msg = str(e).lower()
        if "no such table" in error_msg or ("table" in error_msg and "doesn't exist" in error_msg):
            error_detail = "Database tables not found. Run: pystator db init"
        elif "database is locked" in error_msg:
            error_detail = "Database is locked. Close other connections or wait and try again."
        elif "permission denied" in error_msg or "access denied" in error_msg:
            error_detail = "Database permission denied. Check file permissions."
        else:
            if os.getenv("ENVIRONMENT") == "development" or not os.getenv("ENVIRONMENT"):
                error_detail = f"Failed to connect to database: {e}"
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_detail,
        )
    finally:
        if session:
            try:
                session.close()
            except Exception:
                pass
