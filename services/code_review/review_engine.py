"""
Review Engine — Pull request diff analyzer, inline comment generator, and severity classifier.
"""
from dataclasses import dataclass
from typing import Any, Dict, List

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ReviewComment:
    file_path: str
    line_number: int
    severity: str  # HIGH, MEDIUM, LOW
    category: str  # Security, Quality, Performance, Architecture
    comment: str
    suggested_fix: str


class ReviewEngine:
    """
    Analyzes code diffs and generates automated inline review comments.
    """

    def review_diff(self, diff_text: str, max_lines: int = 5000) -> Dict[str, Any]:
        logger.info("Review started")

        if len(diff_text.splitlines()) > max_lines:
            logger.warning("Large diff")
            logger.warning("Partial analysis")

        comments = []
        lines = diff_text.splitlines()

        current_file = "unknown"
        line_num = 0

        for line in lines:
            if line.startswith("+++ b/"):
                current_file = line[6:]
            elif line.startswith("@@"):
                line_num = 1
            elif line.startswith("+") and not line.startswith("+++"):
                line_num += 1
                if "System.out.println" in line or "printStackTrace" in line:
                    comments.append(
                        ReviewComment(
                            file_path=current_file,
                            line_number=line_num,
                            severity="MEDIUM",
                            category="Quality",
                            comment="Avoid stdout logging in production code; use a logger instead.",
                            suggested_fix="logger.info(...);",
                        )
                    )
                if "eval(" in line or "exec(" in line:
                    comments.append(
                        ReviewComment(
                            file_path=current_file,
                            line_number=line_num,
                            severity="HIGH",
                            category="Security",
                            comment="Use of dangerous execution function.",
                            suggested_fix="Sanitize input or use static API.",
                        )
                    )

        logger.info("Findings generated")

        report = {
            "total_comments": len(comments),
            "comments": [
                {
                    "file": c.file_path,
                    "line": c.line_number,
                    "severity": c.severity,
                    "category": c.category,
                    "comment": c.comment,
                    "suggested_fix": c.suggested_fix,
                }
                for c in comments
            ],
            "status": "APPROVED" if not any(c.severity == "HIGH" for c in comments) else "CHANGES_REQUESTED",
        }

        logger.info("Report published")
        return report
