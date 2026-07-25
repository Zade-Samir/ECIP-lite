"""
Tests for Marketplace & Registry (Prompt 072).
"""
import pytest
from services.marketplace.marketplace_service import MarketplaceService
from services.plugin_registry.registry_service import PluginPackage, PluginRegistryService


@pytest.fixture
def registry():
    reg = PluginRegistryService()
    pkg1 = PluginPackage(
        plugin_id="plugin-a",
        name="Plugin A",
        version="1.0.0",
        author="Dev1",
        description="First plugin",
        download_url="http://example.com/a.zip",
        checksum="hash1",
        signature="sig1",
    )
    pkg2 = PluginPackage(
        plugin_id="plugin-a",
        name="Plugin A",
        version="1.1.0",
        author="Dev1",
        description="First plugin updated",
        download_url="http://example.com/a2.zip",
        checksum="hash2",
        signature="sig2",
    )
    pkg_dep = PluginPackage(
        plugin_id="plugin-dep",
        name="Plugin Dep",
        version="1.0.0",
        author="Dev2",
        description="Dependency plugin",
        download_url="http://example.com/dep.zip",
        checksum="hashdep",
        signature="sigdep",
        dependencies=["plugin-a"]
    )
    reg.register_package(pkg1)
    reg.register_package(pkg2)
    reg.register_package(pkg_dep)
    return reg


@pytest.fixture
def marketplace(registry):
    return MarketplaceService(registry)


def test_browse_and_search(marketplace):
    all_pkgs = marketplace.browse()
    assert len(all_pkgs) == 3

    results = marketplace.search("First")
    assert len(results) == 2


def test_get_plugin_latest_and_version(marketplace):
    latest = marketplace.get_plugin("plugin-a")
    assert latest.version == "1.1.0"

    v1 = marketplace.get_plugin("plugin-a", "1.0.0")
    assert v1.version == "1.0.0"


def test_check_updates(marketplace):
    installed = {"plugin-a": "1.0.0"}
    updates = marketplace.check_updates(installed)
    assert len(updates) == 1
    assert updates[0].version == "1.1.0"


def test_resolve_dependencies(marketplace):
    dep_pkg = marketplace.get_plugin("plugin-dep")
    resolved = marketplace.resolve_dependencies(dep_pkg)
    ids = [p.plugin_id for p in resolved]
    assert "plugin-a" in ids
    assert "plugin-dep" in ids
