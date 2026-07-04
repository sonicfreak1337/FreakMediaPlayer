"""Small domain event primitives."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Generic, TypeVar
from uuid import UUID, uuid4

PayloadT = TypeVar("PayloadT")


@dataclass(frozen=True)
class DomainEvent(Generic[PayloadT]):
    name: str
    payload: PayloadT
    event_id: UUID = field(default_factory=uuid4)
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))


class EventBus:
    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[DomainEvent[object]], None]]] = {}

    def subscribe(self, event_name: str, handler: Callable[[DomainEvent[object]], None]) -> None:
        self._subscribers.setdefault(event_name, []).append(handler)

    def publish(self, event: DomainEvent[object]) -> None:
        for handler in self._subscribers.get(event.name, []):
            handler(event)
