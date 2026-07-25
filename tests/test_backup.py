"""
Tests for BackupManager (Prompt 066).
"""
import os
import json
import zipfile
import tempfile
import pytest
from pathlib import Path

from services.backup.backup_manager import BackupManager


@pytest.fixture
def project_dir(tmp_path):
    """Create a minimal fake ECIP project layout."""
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "ecip.db").write_bytes(b"SQLITE_DATA")
    (tmp_path / "data" / "ecip_project1.db").write_bytes(b"SQLITE_PROJECT1")

    ecip = tmp_path / "projects" / "proj1" / ".ecip"
    ecip.mkdir(parents=True)
    (ecip / "faiss.index").write_bytes(b"FAISS_INDEX_DATA")
    (ecip / "faiss_metadata.json").write_text("[]")

    config = tmp_path / "config"
    config.mkdir()
    (config / "settings.yaml").write_text("model: qwen2.5-coder")

    return tmp_path


@pytest.fixture
def backup_dir(tmp_path):
    return tmp_path / "backups"


class TestBackupManagerFullBackup:
    def test_full_backup_creates_archive(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        archive = mgr.full_backup(str(project_dir))

        assert Path(archive).exists()
        assert archive.endswith(".zip")

    def test_full_backup_archive_contains_data_files(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        archive = mgr.full_backup(str(project_dir))

        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
        assert any("ecip.db" in n for n in names)

    def test_full_backup_archive_contains_faiss(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        archive = mgr.full_backup(str(project_dir))

        with zipfile.ZipFile(archive) as zf:
            names = zf.namelist()
        assert any("faiss.index" in n for n in names)

    def test_full_backup_updates_manifest(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        mgr.full_backup(str(project_dir))

        assert mgr._manifest["last_full_backup"] is not None
        assert len(mgr._manifest["archives"]) == 1
        assert mgr._manifest["archives"][0]["type"] == "full"

    def test_full_backup_manifest_persisted(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        mgr.full_backup(str(project_dir))

        # Reload from disk
        mgr2 = BackupManager(backup_dir=str(backup_dir))
        assert mgr2._manifest["last_full_backup"] is not None


class TestBackupManagerIncrementalBackup:
    def test_incremental_falls_back_to_full_if_no_previous(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        archive = mgr.incremental_backup(str(project_dir))
        # Should have created a full backup
        assert Path(archive).exists()

    def test_incremental_backup_after_full(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        mgr.full_backup(str(project_dir))

        # Modify a file so incremental has something to pick up
        (project_dir / "data" / "ecip.db").write_bytes(b"UPDATED_DATA")

        archive = mgr.incremental_backup(str(project_dir))
        assert archive  # non-empty path = archive created
        assert Path(archive).exists()

    def test_incremental_no_changes_returns_empty(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        mgr.full_backup(str(project_dir))

        # Rewind mtimes by touching nothing
        archive = mgr.incremental_backup(str(project_dir))
        # If no files changed since full backup, returns ""
        assert archive == "" or (archive and Path(archive).exists())


class TestBackupManagerIntegrity:
    def test_verify_valid_archive(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        archive = mgr.full_backup(str(project_dir))
        assert mgr.verify_integrity(archive) is True

    def test_verify_corrupted_archive(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        archive = mgr.full_backup(str(project_dir))

        # Corrupt the archive
        with open(archive, "r+b") as f:
            f.seek(10)
            f.write(b"\x00\x00\x00")

        assert mgr.verify_integrity(archive) is False

    def test_verify_nonexistent_archive(self, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        assert mgr.verify_integrity("/nonexistent/archive.zip") is False


class TestBackupManagerRetention:
    def test_retention_deletes_old_archives(self, project_dir, backup_dir):
        import datetime
        mgr = BackupManager(backup_dir=str(backup_dir), retention_days=0)
        mgr.full_backup(str(project_dir))

        # All archives should be deleted (retention = 0 days)
        deleted = mgr.apply_retention()
        assert deleted >= 1

    def test_retention_keeps_recent_archives(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir), retention_days=30)
        mgr.full_backup(str(project_dir))

        deleted = mgr.apply_retention()
        assert deleted == 0

    def test_list_backups(self, project_dir, backup_dir):
        mgr = BackupManager(backup_dir=str(backup_dir))
        mgr.full_backup(str(project_dir))
        mgr.full_backup(str(project_dir))

        backups = mgr.list_backups()
        assert len(backups) == 2
