from ecip_core.api.routes.query import router as query_router
from ecip_core.api.routes.indexing import router as indexing_router
from ecip_core.api.routes.projects import router as projects_router
from ecip_core.api.routes.workspace import router as workspace_router

__all__ = ["query_router", "indexing_router", "projects_router", "workspace_router"]
