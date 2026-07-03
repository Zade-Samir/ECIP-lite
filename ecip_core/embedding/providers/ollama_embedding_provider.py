from ollama import embed

from ecip_core.chunking.code_chunk import CodeChunk
from ecip_core.embedding.embedding_provider import EmbeddingProvider
from ecip_core.embedding.models.embedding import Embedding
from ecip_core.inference.config.settings import settings


class OllamaEmbeddingProvider(EmbeddingProvider):

    MODEL = "nomic-embed-text"

    def generate(
        self,
        chunk: CodeChunk
    ) -> Embedding:

        response = embed(
            model=self.MODEL,
            input=chunk.source_code
        )

        return Embedding(
            file_name=chunk.file_name,
            class_name=chunk.class_name,
            method_name=chunk.method_name,
            source_code=chunk.source_code,
            vector=response["embeddings"][0]
        )

    def embed(
        self,
        text: str
    ) -> list[float]:
    
        response = embed(
            model=settings.EMBEDDING_MODEL,
            input=text
        )
        return response["embeddings"][0]