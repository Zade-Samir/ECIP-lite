"""
Dashboard Backend FastAPI Router — Serves APIs for the Knowledge Dashboard.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from pathlib import Path
from ecip_core.common.logger import get_logger
from services.dashboard.dashboard_service import DashboardService

logger = get_logger(__name__)

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])
dashboard_service = DashboardService()


@router.get("/ui", response_class=HTMLResponse)
async def get_dashboard_ui():
    logger.info("Dashboard loaded")
    html_path = Path(__file__).parent / "index.html"
    if html_path.exists():
        return html_path.read_text(encoding="utf-8")
    return "<h1>Dashboard UI file not found</h1>"


@router.get("/overview")
async def get_overview():
    logger.info("Dashboard loaded")
    return dashboard_service.get_overview()


@router.get("/workspaces")
async def get_workspaces(workspace_id: str = None):
    return dashboard_service.get_workspace_explorer(workspace_id)


@router.get("/graph/dependency")
async def get_dependency_graph(project_id: str = "sampleProject"):
    return dashboard_service.get_dependency_graph(project_id)


@router.get("/graph/call")
async def get_call_graph(class_name: str = "UserController"):
    return dashboard_service.get_call_graph(class_name)


@router.get("/analytics")
async def get_analytics():
    return dashboard_service.get_query_analytics()


@router.get("/health")
async def get_health():
    return dashboard_service.get_system_health()
