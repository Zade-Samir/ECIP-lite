"""
Tests for Self Healing Coordinator (Prompt 081).
"""
import pytest
from services.self_healing.self_healing_coordinator import SelfHealingCoordinator
from services.verifier.verification_engine import VerificationEngine, VerificationRule


def test_self_healing_success():
    ve = VerificationEngine()
    ve.register_rule(VerificationRule(
        rule_id="check_data",
        description="Data must be valid",
        check_fn=lambda res: res.get("valid") is True
    ))

    shc = SelfHealingCoordinator(ve)

    def recovery_fn(res):
        # Fix the invalid data
        res["valid"] = True
        return res

    shc.register_strategy("check_data", recovery_fn)

    # Initial result is invalid
    initial = {"valid": False}
    ok, report = shc.heal_and_verify(initial)

    assert ok is True
    assert report.is_valid is True


def test_self_healing_escalation_on_failure():
    ve = VerificationEngine()
    ve.register_rule(VerificationRule(
        rule_id="unfixable",
        description="Unfixable rule",
        check_fn=lambda res: False
    ))

    shc = SelfHealingCoordinator(ve)
    ok, report = shc.heal_and_verify({"status": "bad"}, simulate_unrecoverable=True)

    assert ok is False
    assert report.is_valid is False
