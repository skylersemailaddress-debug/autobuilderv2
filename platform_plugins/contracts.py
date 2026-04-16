from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol


PluginType = str


@dataclass(frozen=True)
class PluginMetadata:
    plugin_id: str
    plugin_type: PluginType
    lane_id: str
    capabilities: list[str]
    supported_archetypes: list[str]
    supported_stacks: dict[str, list[str]]
    priority: int = 100


class PluginBase(Protocol):
    metadata: PluginMetadata


class ArchetypePlugin(PluginBase, Protocol):
    def resolve_archetype(self, app_type: str) -> object:
        ...


class StackPlugin(PluginBase, Protocol):
    def resolve_stack_bundle(self, selection: dict[str, str]) -> dict[str, object]:
        ...


class GenerationPlugin(PluginBase, Protocol):
    def generate_templates(self, ir: Any) -> list[Any]:
        ...

    def validation_plan(self) -> list[str]:
        ...


class ValidationPlugin(PluginBase, Protocol):
    def validate_generated_app(self, target_repo: str) -> dict[str, object]:
        ...


class RepairPlugin(PluginBase, Protocol):
    def repair_generated_app(
        self,
        target_repo: str,
        validation_report: dict[str, object],
        expected_templates: list[Any] | None,
        max_repairs: int,
    ) -> dict[str, object]:
        ...


class PackagingPlugin(PluginBase, Protocol):
    def emit_proof_artifacts(
        self,
        target_repo: str,
        build_status: str,
        validation_report: dict[str, object],
        determinism: dict[str, object],
        repair_report: dict[str, object],
    ) -> dict[str, object]:
        ...
