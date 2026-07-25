"""
Readiness Engine — Aggregates enterprise subsystem signals into unified GO/NO-GO release decisions.
"""
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.release_gates.release_gate_evaluator import ReleaseGate, ReleaseGateEvaluator

logger = get_logger(__name__)


class ReadinessEngine:
    """
    Computes overall deployment readiness score and produces explainable release reports.
    """

    def __init__(self, evaluator: Optional[ReleaseGateEvaluator] = None):
        self.evaluator = evaluator or ReleaseGateEvaluator()

    def evaluate_release(self, gates: List[ReleaseGate]) -> Dict[str, Any]:
        logger.info("Readiness evaluation started")
        try:
            gate_res = self.evaluator.evaluate_gates(gates)
            total_score = sum(g.score for g in gates if g.passed)
            max_possible = max(1.0, float(len(gates) * 100))
            readiness_score = round((total_score / max_possible) * 100.0, 1)

            logger.info("Release score calculated")

            is_go = gate_res["all_blocking_passed"] and readiness_score >= 70.0
            if not is_go:
                logger.warning("Elevated deployment risk")

            report = {
                "decision": "GO" if is_go else "NO-GO",
                "readiness_score": readiness_score,
                "all_blocking_passed": gate_res["all_blocking_passed"],
                "passed_gates": gate_res["passed_gates"],
                "failed_blocking": gate_res["failed_blocking"],
                "failed_advisory": gate_res["failed_advisory"],
                "summary": f"Release Decision: {'GO' if is_go else 'NO-GO'} (Score: {readiness_score}/100)",
            }

            logger.info("Report generated")
            return report

        except Exception as e:
            logger.error("Readiness evaluation failed")
            raise e
