"""Invoke (long-lived services) spec for PyStator FSM.

Optional `invoke` on a state: list of service refs (id, src/type, optional on_done).
Runtime starts services on enter and stops them on exit; service completion
can emit an event via the invoke adapter.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class InvokeSpec:
    """Specification for an invoked service on a state.

    Attributes:
        id: Unique identifier for this service invocation.
        src: Service type or name (interpreted by the invoke adapter).
        on_done: Optional event name to emit when the service completes.
    """

    id: str
    src: str
    on_done: str | None = None
