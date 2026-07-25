"""
Tests for Analytics & Usage Insights (Prompt 073).
"""
import pytest
from ecip_core.metrics.privacy_filter import PrivacyFilter
from services.analytics.aggregation_engine import AggregationEngine
from services.analytics.analytics_service import AnalyticsService


@pytest.fixture
def analytics_svc(tmp_path):
    db_file = tmp_path / "test_analytics.db"
    svc = AnalyticsService(db_path=str(db_file), enabled=True)
    return svc


def test_privacy_filter():
    raw_meta = {
        "user_query": "search query",
        "code": "public class Secret { private String key; }",
        "prompt": "Explain code",
        "normal_key": "normal_val"
    }
    filtered = PrivacyFilter.sanitize(raw_meta)
    assert filtered["code"] == "[REDACTED]"
    assert filtered["prompt"] == "[REDACTED]"
    assert filtered["normal_key"] == "normal_val"


def test_record_and_get_events(analytics_svc):
    res = analytics_svc.record_event(
        tenant_id="tenant-1",
        user_id="user-100",
        domain="retrieval",
        event_type="hybrid_search",
        latency_ms=45.2,
        metadata={"code": "select * from table"}
    )
    assert res is True

    events = analytics_svc.get_events(tenant_id="tenant-1")
    assert len(events) == 1
    assert events[0]["domain"] == "retrieval"
    assert events[0]["metadata"]["code"] == "[REDACTED]"


def test_analytics_disabled(tmp_path):
    db_file = tmp_path / "disabled.db"
    disabled_svc = AnalyticsService(db_path=str(db_file), enabled=False)
    res = disabled_svc.record_event("t1", "u1", "query", "search")
    assert res is False
    assert disabled_svc.get_events() == []


def test_aggregation(analytics_svc):
    analytics_svc.record_event("t1", "u1", "retrieval", "search", latency_ms=10.0)
    analytics_svc.record_event("t1", "u2", "retrieval", "search", latency_ms=30.0)
    analytics_svc.record_event("t1", "u1", "llm", "chat", latency_ms=200.0)

    agg = AggregationEngine(analytics_svc)
    metrics = agg.aggregate("t1")

    assert metrics["total_events"] == 3
    assert metrics["active_users_count"] == 2
    assert metrics["avg_retrieval_latency_ms"] == 20.0
    assert metrics["avg_llm_latency_ms"] == 200.0
