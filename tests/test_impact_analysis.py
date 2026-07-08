import sqlite3
# Monkey-patch sqlite3 for multi-threaded access
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

import unittest
from unittest.mock import patch, MagicMock
from ecip_core.dependency.impact_analysis import ImpactAnalysisEngine
from ecip_core.dependency.models.impact_report import ImpactReport
from ecip_core.dependency.models.relationship import Relationship


def make_rel(src, tgt, rel_type="DEPENDS_ON", depth=1, project_id="test-proj"):
    return Relationship(
        source_class=src,
        target_class=tgt,
        relationship_type=rel_type,
        depth=depth,
        project_id=project_id
    )


class TestImpactAnalysis(unittest.TestCase):

    @patch("ecip_core.dependency.impact_analysis.DependencyQueryService")
    def test_direct_impact(self, mock_svc_class):
        mock_svc = mock_svc_class.return_value
        mock_svc._check_class_exists.return_value = True
        mock_svc.get_dependents.side_effect = lambda cls, pid: (
            [make_rel("UserController", "UserService")] if cls == "UserService" else []
        )

        engine = ImpactAnalysisEngine("test-proj")
        report = engine.analyze("UserService", depth=1)

        self.assertIsInstance(report, ImpactReport)
        self.assertEqual(report.target_class, "UserService")
        self.assertIn("UserController", report.affected_classes)
        self.assertEqual(report.total_affected, 1)
        self.assertEqual(len(report.warnings), 0)

    @patch("ecip_core.dependency.impact_analysis.DependencyQueryService")
    def test_multi_level_impact(self, mock_svc_class):
        mock_svc = mock_svc_class.return_value
        mock_svc._check_class_exists.return_value = True

        def mock_get_dependents(cls, pid):
            if cls == "UserRepository":
                return [make_rel("UserService", "UserRepository")]
            elif cls == "UserService":
                return [make_rel("UserController", "UserService")]
            return []

        mock_svc.get_dependents.side_effect = mock_get_dependents

        engine = ImpactAnalysisEngine("test-proj")
        report = engine.analyze("UserRepository", depth=2)

        self.assertIn("UserService", report.affected_classes)
        self.assertIn("UserController", report.affected_classes)
        self.assertEqual(report.total_affected, 2)

    @patch("ecip_core.dependency.impact_analysis.DependencyQueryService")
    def test_circular_dependency_detection(self, mock_svc_class):
        mock_svc = mock_svc_class.return_value
        mock_svc._check_class_exists.return_value = True

        def mock_get_dependents(cls, pid):
            if cls == "ServiceA":
                return [make_rel("ServiceB", "ServiceA")]
            elif cls == "ServiceB":
                return [make_rel("ServiceA", "ServiceB")]
            return []

        mock_svc.get_dependents.side_effect = mock_get_dependents

        engine = ImpactAnalysisEngine("test-proj")
        report = engine.analyze("ServiceA", depth=3)

        circular_warnings = [w for w in report.warnings if "Circular dependency" in w]
        self.assertGreater(len(circular_warnings), 0)

    @patch("ecip_core.dependency.impact_analysis.DependencyQueryService")
    def test_empty_impact_for_leaf_class(self, mock_svc_class):
        mock_svc = mock_svc_class.return_value
        mock_svc._check_class_exists.return_value = True
        mock_svc.get_dependents.return_value = []

        engine = ImpactAnalysisEngine("test-proj")
        report = engine.analyze("UserRepository", depth=2)

        self.assertEqual(report.affected_classes, [])
        self.assertEqual(report.total_affected, 0)

    @patch("ecip_core.dependency.impact_analysis.DependencyQueryService")
    def test_unknown_class_returns_empty_report(self, mock_svc_class):
        mock_svc = mock_svc_class.return_value
        mock_svc._check_class_exists.return_value = False

        engine = ImpactAnalysisEngine("test-proj")

        with self.assertLogs("ecip_core.dependency.impact_analysis", level="WARNING") as log_capture:
            report = engine.analyze("NonExistentClass", depth=2)
            self.assertEqual(report.affected_classes, [])
            self.assertEqual(report.total_affected, 0)
            self.assertTrue(any("Unknown class" in w for w in report.warnings))

    @patch("ecip_core.dependency.impact_analysis.DependencyQueryService")
    def test_deterministic_ordering(self, mock_svc_class):
        mock_svc = mock_svc_class.return_value
        mock_svc._check_class_exists.return_value = True
        mock_svc.get_dependents.side_effect = lambda cls, pid: (
            [
                make_rel("ZController", "UserService"),
                make_rel("AController", "UserService"),
            ] if cls == "UserService" else []
        )

        engine = ImpactAnalysisEngine("test-proj")
        report = engine.analyze("UserService", depth=1)

        self.assertEqual(report.affected_classes[0], "AController")
        self.assertEqual(report.affected_classes[1], "ZController")

    @patch("ecip_core.dependency.impact_analysis.DependencyQueryService")
    def test_report_serialization(self, mock_svc_class):
        mock_svc = mock_svc_class.return_value
        mock_svc._check_class_exists.return_value = True
        mock_svc.get_dependents.return_value = [make_rel("UserController", "UserService")]

        engine = ImpactAnalysisEngine("test-proj")
        report = engine.analyze("UserService", depth=1)
        serialized = report.model_dump()

        self.assertIn("project_id", serialized)
        self.assertIn("target_class", serialized)
        self.assertIn("affected_classes", serialized)
        self.assertIn("dependency_tree", serialized)
        self.assertIn("total_affected", serialized)
        self.assertIn("warnings", serialized)
        self.assertEqual(serialized["target_class"], "UserService")


if __name__ == "__main__":
    unittest.main()
