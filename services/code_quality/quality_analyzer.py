"""
Quality Analyzer — Computes maintainability index, complexity, duplication, and technical debt metrics.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class QualityMetrics:
    cyclomatic_complexity: float
    maintainability_index: float  # 0 to 100
    duplication_percentage: float
    dead_code_items: int
    security_hotspots: int


class QualityAnalyzer:
    """
    Computes quality metrics across repository files and AST chunks.
    """

    def analyze(self, files_metadata: List[Dict[str, Any]]) -> QualityMetrics:
        logger.info("Analysis started")

        if not files_metadata:
            return QualityMetrics(0.0, 100.0, 0.0, 0, 0)

        total_complexity = sum(f.get("complexity", 1.0) for f in files_metadata)
        avg_complexity = total_complexity / len(files_metadata)

        # Simplified Maintainability Index formula simulation
        maintainability = max(0.0, min(100.0, 100.0 - (avg_complexity * 3.0)))
        duplication = sum(f.get("duplication_lines", 0) for f in files_metadata) / max(1, sum(f.get("lines", 10) for f in files_metadata)) * 100.0
        dead_code = sum(f.get("dead_code_count", 0) for f in files_metadata)
        hotspots = sum(f.get("security_hotspots", 0) for f in files_metadata)

        metrics = QualityMetrics(
            cyclomatic_complexity=round(avg_complexity, 2),
            maintainability_index=round(maintainability, 2),
            duplication_percentage=round(duplication, 2),
            dead_code_items=dead_code,
            security_hotspots=hotspots,
        )

        logger.info("Report generated")
        return metrics
