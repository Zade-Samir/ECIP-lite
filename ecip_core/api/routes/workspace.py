from fastapi import APIRouter, HTTPException
from ecip_core.common.logger import get_logger
from ecip_core.workspace.manager import workspace_manager
from ecip_core.diagnostics.service import DiagnosticsService
from pydantic import BaseModel
from typing import Optional

logger = get_logger(__name__)

router = APIRouter()


# ─── Request / Response Models ────────────────────────────────────────────────

class WorkspaceCreateRequest(BaseModel):
    project_id: str
    alias: str
    root_path: str


class WorkspaceResponse(BaseModel):
    project_id: str
    alias: str
    root_path: str
    is_active: bool


class WorkspaceListResponse(BaseModel):
    workspaces: list[WorkspaceResponse]
    active: Optional[str]


class CheckResult(BaseModel):
    name: str
    passed: bool
    message: Optional[str] = None


class DiagnosticsResponse(BaseModel):
    overall_status: str
    checks: list[CheckResult]
    warnings: list[str]
    errors: list[str]


# ─── Workspace Endpoints ──────────────────────────────────────────────────────

@router.post("/workspaces", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(request: WorkspaceCreateRequest):
    """Register a new project workspace."""
    try:
        workspace_manager.register_workspace(
            project_id=request.project_id,
            alias=request.alias,
            root_path=request.root_path
        )
        logger.info(f"Workspace created: {request.project_id}")
        active = workspace_manager.get_active_workspace()
        return WorkspaceResponse(
            project_id=request.project_id,
            alias=request.alias,
            root_path=request.root_path,
            is_active=(active == request.project_id)
        )
    except Exception as e:
        logger.error(f"Workspace creation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create workspace: {e}")


@router.get("/workspaces", response_model=WorkspaceListResponse)
async def list_workspaces():
    """List all registered project workspaces."""
    try:
        workspaces = workspace_manager.list_workspaces()
        active = workspace_manager.get_active_workspace()
        result = [
            WorkspaceResponse(
                project_id=w["project_id"],
                alias=w.get("alias", w["project_id"]),
                root_path=w.get("root_path", ""),
                is_active=(w["project_id"] == active)
            )
            for w in workspaces
        ]
        return WorkspaceListResponse(workspaces=result, active=active)
    except Exception as e:
        logger.error(f"Workspace list failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to list workspaces")


@router.get("/workspaces/active")
async def get_active_workspace():
    """Get the currently active workspace."""
    try:
        active = workspace_manager.get_active_workspace()
        workspace = workspace_manager.get_workspace(active)
        if not workspace:
            return {"active": None}
        return {"active": active, "details": workspace}
    except Exception as e:
        logger.error(f"Active workspace lookup failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to get active workspace")


@router.put("/workspaces/{project_id}/activate")
async def activate_workspace(project_id: str):
    """Switch the active workspace to the given project."""
    try:
        workspace = workspace_manager.get_workspace(project_id)
        if not workspace:
            raise HTTPException(status_code=404, detail=f"Workspace '{project_id}' not found")
        workspace_manager.set_active_workspace(project_id)
        logger.info(f"Workspace activated: {project_id}")
        return {"status": "success", "active": project_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workspace activation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to activate workspace")


@router.delete("/workspaces/{project_id}")
async def delete_workspace(project_id: str):
    """Delete a registered workspace and its data."""
    try:
        workspace = workspace_manager.get_workspace(project_id)
        if not workspace:
            raise HTTPException(status_code=404, detail=f"Workspace '{project_id}' not found")
        workspace_manager.delete_workspace(project_id)
        logger.info(f"Workspace deleted: {project_id}")
        return {"status": "success", "message": f"Workspace '{project_id}' deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Workspace deletion failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete workspace")


# ─── Diagnostics Endpoint ─────────────────────────────────────────────────────

@router.get("/diagnostics", response_model=DiagnosticsResponse)
async def run_diagnostics():
    """Run all system health diagnostic checks."""
    try:
        service = DiagnosticsService()
        report = service.run_diagnostics()

        # Build check results from passed/failed lists
        checks = []
        for name in report.checks_passed:
            checks.append(CheckResult(name=name, passed=True))
        for name in report.checks_failed:
            # Find the associated error message if available
            msg = next((e for e in report.errors if name.lower().replace(" ", "_") in e.lower()), None)
            checks.append(CheckResult(name=name, passed=False, message=msg))

        return DiagnosticsResponse(
            overall_status=report.overall_status,
            checks=checks,
            warnings=report.warnings,
            errors=report.errors
        )
    except Exception as e:
        logger.error(f"Diagnostics failed: {e}")
        raise HTTPException(status_code=500, detail=f"Diagnostics error: {e}")
