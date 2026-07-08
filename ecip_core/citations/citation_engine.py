from typing import List
from ecip_core.common.logger import get_logger
from ecip_core.citations.models.citation import Citation
from ecip_core.retrieval.models.hybrid_result import HybridResult

logger = get_logger(__name__)


class CitationEngine:
    """
    Collects retrieved code chunks, validates them, removes duplicates,
    sorts deterministically, and returns typed Citation objects.
    """

    def generate(
        self,
        retrieved_chunks: List[HybridResult],
        project_id: str = ""
    ) -> List[Citation]:
        """
        Main entry point. Converts HybridResult list into validated, deduplicated Citations.
        """
        logger.info("Citation generation started")

        if not retrieved_chunks:
            logger.info("Total citations: 0")
            return []

        try:
            raw_citations = self._build(retrieved_chunks, project_id)
            validated = self._validate(raw_citations)
            deduplicated = self._deduplicate(validated)
            sorted_citations = self._sort(deduplicated)
            logger.info(f"Total citations: {len(sorted_citations)}")
            return sorted_citations

        except Exception as e:
            logger.error(f"Citation generation failure: {e}")
            raise

    # ─── Internal pipeline steps ──────────────────────────────────────────

    def _build(
        self,
        chunks: List[HybridResult],
        project_id: str
    ) -> List[Citation]:
        """Convert HybridResult objects into Citation objects."""
        citations = []
        for chunk in chunks:
            citation = Citation(
                project_id=project_id,
                file_path=chunk.file_path,
                class_name=chunk.class_name,
                method_name=chunk.method_name,
                start_line=chunk.start_line,
                end_line=chunk.end_line,
                chunk_id=chunk.chunk_id,
                confidence=min(1.0, max(0.0, chunk.score))
            )
            citations.append(citation)
        return citations

    def _validate(self, citations: List[Citation]) -> List[Citation]:
        """
        Validate each citation. Remove invalid ones and log warnings/errors.
        """
        valid = []
        for c in citations:
            # Validate file path
            if not c.file_path or not c.file_path.strip():
                logger.error(f"Invalid file path in citation: chunk_id={c.chunk_id}")
                continue

            # Validate line range presence
            if c.start_line is None or c.end_line is None:
                logger.warning(f"Missing line range: chunk_id={c.chunk_id}")
                continue

            # Validate line range logic
            if c.start_line < 0 or c.end_line < 0 or c.start_line > c.end_line:
                logger.error(
                    f"Invalid line range [{c.start_line}-{c.end_line}]: "
                    f"chunk_id={c.chunk_id}"
                )
                continue

            logger.info(f"Citation validated: {c.file_path}:{c.start_line}-{c.end_line}")
            valid.append(c)

        return valid

    def _deduplicate(self, citations: List[Citation]) -> List[Citation]:
        """
        Remove duplicate citations by chunk_id, preserving first occurrence order.
        """
        seen_chunk_ids: set[str] = set()
        unique: List[Citation] = []

        for c in citations:
            if c.chunk_id in seen_chunk_ids:
                logger.warning(f"Duplicate citation removed: chunk_id={c.chunk_id}")
                continue
            seen_chunk_ids.add(c.chunk_id)
            unique.append(c)

        return unique

    def _sort(self, citations: List[Citation]) -> List[Citation]:
        """
        Sort citations deterministically by file path, then start line, then chunk_id.
        """
        return sorted(
            citations,
            key=lambda c: (c.file_path, c.start_line, c.chunk_id)
        )
