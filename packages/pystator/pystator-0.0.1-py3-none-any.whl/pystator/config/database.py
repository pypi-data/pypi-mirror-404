"""
Database URL configuration for PyStator.

Mirrors PyCharter's config pattern:
- Environment variables: PYSTATOR__DATABASE__SQL_ALCHEMY_CONN, PYSTATOR_DATABASE_URL
- Config file: pystator.cfg [database] sql_alchemy_conn
- Fallback: alembic.ini sqlalchemy.url
"""

import os
from configparser import ConfigParser
from pathlib import Path
from typing import Optional


def get_database_url() -> Optional[str]:
    """
    Get database URL from configuration.

    Priority order:
    1. PYSTATOR__DATABASE__SQL_ALCHEMY_CONN (Airflow-style)
    2. PYSTATOR_DATABASE_URL
    3. pystator.cfg [database] sql_alchemy_conn
    4. alembic.ini sqlalchemy.url
    """
    db_url = os.getenv("PYSTATOR__DATABASE__SQL_ALCHEMY_CONN")
    if db_url:
        return db_url
    db_url = os.getenv("PYSTATOR_DATABASE_URL")
    if db_url:
        return db_url
    config_file = _find_config_file("pystator.cfg")
    if config_file:
        config = ConfigParser()
        config.read(config_file)
        if config.has_section("database"):
            db_url = config.get("database", "sql_alchemy_conn", fallback=None)
            if db_url:
                return db_url
    alembic_ini = _find_config_file("alembic.ini")
    if alembic_ini:
        config = ConfigParser()
        config.read(alembic_ini)
        db_url = config.get("alembic", "sqlalchemy.url", fallback=None)
        if db_url and db_url != "driver://user:pass@localhost/dbname":
            return db_url
    return None


def _find_config_file(filename: str) -> Optional[Path]:
    """Find config file in cwd, ~/.pystator/, or project root."""
    cwd_path = Path.cwd() / filename
    if cwd_path.exists():
        return cwd_path
    home_path = Path.home() / ".pystator" / filename
    if home_path.exists():
        return home_path
    current = Path.cwd()
    for _ in range(5):
        if (current / "alembic.ini").exists():
            p = current / filename
            if p.exists():
                return p
        current = current.parent
    return None


def set_database_url(database_url: str) -> None:
    """Set database URL in environment variable."""
    os.environ["PYSTATOR_DATABASE_URL"] = database_url
