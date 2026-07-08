import os
import json
import time
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from ecip_core.metrics.collector import MetricsCollector, metrics_collector


class TestMetrics(unittest.TestCase):

    def setUp(self):
        self.collector = MetricsCollector()
        self.collector.clear()

    def tearDown(self):
        self.collector.clear()

    def test_timer_starts_and_stops(self):
        """Timer starts, measures elapsed duration, and records statistics."""
        self.collector.start_timer("test_op")
        time.sleep(0.01)  # sleep for ~10ms
        elapsed = self.collector.stop_timer("test_op")

        self.assertIsNotNone(elapsed)
        self.assertGreater(elapsed, 0)
        
        stats = self.collector.get_stats("test_op")
        self.assertEqual(stats["count"], 1)
        self.assertGreater(stats["total_ms"], 0)
        self.assertAlmostEqual(stats["total_ms"], elapsed, places=4)

    def test_timer_context_manager(self):
        """Context manager 'timer' automatically records performance execution times."""
        with self.collector.timer("ctx_op"):
            time.sleep(0.005)

        stats = self.collector.get_stats("ctx_op")
        self.assertEqual(stats["count"], 1)
        self.assertGreater(stats["total_ms"], 0)

    def test_nested_timers_with_different_names(self):
        """Nested timers of different names compile concurrently without conflict."""
        with self.collector.timer("outer_op"):
            time.sleep(0.002)
            with self.collector.timer("inner_op"):
                time.sleep(0.003)

        outer_stats = self.collector.get_stats("outer_op")
        inner_stats = self.collector.get_stats("inner_op")

        self.assertEqual(outer_stats["count"], 1)
        self.assertEqual(inner_stats["count"], 1)
        self.assertGreater(outer_stats["total_ms"], inner_stats["total_ms"])

    def test_nested_same_name_timers_lifo_nesting(self):
        """Nested same-name timers resolve correctly using LIFO stack."""
        self.collector.start_timer("nested_same")
        time.sleep(0.002)
        
        self.collector.start_timer("nested_same")
        time.sleep(0.003)
        inner_elapsed = self.collector.stop_timer("nested_same")
        
        time.sleep(0.002)
        outer_elapsed = self.collector.stop_timer("nested_same")

        self.assertGreater(outer_elapsed, inner_elapsed)
        stats = self.collector.get_stats("nested_same")
        self.assertEqual(stats["count"], 2)

    def test_missing_metric_warning_no_crash(self):
        """Stopping a non-existent timer logs warning and returns None instead of crashing."""
        with self.assertLogs("ecip_core.metrics.collector", level="WARNING") as log:
            elapsed = self.collector.stop_timer("non_existent_timer")
            self.assertIsNone(elapsed)
            self.assertTrue(any("Missing metric" in m for m in log.output))

    def test_metrics_aggregation_math(self):
        """Aggregates multiple runs and computes correct stats (min, max, average, total)."""
        # Inject custom completed runs directly for accurate math verification
        cid = "test-cid"
        self.collector._completed_runs[cid]["math_op"] = [10.0, 20.0, 30.0]

        stats = self.collector.get_stats("math_op")
        self.assertEqual(stats["count"], 3)
        self.assertAlmostEqual(stats["total_ms"], 60.0)
        self.assertAlmostEqual(stats["avg_ms"], 20.0)
        self.assertAlmostEqual(stats["min_ms"], 10.0)
        self.assertAlmostEqual(stats["max_ms"], 30.0)

    def test_json_export_and_file_writing(self):
        """JSON report exports correctly and writes report file."""
        self.collector.start_timer("export_op")
        self.collector.stop_timer("export_op")

        with TemporaryDirectory() as tmpdir:
            dest_file = Path(tmpdir) / "sub" / "metrics.json"
            json_report = self.collector.export_json(file_path=str(dest_file))

            # Verify return payload
            data = json.loads(json_report)
            self.assertIn("active_profile", data)
            self.assertIn("metrics", data)
            self.assertEqual(len(data["metrics"]), 1)
            self.assertEqual(data["metrics"][0]["metric"], "export_op")

            # Verify file exists and holds same data
            self.assertTrue(dest_file.exists())
            file_data = json.loads(dest_file.read_text(encoding="utf-8"))
            self.assertEqual(file_data["metrics"][0]["metric"], "export_op")


if __name__ == "__main__":
    unittest.main()
