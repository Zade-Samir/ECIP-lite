"""
Demo script to test QueryCoordinator routing logic.
Shows which route (Graph vs Retrieval) is selected for each question type.
No Ollama required — InferenceService is patched.
"""
import sqlite3

# Monkey-patch for multi-thread SQLite
original_connect = sqlite3.connect
def custom_connect(*args, **kwargs):
    kwargs["check_same_thread"] = False
    return original_connect(*args, **kwargs)
sqlite3.connect = custom_connect

from unittest.mock import patch, MagicMock
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.models.response import InferenceResponse

PROJECT_ID = "spring-boot-demo"

# ─── Seed dependency edges ──────────────────────────────────────────────────
repo = JavaRepository()
repo.delete_project(PROJECT_ID)
repo.save_project(
    project_id=PROJECT_ID,
    alias="spring-boot-demo",
    root_path="/projects/spring-boot-demo",
    indexed_at="2026-07-08T18:00:00Z",
    indexed_files=5,
    total_chunks=25,
    total_vectors=25,
    status="active"
)
edges = [
    (PROJECT_ID, "UserController",  "UserService",      "DEPENDS_ON"),
    (PROJECT_ID, "UserService",     "UserRepository",   "DEPENDS_ON"),
    (PROJECT_ID, "OrderController", "OrderService",     "DEPENDS_ON"),
    (PROJECT_ID, "OrderService",    "UserService",      "DEPENDS_ON"),
    (PROJECT_ID, "OrderService",    "OrderRepository",  "DEPENDS_ON"),
    (PROJECT_ID, "UserController",  "BaseController",   "EXTENDS"),
    (PROJECT_ID, "OrderController", "BaseController",   "EXTENDS"),
]
for edge in edges:
    repo.save_edge(*edge)

print("\n" + "="*65)
print("  ECIP Lite — QueryCoordinator Routing Demo")
print("="*65)
print(f"✓ Seeded {len(edges)} dependency edges for '{PROJECT_ID}'\n")

# ─── Patch heavy services (no Ollama needed) ────────────────────────────────
with patch("ecip_core.coordinator.query_coordinator.FAISSStore"), \
     patch("ecip_core.coordinator.query_coordinator.EmbeddingService"), \
     patch("ecip_core.coordinator.query_coordinator.SemanticSearch"), \
     patch("ecip_core.coordinator.query_coordinator.MetadataSearchService"), \
     patch("ecip_core.coordinator.query_coordinator.HybridRetrieval") as mock_retrieval_cls, \
     patch("ecip_core.coordinator.query_coordinator.ContextBuilder") as mock_ctx_cls, \
     patch("ecip_core.coordinator.query_coordinator.InferenceService") as mock_inf_cls:

    # Fake LLM always returns a canned answer
    mock_inf = mock_inf_cls.return_value
    mock_inf.ask.return_value = InferenceResponse(
        answer="[LLM summarized the graph/code context here]",
        model="mocked-model"
    )

    # Fake retrieval returns empty (routing is what we're testing)
    mock_retrieval_cls.return_value.retrieve.return_value = []
    mock_ctx_cls.return_value.build.return_value = ""

    from ecip_core.coordinator.query_coordinator import QueryCoordinator
    from ecip_core.models.request import InferenceRequest

    coordinator = QueryCoordinator()

    questions = [
        ("What depends on UserRepository?",          "dependency_analysis → GRAPH ROUTE"),
        ("What classes use UserService?",             "dependency_analysis → GRAPH ROUTE"),
        ("What breaks if UserService changes?",       "impact_analysis    → GRAPH ROUTE"),
        ("What is the impact of changing OrderService?", "impact_analysis → GRAPH ROUTE"),
        ("Explain UserService",                       "explain_code       → RETRIEVAL ROUTE"),
        ("How does getUserById work?",                "explain_method     → RETRIEVAL ROUTE"),
        ("Show me all REST endpoints",                "endpoint_lookup    → RETRIEVAL ROUTE"),
    ]

    for question, expected_route in questions:
        print("-"*65)
        print(f"  Question : {question}")
        print(f"  Expected : {expected_route}")
        req = InferenceRequest(question=question)
        res = coordinator.process(req)
        print(f"  Detected Intent  : {res.intent.intent} (confidence={res.intent.confidence:.2f})")
        print(f"  Citations (code) : {len(res.citations)} result(s)")
        route = "GRAPH ROUTE" if not res.citations and res.intent.intent in {"dependency_analysis", "impact_analysis"} else "RETRIEVAL ROUTE"
        print(f"  Actual Route     : {route}")
        print(f"  LLM Answer       : {res.answer[:60]}...")
        print()

print("="*65)
print("  Routing demo complete!")
print("="*65 + "\n")
