from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field

class PluginType(Enum):
    GENERATOR = "GENERATOR"
    VALIDATOR = "VALIDATOR"
    EXPORTER = "EXPORTER"
    AI_PROVIDER = "AI_PROVIDER"

@dataclass
class PluginMetadata:
    name: str
    version: str
    author: str
    description: str
    plugin_type: PluginType
    compatible_app_versions: List[str] = field(default_factory=lambda: ["1.0.0"])
    dependencies: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "version": self.version,
            "author": self.author,
            "description": self.description,
            "plugin_type": self.plugin_type.value,
            "compatible_app_versions": self.compatible_app_versions,
            "dependencies": self.dependencies
        }

class BasePlugin(ABC):
    """Abstract base class for third-party extensions."""

    def __init__(self, metadata: PluginMetadata):
        self.metadata = metadata

    @abstractmethod
    def initialize(self, app_context: Dict[str, Any]) -> bool:
        """Initialize plugin resources."""
        pass

    @abstractmethod
    def execute(self, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute plugin logic."""
        pass

    def is_compatible(self, app_version: str = "1.0.0") -> bool:
        """Check if plugin version is compatible with application version."""
        if "*" in self.metadata.compatible_app_versions:
            return True
        return app_version in self.metadata.compatible_app_versions
