"""
Tests for Event Bus & Subscriptions (Prompt 076).
"""
import pytest
from services.events.event_bus import Event, EventBus
from services.subscriptions.subscription_manager import SubscriptionManager
from services.notifications.notification_service import NotificationChannel


def test_event_publish_subscribe():
    bus = EventBus()
    received = []

    def handler(ev: Event):
        received.append(ev)

    bus.subscribe("ProjectIndexed", handler)
    event = Event(event_type="ProjectIndexed", payload={"project_id": "sampleProject"})
    count = bus.publish(event)

    assert count == 1
    assert len(received) == 1
    assert received[0].payload["project_id"] == "sampleProject"


def test_subscription_manager():
    sm = SubscriptionManager()
    sm.register_subscriber("alice", "JobFailed", NotificationChannel.EMAIL)

    chans = sm.get_subscriptions("alice", "JobFailed")
    assert NotificationChannel.EMAIL in chans

    sm.set_user_offline("alice")
    chans_offline = sm.get_subscriptions("alice", "JobFailed")
    assert len(chans_offline) == 0
