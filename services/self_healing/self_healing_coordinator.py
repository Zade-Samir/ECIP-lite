"""
Self Healing Coordinator — Coordinates recovery strategies and escalates when self-healing fails.
"""
from typing import Any, Callable, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.verifier.verification_engine import VerificationEngine, VerificationReport

logger = get_logger(__name__)


class SelfHealingCoordinator:
    """
    Attempts automatic recovery on verification failure, escalates to human on persistent failure.
    """

    def __init__(self, verifier: VerificationEngine):
        self.verifier = verifier
        self.recovery_strategies: Dict[str, Callable[[Dict[str, Any]], Dict[str, Any]]] = {}

    def register_strategy(self, rule_id: str, strategy_fn: Callable[[Dict[str, Any]], Dict[str, Any]]) -> None:
        self.recovery_strategies[rule_id] = strategy_fn

    def heal_and_verify(
        self,
        execution_result: Dict[str, Any],
        max_attempts: int = 2,
        simulate_unrecoverable: bool = False,
    ) -> tuple[bool, VerificationReport]:
        report = self.verifier.verify(execution_result)
        if report.is_valid:
            return True, report

        attempt = 0
        current_result = execution_result

        while attempt < max_attempts and not report.is_valid:
            attempt += 1
            logger.warning("Recovery attempted")

            if simulate_unrecoverable:
                logger.error("Recovery failed")
                break

            # Execute recovery strategy for first failed rule
            failed_rule = report.failed_rules[0]
            strategy = self.recovery_strategies.get(failed_rule)

            if strategy:
                try:
                    current_result = strategy(current_result)
                    logger.info("Recovery completed")
                    report = self.verifier.verify(current_result)
                    if report.is_valid:
                        return True, report
                except Exception:
                    logger.error("Recovery failed")
            else:
                logger.error("Recovery failed")

        # Persistent failure -> Escalate
        logger.warning("Manual approval required")
        logger.error("Escalation triggered")
        return False, report
