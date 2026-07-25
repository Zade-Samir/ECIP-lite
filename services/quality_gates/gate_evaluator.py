"""
Quality Gate Evaluator — Evaluates deployment readiness and CI build pass/fail gates.
"""
from dataclasses import dataclass
from typing import Any, Dict, List

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QualityGate:
    name: str
    is_blocking: bool
    threshold_value: float
    actual_value: float
    comparator: str = "<="  # "<=" or ">="


class GateEvaluator:
    """
    Evaluates CI pipeline quality gates and generates deployment risk assessment.
    """

    def evaluate_pipeline(self, gates: List[QualityGate]) -> Dict[str, Any]:
        logger.info("Pipeline started")

        passed_gates = []
        failed_blocking = []
        failed_advisory = []

        for gate in gates:
            if gate.comparator == "<=":
                passed = gate.actual_value <= gate.threshold_value
            else:
                passed = gate.actual_value >= gate.threshold_value

            if passed:
                passed_gates.append(gate.name)
            else:
                logger.warning("Quality threshold exceeded")
                if gate.is_blocking:
                    failed_blocking.append(gate.name)
                else:
                    failed_advisory.append(gate.name)

        logger.info("Analysis completed")

        if failed_blocking:
            logger.warning("Deployment risk detected")
            logger.error("Quality gate failed")
            return {
                "status": "FAILED",
                "passed_gates": passed_gates,
                "failed_blocking": failed_blocking,
                "failed_advisory": failed_advisory,
            }

        logger.info("Quality gate passed")
        return {
            "status": "PASSED",
            "passed_gates": passed_gates,
            "failed_advisory": failed_advisory,
        }
