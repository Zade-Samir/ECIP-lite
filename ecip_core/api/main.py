import sqlite3
# Monkey-patch sqlite3 to allow multi-threaded access without thread-ownership errors
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ecip_core.api.routes import query_router, indexing_router, projects_router, workspace_router

app = FastAPI(
    title="ECIP Lite API",
    description="REST API for ECIP Lite — offline, privacy-first AI code intelligence.",
    version="1.0.0"
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes with /api/v1 prefix
app.include_router(query_router,     prefix="/api/v1", tags=["Query"])
app.include_router(indexing_router,  prefix="/api/v1", tags=["Index"])
app.include_router(projects_router,  prefix="/api/v1", tags=["Projects"])
app.include_router(workspace_router, prefix="/api/v1", tags=["Workspaces & Diagnostics"])


@app.get("/health", tags=["System"])
async def health_check():
    """Health check status endpoint."""
    return {"status": "healthy"}
