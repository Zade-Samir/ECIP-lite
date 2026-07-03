from ecip_core.chunking.code_chunk import CodeChunk
from ecip_core.embedding.providers.ollama_embedding_provider import (
    OllamaEmbeddingProvider,
)
from ecip_core.embedding.models.embedding import Embedding


class EmbeddingService:

    def __init__(self):

        self.provider = OllamaEmbeddingProvider()

    def generate(
        self,
        chunk: CodeChunk
    ) -> Embedding:

        return self.provider.generate(chunk)