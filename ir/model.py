from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
    application_domains: list[str] = field(default_factory=list)
    assets: dict[str, list[str]] = field(default_factory=dict)
    runtime_targets: list[str] = field(default_factory=list)
    environment_requirements: list[str] = field(default_factory=list)
    deployment_expectations: list[str] = field(default_factory=list)
    navigation_flows: list[dict[str, Any]] = field(default_factory=list)
    state_machines: list[dict[str, Any]] = field(default_factory=list)
    background_jobs: list[dict[str, Any]] = field(default_factory=list)
    workers: list[dict[str, Any]] = field(default_factory=list)
    realtime_channels: list[dict[str, Any]] = field(default_factory=list)
    realtime_events: list[dict[str, Any]] = field(default_factory=list)
    user_sessions: list[dict[str, Any]] = field(default_factory=list)
    auth_roles: list[dict[str, Any]] = field(default_factory=list)
    scenes: list[dict[str, Any]] = field(default_factory=list)
    game_entities: list[dict[str, Any]] = field(default_factory=list)
    input_actions: list[dict[str, Any]] = field(default_factory=list)
    update_loops: list[dict[str, Any]] = field(default_factory=list)
    asset_references: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
