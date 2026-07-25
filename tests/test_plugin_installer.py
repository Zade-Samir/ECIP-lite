"""
Tests for Plugin Installer (Prompt 072).
"""
import pytest
from pathlib import Path
from sdk.installer.plugin_installer import PluginInstaller, compute_checksum, verify_signature
from services.plugin_registry.registry_service import PluginPackage


@pytest.fixture
def installer(tmp_path):
    target = tmp_path / "installed"
    return PluginInstaller(target_dir=str(target), secret_key="test-key")


def test_signature_verification():
    data = b"sample_plugin_data"
    checksum = compute_checksum(data)
    sig = verify_signature(data, checksum, "test-key")
    assert sig is True


def test_install_and_update_plugin(installer):
    data = b"plugin_content_v1"
    cs = compute_checksum(data)

    pkg_v1 = PluginPackage(
        plugin_id="test-plugin",
        name="Test Plugin",
        version="1.0.0",
        author="Tester",
        description="Test",
        download_url="",
        checksum=cs,
        signature=cs,
        package_data=data,
    )

    # Fresh installation
    assert installer.install(pkg_v1) is True
    installed_manifest = installer.target_dir / "test-plugin" / "manifest.json"
    assert installed_manifest.exists()

    # Update to v2
    data_v2 = b"plugin_content_v2"
    cs_v2 = compute_checksum(data_v2)
    pkg_v2 = PluginPackage(
        plugin_id="test-plugin",
        name="Test Plugin",
        version="2.0.0",
        author="Tester",
        description="Test Updated",
        download_url="",
        checksum=cs_v2,
        signature=cs_v2,
        package_data=data_v2,
    )

    assert installer.install(pkg_v2) is True
    assert "2.0.0" in installed_manifest.read_text()


def test_install_invalid_signature_fails(installer):
    data = b"corrupted_data"
    pkg = PluginPackage(
        plugin_id="bad-plugin",
        name="Bad Plugin",
        version="1.0.0",
        author="Hacker",
        description="Bad",
        download_url="",
        checksum="invalid_checksum",
        signature="invalid_signature",
        package_data=data,
    )
    assert installer.install(pkg) is False


def test_uninstall_plugin(installer):
    data = b"plugin_data"
    cs = compute_checksum(data)
    pkg = PluginPackage(
        plugin_id="remove-me",
        name="Remove Me",
        version="1.0.0",
        author="Tester",
        description="Test",
        download_url="",
        checksum=cs,
        signature=cs,
        package_data=data,
    )
    installer.install(pkg)
    assert installer.uninstall("remove-me") is True
    assert not (installer.target_dir / "remove-me").exists()
