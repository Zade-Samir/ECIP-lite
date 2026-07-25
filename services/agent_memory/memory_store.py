"""
Agent Memory Store — Multi-level structured memory store for ECIP agents.
"""
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class MemoryType(str, Enum):
    SESSION = "session"
    CONVERSATION = "conversation"
    TASK = "task"
    WORKSPACE = "workspace"
    LONG_TERM = "long_term"


@dataclass
class MemoryRecord:
    key: str
    content: Any
    memory_type: MemoryType
    workspace_id: str = "default"
    tenant_id: str = "default"
    timestamp: float = field(default_factory=time.time)
    version: int = 1


class AgentMemoryStore:
    """
    Stores and retrieves agent memories across session, conversation, task, and workspace scopes.
    """

    def __init__(self, capacity_per_type: int = 100):
        self.capacity_per_type = capacity_per_type
        # tenant_id -> workspace_id -> memory_type -> key -> MemoryRecord
        self._store: Dict[str, Dict[str, Dict[str, Dict[str, MemoryRecord]]]] = {}

    def store_memory(
        self,
        key: str,
        content: Any,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        workspace_id: str = "default",
        tenant_id: str = "default",
    ) -> MemoryRecord:
        if tenant_id not in self._store:
            self._store[tenant_id] = {}
        if workspace_id not in self._store[tenant_id]:
            self._store[tenant_id][workspace_id] = {}
        m_type_val = memory_type.value
        if m_type_val not in self._store[tenant_id][workspace_id]:
            self._store[tenant_id][workspace_id][m_type_val] = {}

        bucket = self._store[tenant_id][workspace_id][m_type_val]
        if len(bucket) >= self.capacity_per_type and key not in bucket:
            logger.warning("Memory limit reached")
            # Prune oldest
            oldest_key = min(bucket.keys(), key=lambda k: bucket[k].timestamp)
            del bucket[oldest_key]

        existing = bucket.get(key)
        version = (existing.version + 1) if existing else 1

        record = MemoryRecord(
            key=key,
            content=content,
            memory_type=memory_type,
            workspace_id=workspace_id,
            tenant_id=tenant_id,
            version=version,
        )
        bucket[key] = record
        logger.info("Memory stored")
        return record

    def retrieve_memory(
        self,
        key: str,
        memory_type: MemoryType = MemoryType.CONVERSATION,
        workspace_id: str = "default",
        tenant_id: str = "default",
    ) -> Optional[MemoryRecord]:
        try:
            record = (
                self._store.get(tenant_id, {})
                .get(workspace_id, {})
                .get(memory_type.value, {})
                .get(key)
            )
            return record
        except Exception as e:
            logger.error("Retrieval failure")
            return None

    def list_memories(
        self,
        memory_type: Optional[MemoryType] = None,
        workspace_id: str = "default",
        tenant_id: str = "default",
    ) -> List[MemoryRecord]:
        results = []
        ws_dict = self._store.get(tenant_id, {}).get(workspace_id, {})
        for m_type_str, bucket in ws_dict.items():
            if memory_type and m_type_str != memory_type.value:
                continue
            results.extend(bucket.values())
        return sorted(results, key=lambda r: r.timestamp)

    def prune(self, workspace_id: str = "default", tenant_id: str = "default") -> int:
        ws_dict = self._store.get(tenant_id, {}).get(workspace_id, {})
        count = 0
        for bucket in ws_dict.values():
            count += len(bucket)
            bucket.clear()
        return count
