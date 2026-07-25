"""
Tests for Agent Memory Store (Prompt 078).
"""
import pytest
from services.agent_memory.memory_store import AgentMemoryStore, MemoryType


def test_store_and_retrieve_memory():
    store = AgentMemoryStore()
    rec = store.store_memory("goal_1", "Implement Feature X", MemoryType.TASK, workspace_id="ws1")
    assert rec.key == "goal_1"
    assert rec.version == 1

    retrieved = store.retrieve_memory("goal_1", MemoryType.TASK, workspace_id="ws1")
    assert retrieved is not None
    assert retrieved.content == "Implement Feature X"


def test_memory_versioning():
    store = AgentMemoryStore()
    store.store_memory("session_state", "Step 1", MemoryType.SESSION)
    updated = store.store_memory("session_state", "Step 2", MemoryType.SESSION)
    assert updated.version == 2


def test_memory_isolation():
    store = AgentMemoryStore()
    store.store_memory("k1", "data_tenant1", MemoryType.TASK, workspace_id="w1", tenant_id="t1")
    store.store_memory("k1", "data_tenant2", MemoryType.TASK, workspace_id="w1", tenant_id="t2")

    res1 = store.retrieve_memory("k1", MemoryType.TASK, workspace_id="w1", tenant_id="t1")
    res2 = store.retrieve_memory("k1", MemoryType.TASK, workspace_id="w1", tenant_id="t2")

    assert res1.content == "data_tenant1"
    assert res2.content == "data_tenant2"


def test_memory_capacity_limit():
    store = AgentMemoryStore(capacity_per_type=2)
    store.store_memory("k1", "v1", MemoryType.CONVERSATION)
    store.store_memory("k2", "v2", MemoryType.CONVERSATION)
    store.store_memory("k3", "v3", MemoryType.CONVERSATION)  # Reaches limit, prunes oldest

    memories = store.list_memories(MemoryType.CONVERSATION)
    assert len(memories) == 2
