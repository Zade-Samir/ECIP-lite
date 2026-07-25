"""
Tests for Semantic Cache (Prompt 077).
"""
import time
import pytest
from services.cache.semantic_cache import SemanticCache


def test_cache_hit_and_miss():
    cache = SemanticCache(similarity_threshold=0.8)
    cache.put("what is getAllUsers method", "It returns list of users", workspace_id="ws1")

    # Exact or near hit
    hit = cache.get("what is getAllUsers method", workspace_id="ws1")
    assert hit == "It returns list of users"

    # Similar query (Jaccard > 0.8)
    similar_hit = cache.get("what is getAllUsers method in controller", workspace_id="ws1")
    # if token match high enough -> hit or miss
    # Completely different query -> miss
    miss = cache.get("how to configure database connection", workspace_id="ws1")
    assert miss is None


def test_workspace_isolation():
    cache = SemanticCache(similarity_threshold=0.8)
    cache.put("get user details", "Response WS1", workspace_id="ws1")

    assert cache.get("get user details", workspace_id="ws2") is None
    assert cache.get("get user details", workspace_id="ws1") == "Response WS1"


def test_ttl_expiration():
    cache = SemanticCache(similarity_threshold=0.8)
    cache.put("short ttl query", "Fast response", workspace_id="ws1", ttl=0.1)
    time.sleep(0.2)
    assert cache.get("short ttl query", workspace_id="ws1") is None


def test_capacity_pruning():
    cache = SemanticCache(capacity=2, similarity_threshold=0.8)
    cache.put("q1", "r1", "ws1")
    cache.put("q2", "r2", "ws1")
    cache.put("q3", "r3", "ws1")  # Should prune oldest q1

    assert cache.get("q1", "ws1") is None
    assert cache.get("q2", "ws1") == "r2"
