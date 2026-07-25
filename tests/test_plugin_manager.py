"""
Tests for Plugin Manager (Prompt 071).
"""
import pytest
from sdk.plugin import BasePlugin, ExtensionPoint, PluginManifest, PluginState
from services.plugin_manager.plugin_manager import PluginManager


class DummyPlugin(BasePlugin):
    def __init__(self, manifest, fail_load=False, fail_enable=False):
        super().__init__(manifest)
        self.fail_load = fail_load
        self.fail_enable = fail_enable
        self.loaded = False
        self.enabled = False
        self.disabled = False
        self.unloaded = False

    def on_load(self):
        if self.fail_load:
            raise RuntimeError("Load failure")
        self.loaded = True

    def on_enable(self):
        if self.fail_enable:
            raise RuntimeError("Enable failure")
        self.enabled = True

    def on_disable(self):
        self.disabled = True

    def on_unload(self):
        self.unloaded = True

    def _handle_extension(self, extension_point, *args, **kwargs):
        if extension_point == ExtensionPoint.RETRIEVER:
            return "retrieved"
        return super()._handle_extension(extension_point, *args, **kwargs)


@pytest.fixture
def pm(tmp_path):
    # Create plugin_dir
    p_dir = tmp_path / "plugins"
    p_dir.mkdir()
    (p_dir / "plugin_a.py").write_text("# dummy plugin file")
    return PluginManager(sdk_version="1.0.0", plugin_dir=str(p_dir))


def test_discover_plugins(pm):
    discovered = pm.discover_plugins()
    assert "plugin_a" in discovered


def test_load_and_enable_plugin(pm):
    manifest = PluginManifest(
        plugin_id="dummy",
        name="Dummy",
        version="1.0.0",
        min_sdk_version="1.0.0",
        max_sdk_version="2.0.0",
        extension_points=[ExtensionPoint.RETRIEVER]
    )
    plugin = DummyPlugin(manifest)

    assert pm.load_plugin(plugin) is True
    assert plugin.state == PluginState.LOADED
    assert plugin.loaded is True

    assert pm.enable_plugin("dummy") is True
    assert plugin.state == PluginState.ENABLED
    assert plugin.enabled is True

    # Execute sandboxed
    res = pm.execute_sandboxed("dummy", ExtensionPoint.RETRIEVER)
    assert res == "retrieved"

    # Disable & Unload
    assert pm.disable_plugin("dummy") is True
    assert plugin.state == PluginState.DISABLED
    assert pm.unload_plugin("dummy") is True
    assert "dummy" not in pm.plugins


def test_plugin_version_mismatch(pm):
    manifest = PluginManifest(
        plugin_id="old",
        name="Old",
        version="1.0.0",
        min_sdk_version="2.0.0",
        max_sdk_version="3.0.0"
    )
    plugin = DummyPlugin(manifest)
    assert pm.load_plugin(plugin) is False


def test_sandboxed_execution_failure(pm):
    manifest = PluginManifest(
        plugin_id="bad",
        name="Bad",
        version="1.0.0",
        extension_points=[ExtensionPoint.RETRIEVER]
    )
    plugin = DummyPlugin(manifest)
    pm.load_plugin(plugin)
    pm.enable_plugin("bad")

    # Force error during extension
    plugin._handle_extension = lambda *a, **kw: 1 / 0
    with pytest.raises(RuntimeError):
        pm.execute_sandboxed("bad", ExtensionPoint.RETRIEVER)

    assert plugin.state == PluginState.ERROR


def test_plugin_health_check(pm):
    manifest = PluginManifest(plugin_id="h1", name="H1", version="1.0.0")
    plugin = DummyPlugin(manifest)
    pm.load_plugin(plugin)

    health = pm.health_check("h1")
    assert health["healthy"] is True
    assert health["state"] == PluginState.LOADED

    health_missing = pm.health_check("missing")
    assert health_missing["healthy"] is False
