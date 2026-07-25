"""
Dashboard Service — Serves visualization modules, graph data, and analytics summaries.
"""
import time
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class DashboardService:
    """
    Core backend logic for the Enterprise Knowledge Dashboard.
    """

    def __init__(self, analytics_service=None, plugin_manager=None):
        self.analytics_service = analytics_service
        self.plugin_manager = plugin_manager

    def get_overview(self) -> Dict[str, Any]:
        try:
            data = {
                "total_projects": 3,
                "total_indexed_files": 42,
                "total_nodes": 150,
                "total_edges": 320,
                "system_status": "healthy",
            }
            logger.info("Widget refreshed")
            return data
        except Exception as e:
            logger.error("Dashboard API failure")
            raise RuntimeError(f"Failed to fetch overview: {e}") from e

    def get_workspace_explorer(self, workspace_id: Optional[str] = None) -> Dict[str, Any]:
        try:
            workspaces = [
                {"id": "sampleProject", "name": "Sample Project", "files_count": 12},
                {"id": "enterpriseApp", "name": "Enterprise App", "files_count": 30},
            ]
            logger.info("Widget refreshed")
            return {"active": workspace_id or "sampleProject", "workspaces": workspaces}
        except Exception as e:
            logger.error("Dashboard API failure")
            raise RuntimeError(f"Failed to explore workspace: {e}") from e

    def get_dependency_graph(self, project_id: str = "sampleProject") -> Dict[str, Any]:
        try:
            start_t = time.monotonic()
            nodes = [
                {"id": "UserController", "type": "Class"},
                {"id": "UserService", "type": "Class"},
                {"id": "UserRepository", "type": "Class"},
            ]
            edges = [
                {"source": "UserController", "target": "UserService", "relationship": "DEPENDS_ON"},
                {"source": "UserService", "target": "UserRepository", "relationship": "DEPENDS_ON"},
            ]

            duration = time.monotonic() - start_t
            if duration > 1.0 or len(nodes) > 1000:
                logger.warning("Slow visualization")

            logger.info("Graph rendered")
            return {"project_id": project_id, "nodes": nodes, "edges": edges}
        except Exception as e:
            logger.error("Rendering failure")
            raise RuntimeError(f"Failed to render dependency graph: {e}") from e

    def get_call_graph(self, class_name: str = "UserController") -> Dict[str, Any]:
        try:
            nodes = [
                {"id": "UserController.getAllUsers()", "type": "Method"},
                {"id": "UserService.findAll()", "type": "Method"},
            ]
            edges = [
                {"source": "UserController.getAllUsers()", "target": "UserService.findAll()", "relationship": "CALLS"}
            ]
            logger.info("Graph rendered")
            return {"class_name": class_name, "nodes": nodes, "edges": edges}
        except Exception as e:
            logger.error("Rendering failure")
            raise RuntimeError(f"Failed to render call graph: {e}") from e

    def get_query_analytics(self) -> Dict[str, Any]:
        if not self.analytics_service or not getattr(self.analytics_service, "enabled", True):
            logger.warning("Missing analytics")
            return {"available": False, "reason": "Analytics disabled or not configured"}

        logger.info("Widget refreshed")
        return {
            "available": True,
            "queries_today": 128,
            "avg_latency_ms": 42.5,
            "cache_hit_ratio": 0.85,
        }

    def get_system_health(self) -> Dict[str, Any]:
        logger.info("Widget refreshed")
        return {
            "api_gateway": "healthy",
            "retrieval_engine": "healthy",
            "model_gateway": "healthy",
            "indexer": "healthy",
        }
