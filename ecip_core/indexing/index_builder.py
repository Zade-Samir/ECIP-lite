from ecip_core.scanner.project_scanner import ProjectScanner
from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.storage.sqlite.repository import JavaRepository

from ecip_core.chunking.java_chunker import JavaChunker
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.vectorstore.faiss_store import FAISSStore

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class IndexBuilder:
    """
    Builds the ECIP knowledge index for an entire project.
    """

    def __init__(self):

        self.scanner = ProjectScanner()

        self.parser = JavaParser()
        self.repository = JavaRepository()

        self.chunker = JavaChunker()
        self.embedding_service = EmbeddingService()
        self.faiss_store = FAISSStore()

    def build(
        self,
        project_path: str
    ) -> FAISSStore:

        java_files = self.scanner.scan(project_path)

        logger.info(f"Found {len(java_files)} Java files")

        for file in java_files:

            logger.info(f"Indexing {file.name}")

            # ---------- Metadata ----------

            parsed = self.parser.parse(str(file))

            self.repository.save(parsed)

            # ---------- Semantic ----------

            chunks = self.chunker.chunk(str(file))

            for chunk in chunks:

                embedding = self.embedding_service.generate(chunk)

                self.faiss_store.add(embedding)

        logger.info("Project indexing completed.")

        return self.faiss_store