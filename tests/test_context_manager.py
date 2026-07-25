"""
Tests for Context Manager (Prompt 078).
"""
import pytest
from services.agent_memory.memory_store import AgentMemoryStore, MemoryType
from services.context.context_manager import ContextManager


def test_restore_context():
    store = AgentMemoryStore()
    store.store_memory("step1", "Parsed AST", MemoryType.TASK, workspace_id="ws1")
    cm = ContextManager(memory_store=store)

    context = cm.restore_context(workspace_id="ws1")
    assert len(context) == 1
    assert context[0]["key"] == "step1"


def test_summarize_and_truncate():
    cm = ContextManager()
    summary = cm.summarize_memory(["m1", "m2", "m3"])
    assert "3" in summary

    items = [f"item_{i}" for i in range(15)]
    truncated = cm.truncate_context(items, max_items=5)
    assert len(truncated) == 5
    assert truncated[0] == "item_10"
