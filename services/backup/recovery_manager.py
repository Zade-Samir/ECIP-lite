"""
Recovery Manager — Restore ECIP data from backup archives.
Supports dry-run validation, integrity checking before restore, and partial restores.
"""
import io
import json
import shutil
import hashlib
import zipfile
from pathlib import Path
from typing import Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


class RecoveryManager:
    """
    Restores ECIP data from backup archives created by BackupManager.

    Supports:
    - Full restore from a backup archive
    - Dry-run mode (validate without overwriting)
    - Integrity verification before restore
    - Partial restore (single file from archive)
    """

    def __init__(self, encryption_key: Optional[bytes] = None):
        self.encryption_key = encryption_key

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def restore(
        self,
        archive_path: str,
        restore_root: str = ".",
        dry_run: bool = False,
    ) -> dict:
        """
        Restore all files from a backup archive.

        Args:
            archive_path: Path to the .zip or .zip.enc archive.
            restore_root: Root directory to restore files into.
            dry_run: If True, validates and lists files without writing.

        Returns:
            Dict with restore summary.
        """
        logger.info("Restore completed" if not dry_run else "Restore completed")
        path = Path(archive_path)
        restore_root = Path(restore_root).resolve()

        if not path.exists():
            logger.error("Restore failed")
            raise FileNotFoundError(f"Archive not found: {archive_path}")

        # Decrypt if needed
        archive_data = self._read_archive(path)

        # Validate archive integrity
        if not self._validate_zip(archive_data):
            logger.error("Integrity mismatch")
            raise ValueError("Archive appears corrupted — restore aborted")

        result = {
            "archive": str(path),
            "dry_run": dry_run,
            "restored_files": [],
            "skipped_files": [],
            "errors": [],
        }

        try:
            with zipfile.ZipFile(io.BytesIO(archive_data), "r") as zf:
                for member in zf.namelist():
                    if member == "_ecip_backup_meta.json":
                        continue  # Internal metadata, skip

                    dest = restore_root / member

                    if dry_run:
                        result["restored_files"].append(str(dest))
                        continue

                    try:
                        dest.parent.mkdir(parents=True, exist_ok=True)
                        with zf.open(member) as src, open(dest, "wb") as dst:
                            shutil.copyfileobj(src, dst)
                        result["restored_files"].append(str(dest))
                    except Exception as e:
                        logger.error("Restore failed")
                        result["errors"].append({"file": member, "error": str(e)})

        except zipfile.BadZipFile as e:
            logger.error("Restore failed")
            raise ValueError(f"Bad zip archive: {e}") from e

        if not dry_run:
            logger.info("Restore completed")

        return result

    def restore_file(
        self,
        archive_path: str,
        member_name: str,
        dest_path: str,
    ) -> bool:
        """
        Restore a single file from a backup archive.

        Args:
            archive_path: Path to backup archive.
            member_name: Name of the file within the archive (relative path).
            dest_path: Destination path to write the file.

        Returns:
            True on success, False on failure.
        """
        path = Path(archive_path)
        archive_data = self._read_archive(path)

        try:
            with zipfile.ZipFile(io.BytesIO(archive_data), "r") as zf:
                if member_name not in zf.namelist():
                    logger.error("Restore failed")
                    return False

                dest = Path(dest_path)
                dest.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(member_name) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                logger.info("Restore completed")
                return True

        except Exception as e:
            logger.error("Restore failed")
            return False

    def validate(self, archive_path: str) -> dict:
        """
        Validate archive integrity without restoring.

        Returns:
            Dict with validation result and file list.
        """
        path = Path(archive_path)
        if not path.exists():
            return {"valid": False, "error": "Archive not found", "files": []}

        try:
            archive_data = self._read_archive(path)
            valid = self._validate_zip(archive_data)

            files = []
            if valid:
                with zipfile.ZipFile(io.BytesIO(archive_data), "r") as zf:
                    files = [m for m in zf.namelist() if m != "_ecip_backup_meta.json"]

            return {"valid": valid, "files": files, "file_count": len(files)}

        except Exception as e:
            logger.error("Integrity mismatch")
            return {"valid": False, "error": str(e), "files": []}

    def list_archive_contents(self, archive_path: str) -> list[str]:
        """List all files in a backup archive."""
        result = self.validate(archive_path)
        return result.get("files", [])

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _read_archive(self, path: Path) -> bytes:
        """Read archive bytes, decrypting if needed."""
        with open(path, "rb") as f:
            data = f.read()

        if path.suffix == ".enc" and self.encryption_key:
            data = self._decrypt(data)
        elif path.suffix == ".enc" and not self.encryption_key:
            raise ValueError("Archive is encrypted but no encryption_key provided")

        return data

    def _decrypt(self, data: bytes) -> bytes:
        """Decrypt Fernet-encrypted bytes."""
        try:
            from cryptography.fernet import Fernet
            import base64
            key = base64.urlsafe_b64encode(self.encryption_key[:32])
            fernet = Fernet(key)
            return fernet.decrypt(data)
        except ImportError:
            raise RuntimeError("cryptography library not installed — cannot decrypt archive")

    def _validate_zip(self, data: bytes) -> bool:
        """Check if bytes constitute a valid ZIP archive."""
        try:
            with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
                result = zf.testzip()  # Returns None if OK
                return result is None
        except zipfile.BadZipFile:
            return False
