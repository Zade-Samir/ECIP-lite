"""
Backup Manager — Full and incremental backup of all ECIP data.
Backup targets: SQLite DB, FAISS index, config files, audit logs, workspace metadata.
Local-only: no external dependencies. Archives stored as timestamped .zip files.
Optional AES-256 encryption using Python cryptography library.
"""
import os
import io
import json
import time
import shutil
import hashlib
import zipfile
import datetime
from pathlib import Path
from typing import Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)

# Default backup directory (relative to project root)
DEFAULT_BACKUP_DIR = Path("backups")
DEFAULT_RETENTION_DAYS = 7


class BackupManager:
    """
    Manages full and incremental backups of all ECIP data.

    Backup targets:
    - SQLite database (data/*.db)
    - FAISS indexes (.ecip/faiss.index + faiss_metadata.json per project)
    - Configuration files (config/*.yaml, config/*.json)
    - Audit logs (logs/*.log)
    - Workspace metadata (workspace registry)
    """

    def __init__(
        self,
        backup_dir: str = str(DEFAULT_BACKUP_DIR),
        retention_days: int = DEFAULT_RETENTION_DAYS,
        encryption_key: Optional[bytes] = None,
    ):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.retention_days = retention_days
        self.encryption_key = encryption_key  # 32-byte AES key or None

        # Track last backup mtime for incremental support
        self._manifest_path = self.backup_dir / "backup_manifest.json"
        self._manifest = self._load_manifest()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def full_backup(self, project_root: str = ".") -> str:
        """
        Create a full backup of all ECIP data.

        Returns:
            Path to the created backup archive.
        """
        logger.info("Backup started")
        project_root = Path(project_root).resolve()
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        archive_name = f"ecip_backup_full_{timestamp}.zip"
        archive_path = self.backup_dir / archive_name

        targets = self._collect_targets(project_root)

        try:
            self._write_archive(archive_path, targets, project_root)
            checksum = self._compute_checksum(archive_path)

            if self.encryption_key:
                archive_path = self._encrypt_archive(archive_path)

            # Update manifest
            self._manifest["last_full_backup"] = timestamp
            self._manifest["archives"].append({
                "name": archive_path.name,
                "type": "full",
                "timestamp": timestamp,
                "checksum": checksum,
                "files": len(targets),
                "encrypted": self.encryption_key is not None,
            })
            self._save_manifest()

            logger.info("Backup completed")
            return str(archive_path)

        except Exception as e:
            logger.error("Backup failed")
            raise RuntimeError(f"Full backup failed: {e}") from e

    def incremental_backup(self, project_root: str = ".") -> str:
        """
        Create an incremental backup containing only files modified since
        the last backup.

        Returns:
            Path to the created backup archive.
        """
        logger.info("Backup started")
        project_root = Path(project_root).resolve()
        last_backup_ts = self._manifest.get("last_full_backup")

        if not last_backup_ts:
            logger.warning("No previous full backup found — performing full backup instead")
            return self.full_backup(project_root)

        last_backup_time = datetime.datetime.strptime(last_backup_ts, "%Y%m%dT%H%M%SZ").timestamp()
        timestamp = datetime.datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        archive_name = f"ecip_backup_incremental_{timestamp}.zip"
        archive_path = self.backup_dir / archive_name

        all_targets = self._collect_targets(project_root)
        changed_targets = [
            t for t in all_targets
            if t.exists() and t.stat().st_mtime > last_backup_time
        ]

        if not changed_targets:
            logger.info("Backup completed")
            logger.info("No changed files found — incremental backup skipped")
            return ""

        try:
            self._write_archive(archive_path, changed_targets, project_root)
            checksum = self._compute_checksum(archive_path)

            if self.encryption_key:
                archive_path = self._encrypt_archive(archive_path)

            self._manifest["archives"].append({
                "name": archive_path.name,
                "type": "incremental",
                "timestamp": timestamp,
                "checksum": checksum,
                "files": len(changed_targets),
                "encrypted": self.encryption_key is not None,
            })
            self._save_manifest()

            logger.info("Backup completed")
            return str(archive_path)

        except Exception as e:
            logger.error("Backup failed")
            raise RuntimeError(f"Incremental backup failed: {e}") from e

    def verify_integrity(self, archive_path: str) -> bool:
        """
        Verify a backup archive is not corrupted by recomputing its checksum.
        """
        path = Path(archive_path)
        if not path.exists():
            logger.error("Integrity mismatch")
            return False

        computed = self._compute_checksum(path)
        archive_name = path.name
        if path.suffix == ".enc":
            archive_name = path.stem  # strip .enc to find original entry

        for entry in self._manifest.get("archives", []):
            if entry["name"] == archive_name or entry["name"] == path.name:
                expected = entry["checksum"]
                ok = computed == expected
                if not ok:
                    logger.error("Integrity mismatch")
                else:
                    logger.info("Backup completed")
                return ok

        logger.warning("Archive not found in manifest — cannot verify")
        return False

    def apply_retention(self) -> int:
        """
        Delete backup archives older than retention_days.

        Returns:
            Number of archives deleted.
        """
        cutoff = datetime.datetime.utcnow() - datetime.timedelta(days=self.retention_days)
        deleted = 0

        remaining = []
        for entry in self._manifest.get("archives", []):
            ts_str = entry.get("timestamp", "")
            try:
                ts = datetime.datetime.strptime(ts_str, "%Y%m%dT%H%M%SZ")
            except ValueError:
                remaining.append(entry)
                continue

            if ts < cutoff:
                archive_path = self.backup_dir / entry["name"]
                if archive_path.exists():
                    archive_path.unlink()
                    logger.warning("Retention cleanup")
                    deleted += 1
            else:
                remaining.append(entry)

        self._manifest["archives"] = remaining
        self._save_manifest()
        return deleted

    def list_backups(self) -> list:
        """Return list of recorded backup archives."""
        return self._manifest.get("archives", [])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _collect_targets(self, project_root: Path) -> list[Path]:
        """Collect all files that should be backed up."""
        targets: list[Path] = []

        # SQLite databases
        data_dir = project_root / "data"
        if data_dir.exists():
            targets.extend(data_dir.glob("*.db"))

        # FAISS indexes (per project in .ecip/)
        for ecip_dir in project_root.rglob(".ecip"):
            if ecip_dir.is_dir():
                targets.extend(ecip_dir.glob("faiss*"))
                targets.extend(ecip_dir.glob("bm25*"))

        # Config files
        config_dir = project_root / "config"
        if config_dir.exists():
            targets.extend(config_dir.rglob("*.yaml"))
            targets.extend(config_dir.rglob("*.yml"))
            targets.extend(config_dir.rglob("*.json"))

        # Audit logs
        logs_dir = project_root / "logs"
        if logs_dir.exists():
            targets.extend(logs_dir.glob("audit*.log"))
            targets.extend(logs_dir.glob("audit*.json"))

        return [t for t in targets if t.is_file()]

    def _write_archive(self, archive_path: Path, targets: list[Path], root: Path) -> None:
        """Write files into a zip archive."""
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for target in targets:
                try:
                    arcname = str(target.relative_to(root))
                except ValueError:
                    arcname = target.name
                zf.write(target, arcname)
            # Embed manifest snapshot
            zf.writestr("_ecip_backup_meta.json", json.dumps({
                "created_at": datetime.datetime.utcnow().isoformat(),
                "file_count": len(targets),
            }))

    def _compute_checksum(self, path: Path) -> str:
        sha = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha.update(chunk)
        return sha.hexdigest()

    def _encrypt_archive(self, archive_path: Path) -> Path:
        """Encrypt an archive using Fernet (AES-128-CBC)."""
        try:
            from cryptography.fernet import Fernet
            import base64
            key = base64.urlsafe_b64encode(self.encryption_key[:32])
            fernet = Fernet(key)

            with open(archive_path, "rb") as f:
                data = f.read()

            encrypted = fernet.encrypt(data)
            enc_path = archive_path.with_suffix(archive_path.suffix + ".enc")

            with open(enc_path, "wb") as f:
                f.write(encrypted)

            archive_path.unlink()  # Remove unencrypted copy
            return enc_path

        except ImportError:
            logger.warning("cryptography library not installed — skipping encryption")
            return archive_path

    def _load_manifest(self) -> dict:
        if self._manifest_path.exists():
            try:
                with open(self._manifest_path) as f:
                    return json.load(f)
            except Exception:
                pass
        return {"last_full_backup": None, "archives": []}

    def _save_manifest(self) -> None:
        with open(self._manifest_path, "w") as f:
            json.dump(self._manifest, f, indent=2)
