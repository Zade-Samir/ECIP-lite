import shutil
from pathlib import Path
from fastapi import APIRouter, HTTPException
from ecip_core.common.logger import get_logger
from ecip_core.api.models.project import ProjectModel, ProjectListResponse
from ecip_core.storage.sqlite.repository import JavaRepository

logger = get_logger(__name__)

router = APIRouter()


@router.get("/projects", response_model=ProjectListResponse)
async def list_projects():
    try:
        repo = JavaRepository()
        projects_data = repo.get_projects()
        logger.info("Project listed")
        return ProjectListResponse(projects=[ProjectModel(**p) for p in projects_data])
    except Exception as e:
        logger.error(f"Database failure: {e}")
        raise HTTPException(status_code=500, detail="Database access error")


@router.get("/projects/{project_id}", response_model=ProjectModel)
async def get_project_details(project_id: str):
    try:
        repo = JavaRepository()
        project = repo.get_project(project_id)
        if not project:
            logger.warning("Unknown project")
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
        logger.info("Project loaded")
        return ProjectModel(**project)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Database failure: {e}")
        raise HTTPException(status_code=500, detail="Database access error")


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    try:
        repo = JavaRepository()
        project = repo.get_project(project_id)
        if not project:
            logger.warning("Unknown project")
            raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")

        root_path = project["root_path"]

        # 1. Clean FAISS vectors from filesystem
        try:
            ecip_dir = Path(root_path) / ".ecip"
            if ecip_dir.exists() and ecip_dir.is_dir():
                shutil.rmtree(ecip_dir)
        except Exception as e:
            logger.error(f"Vector cleanup failure: {e}")
            logger.error("Delete failure")
            raise HTTPException(status_code=500, detail="Failed to delete FAISS vector files")

        # 2. Clean SQLite metadata
        try:
            repo.delete_project(project_id)
        except Exception as e:
            logger.error(f"Database failure: {e}")
            logger.error("Delete failure")
            raise HTTPException(status_code=500, detail="Failed to delete database metadata")

        logger.info("Project deleted")
        return {"status": "success", "message": f"Project '{project_id}' successfully deleted"}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete failure: {e}")
        raise HTTPException(status_code=500, detail="Unexpected delete failure")
