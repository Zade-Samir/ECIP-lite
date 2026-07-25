"""
Recommendation Engine — Generates prioritized architecture improvement recommendations.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.architecture_advisor.architecture_rules import DEFAULT_RULES, ArchitectureRule

logger = get_logger(__name__)


@dataclass
class Recommendation:
    rule_id: str
    category: str
    target: str
    summary: str
    severity: str
    impact_score: float


class RecommendationEngine:
    """
    Analyzes codebase graph metadata and generates prioritized architecture recommendations.
    """

    def __init__(self, rules: Optional[List[ArchitectureRule]] = None):
        self.rules = rules or DEFAULT_RULES

    def analyze(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]) -> List[Recommendation]:
        logger.info("Analysis started")
        if not nodes:
            logger.warning("Incomplete graph")

        recommendations = []
        for rule in self.rules:
            try:
                violations = rule.evaluate_fn(nodes, edges)
                for v in violations:
                    rec = Recommendation(
                        rule_id=rule.rule_id,
                        category=rule.category,
                        target=v["target"],
                        summary=v["reason"],
                        severity=v["severity"],
                        impact_score=0.9 if v["severity"] == "HIGH" else 0.5,
                    )
                    recommendations.append(rec)
            except Exception as e:
                logger.error("Rule engine failure")
                logger.error("Analysis failure")
                raise e

        recommendations.sort(key=lambda r: r.impact_score, reverse=True)
        logger.info("Recommendations generated")
        return recommendations

    def export_report(self, recommendations: List[Recommendation]) -> Dict[str, Any]:
        report = {
            "total_recommendations": len(recommendations),
            "high_severity_count": sum(1 for r in recommendations if r.severity == "HIGH"),
            "items": [
                {
                    "rule_id": r.rule_id,
                    "target": r.target,
                    "summary": r.summary,
                    "severity": r.severity,
                    "impact_score": r.impact_score,
                }
                for r in recommendations
            ],
        }
        logger.info("Report exported")
        return report
