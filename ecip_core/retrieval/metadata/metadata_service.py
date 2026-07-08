import sqlite3
from pathlib import Path
from ecip_core.common.logger import get_logger
from ecip_core.storage.sqlite.repository import JavaRepository
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.retrieval.models.metadata_result import MetadataResult
from ecip_core.embedding.models.embedding import Embedding

logger = get_logger(__name__)


class MetadataSearchService:
    """
    Service responsible for executing deterministic SQLite lookups
    by class name, method name, package, or file path.
    """

    def __init__(self, repository: JavaRepository, faiss_store: FAISSStore):
        self.repository = repository
        self.faiss_store = faiss_store

    def search_classes(self, query: str, exact: bool = True, project_id: str = "default") -> list[MetadataResult]:
        logger.info(f"Metadata query started: search_classes (query={query}, exact={exact})")
        try:
            db_results = self.repository.search_classes(query, exact=exact)
        except (sqlite3.Error, AttributeError) as e:
            logger.error("Database unavailable")
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

        results = self._map_to_results(db_results, project_id=project_id)
        self._log_search_summary(len(results))
        return results

    def search_methods(self, query: str, exact: bool = True, project_id: str = "default") -> list[MetadataResult]:
        logger.info(f"Metadata query started: search_methods (query={query}, exact={exact})")
        try:
            db_results = self.repository.search_methods(query, exact=exact)
        except (sqlite3.Error, AttributeError) as e:
            logger.error("Database unavailable")
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

        results = self._map_to_results(db_results, is_method=True, project_id=project_id)
        self._log_search_summary(len(results))
        return results

    def search_packages(self, query: str, exact: bool = True, project_id: str = "default") -> list[MetadataResult]:
        logger.info(f"Metadata query started: search_packages (query={query}, exact={exact})")
        try:
            db_results = self.repository.search_packages(query, exact=exact)
        except (sqlite3.Error, AttributeError) as e:
            logger.error("Database unavailable")
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

        results = self._map_to_results(db_results, project_id=project_id)
        self._log_search_summary(len(results))
        return results

    def search_file_paths(self, query: str, exact: bool = True, project_id: str = "default") -> list[MetadataResult]:
        logger.info(f"Metadata query started: search_file_paths (query={query}, exact={exact})")
        try:
            db_results = self.repository.search_file_paths(query, exact=exact)
        except (sqlite3.Error, AttributeError) as e:
            logger.error("Database unavailable")
            raise
        except Exception as e:
            logger.error(f"Query execution failed: {e}")
            raise

        results = self._map_to_results(db_results, project_id=project_id)
        self._log_search_summary(len(results))
        return results

    def _map_to_results(
        self,
        db_results: list[dict],
        is_method: bool = False,
        project_id: str = "default"
    ) -> list[MetadataResult]:
        results: list[MetadataResult] = []

        for row in db_results:
            file_path = row["file_path"]
            class_name = row["class_name"]
            package_name = row["package_name"]
            method_name = row.get("method_name") if is_method else None

            # Look up matching vector chunks from persistent store
            chunks = self._find_chunks(file_path, class_name, method_name)

            for chunk in chunks:
                signature = ""
                if chunk.source_code:
                    signature = chunk.source_code.splitlines()[0].strip()

                results.append(
                    MetadataResult(
                        project_id=project_id,
                        chunk_id=chunk.chunk_id or "",
                        file_path=file_path,
                        package_name=package_name,
                        class_name=class_name,
                        method_name=chunk.method_name or "",
                        signature=signature,
                        start_line=chunk.start_line or 0,
                        end_line=chunk.end_line or 0,
                        source_reference=chunk.source_code or "",
                    )
                )

        return results

    def _find_chunks(
        self,
        file_path: str,
        class_name: str,
        method_name: str | None = None
    ) -> list[Embedding]:
        results: list[Embedding] = []
        for e in self.faiss_store.metadata:
            # Support both exact path match and basename matches
            path_match = e.file_path == file_path or (e.file_name and Path(e.file_name).name == Path(file_path).name)
            if not path_match:
                continue
            if e.class_name != class_name:
                continue

            if method_name is not None:
                if e.method_name == method_name:
                    results.append(e)
            else:
                # Class Overview Chunk has empty method_name
                if not e.method_name or e.method_name == "":
                    results.append(e)

        # Fallback: return any chunk for the file if overview chunk is not explicitly marked
        if not results:
            for e in self.faiss_store.metadata:
                path_match = e.file_path == file_path or (e.file_name and Path(e.file_name).name == Path(file_path).name)
                if path_match:
                    results.append(e)
                    break
        return results

    def _log_search_summary(self, count: int) -> None:
        if count > 0:
            logger.info(f"Exact match found. Result count: {count}")
        else:
            logger.warning("No exact match")