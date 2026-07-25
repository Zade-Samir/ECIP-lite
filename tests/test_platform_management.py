"""
Tests for Platform Management & Capacity Forecasting (Prompt 098).
"""
import pytest
from services.operations_center.operations_backend import OperationsBackend


def test_capacity_forecasting():
    backend = OperationsBackend()
    forecast = backend.forecast_capacity(growth_rate_percent=20.0)

    assert forecast["current_storage_gb"] == 500
    assert forecast["forecast_30_days_gb"] == 600.0
    assert "Provision +100GB" in forecast["recommendation"]
