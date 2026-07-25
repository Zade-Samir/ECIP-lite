"""
Debugging Engine — Stack trace analyzer, log correlator, root cause identifier, and confidence scorer.
"""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RootCause:
    exception_type: str
    failing_class: str
    failing_line: int
    summary: str
    confidence_score: float  # 0.0 to 1.0
    fix_recommendation: str


class DebuggingEngine:
    """
    Parses runtime exceptions, correlates logs, and performs root-cause analysis.
    """

    def analyze_stack_trace(self, stack_trace: str, logs: Optional[str] = None) -> Dict[str, Any]:
        logger.info("Diagnostic started")

        if not stack_trace:
            logger.error("Missing context")
            logger.error("Analysis failed")
            raise ValueError("Empty stack trace provided")

        if logs and len(logs) < 10:
            logger.warning("Incomplete logs")

        lines = stack_trace.splitlines()
        first_line = lines[0] if lines else "UnknownException"

        match = re.search(r"at\s+([a-zA-Z0-9_.]+)\.([a-zA-Z0-9_]+)\(([^:]+):(\d+)\)", stack_trace)

        if match:
            f_class, f_method, f_file, f_line = match.groups()
            f_line_int = int(f_line)
            confidence = 0.95
        else:
            logger.warning("Ambiguous diagnosis")
            f_class, f_line_int = "Unknown", 0
            confidence = 0.50

        cause = RootCause(
            exception_type=first_line.split(":")[0],
            failing_class=f_class,
            failing_line=f_line_int,
            summary=f"Failure in {f_class} at line {f_line_int}",
            confidence_score=confidence,
            fix_recommendation=f"Check null references or bounds in {f_class}:{f_line_int}",
        )

        logger.info("Root cause identified")

        report = {
            "root_cause": {
                "exception": cause.exception_type,
                "class": cause.failing_class,
                "line": cause.failing_line,
                "summary": cause.summary,
                "confidence": cause.confidence_score,
                "recommendation": cause.fix_recommendation,
            }
        }

        logger.info("Report generated")
        return report
