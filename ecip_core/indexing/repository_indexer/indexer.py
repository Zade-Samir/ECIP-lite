import os
import time
import subprocess
import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

from ecip_core.common.logger import get_logger
from ecip_core.workspace.manager import workspace_manager
from ecip_core.indexing.index_builder import IndexBuilder
from ecip_core.storage.sqlite.database import Database
from ecip_core.graph.factory import get_graph_provider

logger = get_logger(__name__)


class RepositoryIndexer:
    """
    Engine to index multiple git repositories into a unified enterprise knowledge graph
    while preserving isolation boundaries and building cross-repository links.
    """

    def __init__(self):
        self.workspace_manager = workspace_manager

    def register_repository(
        self,
        repository_id: str,
        name: str,
        root_path: str,
        branch: str = "main",
        language: str = "Java",
        project_type: str = "Maven"
    ) -> Dict[str, Any]:
        """
        Registers a repository into the registry.
        """
        # Duplicate registration check is done in WorkspaceManager.register_repository
        try:
            return self.workspace_manager.register_repository(
                repository_id=repository_id,
                name=name,
                root_path=root_path,
                branch=branch,
                language=language,
                project_type=project_type
            )
        except ValueError as e:
            if "already registered" in str(e).lower():
                logger.warning("Duplicate repository")
            raise e

    def discover_repositories(self, parent_directory: str) -> List[Dict[str, Any]]:
        """
        Discovers project repositories in a parent directory.
        """
        discovered = []
        parent_path = Path(parent_directory)
        if not parent_path.exists() or not parent_path.is_dir():
            logger.warning("Unsupported repository")
            return discovered

        for child in parent_path.iterdir():
            if child.is_dir() and not child.name.startswith("."):
                has_git = (child / ".git").exists()
                has_pom = (child / "pom.xml").exists()
                has_gradle = (child / "build.gradle").exists()
                if has_git or has_pom or has_gradle:
                    repo_id = child.name.lower().replace(" ", "-")
                    discovered.append({
                        "repository_id": repo_id,
                        "name": child.name,
                        "root_path": str(child.resolve()),
                        "branch": "main",
                        "language": "Java",
                        "project_type": "Maven" if has_pom else ("Gradle" if has_gradle else "Unknown")
                    })
        return discovered

    def get_git_commit_hash(self, repo_path: str) -> str:
        """
        Gets the current git commit hash of a repository directory.
        """
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            return res.stdout.strip()
        except Exception:
            # Fallback to direct ref reading
            try:
                git_dir = Path(repo_path) / ".git"
                if git_dir.exists():
                    head_file = git_dir / "HEAD"
                    if head_file.exists():
                        with open(head_file, "r") as f:
                            ref = f.read().strip()
                        if ref.startswith("ref:"):
                            ref_path = git_dir / ref.split(" ")[1]
                            if ref_path.exists():
                                with open(ref_path, "r") as f:
                                    return f.read().strip()
            except Exception:
                pass
        return "unknown"

    def index_repository(self, repository_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Indexes a single repository incrementally.
        """
        repo = self.workspace_manager.get_repository(repository_id)
        if not repo:
            logger.error("Indexing failed")
            raise ValueError(f"Repository '{repository_id}' is not registered.")

        root_path = Path(repo["root_path"])
        if not root_path.exists() or not root_path.is_dir():
            logger.warning("Unsupported repository")
            logger.error("Indexing failed")
            raise FileNotFoundError(f"Root path '{repo['root_path']}' does not exist or is not a directory.")

        commit_hash = self.get_git_commit_hash(str(root_path.resolve()))

        # Incremental check
        if not force and repo["commit_hash"] == commit_hash and repo["commit_hash"] != "unknown":
            logger.info(f"Repository skipped (unchanged): {repository_id}")
            return {
                "repository_id": repository_id,
                "status": "skipped",
                "commit_hash": commit_hash,
                "files_scanned": 0,
                "files_indexed": 0
            }

        # Indexing run
        start_time = time.perf_counter()
        old_active = self.workspace_manager.get_active_workspace()
        try:
            self.workspace_manager.set_active_workspace(repository_id)
            
            builder = IndexBuilder()
            builder.build(str(root_path.resolve()), project_id=repository_id)
            
            # Update registered commit metadata
            self.workspace_manager.update_repository_commit(repository_id, commit_hash)
            
            duration_ms = int((time.perf_counter() - start_time) * 1000)
            logger.info("Repository indexed")
            
            return {
                "repository_id": repository_id,
                "status": "success",
                "commit_hash": commit_hash,
                "duration_ms": duration_ms
            }
        except Exception as e:
            logger.error("Indexing failed")
            raise e
        finally:
            self.workspace_manager.set_active_workspace(old_active)

    def index_all(self, force: bool = False) -> Dict[str, Any]:
        """
        Cross-repository scheduler that indexes all registered repositories sequentially.
        """
        repos = self.workspace_manager.list_repositories()
        stats = {
            "repositories_scanned": len(repos),
            "repositories_indexed": 0,
            "duration_ms": 0,
            "cross_repo_links_created": 0
        }
        
        start_time = time.perf_counter()
        
        for r in repos:
            try:
                res = self.index_repository(r["repository_id"], force=force)
                if res.get("status") == "success":
                    stats["repositories_indexed"] += 1
            except Exception as e:
                logger.error(f"Failed to index repository {r['repository_id']}: {e}")
                logger.error("Indexing failed")
                
        # Link cross-repository dependencies
        try:
            links_count = self.create_cross_repository_links()
            stats["cross_repo_links_created"] = links_count
        except Exception as e:
            logger.error(f"Failed to build cross-repository links: {e}")
            logger.error("Graph update failed")

        stats["duration_ms"] = int((time.perf_counter() - start_time) * 1000)
        return stats

    def create_cross_repository_links(self) -> int:
        """
        Finds unresolved class dependencies in each repository and builds edges across repository boundaries.
        """
        repos = self.workspace_manager.list_repositories()
        class_to_repo = {}
        
        old_active = self.workspace_manager.get_active_workspace()
        
        # 1. Build map of class_name -> repository_id for all classes in the enterprise context
        for repo in repos:
            repo_id = repo["repository_id"]
            try:
                self.workspace_manager.set_active_workspace(repo_id)
                db = Database()
                cursor = db.get_connection().cursor()
                cursor.execute("SELECT class_name FROM java_files WHERE class_name IS NOT NULL")
                classes = [row[0] for row in cursor.fetchall()]
                for cls in classes:
                    class_to_repo[cls] = repo_id
            except Exception:
                pass
        
        links_created = 0
        provider = get_graph_provider()
        
        # 2. Iterate through all repository edges and link unresolved external targets to other repositories
        for repo in repos:
            repo_id = repo["repository_id"]
            try:
                self.workspace_manager.set_active_workspace(repo_id)
                db = Database()
                cursor = db.get_connection().cursor()
                
                # Fetch all local edges
                cursor.execute("SELECT source_class, target_class, relationship_type FROM dependency_edges")
                edges = cursor.fetchall()
                
                # Fetch local classes to distinguish unresolved targets
                cursor.execute("SELECT class_name FROM java_files WHERE class_name IS NOT NULL")
                local_classes = {row[0] for row in cursor.fetchall()}
                
                for src, tgt, rel_type in edges:
                    # If target class is not within local workspace, but is registered in another repository
                    if tgt not in local_classes and tgt in class_to_repo:
                        target_repo = class_to_repo[tgt]
                        if target_repo != repo_id:
                            # Add cross-repository relationship to graph database
                            if hasattr(provider, "create_cross_repo_relationship"):
                                provider.create_cross_repo_relationship(
                                    source_id=src,
                                    source_project=repo_id,
                                    target_id=tgt,
                                    target_project=target_repo,
                                    rel_type=rel_type,
                                    properties={"cross_repository": "true"}
                                )
                                links_created += 1
                                logger.info("Cross-repository links created")
            except Exception as e:
                logger.error(f"Error creating cross-repository links for {repo_id}: {e}")
                logger.error("Graph update failed")
                
        # Restore original workspace context
        self.workspace_manager.set_active_workspace(old_active)
        return links_created
