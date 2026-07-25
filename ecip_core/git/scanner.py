import os
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Optional
from ecip_core.common.logger import get_logger
from ecip_core.models.git_metadata import GitRepositoryMetadata, CommitMetadata, FileGitMetadata

logger = get_logger(__name__)


class GitRepositoryScanner:
    """
    Scans a Git repository directory and extracts history, commit history, blame,
    ownership, and contribution statistics.
    """

    def is_git_repo(self, repo_path: str) -> bool:
        git_dir = Path(repo_path) / ".git"
        return git_dir.exists() and git_dir.is_dir()

    def scan(self, repo_path: str) -> GitRepositoryMetadata:
        if not self.is_git_repo(repo_path):
            logger.error("Invalid repository")
            raise ValueError(f"Directory '{repo_path}' is not a valid Git repository.")

        logger.info("Repository detected")

        # Check shallow clone
        shallow_file = Path(repo_path) / ".git" / "shallow"
        if shallow_file.exists():
            logger.warning("Shallow clone detected")

        # 1. Fetch branch name
        branch = "unknown"
        try:
            res = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            branch = res.stdout.strip()
            if branch == "HEAD":
                logger.warning("Detached HEAD")
        except Exception as e:
            logger.error("Git command failure")
            raise RuntimeError(f"Failed to get git branch name: {e}")

        # 2. Fetch HEAD commit hash
        head_commit = "unknown"
        try:
            res = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            head_commit = res.stdout.strip()
        except Exception as e:
            logger.error("Git command failure")
            raise RuntimeError(f"Failed to get git HEAD commit: {e}")

        repo_meta = GitRepositoryMetadata(
            branch=branch,
            head_commit=head_commit
        )

        # 3. Fetch recent commits (limit to last 50 for performance)
        try:
            res = subprocess.run(
                ["git", "log", "-n", "50", "--pretty=format:%H|%an|%ad|%s", "--name-status"],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            commit_blocks = res.stdout.strip().split("\n\n")
            
            for block in commit_blocks:
                if not block.strip():
                    continue
                lines = block.splitlines()
                header = lines[0].split("|")
                if len(header) < 4:
                    continue
                
                c_hash = header[0].strip()
                author = header[1].strip()
                date = header[2].strip()
                msg = header[3].strip()

                files = []
                for f_line in lines[1:]:
                    f_parts = f_line.split()
                    if len(f_parts) >= 2:
                        files.append(f_parts[1].strip())

                repo_meta.commits.append(
                    CommitMetadata(
                        commit_hash=c_hash,
                        author=author,
                        date=date,
                        message=msg,
                        files_changed=files
                    )
                )
            logger.info("Commits indexed")
        except Exception as e:
            # Empty repositories will throw errors during git log
            logger.warning(f"Failed to read git commit logs (repo might be empty): {e}")

        return repo_meta

    def scan_file_history(self, repo_path: str, relative_file_path: str) -> Optional[FileGitMetadata]:
        """
        Gets evolution, contributors, and blame statistics for a single file.
        """
        if not self.is_git_repo(repo_path):
            return None

        try:
            # Fetch git log for file
            res = subprocess.run(
                ["git", "log", "--follow", "--pretty=format:%H|%an|%ad", "--", relative_file_path],
                cwd=repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=True
            )
            log_lines = res.stdout.strip().splitlines()
            if not log_lines or not log_lines[0].strip():
                return None

            # First line is latest modified commit
            latest_parts = log_lines[0].split("|")
            last_modified_commit = latest_parts[0]

            # Last line is creation commit
            creation_parts = log_lines[-1].split("|")
            creation_commit = creation_parts[0]

            # Contributors
            contributors = []
            seen = set()
            for line in log_lines:
                parts = line.split("|")
                if len(parts) >= 2:
                    author = parts[1].strip()
                    if author not in seen:
                        seen.add(author)
                        contributors.append(author)

            logger.info("History updated")

            return FileGitMetadata(
                file_path=relative_file_path,
                creation_commit=creation_commit,
                last_modified_commit=last_modified_commit,
                total_revisions=len(log_lines),
                contributors=contributors
            )
        except Exception as e:
            logger.error("Git command failure")
            logger.warning(f"Failed to trace file history for '{relative_file_path}': {e}")
            return None
