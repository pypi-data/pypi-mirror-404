"""Invoke adapter for long-lived services on states.

Optional `invoke` on a state: list of service refs (id, src, optional on_done).
The orchestrator calls the invoke adapter to start services on enter and
stop them on exit. When a service completes, the adapter emits the on_done
event (e.g. the app calls process_event(entity_id, on_done)).
"""

from __future__ import annotations

from typing import Any, Protocol

from pystator.core.invoke import InvokeSpec


class InvokeAdapter(Protocol):
    """Protocol for starting and stopping invoked services.

    Applications provide an implementation that starts real services (e.g.
    subscriptions, timers) when entering a state with `invoke`, and stops
    them when leaving. Service completion can emit the `on_done` event
    (e.g. by calling orchestrator.process_event(entity_id, on_done)).
    """

    def start_services(
        self,
        entity_id: str,
        state_name: str,
        invoke_specs: tuple[InvokeSpec, ...],
        context: dict[str, Any],
    ) -> None:
        """Start the given invoked services for the entity in the state."""
        ...

    def stop_services(self, entity_id: str, state_name: str) -> None:
        """Stop any services previously started for the entity in the state."""
        ...


class NoOpInvokeAdapter:
    """No-op invoke adapter. Use when no state has `invoke` or no real services are needed."""

    def start_services(
        self,
        entity_id: str,
        state_name: str,
        invoke_specs: tuple[InvokeSpec, ...],
        context: dict[str, Any],
    ) -> None:
        pass

    def stop_services(self, entity_id: str, state_name: str) -> None:
        pass
