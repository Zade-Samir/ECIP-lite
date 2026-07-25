"""
Tests for Security Analyzer (Prompt 089).
"""
import pytest
from services.security_intelligence.security_analyzer import SecurityAnalyzer


def test_security_analyzer_repository_scan():
    analyzer = SecurityAnalyzer()
    files = {
        "src/Secret.java": 'String secret_key = "12345678901234567890";',
        "src/App.java": 'MessageDigest.getInstance("MD5");',
    }

    findings = analyzer.scan_repository(files)
    assert len(findings) >= 2

    score = analyzer.calculate_risk_score(findings)
    assert score > 0.0

    report = analyzer.export_report(findings)
    assert report["total_findings"] >= 2
    assert "risk_score" in report
