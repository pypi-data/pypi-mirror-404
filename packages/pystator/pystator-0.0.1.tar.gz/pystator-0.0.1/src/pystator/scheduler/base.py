"""Abstract base class for scheduler adapters.

Scheduler adapters handle delayed transitions by scheduling events
to fire after a specified delay. The core FSM remains stateless -
the scheduler manages the timing externally.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable, Awaitable
from uuid import uuid4


class TaskStatus(str, Enum):
    """Status of a scheduled task."""
    
    PENDING = "pending"
    """Task is scheduled but hasn't fired yet."""
    
    RUNNING = "running"
    """Task callback is currently executing."""
    
    COMPLETED = "completed"
    """Task has fired successfully."""
    
    CANCELLED = "cancelled"
    """Task was cancelled before firing."""
    
    FAILED = "failed"
    """Task callback raised an exception."""


@dataclass
class ScheduledTask:
    """Information about a scheduled task.
    
    Attributes:
        task_id: Unique identifier for the task.
        entity_id: Entity this task is for (e.g., order_id).
        event: Event to fire when task triggers.
        delay_ms: Delay in milliseconds.
        status: Current task status.
        scheduled_at: When the task was scheduled.
        fires_at: When the task will fire.
        fired_at: When the task actually fired (if completed).
        metadata: Additional task metadata.
    """
    task_id: str
    entity_id: str
    event: str
    delay_ms: int
    status: TaskStatus = TaskStatus.PENDING
    scheduled_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    fires_at: datetime | None = None
    fired_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self) -> None:
        if self.fires_at is None:
            from datetime import timedelta
            self.fires_at = self.scheduled_at + timedelta(milliseconds=self.delay_ms)
    
    @property
    def remaining_ms(self) -> int:
        """Milliseconds remaining until task fires (0 if past)."""
        if self.fires_at is None:
            return 0
        now = datetime.now(timezone.utc)
        delta = self.fires_at - now
        ms = int(delta.total_seconds() * 1000)
        return max(0, ms)
    
    @property
    def is_pending(self) -> bool:
        """Check if task is still pending."""
        return self.status == TaskStatus.PENDING


def generate_task_id() -> str:
    """Generate a unique task ID."""
    return str(uuid4())


class SchedulerAdapter(ABC):
    """Abstract base class for scheduler adapters.
    
    Scheduler adapters handle the timing of delayed transitions.
    When a delayed transition is encountered, the orchestrator
    schedules an event to fire after the specified delay.
    
    Implementations:
    - AsyncioScheduler: In-memory using asyncio (zero infrastructure)
    - RedisScheduler: Persistence using Redis sorted sets
    - CeleryScheduler: Task queue using Celery
    
    Example:
        >>> scheduler = AsyncioScheduler()
        >>> 
        >>> def on_timeout():
        ...     print("Timeout fired!")
        >>> 
        >>> task_id = await scheduler.schedule(
        ...     delay_ms=5000,
        ...     callback=on_timeout,
        ...     entity_id="order-123",
        ...     event="timeout",
        ... )
        >>> 
        >>> # Cancel if needed
        >>> await scheduler.cancel(task_id)
    """
    
    @abstractmethod
    async def schedule(
        self,
        delay_ms: int,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
        entity_id: str,
        event: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Schedule a callback to run after delay_ms milliseconds.
        
        Args:
            delay_ms: Delay in milliseconds before firing.
            callback: Function to call when delay expires.
            entity_id: Entity ID this task is for.
            event: Event name that will be fired.
            metadata: Optional metadata to store with the task.
        
        Returns:
            Unique task ID for cancellation.
        """
        ...
    
    @abstractmethod
    async def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task.
        
        Args:
            task_id: ID of the task to cancel.
        
        Returns:
            True if task was cancelled, False if not found or already fired.
        """
        ...
    
    @abstractmethod
    async def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get information about a scheduled task.
        
        Args:
            task_id: ID of the task.
        
        Returns:
            ScheduledTask if found, None otherwise.
        """
        ...
    
    @abstractmethod
    async def get_pending_tasks(self, entity_id: str | None = None) -> list[ScheduledTask]:
        """Get all pending tasks, optionally filtered by entity.
        
        Args:
            entity_id: If provided, only return tasks for this entity.
        
        Returns:
            List of pending ScheduledTask objects.
        """
        ...
    
    @abstractmethod
    async def cancel_for_entity(self, entity_id: str) -> int:
        """Cancel all pending tasks for an entity.
        
        Useful when an entity transitions to a new state and
        all pending delayed transitions should be cancelled.
        
        Args:
            entity_id: Entity ID to cancel tasks for.
        
        Returns:
            Number of tasks cancelled.
        """
        ...
    
    async def close(self) -> None:
        """Clean up scheduler resources.
        
        Override this method if your adapter needs cleanup.
        """
        pass
