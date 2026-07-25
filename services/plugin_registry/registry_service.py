"""
Plugin Registry Service — Index and metadata for available plugin packages.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ecip_core.common.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PluginPackage:
    plugin_id: str
    name: str
    version: str
    author: str
    description: str
    download_url: str
    checksum: str
    signature: str
    min_sdk_version: str = "1.0.0"
    max_sdk_version: str = "9.9.9"
    dependencies: List[str] = field(default_factory=list)
    is_deprecated: bool = False
    package_data: Optional[bytes] = None


class PluginRegistryService:
    """
    Registry store for available plugins in the marketplace.
    """

    def __init__(self):
        self._packages: Dict[str, Dict[str, PluginPackage]] = {}  # plugin_id -> {version -> PluginPackage}

    def register_package(self, pkg: PluginPackage) -> None:
        if pkg.plugin_id not in self._packages:
            self._packages[pkg.plugin_id] = {}
        self._packages[pkg.plugin_id][pkg.version] = pkg

    def get_latest_package(self, plugin_id: str) -> Optional[PluginPackage]:
        versions = self._packages.get(plugin_id, {})
        if not versions:
            return None
        latest_ver = sorted(versions.keys())[-1]
        pkg = versions[latest_ver]
        if pkg.is_deprecated:
            logger.warning("Deprecated plugin")
        return pkg

    def get_package(self, plugin_id: str, version: str) -> Optional[PluginPackage]:
        pkg = self._packages.get(plugin_id, {}).get(version)
        if pkg and pkg.is_deprecated:
            logger.warning("Deprecated plugin")
        return pkg

    def search(self, query: str) -> List[PluginPackage]:
        results = []
        q = query.lower()
        for pid, versions in self._packages.items():
            for v, pkg in versions.items():
                if q in pkg.name.lower() or q in pkg.description.lower() or q in pid.lower():
                    results.append(pkg)
        return results

    def list_all(self) -> List[PluginPackage]:
        res = []
        for pid, versions in self._packages.items():
            for v, pkg in versions.items():
                res.append(pkg)
        return res
