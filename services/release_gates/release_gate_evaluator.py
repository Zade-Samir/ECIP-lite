"""
Release Gate Evaluator — Evaluates blocking and advisory release gates across enterprise subsystems.
"""
from dataclasses import dataclass
from typing import Any, Dict, List

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReleaseGate:
    name: str
    category: str
    is_blocking: bool
    passed: bool
    score: float = 100.0
    details: str = ""


class ReleaseGateEvaluator:
    """
    Evaluates subsystem health signals against release readiness gates.
    """

    def evaluate_gates(self, gates: List[ReleaseGate]) -> Dict[str, Any]:
        passed_gates = []
        failed_blocking = []
        failed_advisory = []

        for g in gates:
            if g.passed:
                passed_gates.append(g.name)
            else:
                if g.is_blocking:
                    failed_blocking.append(g.name)
                    logger.error("Blocking gate failed")
                else:
                    failed_advisory.append(g.name)
                    logger.warning("Advisory gate failed")

        return {
            "all_blocking_passed": len(failed_blocking) == 0,
            "passed_gates": passed_gates,
            "failed_blocking": failed_blocking,
            "failed_advisory": failed_advisory,
        }
