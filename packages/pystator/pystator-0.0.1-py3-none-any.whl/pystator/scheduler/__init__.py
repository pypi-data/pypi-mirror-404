"""Scheduler adapters for delayed transitions.

Provides pluggable scheduling backends for handling delayed transitions
in PyStator FSMs. Choose the adapter that fits your infrastructure:

- AsyncioScheduler: Zero infrastructure, in-memory (development, testing)
- RedisScheduler: Persistence + distribution (production with Redis)
- CeleryScheduler: Task queue integration (production with Celery)
"""

from __future__ import annotations

from pystator.scheduler.base import (
    SchedulerAdapter,
    ScheduledTask,
    TaskStatus,
)
from pystator.scheduler.asyncio_scheduler import AsyncioScheduler

__all__ = [
    # Base
    "SchedulerAdapter",
    "ScheduledTask",
    "TaskStatus",
    # Implementations
    "AsyncioScheduler",
]

# Optional imports for Redis and Celery adapters
try:
    from pystator.scheduler.redis_scheduler import RedisScheduler
    __all__.append("RedisScheduler")
except ImportError:
    pass  # Redis not installed

try:
    from pystator.scheduler.celery_scheduler import CeleryScheduler
    __all__.append("CeleryScheduler")
except ImportError:
    pass  # Celery not installed
