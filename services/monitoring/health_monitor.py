from typing import Dict, Any
from ecip_core.metrics.collector import MetricsCollector


class HealthMonitor:
    """Aggregates system health and tracks SLO compliance across services."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector

    def get_service_health(self) -> Dict[str, Any]:
        avg_api_latency = self.collector.get_average_metric("api_latency_ms")
        avg_retrieval_latency = self.collector.get_average_metric("retrieval_latency_ms")
        avg_llm_latency = self.collector.get_average_metric("llm_latency_ms")

        # Basic database checks (mock connection validation)
        db_healthy = True
        graph_healthy = True

        # Aggregate statuses
        status = "healthy"
        reasons = []

        if avg_api_latency > 500:
            status = "degraded"
            reasons.append("High API latency")
        if avg_llm_latency > 5000:
            status = "degraded"
            reasons.append("High LLM response latency")
        if not db_healthy or not graph_healthy:
            status = "unhealthy"
            reasons.append("Database connection failure")

        return {
            "status": status,
            "reasons": reasons,
            "services": {
                "api": "healthy" if avg_api_latency <= 500 else "degraded",
                "retrieval": "healthy" if avg_retrieval_latency <= 1000 else "degraded",
                "llm": "healthy" if avg_llm_latency <= 5000 else "degraded",
                "database": "healthy" if db_healthy else "unhealthy",
                "graph": "healthy" if graph_healthy else "unhealthy"
            },
            "sla": {
                "slo_api_latency_target_ms": 200,
                "api_latency_slo_compliant": avg_api_latency <= 200
            }
        }
