"""
Service Dependency Analyzer — Discovers microservice API contracts, shared libraries, and event topics.
"""
from typing import Any, Dict, List, Set
from ecip_core.common.logger import get_logger
from services.cross_repo_reasoning.cross_repo_engine import CrossRepoEngine

logger = get_logger(__name__)


class ServiceDependencyAnalyzer:
    """
    Analyzes microservice interactions and shared library dependencies.
    """

    def __init__(self, engine: CrossRepoEngine):
        self.engine = engine

    def analyze_service(self, service_repo_id: str) -> Dict[str, Any]:
        if service_repo_id not in self.engine.repos:
            logger.warning("Missing repository metadata")
            logger.error("Graph inconsistency detected")
            raise ValueError(f"Service repository {service_repo_id} not registered")

        outgoing = []
        incoming = []

        for edge in self.engine.edges:
            if edge.source_repo == service_repo_id:
                outgoing.append({"target_repo": edge.target_repo, "relationship": edge.relationship})
            if edge.target_repo == service_repo_id:
                incoming.append({"source_repo": edge.source_repo, "relationship": edge.relationship})

        logger.info("Report generated")
        return {
            "service_repo": service_repo_id,
            "outgoing_dependencies": outgoing,
            "incoming_dependents": incoming,
        }
