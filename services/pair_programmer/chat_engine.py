"""
Chat Engine — High-level developer Q&A, code generation, and citation generator.
"""
from typing import Any, Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.pair_programmer.conversation_engine import ConversationEngine

logger = get_logger(__name__)


class ChatEngine:
    """
    Orchestrates developer pairing requests with workspace citations.
    """

    def __init__(self, conversation_engine: Optional[ConversationEngine] = None):
        self.conv = conversation_engine or ConversationEngine()
        self.conv.start_conversation()

    def generate_response(
        self, user_query: str, workspace_context: Optional[str] = None
    ) -> Dict[str, Any]:
        self.conv.add_message("user", user_query)
        context = self.conv.assemble_context()

        # Simulated response with citations
        citations = ["file:///src/UserService.java#L10-L40"]
        response_text = f"Based on your codebase context:\n```java\n// Solution for: {user_query[:30]}...\n```"

        self.conv.add_message("assistant", response_text, citations=citations)
        logger.info("Response generated")

        return {
            "query": user_query,
            "response": response_text,
            "citations": citations,
        }
