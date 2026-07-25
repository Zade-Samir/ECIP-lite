"""
Architecture Copilot Engine — Interactive design assistant, trade-off analyzer, and ADR generator.
"""
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ADRDocument:
    title: str
    status: str  # PROPOSED, ACCEPTED, SUPERSEDED
    context: str
    decision: str
    consequences: List[str]


class ArchitectureCopilotEngine:
    """
    Assists enterprise architects with pattern design, trade-off reasoning, and ADR generation.
    """

    def analyze_architecture(self, modules_meta: List[Dict[str, Any]]) -> Dict[str, Any]:
        logger.info("Architecture analysis started")

        if not modules_meta:
            logger.warning("Incomplete repository context")

        recs = [
            "Consider extracting Order Processing into an independent microservice to improve scalability.",
            "Implement Saga pattern for distributed transactions across Payment and Inventory services.",
        ]

        logger.info("Recommendations generated")
        return {"recommendations": recs, "modules_analyzed": len(modules_meta)}

    def create_adr(self, title: str, context: str, decision: str, consequences: List[str]) -> ADRDocument:
        adr = ADRDocument(
            title=title,
            status="PROPOSED",
            context=context,
            decision=decision,
            consequences=consequences,
        )
        logger.info("ADR created")
        return adr
