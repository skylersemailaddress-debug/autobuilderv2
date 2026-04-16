from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path

from platform_plugins.contracts import PluginBase


class PluginResolutionError(ValueError):
    """Raised when compatible plugins cannot be resolved for a requested lane."""


@dataclass(frozen=True)
class ResolvedPluginSet:
    archetype: PluginBase
    stack: PluginBase
    generation: PluginBase
    validation: PluginBase
    repair: PluginBase
    packaging: PluginBase


def _supports(plugin: PluginBase, app_type: str, stack_selection: dict[str, str]) -> bool:
    metadata = plugin.metadata
    if metadata.plugin_type != "archetype" and metadata.supported_archetypes:
        if app_type not in metadata.supported_archetypes:
            return False
    for category, expected_values in metadata.supported_stacks.items():
        chosen = stack_selection.get(category)
        if chosen is None or chosen not in expected_values:
            return False
    return True


class PluginRegistry:
    def __init__(self) -> None:
        self._plugins_by_type: dict[str, dict[str, PluginBase]] = {}
        self._loaded = False

    def register(self, plugin: PluginBase) -> None:
        plugin_type = plugin.metadata.plugin_type
        by_id = self._plugins_by_type.setdefault(plugin_type, {})
        by_id[plugin.metadata.plugin_id] = plugin

    def ensure_loaded(self) -> None:
        if self._loaded:
            return
        package_name = "platform_plugins.plugins"
        package = importlib.import_module(package_name)
        package_path = Path(package.__file__).resolve().parent
        for module_info in sorted(pkgutil.iter_modules([str(package_path)]), key=lambda item: item.name):
            importlib.import_module(f"{package_name}.{module_info.name}")
        self._loaded = True

    def list_plugins(self, plugin_type: str | None = None) -> list[dict[str, object]]:
        self.ensure_loaded()
        items: list[PluginBase] = []
        if plugin_type is None:
            for by_id in self._plugins_by_type.values():
                items.extend(by_id.values())
        else:
            items.extend(self._plugins_by_type.get(plugin_type, {}).values())

        return [
            {
                "plugin_id": plugin.metadata.plugin_id,
                "plugin_type": plugin.metadata.plugin_type,
                "lane_id": plugin.metadata.lane_id,
                "capabilities": list(plugin.metadata.capabilities),
                "supported_archetypes": list(plugin.metadata.supported_archetypes),
                "supported_stacks": dict(plugin.metadata.supported_stacks),
                "priority": plugin.metadata.priority,
            }
            for plugin in sorted(items, key=lambda entry: (entry.metadata.plugin_type, entry.metadata.priority, entry.metadata.plugin_id))
        ]

    def _resolve_one(self, plugin_type: str, app_type: str, stack_selection: dict[str, str]) -> PluginBase:
        self.ensure_loaded()
        candidates = [
            plugin
            for plugin in self._plugins_by_type.get(plugin_type, {}).values()
            if _supports(plugin, app_type, stack_selection)
        ]
        if not candidates:
            available = ", ".join(sorted(self._plugins_by_type.get(plugin_type, {}).keys())) or "none"
            raise PluginResolutionError(
                "Unsupported commercial lane stack selection. "
                f"No compatible {plugin_type} plugin for app_type '{app_type}' and stack {stack_selection}. "
                f"Available: {available}"
            )
        return sorted(candidates, key=lambda entry: (entry.metadata.priority, entry.metadata.plugin_id))[0]

    def resolve_plugins(self, app_type: str, stack_selection: dict[str, str]) -> ResolvedPluginSet:
        archetype_plugin = self._resolve_one("archetype", app_type, stack_selection)
        # Validate app_type explicitly through the archetype plugin so unknown app_type retains clear errors.
        archetype_plugin.resolve_archetype(app_type)

        resolved = ResolvedPluginSet(
            archetype=archetype_plugin,
            stack=self._resolve_one("stack", app_type, stack_selection),
            generation=self._resolve_one("generation", app_type, stack_selection),
            validation=self._resolve_one("validation", app_type, stack_selection),
            repair=self._resolve_one("repair", app_type, stack_selection),
            packaging=self._resolve_one("packaging", app_type, stack_selection),
        )

        lane_ids = {
            resolved.archetype.metadata.lane_id,
            resolved.stack.metadata.lane_id,
            resolved.generation.metadata.lane_id,
            resolved.validation.metadata.lane_id,
            resolved.repair.metadata.lane_id,
            resolved.packaging.metadata.lane_id,
        }
        if len(lane_ids) != 1:
            raise PluginResolutionError(
                "Resolved plugins are not lane-compatible: " + ", ".join(sorted(lane_ids))
            )

        return resolved


GLOBAL_PLUGIN_REGISTRY = PluginRegistry()


def register_plugin(plugin: PluginBase) -> PluginBase:
    GLOBAL_PLUGIN_REGISTRY.register(plugin)
    return plugin


def get_plugin_registry() -> PluginRegistry:
    return GLOBAL_PLUGIN_REGISTRY
