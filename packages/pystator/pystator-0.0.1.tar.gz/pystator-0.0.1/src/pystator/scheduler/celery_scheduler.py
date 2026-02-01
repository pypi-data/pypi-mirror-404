"""CeleryScheduler: Task queue scheduler using Celery.

Uses Celery for task scheduling and execution.
Requires the celery package: pip install celery

Trade-offs:
- Production-ready: robust task queue with retries, monitoring
- Distribution: workers can run on multiple machines
- Requires: Celery + broker (Redis/RabbitMQ)
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Callable, Awaitable, TYPE_CHECKING

from pystator.scheduler.base import (
    SchedulerAdapter,
    ScheduledTask,
    TaskStatus,
    generate_task_id,
)


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from celery import Celery


class CeleryScheduler(SchedulerAdapter):
    """Task queue scheduler using Celery.
    
    Creates Celery tasks that fire after the specified delay.
    Tasks are persistent (depending on broker) and can be
    distributed across multiple workers.
    
    Requires:
        pip install celery
        
        Plus a broker like Redis or RabbitMQ.
    
    Example:
        >>> from celery import Celery
        >>> 
        >>> celery_app = Celery('tasks', broker='redis://localhost:6379')
        >>> scheduler = CeleryScheduler(celery_app)
        >>> 
        >>> # Register the Celery task (do this once at app startup)
        >>> scheduler.register_task()
        >>> 
        >>> task_id = await scheduler.schedule(
        ...     delay_ms=5000,
        ...     callback=handle_timeout,
        ...     entity_id="order-123",
        ...     event="timeout",
        ... )
    
    Note:
        The callback must be serializable or you need to use a
        callback registry pattern where callbacks are looked up
        by name at execution time.
    """
    
    def __init__(
        self,
        celery_app: "Celery",
        task_name: str = "pystator.scheduler.fire_task",
    ) -> None:
        """Initialize the Celery scheduler.
        
        Args:
            celery_app: Celery application instance.
            task_name: Name for the Celery task.
        """
        self._app = celery_app
        self._task_name = task_name
        self._tasks: dict[str, ScheduledTask] = {}
        self._callbacks: dict[str, Callable[[], None] | Callable[[], Awaitable[None]]] = {}
        self._celery_task = None
    
    def register_task(self) -> None:
        """Register the Celery task.
        
        Call this once at application startup to register the
        task with Celery. The task will look up and execute
        callbacks by task_id.
        """
        scheduler = self
        
        @self._app.task(name=self._task_name, bind=True)
        def fire_task(celery_self, task_id: str, entity_id: str, event: str) -> dict[str, Any]:
            """Celery task that fires a scheduled callback."""
            import asyncio
            
            logger.debug(f"Celery firing task {task_id} for {entity_id}:{event}")
            
            info = scheduler._tasks.get(task_id)
            if info:
                info.status = TaskStatus.RUNNING
                info.fired_at = datetime.now(timezone.utc)
            
            callback = scheduler._callbacks.get(task_id)
            result = {"task_id": task_id, "status": "no_callback"}
            
            if callback is not None:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        # Run async callback in event loop
                        loop = asyncio.new_event_loop()
                        try:
                            loop.run_until_complete(callback())
                        finally:
                            loop.close()
                    else:
                        callback()
                    
                    if info:
                        info.status = TaskStatus.COMPLETED
                    result = {"task_id": task_id, "status": "completed"}
                    logger.debug(f"Celery task {task_id} completed")
                    
                except Exception as e:
                    if info:
                        info.status = TaskStatus.FAILED
                    result = {"task_id": task_id, "status": "failed", "error": str(e)}
                    logger.exception(f"Celery task {task_id} failed: {e}")
                    raise
                finally:
                    scheduler._callbacks.pop(task_id, None)
            
            return result
        
        self._celery_task = fire_task
        logger.info(f"Registered Celery task: {self._task_name}")
    
    async def schedule(
        self,
        delay_ms: int,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
        entity_id: str,
        event: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Schedule a callback to run after delay_ms milliseconds."""
        if self._celery_task is None:
            raise RuntimeError(
                "Celery task not registered. Call register_task() first."
            )
        
        task_id = generate_task_id()
        now = datetime.now(timezone.utc)
        
        # Store task info
        info = ScheduledTask(
            task_id=task_id,
            entity_id=entity_id,
            event=event,
            delay_ms=delay_ms,
            status=TaskStatus.PENDING,
            scheduled_at=now,
            metadata=metadata or {},
        )
        self._tasks[task_id] = info
        self._callbacks[task_id] = callback
        
        # Schedule Celery task with countdown
        countdown_seconds = delay_ms / 1000.0
        self._celery_task.apply_async(
            args=[task_id, entity_id, event],
            countdown=countdown_seconds,
            task_id=task_id,
        )
        
        logger.debug(f"Scheduled Celery task {task_id}: {entity_id}:{event} in {delay_ms}ms")
        return task_id
    
    async def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        info = self._tasks.get(task_id)
        if info is None or info.status != TaskStatus.PENDING:
            return False
        
        # Revoke Celery task
        self._app.control.revoke(task_id, terminate=True)
        
        info.status = TaskStatus.CANCELLED
        self._callbacks.pop(task_id, None)
        
        logger.debug(f"Cancelled Celery task {task_id}")
        return True
    
    async def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get information about a scheduled task."""
        return self._tasks.get(task_id)
    
    async def get_pending_tasks(self, entity_id: str | None = None) -> list[ScheduledTask]:
        """Get all pending tasks, optionally filtered by entity."""
        tasks = [t for t in self._tasks.values() if t.status == TaskStatus.PENDING]
        
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
        
        return cancelled
    
    async def close(self) -> None:
        """Cleanup resources."""
        # Cancel all pending tasks
        for task_id in list(self._tasks.keys()):
            info = self._tasks.get(task_id)
            if info and info.status == TaskStatus.PENDING:
                await self.cancel(task_id)
        
        self._tasks.clear()
        self._callbacks.clear()
        logger.info("CeleryScheduler closed")
