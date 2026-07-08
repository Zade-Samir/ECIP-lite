import time
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ecip_core.diagnostics.models import HealthReport
from ecip_core.storage.sqlite.database import Database
from ecip_core.settings import settings

logger = logging.getLogger("ecip.diagnostics")


class DiagnosticsService:
    """
    Diagnostics service executing integrity and consistency checks on:
    - SQLite schema & database state
    - FAISS indices & metadata alignment
    - Code file tracking & dependency graphs
    - Response caches
    - Active workspaces
    """

    def run_diagnostics(self) -> HealthReport:
        """
        Executes all diagnostics checks, measures latency, and generates a typed HealthReport.
        """
        logger.info("Diagnostics started")
        start_time = time.perf_counter()

        errors: List[str] = []
        warnings: List[str] = []
        passed: List[str] = []
        failed: List[str] = []
        recs: List[str] = []

        # 1. SQLite integrity check
        try:
            ok, err = self.check_sqlite_integrity()
            if ok:
                passed.append("SQLite Integrity Check")
            else:
                failed.append("SQLite Integrity Check")
                errors.append(err or "SQLite integrity failure detected")
                recs.append("Re-index the project to repair database corruption.")
            logger.info("Check completed: SQLite Integrity Check")
        except Exception as e:
            failed.append("SQLite Integrity Check")
            errors.append(f"SQLite integrity check aborted: {e}")
            recs.append("Re-index the project to repair database corruption.")
            logger.error(f"Integrity failure in SQLite check: {e}")

        # 2. Workspace validity check
        try:
            ok, err = self.check_workspace_validity()
            if ok:
                passed.append("Workspace Validity Check")
            else:
                failed.append("Workspace Validity Check")
                errors.append(err or "Active workspace is invalid")
                recs.append("Restore workspace directory or update root path in registry.")
            logger.info("Check completed: Workspace Validity Check")
        except Exception as e:
            failed.append("Workspace Validity Check")
            errors.append(f"Workspace check aborted: {e}")
            recs.append("Restore workspace directory or update root path in registry.")
            logger.error(f"Workspace validation failed: {e}")

        # 3. FAISS Index availability
        try:
            ok, err = self.check_faiss_availability()
            if ok:
                passed.append("FAISS Index Availability")
            else:
                failed.append("FAISS Index Availability")
                errors.append(err or "FAISS index missing or corrupt")
                recs.append("Run indexer command to generate missing vector store index.")
            logger.info("Check completed: FAISS Index Availability")
        except Exception as e:
            failed.append("FAISS Index Availability")
            errors.append(f"FAISS check aborted: {e}")
            recs.append("Run indexer command to generate missing vector store index.")
            logger.error(f"FAISS index availability check failed: {e}")

        # 4. Vector vs Chunk Count check
        try:
            ok, err = self.check_vector_vs_chunk_count()
            if ok:
                passed.append("Vector vs Chunk Count Check")
            else:
                failed.append("Vector vs Chunk Count Check")
                warnings.append(err or "Vector count mismatch")
                recs.append("Perform full re-index to synchronize chunk metadata with FAISS vectors.")
            logger.info("Check completed: Vector vs Chunk Count Check")
        except Exception as e:
            failed.append("Vector vs Chunk Count Check")
            warnings.append(f"Vector vs chunk check aborted: {e}")
            recs.append("Perform full re-index to synchronize chunk metadata with FAISS vectors.")
            logger.warning(f"Vector vs chunk count check failed: {e}")

        # 5. Missing source files check
        try:
            ok, missing_paths = self.check_missing_source_files()
            if ok:
                passed.append("Source Files Existence Check")
            else:
                failed.append("Source Files Existence Check")
                warnings.append(f"Missing source files: {', '.join(missing_paths)}")
                recs.append("Clean metadata database to remove deleted files.")
            logger.info("Check completed: Source Files Existence Check")
        except Exception as e:
            failed.append("Source Files Existence Check")
            warnings.append(f"Source files check aborted: {e}")
            recs.append("Clean metadata database to remove deleted files.")
            logger.warning(f"Source files existence check failed: {e}")

        # 6. Orphaned metadata check
        try:
            ok, err = self.check_orphaned_metadata()
            if ok:
                passed.append("Orphaned Metadata Check")
            else:
                failed.append("Orphaned Metadata Check")
                warnings.append(err or "Orphaned chunks found")
                recs.append("Clean database to remove orphaned method chunks.")
            logger.info("Check completed: Orphaned Metadata Check")
        except Exception as e:
            failed.append("Orphaned Metadata Check")
            warnings.append(f"Orphaned check aborted: {e}")
            recs.append("Clean database to remove orphaned method chunks.")
            logger.warning(f"Orphaned metadata check failed: {e}")

        # 7. Dependency graph consistency
        try:
            ok, err = self.check_dependency_consistency()
            if ok:
                passed.append("Dependency Graph Consistency")
            else:
                failed.append("Dependency Graph Consistency")
                warnings.append(err or "Dependency graph inconsistencies found")
                recs.append("Update dependency graph using project re-index.")
            logger.info("Check completed: Dependency Graph Consistency")
        except Exception as e:
            failed.append("Dependency Graph Consistency")
            warnings.append(f"Dependency check aborted: {e}")
            recs.append("Update dependency graph using project re-index.")
            logger.warning(f"Dependency graph check failed: {e}")

        # 8. Cache consistency check
        try:
            ok, err = self.check_cache_consistency()
            if ok:
                passed.append("Cache Consistency Check")
            else:
                failed.append("Cache Consistency Check")
                warnings.append(err or "Cache inconsistencies found")
                recs.append("Clear caches using response cache purge utility or clear disk folder.")
            logger.info("Check completed: Cache Consistency Check")
        except Exception as e:
            failed.append("Cache Consistency Check")
            warnings.append(f"Cache check aborted: {e}")
            recs.append("Clear caches using response cache purge utility or clear disk folder.")
            logger.warning(f"Cache consistency check failed: {e}")

        # 9. Configuration validation
        try:
            ok, err = self.check_configuration_validation()
            if ok:
                passed.append("Configuration Validation")
            else:
                failed.append("Configuration Validation")
                warnings.append(err or "Configuration is invalid")
                recs.append("Adjust settings in .env or config file.")
            logger.info("Check completed: Configuration Validation")
        except Exception as e:
            failed.append("Configuration Validation")
            warnings.append(f"Configuration check aborted: {e}")
            recs.append("Adjust settings in .env or config file.")
            logger.warning(f"Configuration validation check failed: {e}")

        # Determine overall status
        if errors:
            status = "unhealthy"
        elif warnings:
            status = "degraded"
        else:
            status = "healthy"

        # Unique recommendations list
        unique_recs = []
        for r in recs:
            if r not in unique_recs:
                unique_recs.append(r)

        end_time = time.perf_counter()
        execution_time_ms = (end_time - start_time) * 1000.0

        report = HealthReport(
            overall_status=status,
            warnings=warnings,
            errors=errors,
            checks_passed=passed,
            checks_failed=failed,
            recommendations=unique_recs,
            execution_time_ms=execution_time_ms
        )

        logger.info("Report generated")
        return report

    # ─── Individual Diagnostic Checks ──────────────────────────────────────

    def check_sqlite_integrity(self) -> Tuple[bool, Optional[str]]:
        """Validates database schema and integrity via PRAGMA."""
        try:
            db = Database()
            cursor = db.get_connection().cursor()
            cursor.execute("PRAGMA integrity_check;")
            res = cursor.fetchone()
            if res and res[0] == "ok":
                return True, None
            return False, f"Integrity check failed: {res[0]}"
        except Exception as e:
            return False, f"Database access error: {e}"

    def check_workspace_validity(self) -> Tuple[bool, Optional[str]]:
        """Verifies if the active workspace directory exists on disk."""
        try:
            from ecip_core.workspace.manager import workspace_manager
            active = workspace_manager.get_active_workspace()
            project = workspace_manager.get_workspace(active)
            if not project:
                return False, f"Active workspace '{active}' is not registered in workspace registry"
            
            root_path = Path(project["root_path"])
            if not root_path.exists():
                return False, f"Active workspace root directory '{root_path}' does not exist on filesystem"
            return True, None
        except Exception as e:
            return False, f"Workspace check error: {e}"

    def check_faiss_availability(self) -> Tuple[bool, Optional[str]]:
        """Verifies if FAISS vector store index file exists and is readable."""
        try:
            import faiss
            idx_path = Path(settings.FAISS_INDEX_PATH)
            meta_path = Path(settings.FAISS_METADATA_PATH)

            if not idx_path.exists():
                return False, f"FAISS index file not found at: {idx_path}"
            if not meta_path.exists():
                return False, f"FAISS metadata file not found at: {meta_path}"

            # Load it briefly to verify file readability/corruption
            try:
                faiss.read_index(str(idx_path))
            except Exception as e:
                return False, f"Corrupted FAISS index: {e}"

            return True, None
        except Exception as e:
            return False, f"FAISS index read error: {e}"

    def check_vector_vs_chunk_count(self) -> Tuple[bool, Optional[str]]:
        """Validates total indexed vectors against total methods chunk metadata."""
        try:
            import faiss
            db = Database()
            cursor = db.get_connection().cursor()
            cursor.execute("SELECT COUNT(*) FROM java_methods")
            chunk_count = cursor.fetchone()[0]

            idx_path = Path(settings.FAISS_INDEX_PATH)
            if not idx_path.exists():
                return False, "Cannot verify counts: FAISS index is missing"

            index = faiss.read_index(str(idx_path))
            vector_count = index.ntotal

            if chunk_count != vector_count:
                return False, f"Vector mismatch: SQLite has {chunk_count} chunks vs FAISS has {vector_count} vectors"
            return True, None
        except Exception as e:
            return False, f"Vector count comparison failed: {e}"

    def check_missing_source_files(self) -> Tuple[bool, List[str]]:
        """Verifies if all tracked metadata files still exist physically on disk."""
        try:
            db = Database()
            cursor = db.get_connection().cursor()
            cursor.execute("SELECT file_path FROM java_files")
            paths = [r[0] for r in cursor.fetchall()]
            
            missing = []
            for p in paths:
                if not Path(p).exists():
                    missing.append(p)

            if missing:
                return False, missing
            return True, []
        except Exception:
            return False, ["Failed to retrieve tracked database files"]

    def check_orphaned_metadata(self) -> Tuple[bool, Optional[str]]:
        """Detects chunks/methods without parent source file references in DB."""
        try:
            db = Database()
            cursor = db.get_connection().cursor()
            cursor.execute("SELECT COUNT(*) FROM java_methods WHERE file_id NOT IN (SELECT id FROM java_files)")
            orphaned = cursor.fetchone()[0]
            
            if orphaned > 0:
                return False, f"Found {orphaned} orphaned methods without associated java files in DB"
            return True, None
        except Exception as e:
            return False, f"Orphaned metadata lookup failed: {e}"

    def check_dependency_consistency(self) -> Tuple[bool, Optional[str]]:
        """Validates dependency edge vertices connect valid existing metadata classes."""
        try:
            db = Database()
            cursor = db.get_connection().cursor()
            
            cursor.execute("SELECT DISTINCT class_name FROM java_files")
            valid_classes = {r[0] for r in cursor.fetchall() if r[0]}

            cursor.execute("SELECT DISTINCT source_class, target_class FROM dependency_edges")
            edges = cursor.fetchall()

            inconsistent = 0
            for src, tgt in edges:
                if src not in valid_classes or tgt not in valid_classes:
                    inconsistent += 1

            if inconsistent > 0:
                return False, f"Found {inconsistent} dependency edges pointing to missing classes in index"
            return True, None
        except Exception as e:
            return False, f"Dependency consistency check failed: {e}"

    def check_cache_consistency(self) -> Tuple[bool, Optional[str]]:
        """Validates response caches are valid pickling entries."""
        try:
            import pickle
            cache_dir = Path(".ecip/cache")
            if cache_dir.exists():
                corrupt_files = 0
                for f in cache_dir.glob("*"):
                    if f.is_file():
                        try:
                            with open(f, "rb") as fp:
                                pickle.load(fp)
                        except Exception:
                            corrupt_files += 1
                if corrupt_files > 0:
                    return False, f"Found {corrupt_files} corrupted cache pickle files in .ecip/cache/"
            return True, None
        except Exception as e:
            return False, f"Cache directory check failed: {e}"

    def check_configuration_validation(self) -> Tuple[bool, Optional[str]]:
        """Validates settings attributes conform to expected boundaries."""
        try:
            if settings.EMBEDDING_DIMENSION <= 0:
                return False, f"EMBEDDING_DIMENSION must be positive, got {settings.EMBEDDING_DIMENSION}"
            if not settings.OLLAMA_BASE_URL.startswith("http"):
                return False, f"OLLAMA_BASE_URL must start with http, got {settings.OLLAMA_BASE_URL}"
            if settings.MAX_TOKENS <= 0:
                return False, f"MAX_TOKENS must be positive, got {settings.MAX_TOKENS}"
            return True, None
        except Exception as e:
            return False, f"Settings check failed: {e}"
