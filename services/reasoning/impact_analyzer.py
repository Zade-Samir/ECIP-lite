"""
Impact Analyzer — Analyzes ripple effects and change impact across Knowledge Graph nodes.
"""
from typing import Any, Dict, List, Set

from ecip_core.common.logger import get_logger
from services.reasoning.graph_reasoning_engine import GraphReasoningEngine

logger = get_logger(__name__)


class ImpactAnalyzer:
    """
    Predicts code modification ripple effects and structural impact scores.
    """

    def __init__(self, reasoning_engine: GraphReasoningEngine):
        self.engine = reasoning_engine

    def analyze_impact(self, target_node_id: str) -> Dict[str, Any]:
        if target_node_id not in self.engine.nodes:
            logger.error("Graph traversal failed")
            raise ValueError(f"Target node {target_node_id} not in graph")

        paths = self.engine.multi_hop_traversal(target_node_id, max_depth=5)
        affected: Set[str] = set()

        for path in paths:
            for node_id in path:
                if node_id != target_node_id:
                    affected.add(node_id)

        risk_score = min(1.0, round(len(affected) * 0.25, 2))

        report = {
            "target": target_node_id,
            "affected_nodes_count": len(affected),
            "affected_nodes": list(affected),
            "risk_score": risk_score,
            "explanation": f"Modifying {target_node_id} directly impacts {len(affected)} dependent nodes.",
        }

        logger.info("Report generated")
        return report
