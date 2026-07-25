"""
DevOps Copilot Engine — Infrastructure analyzer, Kubernetes manifest checker, and CI/CD optimizer.
"""
from typing import Any, Dict, List

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class DevOpsCopilotEngine:
    """
    Assists platform engineers with Docker, K8s, Helm, cost optimization, and CI/CD pipelines.
    """

    def analyze_infrastructure(self, manifests: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("Infrastructure analysis started")

        if not manifests:
            logger.warning("Missing deployment metadata")

        recs = []
        for m in manifests:
            kind = m.get("kind", "")
            if kind == "Deployment":
                resources = m.get("spec", {}).get("template", {}).get("spec", {}).get("containers", [{}])[0].get("resources")
                if not resources:
                    recs.append(f"Deployment {m.get('metadata', {}).get('name', 'app')} is missing container CPU/memory resource limits.")

        logger.info("Recommendations generated")

        report = {
            "total_manifests_analyzed": len(manifests),
            "recommendations": recs,
        }

        logger.info("Report exported")
        return report
