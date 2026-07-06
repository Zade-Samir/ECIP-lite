import unittest
import math
import time
from unittest.mock import patch
from ecip_core.chunking.code_chunk import CodeChunk
from ecip_core.embedding.embedding_provider import EmbeddingProvider
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.embedding.exceptions import (
    ProviderUnavailableError,
    EmbeddingTimeoutError,
    EmbeddingError,
    InvalidVectorError,
)
from ecip_core.embedding.providers.ollama_embedding_provider import OllamaEmbeddingProvider
from ecip_core.inference.config.settings import settings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_chunk(
    chunk_id="c1",
    class_name="MyClass",
    method_name="myMethod",
    source_code="public void myMethod() {}",
) -> CodeChunk:
    return CodeChunk(
        chunk_id=chunk_id,
        project_id="test_project",
        file_path="MyClass.java",
        file_name="MyClass.java",
        class_name=class_name,
        method_name=method_name,
        chunk_type="METHOD",
        content=source_code,
        source_code=source_code,
        start_line=1,
        end_line=3,
        content_hash="abc",
    )


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock implementation of EmbeddingProvider for testing.
    Supports configurable dimension, failure modes, and batch toggling.
    """

    def __init__(self, dimension=768, should_fail_type=None, batch_support=True):
        self.dimension = dimension
        self.should_fail_type = should_fail_type
        self._batch_support = batch_support
        self.embed_call_count = 0
        self.embed_batch_call_count = 0

    def _make_vector(self) -> list[float]:
        vector = [1.0] * self.dimension
        return self.normalize(vector)

    def embed(self, text: str) -> list[float]:
        self.embed_call_count += 1
        if self.should_fail_type == "connection":
            raise ProviderUnavailableError("Connection refused")
        elif self.should_fail_type == "timeout":
            raise EmbeddingTimeoutError("Request timed out")
        elif self.should_fail_type == "generic":
            raise EmbeddingError("General failure")
        elif self.should_fail_type == "invalid_value":
            raise InvalidVectorError("Empty embedding")
        return self._make_vector()

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        self.embed_batch_call_count += 1
        if self.should_fail_type == "batch_count_mismatch":
            # Return fewer vectors than sent
            return [self._make_vector()] * max(0, len(texts) - 1)
        return [self._make_vector() if t else [] for t in texts]

    def supports_batch(self) -> bool:
        return self._batch_support

    def validate_dimensions(self, vector: list[float]) -> bool:
        return len(vector) == self.dimension

    def normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in vector))
        if norm == 0:
            return vector
        return [x / norm for x in vector]

    def get_metadata(self) -> dict:
        return {
            "provider": "mock",
            "model": "mock-model",
            "dimension": self.dimension,
            "supports_batch": self._batch_support,
        }


# ---------------------------------------------------------------------------
# Test Suite
# ---------------------------------------------------------------------------

class TestEmbeddingPipeline(unittest.TestCase):

    # -----------------------------------------------------------------------
    # Single-item tests (backward compatibility)
    # -----------------------------------------------------------------------

    def test_mock_provider_happy_path(self):
        provider = MockEmbeddingProvider(dimension=384)
        service = EmbeddingService(provider=provider)

        chunk = make_chunk()
        emb = service.generate(chunk)

        self.assertEqual(emb.file_name, "MyClass.java")
        self.assertEqual(emb.class_name, "MyClass")
        self.assertEqual(emb.method_name, "myMethod")
        self.assertEqual(len(emb.vector), 384)

        l2_norm = math.sqrt(sum(x * x for x in emb.vector))
        self.assertAlmostEqual(l2_norm, 1.0)

    def test_provider_metadata(self):
        provider = MockEmbeddingProvider(dimension=768)
        meta = provider.get_metadata()
        self.assertEqual(meta["provider"], "mock")
        self.assertEqual(meta["dimension"], 768)

    def test_provider_errors(self):
        for fail_type, exc_cls in [
            ("connection", ProviderUnavailableError),
            ("timeout", EmbeddingTimeoutError),
            ("generic", EmbeddingError),
        ]:
            provider = MockEmbeddingProvider(should_fail_type=fail_type)
            service = EmbeddingService(provider=provider)
            with self.assertRaises(exc_cls):
                service.embed_question("hello")

    def test_ollama_provider_exceptions(self):
        # ConnectionRefusedError → ProviderUnavailableError
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.side_effect = ConnectionRefusedError("Connection refused")
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(ProviderUnavailableError):
                provider.embed("hello")

        # TimeoutError → EmbeddingTimeoutError
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.side_effect = TimeoutError("Timed out")
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(EmbeddingTimeoutError):
                provider.embed("hello")

        # Dimension mismatch → InvalidVectorError
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.return_value = {"embeddings": [[0.1] * (settings.EMBEDDING_DIMENSION - 2)]}
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(InvalidVectorError):
                provider.embed("hello")

    # -----------------------------------------------------------------------
    # Batch tests
    # -----------------------------------------------------------------------

    def test_batch_empty_input(self):
        provider = MockEmbeddingProvider(dimension=768)
        service = EmbeddingService(provider=provider, batch_size=4)
        result = service.generate_batch([])
        self.assertEqual(result, [])

    def test_batch_single_chunk(self):
        provider = MockEmbeddingProvider(dimension=768)
        service = EmbeddingService(provider=provider, batch_size=4)
        chunks = [make_chunk(chunk_id="c1")]
        result = service.generate_batch(chunks)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].file_name, "MyClass.java")
        # Exactly 1 embed_batch call with 1 item
        self.assertEqual(provider.embed_batch_call_count, 1)

    def test_batch_multiple_chunks_order_preserved(self):
        provider = MockEmbeddingProvider(dimension=768)
        service = EmbeddingService(provider=provider, batch_size=3)
        chunks = [
            make_chunk(chunk_id=f"c{i}", method_name=f"method{i}", source_code=f"void method{i}(){{}}")
            for i in range(7)
        ]
        result = service.generate_batch(chunks)
        self.assertEqual(len(result), 7)
        for i, emb in enumerate(result):
            self.assertEqual(emb.method_name, f"method{i}")

    def test_batch_uses_native_batch_not_single(self):
        """Provider with batch support should use embed_batch, not embed."""
        provider = MockEmbeddingProvider(dimension=768, batch_support=True)
        service = EmbeddingService(provider=provider, batch_size=4)
        chunks = [make_chunk(chunk_id=f"c{i}") for i in range(4)]
        service.generate_batch(chunks)
        self.assertEqual(provider.embed_batch_call_count, 1)
        self.assertEqual(provider.embed_call_count, 0)

    def test_batch_sequential_fallback_when_no_batch_support(self):
        """Provider without batch support must fall back to sequential single-item calls."""
        provider = MockEmbeddingProvider(dimension=768, batch_support=False)
        service = EmbeddingService(provider=provider, batch_size=4)
        chunks = [make_chunk(chunk_id=f"c{i}") for i in range(5)]
        result = service.generate_batch(chunks)
        self.assertEqual(len(result), 5)
        self.assertEqual(provider.embed_call_count, 5)
        self.assertEqual(provider.embed_batch_call_count, 0)

    def test_batch_configurable_batch_size(self):
        """Batch size of 2 on 5 chunks should trigger 3 batch calls."""
        provider = MockEmbeddingProvider(dimension=768, batch_support=True)
        service = EmbeddingService(provider=provider, batch_size=2)
        chunks = [make_chunk(chunk_id=f"c{i}") for i in range(5)]
        result = service.generate_batch(chunks)
        self.assertEqual(len(result), 5)
        self.assertEqual(provider.embed_batch_call_count, 3)  # ceil(5/2) = 3

    def test_batch_vector_validation_mismatch_raises(self):
        """If provider returns wrong number of vectors, InvalidVectorError is raised."""
        provider = MockEmbeddingProvider(dimension=768, should_fail_type="batch_count_mismatch")
        service = EmbeddingService(provider=provider, batch_size=4)
        chunks = [make_chunk(chunk_id=f"c{i}") for i in range(4)]
        with self.assertRaises(InvalidVectorError):
            service.generate_batch(chunks)

    def test_ollama_provider_supports_batch(self):
        provider = OllamaEmbeddingProvider()
        self.assertTrue(provider.supports_batch())

    def test_ollama_batch_connection_error(self):
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.side_effect = ConnectionRefusedError("refused")
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(ProviderUnavailableError):
                provider.embed_batch(["hello", "world"])

    def test_ollama_batch_dimension_mismatch(self):
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.return_value = {
                "embeddings": [
                    [0.1] * (settings.EMBEDDING_DIMENSION - 2),
                    [0.1] * settings.EMBEDDING_DIMENSION,
                ]
            }
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(InvalidVectorError):
                provider.embed_batch(["hello", "world"])


if __name__ == "__main__":
    unittest.main()
