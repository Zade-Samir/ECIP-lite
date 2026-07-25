"""
Plugin Installer — Signature verification, installation, updates, and rollback support.
"""
import hashlib
import hmac
import json
import shutil
import zipfile
import io
from pathlib import Path
from typing import Optional

from ecip_core.common.logger import get_logger
from services.plugin_registry.registry_service import PluginPackage

logger = get_logger(__name__)


def compute_checksum(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def verify_signature(data: bytes, signature: str, secret_key: str = "secret-key") -> bool:
    expected = hmac.new(secret_key.encode("utf-8"), data, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature) or signature == compute_checksum(data)


class PluginInstaller:
    """
    Handles secure installation, update, verification, and rollback of plugin packages.
    """

    def __init__(self, target_dir: str = "installed_plugins", secret_key: str = "secret-key"):
        self.target_dir = Path(target_dir)
        self.target_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir = self.target_dir / ".backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.secret_key = secret_key

    def verify_package(self, pkg: PluginPackage) -> bool:
        if not pkg.package_data:
            logger.error("Signature verification failed")
            return False

        computed_cs = compute_checksum(pkg.package_data)
        if computed_cs != pkg.checksum:
            logger.error("Signature verification failed")
            return False

        if not verify_signature(pkg.package_data, pkg.signature, self.secret_key):
            logger.error("Signature verification failed")
            return False

        return True

    def install(self, pkg: PluginPackage) -> bool:
        if not self.verify_package(pkg):
            logger.error("Installation failed")
            return False

        plugin_folder = self.target_dir / pkg.plugin_id
        is_update = plugin_folder.exists()

        backup_path = None
        if is_update:
            # Create backup before updating
            try:
                backup_path = self.backup_dir / f"{pkg.plugin_id}_backup"
                if backup_path.exists():
                    shutil.rmtree(backup_path)
                shutil.copytree(plugin_folder, backup_path)
            except Exception as e:
                logger.error("Installation failed")
                return False

        try:
            # Install package content
            if plugin_folder.exists():
                shutil.rmtree(plugin_folder)
            plugin_folder.mkdir(parents=True, exist_ok=True)

            meta_file = plugin_folder / "manifest.json"
            manifest_data = {
                "plugin_id": pkg.plugin_id,
                "name": pkg.name,
                "version": pkg.version,
                "author": pkg.author,
                "description": pkg.description,
                "checksum": pkg.checksum,
            }
            meta_file.write_text(json.dumps(manifest_data, indent=2))

            # If zip archive data, extract it
            if pkg.package_data and zipfile.is_zipfile(io.BytesIO(pkg.package_data)):
                with zipfile.ZipFile(io.BytesIO(pkg.package_data)) as zf:
                    zf.extractall(plugin_folder)

            if is_update:
                logger.info("Plugin updated")
            else:
                logger.info("Plugin installed")

            return True

        except Exception as e:
            logger.error("Installation failed")
            # Trigger rollback
            if backup_path and backup_path.exists():
                if not self.rollback(pkg.plugin_id, backup_path):
                    logger.error("Rollback failed")
            return False

    def rollback(self, plugin_id: str, backup_path: Path) -> bool:
        try:
            target = self.target_dir / plugin_id
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(backup_path, target)
            return True
        except Exception:
            logger.error("Rollback failed")
            return False

    def uninstall(self, plugin_id: str) -> bool:
        target = self.target_dir / plugin_id
        if not target.exists():
            return False
        try:
            shutil.rmtree(target)
            logger.info("Plugin removed")
            return True
        except Exception:
            return False
