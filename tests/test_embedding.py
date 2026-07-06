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


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Mock implementation of EmbeddingProvider for testing.
    """
    def __init__(self, dimension=768, should_fail_type=None):
        self.dimension = dimension
        self.should_fail_type = should_fail_type

    def embed(self, text: str) -> list[float]:
        if self.should_fail_type == "connection":
            raise ProviderUnavailableError("Connection refused")
        elif self.should_fail_type == "timeout":
            raise EmbeddingTimeoutError("Request timed out")
        elif self.should_fail_type == "invalid_dim":
            return [0.1] * (self.dimension - 5)
        elif self.should_fail_type == "invalid_value":
            raise InvalidVectorError("Empty embedding")
        elif self.should_fail_type == "generic":
            raise EmbeddingError("General failure")
        
        vector = [1.0] * self.dimension
        if not self.validate_dimensions(vector):
            raise InvalidVectorError("Mock dimension mismatch")
        return self.normalize(vector)

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
            "dimension": self.dimension
        }


class TestEmbeddingPipeline(unittest.TestCase):

    def test_mock_provider_happy_path(self):
        provider = MockEmbeddingProvider(dimension=384)
        service = EmbeddingService(provider=provider)
        
        chunk = CodeChunk(
            chunk_id="test_id",
            project_id="test_project",
            file_path="MyClass.java",
            file_name="MyClass.java",
            class_name="MyClass",
            method_name="myMethod",
            chunk_type="METHOD",
            content="public void myMethod() {}",
            source_code="public void myMethod() {}",
            start_line=10,
            end_line=12,
            content_hash="abc"
        )
        
        emb = service.generate(chunk)
        self.assertEqual(emb.file_name, "MyClass.java")
        self.assertEqual(emb.class_name, "MyClass")
        self.assertEqual(emb.method_name, "myMethod")
        self.assertEqual(len(emb.vector), 384)
        
        # L2 norm of the returned normalized mock vector should be 1.0
        l2_norm = math.sqrt(sum(x * x for x in emb.vector))
        self.assertAlmostEqual(l2_norm, 1.0)

    def test_provider_metadata(self):
        provider = MockEmbeddingProvider(dimension=768)
        meta = provider.get_metadata()
        self.assertEqual(meta["provider"], "mock")
        self.assertEqual(meta["dimension"], 768)

    def test_provider_errors(self):
        # 1. Connection error
        provider = MockEmbeddingProvider(should_fail_type="connection")
        service = EmbeddingService(provider=provider)
        with self.assertRaises(ProviderUnavailableError):
            service.embed_question("hello")

        # 2. Timeout error
        provider = MockEmbeddingProvider(should_fail_type="timeout")
        service = EmbeddingService(provider=provider)
        with self.assertRaises(EmbeddingTimeoutError):
            service.embed_question("hello")

        # 3. Generic error
        provider = MockEmbeddingProvider(should_fail_type="generic")
        service = EmbeddingService(provider=provider)
        with self.assertRaises(EmbeddingError):
            service.embed_question("hello")

    def test_ollama_provider_exceptions(self):
        # Mock ollama.embed to raise ConnectionRefusedError
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.side_effect = ConnectionRefusedError("Connection refused")
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(ProviderUnavailableError):
                provider.embed("hello")

        # Mock ollama.embed to raise TimeoutError
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.side_effect = TimeoutError("Timed out")
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(EmbeddingTimeoutError):
                provider.embed("hello")

        # Mock ollama.embed to return invalid dimensions
        with patch("ecip_core.embedding.providers.ollama_embedding_provider.embed") as mock_embed:
            mock_embed.return_value = {"embeddings": [[0.1] * (settings.EMBEDDING_DIMENSION - 2)]}
            provider = OllamaEmbeddingProvider()
            with self.assertRaises(InvalidVectorError):
                provider.embed("hello")


if __name__ == "__main__":
    unittest.main()
