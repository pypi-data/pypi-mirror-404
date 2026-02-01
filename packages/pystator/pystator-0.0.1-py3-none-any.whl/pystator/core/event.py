"""Event definitions for PyStator FSM."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import UUID, uuid4


@dataclass(frozen=True, slots=True)
class Event:
    """Immutable event that triggers state transitions.

    Events are the inputs to the FSM that cause state changes. Each event
    has a trigger (the event type/name) and an optional payload with
    additional data that can be used by guards and actions.

    The event also carries metadata for idempotency checking (event_id)
    and audit trails (timestamp).

    Attributes:
        trigger: The event type name (must match transition triggers).
        payload: Additional data associated with the event.
        event_id: Unique identifier for idempotency checking.
        timestamp: When the event was created (UTC).
        source: Origin of the event (e.g., "exchange", "user", "system").
        metadata: Additional event metadata.

    Example:
        >>> event = Event(
        ...     trigger="execution_report",
        ...     payload={"fill_qty": 100, "fill_price": 50.25},
        ...     source="exchange",
        ... )
        >>> result = machine.process("OPEN", event, context)
    """

    trigger: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: UUID = field(default_factory=uuid4)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    source: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.trigger:
            raise ValueError("Event trigger cannot be empty")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a value from the event payload."""
        return self.payload.get(key, default)

    def __getitem__(self, key: str) -> Any:
        """Get a value from the event payload."""
        return self.payload[key]

    def __contains__(self, key: str) -> bool:
        """Check if key exists in payload."""
        return key in self.payload

    def with_payload(self, **kwargs: Any) -> "Event":
        """Create a new Event with additional payload data."""
        new_payload = {**self.payload, **kwargs}
        return Event(
            trigger=self.trigger,
            payload=new_payload,
            event_id=self.event_id,
            timestamp=self.timestamp,
            source=self.source,
            metadata=self.metadata,
        )

    def with_metadata(self, **kwargs: Any) -> "Event":
        """Create a new Event with additional metadata."""
        new_metadata = {**self.metadata, **kwargs}
        return Event(
            trigger=self.trigger,
            payload=self.payload,
            event_id=self.event_id,
            timestamp=self.timestamp,
            source=self.source,
            metadata=new_metadata,
        )

    @classmethod
    def simple(cls, trigger: str, **payload: Any) -> "Event":
        """Create a simple event with trigger and payload."""
        return cls(trigger=trigger, payload=payload)

    def to_dict(self) -> dict[str, Any]:
        """Serialize event to dictionary for storage/transmission."""
        return {
            "trigger": self.trigger,
            "payload": self.payload,
            "event_id": str(self.event_id),
            "timestamp": self.timestamp.isoformat(),
            "source": self.source,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Event":
        """Deserialize event from dictionary."""
        return cls(
            trigger=data["trigger"],
            payload=data.get("payload", {}),
            event_id=UUID(data["event_id"]) if "event_id" in data else uuid4(),
            timestamp=(
                datetime.fromisoformat(data["timestamp"])
                if "timestamp" in data
                else datetime.now(timezone.utc)
            ),
            source=data.get("source", ""),
            metadata=data.get("metadata", {}),
        )
