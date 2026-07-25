"""
Tests for Query Optimizer (Prompt 077).
"""
import pytest
from services.cache.semantic_cache import SemanticCache
from services.query_optimizer.query_optimizer import QueryOptimizer


def test_query_normalization():
    opt = QueryOptimizer()
    assert opt.normalize("   What IS   UserController  ? ") == "what is usercontroller ?"


def test_optimize_and_execute_cache_hit():
    cache = SemanticCache(similarity_threshold=0.8)
    opt = QueryOptimizer(cache=cache)

    execution_count = {"n": 0}

    def dummy_exec(q: str) -> str:
        execution_count["n"] += 1
        return "computed response"

    r1 = opt.optimize_and_execute("find all users", "ws1", dummy_exec)
    assert r1 == "computed response"
    assert execution_count["n"] == 1

    # Second call should hit cache
    r2 = opt.optimize_and_execute("find all users", "ws1", dummy_exec)
    assert r2 == "computed response"
    assert execution_count["n"] == 1
