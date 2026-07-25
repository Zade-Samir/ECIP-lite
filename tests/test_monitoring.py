import unittest
from ecip_core.metrics.collector import MetricsCollector
from services.monitoring.health_monitor import HealthMonitor


class TestMonitoring(unittest.TestCase):

    def setUp(self):
        self.collector = MetricsCollector()
        self.monitor = HealthMonitor(self.collector)

    def test_metric_collection_and_average(self):
        self.collector.record_metric("api_latency_ms", 150.0)
        self.collector.record_metric("api_latency_ms", 250.0)
        
        avg = self.collector.get_average_metric("api_latency_ms")
        self.assertEqual(avg, 200.0)

    def test_health_aggregation_and_slo(self):
        self.collector.record_metric("api_latency_ms", 100.0)
        self.collector.record_metric("llm_latency_ms", 3000.0)

        health = self.monitor.get_service_health()
        self.assertEqual(health["status"], "healthy")
        self.assertTrue(health["sla"]["api_latency_slo_compliant"])

        # Record high API latency to degrade state
        self.collector.record_metric("api_latency_ms", 1100.0)
        
        health_degraded = self.monitor.get_service_health()
        self.assertEqual(health_degraded["status"], "degraded")
        self.assertFalse(health_degraded["sla"]["api_latency_slo_compliant"])


if __name__ == "__main__":
    unittest.main()
