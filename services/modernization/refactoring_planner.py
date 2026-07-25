"""
Refactoring Planner — Generates phased migration roadmaps from modernization findings.
"""
from typing import Any, Dict, List
from ecip_core.common.logger import get_logger
from services.modernization.modernization_analyzer import ModernizationFinding

logger = get_logger(__name__)


class RefactoringPlanner:
    """
    Generates structured migration phases from modernization findings.
    """

    def generate_migration_plan(self, findings: List[ModernizationFinding]) -> Dict[str, Any]:
        total_hours = sum(f.effort_hours for f in findings)
        phases = [
            {
                "phase": 1,
                "name": "Dependency & Framework Preparation",
                "findings": [f.category for f in findings if f.category in ("Framework", "DeprecatedAPI")],
            },
            {
                "phase": 2,
                "name": "Java Runtime & Syntax Upgrade",
                "findings": [f.category for f in findings if f.category == "JavaVersion"],
            },
        ]

        logger.info("Migration plan generated")

        report = {
            "total_findings": len(findings),
            "estimated_total_hours": total_hours,
            "phases": phases,
            "findings_detail": [
                {
                    "category": f.category,
                    "current": f.current_version,
                    "target": f.target_version,
                    "effort_hours": f.effort_hours,
                    "breaking_changes": f.breaking_changes,
                }
                for f in findings
            ],
        }

        logger.info("Report exported")
        return report
