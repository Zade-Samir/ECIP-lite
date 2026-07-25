import time
from typing import Dict, Any, List
from pydantic import BaseModel, Field
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class MetricSample(BaseModel):
    name: str  # e.g., "api_latency_ms", "cpu_usage_percent"
    value: float
    timestamp: float = Field(default_factory=time.time)
    tags: Dict[str, str] = Field(default_factory=dict)


class MetricsCollector:
    """Collects and aggregates system and operational metrics."""

    def __init__(self):
        self.samples: List[MetricSample] = []

    def record_metric(self, name: str, value: float, tags: Dict[str, str] = None):
        try:
            sample = MetricSample(name=name, value=value, tags=tags or {})
            self.samples.append(sample)
            logger.info("Metric collected")
        except Exception as e:
            logger.error("Monitoring failure")
            raise e

    def get_average_metric(self, name: str, seconds: float = 60.0) -> float:
        cutoff = time.time() - seconds
        relevant = [s.value for s in self.samples if s.name == name and s.timestamp >= cutoff]
        if not relevant:
            return 0.0
        return sum(relevant) / len(relevant)

    def clear(self):
        self.samples.clear()


metrics_collector = MetricsCollector()
