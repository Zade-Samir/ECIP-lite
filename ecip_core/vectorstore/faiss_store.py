from ecip_core.embedding import embedding_service
import faiss
import numpy as np
from pathlib import Path
from ecip_core.inference.config.settings import settings

from ecip_core.embedding.models.embedding import Embedding
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


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

    def remove_file(self, file_path: str):
        try:
            name_to_remove = Path(file_path).name
            new_metadata = [e for e in self.metadata if Path(e.file_name).name != name_to_remove]
            
            # Rebuild Flat Index
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []
            
            for e in new_metadata:
                self.add(e)
                
            logger.info("Stale vector cleaned")
        except Exception as e:
            logger.error("FAISS update failure")
            raise e

    def search_question(
        self,
        question: str,
        embedding_service,
        k: int = 3,
        ):

        vector = embedding_service.embed_question(question)

        return self.search(vector, k)