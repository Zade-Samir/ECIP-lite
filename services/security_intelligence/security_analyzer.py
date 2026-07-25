"""
Security Analyzer — Orchestrates multi-file security scanning and risk scoring.
"""
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.security_rules.vulnerability_scanner import SecurityFinding, Severity, VulnerabilityScanner

logger = get_logger(__name__)


class SecurityAnalyzer:
    """
    Security Intelligence platform scanner and risk assessment engine.
    """

    def __init__(self, scanner: Optional[VulnerabilityScanner] = None):
        self.scanner = scanner or VulnerabilityScanner()

    def scan_repository(self, files: Dict[str, str]) -> List[SecurityFinding]:
        logger.info("Scan started")
        all_findings = []

        try:
            for file_path, content in files.items():
                findings = self.scanner.scan_content(file_path, content)
                all_findings.extend(findings)
        except Exception as e:
            logger.error("Scan failed")
            raise e

        logger.info("Findings generated")
        return all_findings

    def calculate_risk_score(self, findings: List[SecurityFinding]) -> float:
        weights = {
            Severity.CRITICAL: 25.0,
            Severity.HIGH: 10.0,
            Severity.MEDIUM: 5.0,
            Severity.LOW: 1.0,
        }
        score = sum(weights.get(f.severity, 1.0) for f in findings)
        return min(100.0, round(score, 1))

    def export_report(self, findings: List[SecurityFinding]) -> Dict[str, Any]:
        score = self.calculate_risk_score(findings)
        report = {
            "total_findings": len(findings),
            "risk_score": score,
            "findings": [
                {
                    "finding_id": f.finding_id,
                    "rule": f.rule_name,
                    "severity": f.severity.value,
                    "file": f.file_path,
                    "line": f.line_number,
                    "description": f.description,
                    "remediation": f.remediation,
                }
                for f in findings
            ],
        }
        logger.info("Report exported")
        return report
