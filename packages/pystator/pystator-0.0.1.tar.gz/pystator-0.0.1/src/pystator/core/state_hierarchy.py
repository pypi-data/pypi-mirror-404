"""State hierarchy (statecharts) for PyStator FSM.

Builds and owns the state tree. Exposes ancestors, LCA, exit/enter chains,
and initial leaf resolution. No transition logic—used by StateMachine.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from pystator.core.errors import ConfigurationError
from pystator.core.state import StateType

if TYPE_CHECKING:
    from pystator.core.state import State


class StateHierarchy:
    """Tree of states: parent map, children, roots. Validates and provides hierarchy queries."""

    def __init__(self, states: dict[str, State]) -> None:
        """Build hierarchy from states dict. Validates structure (one root initial, no cycles)."""
        self._states = states
        self._parent: dict[str, str] = {}
        self._children: dict[str, list[str]] = {name: [] for name in states}
        self._roots: list[str] = []

        for name, state in states.items():
            if state.parent is not None:
                self._parent[name] = state.parent
                self._children.setdefault(state.parent, []).append(name)
            else:
                self._roots.append(name)

        self._validate()

    def _validate(self) -> None:
        """Ensure one root initial, no cycles, all parent/initial_child refs exist."""
        # All parent refs exist
        for child, parent in self._parent.items():
            if parent not in self._states:
                raise ConfigurationError(
                    f"State '{child}' references unknown parent '{parent}'",
                    context={"state": child, "parent": parent},
                )

        # No cycles
        for name in self._states:
            seen: set[str] = set()
            current: str | None = name
            while current is not None:
                if current in seen:
                    raise ConfigurationError(
                        f"Cycle in parent chain involving state '{name}'",
                        context={"state": name},
                    )
                seen.add(current)
                current = self._parent.get(current)

        # All initial_child refs exist
        for name, state in self._states.items():
            if state.initial_child is not None:
                if state.initial_child not in self._states:
                    raise ConfigurationError(
                        f"State '{name}' references unknown initial_child '{state.initial_child}'",
                        context={"state": name, "initial_child": state.initial_child},
                    )

        # Exactly one root state with type initial
        root_initial = [r for r in self._roots if self._states[r].type == StateType.INITIAL]
        if len(root_initial) == 0:
            raise ConfigurationError(
                "No initial state defined (no root state with type 'initial')",
                context={"roots": self._roots},
            )
        if len(root_initial) > 1:
            raise ConfigurationError(
                "Multiple root initial states defined",
                context={"root_initial": root_initial},
            )

    def ancestors(self, leaf: str) -> list[str]:
        """Path from leaf to root: [leaf, parent, grandparent, ...]. For a root, [leaf]."""
        if leaf not in self._states:
            return []
        path = [leaf]
        current: str | None = leaf
        while current is not None:
            parent = self._parent.get(current)
            if parent is None:
                break
            path.append(parent)
            current = parent
        return path

    def resolve_initial_leaf(self, state_name: str) -> str:
        """If state is compound, follow initial_child until leaf; else return state_name."""
        if state_name not in self._states:
            return state_name
        current = state_name
        while True:
            state = self._states[current]
            if state.initial_child is None:
                return current
            current = state.initial_child
            if current not in self._states:
                return state_name

    def effective_target_leaf(self, dest: str) -> str:
        """Same as resolve_initial_leaf(dest); used for transition destination."""
        return self.resolve_initial_leaf(dest)

    def lca(self, leaf_a: str, leaf_b: str) -> str | None:
        """Lowest common ancestor of the two states. None if different trees."""
        if leaf_a not in self._states or leaf_b not in self._states:
            return None
        anc_a = set(self.ancestors(leaf_a))
        for node in self.ancestors(leaf_b):
            if node in anc_a:
                return node
        return None

    def exit_chain(self, from_leaf: str, to_lca: str | None) -> list[str]:
        """State names from from_leaf up to (but not including) to_lca. If to_lca is None, from_leaf up to root."""
        path = self.ancestors(from_leaf)
        if to_lca is None:
            return path
        result = []
        for s in path:
            if s == to_lca:
                break
            result.append(s)
        return result

    def enter_chain(self, from_lca: str | None, to_leaf: str) -> list[str]:
        """State names from first child of from_lca on path to to_leaf, down to to_leaf. If from_lca is None, root path to to_leaf."""
        path_from_root_to_leaf = list(reversed(self.ancestors(to_leaf)))
        if from_lca is None:
            return path_from_root_to_leaf
        try:
            idx = path_from_root_to_leaf.index(from_lca)
            return path_from_root_to_leaf[idx + 1:]
        except ValueError:
            return path_from_root_to_leaf

    def is_compound(self, state_name: str) -> bool:
        """True if state has initial_child."""
        if state_name not in self._states:
            return False
        return self._states[state_name].initial_child is not None

    def children(self, state_name: str) -> list[str]:
        """Direct children of the state."""
        return list(self._children.get(state_name, []))

    @property
    def roots(self) -> list[str]:
        """Root state names (no parent)."""
        return list(self._roots)
