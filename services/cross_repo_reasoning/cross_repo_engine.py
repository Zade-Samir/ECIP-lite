"""
Cross-Repository Reasoning Engine — Federated graph traversal across multi-repository microservices.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set, Tuple

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class RepoNode:
    repo_id: str
    node_id: str
    node_type: str  # Service, API, Library, Class


@dataclass
class CrossRepoEdge:
    source_repo: str
    source_node: str
    target_repo: str
    target_node: str
    relationship: str  # CALLS_API, IMPORTS_LIB, PRODUCES_EVENT


class CrossRepoEngine:
    """
    Federates multiple repository graphs and traverses cross-boundary dependencies.
    """

    def __init__(self):
        self.repos: Dict[str, Dict[str, RepoNode]] = {}
        self.edges: List[CrossRepoEdge] = []

    def register_repo(self, repo_id: str, nodes: List[RepoNode]) -> None:
        self.repos[repo_id] = {n.node_id: n for n in nodes}

    def add_cross_repo_edge(self, edge: CrossRepoEdge) -> None:
        if edge.source_repo not in self.repos or edge.target_repo not in self.repos:
            logger.warning("Missing repository metadata")
            logger.warning("Ambiguous dependency")

        self.edges.append(edge)

    def traverse(self, start_repo: str, start_node: str, max_depth: int = 5) -> List[Dict[str, Any]]:
        logger.info("Cross-repository traversal started")
        if start_repo not in self.repos or start_node not in self.repos[start_repo]:
            logger.error("Traversal failed")
            raise ValueError(f"Node {start_node} in repo {start_repo} not found")

        visited = set()
        chain = []

        def _dfs(r_id: str, n_id: str, depth: int):
            if depth >= max_depth or (r_id, n_id) in visited:
                return
            visited.add((r_id, n_id))
            chain.append({"repo_id": r_id, "node_id": n_id})

            for edge in self.edges:
                if edge.source_repo == r_id and edge.source_node == n_id:
                    _dfs(edge.target_repo, edge.target_node, depth + 1)

        _dfs(start_repo, start_node, 0)
        logger.info("Dependency chain resolved")
        return chain

    def generate_report(self, start_repo: str, start_node: str) -> Dict[str, Any]:
        chain = self.traverse(start_repo, start_node)
        repos_spanned = list(set(item["repo_id"] for item in chain))
        report = {
            "start": f"{start_repo}:{start_node}",
            "chain_length": len(chain),
            "repos_spanned": repos_spanned,
            "chain": chain,
        }
        logger.info("Report generated")
        return report
