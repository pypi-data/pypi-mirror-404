"""AsyncioScheduler: In-memory scheduler using asyncio.

Zero infrastructure required - uses Python's asyncio for scheduling.
Best for development, testing, and single-process applications.

Trade-offs:
- No persistence: tasks lost on process restart
- No distribution: single process only
- Simple: no external dependencies
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable

from pystator.scheduler.base import (
    SchedulerAdapter,
    ScheduledTask,
    TaskStatus,
    generate_task_id,
)


logger = logging.getLogger(__name__)


class AsyncioScheduler(SchedulerAdapter):
    """In-memory scheduler using asyncio tasks.
    
    Uses asyncio.create_task to schedule callbacks. All state is
    held in memory and lost on process restart.
    
    Example:
        >>> scheduler = AsyncioScheduler()
        >>> 
        >>> async def handle_timeout():
        ...     print("Timeout!")
        >>> 
        >>> task_id = await scheduler.schedule(
        ...     delay_ms=5000,
        ...     callback=handle_timeout,
        ...     entity_id="order-123",
        ...     event="timeout",
        ... )
        >>> 
        >>> # Later, cancel if needed
        >>> cancelled = await scheduler.cancel(task_id)
    """
    
    def __init__(self) -> None:
        """Initialize the asyncio scheduler."""
        self._tasks: dict[str, asyncio.Task[None]] = {}
        self._task_info: dict[str, ScheduledTask] = {}
    
    async def schedule(
        self,
        delay_ms: int,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
        entity_id: str,
        event: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Schedule a callback to run after delay_ms milliseconds.
        
        Creates an asyncio task that sleeps for the delay then calls
        the callback. Both sync and async callbacks are supported.
        """
        task_id = generate_task_id()
        
        # Create task info
        info = ScheduledTask(
            task_id=task_id,
            entity_id=entity_id,
            event=event,
            delay_ms=delay_ms,
            status=TaskStatus.PENDING,
            metadata=metadata or {},
        )
        self._task_info[task_id] = info
        
        # Create the delayed task
        async def _delayed_callback() -> None:
            try:
                await asyncio.sleep(delay_ms / 1000.0)
                
                # Check if cancelled during sleep
                if task_id not in self._task_info:
                    return
                
                info = self._task_info[task_id]
                if info.status != TaskStatus.PENDING:
                    return
                
                # Update status and execute
                info.status = TaskStatus.RUNNING
                info.fired_at = datetime.now(timezone.utc)
                
                logger.debug(f"Firing scheduled task {task_id} for {entity_id}:{event}")
                
                # Call the callback (sync or async)
                if inspect.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                
                info.status = TaskStatus.COMPLETED
                logger.debug(f"Task {task_id} completed successfully")
                
            except asyncio.CancelledError:
                if task_id in self._task_info:
                    self._task_info[task_id].status = TaskStatus.CANCELLED
                logger.debug(f"Task {task_id} was cancelled")
                raise
            except Exception as e:
                if task_id in self._task_info:
                    self._task_info[task_id].status = TaskStatus.FAILED
                logger.exception(f"Task {task_id} failed: {e}")
            finally:
                # Clean up asyncio task reference
                self._tasks.pop(task_id, None)
        
        # Create and store the asyncio task
        task = asyncio.create_task(_delayed_callback())
        self._tasks[task_id] = task
        
        logger.debug(
            f"Scheduled task {task_id}: {entity_id}:{event} in {delay_ms}ms"
        )
        
        return task_id
    
    async def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task.
        
        Cancels the asyncio task and updates the status to CANCELLED.
        """
        info = self._task_info.get(task_id)
        if info is None:
            return False
        
        if info.status != TaskStatus.PENDING:
            return False
        
        # Cancel the asyncio task
        task = self._tasks.get(task_id)
        if task is not None and not task.done():
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        # Update status
        info.status = TaskStatus.CANCELLED
        self._tasks.pop(task_id, None)
        
        logger.debug(f"Cancelled task {task_id}")
        return True
    
    async def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get information about a scheduled task."""
        return self._task_info.get(task_id)
    
    async def get_pending_tasks(self, entity_id: str | None = None) -> list[ScheduledTask]:
        """Get all pending tasks, optionally filtered by entity."""
        tasks = [
            t for t in self._task_info.values()
            if t.status == TaskStatus.PENDING
        ]
        
        if entity_id is not None:
            tasks = [t for t in tasks if t.entity_id == entity_id]
        
        return tasks
    
    async def cancel_for_entity(self, entity_id: str) -> int:
        """Cancel all pending tasks for an entity."""
        tasks = await self.get_pending_tasks(entity_id)
        cancelled = 0
        
        for task in tasks:
            if await self.cancel(task.task_id):
                cancelled += 1
        
        if cancelled:
            logger.debug(f"Cancelled {cancelled} tasks for entity {entity_id}")
        
        return cancelled
    
    async def close(self) -> None:
        """Cancel all pending tasks and clean up."""
        for task_id in list(self._tasks.keys()):
            await self.cancel(task_id)
        
        self._tasks.clear()
        self._task_info.clear()
        
        logger.debug("AsyncioScheduler closed")
    
    @property
    def pending_count(self) -> int:
        """Number of pending tasks."""
        return sum(1 for t in self._task_info.values() if t.status == TaskStatus.PENDING)
    
    @property
    def total_count(self) -> int:
        """Total number of tracked tasks."""
        return len(self._task_info)
