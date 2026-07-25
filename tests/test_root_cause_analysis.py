"""
Tests for Root Cause Analysis (Prompt 093).
"""
import pytest
from services.debugging.debugging_engine import DebuggingEngine


def test_ambiguous_stack_trace_fallback():
    de = DebuggingEngine()
    st = "Uncaught error occurred in worker"

    res = de.analyze_stack_trace(st)
    rc = res["root_cause"]

    assert rc["confidence"] == 0.5
    assert rc["class"] == "Unknown"
