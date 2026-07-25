from typing import Dict, Any, List
from ecip_core.common.logger import get_logger
from ecip_core.metrics.collector import MetricsCollector

logger = get_logger(__name__)


class AlertManager:
    """Evaluates rules and delivers notifications when thresholds are crossed."""

    def __init__(self, metrics_collector: MetricsCollector):
        self.collector = metrics_collector
        self.active_alerts: Dict[str, Dict[str, Any]] = {}
        self.triggered_notifications: List[Dict[str, Any]] = []

    def evaluate_rules(self):
        # 1. API Latency Rule
        api_lat = self.collector.get_average_metric("api_latency_ms")
        if api_lat > 200:
            logger.warning("Threshold exceeded")
            logger.warning("Slow service detected")
            self._trigger_alert("api_latency_high", f"Average API latency of {api_lat:.1f}ms exceeds threshold of 200ms")
        else:
            self._resolve_alert("api_latency_high")

        # 2. CPU Usage Rule
        cpu_usage = self.collector.get_average_metric("cpu_usage_percent")
        if cpu_usage > 90:
            logger.warning("Threshold exceeded")
            self._trigger_alert("cpu_usage_critical", f"CPU utilization at {cpu_usage:.1f}% exceeds critical threshold of 90%")
        else:
            self._resolve_alert("cpu_usage_critical")

    def _trigger_alert(self, rule_name: str, message: str):
        if rule_name not in self.active_alerts:
            alert = {
                "rule": rule_name,
                "message": message,
                "status": "firing"
            }
            self.active_alerts[rule_name] = alert
            logger.info("Alert triggered")
            self._deliver_notification(rule_name, message)

    def _resolve_alert(self, rule_name: str):
        if rule_name in self.active_alerts:
            self.active_alerts.pop(rule_name)
            logger.info("Alert resolved")
            self._deliver_notification(rule_name, f"RESOLVED: {rule_name}")

    def _deliver_notification(self, rule_name: str, message: str):
        notification = {
            "rule": rule_name,
            "message": message,
            "channel": "Slack/Email"
        }
        try:
            self.triggered_notifications.append(notification)
        except Exception as e:
            logger.error("Alert delivery failure")
            raise e
