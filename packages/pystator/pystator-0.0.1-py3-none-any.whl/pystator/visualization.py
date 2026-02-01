"""State machine visualization for PyStator FSM.

Generates Mermaid diagrams from state machine definitions.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pystator.core.machine import StateMachine


def to_mermaid(
    machine: "StateMachine",
    title: str | None = None,
    show_guards: bool = True,
    show_actions: bool = False,
    show_timeouts: bool = True,
    direction: str = "TB",
) -> str:
    """Generate a Mermaid stateDiagram-v2 from a state machine.

    Args:
        machine: The state machine to visualize.
        title: Optional title for the diagram.
        show_guards: If True, show guard names on transitions.
        show_actions: If True, show action names on transitions.
        show_timeouts: If True, show timeout transitions.
        direction: Diagram direction: "TB" (top-bottom), "LR" (left-right),
            "BT" (bottom-top), "RL" (right-left).

    Returns:
        Mermaid diagram string.

    Example:
        >>> machine = StateMachine.from_yaml("order_fsm.yaml")
        >>> diagram = to_mermaid(machine, title="Order Lifecycle")
        >>> print(diagram)
        ---
        title: Order Lifecycle
        ---
        stateDiagram-v2
            direction TB
            [*] --> PENDING_NEW
            PENDING_NEW --> OPEN : broker_ack
            ...
    """
    lines: list[str] = []

    # Add title if provided
    if title:
        lines.append("---")
        lines.append(f"title: {title}")
        lines.append("---")

    lines.append("stateDiagram-v2")
    lines.append(f"    direction {direction}")

    # Add states with styling
    initial_state = machine.get_initial_state()
    terminal_states = machine.terminal_states

    # Initial transition
    lines.append(f"    [*] --> {initial_state.name}")

    # State definitions with notes for timeouts
    for state_name, state in machine.states.items():
        # Add state with description if available
        if state.description:
            lines.append(f"    {state_name} : {_escape_mermaid(state.description)}")

        # Add timeout note
        if show_timeouts and state.timeout:
            timeout_note = f"timeout: {state.timeout.seconds}s -> {state.timeout.destination}"
            lines.append(f"    note right of {state_name}")
            lines.append(f"        {timeout_note}")
            lines.append(f"    end note")

    # Terminal states
    for term_state in terminal_states:
        lines.append(f"    {term_state} --> [*]")

    # Transitions
    for transition in machine.transitions:
        for source in transition.source:
            label_parts = [transition.trigger]

            if show_guards and transition.guards:
                guards_str = ", ".join(transition.guards)
                label_parts.append(f"[{guards_str}]")

            if show_actions and transition.actions:
                actions_str = ", ".join(transition.actions)
                label_parts.append(f"/ {actions_str}")

            label = " ".join(label_parts)
            label = _escape_mermaid(label)

            lines.append(f"    {source} --> {transition.dest} : {label}")

    # Timeout transitions (dashed)
    if show_timeouts:
        for state_name, state in machine.states.items():
            if state.timeout:
                lines.append(
                    f"    {state_name} --> {state.timeout.destination} : timeout"
                )

    return "\n".join(lines)


def to_mermaid_flowchart(
    machine: "StateMachine",
    title: str | None = None,
    show_guards: bool = True,
    direction: str = "TB",
) -> str:
    """Generate a Mermaid flowchart from a state machine.

    Alternative visualization using flowchart syntax.

    Args:
        machine: The state machine to visualize.
        title: Optional title for the diagram.
        show_guards: If True, show guard names on transitions.
        direction: Diagram direction.

    Returns:
        Mermaid flowchart string.
    """
    lines: list[str] = []

    if title:
        lines.append("---")
        lines.append(f"title: {title}")
        lines.append("---")

    lines.append(f"flowchart {direction}")

    initial_state = machine.get_initial_state()
    terminal_states = machine.terminal_states

    # Define state nodes with shapes
    for state_name, state in machine.states.items():
        if state.is_initial:
            # Stadium shape for initial
            lines.append(f"    {state_name}([{state_name}])")
        elif state.is_terminal:
            # Double circle for terminal (hexagon in flowchart)
            lines.append(f"    {state_name}{{{{{state_name}}}}}")
        else:
            # Rectangle for normal states
            lines.append(f"    {state_name}[{state_name}]")

    # Transitions
    for transition in machine.transitions:
        for source in transition.source:
            if show_guards and transition.guards:
                guards_str = ", ".join(transition.guards)
                label = f"{transition.trigger} [{guards_str}]"
            else:
                label = transition.trigger

            label = _escape_mermaid(label)
            lines.append(f"    {source} -->|\"{label}\"| {transition.dest}")

    # Timeout transitions
    for state_name, state in machine.states.items():
        if state.timeout:
            lines.append(
                f"    {state_name} -.->|\"timeout\"| {state.timeout.destination}"
            )

    return "\n".join(lines)


def to_dot(
    machine: "StateMachine",
    title: str | None = None,
    show_guards: bool = True,
    show_actions: bool = False,
) -> str:
    """Generate a Graphviz DOT diagram from a state machine.

    Args:
        machine: The state machine to visualize.
        title: Optional title for the diagram.
        show_guards: If True, show guard names on transitions.
        show_actions: If True, show action names on transitions.

    Returns:
        DOT diagram string.
    """
    lines: list[str] = []

    graph_name = title or machine.name or "fsm"
    graph_name = graph_name.replace(" ", "_").replace("-", "_")

    lines.append(f"digraph {graph_name} {{")
    lines.append("    rankdir=TB;")
    lines.append("    node [shape=rectangle, style=rounded];")

    initial_state = machine.get_initial_state()
    terminal_states = machine.terminal_states

    # Start point
    lines.append('    __start__ [shape=point, width=0.2, label=""];')
    lines.append(f"    __start__ -> {initial_state.name};")

    # State definitions
    for state_name, state in machine.states.items():
        attrs = []

        if state.is_initial:
            attrs.append('style="rounded,bold"')
        elif state.is_terminal:
            attrs.append("shape=doublecircle")

        if state.description:
            attrs.append(f'tooltip="{_escape_dot(state.description)}"')

        if attrs:
            lines.append(f"    {state_name} [{', '.join(attrs)}];")

    # End points for terminal states
    for i, term_state in enumerate(terminal_states):
        lines.append(f'    __end{i}__ [shape=point, width=0.2, label=""];')
        lines.append(f"    {term_state} -> __end{i}__;")

    # Transitions
    for transition in machine.transitions:
        for source in transition.source:
            label_parts = [transition.trigger]

            if show_guards and transition.guards:
                guards_str = ", ".join(transition.guards)
                label_parts.append(f"[{guards_str}]")

            if show_actions and transition.actions:
                actions_str = ", ".join(transition.actions)
                label_parts.append(f"/ {actions_str}")

            label = "\\n".join(label_parts)
            label = _escape_dot(label)

            lines.append(f'    {source} -> {transition.dest} [label="{label}"];')

    # Timeout transitions (dashed)
    for state_name, state in machine.states.items():
        if state.timeout:
            lines.append(
                f'    {state_name} -> {state.timeout.destination} '
                f'[label="timeout ({state.timeout.seconds}s)", style=dashed];'
            )

    lines.append("}")

    return "\n".join(lines)


def get_statistics(machine: "StateMachine") -> dict:
    """Get statistics about a state machine.

    Args:
        machine: The state machine to analyze.

    Returns:
        Dictionary with statistics.
    """
    states = machine.states
    transitions = machine.transitions

    # Count state types
    initial_count = sum(1 for s in states.values() if s.is_initial)
    terminal_count = sum(1 for s in states.values() if s.is_terminal)
    stable_count = len(states) - initial_count - terminal_count

    # Count transitions
    guarded_count = sum(1 for t in transitions if t.guards)
    actioned_count = sum(1 for t in transitions if t.actions)

    # Count unique triggers
    triggers = set(t.trigger for t in transitions)

    # States with timeouts
    timeout_count = sum(1 for s in states.values() if s.timeout)

    # Transitions per state (fan-out)
    fan_out = {}
    for state_name in states:
        fan_out[state_name] = len(machine.get_available_transitions(state_name))

    return {
        "total_states": len(states),
        "initial_states": initial_count,
        "terminal_states": terminal_count,
        "stable_states": stable_count,
        "total_transitions": len(transitions),
        "guarded_transitions": guarded_count,
        "actioned_transitions": actioned_count,
        "unique_triggers": len(triggers),
        "triggers": sorted(triggers),
        "states_with_timeouts": timeout_count,
        "max_fan_out": max(fan_out.values()) if fan_out else 0,
        "fan_out_by_state": fan_out,
    }


def _escape_mermaid(text: str) -> str:
    """Escape special characters for Mermaid."""
    # Replace characters that could break Mermaid syntax
    text = text.replace('"', "'")
    text = text.replace("<", "&lt;")
    text = text.replace(">", "&gt;")
    return text


def _escape_dot(text: str) -> str:
    """Escape special characters for DOT."""
    text = text.replace('"', '\\"')
    text = text.replace("\n", "\\n")
    return text
