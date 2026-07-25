"""
Tests for Vulnerability Scanner (Prompt 089).
"""
import pytest
from services.security_rules.vulnerability_scanner import Severity, VulnerabilityScanner


def test_secret_detection():
    scanner = VulnerabilityScanner()
    code = """
    public class Config {
        private String api_key = "AIzaSyD_1234567890123456";
    }
    """
    findings = scanner.scan_content("Config.java", code)
    assert len(findings) == 1
    assert findings[0].severity == Severity.CRITICAL
    assert "Hardcoded Secret Token" in findings[0].description


def test_sql_injection_detection():
    scanner = VulnerabilityScanner()
    code = """
    String query = "SELECT * FROM users WHERE name = '" + userInput;
    Statement.executeQuery(query);
    """
    findings = scanner.scan_content("UserDao.java", code)
    assert any("SQL Injection" in f.description for f in findings)
