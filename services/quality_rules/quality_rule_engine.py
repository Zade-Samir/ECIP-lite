"""
Quality Rule Engine — Evaluates quality baselines, threshold limits, and regression trends.
"""
from typing import Any, Dict, List, Optional
from ecip_core.common.logger import get_logger
from services.code_quality.quality_analyzer import QualityMetrics

logger = get_logger(__name__)


class QualityRuleEngine:
    """
    Evaluates current quality metrics against baseline thresholds and historical trends.
    """

    def __init__(self, min_maintainability: float = 65.0, max_complexity: float = 15.0):
        self.min_maintainability = min_maintainability
        self.max_complexity = max_complexity

    def evaluate(self, current: QualityMetrics, baseline: Optional[QualityMetrics] = None) -> Dict[str, Any]:
        logger.info("Rules evaluated")
        violations = []

        if current.maintainability_index < self.min_maintainability:
            logger.warning("Threshold exceeded")
            violations.append(f"Maintainability index {current.maintainability_index} is below threshold {self.min_maintainability}")

        if current.cyclomatic_complexity > self.max_complexity:
            logger.warning("Threshold exceeded")
            violations.append(f"Cyclomatic complexity {current.cyclomatic_complexity} exceeds max {self.max_complexity}")

        if baseline:
            if current.maintainability_index < baseline.maintainability_index - 5.0:
                logger.warning("Quality regression detected")
                violations.append("Maintainability index regressed by > 5 points from baseline.")

        return {
            "passed": len(violations) == 0,
            "violations": violations,
            "metrics": {
                "maintainability": current.maintainability_index,
                "complexity": current.cyclomatic_complexity,
                "duplication": current.duplication_percentage,
            },
        }
