"""
SQLAlchemy model for FSM machine definitions.

Stores full FSM configuration (meta, states, transitions, error_policy) as JSON
for round-trip fidelity, mirroring how PyCharter stores contract/schema data.
"""

import uuid

from sqlalchemy import JSON, Column, DateTime, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func

from pystator.db.base import Base


class MachineModel(Base):
    """
    SQLAlchemy model for FSM machines (state machine definitions).

    config_json holds the full FSM config dict (meta, states, transitions,
    error_policy) so it can be loaded with StateMachine.from_dict(config_json).
    """

    __tablename__ = "machines"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Core identifiers (also in meta)
    name = Column(String(255), nullable=False)  # machine_name from meta
    version = Column(String(50), nullable=False)
    description = Column(Text, nullable=True)
    strict_mode = Column(String(10), nullable=True)  # store as "true"/"false" or use Boolean

    # Full FSM config for round-trip (meta, states, transitions, error_policy)
    config_json = Column(JSON, nullable=False)

    # Audit fields (mirror PyCharter)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
    created_by = Column(String(255), nullable=True)
    updated_by = Column(String(255), nullable=True)

    __table_args__ = (
        UniqueConstraint("name", "version", name="uq_machines_name_version"),
        {"schema": "pystator"},
    )
