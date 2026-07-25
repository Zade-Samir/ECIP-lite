"""
Tests for Verification Engine (Prompt 081).
"""
import pytest
from services.verifier.verification_engine import VerificationEngine, VerificationRule


def test_verification_pass():
    ve = VerificationEngine()
    ve.register_rule(VerificationRule(
        rule_id="r1",
        description="Check status is success",
        check_fn=lambda res: res.get("status") == "success"
    ))

    report = ve.verify({"status": "success"})
    assert report.is_valid is True
    assert report.passed_rules == ["r1"]


def test_verification_fail():
    ve = VerificationEngine()
    ve.register_rule(VerificationRule(
        rule_id="r1",
        description="Check status is success",
        check_fn=lambda res: res.get("status") == "success"
    ))

    report = ve.verify({"status": "failed"})
    assert report.is_valid is False
    assert report.failed_rules == ["r1"]
