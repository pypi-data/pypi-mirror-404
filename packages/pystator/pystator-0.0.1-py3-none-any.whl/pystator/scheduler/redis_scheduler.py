"""RedisScheduler: Persistent scheduler using Redis.

Uses Redis sorted sets for persistence and distribution.
Requires the redis package: pip install redis

Trade-offs:
- Persistence: tasks survive process restarts
- Distribution: multiple processes can share tasks
- Requires: Redis server and redis-py package
"""

from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Awaitable, TYPE_CHECKING

from pystator.scheduler.base import (
    SchedulerAdapter,
    ScheduledTask,
    TaskStatus,
    generate_task_id,
)


logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from redis.asyncio import Redis


class RedisScheduler(SchedulerAdapter):
    """Persistent scheduler using Redis sorted sets.
    
    Tasks are stored in Redis sorted sets ordered by fire time.
    A polling loop checks for due tasks and executes callbacks.
    
    Requires:
        pip install redis
    
    Example:
        >>> from redis.asyncio import Redis
        >>> 
        >>> redis = Redis.from_url("redis://localhost:6379")
        >>> scheduler = RedisScheduler(redis)
        >>> await scheduler.start()  # Start the polling loop
        >>> 
        >>> task_id = await scheduler.schedule(
        ...     delay_ms=5000,
        ...     callback=handle_timeout,
        ...     entity_id="order-123",
        ...     event="timeout",
        ... )
        >>> 
        >>> await scheduler.close()  # Stop polling and cleanup
    """
    
    def __init__(
        self,
        redis: "Redis",
        key_prefix: str = "pystator:scheduler:",
        poll_interval_ms: int = 100,
    ) -> None:
        """Initialize the Redis scheduler.
        
        Args:
            redis: Async Redis client.
            key_prefix: Prefix for Redis keys.
            poll_interval_ms: How often to check for due tasks (ms).
        """
        self._redis = redis
        self._prefix = key_prefix
        self._poll_interval = poll_interval_ms / 1000.0
        
        # Keys
        self._tasks_key = f"{key_prefix}tasks"  # Sorted set: score=fire_time
        self._data_key = f"{key_prefix}data:"  # Hash: task data
        
        # Runtime state
        self._callbacks: dict[str, Callable[[], None] | Callable[[], Awaitable[None]]] = {}
        self._running = False
        self._poll_task: asyncio.Task[None] | None = None
    
    async def start(self) -> None:
        """Start the polling loop.
        
        Must be called before tasks will fire. The polling loop
        checks Redis for due tasks and executes their callbacks.
        """
        if self._running:
            return
        
        self._running = True
        self._poll_task = asyncio.create_task(self._poll_loop())
        logger.info("RedisScheduler started")
    
    async def _poll_loop(self) -> None:
        """Poll for due tasks and execute callbacks."""
        while self._running:
            try:
                await self._process_due_tasks()
            except Exception as e:
                logger.exception(f"Error in poll loop: {e}")
            
            await asyncio.sleep(self._poll_interval)
    
    async def _process_due_tasks(self) -> None:
        """Process all tasks that are due."""
        now = datetime.now(timezone.utc).timestamp() * 1000
        
        # Get due tasks (score <= now)
        due_tasks = await self._redis.zrangebyscore(
            self._tasks_key, 0, now, start=0, num=100
        )
        
        for task_id_bytes in due_tasks:
            task_id = task_id_bytes.decode() if isinstance(task_id_bytes, bytes) else task_id_bytes
            await self._fire_task(task_id)
    
    async def _fire_task(self, task_id: str) -> None:
        """Fire a single task."""
        # Remove from sorted set (atomic)
        removed = await self._redis.zrem(self._tasks_key, task_id)
        if not removed:
            return  # Already processed
        
        # Get task data
        data_key = f"{self._data_key}{task_id}"
        data = await self._redis.hgetall(data_key)
        if not data:
            return
        
        # Decode data
        entity_id = data.get(b"entity_id", b"").decode()
        event = data.get(b"event", b"").decode()
        
        # Update status
        await self._redis.hset(data_key, mapping={
            "status": TaskStatus.RUNNING.value,
            "fired_at": datetime.now(timezone.utc).isoformat(),
        })
        
        logger.debug(f"Firing task {task_id} for {entity_id}:{event}")
        
        # Execute callback
        callback = self._callbacks.get(task_id)
        if callback is not None:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
                
                await self._redis.hset(data_key, "status", TaskStatus.COMPLETED.value)
                logger.debug(f"Task {task_id} completed")
                
            except Exception as e:
                await self._redis.hset(data_key, "status", TaskStatus.FAILED.value)
                logger.exception(f"Task {task_id} failed: {e}")
            finally:
                self._callbacks.pop(task_id, None)
        else:
            # No callback - just mark completed (useful for distributed scenarios)
            await self._redis.hset(data_key, "status", TaskStatus.COMPLETED.value)
    
    async def schedule(
        self,
        delay_ms: int,
        callback: Callable[[], None] | Callable[[], Awaitable[None]],
        entity_id: str,
        event: str,
        metadata: dict[str, Any] | None = None,
    ) -> str:
        """Schedule a callback to run after delay_ms milliseconds."""
        task_id = generate_task_id()
        
        now = datetime.now(timezone.utc)
        fire_time = now.timestamp() * 1000 + delay_ms
        
        # Store task data
        data_key = f"{self._data_key}{task_id}"
        await self._redis.hset(data_key, mapping={
            "task_id": task_id,
            "entity_id": entity_id,
            "event": event,
            "delay_ms": str(delay_ms),
            "status": TaskStatus.PENDING.value,
            "scheduled_at": now.isoformat(),
            "metadata": json.dumps(metadata or {}),
        })
        
        # Add to sorted set with fire time as score
        await self._redis.zadd(self._tasks_key, {task_id: fire_time})
        
        # Store callback locally
        self._callbacks[task_id] = callback
        
        logger.debug(f"Scheduled task {task_id}: {entity_id}:{event} in {delay_ms}ms")
        return task_id
    
    async def cancel(self, task_id: str) -> bool:
        """Cancel a scheduled task."""
        # Remove from sorted set
        removed = await self._redis.zrem(self._tasks_key, task_id)
        
        if removed:
            # Update status
            data_key = f"{self._data_key}{task_id}"
            await self._redis.hset(data_key, "status", TaskStatus.CANCELLED.value)
            self._callbacks.pop(task_id, None)
            logger.debug(f"Cancelled task {task_id}")
            return True
        
        return False
    
    async def get_task(self, task_id: str) -> ScheduledTask | None:
        """Get information about a scheduled task."""
        data_key = f"{self._data_key}{task_id}"
        data = await self._redis.hgetall(data_key)
        
        if not data:
            return None
        
        # Decode bytes
        data = {k.decode() if isinstance(k, bytes) else k: v.decode() if isinstance(v, bytes) else v
                for k, v in data.items()}
        
        return ScheduledTask(
            task_id=data.get("task_id", task_id),
            entity_id=data.get("entity_id", ""),
            event=data.get("event", ""),
            delay_ms=int(data.get("delay_ms", 0)),
            status=TaskStatus(data.get("status", TaskStatus.PENDING.value)),
            scheduled_at=datetime.fromisoformat(data["scheduled_at"]) if "scheduled_at" in data else datetime.now(timezone.utc),
            metadata=json.loads(data.get("metadata", "{}")),
        )
    
    async def get_pending_tasks(self, entity_id: str | None = None) -> list[ScheduledTask]:
        """Get all pending tasks, optionally filtered by entity."""
        # Get all pending task IDs from sorted set
        task_ids = await self._redis.zrange(self._tasks_key, 0, -1)
        
        tasks = []
        for task_id_bytes in task_ids:
            task_id = task_id_bytes.decode() if isinstance(task_id_bytes, bytes) else task_id_bytes
            task = await self.get_task(task_id)
            
            if task and task.status == TaskStatus.PENDING:
                if entity_id is None or task.entity_id == entity_id:
                    tasks.append(task)
        
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
        """Stop polling and cleanup."""
        self._running = False
        
        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None
        
        self._callbacks.clear()
        logger.info("RedisScheduler closed")
