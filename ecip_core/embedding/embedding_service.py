from ecip_core.chunking.code_chunk import CodeChunk
from ecip_core.embedding.models.embedding import Embedding
from ecip_core.embedding.embedding_provider import EmbeddingProvider
from ecip_core.embedding.providers.ollama_embedding_provider import (
    OllamaEmbeddingProvider,
)


class EmbeddingService:
    """
    Coordinates embedding generation using the configured provider.
    """

    def __init__(self, provider: EmbeddingProvider | None = None):
        self.provider = provider or OllamaEmbeddingProvider()

    def generate(self, chunk: CodeChunk) -> Embedding:
        vector = self.provider.embed(chunk.source_code)

        return Embedding(
            file_name=chunk.file_name,
            class_name=chunk.class_name,
            method_name=chunk.method_name or "",
            source_code=chunk.source_code,
            vector=vector,
        )

    def embed_question(self, question: str) -> list[float]:
        return self.provider.embed(question)