"""Event idempotency checking for PyStator FSM.

Provides pluggable backends for tracking processed events to prevent
duplicate processing (at-most-once or exactly-once semantics).
"""

from __future__ import annotations

import logging
import threading
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Protocol, runtime_checkable
from uuid import UUID

logger = logging.getLogger(__name__)


@dataclass
class IdempotencyRecord:
    """Record of a processed event.

    Attributes:
        event_id: Unique identifier of the event.
        processed_at: When the event was processed.
        result_state: The resulting state after processing (optional).
        metadata: Additional metadata about the processing.
    """

    event_id: str
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    result_state: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@runtime_checkable
class IdempotencyBackend(Protocol):
    """Protocol for idempotency checking backends.

    Implementations store and retrieve records of processed events.
    The backend must support:
    - Checking if an event has been processed
    - Marking an event as processed
    - Optional TTL for automatic cleanup
    """

    def has_processed(self, event_id: str) -> bool:
        """Check if an event has already been processed.

        Args:
            event_id: Unique identifier of the event.

        Returns:
            True if the event has been processed, False otherwise.
        """
        ...

    def mark_processed(
        self,
        event_id: str,
        result_state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark an event as processed.

        Args:
            event_id: Unique identifier of the event.
            result_state: Optional resulting state after processing.
            metadata: Optional additional metadata.
        """
        ...

    def get_record(self, event_id: str) -> IdempotencyRecord | None:
        """Get the idempotency record for an event.

        Args:
            event_id: Unique identifier of the event.

        Returns:
            The idempotency record if found, None otherwise.
        """
        ...


class InMemoryIdempotencyBackend:
    """In-memory idempotency backend for single-instance deployments.

    Stores processed event records in memory with optional TTL.
    NOT suitable for distributed/multi-instance deployments.

    Example:
        >>> backend = InMemoryIdempotencyBackend(ttl_seconds=3600)
        >>> backend.mark_processed("event-123", result_state="FILLED")
        >>> backend.has_processed("event-123")
        True
    """

    def __init__(
        self,
        ttl_seconds: float | None = None,
        max_size: int | None = 10000,
    ) -> None:
        """Initialize the in-memory backend.

        Args:
            ttl_seconds: Time-to-live for records in seconds.
                If None, records never expire.
            max_size: Maximum number of records to store.
                If None, no limit. When exceeded, oldest records are evicted.
        """
        self._records: dict[str, IdempotencyRecord] = {}
        self._timestamps: dict[str, float] = {}  # For TTL tracking
        self._ttl_seconds = ttl_seconds
        self._max_size = max_size
        self._lock = threading.Lock()

    def has_processed(self, event_id: str) -> bool:
        """Check if an event has been processed."""
        with self._lock:
            self._cleanup_expired()
            return event_id in self._records

    def mark_processed(
        self,
        event_id: str,
        result_state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark an event as processed."""
        with self._lock:
            self._cleanup_expired()
            self._evict_if_full()

            record = IdempotencyRecord(
                event_id=event_id,
                result_state=result_state,
                metadata=metadata or {},
            )
            self._records[event_id] = record
            self._timestamps[event_id] = time.time()

    def get_record(self, event_id: str) -> IdempotencyRecord | None:
        """Get the idempotency record for an event."""
        with self._lock:
            self._cleanup_expired()
            return self._records.get(event_id)

    def clear(self) -> None:
        """Clear all records."""
        with self._lock:
            self._records.clear()
            self._timestamps.clear()

    def _cleanup_expired(self) -> None:
        """Remove expired records (called with lock held)."""
        if self._ttl_seconds is None:
            return

        now = time.time()
        expired = [
            event_id
            for event_id, ts in self._timestamps.items()
            if now - ts > self._ttl_seconds
        ]
        for event_id in expired:
            del self._records[event_id]
            del self._timestamps[event_id]

    def _evict_if_full(self) -> None:
        """Evict oldest records if at capacity (called with lock held)."""
        if self._max_size is None:
            return

        while len(self._records) >= self._max_size:
            # Find oldest record
            oldest_id = min(self._timestamps, key=self._timestamps.get)  # type: ignore
            del self._records[oldest_id]
            del self._timestamps[oldest_id]

    def __len__(self) -> int:
        """Get number of stored records."""
        with self._lock:
            return len(self._records)


class NoOpIdempotencyBackend:
    """No-op backend that always allows processing.

    Use when idempotency checking is not needed.
    """

    def has_processed(self, event_id: str) -> bool:
        """Always returns False."""
        return False

    def mark_processed(
        self,
        event_id: str,
        result_state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Does nothing."""
        pass

    def get_record(self, event_id: str) -> IdempotencyRecord | None:
        """Always returns None."""
        return None


@dataclass
class IdempotencyResult:
    """Result of an idempotency check.

    Attributes:
        is_duplicate: Whether this event was already processed.
        event_id: The event ID that was checked.
        previous_record: If duplicate, the previous processing record.
    """

    is_duplicate: bool
    event_id: str
    previous_record: IdempotencyRecord | None = None


class IdempotencyChecker:
    """High-level idempotency checker for FSM events.

    Wraps a backend and provides convenient methods for checking
    and marking events as processed.

    Example:
        >>> checker = IdempotencyChecker(InMemoryIdempotencyBackend(ttl_seconds=3600))
        >>>
        >>> # Check before processing
        >>> result = checker.check("event-123")
        >>> if result.is_duplicate:
        ...     print(f"Event already processed, result was: {result.previous_record.result_state}")
        >>> else:
        ...     # Process the event...
        ...     checker.mark_processed("event-123", result_state="FILLED")
    """

    def __init__(
        self,
        backend: IdempotencyBackend | None = None,
        enabled: bool = True,
    ) -> None:
        """Initialize the idempotency checker.

        Args:
            backend: Backend for storing idempotency records.
                Defaults to NoOpIdempotencyBackend if not provided.
            enabled: If False, all events are allowed (no checking).
        """
        self.backend = backend if backend is not None else NoOpIdempotencyBackend()
        self.enabled = enabled

    def check(self, event_id: str | UUID) -> IdempotencyResult:
        """Check if an event has been processed.

        Args:
            event_id: Unique identifier of the event.

        Returns:
            IdempotencyResult with duplicate status.
        """
        event_id_str = str(event_id)

        if not self.enabled:
            return IdempotencyResult(
                is_duplicate=False,
                event_id=event_id_str,
            )

        is_duplicate = self.backend.has_processed(event_id_str)
        previous_record = None

        if is_duplicate:
            previous_record = self.backend.get_record(event_id_str)

        return IdempotencyResult(
            is_duplicate=is_duplicate,
            event_id=event_id_str,
            previous_record=previous_record,
        )

    def mark_processed(
        self,
        event_id: str | UUID,
        result_state: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Mark an event as processed.

        Args:
            event_id: Unique identifier of the event.
            result_state: Optional resulting state after processing.
            metadata: Optional additional metadata.
        """
        if not self.enabled:
            return

        event_id_str = str(event_id)
        self.backend.mark_processed(event_id_str, result_state, metadata)

    def check_and_mark(
        self,
        event_id: str | UUID,
    ) -> IdempotencyResult:
        """Atomically check if processed and mark if not.

        This is useful for "claim" semantics where you want to ensure
        only one processor handles an event.

        Args:
            event_id: Unique identifier of the event.

        Returns:
            IdempotencyResult. If is_duplicate is False, the event was
            atomically marked as being processed.
        """
        event_id_str = str(event_id)

        if not self.enabled:
            return IdempotencyResult(
                is_duplicate=False,
                event_id=event_id_str,
            )

        # For in-memory backend, we can do this atomically
        if isinstance(self.backend, InMemoryIdempotencyBackend):
            with self.backend._lock:
                self.backend._cleanup_expired()
                if event_id_str in self.backend._records:
                    return IdempotencyResult(
                        is_duplicate=True,
                        event_id=event_id_str,
                        previous_record=self.backend._records[event_id_str],
                    )
                # Mark as processing
                self.backend._evict_if_full()
                record = IdempotencyRecord(event_id=event_id_str)
                self.backend._records[event_id_str] = record
                self.backend._timestamps[event_id_str] = time.time()
                return IdempotencyResult(
                    is_duplicate=False,
                    event_id=event_id_str,
                )

        # For other backends, do check-then-mark (not atomic)
        result = self.check(event_id_str)
        if not result.is_duplicate:
            self.mark_processed(event_id_str)
        return result
