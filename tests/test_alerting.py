import unittest
from ecip_core.metrics.collector import MetricsCollector
from services.alerting.alert_manager import AlertManager


class TestAlerting(unittest.TestCase):

    def setUp(self):
        self.collector = MetricsCollector()
        self.collector.clear()
        self.alert_manager = AlertManager(self.collector)

    def test_alert_rule_evaluation_and_trigger(self):
        # Initial: no alerts firing
        self.alert_manager.evaluate_rules()
        self.assertEqual(len(self.alert_manager.active_alerts), 0)

        # Trigger high API latency threshold (> 200ms)
        self.collector.record_metric("api_latency_ms", 300.0)
        self.alert_manager.evaluate_rules()

        self.assertEqual(len(self.alert_manager.active_alerts), 1)
        self.assertIn("api_latency_high", self.alert_manager.active_alerts)
        self.assertEqual(len(self.alert_manager.triggered_notifications), 1)

    def test_duplicate_alert_suppression(self):
        self.collector.record_metric("api_latency_ms", 300.0)
        
        # Evaluate twice
        self.alert_manager.evaluate_rules()
        self.alert_manager.evaluate_rules()

        # Should only trigger 1 notification (suppressed the duplicate alert)
        self.assertEqual(len(self.alert_manager.active_alerts), 1)
        self.assertEqual(len(self.alert_manager.triggered_notifications), 1)

    def test_alert_resolution(self):
        self.collector.record_metric("api_latency_ms", 300.0)
        self.alert_manager.evaluate_rules()
        self.assertEqual(len(self.alert_manager.active_alerts), 1)

        # Record a low latency measurement to resolve alert
        self.collector.clear()
        self.collector.record_metric("api_latency_ms", 50.0)
        self.alert_manager.evaluate_rules()

        # Alert should be resolved (removed from active list)
        self.assertEqual(len(self.alert_manager.active_alerts), 0)
        self.assertEqual(self.alert_manager.triggered_notifications[-1]["message"], "RESOLVED: api_latency_high")


if __name__ == "__main__":
    unittest.main()
