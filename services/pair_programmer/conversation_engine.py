"""
Conversation Engine — Multi-turn dialogue manager, context builder, and citation generator.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class ChatMessage:
    role: str  # user, assistant, system
    content: str
    citations: List[str] = field(default_factory=list)


class ConversationEngine:
    """
    Manages multi-turn conversations and citation generation.
    """

    def __init__(self, conversation_id: str = "conv-1"):
        self.conversation_id = conversation_id
        self.messages: List[ChatMessage] = []

    def start_conversation(self, initial_system_prompt: str = "") -> None:
        logger.info("Conversation started")
        if initial_system_prompt:
            self.messages.append(ChatMessage("system", initial_system_prompt))

    def add_message(self, role: str, content: str, citations: List[str] = None) -> None:
        self.messages.append(ChatMessage(role=role, content=content, citations=citations or []))

    def assemble_context(self, max_chars: int = 4000) -> str:
        logger.info("Context assembled")
        full_text = "\n".join(f"{m.role}: {m.content}" for m in self.messages)
        if len(full_text) > max_chars:
            logger.warning("Context truncated")
            return full_text[-max_chars:]
        return full_text
