"""
Modernization Analyzer — Scans codebase for legacy frameworks, Java versions, and deprecated APIs.
"""
from dataclasses import dataclass
from typing import Any, Dict, List

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ModernizationFinding:
    category: str  # JavaVersion, Framework, DeprecatedAPI
    current_version: str
    target_version: str
    effort_hours: float
    description: str
    breaking_changes: List[str]


class ModernizationAnalyzer:
    """
    Analyzes application metadata and produces modernization finding reports.
    """

    def analyze(self, meta: Dict[str, Any]) -> List[ModernizationFinding]:
        logger.info("Analysis started")
        findings = []

        java_ver = str(meta.get("java_version", "8"))
        if java_ver in ("8", "11", "1.8"):
            findings.append(
                ModernizationFinding(
                    category="JavaVersion",
                    current_version=f"Java {java_ver}",
                    target_version="Java 21 LTS",
                    effort_hours=40.0,
                    description="Upgrade to Java 21 LTS for virtual threads and performance improvements.",
                    breaking_changes=["Deprecated SecurityManager removed", "Strongly encapsulated JDK internals"],
                )
            )

        spring_ver = str(meta.get("spring_boot_version", "2.1.0"))
        if spring_ver.startswith("1.") or spring_ver.startswith("2."):
            logger.warning("Deprecated dependency")
            findings.append(
                ModernizationFinding(
                    category="Framework",
                    current_version=f"Spring Boot {spring_ver}",
                    target_version="Spring Boot 3.2.0",
                    effort_hours=60.0,
                    description="Upgrade Spring Boot 2.x to 3.x.",
                    breaking_changes=["javax.* packages renamed to jakarta.*"],
                )
            )

        frameworks = meta.get("frameworks", [])
        for f in frameworks:
            if f.lower() not in ("spring", "quarkus", "micronaut", "struts"):
                logger.warning("Unsupported framework")

        return findings
