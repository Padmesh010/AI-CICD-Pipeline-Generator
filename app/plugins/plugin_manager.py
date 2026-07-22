import os
import json
import importlib.util
from typing import Dict, List, Any, Optional
from app.core.logger import logger
from app.core.exceptions import PluginError, ErrorHandler
from app.plugins.base_plugin import BasePlugin, PluginMetadata, PluginType

class PluginManager:
    """Auto-discovery manager for third-party extensions."""

    def __init__(self, plugins_dir: Optional[str] = None):
        if not plugins_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            plugins_dir = os.path.join(base_dir, "plugins")

        self.plugins_dir = plugins_dir
        os.makedirs(self.plugins_dir, exist_ok=True)
        self.registered_plugins: Dict[str, BasePlugin] = {}
        self.discover_plugins()

    def discover_plugins(self) -> None:
        """Scan plugins/ directory for plugin manifests and python modules."""
        if not os.path.exists(self.plugins_dir):
            return

        for item in os.listdir(self.plugins_dir):
            item_path = os.path.join(self.plugins_dir, item)
            if os.path.isdir(item_path):
                manifest_path = os.path.join(item_path, "plugin.json")
                py_path = os.path.join(item_path, "plugin.py")
                
                if os.path.exists(manifest_path) and os.path.exists(py_path):
                    self.load_plugin(item_path, manifest_path, py_path)

    def load_plugin(self, plugin_dir: str, manifest_path: str, py_path: str) -> bool:
        """Dynamically load and register a single plugin module."""
        try:
            with open(manifest_path, "r", encoding="utf-8") as mf:
                data = json.load(mf)

            metadata = PluginMetadata(
                name=data.get("name", os.path.basename(plugin_dir)),
                version=data.get("version", "1.0.0"),
                author=data.get("author", "Unknown"),
                description=data.get("description", ""),
                plugin_type=PluginType(data.get("plugin_type", "GENERATOR")),
                compatible_app_versions=data.get("compatible_app_versions", ["1.0.0"]),
                dependencies=data.get("dependencies", [])
            )

            # Load module dynamically
            spec = importlib.util.spec_from_file_location(f"plugin_{metadata.name}", py_path)
            if not spec or not spec.loader:
                return False

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Look for class inheriting BasePlugin
            for attr_name in dir(module):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and issubclass(attr, BasePlugin) and attr is not BasePlugin:
                    plugin_instance = attr(metadata)
                    if plugin_instance.is_compatible():
                        plugin_instance.initialize({})
                        self.registered_plugins[metadata.name] = plugin_instance
                        logger.info(f"Successfully loaded plugin '{metadata.name}' (v{metadata.version}).")
                        return True
                    else:
                        logger.warning(f"Plugin '{metadata.name}' skipped: Incompatible version.")
                        return False
            return False

        except Exception as e:
            ErrorHandler.handle_exception(
                PluginError(f"Failed to load plugin from '{plugin_dir}': {e}", e),
                show_dialog=False
            )
            return False

    def get_plugins_by_type(self, plugin_type: PluginType) -> List[BasePlugin]:
        """Retrieve plugins belonging to a specific type."""
        return [p for p in self.registered_plugins.values() if p.metadata.plugin_type == plugin_type]

    def execute_plugin(self, plugin_name: str, action: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action on a specific registered plugin."""
        if plugin_name not in self.registered_plugins:
            raise PluginError(f"Plugin '{plugin_name}' is not registered.")
        
        plugin = self.registered_plugins[plugin_name]
        try:
            return plugin.execute(action, payload)
        except Exception as e:
            ErrorHandler.handle_exception(
                PluginError(f"Execution error in plugin '{plugin_name}': {e}", e),
                show_dialog=False
            )
            raise e

    def list_plugins(self) -> Dict[str, Dict[str, Any]]:
        """List registered plugins with status metadata."""
        return {
            name: {
                "metadata": p.metadata,
                "active": True
            } for name, p in self.registered_plugins.items()
        }

    def disable_plugin(self, name: str) -> None:
        """Deactivate a plugin (stub wrapper)."""
        logger.info(f"Plugin '{name}' deactivated.")

    def enable_plugin(self, name: str) -> None:
        """Activate a plugin (stub wrapper)."""
        logger.info(f"Plugin '{name}' activated.")

# Global plugin manager instance
plugin_manager = PluginManager()
