import hashlib
import time
from pathlib import Path
from ecip_core.scanner.project_scanner import ProjectScanner
from ecip_core.parser.java.java_parser import JavaParser
from ecip_core.storage.sqlite.repository import JavaRepository

from ecip_core.chunking.java_chunker import JavaChunker
from ecip_core.embedding.embedding_service import EmbeddingService
from ecip_core.vectorstore.faiss_store import FAISSStore
from ecip_core.embedding.models.embedding import Embedding
from ecip_core.dependency.graph_builder import DependencyGraphBuilder
from ecip_core.graph.synchronization.synchronizer import GraphSynchronizer

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class IndexBuilder:
    """
    Builds the ECIP knowledge index for an entire project.
    Uses persistent FAISS index stored inside the project's .ecip/ directory.
    """

    def __init__(self):
        self.scanner = ProjectScanner()
        self.parser = JavaParser()
        self.repository = JavaRepository()
        self.chunker = JavaChunker()
        self.embedding_service = EmbeddingService()
        self.graph_builder = DependencyGraphBuilder()
        self.synchronizer = GraphSynchronizer()
        # FAISSStore is initialized without paths here; paths are set per build()
        self.faiss_store: FAISSStore | None = None

    def build(self, project_path: str, project_id: str = None) -> FAISSStore:
        start_time = time.perf_counter()
        logger.info("Index started")

        project_id = project_id or Path(project_path).name

        ecip_dir = Path(project_path) / ".ecip"
        index_path = str(ecip_dir / "faiss.index")
        metadata_path = str(ecip_dir / "faiss_metadata.json")

        # Initialize (or reload) the persistent FAISS store for this project
        self.faiss_store = FAISSStore(
            index_path=index_path,
            metadata_path=metadata_path,
        )

        try:
            java_files = self.scanner.scan(project_path)
            
            # Scan for SQL and Config files
            path_obj = Path(project_path)
            sql_files = list(path_obj.rglob("*.sql"))
            config_files = (
                list(path_obj.rglob("*.properties")) +
                list(path_obj.rglob("*.yml")) +
                list(path_obj.rglob("*.yaml"))
            )
            
            # Filter out .ecip folder to avoid index recursion
            sql_files = [f for f in sql_files if ".ecip" not in f.parts]
            config_files = [f for f in config_files if ".ecip" not in f.parts]
            
            all_files = java_files + sql_files + config_files
        except Exception as e:
            logger.error("Database failure")
            raise e

        logger.info(f"Found {len(java_files)} Java files, {len(sql_files)} SQL files, {len(config_files)} Config files")
        project_classes = {Path(f).stem for f in java_files}

        stats = {
            "skipped": 0,
            "indexed": 0,
            "removed": 0,
            "total_chunks": 0,
            "total_batches": 0,
        }

        # 1. Identify active file paths and calculate current hashes
        active_files = {}
        for file in all_files:
            file_path_str = str(file.resolve())
            try:
                with open(file, "rb") as f:
                    curr_hash = hashlib.sha256(f.read()).hexdigest()
                active_files[file_path_str] = curr_hash
            except Exception as e:
                logger.error("Hash failure")
                raise e

        # 2. Clean up deleted files from SQLite and FAISS
        try:
            db_file_paths = self.repository.get_all_file_paths()
        except Exception as e:
            logger.error("Database failure")
            raise e

        deleted_file_paths = [p for p in db_file_paths if p not in active_files]
        for p in deleted_file_paths:
            self.repository.delete_by_file_path(p)
            self.repository.delete_class_edges(project_id, Path(p).stem)
            self.synchronizer.delete_class(project_id, Path(p).stem)
            self.faiss_store.remove_file(p)
            stats["removed"] += 1

        # 3. Process active files
        # FAISS-DB consistency check: if FAISS is empty but files have stored hashes,
        # those hashes are stale (e.g., previous indexing crashed mid-way).
        # Force a fresh re-index by clearing stored hashes for all active files.
        if self.faiss_store.index.ntotal == 0 and any(
            self.repository.get_file_hash(str(f.resolve())) for f in all_files
        ):
            logger.warning("FAISS empty but DB has stale hashes — forcing fresh re-index")
            for f in all_files:
                self.repository.clear_file_hash(str(f.resolve()))

        for file in all_files:
            file_path_str = str(file.resolve())
            curr_hash = active_files[file_path_str]

            # Get stored hash from database
            stored_hash = self.repository.get_file_hash(file_path_str)

            if stored_hash == curr_hash:
                logger.info(f"File skipped: {file.name}")
                stats["skipped"] += 1
                # Vectors for this file are already in the persisted FAISS index
            else:
                logger.info(f"File indexed: {file.name}")
                stats["indexed"] += 1

                # If this is a modified file, remove its stale vectors first
                if stored_hash:
                    self.faiss_store.remove_file(file_path_str)

                # Initialize chunks list
                chunks = []

                if file_path_str.endswith(".sql"):
                    try:
                        from ecip_core.parser.sql.sql_parser import SqlParser
                        sql_parser = SqlParser()
                        sql_meta = sql_parser.parse(file_path_str)

                        # Save hash only in database
                        cursor = self.repository.connection.cursor()
                        cursor.execute("SELECT id FROM java_files WHERE file_path = ?", (file_path_str,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute("UPDATE java_files SET file_hash = ? WHERE file_path = ?", (curr_hash, file_path_str))
                        else:
                            cursor.execute("INSERT INTO java_files (file_name, file_path, file_hash) VALUES (?, ?, ?)", (file.name, file_path_str, curr_hash))
                        self.repository.connection.commit()

                        chunks = self._generate_sql_chunks(project_id, file_path_str, sql_meta)
                        logger.info("Metadata indexed")
                    except Exception as e:
                        logger.error("Parse failure")
                        raise e
                elif file_path_str.endswith((".properties", ".yml", ".yaml")):
                    try:
                        from ecip_core.parser.config.config_parser import ConfigParser
                        config_parser = ConfigParser()
                        config_meta = config_parser.parse(file_path_str)

                        # Save hash only in database
                        cursor = self.repository.connection.cursor()
                        cursor.execute("SELECT id FROM java_files WHERE file_path = ?", (file_path_str,))
                        row = cursor.fetchone()
                        if row:
                            cursor.execute("UPDATE java_files SET file_hash = ? WHERE file_path = ?", (curr_hash, file_path_str))
                        else:
                            cursor.execute("INSERT INTO java_files (file_name, file_path, file_hash) VALUES (?, ?, ?)", (file.name, file_path_str, curr_hash))
                        self.repository.connection.commit()

                        chunks = self._generate_config_chunks(project_id, file_path_str, config_meta)
                        logger.info("Metadata indexed")
                    except Exception as e:
                        logger.error("Parse failure")
                        raise e
                else:
                    # Re-parse changed Java file — non-fatal: skip file on error
                    try:
                        parsed = self.parser.parse(file_path_str)
                    except Exception as e:
                        logger.warning(f"Parse failure for {file.name} (invalid syntax?) — skipping: {e}")
                        stats["indexed"] -= 1
                        stats["skipped"] += 1
                        continue  # Skip to next file, don't crash whole build

                    # Re-chunk changed Java file — non-fatal: skip file on error
                    try:
                        chunks = self.chunker.chunk(file_path_str)
                    except Exception as e:
                        logger.warning(f"Chunk failure for {file.name} — skipping: {e}")
                        stats["indexed"] -= 1
                        stats["skipped"] += 1
                        continue

                    # Save metadata and file_hash ONLY after successful parse+chunk
                    self.repository.save(parsed, file_hash=curr_hash)

                    # Build class dependency edges
                    self.graph_builder.build_class_edges(project_id, parsed, project_classes)

                    # Sync graph database (Project, Package, Class, Method nodes)
                    self.synchronizer.sync_class(project_id, parsed)

                # Generate embeddings in batch for all chunks of this file
                if chunks:
                    try:
                        embeddings = self.embedding_service.generate_batch(chunks)
                        batch_count = max(
                            1,
                            (len(chunks) + self.embedding_service.batch_size - 1)
                            // self.embedding_service.batch_size,
                        )
                        stats["total_chunks"] += len(chunks)
                        stats["total_batches"] += batch_count

                        for embedding in embeddings:
                            self.faiss_store.add(embedding)
                    except Exception as e:
                        logger.warning(f"Embedding failure for {file.name} — skipping: {e}")
                        stats["indexed"] -= 1
                        stats["skipped"] += 1

        # Generate Git history chunks
        git_chunks = self._generate_git_chunks(project_id, project_path, java_files)
        if git_chunks:
            try:
                embeddings = self.embedding_service.generate_batch(git_chunks)
                for embedding in embeddings:
                    self.faiss_store.add(embedding)
                logger.info("History updated")
            except Exception as e:
                logger.error(f"Failed to index git history chunks: {e}")

        # Build and save BM25 index
        try:
            from ecip_core.search.bm25.bm25 import BM25Index
            bm25_index = BM25Index()
            chunks_to_index = []
            for e in self.faiss_store.metadata:
                chunks_to_index.append({
                    "chunk_id": e.chunk_id,
                    "content": e.source_code,
                    "file_path": e.file_path,
                    "class_name": e.class_name,
                    "method_name": e.method_name,
                    "start_line": e.start_line,
                    "end_line": e.end_line,
                    "chunk_type": e.chunk_type
                })
            bm25_index.fit(chunks_to_index)
            bm25_path = str(ecip_dir / "bm25_index.json")
            bm25_index.save(bm25_path)
            logger.info("BM25 index saved")
        except Exception as e:
            logger.error(f"Failed to build BM25 index: {e}")

        # Build Call Graph
        try:
            from ecip_core.callgraph.builder import CallGraphBuilder
            call_graph_builder = CallGraphBuilder()
            parsed_all = []
            for file in java_files:
                try:
                    parsed_all.append(self.parser.parse(str(file.resolve())))
                except Exception as e:
                    logger.warning(f"Failed to parse {file} during call graph building: {e}")
            call_graph_builder.build(project_id, parsed_all)
            logger.info("Call graph generated")
        except Exception as e:
            logger.error(f"Failed to generate call graph: {e}")


        duration = time.perf_counter() - start_time
        logger.info(f"Total duration: {duration:.4f}s")

        # Summary report
        print(f"\n--- Indexing Summary Report ---")
        print(f"Files Skipped:   {stats['skipped']}")
        print(f"Files Indexed:   {stats['indexed']}")
        print(f"Files Removed:   {stats['removed']}")
        print(f"Chunks Embedded: {stats['total_chunks']} (in {stats['total_batches']} batches)")
        print(f"Total Duration:  {duration:.4f}s\n")

        return self.faiss_store

    def _generate_sql_chunks(self, project_id: str, file_path_str: str, sql_meta) -> list:
        from ecip_core.chunking.code_chunk import CodeChunk
        import datetime
        from ecip_core.chunking.java_chunker import compute_hash
        
        chunks = []
        file_name = Path(file_path_str).name
        
        # 1. Overview chunk
        overview_content = f"SQL Schema file: {file_name} (path: {file_path_str})\n"
        if sql_meta.tables:
            overview_content += f"Tables: {', '.join([t.name for t in sql_meta.tables])}\n"
        if sql_meta.views:
            overview_content += f"Views: {', '.join([v.name for v in sql_meta.views])}\n"
        if sql_meta.procedures:
            overview_content += f"Procedures: {', '.join([p.name for p in sql_meta.procedures])}\n"
            
        chunks.append(
            CodeChunk(
                chunk_id=f"{file_name}_overview",
                project_id=project_id,
                file_path=file_path_str,
                file_name=file_name,
                class_name="SQL_OVERVIEW",
                method_name=None,
                chunk_type="SQL_OVERVIEW",
                content=overview_content,
                source_code=overview_content,
                start_line=1,
                end_line=1,
                content_hash=compute_hash(overview_content),
                created_at=datetime.datetime.utcnow().isoformat() + "Z"
            )
        )
        
        # 2. Table chunks
        for table in sql_meta.tables:
            tbl_content = f"SQL Table Schema: {table.name} in {file_name}\n"
            tbl_content += "Columns:\n"
            for col in table.columns:
                pk_str = " (PRIMARY KEY)" if col.is_primary else ""
                null_str = " NULL" if col.is_nullable else " NOT NULL"
                tbl_content += f"  - {col.name} {col.data_type}{pk_str}{null_str}\n"
            if table.primary_keys:
                tbl_content += f"Primary Keys: {', '.join(table.primary_keys)}\n"
            if table.foreign_keys:
                tbl_content += "Foreign Keys:\n"
                for fk in table.foreign_keys:
                    tbl_content += f"  - {fk.column} -> {fk.referenced_table}({fk.referenced_column})\n"
                    
            chunks.append(
                CodeChunk(
                    chunk_id=f"sql_table_{table.name}",
                    project_id=project_id,
                    file_path=file_path_str,
                    file_name=file_name,
                    class_name=table.name,
                    method_name=None,
                    chunk_type="SQL_TABLE",
                    content=tbl_content,
                    source_code=tbl_content,
                    start_line=1,
                    end_line=1,
                    content_hash=compute_hash(tbl_content),
                    created_at=datetime.datetime.utcnow().isoformat() + "Z"
                )
            )
            
        return chunks

    def _generate_config_chunks(self, project_id: str, file_path_str: str, config_meta) -> list:
        from ecip_core.chunking.code_chunk import CodeChunk
        import datetime
        from ecip_core.chunking.java_chunker import compute_hash
        
        file_name = Path(file_path_str).name
        
        # Format properties as text block
        props_content = f"Application Configuration properties from {file_name} (path: {file_path_str}):\n"
        if config_meta.profiles:
            props_content += f"Active Profiles: {', '.join(config_meta.profiles)}\n"
        if config_meta.server_port:
            props_content += f"Server Port: {config_meta.server_port}\n"
        if config_meta.datasource_url:
            props_content += f"Datasource JDBC URL: {config_meta.datasource_url}\n"
            
        props_content += "Properties list:\n"
        for k, v in config_meta.properties.items():
            props_content += f"  {k} = {v}\n"
            
        return [
            CodeChunk(
                chunk_id=f"{file_name}_config",
                project_id=project_id,
                file_path=file_path_str,
                file_name=file_name,
                class_name="CONFIG",
                method_name=None,
                chunk_type="CONFIG",
                content=props_content,
                source_code=props_content,
                start_line=1,
                end_line=1,
                content_hash=compute_hash(props_content),
                created_at=datetime.datetime.utcnow().isoformat() + "Z"
            )
        ]

    def _generate_git_chunks(self, project_id: str, project_path: str, java_files: list) -> list:
        from ecip_core.git.scanner import GitRepositoryScanner
        from ecip_core.chunking.code_chunk import CodeChunk
        import datetime
        from ecip_core.chunking.java_chunker import compute_hash

        scanner = GitRepositoryScanner()
        if not scanner.is_git_repo(project_path):
            return []

        chunks = []
        try:
            repo_meta = scanner.scan(project_path)
            
            # 1. Repository History chunk
            repo_text = f"Git Repository History details for project: {project_id}\n"
            repo_text += f"Active Branch: {repo_meta.branch}\n"
            repo_text += f"HEAD Commit Hash: {repo_meta.head_commit}\n"
            repo_text += "Recent Commits:\n"
            for c in repo_meta.commits[:15]:
                repo_text += f"  - {c.commit_hash[:8]} by {c.author} on {c.date}: {c.message}\n"
                
            chunks.append(
                CodeChunk(
                    chunk_id=f"git_repo_{project_id}_history",
                    project_id=project_id,
                    file_path=project_path,
                    file_name="git_history",
                    class_name="GIT_HISTORY",
                    method_name=None,
                    chunk_type="GIT_HISTORY",
                    content=repo_text,
                    source_code=repo_text,
                    start_line=1,
                    end_line=1,
                    content_hash=compute_hash(repo_text),
                    created_at=datetime.datetime.utcnow().isoformat() + "Z"
                )
            )

            # 2. File evolution and ownership chunks
            for file in java_files:
                file_path_str = str(file.resolve())
                try:
                    rel_path = str(file.relative_to(project_path))
                except Exception:
                    rel_path = file.name
                    
                file_git = scanner.scan_file_history(project_path, rel_path)
                if file_git:
                    git_text = f"Git File Evolution & Ownership stats for file '{rel_path}':\n"
                    git_text += f"  - Created by commit: {file_git.creation_commit}\n"
                    git_text += f"  - Last modified by commit: {file_git.last_modified_commit}\n"
                    git_text += f"  - Total revisions: {file_git.total_revisions}\n"
                    git_text += f"  - Contributors/Authors: {', '.join(file_git.contributors)}\n"
                    
                    chunks.append(
                        CodeChunk(
                            chunk_id=f"git_file_{file.name}_evolution",
                            project_id=project_id,
                            file_path=file_path_str,
                            file_name=file.name,
                            class_name=file.stem,
                            method_name=None,
                            chunk_type="GIT_FILE_EVOLUTION",
                            content=git_text,
                            source_code=git_text,
                            start_line=1,
                            end_line=1,
                            content_hash=compute_hash(git_text),
                            created_at=datetime.datetime.utcnow().isoformat() + "Z"
                        )
                    )
        except Exception as e:
            logger.error(f"Failed to scan Git metadata: {e}")
            
        return chunks