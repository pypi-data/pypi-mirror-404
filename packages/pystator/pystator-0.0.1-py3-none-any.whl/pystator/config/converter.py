"""Convert Pydantic config models to core State/Transition dataclasses."""

from __future__ import annotations

from typing import Any

from pystator.config.models import (
    MachineConfig,
    StateDef,
    TransitionDef,
)
from pystator.core.invoke import InvokeSpec
from pystator.core.state import Region, State, StateType, Timeout
from pystator.core.transition import ActionSpec, GuardSpec, Transition, parse_delay


def _implicit_trigger_for_after(source: str, after_ms: int) -> str:
    """Generate synthetic trigger for delayed transition with no explicit trigger."""
    return f"_after_{source}_{after_ms}_ms"


def _state_def_metadata(s: StateDef) -> dict[str, Any]:
    """Merge model_extra into metadata for StateDef."""
    meta = dict(s.metadata)
    if s.model_extra:
        meta.update(s.model_extra)
    return meta


def _transition_def_metadata(t: TransitionDef) -> dict[str, Any]:
    """Merge model_extra into metadata for TransitionDef."""
    meta = dict(t.metadata)
    if t.model_extra:
        meta.update(t.model_extra)
    return meta


def state_def_to_state(s: StateDef) -> State:
    """Convert StateDef to State."""
    timeout = None
    if s.timeout is not None:
        timeout = Timeout(seconds=s.timeout.seconds, destination=s.timeout.destination)

    regions = tuple(
        Region(
            name=r.name,
            initial=r.initial,
            states=tuple(r.states),
            description=r.description or "",
        )
        for r in s.regions
    )

    on_enter = tuple(
        ActionSpec.from_config(item) if isinstance(item, dict) else ActionSpec(name=item)
        for item in (s.on_enter if isinstance(s.on_enter, list) else [s.on_enter])
    )
    on_exit = tuple(
        ActionSpec.from_config(item) if isinstance(item, dict) else ActionSpec(name=item)
        for item in (s.on_exit if isinstance(s.on_exit, list) else [s.on_exit])
    )

    invoke = tuple(
        InvokeSpec(id=inv.id, src=inv.src, on_done=inv.on_done)
        for inv in s.invoke
    )

    return State(
        name=s.name,
        type=StateType(s.type),
        description=s.description or "",
        parent=s.parent,
        initial_child=s.initial_child,
        regions=regions,
        on_enter=on_enter,
        on_exit=on_exit,
        invoke=invoke,
        timeout=timeout,
        metadata=_state_def_metadata(s),
    )


def transition_def_to_transition(t: TransitionDef) -> Transition:
    """Convert TransitionDef to Transition. Resolves implicit trigger when after is set."""
    source = t.source if isinstance(t.source, list) else [t.source]
    source_set = frozenset(source)

    after_ms: int | None = None
    if t.after is not None:
        after_ms = parse_delay(t.after)

    trigger = (t.trigger or "").strip()
    if not trigger and after_ms is not None:
        if len(source_set) != 1:
            raise ValueError(
                "Delayed transition with implicit trigger (no 'trigger' key) "
                "must have exactly one source state"
            )
        (single_source,) = source_set
        trigger = _implicit_trigger_for_after(single_source, after_ms)
    elif not trigger:
        raise ValueError("Transition must have either 'trigger' or 'after'")

    guards = tuple(
        GuardSpec.from_config(item) if isinstance(item, dict) else GuardSpec(name=item)
        for item in t.guards
    )
    actions = tuple(
        ActionSpec.from_config(item) if isinstance(item, dict) else ActionSpec(name=item)
        for item in t.actions
    )

    region = t.region if isinstance(t.region, str) else None

    return Transition(
        trigger=trigger,
        source=source_set,
        dest=t.dest,
        region=region,
        guards=guards,
        actions=actions,
        after=after_ms,
        description=t.description or "",
        metadata=_transition_def_metadata(t),
    )


def machine_config_to_core(config: MachineConfig) -> tuple[dict[str, State], list[Transition], dict[str, Any]]:
    """Convert validated MachineConfig to (states dict, transitions list, meta dict)."""
    states = {s.name: state_def_to_state(s) for s in config.states}
    transitions = [transition_def_to_transition(t) for t in config.transitions]

    meta: dict[str, Any] = {}
    if isinstance(config.meta, dict):
        meta = dict(config.meta)
    else:
        m = config.meta
        if m.version is not None:
            meta["version"] = m.version
        if m.machine_name is not None:
            meta["machine_name"] = m.machine_name
        meta["strict_mode"] = m.strict_mode
        if m.event_normalizer is not None:
            meta["event_normalizer"] = m.event_normalizer
        if m.description is not None:
            meta["description"] = m.description
        if getattr(m, "model_extra", None):
            meta.update(m.model_extra)

    if config.context is not None:
        meta["context"] = config.context
    if config.events is not None:
        meta["events"] = config.events

    return states, transitions, meta
