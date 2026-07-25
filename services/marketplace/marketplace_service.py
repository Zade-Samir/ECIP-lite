"""
Marketplace Service — Browse, search, resolve dependencies, and update plugins.
"""
from typing import Dict, List, Optional

from ecip_core.common.logger import get_logger
from services.plugin_registry.registry_service import PluginPackage, PluginRegistryService

logger = get_logger(__name__)


class MarketplaceService:
    """
    Marketplace front service for discovering plugins and checking updates.
    """

    def __init__(self, registry: PluginRegistryService):
        self.registry = registry

    def browse(self) -> List[PluginPackage]:
        return self.registry.list_all()

    def search(self, query: str) -> List[PluginPackage]:
        return self.registry.search(query)

    def get_plugin(self, plugin_id: str, version: Optional[str] = None) -> Optional[PluginPackage]:
        if version:
            return self.registry.get_package(plugin_id, version)
        return self.registry.get_latest_package(plugin_id)

    def check_updates(self, installed: Dict[str, str]) -> List[PluginPackage]:
        """
        installed: dict of plugin_id -> current_version
        Returns list of available updates.
        """
        updates = []
        for pid, curr_ver in installed.items():
            latest = self.registry.get_latest_package(pid)
            if latest and latest.version != curr_ver:
                updates.append(latest)
        return updates

    def resolve_dependencies(self, pkg: PluginPackage) -> List[PluginPackage]:
        """
        Resolves transitive dependencies for a plugin package.
        """
        resolved = []
        visited = set()

        def _resolve(current: PluginPackage):
            if current.plugin_id in visited:
                logger.warning("Version conflict")
                return
            visited.add(current.plugin_id)

            for dep_id in current.dependencies:
                dep_pkg = self.registry.get_latest_package(dep_id)
                if not dep_pkg:
                    logger.warning("Version conflict")
                    raise ValueError(f"Missing dependency: {dep_id}")
                _resolve(dep_pkg)

            resolved.append(current)

        _resolve(pkg)
        return resolved
