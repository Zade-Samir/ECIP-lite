"""
Tests for Notification Service (Prompt 076).
"""
import pytest
from services.events.event_bus import Event
from services.notifications.notification_service import NotificationChannel, NotificationService


def test_notification_delivery():
    ns = NotificationService()
    res = ns.send_notification("bob", "Test", "Hello Bob", NotificationChannel.IN_APP)
    assert res is True
    assert len(ns.history) == 1
    assert ns.history[0]["recipient"] == "bob"


def test_notification_event_handler():
    ns = NotificationService()
    ev = Event(event_type="BackupCompleted", payload={"backup_id": "b123"})
    res = ns.handle_event(ev)
    assert res is True
    assert len(ns.history) == 1


def test_notification_retry():
    ns = NotificationService(max_retries=2)
    # Simulate temporary failure that succeeds on retry
    res = ns.send_notification("charlie", "Alert", "Msg", simulate_failure=True)
    assert res is True
