from ecip_core.embedding import embedding_service
import faiss
import numpy as np
from ecip_core.inference.config.settings import settings

from ecip_core.embedding.models.embedding import Embedding


class FAISSStore:
    """
    Stores and searches embedding vectors.
    """

    def __init__(self):

        self.dimension = settings.EMBEDDING_DIMENSION

        self.index = faiss.IndexFlatL2(
            self.dimension
        )

        self.metadata = []

    def add(
        self,
        embedding: Embedding
    ):

        vector = np.array(
            [embedding.vector],
            dtype="float32"
        )

        self.index.add(vector)

        self.metadata.append(embedding)

    def search(
        self,
        vector: list[float],
        k: int = 3
    ):

        query = np.array(
            [vector],
            dtype="float32"
        )

        distances, indices = self.index.search(
            query,
            k
        )

        results = []

        for idx in indices[0]:

            if idx == -1:
                continue

            results.append(
                self.metadata[idx]
            )

        return results

    def search_question(
        self,
        question: str,
        embedding_service,
        k: int = 3,
        ):

        vector = embedding_service.embed_question(question)

        return self.search(vector, k)