"""
Reporting Service — Formats aggregated metrics into JSON/CSV reports.
"""
import csv
import io
import json
from typing import Any, Dict, Optional

from ecip_core.common.logger import get_logger
from services.analytics.aggregation_engine import AggregationEngine

logger = get_logger(__name__)


class ReportingService:
    """
    Generates downloadable reports (CSV/JSON) for enterprise usage.
    """

    def __init__(self, aggregation_engine: AggregationEngine):
        self.aggregation_engine = aggregation_engine

    def generate_report(self, tenant_id: Optional[str] = None, format: str = "json") -> str:
        try:
            agg_data = self.aggregation_engine.aggregate(tenant_id=tenant_id)

            if format == "csv":
                output = io.StringIO()
                writer = csv.writer(output)
                writer.writerow(["Metric", "Value"])
                writer.writerow(["Tenant ID", agg_data["tenant_id"]])
                writer.writerow(["Total Events", agg_data["total_events"]])
                writer.writerow(["Active Users", agg_data["active_users_count"]])
                writer.writerow(["Avg Retrieval Latency (ms)", agg_data["avg_retrieval_latency_ms"]])
                writer.writerow(["Avg LLM Latency (ms)", agg_data["avg_llm_latency_ms"]])

                for domain, count in agg_data.get("domain_breakdown", {}).items():
                    writer.writerow([f"Domain - {domain}", count])

                report_str = output.getvalue()
            else:
                report_str = json.dumps(agg_data, indent=2)

            logger.info("Report generated")
            return report_str
        except Exception as e:
            logger.error("Export failure")
            raise RuntimeError(f"Report generation failed: {e}") from e
