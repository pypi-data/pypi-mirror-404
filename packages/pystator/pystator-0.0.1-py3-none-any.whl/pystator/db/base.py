"""
Base SQLAlchemy configuration.

Mirrors PyCharter's db/base.py for consistent behavior across SQLite and PostgreSQL.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


def get_engine(connection_string: str):
    """
    Create SQLAlchemy engine from connection string.

    For SQLite, configures the engine to handle schema references properly.
    SQLite doesn't support schemas, so we ensure schema prefixes are ignored.
    """
    if connection_string.startswith("sqlite://"):
        engine = create_engine(
            connection_string,
            echo=False,
            connect_args={"check_same_thread": False}
            if connection_string != "sqlite:///:memory:" else {},
        )

        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_conn, connection_record):
            cursor = dbapi_conn.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        @event.listens_for(engine, "before_cursor_execute", retval=True)
        def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
            if connection_string.startswith("sqlite://"):
                statement = statement.replace('"pystator".', "").replace("pystator.", "")
            return statement, parameters

        return engine
    return create_engine(connection_string, echo=False)


def get_session(connection_string: str):
    """Create SQLAlchemy session from connection string."""
    engine = get_engine(connection_string)
    Session = sessionmaker(bind=engine)
    return Session()
