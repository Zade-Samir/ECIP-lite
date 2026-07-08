import sqlite3
# Monkey-patch sqlite3 to allow multi-threaded access without thread-ownership errors
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

from fastapi import FastAPI
from ecip_core.api.routes import query_router, indexing_router, projects_router

app = FastAPI(
    title="ECIP Lite API",
    description="REST API for ECIP Lite semantic query pipeline and metadata retrieval.",
    version="1.0.0"
)

# Register routes
app.include_router(query_router, tags=["Query"])
app.include_router(indexing_router, tags=["Index"])
app.include_router(projects_router, tags=["Projects"])


@app.get("/health", tags=["System"])
async def health_check():
    """Health check status endpoint."""
    return {"status": "healthy"}
