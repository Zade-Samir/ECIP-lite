"""
Tests for Conversation Engine (Prompt 091).
"""
import pytest
from services.pair_programmer.conversation_engine import ConversationEngine


def test_conversation_context_assembly():
    ce = ConversationEngine("c1")
    ce.start_conversation("System Prompt")
    ce.add_message("user", "How to add user?")
    ce.add_message("assistant", "Use UserService.addUser()")

    ctx = ce.assemble_context(max_chars=1000)
    assert "user: How to add user?" in ctx
    assert "assistant: Use UserService.addUser()" in ctx
