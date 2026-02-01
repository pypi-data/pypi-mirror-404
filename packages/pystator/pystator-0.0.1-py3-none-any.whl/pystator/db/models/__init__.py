"""
SQLAlchemy models for PyStator FSM persistence.

Mirrors PyCharter's data model pattern: versioned, audited records.
- MachineModel: FSM definition (meta, states, transitions, error_policy) stored as config_json
  for full round-trip; name + version unique.
"""

from pystator.db.models.machine import MachineModel

__all__ = ["MachineModel"]
