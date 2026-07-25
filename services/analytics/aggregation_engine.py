"""
Aggregation Engine — Aggregates metrics by tenant, user, domain, and latency.
"""
from typing import Any, Dict, Optional

from ecip_core.common.logger import get_logger
from services.analytics.analytics_service import AnalyticsService

logger = get_logger(__name__)


class AggregationEngine:
    """
    Computes statistical aggregations over recorded analytics events.
    """

    def __init__(self, analytics_service: AnalyticsService):
        self.analytics_service = analytics_service

    def aggregate(self, tenant_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            events = self.analytics_service.get_events(tenant_id=tenant_id, limit=5000)

            total_events = len(events)
            active_users = set()
            domains_count: Dict[str, int] = {}
            retrieval_latencies = []
            llm_latencies = []

            for ev in events:
                active_users.add(ev["user_id"])
                domain = ev["domain"]
                domains_count[domain] = domains_count.get(domain, 0) + 1

                if domain == "retrieval" and ev["latency_ms"] > 0:
                    retrieval_latencies.append(ev["latency_ms"])
                elif domain == "llm" and ev["latency_ms"] > 0:
                    llm_latencies.append(ev["latency_ms"])

            avg_retrieval_latency = sum(retrieval_latencies) / len(retrieval_latencies) if retrieval_latencies else 0.0
            avg_llm_latency = sum(llm_latencies) / len(llm_latencies) if llm_latencies else 0.0

            result = {
                "tenant_id": tenant_id or "all",
                "total_events": total_events,
                "active_users_count": len(active_users),
                "domain_breakdown": domains_count,
                "avg_retrieval_latency_ms": round(avg_retrieval_latency, 2),
                "avg_llm_latency_ms": round(avg_llm_latency, 2),
            }

            logger.info("Aggregation completed")
            return result
        except Exception as e:
            logger.error("Aggregation failure")
            raise RuntimeError(f"Aggregation failed: {e}") from e
