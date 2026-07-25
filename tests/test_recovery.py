"""
Tests for RecoveryManager (Prompt 066).
"""
import io
import json
import zipfile
import pytest
from pathlib import Path

from services.backup.backup_manager import BackupManager
from services.backup.recovery_manager import RecoveryManager


@pytest.fixture
def project_dir(tmp_path):
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "ecip.db").write_bytes(b"SQLITE_ORIGINAL")
    ecip = tmp_path / ".ecip"
    ecip.mkdir()
    (ecip / "faiss.index").write_bytes(b"FAISS_ORIGINAL")
    return tmp_path


@pytest.fixture
def backup_archive(project_dir, tmp_path):
    backup_dir = tmp_path / "backups"
    mgr = BackupManager(backup_dir=str(backup_dir))
    archive_path = mgr.full_backup(str(project_dir))
    return archive_path


class TestRecoveryManagerRestore:
    def test_restore_recreates_files(self, backup_archive, tmp_path):
        restore_root = tmp_path / "restored"
        rec = RecoveryManager()
        result = rec.restore(backup_archive, restore_root=str(restore_root))

        assert len(result["restored_files"]) > 0
        assert len(result["errors"]) == 0

    def test_restore_dry_run_does_not_write(self, backup_archive, tmp_path):
        restore_root = tmp_path / "dry_run_dest"
        rec = RecoveryManager()
        result = rec.restore(backup_archive, restore_root=str(restore_root), dry_run=True)

        assert result["dry_run"] is True
        assert len(result["restored_files"]) > 0
        # Nothing should have been written
        assert not restore_root.exists() or not any(restore_root.iterdir())

    def test_restore_missing_archive_raises(self, tmp_path):
        rec = RecoveryManager()
        with pytest.raises(FileNotFoundError):
            rec.restore("/nonexistent/backup.zip", restore_root=str(tmp_path))

    def test_restore_corrupted_archive_raises(self, tmp_path):
        bad_archive = tmp_path / "bad.zip"
        bad_archive.write_bytes(b"not a zip file at all")

        rec = RecoveryManager()
        with pytest.raises(ValueError):
            rec.restore(str(bad_archive), restore_root=str(tmp_path))


class TestRecoveryManagerSingleFile:
    def test_restore_single_file(self, backup_archive, tmp_path):
        rec = RecoveryManager()
        contents = rec.list_archive_contents(backup_archive)
        assert len(contents) > 0

        first_file = contents[0]
        dest = tmp_path / "single_restore.bin"
        success = rec.restore_file(backup_archive, first_file, str(dest))
        assert success is True
        assert dest.exists()

    def test_restore_missing_member_returns_false(self, backup_archive, tmp_path):
        rec = RecoveryManager()
        dest = tmp_path / "out.bin"
        result = rec.restore_file(backup_archive, "nonexistent/file.db", str(dest))
        assert result is False


class TestRecoveryManagerValidation:
    def test_validate_good_archive(self, backup_archive):
        rec = RecoveryManager()
        result = rec.validate(backup_archive)
        assert result["valid"] is True
        assert result["file_count"] > 0

    def test_validate_bad_archive(self, tmp_path):
        bad = tmp_path / "bad.zip"
        bad.write_bytes(b"garbage data")
        rec = RecoveryManager()
        result = rec.validate(str(bad))
        assert result["valid"] is False

    def test_validate_missing_archive(self):
        rec = RecoveryManager()
        result = rec.validate("/no/such/file.zip")
        assert result["valid"] is False

    def test_list_archive_contents(self, backup_archive):
        rec = RecoveryManager()
        files = rec.list_archive_contents(backup_archive)
        assert isinstance(files, list)
        assert len(files) > 0
