"""
Tests for Usage Reporting (Prompt 073).
"""
import pytest
from services.analytics.aggregation_engine import AggregationEngine
from services.analytics.analytics_service import AnalyticsService
from services.reporting.reporting_service import ReportingService


@pytest.fixture
def reporting_svc(tmp_path):
    db_file = tmp_path / "rep_analytics.db"
    analytics = AnalyticsService(db_path=str(db_file), enabled=True)
    analytics.record_event("t-corp", "u-1", "api", "query", latency_ms=15.0)
    analytics.record_event("t-corp", "u-2", "retrieval", "search", latency_ms=25.0)

    agg = AggregationEngine(analytics)
    return ReportingService(agg)


def test_generate_json_report(reporting_svc):
    report = reporting_svc.generate_report(tenant_id="t-corp", format="json")
    assert '"tenant_id": "t-corp"' in report
    assert '"total_events": 2' in report


def test_generate_csv_report(reporting_svc):
    report = reporting_svc.generate_report(tenant_id="t-corp", format="csv")
    assert "Metric,Value" in report
    assert "Tenant ID,t-corp" in report
    assert "Total Events,2" in report
