"""
Enterprise Plugin SDK — Extension interfaces and BasePlugin model.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ExtensionPoint(str, Enum):
    PARSER = "parser"
    RETRIEVER = "retriever"
    EMBEDDING_PROVIDER = "embedding_provider"
    LLM_PROVIDER = "llm_provider"
    AUTH_PROVIDER = "auth_provider"
    NOTIFICATION_PROVIDER = "notification_provider"
    EXPORT_PROVIDER = "export_provider"
    MONITORING_PROVIDER = "monitoring_provider"


class PluginState(str, Enum):
    UNLOADED = "unloaded"
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"


@dataclass
class PluginManifest:
    plugin_id: str
    name: str
    version: str
    min_sdk_version: str = "1.0.0"
    max_sdk_version: str = "9.9.9"
    extension_points: List[ExtensionPoint] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    optional_dependencies: List[str] = field(default_factory=list)
    author: str = "Unknown"
    description: str = ""


class BasePlugin(ABC):
    """
    Abstract base class for all ECIP Enterprise Plugins.
    """

    def __init__(self, manifest: PluginManifest):
        self.manifest = manifest
        self.state = PluginState.UNLOADED
        self.config: Dict[str, Any] = {}

    @abstractmethod
    def on_load(self) -> None:
        """Callback invoked when plugin is loaded into memory."""
        pass

    @abstractmethod
    def on_enable(self) -> None:
        """Callback invoked when plugin is activated."""
        pass

    @abstractmethod
    def on_disable(self) -> None:
        """Callback invoked when plugin is deactivated."""
        pass

    @abstractmethod
    def on_unload(self) -> None:
        """Callback invoked when plugin is removed."""
        pass

    def execute_extension(self, extension_point: ExtensionPoint, *args, **kwargs) -> Any:
        """Default handler for extension point requests."""
        if extension_point not in self.manifest.extension_points:
            raise ValueError(f"Plugin {self.manifest.plugin_id} does not support extension point {extension_point}")
        return self._handle_extension(extension_point, *args, **kwargs)

    def _handle_extension(self, extension_point: ExtensionPoint, *args, **kwargs) -> Any:
        """Custom override point for plugin logic."""
        return None
