"""
Tests for DevOps Copilot (Prompt 097).
"""
import pytest
from services.devops_copilot.devops_engine import DevOpsCopilotEngine


def test_k8s_manifest_analysis():
    engine = DevOpsCopilotEngine()
    manifests = [
        {
            "kind": "Deployment",
            "metadata": {"name": "user-service"},
            "spec": {"template": {"spec": {"containers": [{"name": "web"}]}}},
        }
    ]

    report = engine.analyze_infrastructure(manifests)
    assert report["total_manifests_analyzed"] == 1
    assert len(report["recommendations"]) == 1
    assert "missing container CPU/memory resource limits" in report["recommendations"][0]
