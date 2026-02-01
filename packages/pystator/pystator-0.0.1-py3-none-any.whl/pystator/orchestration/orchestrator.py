"""Orchestrator: run loop (load state, process, persist, execute actions).

PyStator owns the full sandwich loop behind a single API so the app
only implements a state-store adapter and calls process_event(entity_id, event).

Supports delayed transitions via scheduler adapters:
- AsyncioScheduler: In-memory (development, testing)
- RedisScheduler: Persistent (production with Redis)
- CeleryScheduler: Task queue (production with Celery)
"""

from __future__ import annotations

import logging
from typing import Any, TYPE_CHECKING

from pystator.actions.executor import ActionExecutor
from pystator.actions.registry import ActionRegistry
from pystator.core.event import Event
from pystator.core.machine import StateMachine
from pystator.core.state_store import AsyncStateStore, StateStore
from pystator.core.transition import TransitionResult
from pystator.guards.registry import GuardRegistry

if TYPE_CHECKING:
    from pystator.scheduler.base import SchedulerAdapter
    from pystator.orchestration.invoke import InvokeAdapter


logger = logging.getLogger(__name__)


class Orchestrator:
    """Runs the full FSM sandwich loop: load state, process, persist, execute.

    The orchestrator uses a StateStore to load and save entity state, and
    runs actions after persisting the new state. Sync and async APIs
    are provided.
    
    Supports delayed transitions via an optional scheduler adapter.
    When a transition has an `after` delay, it will be scheduled to
    fire automatically after the specified time.
    """

    def __init__(
        self,
        machine: StateMachine,
        state_store: StateStore | AsyncStateStore,
        guards: GuardRegistry,
        actions: ActionRegistry,
        *,
        executor: ActionExecutor | None = None,
        scheduler: "SchedulerAdapter | None" = None,
        invoke_adapter: "InvokeAdapter | None" = None,
        use_initial_state_when_missing: bool = True,
    ) -> None:
        """Initialize the orchestrator.

        Args:
            machine: The FSM. Guards will be bound to it if not already.
            state_store: Sync or async state store for get/set state (and
                optional get_context). For async_process_event, state_store
                must implement AsyncStateStore (aget_state, aset_state, aget_context).
            guards: Guard registry. Will be bound to machine if not already bound.
            actions: Action registry for the executor.
            executor: Optional. If None, an ActionExecutor(actions) is created.
            scheduler: Optional scheduler for delayed transitions. If None,
                delayed transitions are ignored. Use AsyncioScheduler for
                zero-infrastructure scheduling.
            use_initial_state_when_missing: If True, when get_state returns None
                use the machine's initial state (for new entities). If False, raise.
        """
        self._machine = machine
        self._state_store = state_store
        self._guards = guards
        self._actions = actions
        self._executor = executor or ActionExecutor(actions, log_execution=True)
        self._scheduler = scheduler
        self._invoke_adapter = invoke_adapter
        self._use_initial_state_when_missing = use_initial_state_when_missing

        if machine._guard_evaluator is None:
            machine.bind_guards(guards)
    
    def _get_delayed_transitions(self, state_name: str) -> list[tuple[str, int]]:
        """Get delayed transitions from a state.
        
        Returns:
            List of (event, delay_ms) tuples for transitions with `after` set.
        """
        delayed = []
        for trans in self._machine._transitions:
            if trans.is_delayed and trans.matches_source(state_name):
                delayed.append((trans.trigger, trans.after))  # type: ignore
        return delayed
    
    async def _schedule_delayed_transitions(
        self, 
        entity_id: str, 
        state_name: str,
        context: dict[str, Any],
    ) -> None:
        """Schedule any delayed transitions for the given state.
        
        Args:
            entity_id: Entity ID for the scheduled events.
            state_name: Current state to check for delayed transitions.
            context: Context to pass to the scheduled event.
        """
        if self._scheduler is None:
            return
        
        delayed = self._get_delayed_transitions(state_name)
        
        for event, delay_ms in delayed:
            async def make_callback(evt: str, ctx: dict[str, Any]) -> None:
                # Closure to capture event and context
                async def callback() -> None:
                    logger.debug(f"Firing delayed event {evt} for {entity_id}")
                    await self.async_process_event(entity_id, evt, ctx)
                return callback
            
            cb = await make_callback(event, context.copy())
            task_id = await self._scheduler.schedule(
                delay_ms=delay_ms,
                callback=cb,
                entity_id=entity_id,
                event=event,
                metadata={"state": state_name},
            )
            logger.debug(f"Scheduled delayed transition {event} in {delay_ms}ms (task {task_id})")
    
    async def _cancel_pending_for_entity(self, entity_id: str) -> None:
        """Cancel any pending delayed transitions for an entity.
        
        Called when an entity transitions to a new state, cancelling
        any delayed transitions that were scheduled from the old state.
        """
        if self._scheduler is None:
            return
        
        cancelled = await self._scheduler.cancel_for_entity(entity_id)
        if cancelled:
            logger.debug(f"Cancelled {cancelled} pending delayed transitions for {entity_id}")

    def process_event(
        self,
        entity_id: str,
        event: str | Event,
        context: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """Run the sandwich loop: load state, process, persist, execute.

        Args:
            entity_id: Unique identifier for the entity (e.g. order_id).
            event: Trigger (string) or Event object.
            context: Optional context merged with event payload and store context.

        Returns:
            TransitionResult from the FSM.

        Raises:
            UndefinedStateError: If current state is not defined (e.g. entity
                unknown and use_initial_state_when_missing is False).
        """
        store = self._state_store
        if not isinstance(store, StateStore):
            raise TypeError(
                "process_event requires a sync StateStore (get_state, set_state, get_context)"
            )

        current_state = store.get_state(entity_id)
        if current_state is None:
            if self._use_initial_state_when_missing:
                current_state = self._machine.get_initial_state().name
            else:
                raise ValueError(
                    f"Entity {entity_id!r} has no state and use_initial_state_when_missing is False"
                )

        ctx = dict(store.get_context(entity_id))
        if isinstance(event, Event):
            ctx = {**ctx, **event.payload}
        else:
            event = Event(trigger=event, payload={})
        if context:
            ctx = {**ctx, **context}
        ctx["_event"] = event
        ctx["_entity_id"] = entity_id

        result = self._machine.process(current_state, event, ctx)

        if result.success and result.target_state is not None:
            if result.target_state != current_state:
                if self._invoke_adapter:
                    old_state = self._machine._states.get(current_state)
                    if old_state and old_state.invoke:
                        self._invoke_adapter.stop_services(entity_id, current_state)
                metadata = {
                    "trigger": result.trigger,
                    "source_state": result.source_state,
                    "target_state": result.target_state,
                }
                store.set_state(entity_id, result.target_state, metadata=metadata)
                if self._invoke_adapter:
                    new_state = self._machine._states.get(result.target_state)
                    if new_state and new_state.invoke:
                        self._invoke_adapter.start_services(
                            entity_id, result.target_state, new_state.invoke, ctx
                        )
            if result.all_actions:
                ctx["new_status"] = result.target_state
                self._executor.execute(result, ctx)

        return result

    async def async_process_event(
        self,
        entity_id: str,
        event: str | Event,
        context: dict[str, Any] | None = None,
    ) -> TransitionResult:
        """Run the sandwich loop asynchronously.

        Requires state_store to implement AsyncStateStore (aget_state,
        aset_state, aget_context). Uses machine.async_process and
        executor.async_execute for async guards and actions.
        
        If a scheduler is configured, handles delayed transitions:
        - Cancels pending delays when transitioning away from a state
        - Schedules new delays when entering a state with `after` transitions
        """
        store = self._state_store
        if not isinstance(store, AsyncStateStore):
            raise TypeError(
                "async_process_event requires an AsyncStateStore (aget_state, aset_state, aget_context)"
            )

        current_state = await store.aget_state(entity_id)
        if current_state is None:
            if self._use_initial_state_when_missing:
                current_state = self._machine.get_initial_state().name
                # Schedule any delayed transitions from initial state
                if self._scheduler:
                    await self._schedule_delayed_transitions(entity_id, current_state, context or {})
            else:
                raise ValueError(
                    f"Entity {entity_id!r} has no state and use_initial_state_when_missing is False"
                )

        ctx = dict(await store.aget_context(entity_id))
        if isinstance(event, Event):
            ctx = {**ctx, **event.payload}
        else:
            event = Event(trigger=event, payload={})
        if context:
            ctx = {**ctx, **context}
        ctx["_event"] = event
        ctx["_entity_id"] = entity_id

        result = await self._machine.async_process(current_state, event, ctx)

        if result.success and result.target_state is not None:
            state_changed = result.target_state != current_state
            
            if state_changed:
                if self._invoke_adapter:
                    old_state = self._machine._states.get(current_state)
                    if old_state and old_state.invoke:
                        self._invoke_adapter.stop_services(entity_id, current_state)
                # Cancel any pending delayed transitions from old state
                await self._cancel_pending_for_entity(entity_id)
                
                # Persist state change
                metadata = {
                    "trigger": result.trigger,
                    "source_state": result.source_state,
                    "target_state": result.target_state,
                }
                await store.aset_state(
                    entity_id, result.target_state, metadata=metadata
                )
                if self._invoke_adapter:
                    new_state = self._machine._states.get(result.target_state)
                    if new_state and new_state.invoke:
                        self._invoke_adapter.start_services(
                            entity_id, result.target_state, new_state.invoke, ctx
                        )
                # Schedule delayed transitions from new state
                await self._schedule_delayed_transitions(entity_id, result.target_state, ctx)
            
            if result.all_actions:
                ctx["new_status"] = result.target_state
                await self._executor.async_execute(result, ctx)

        return result
    
    async def close(self) -> None:
        """Clean up resources (scheduler, etc.)."""
        if self._scheduler:
            await self._scheduler.close()
