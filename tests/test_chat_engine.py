"""
Tests for Chat Engine (Prompt 091).
"""
import pytest
from services.pair_programmer.chat_engine import ChatEngine


def test_chat_engine_generation():
    engine = ChatEngine()
    res = engine.generate_response("Explain Spring Security setup")

    assert "response" in res
    assert len(res["citations"]) > 0
    assert "src/UserService.java" in res["citations"][0]
