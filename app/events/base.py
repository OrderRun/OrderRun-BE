"""Domain event base classes and in-process event bus."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

if TYPE_CHECKING:
    from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class DomainEvent:
    pass


class EventBus:
    _handlers: dict[type, list[Callable]] = {}

    @classmethod
    def register(cls, event_type: type, handler: Callable) -> None:
        handlers = cls._handlers.setdefault(event_type, [])
        if handler not in handlers:
            handlers.append(handler)

    @classmethod
    def publish(cls, event: DomainEvent, db: Session) -> None:
        for handler in cls._handlers.get(type(event), []):
            try:
                handler(event, db)
            except Exception:
                logger.exception("Event handler %s failed for %s", handler.__name__, type(event).__name__)
