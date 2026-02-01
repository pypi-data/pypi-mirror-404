"""Action execution management for PyStator FSM.

Supports both sequential and parallel action execution with async support.
The executor handles the "Phase 5" of the sandwich pattern: executing side
effects AFTER state changes have been persisted.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import logging

from pystator.actions.registry import ActionRegistry, ActionResult
from pystator.core.transition import TransitionResult, ActionSpec


logger = logging.getLogger(__name__)


# Key used to inject action parameters into context
ACTION_PARAMS_KEY = "_action_params"


class ExecutionMode(str, Enum):
    """Mode for action execution."""
    
    SEQUENTIAL = "sequential"
    """Execute actions one after another (default)."""
    
    PARALLEL = "parallel"
    """Execute independent actions concurrently using asyncio.gather."""
    
    PHASED = "phased"
    """Execute exit actions, then transition actions, then enter actions in parallel phases."""


@dataclass
class ExecutionResult:
    """Complete result of executing all actions from a transition.

    Attributes:
        transition_result: The original transition result.
        action_results: Results from executing each action.
        execution_mode: How actions were executed (sequential, parallel, phased).
        started_at: When execution started.
        completed_at: When execution completed.
    """

    transition_result: TransitionResult
    action_results: list[ActionResult] = field(default_factory=list)
    execution_mode: ExecutionMode = ExecutionMode.SEQUENTIAL
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    @property
    def all_succeeded(self) -> bool:
        """Check if all actions succeeded."""
        return all(r.success for r in self.action_results)

    @property
    def failed_actions(self) -> list[str]:
        """Get list of failed action names."""
        return [r.action_name for r in self.action_results if not r.success]

    @property
    def succeeded_actions(self) -> list[str]:
        """Get list of succeeded action names."""
        return [r.action_name for r in self.action_results if r.success]

    @property
    def duration_ms(self) -> float | None:
        """Get execution duration in milliseconds."""
        if self.completed_at is None:
            return None
        delta = self.completed_at - self.started_at
        return delta.total_seconds() * 1000
    
    @property
    def action_count(self) -> int:
        """Total number of actions executed."""
        return len(self.action_results)


class ActionExecutor:
    """Executes actions from transition results with parallel execution support.

    The executor handles the "Phase 5" of the sandwich pattern:
    executing side effects AFTER state changes have been persisted.

    It provides:
    - Sequential action execution (default)
    - Parallel action execution using asyncio.gather
    - Phased execution (exit -> transition -> enter in parallel phases)
    - Error isolation (one failure doesn't stop others unless configured)
    - Execution tracking and logging
    - Retry support (optional)

    Execution Modes:
    - SEQUENTIAL: Actions run one after another (default, safest)
    - PARALLEL: All actions run concurrently (fastest, use when actions are independent)
    - PHASED: Exit actions run in parallel, then transition actions, then enter actions
              (balanced approach for state machine patterns)

    Example:
        >>> executor = ActionExecutor(action_registry)
        >>>
        >>> # Sequential execution (default)
        >>> execution = executor.execute(transition_result, context)
        >>>
        >>> # Parallel execution (async)
        >>> execution = await executor.async_execute_parallel(transition_result, context)
        >>>
        >>> # Phased execution (async)
        >>> execution = await executor.async_execute_phased(transition_result, context)
    """

    def __init__(
        self,
        registry: ActionRegistry,
        stop_on_error: bool = False,
        log_execution: bool = True,
        default_mode: ExecutionMode = ExecutionMode.SEQUENTIAL,
    ) -> None:
        """Initialize the action executor.

        Args:
            registry: Action registry containing action functions.
            stop_on_error: If True, stop execution on first failure (sequential only).
            log_execution: If True, log action execution details.
            default_mode: Default execution mode for async operations.
        """
        self.registry = registry
        self.stop_on_error = stop_on_error
        self.log_execution = log_execution
        self.default_mode = default_mode

    def execute(
        self,
        transition_result: TransitionResult,
        context: dict[str, Any],
    ) -> ExecutionResult:
        """Execute all actions from a transition result.

        Actions are executed in order:
        1. on_exit actions (from source state)
        2. transition actions
        3. on_enter actions (to target state)

        Args:
            transition_result: The transition result containing actions.
            context: Context dictionary for action execution.

        Returns:
            ExecutionResult with details of all action executions.
        """
        result = ExecutionResult(
            transition_result=transition_result,
            started_at=datetime.now(timezone.utc),
        )

        if not transition_result.success:
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Get all action specs in execution order
        all_specs = transition_result.all_action_specs

        if self.log_execution and all_specs:
            logger.info(
                f"Executing {len(all_specs)} actions for transition "
                f"{transition_result.source_state} -> {transition_result.target_state}"
            )

        # Execute actions
        for action_spec in all_specs:
            action_result = self._execute_single(
                action_spec.name,
                context,
                action_spec.params if action_spec.has_params else None,
            )
            result.action_results.append(action_result)

            if not action_result.success and self.stop_on_error:
                if self.log_execution:
                    logger.error(
                        f"Action '{action_spec.name}' failed, stopping execution: "
                        f"{action_result.error}"
                    )
                break

        result.completed_at = datetime.now(timezone.utc)

        if self.log_execution:
            if result.all_succeeded:
                logger.info(
                    f"All {len(all_specs)} actions completed successfully "
                    f"in {result.duration_ms:.2f}ms"
                )
            else:
                logger.warning(
                    f"Action execution completed with failures: {result.failed_actions}"
                )

        return result

    def _execute_single(
        self,
        action_name: str,
        context: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> ActionResult:
        """Execute a single action with error handling.

        Args:
            action_name: Name of the action to execute.
            context: Context dictionary.
            params: Optional parameters to inject into context.

        Returns:
            ActionResult with execution details.
        """
        if not self.registry.has(action_name):
            if self.log_execution:
                logger.warning(f"Action '{action_name}' not registered, skipping")
            return ActionResult.ok(action_name, result="skipped_not_registered")

        try:
            if self.log_execution:
                logger.debug(f"Executing action: {action_name}")

            # Inject params into context if provided
            exec_context = context
            if params:
                exec_context = {**context, ACTION_PARAMS_KEY: params}

            result = self.registry.execute(action_name, exec_context)

            if self.log_execution:
                if result.success:
                    logger.debug(f"Action '{action_name}' completed successfully")
                else:
                    logger.warning(f"Action '{action_name}' failed: {result.error}")

            return result

        except Exception as e:
            if self.log_execution:
                logger.exception(f"Action '{action_name}' raised exception: {e}")
            return ActionResult.fail(action_name, e)
    
    def execute_action_spec(
        self,
        action: ActionSpec,
        context: dict[str, Any],
    ) -> ActionResult:
        """Execute a single ActionSpec with optional parameters.

        Args:
            action: ActionSpec containing action name and optional params.
            context: Context dictionary.

        Returns:
            ActionResult with execution details.
        """
        return self._execute_single(action.name, context, action.params if action.has_params else None)
    
    def execute_action_specs(
        self,
        actions: tuple[ActionSpec, ...] | list[ActionSpec],
        context: dict[str, Any],
    ) -> list[ActionResult]:
        """Execute a list of ActionSpec objects sequentially.

        Args:
            actions: List of ActionSpec objects to execute.
            context: Context dictionary.

        Returns:
            List of ActionResult objects.
        """
        results: list[ActionResult] = []
        
        for action in actions:
            result = self.execute_action_spec(action, context)
            results.append(result)
            
            if not result.success and self.stop_on_error:
                break
        
        return results

    def execute_specific(
        self,
        actions: list[str] | tuple[str, ...],
        context: dict[str, Any],
    ) -> list[ActionResult]:
        """Execute a specific list of actions.

        Useful for retrying failed actions or executing ad-hoc action sequences.

        Args:
            actions: List of action names to execute.
            context: Context dictionary.

        Returns:
            List of ActionResult objects.
        """
        results: list[ActionResult] = []

        for action_name in actions:
            result = self._execute_single(action_name, context)
            results.append(result)

            if not result.success and self.stop_on_error:
                break

        return results

    def validate_actions_exist(
        self,
        transition_result: TransitionResult,
    ) -> list[str]:
        """Check which actions from a transition are missing.

        Args:
            transition_result: The transition result to check.

        Returns:
            List of missing action names.
        """
        all_specs = transition_result.all_action_specs
        return [a.name for a in all_specs if not self.registry.has(a.name)]

    async def async_execute(
        self,
        transition_result: TransitionResult,
        context: dict[str, Any],
    ) -> ExecutionResult:
        """Execute all actions from a transition result asynchronously.

        Actions are executed in order:
        1. on_exit actions (from source state)
        2. transition actions
        3. on_enter actions (to target state)

        Works with both sync and async actions.

        Args:
            transition_result: The transition result containing actions.
            context: Context dictionary for action execution.

        Returns:
            ExecutionResult with details of all action executions.
        """
        from datetime import datetime, timezone

        result = ExecutionResult(
            transition_result=transition_result,
            started_at=datetime.now(timezone.utc),
        )

        if not transition_result.success:
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Get all action specs in execution order
        all_specs = transition_result.all_action_specs

        if self.log_execution and all_specs:
            logger.info(
                f"Executing {len(all_specs)} actions for transition "
                f"{transition_result.source_state} -> {transition_result.target_state}"
            )

        # Execute actions
        for action_spec in all_specs:
            action_result = await self._async_execute_single(
                action_spec.name,
                context,
                action_spec.params if action_spec.has_params else None,
            )
            result.action_results.append(action_result)

            if not action_result.success and self.stop_on_error:
                if self.log_execution:
                    logger.error(
                        f"Action '{action_spec.name}' failed, stopping execution: "
                        f"{action_result.error}"
                    )
                break

        result.completed_at = datetime.now(timezone.utc)

        if self.log_execution:
            if result.all_succeeded:
                logger.info(
                    f"All {len(all_specs)} actions completed successfully "
                    f"in {result.duration_ms:.2f}ms"
                )
            else:
                logger.warning(
                    f"Action execution completed with failures: {result.failed_actions}"
                )

        return result

    async def _async_execute_single(
        self,
        action_name: str,
        context: dict[str, Any],
        params: dict[str, Any] | None = None,
    ) -> ActionResult:
        """Execute a single action asynchronously with error handling.

        Args:
            action_name: Name of the action to execute.
            context: Context dictionary.
            params: Optional parameters to inject into context.

        Returns:
            ActionResult with execution details.
        """
        if not self.registry.has(action_name):
            if self.log_execution:
                logger.warning(f"Action '{action_name}' not registered, skipping")
            return ActionResult.ok(action_name, result="skipped_not_registered")

        try:
            if self.log_execution:
                logger.debug(f"Executing action: {action_name}")

            # Inject params into context if provided
            exec_context = context
            if params:
                exec_context = {**context, ACTION_PARAMS_KEY: params}

            result = await self.registry.async_execute(action_name, exec_context)

            if self.log_execution:
                if result.success:
                    logger.debug(f"Action '{action_name}' completed successfully")
                else:
                    logger.warning(f"Action '{action_name}' failed: {result.error}")

            return result

        except Exception as e:
            if self.log_execution:
                logger.exception(f"Action '{action_name}' raised exception: {e}")
            return ActionResult.fail(action_name, e)
    
    async def async_execute_action_spec(
        self,
        action: ActionSpec,
        context: dict[str, Any],
    ) -> ActionResult:
        """Execute a single ActionSpec asynchronously with optional parameters.

        Args:
            action: ActionSpec containing action name and optional params.
            context: Context dictionary.

        Returns:
            ActionResult with execution details.
        """
        return await self._async_execute_single(
            action.name, context, action.params if action.has_params else None
        )
    
    async def async_execute_action_specs(
        self,
        actions: tuple[ActionSpec, ...] | list[ActionSpec],
        context: dict[str, Any],
    ) -> list[ActionResult]:
        """Execute a list of ActionSpec objects sequentially (async).

        Args:
            actions: List of ActionSpec objects to execute.
            context: Context dictionary.

        Returns:
            List of ActionResult objects.
        """
        results: list[ActionResult] = []
        
        for action in actions:
            result = await self.async_execute_action_spec(action, context)
            results.append(result)
            
            if not result.success and self.stop_on_error:
                break
        
        return results
    
    async def async_execute_action_specs_parallel(
        self,
        actions: tuple[ActionSpec, ...] | list[ActionSpec],
        context: dict[str, Any],
    ) -> list[ActionResult]:
        """Execute a list of ActionSpec objects in parallel.

        Args:
            actions: List of ActionSpec objects to execute.
            context: Context dictionary.

        Returns:
            List of ActionResult objects.
        """
        if not actions:
            return []
        
        tasks = [
            self.async_execute_action_spec(action, context)
            for action in actions
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=False))

    async def async_execute_specific(
        self,
        actions: list[str] | tuple[str, ...],
        context: dict[str, Any],
    ) -> list[ActionResult]:
        """Execute a specific list of actions asynchronously.

        Useful for retrying failed actions or executing ad-hoc action sequences.

        Args:
            actions: List of action names to execute.
            context: Context dictionary.

        Returns:
            List of ActionResult objects.
        """
        results: list[ActionResult] = []

        for action_name in actions:
            result = await self._async_execute_single(action_name, context)
            results.append(result)

            if not result.success and self.stop_on_error:
                break

        return results

    # -------------------------------------------------------------------------
    # Parallel Execution Methods
    # -------------------------------------------------------------------------

    async def async_execute_parallel(
        self,
        transition_result: TransitionResult,
        context: dict[str, Any],
    ) -> ExecutionResult:
        """Execute all actions in parallel using asyncio.gather.

        All actions run concurrently. This is the fastest mode but requires
        that actions are independent and don't have ordering dependencies.

        Use this when:
        - Actions are independent (e.g., send notification AND update metrics)
        - Latency is critical
        - Actions don't modify shared state that other actions read

        Args:
            transition_result: The transition result containing actions.
            context: Context dictionary for action execution.

        Returns:
            ExecutionResult with details of all action executions.
        """
        result = ExecutionResult(
            transition_result=transition_result,
            execution_mode=ExecutionMode.PARALLEL,
            started_at=datetime.now(timezone.utc),
        )

        if not transition_result.success:
            result.completed_at = datetime.now(timezone.utc)
            return result

        all_specs = transition_result.all_action_specs

        if self.log_execution and all_specs:
            logger.info(
                f"Executing {len(all_specs)} actions in PARALLEL for transition "
                f"{transition_result.source_state} -> {transition_result.target_state}"
            )

        if not all_specs:
            result.completed_at = datetime.now(timezone.utc)
            return result

        # Execute all actions concurrently
        tasks = [
            self._async_execute_single(
                spec.name,
                context,
                spec.params if spec.has_params else None,
            )
            for spec in all_specs
        ]
        action_results = await asyncio.gather(*tasks, return_exceptions=False)
        result.action_results = list(action_results)

        result.completed_at = datetime.now(timezone.utc)

        if self.log_execution:
            if result.all_succeeded:
                logger.info(
                    f"All {len(all_specs)} actions completed successfully "
                    f"in parallel in {result.duration_ms:.2f}ms"
                )
            else:
                logger.warning(
                    f"Parallel execution completed with failures: {result.failed_actions}"
                )

        return result

    async def async_execute_phased(
        self,
        transition_result: TransitionResult,
        context: dict[str, Any],
    ) -> ExecutionResult:
        """Execute actions in phases: exit -> transition -> enter.

        Within each phase, actions run in parallel. Phases execute sequentially:
        1. All on_exit actions run in parallel
        2. All transition actions run in parallel
        3. All on_enter actions run in parallel

        This provides a balance between parallelism and respecting the natural
        order of state machine transitions.

        Use this when:
        - Exit actions should complete before transition actions
        - Enter actions should run after transition actions
        - Actions within each phase are independent

        Args:
            transition_result: The transition result containing actions.
            context: Context dictionary for action execution.

        Returns:
            ExecutionResult with details of all action executions.
        """
        result = ExecutionResult(
            transition_result=transition_result,
            execution_mode=ExecutionMode.PHASED,
            started_at=datetime.now(timezone.utc),
        )

        if not transition_result.success:
            result.completed_at = datetime.now(timezone.utc)
            return result

        phases = [
            ("exit", transition_result.on_exit_actions),
            ("transition", transition_result.actions_to_execute),
            ("enter", transition_result.on_enter_actions),
        ]

        total_actions = sum(len(specs) for _, specs in phases)

        if self.log_execution and total_actions:
            logger.info(
                f"Executing {total_actions} actions in PHASED mode for transition "
                f"{transition_result.source_state} -> {transition_result.target_state}"
            )

        all_results: list[ActionResult] = []

        for phase_name, action_specs in phases:
            if not action_specs:
                continue

            if self.log_execution:
                logger.debug(f"Executing {len(action_specs)} {phase_name} actions in parallel")

            # Execute phase actions in parallel
            tasks = [
                self._async_execute_single(
                    spec.name,
                    context,
                    spec.params if spec.has_params else None,
                )
                for spec in action_specs
            ]
            phase_results = await asyncio.gather(*tasks, return_exceptions=False)
            all_results.extend(phase_results)

            # Check for failures if stop_on_error is set
            if self.stop_on_error:
                failed = [r for r in phase_results if not r.success]
                if failed:
                    if self.log_execution:
                        logger.error(
                            f"Phase '{phase_name}' had failures, stopping: "
                            f"{[r.action_name for r in failed]}"
                        )
                    break

        result.action_results = all_results
        result.completed_at = datetime.now(timezone.utc)

        if self.log_execution:
            if result.all_succeeded:
                logger.info(
                    f"All {total_actions} actions completed successfully "
                    f"in phased mode in {result.duration_ms:.2f}ms"
                )
            else:
                logger.warning(
                    f"Phased execution completed with failures: {result.failed_actions}"
                )

        return result

    async def async_execute_with_mode(
        self,
        transition_result: TransitionResult,
        context: dict[str, Any],
        mode: ExecutionMode | None = None,
    ) -> ExecutionResult:
        """Execute actions using the specified mode.

        Args:
            transition_result: The transition result containing actions.
            context: Context dictionary for action execution.
            mode: Execution mode (defaults to self.default_mode).

        Returns:
            ExecutionResult with details of all action executions.
        """
        mode = mode or self.default_mode

        if mode == ExecutionMode.PARALLEL:
            return await self.async_execute_parallel(transition_result, context)
        elif mode == ExecutionMode.PHASED:
            return await self.async_execute_phased(transition_result, context)
        else:
            return await self.async_execute(transition_result, context)

    async def async_execute_specific_parallel(
        self,
        actions: list[str] | tuple[str, ...],
        context: dict[str, Any],
    ) -> list[ActionResult]:
        """Execute a specific list of actions in parallel.

        Args:
            actions: List of action names to execute.
            context: Context dictionary.

        Returns:
            List of ActionResult objects.
        """
        if not actions:
            return []

        tasks = [
            self._async_execute_single(action_name, context)
            for action_name in actions
        ]
        return list(await asyncio.gather(*tasks, return_exceptions=False))
