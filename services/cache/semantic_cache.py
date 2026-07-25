"""
Semantic Cache — Similarity-based query cache with TTL, workspace isolation, and LRU pruning.
"""
import time
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


def tokenize(text: str) -> set[str]:
    return set(text.lower().strip().split())


def jaccard_similarity(s1: set[str], s2: set[str]) -> float:
    if not s1 or not s2:
        return 0.0
    intersection = len(s1.intersection(s2))
    union = len(s1.union(s2))
    return intersection / union if union > 0 else 0.0


@dataclass
class CacheEntry:
    query: str
    response: str
    workspace_id: str
    tokens: set[str]
    created_at: float = field(default_factory=time.time)
    ttl: float = 3600.0

    def is_expired(self) -> bool:
        return (time.time() - self.created_at) > self.ttl


class SemanticCache:
    """
    Semantic cache storing queries and responses per workspace.
    """

    def __init__(self, capacity: int = 100, similarity_threshold: float = 0.85):
        self.capacity = capacity
        self.similarity_threshold = similarity_threshold
        # workspace_id -> list of CacheEntry
        self._store: Dict[str, List[CacheEntry]] = {}

    def get(self, query: str, workspace_id: str = "default") -> Optional[str]:
        entries = self._store.get(workspace_id, [])
        query_tokens = tokenize(query)

        best_match: Optional[CacheEntry] = None
        best_score = 0.0

        valid_entries = []
        for entry in entries:
            if entry.is_expired():
                continue
            valid_entries.append(entry)
            score = jaccard_similarity(query_tokens, entry.tokens)
            if score > best_score:
                best_score = score
                best_match = entry

        self._store[workspace_id] = valid_entries

        if best_match and best_score >= self.similarity_threshold:
            logger.info("Cache hit")
            return best_match.response
        elif best_match and 0.5 <= best_score < self.similarity_threshold:
            logger.warning("Low similarity match")
            logger.info("Cache miss")
            return None
        else:
            logger.info("Cache miss")
            return None

    def put(self, query: str, response: str, workspace_id: str = "default", ttl: float = 3600.0) -> None:
        if workspace_id not in self._store:
            self._store[workspace_id] = []

        entries = self._store[workspace_id]
        if len(entries) >= self.capacity:
            logger.warning("Cache nearing capacity")
            # Prune oldest entry
            entries.pop(0)

        entry = CacheEntry(
            query=query,
            response=response,
            workspace_id=workspace_id,
            tokens=tokenize(query),
            ttl=ttl,
        )
        entries.append(entry)

    def invalidate(self, workspace_id: str) -> None:
        if workspace_id in self._store:
            del self._store[workspace_id]
        logger.info("Cache refreshed")

    def clear(self) -> None:
        self._store.clear()
        logger.info("Cache refreshed")
