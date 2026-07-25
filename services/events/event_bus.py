"""
Event Bus — In-process publish-subscribe system for Enterprise events.
"""
import uuid
import datetime
import threading
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Event:
    event_type: str
    payload: Dict[str, Any]
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = "default"
    timestamp: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat())


class EventBus:
    """
    Central event bus for subscribing handlers to domain events.
    """

    def __init__(self):
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: Callable[[Event], None]) -> None:
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
        logger.info("Subscriber registered")

    def publish(self, event: Event) -> int:
        logger.info("Event published")
        with self._lock:
            handlers = list(self._subscribers.get(event.event_type, [])) + list(self._subscribers.get("*", []))

        delivered_count = 0
        for handler in handlers:
            try:
                handler(event)
                delivered_count += 1
            except Exception as e:
                logger.error("Event processing failed")

        return delivered_count


# Global singleton EventBus
event_bus = EventBus()
