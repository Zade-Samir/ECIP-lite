"""
Subscription Manager — Manages user event subscription preferences.
"""
from typing import Dict, List, Set, Optional
from ecip_core.common.logger import get_logger
from services.notifications.notification_service import NotificationChannel

logger = get_logger(__name__)


class SubscriptionManager:
    """
    Tracks user event subscriptions and preferences.
    """

    def __init__(self):
        # user_id -> {event_type -> Set[NotificationChannel]}
        self._user_subscriptions: Dict[str, Dict[str, Set[NotificationChannel]]] = {}
        self._offline_users: Set[str] = set()

    def register_subscriber(self, user_id: str, event_type: str, channel: NotificationChannel) -> None:
        if user_id not in self._user_subscriptions:
            self._user_subscriptions[user_id] = {}
        if event_type not in self._user_subscriptions[user_id]:
            self._user_subscriptions[user_id][event_type] = set()

        self._user_subscriptions[user_id][event_type].add(channel)
        logger.info("Subscriber registered")

    def set_user_offline(self, user_id: str):
        self._offline_users.add(user_id)

    def is_user_available(self, user_id: str) -> bool:
        if user_id in self._offline_users:
            logger.warning("Subscriber unavailable")
            return False
        return True

    def get_subscriptions(self, user_id: str, event_type: str) -> Set[NotificationChannel]:
        if not self.is_user_available(user_id):
            return set()
        return self._user_subscriptions.get(user_id, {}).get(event_type, set())
