"""Alembic environment for PyStator DB migrations.

Mirrors PyCharter's migrations/env.py: uses PYSTATOR_DATABASE_URL,
pystator schema for PostgreSQL, no schema for SQLite.
"""

import os

from alembic import context
from sqlalchemy import engine_from_config, pool

from pystator.config import get_database_url
from pystator.db.base import Base
from pystator.db.models import MachineModel  # noqa: F401 - for metadata

config = context.config
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = get_database_url() or config.get_main_option("sqlalchemy.url")
    version_table_schema = None
    if url and url.startswith(("postgresql://", "postgres://")):
        version_table_schema = "pystator"
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        version_table_schema=version_table_schema,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    database_url = get_database_url()
    configuration = config.get_section(config.config_ini_section, {}) or {}
    if database_url:
        configuration["sqlalchemy.url"] = database_url
    url = configuration.get("sqlalchemy.url", "")
    version_table_schema = None
    if url and url.startswith(("postgresql://", "postgres://")):
        version_table_schema = "pystator"
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=version_table_schema,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
