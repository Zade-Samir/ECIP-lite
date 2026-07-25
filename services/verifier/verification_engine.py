"""
Verification Engine — Evaluates rules and validates autonomous execution results.
"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class VerificationRule:
    rule_id: str
    description: str
    check_fn: Callable[[Dict[str, Any]], bool]


@dataclass
class VerificationReport:
    is_valid: bool
    passed_rules: List[str]
    failed_rules: List[str]
    details: Dict[str, Any] = field(default_factory=dict)


class VerificationEngine:
    """
    Validates completed autonomous execution results against defined rules.
    """

    def __init__(self):
        self.rules: Dict[str, VerificationRule] = {}

    def register_rule(self, rule: VerificationRule) -> None:
        self.rules[rule.rule_id] = rule

    def verify(self, execution_result: Dict[str, Any]) -> VerificationReport:
        logger.info("Verification started")

        passed = []
        failed = []

        for r_id, rule in self.rules.items():
            try:
                ok = rule.check_fn(execution_result)
                if ok:
                    passed.append(r_id)
                else:
                    failed.append(r_id)
            except Exception:
                failed.append(r_id)

        is_valid = len(failed) == 0
        if is_valid:
            logger.info("Validation passed")
        else:
            logger.error("Validation failed")

        return VerificationReport(
            is_valid=is_valid,
            passed_rules=passed,
            failed_rules=failed,
            details={"total_checked": len(self.rules)},
        )
