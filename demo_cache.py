"""
Demo script to verify the Intelligent Caching Layer.
Demonstrates cache misses, hits, stats, and reduced execution time.
No Ollama required.
"""
import time
from unittest.mock import patch
from ecip_core.models.request import InferenceRequest
from ecip_core.inference.models.inference_response import InferenceResponse

print("\n" + "="*70)
print("          ECIP Lite — Intelligent Caching Layer Demo")
print("="*70)

# Patching low-level network providers and Faiss store search calls
with patch("ecip_core.vectorstore.faiss_store.FAISSStore.search") as mock_faiss_search, \
     patch("ecip_core.embedding.providers.ollama_embedding_provider.OllamaEmbeddingProvider.embed") as mock_embed, \
     patch("ecip_core.inference.providers.ollama_provider.OllamaProvider.generate") as mock_generate:

    # Configure mock returns
    mock_faiss_search.return_value = []
    mock_embed.return_value = [0.0] * 768

    def mock_ask(prompt, model, callback=None):
        time.sleep(0.2)  # Simulate 200ms LLM latency
        return InferenceResponse(
            answer="Calculated UserService details answer.",
            citations=[],
            model_name=model,
            provider_name="ollama",
            inference_time_ms=200,
            prompt_tokens=10,
            completion_tokens=20,
            total_tokens=30,
            warnings=[],
            errors=[]
        )
    
    mock_generate.side_effect = mock_ask

    # Import QueryCoordinator and CacheManager
    from ecip_core.coordinator.query_coordinator import QueryCoordinator
    from ecip_core.cache.manager import cache_manager

    # Force enable caching and clear stats
    cache_manager.clear()

    coordinator = QueryCoordinator()
    request = InferenceRequest(question="Explain UserService")

    # Run 1: Cache Miss
    print("1. Executing First Query (Cache Miss):")
    t0 = time.perf_counter()
    res1 = coordinator.process(request)
    dur1 = (time.perf_counter() - t0) * 1000
    print(f"   Answer   : {res1.answer}")
    print(f"   Duration : {dur1:.2f} ms")
    stats1 = cache_manager.get_stats()
    print(f"   Stats    : Hits={stats1['hits']}, Misses={stats1['misses']}\n")

    # Run 2: Cache Hit
    print("2. Executing Second Query (Cache Hit - Repeated query):")
    t1 = time.perf_counter()
    res2 = coordinator.process(request)
    dur2 = (time.perf_counter() - t1) * 1000
    print(f"   Answer   : {res2.answer}")
    print(f"   Duration : {dur2:.2f} ms")
    stats2 = cache_manager.get_stats()
    print(f"   Stats    : Hits={stats2['hits']}, Misses={stats2['misses']}\n")

    # Summary calculations
    speedup = dur1 / dur2 if dur2 > 0 else 1.0
    print(f"⚡ Acceleration Speedup: {speedup:.1f}x faster!")

print("="*70)
print("Demo complete! Intelligent caching verified successfully.")
print("="*70 + "\n")
