"""
Tests for Debugging Assistant (Prompt 093).
"""
import pytest
from services.debugging.debugging_engine import DebuggingEngine


def test_stack_trace_analysis():
    de = DebuggingEngine()
    st = """java.lang.NullPointerException: Cannot invoke "String.length()" because "str" is null
    at com.example.UserService.getUserName(UserService.java:45)
    at com.example.UserController.get(UserController.java:20)
    """

    res = de.analyze_stack_trace(st)
    rc = res["root_cause"]

    assert rc["exception"] == "java.lang.NullPointerException"
    assert rc["class"] == "com.example.UserService"
    assert rc["line"] == 45
    assert rc["confidence"] > 0.9
