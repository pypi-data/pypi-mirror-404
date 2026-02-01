"""Guard evaluation logic for PyStator FSM."""

from __future__ import annotations

from typing import Any

from pystator.core.errors import GuardNotFoundError, GuardRejectedError
from pystator.core.transition import Transition, GuardSpec
from pystator.guards.registry import GuardRegistry, GuardResult


# Safe builtins allowed in inline guard expressions (e.g. len(positions) < max_positions).
_INLINE_GUARD_BUILTINS: dict[str, Any] = {
    "len": len,
    "min": min,
    "max": max,
    "abs": abs,
    "sum": sum,
}


def _eval_expression(expr: str, context: dict[str, Any]) -> bool:
    """Evaluate a boolean expression with context as namespace.
    
    Uses simpleeval for safe expression evaluation. A minimal set of safe
    builtins is registered so expressions like ``len(positions) < max_positions``
    work without precomputing values in context.
    
    Allowed builtins: len, min, max, abs, sum.
    
    Args:
        expr: Boolean expression string.
        context: Variables available in the expression.
    
    Returns:
        Boolean result of the expression.
    
    Raises:
        ImportError: If simpleeval is not installed.
        Exception: If expression evaluation fails.
    """
    try:
        from simpleeval import SimpleEval
    except ImportError as e:
        raise ImportError(
            "Inline guard expressions require simpleeval. "
            "Install with: pip install pystator[recipes]"
        ) from e
    
    evaluator = SimpleEval(names=context)
    for name, func in _INLINE_GUARD_BUILTINS.items():
        evaluator.functions[name] = func
    result = evaluator.eval(expr)
    return bool(result)


class GuardEvaluator:
    """Evaluates guard conditions for transitions.

    The evaluator is responsible for determining whether a transition
    should be allowed based on its guard conditions and the current
    context.

    Supports both:
    - Named guard functions (registered in GuardRegistry)
    - Inline expressions (evaluated with simpleeval)

    Example:
        >>> evaluator = GuardEvaluator(guard_registry)
        >>> result = evaluator.can_transition(transition, context)
        >>> if not result.passed:
        ...     print(f"Blocked by: {result.guard_name}")
    """

    def __init__(
        self,
        registry: GuardRegistry | None = None,
        strict: bool = True,
    ) -> None:
        """Initialize the guard evaluator.

        Args:
            registry: Guard registry containing guard functions.
                     Can be None if only using inline expressions.
            strict: If True, raise errors for missing guards.
                   If False, missing guards are treated as passing.
        """
        self.registry = registry
        self.strict = strict

    def can_transition(
        self,
        transition: Transition,
        context: dict[str, Any],
    ) -> GuardResult:
        """Check if a transition is allowed based on its guards.

        Args:
            transition: The transition to check.
            context: Context dictionary for guard evaluation.

        Returns:
            GuardResult indicating if transition is allowed.

        Raises:
            GuardNotFoundError: If strict=True and a named guard is missing.
        """
        if not transition.guards:
            return GuardResult.success()

        return self._evaluate_guards(transition.guards, context)

    def _evaluate_guards(
        self,
        guards: tuple[GuardSpec, ...],
        context: dict[str, Any],
    ) -> GuardResult:
        """Evaluate a sequence of guard conditions.

        All guards must pass for the result to be successful (AND logic).
        Supports both named guards and inline expressions.
        """
        evaluated: list[tuple[str, bool]] = []

        for guard in guards:
            guard_id = guard.expr if guard.is_expression else guard.name
            
            try:
                if guard.is_expression:
                    # Inline expression guard
                    result = _eval_expression(guard.expr, context)  # type: ignore
                    evaluated.append((f"expr:{guard.expr}", result))
                else:
                    # Named guard function
                    guard_name = guard.name  # type: ignore
                    
                    if self.registry is None or not self.registry.has(guard_name):
                        if self.strict:
                            raise GuardNotFoundError(
                                f"Guard '{guard_name}' not registered",
                                guard_name=guard_name,
                            )
                        # Non-strict: treat missing guard as passing
                        evaluated.append((guard_name, True))
                        continue
                    
                    result = self.registry.evaluate(guard_name, context)
                    evaluated.append((guard_name, result))
                
                if not result:
                    return GuardResult.failure(
                        str(guard_id), 
                        evaluated=evaluated
                    )

            except GuardNotFoundError:
                raise
            except Exception as e:
                # Guard raised an exception - treat as failure
                evaluated.append((str(guard_id), False))
                return GuardResult.failure(
                    str(guard_id),
                    message=f"Guard '{guard_id}' raised exception: {e}",
                    evaluated=evaluated,
                )

        return GuardResult.success(evaluated)

    def evaluate_and_raise(
        self,
        transition: Transition,
        current_state: str,
        context: dict[str, Any],
    ) -> None:
        """Evaluate guards and raise exception if blocked.

        Args:
            transition: The transition to check.
            current_state: The current state name.
            context: Context dictionary for guard evaluation.

        Raises:
            GuardRejectedError: If any guard blocks the transition.
            GuardNotFoundError: If strict=True and a guard is missing.
        """
        result = self.can_transition(transition, context)

        if not result.passed:
            raise GuardRejectedError(
                message=result.message,
                current_state=current_state,
                trigger=transition.trigger,
                guard_name=result.guard_name or "unknown",
                guard_result=result.evaluated_guards,
            )

    def validate_guards_exist(self, guards: tuple[GuardSpec, ...]) -> list[str]:
        """Check which named guards are missing from the registry.

        Args:
            guards: Guard specifications to check.

        Returns:
            List of missing named guard names.
        """
        if self.registry is None:
            return [g.name for g in guards if g.name is not None]
        return [
            g.name for g in guards 
            if g.name is not None and not self.registry.has(g.name)
        ]

    def get_required_guards(self, transitions: list[Transition]) -> set[str]:
        """Get all unique named guard function names from transitions.

        Args:
            transitions: List of transitions to analyze.

        Returns:
            Set of unique named guard names (excludes inline expressions).
        """
        guards: set[str] = set()
        for trans in transitions:
            for guard in trans.guards:
                if guard.name is not None:
                    guards.add(guard.name)
        return guards
