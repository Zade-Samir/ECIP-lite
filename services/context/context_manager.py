"""
Context Manager — Restores, summarizes, and prunes agent conversation and task context window.
"""
from typing import Any, Dict, List, Optional
from ecip_core.common.logger import get_logger
from services.agent_memory.memory_store import AgentMemoryStore, MemoryType

logger = get_logger(__name__)


class ContextManager:
    """
    Manages active context window size, summarization, and restoration.
    """

    def __init__(self, memory_store: Optional[AgentMemoryStore] = None, max_token_limit: int = 4096):
        self.memory_store = memory_store or AgentMemoryStore()
        self.max_token_limit = max_token_limit

    def restore_context(self, workspace_id: str = "default", tenant_id: str = "default") -> List[Dict[str, Any]]:
        memories = self.memory_store.list_memories(workspace_id=workspace_id, tenant_id=tenant_id)
        context = []
        for m in memories:
            context.append({"key": m.key, "type": m.memory_type.value, "content": m.content})
        logger.info("Context restored")
        return context

    def summarize_memory(self, memories: List[Any]) -> str:
        summary_text = f"Summary of {len(memories)} interaction items."
        logger.info("Summary generated")
        return summary_text

    def truncate_context(self, context_items: List[str], max_items: int = 10) -> List[str]:
        if len(context_items) > max_items:
            logger.warning("Context truncated")
            return context_items[-max_items:]
        return context_items
