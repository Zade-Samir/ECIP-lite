"""
Query Optimizer — Normalizes queries, eliminates redundancy, and orchestrates semantic cache lookups.
"""
import re
from typing import Callable, Optional
from services.cache.semantic_cache import SemanticCache


class QueryOptimizer:
    """
    Optimizes queries prior to execution.
    """

    def __init__(self, cache: Optional[SemanticCache] = None):
        self.cache = cache or SemanticCache()

    def normalize(self, query: str) -> str:
        # Strip extra whitespace and lowercase
        cleaned = re.sub(r"\s+", " ", query.strip())
        return cleaned.lower()

    def optimize_and_execute(self, query: str, workspace_id: str, execution_fn: Callable[[str], str]) -> str:
        norm_query = self.normalize(query)

        # Check semantic cache
        cached_resp = self.cache.get(norm_query, workspace_id=workspace_id)
        if cached_resp is not None:
            return cached_resp

        # Cache miss — execute underlying function
        response = execution_fn(norm_query)
        self.cache.put(norm_query, response, workspace_id=workspace_id)
        return response
