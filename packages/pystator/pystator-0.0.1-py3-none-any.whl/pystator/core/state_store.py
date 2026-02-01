"""State store protocol for PyStator orchestration.

The state store is the persistence adapter used by the Orchestrator to load
and save entity state. Implement this protocol with your database, Redis, etc.
"""

from __future__ import annotations

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class StateStore(Protocol):
    """Protocol for synchronous state store.

    Implement this to persist FSM state per entity (e.g. order_id, run_id).
    Used by Orchestrator for the sandwich loop: load state, compute transition,
    persist new state, execute actions.
    """

    def get_state(self, entity_id: str) -> str | None:
        """Return the current FSM state name for the entity.

        Args:
            entity_id: Unique identifier for the entity (e.g. order_id, run_id).

        Returns:
            Current state name, or None if entity is unknown (orchestrator
            may then use the machine's initial state for new entities).
        """
        ...

    def set_state(
        self,
        entity_id: str,
        state: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist the new FSM state after a successful transition.

        Args:
            entity_id: Unique identifier for the entity.
            state: The new state name to persist.
            metadata: Optional transition metadata (e.g. trigger, timestamp).
        """
        ...

    def get_context(self, entity_id: str) -> dict[str, Any]:
        """Return extra context keys to merge into the FSM context.

        Optional. Default implementation can return {}. Used to inject
        entity-specific data (e.g. from DB) into the context for guards
        and actions.

        Args:
            entity_id: Unique identifier for the entity.

        Returns:
            Dictionary of context keys to merge (event payload and
            process_event context override these).
        """
        ...


@runtime_checkable
class AsyncStateStore(Protocol):
    """Protocol for asynchronous state store.

    Use this when your persistence layer is async (e.g. async DB driver).
    Orchestrator.async_process_event uses these methods.
    """

    async def aget_state(self, entity_id: str) -> str | None:
        """Return the current FSM state name for the entity (async)."""
        ...

    async def aset_state(
        self,
        entity_id: str,
        state: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Persist the new FSM state after a successful transition (async)."""
        ...

    async def aget_context(self, entity_id: str) -> dict[str, Any]:
        """Return extra context keys to merge into the FSM context (async)."""
        ...


class InMemoryStateStore:
    """In-memory state store for testing and simple use cases.

    Implements both StateStore and AsyncStateStore. State and optional
    context are stored in a dict. Not suitable for production (no persistence).
    """

    def __init__(self) -> None:
        self._state: dict[str, str] = {}
        self._context: dict[str, dict[str, Any]] = {}

    def get_state(self, entity_id: str) -> str | None:
        return self._state.get(entity_id)

    def set_state(
        self,
        entity_id: str,
        state: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self._state[entity_id] = state

    def get_context(self, entity_id: str) -> dict[str, Any]:
        return dict(self._context.get(entity_id, {}))

    def set_context(self, entity_id: str, context: dict[str, Any]) -> None:
        self._context[entity_id] = dict(context)

    async def aget_state(self, entity_id: str) -> str | None:
        return self.get_state(entity_id)

    async def aset_state(
        self,
        entity_id: str,
        state: str,
        *,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        self.set_state(entity_id, state, metadata=metadata)

    async def aget_context(self, entity_id: str) -> dict[str, Any]:
        return self.get_context(entity_id)
