"""
Tests for Plugin SDK (Prompt 071).
"""
import pytest
from sdk.plugin import BasePlugin, ExtensionPoint, PluginManifest, PluginState


class SamplePlugin(BasePlugin):
    def on_load(self):
        pass

    def on_enable(self):
        pass

    def on_disable(self):
        pass

    def on_unload(self):
        pass

    def _handle_extension(self, extension_point, *args, **kwargs):
        if extension_point == ExtensionPoint.PARSER:
            return "parsed_result"
        return super()._handle_extension(extension_point, *args, **kwargs)


def test_plugin_manifest():
    manifest = PluginManifest(
        plugin_id="sample-plugin",
        name="Sample Plugin",
        version="1.0.0",
        extension_points=[ExtensionPoint.PARSER]
    )
    assert manifest.plugin_id == "sample-plugin"
    assert manifest.version == "1.0.0"
    assert ExtensionPoint.PARSER in manifest.extension_points


def test_plugin_lifecycle_methods():
    manifest = PluginManifest(
        plugin_id="sample-plugin",
        name="Sample Plugin",
        version="1.0.0",
        extension_points=[ExtensionPoint.PARSER]
    )
    plugin = SamplePlugin(manifest)
    assert plugin.state == PluginState.UNLOADED

    result = plugin.execute_extension(ExtensionPoint.PARSER)
    assert result == "parsed_result"

    with pytest.raises(ValueError):
        plugin.execute_extension(ExtensionPoint.RETRIEVER)
