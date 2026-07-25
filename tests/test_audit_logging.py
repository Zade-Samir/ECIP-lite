import unittest
import time
import json
from ecip_core.security.audit.audit_service import AuditLoggingService


class TestAuditLogging(unittest.TestCase):

    def setUp(self):
        self.audit_service = AuditLoggingService()
        self.audit_service.record_event(
            actor="admin",
            tenant_id="tenant_a",
            action="login",
            resource_id="auth",
            status="success"
        )
        self.audit_service.record_event(
            actor="bob",
            tenant_id="tenant_b",
            action="query_execution",
            resource_id="UserService",
            status="success"
        )
        self.audit_service.record_event(
            actor="hacker",
            tenant_id="tenant_a",
            action="login",
            resource_id="auth",
            status="denied",
            details="invalid password"
        )

    def test_audit_event_persistence_and_search(self):
        # A should have 2 events
        events_a = self.audit_service.get_events("tenant_a")
        self.assertEqual(len(events_a), 2)
        
        # B should have 1 event
        events_b = self.audit_service.get_events("tenant_b")
        self.assertEqual(len(events_b), 1)
        self.assertEqual(events_b[0].actor, "bob")

    def test_audit_export_json_and_csv(self):
        json_str = self.audit_service.export_to_json("tenant_a")
        data = json.loads(json_str)
        self.assertEqual(len(data), 2)
        self.assertEqual(data[0]["actor"], "admin")

        csv_str = self.audit_service.export_to_csv("tenant_b")
        self.assertIn("bob", csv_str)
        self.assertIn("query_execution", csv_str)

    def test_retention_policy(self):
        # Record an old event artificially by mocking timestamp
        event = self.audit_service.record_event(
            actor="old_user",
            tenant_id="tenant_a",
            action="logout",
            resource_id="session"
        )
        event.timestamp = time.time() - 3600  # 1 hour ago
        
        # Total events should be 4
        self.assertEqual(len(self.audit_service._audit_records), 4)

        # Apply retention policy of 1800 seconds (30 mins)
        self.audit_service.apply_retention_policy(1800)

        # Old event should be removed
        self.assertEqual(len(self.audit_service._audit_records), 3)
        actors = [e.actor for e in self.audit_service._audit_records]
        self.assertNotIn("old_user", actors)


if __name__ == "__main__":
    unittest.main()
