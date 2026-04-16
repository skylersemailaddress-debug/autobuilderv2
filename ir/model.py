from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class AppIR:
    app_identity: str
    app_type: str
    archetype: dict[str, Any]
    entities: list[dict[str, Any]]
    workflows: list[dict[str, Any]]
    pages_surfaces: list[dict[str, Any]]
    api_routes: list[dict[str, Any]]
    runtime_services: list[dict[str, Any]]
    permissions: list[dict[str, Any]]
    stack_selection: dict[str, str]
    stack_entries: dict[str, dict[str, Any]]
    deployment_target: str
    acceptance_criteria: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
