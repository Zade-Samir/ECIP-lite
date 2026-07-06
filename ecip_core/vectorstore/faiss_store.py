import json
import faiss
import numpy as np
from pathlib import Path
from ecip_core.inference.config.settings import settings
from ecip_core.embedding.models.embedding import Embedding
from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class FAISSStore:
    """
    Production-ready FAISS index management service.
    Supports persistence, loading, incremental updates, deletion, and search.
    """

    def __init__(
        self,
        index_path: str | None = None,
        metadata_path: str | None = None,
    ):
        self.dimension = settings.EMBEDDING_DIMENSION
        self.index_path = Path(index_path) if index_path else None
        self.metadata_path = Path(metadata_path) if metadata_path else None

        self.metadata: list[Embedding] = []
        self.index = faiss.IndexFlatL2(self.dimension)

        # Try to load from disk if paths provided
        if self.index_path and self.metadata_path:
            self._load()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def add(self, embedding: Embedding) -> None:
        """Add a single embedding vector to the index."""
        self._validate_dimension(embedding.vector, context="add")

        vector = np.array([embedding.vector], dtype="float32")
        self.index.add(vector)
        self.metadata.append(embedding)
        logger.info("Vector added")

        self._save()

    def search(self, vector: list[float], k: int = 3) -> list[Embedding]:
        """Search for top-K nearest neighbours."""
        self._validate_dimension(vector, context="search")

        if self.index.ntotal == 0:
            return []

        query = np.array([vector], dtype="float32")
        distances, indices = self.index.search(query, min(k, self.index.ntotal))

        results: list[Embedding] = []
        for idx in indices[0]:
            if idx == -1:
                continue
            if idx >= len(self.metadata):
                logger.warning("Missing metadata")
                continue
            results.append(self.metadata[idx])

        logger.info(f"Search completed: {len(results)} results")
        return results

    def search_with_scores(self, vector: list[float], k: int = 3) -> list[tuple[Embedding, float]]:
        """Search and return both the matched embeddings and their corresponding distances."""
        self._validate_dimension(vector, context="search_with_scores")

        if self.index.ntotal == 0:
            return []

        query = np.array([vector], dtype="float32")
        distances, indices = self.index.search(query, min(k, self.index.ntotal))

        results: list[tuple[Embedding, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == -1:
                continue
            if idx >= len(self.metadata):
                logger.warning("Missing metadata")
                continue
            results.append((self.metadata[idx], float(dist)))

        logger.info(f"Search completed: {len(results)} results with scores")
        return results

    def remove_file(self, file_path: str) -> None:
        """Remove all vectors belonging to a file and rebuild the index."""
        try:
            name_to_remove = Path(file_path).name
            new_metadata = [
                e for e in self.metadata
                if Path(e.file_name).name != name_to_remove
            ]

            # Rebuild flat index without the removed file's vectors
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []

            for e in new_metadata:
                vector = np.array([e.vector], dtype="float32")
                self.index.add(vector)
                self.metadata.append(e)

            logger.info("Stale vector cleaned")
            self._save()
        except Exception as e:
            logger.error("FAISS update failure")
            raise e

    def search_question(
        self,
        question: str,
        embedding_service,
        k: int = 3,
    ) -> list[Embedding]:
        """Convenience method: embed a question then search."""
        vector = embedding_service.embed_question(question)
        return self.search(vector, k)

    def vector_count(self) -> int:
        """Return total number of vectors currently indexed."""
        return self.index.ntotal

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _save(self) -> None:
        """Persist FAISS index and metadata to disk."""
        if not self.index_path or not self.metadata_path:
            return

        try:
            self.index_path.parent.mkdir(parents=True, exist_ok=True)
            self.metadata_path.parent.mkdir(parents=True, exist_ok=True)

            faiss.write_index(self.index, str(self.index_path))

            serialized = [
                {
                    "file_name": e.file_name,
                    "class_name": e.class_name,
                    "method_name": e.method_name,
                    "source_code": e.source_code,
                    "vector": e.vector,
                    "chunk_id": e.chunk_id,
                    "file_path": e.file_path,
                    "chunk_type": e.chunk_type,
                    "start_line": e.start_line,
                    "end_line": e.end_line,
                }
                for e in self.metadata
            ]
            with open(self.metadata_path, "w", encoding="utf-8") as f:
                json.dump(serialized, f)

            logger.info("Index saved")
        except Exception as e:
            logger.error(f"Save failure: {e}")
            raise

    def _load(self) -> None:
        """Load FAISS index and metadata from disk if they exist."""
        index_exists = self.index_path.exists()
        meta_exists = self.metadata_path.exists()

        if not index_exists or not meta_exists:
            return

        try:
            self.index = faiss.read_index(str(self.index_path))

            with open(self.metadata_path, "r", encoding="utf-8") as f:
                raw = json.load(f)

            self.metadata = [
                Embedding(
                    file_name=item["file_name"],
                    class_name=item["class_name"],
                    method_name=item["method_name"],
                    source_code=item["source_code"],
                    vector=item["vector"],
                    chunk_id=item.get("chunk_id"),
                    file_path=item.get("file_path"),
                    chunk_type=item.get("chunk_type"),
                    start_line=item.get("start_line"),
                    end_line=item.get("end_line"),
                )
                for item in raw
            ]

            logger.info(f"Index loaded: {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Load failure — resetting to empty index: {e}")
            self.index = faiss.IndexFlatL2(self.dimension)
            self.metadata = []

    # ------------------------------------------------------------------
    # Internal validation
    # ------------------------------------------------------------------

    def _validate_dimension(self, vector: list[float], context: str = "") -> None:
        """Raise ValueError if vector dimension doesn't match expected."""
        if len(vector) != self.dimension:
            logger.error(
                f"Dimension mismatch during {context}: "
                f"expected {self.dimension}, got {len(vector)}"
            )
            raise ValueError(
                f"Vector dimension mismatch: expected {self.dimension}, got {len(vector)}."
            )