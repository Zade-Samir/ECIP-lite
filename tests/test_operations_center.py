"""
Tests for Operations Center (Prompt 098).
"""
import pytest
from services.operations_center.operations_backend import OperationsBackend


def test_operations_dashboard_and_incidents():
    backend = OperationsBackend()

    data = backend.refresh_dashboard()
    assert data["platform_status"] == "HEALTHY"

    inc_id = backend.create_incident("EmbeddingService", "HIGH", "Latency spike above 500ms")
    assert inc_id.startswith("INC-")

    data_updated = backend.refresh_dashboard()
    assert data_updated["open_incidents_count"] == 1
