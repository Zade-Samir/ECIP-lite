"""
Graph Reasoning Engine — Multi-hop graph traversal, cycle detection, and pattern recognition.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class GraphNode:
    node_id: str
    node_type: str  # Class, Method, Repository, Interface
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass
class GraphEdge:
    source: str
    target: str
    relationship: str  # CALLS, DEPENDS_ON, EXTENDS, IMPLEMENTS


class GraphReasoningEngine:
    """
    Multi-hop graph traversal and structural relationship reasoning.
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.adj: Dict[str, List[GraphEdge]] = {}

    def add_node(self, node: GraphNode) -> None:
        self.nodes[node.node_id] = node
        if node.node_id not in self.adj:
            self.adj[node.node_id] = []

    def add_edge(self, edge: GraphEdge) -> None:
        if edge.source not in self.nodes or edge.target not in self.nodes:
            logger.warning("Ambiguous relationship")
        if edge.source not in self.adj:
            self.adj[edge.source] = []
        self.adj[edge.source].append(edge)

    def multi_hop_traversal(self, start_id: str, max_depth: int = 5) -> List[List[str]]:
        logger.info("Traversal started")
        if start_id not in self.nodes:
            logger.error("Graph traversal failed")
            raise ValueError(f"Start node {start_id} not found in graph")

        paths: List[List[str]] = []

        def _dfs(curr_id: str, current_path: List[str], depth: int):
            if depth >= max_depth:
                logger.warning("Deep traversal limit reached")
                paths.append(list(current_path))
                return

            edges = self.adj.get(curr_id, [])
            if not edges:
                paths.append(list(current_path))
                return

            for edge in edges:
                nxt = edge.target
                if nxt in current_path:
                    # Cycle detected
                    paths.append(list(current_path) + [nxt])
                    continue
                current_path.append(nxt)
                _dfs(nxt, current_path, depth + 1)
                current_path.pop()

        _dfs(start_id, [start_id], 0)
        logger.info("Reasoning completed")
        return paths

    def detect_cycles(self) -> List[List[str]]:
        cycles = []
        visited = set()

        for start_node in self.nodes:
            if start_node in visited:
                continue
            paths = self.multi_hop_traversal(start_node, max_depth=10)
            for path in paths:
                if len(path) > 1 and path[0] == path[-1]:
                    cycles.append(path)
            visited.add(start_node)

        return cycles
