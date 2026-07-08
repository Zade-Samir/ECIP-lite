"""
Demo script to verify the Performance Metrics & Benchmarking Framework.
Executes a simulated query pipeline and exports timing statistics as JSON.
"""
from unittest.mock import patch
from ecip_core.models.request import InferenceRequest
from ecip_core.models.response import InferenceResponse
from ecip_core.query.models.intent_result import IntentResult
from ecip_core.query.models.entity_result import EntityResult
from ecip_core.retrieval.models.hybrid_result import HybridResult

print("\n" + "="*70)
print("     ECIP Lite — Performance Metrics & Benchmarking Demo")
print("="*70)

# Patching semantic store and model provider components to skip heavy network calls
with patch("ecip_core.coordinator.query_coordinator.FAISSStore"), \
     patch("ecip_core.coordinator.query_coordinator.EmbeddingService"), \
     patch("ecip_core.coordinator.query_coordinator.SemanticSearch"), \
     patch("ecip_core.coordinator.query_coordinator.MetadataSearchService"), \
     patch("ecip_core.coordinator.query_coordinator.HybridRetrieval") as mock_retrieval_cls, \
     patch("ecip_core.coordinator.query_coordinator.ContextBuilder") as mock_ctx_cls, \
     patch("ecip_core.coordinator.query_coordinator.InferenceService") as mock_inf_cls, \
     patch("ecip_core.coordinator.query_coordinator.IntentAnalyzer") as mock_intent_cls, \
     patch("ecip_core.coordinator.query_coordinator.EntityExtractor") as mock_extractor_cls:

    # Configure mock return behaviors
    mock_intent_cls.return_value.analyze.return_value = IntentResult(
        intent="explain_code", confidence=0.95, matched_patterns=[], normalized_query=""
    )
    mock_extractor_cls.return_value.extract_entities.return_value = [
        EntityResult(entity_type="class", entity_name="UserService", confidence=1.0, matched_text="UserService", normalized_value="userservice")
    ]
    mock_retrieval_cls.return_value.retrieve.return_value = [
        HybridResult(source="semantic", score=0.9, chunk_id="c1", file_path="/src/UserService.java", class_name="UserService", method_name="getUser", chunk_type="method", content="code", start_line=10, end_line=30)
    ]
    mock_ctx_cls.return_value.build.return_value = "Project context string"
    mock_inf_cls.return_value.ask.return_value = InferenceResponse(
        answer="This is a mock answer about UserService.", model="qwen3.5:9b"
    )

    # Import QueryCoordinator and MetricsCollector
    from ecip_core.coordinator.query_coordinator import QueryCoordinator
    from ecip_core.metrics.collector import metrics_collector

    # Clear collector to start clean
    metrics_collector.clear()

    print("1. Running QueryCoordinator to trigger pipeline timing metrics:")
    coordinator = QueryCoordinator()
    request = InferenceRequest(question="Explain UserService")
    
    # Process request (this will automatically track metrics for each phase)
    response = coordinator.process(request)
    print("✓ Pipeline executed successfully.\n")

    # Display Aggregated Stats in Table
    print("2. Aggregated Performance Metrics Stats:")
    print("-" * 75)
    print(f"{'Metric Name':<30} | {'Count':<5} | {'Total Time (ms)':<15} | {'Avg Time (ms)':<15}")
    print("-" * 75)
    
    stats_list = metrics_collector.get_all_stats()
    for stat in stats_list:
        print(f"{stat['metric']:<30} | {stat['count']:<5} | {stat['total_ms']:<15.2f} | {stat['avg_ms']:<15.2f}")
    print("-" * 75 + "\n")

    # Export report to JSON file
    print("3. Exporting metrics to JSON file (.ecip/metrics_report.json):")
    report_file = ".ecip/metrics_report.json"
    json_report = metrics_collector.export_json(file_path=report_file)
    print(f"✓ Metrics exported successfully. Content:\n")
    print(json_report)

print("="*70)
print("Demo complete! All performance metrics tracked and exported.")
print("="*70 + "\n")
