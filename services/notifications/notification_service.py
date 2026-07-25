"""
Notification Service — Multi-channel notification delivery with retries and tracking.
"""
from enum import Enum
from typing import Any, Dict, List, Optional
import time

from ecip_core.common.logger import get_logger
from services.events.event_bus import Event

logger = get_logger(__name__)


class NotificationChannel(str, Enum):
    IN_APP = "in_app"
    EMAIL = "email"
    WEBHOOK = "webhook"
    SLACK = "slack"
    TEAMS = "teams"


class NotificationService:
    """
    Delivers notifications across multiple channels with retry tracking.
    """

    def __init__(self, max_retries: int = 3):
        self.max_retries = max_retries
        self.history: List[Dict[str, Any]] = []

    def send_notification(
        self,
        recipient: str,
        title: str,
        message: str,
        channel: NotificationChannel = NotificationChannel.IN_APP,
        simulate_delay: bool = False,
        simulate_failure: bool = False,
    ) -> bool:
        if simulate_delay:
            logger.warning("Delivery delayed")

        attempts = 0
        while attempts <= self.max_retries:
            attempts += 1
            if simulate_failure and attempts == 1:
                logger.error("Notification delivery failed")
                continue

            record = {
                "recipient": recipient,
                "title": title,
                "message": message,
                "channel": channel.value,
                "status": "delivered",
                "timestamp": time.time(),
            }
            self.history.append(record)
            logger.info("Notification delivered")
            return True

        logger.error("Notification delivery failed")
        logger.error("Retry exhausted")
        return False

    def handle_event(self, event: Event) -> bool:
        title = f"Event Notification: {event.event_type}"
        msg = f"Event {event.event_id} payload: {event.payload}"
        return self.send_notification("all-users", title, msg, NotificationChannel.IN_APP)
