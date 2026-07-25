"""
Job Registry — maps named job types to callable handlers.
"""
from typing import Callable, Dict, Any, Optional
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class JobRegistry:
    """
    Central registry of named job handlers.

    Usage:
        registry = JobRegistry()
        registry.register("index_project", index_fn)
        handler = registry.get("index_project")
    """

    def __init__(self):
        self._jobs: Dict[str, Callable] = {}

    def register(self, name: str, fn: Callable, description: str = "") -> None:
        """Register a job handler."""
        self._jobs[name] = fn
        logger.info("Job scheduled")

    def get(self, name: str) -> Optional[Callable]:
        """Retrieve a job handler by name."""
        return self._jobs.get(name)

    def list_jobs(self) -> list[dict]:
        """List all registered job names."""
        return [{"name": k} for k in self._jobs.keys()]

    def is_registered(self, name: str) -> bool:
        return name in self._jobs

    def unregister(self, name: str) -> bool:
        if name in self._jobs:
            del self._jobs[name]
            return True
        return False


# Singleton registry
job_registry = JobRegistry()
