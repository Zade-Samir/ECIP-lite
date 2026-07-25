"""
Plugin Manager — Dynamic discovery, loading, lifecycle, and sandboxing of SDK plugins.
"""
import importlib
import inspect
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

from ecip_core.common.logger import get_logger
from sdk.plugin import BasePlugin, ExtensionPoint, PluginManifest, PluginState

logger = get_logger(__name__)


def parse_semver(v: str) -> tuple:
    parts = v.split(".")
    res = []
    for p in parts:
        try:
            res.append(int(p))
        except ValueError:
            res.append(0)
    return tuple(res)


class PluginManager:
    """
    Manages plugin discovery, lifecycle, version compatibility, and sandboxed execution.
    """

    def __init__(self, sdk_version: str = "1.0.0", plugin_dir: Optional[str] = None):
        self.sdk_version = sdk_version
        self.plugin_dir = Path(plugin_dir) if plugin_dir else Path("plugins")
        self.plugins: Dict[str, BasePlugin] = {}

    def discover_plugins(self) -> List[str]:
        """Scan plugin directory for valid plugin classes/files."""
        discovered = []
        if not self.plugin_dir.exists():
            return discovered

        for file_path in self.plugin_dir.glob("*.py"):
            if file_path.name.startswith("__"):
                continue
            discovered.append(file_path.stem)
            logger.info("Plugin discovered")

        return discovered

    def validate_plugin(self, plugin: BasePlugin) -> bool:
        manifest = plugin.manifest

        # Check SDK version compatibility
        sdk_v = parse_semver(self.sdk_version)
        min_v = parse_semver(manifest.min_sdk_version)
        max_v = parse_semver(manifest.max_sdk_version)

        if sdk_v < min_v or sdk_v > max_v:
            logger.warning("Version mismatch")
            logger.error("Validation failed")
            return False

        # Check required dependencies
        for dep in manifest.dependencies:
            if dep not in self.plugins or self.plugins[dep].state not in (PluginState.LOADED, PluginState.ENABLED):
                logger.error("Validation failed")
                return False

        # Check optional dependencies
        for opt_dep in manifest.optional_dependencies:
            if opt_dep not in self.plugins:
                logger.warning("Optional dependency missing")

        return True

    def load_plugin(self, plugin: BasePlugin) -> bool:
        if plugin.manifest.plugin_id in self.plugins:
            logger.error("Plugin failed to load")
            return False

        if not self.validate_plugin(plugin):
            logger.error("Plugin failed to load")
            return False

        try:
            plugin.on_load()
            plugin.state = PluginState.LOADED
            self.plugins[plugin.manifest.plugin_id] = plugin
            logger.info("Plugin loaded")
            return True
        except Exception as e:
            logger.error("Plugin failed to load")
            plugin.state = PluginState.ERROR
            return False

    def enable_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self.plugins:
            return False
        plugin = self.plugins[plugin_id]
        if plugin.state not in (PluginState.LOADED, PluginState.DISABLED):
            return False

        try:
            plugin.on_enable()
            plugin.state = PluginState.ENABLED
            logger.info("Plugin initialized")
            return True
        except Exception:
            plugin.state = PluginState.ERROR
            logger.error("Sandbox violation")
            return False

    def disable_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self.plugins:
            return False
        plugin = self.plugins[plugin_id]
        if plugin.state != PluginState.ENABLED:
            return False

        try:
            plugin.on_disable()
            plugin.state = PluginState.DISABLED
            return True
        except Exception:
            plugin.state = PluginState.ERROR
            return False

    def unload_plugin(self, plugin_id: str) -> bool:
        if plugin_id not in self.plugins:
            return False
        plugin = self.plugins[plugin_id]
        try:
            if plugin.state == PluginState.ENABLED:
                plugin.on_disable()
            plugin.on_unload()
            plugin.state = PluginState.UNLOADED
            del self.plugins[plugin_id]
            return True
        except Exception:
            plugin.state = PluginState.ERROR
            del self.plugins[plugin_id]
            return False

    def execute_sandboxed(self, plugin_id: str, extension_point: ExtensionPoint, *args, **kwargs) -> Any:
        """Executes a plugin method wrapped in sandbox error isolation."""
        if plugin_id not in self.plugins:
            logger.error("Sandbox violation")
            raise RuntimeError(f"Plugin {plugin_id} not loaded")

        plugin = self.plugins[plugin_id]
        if plugin.state != PluginState.ENABLED:
            logger.error("Sandbox violation")
            raise RuntimeError(f"Plugin {plugin_id} is not enabled")

        try:
            return plugin.execute_extension(extension_point, *args, **kwargs)
        except Exception as e:
            logger.error("Sandbox violation")
            plugin.state = PluginState.ERROR
            raise RuntimeError(f"Sandbox execution failed for plugin {plugin_id}: {e}") from e

    def get_plugin(self, plugin_id: str) -> Optional[BasePlugin]:
        return self.plugins.get(plugin_id)

    def health_check(self, plugin_id: str) -> dict:
        if plugin_id not in self.plugins:
            return {"status": "not_found", "healthy": False}
        plugin = self.plugins[plugin_id]
        return {
            "plugin_id": plugin_id,
            "state": plugin.state.value,
            "healthy": plugin.state in (PluginState.LOADED, PluginState.ENABLED),
        }
