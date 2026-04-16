from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


class SpecValidationError(ValueError):
    """Raised when a required spec file or section is missing."""


@dataclass(frozen=True)
class NormalizedSpecBundle:
    spec_root: str
    app_identity: str
    app_type: str
    product: dict[str, Any]
    architecture: dict[str, Any]
    ui: dict[str, Any]
    acceptance: dict[str, Any]
    stack: dict[str, Any]
    entities: list[dict[str, Any]]
    workflows: list[dict[str, Any]]
    pages: list[dict[str, Any]]
    api_routes: list[dict[str, Any]]
    runtime_services: list[dict[str, Any]]
    permissions: list[dict[str, Any]]
    stack_selection: dict[str, str]
    deployment_target: str
    acceptance_criteria: list[str]
    application_domains: list[str] = ()  # type: ignore[assignment]
    assets: dict[str, list[str]] = ()  # type: ignore[assignment]
    runtime_targets: list[str] = ()  # type: ignore[assignment]
    environment_requirements: list[str] = ()  # type: ignore[assignment]
    deployment_expectations: list[str] = ()  # type: ignore[assignment]
    navigation_flows: list[dict[str, Any]] = ()  # type: ignore[assignment]
    state_machines: list[dict[str, Any]] = ()  # type: ignore[assignment]
    background_jobs: list[dict[str, Any]] = ()  # type: ignore[assignment]
    workers: list[dict[str, Any]] = ()  # type: ignore[assignment]
    realtime_channels: list[dict[str, Any]] = ()  # type: ignore[assignment]
    realtime_events: list[dict[str, Any]] = ()  # type: ignore[assignment]
    user_sessions: list[dict[str, Any]] = ()  # type: ignore[assignment]
    auth_roles: list[dict[str, Any]] = ()  # type: ignore[assignment]
    scenes: list[dict[str, Any]] = ()  # type: ignore[assignment]
    game_entities: list[dict[str, Any]] = ()  # type: ignore[assignment]
    input_actions: list[dict[str, Any]] = ()  # type: ignore[assignment]
    update_loops: list[dict[str, Any]] = ()  # type: ignore[assignment]
    asset_references: list[dict[str, Any]] = ()  # type: ignore[assignment]


REQUIRED_FILES = (
    "product.yaml",
    "architecture.yaml",
    "ui.yaml",
    "acceptance.yaml",
    "stack.yaml",
)


REQUIRED_SECTION_KEYS: dict[str, tuple[str, ...]] = {
    "product.yaml": ("name", "app_type"),
    "architecture.yaml": ("entities", "workflows", "api_routes", "runtime_services", "permissions"),
    "ui.yaml": ("pages",),
    "acceptance.yaml": ("criteria",),
    "stack.yaml": ("frontend", "backend", "database", "deployment", "deployment_target"),
}


def _load_yaml_mapping(path: Path) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")

    try:
        import yaml  # type: ignore

        loaded = yaml.safe_load(text)
    except ModuleNotFoundError:
        # Deterministic fallback that supports JSON-compatible YAML.
        try:
            loaded = json.loads(text)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive branch
            raise SpecValidationError(
                f"Cannot parse {path.name}: install PyYAML or provide JSON-compatible YAML"
            ) from exc

    if loaded is None:
        return {}

    if not isinstance(loaded, dict):
        raise SpecValidationError(f"{path.name} must contain a mapping/object at the top level")

    return loaded


def _require_keys(file_name: str, payload: dict[str, Any]) -> None:
    missing = [key for key in REQUIRED_SECTION_KEYS[file_name] if key not in payload]
    if missing:
        missing_text = ", ".join(sorted(missing))
        raise SpecValidationError(f"{file_name} is missing required keys: {missing_text}")


def _normalize_dict_list(value: Any, field_name: str) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise SpecValidationError(f"{field_name} must be a list")
    normalized: list[dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, dict):
            raise SpecValidationError(f"{field_name}[{idx}] must be an object")
        normalized.append(item)
    return normalized


def _normalize_str_list(value: Any, field_name: str) -> list[str]:
    if not isinstance(value, list):
        raise SpecValidationError(f"{field_name} must be a list")
    normalized: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise SpecValidationError(f"{field_name}[{idx}] must be a non-empty string")
        normalized.append(item.strip())
    return normalized


def _normalize_non_empty_str(value: Any, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SpecValidationError(f"{field_name} must be a non-empty string")
    return value.strip()


def load_spec_bundle(spec_root: str | Path) -> NormalizedSpecBundle:
    root = Path(spec_root).resolve()
    missing_files = [name for name in REQUIRED_FILES if not (root / name).is_file()]
    if missing_files:
        raise SpecValidationError(
            "Missing required spec files: " + ", ".join(sorted(missing_files))
        )

    loaded: dict[str, dict[str, Any]] = {}
    for file_name in REQUIRED_FILES:
        payload = _load_yaml_mapping(root / file_name)
        _require_keys(file_name, payload)
        loaded[file_name] = payload

    product = loaded["product.yaml"]
    architecture = loaded["architecture.yaml"]
    ui = loaded["ui.yaml"]
    acceptance = loaded["acceptance.yaml"]
    stack = loaded["stack.yaml"]

    app_identity = str(product["name"]).strip()
    app_type = str(product["app_type"]).strip()
    deployment_target = _normalize_non_empty_str(stack["deployment_target"], "stack.deployment_target")
    stack_selection = {
        "frontend": _normalize_non_empty_str(stack["frontend"], "stack.frontend"),
        "backend": _normalize_non_empty_str(stack["backend"], "stack.backend"),
        "database": _normalize_non_empty_str(stack["database"], "stack.database"),
        "deployment": _normalize_non_empty_str(stack["deployment"], "stack.deployment"),
    }

    if not app_identity:
        raise SpecValidationError("product.yaml name must be non-empty")
    if not app_type:
        raise SpecValidationError("product.yaml app_type must be non-empty")

    entities = _normalize_dict_list(architecture["entities"], "architecture.entities")
    workflows = _normalize_dict_list(architecture["workflows"], "architecture.workflows")
    api_routes = _normalize_dict_list(architecture["api_routes"], "architecture.api_routes")
    runtime_services = _normalize_dict_list(
        architecture["runtime_services"], "architecture.runtime_services"
    )
    permissions = _normalize_dict_list(architecture["permissions"], "architecture.permissions")
    pages = _normalize_dict_list(ui["pages"], "ui.pages")
    acceptance_criteria = _normalize_str_list(acceptance["criteria"], "acceptance.criteria")

    # Optional extended fields
    application_domains: list[str] = list(product.get("application_domains") or [])
    assets: dict[str, list[str]] = dict(product.get("assets") or {})
    stack_obj = stack
    runtime_targets: list[str] = sorted(stack_obj.get("runtime_targets") or [])
    environment_requirements: list[str] = sorted(stack_obj.get("environment_requirements") or [])
    deployment_expectations: list[str] = sorted(stack_obj.get("deployment_expectations") or [])

    def _opt_dict_list(source: dict[str, Any], key: str) -> list[dict[str, Any]]:
        val = source.get(key)
        if not val:
            return []
        return [item for item in val if isinstance(item, dict)]

    navigation_flows = sorted(_opt_dict_list(ui, "navigation_flows"), key=lambda x: list(x.values())[0] if x else "")
    state_machines = sorted(_opt_dict_list(architecture, "state_machines"), key=lambda x: x.get("name", ""))
    background_jobs = sorted(_opt_dict_list(architecture, "background_jobs"), key=lambda x: x.get("name", ""))
    workers = sorted(_opt_dict_list(architecture, "workers"), key=lambda x: x.get("name", ""))
    realtime_channels = sorted(_opt_dict_list(architecture, "realtime_channels"), key=lambda x: x.get("channel", ""))
    realtime_events = sorted(_opt_dict_list(architecture, "realtime_events"), key=lambda x: x.get("event", ""))
    user_sessions = sorted(_opt_dict_list(architecture, "user_sessions"), key=lambda x: x.get("name", ""))
    auth_roles = sorted(_opt_dict_list(architecture, "auth_roles"), key=lambda x: x.get("name", ""))
    scenes = sorted(_opt_dict_list(architecture, "scenes"), key=lambda x: x.get("name", ""))
    game_entities = sorted(_opt_dict_list(architecture, "game_entities"), key=lambda x: x.get("name", ""))
    input_actions = sorted(_opt_dict_list(architecture, "input_actions"), key=lambda x: x.get("name", ""))
    update_loops = sorted(_opt_dict_list(architecture, "update_loops"), key=lambda x: x.get("name", ""))
    asset_references = sorted(_opt_dict_list(architecture, "asset_references"), key=lambda x: x.get("asset", ""))

    return NormalizedSpecBundle(
        spec_root=str(root),
        app_identity=app_identity,
        app_type=app_type,
        product=product,
        architecture=architecture,
        ui=ui,
        acceptance=acceptance,
        stack=stack,
        entities=entities,
        workflows=workflows,
        pages=pages,
        api_routes=api_routes,
        runtime_services=runtime_services,
        permissions=permissions,
        stack_selection=stack_selection,
        deployment_target=deployment_target,
        acceptance_criteria=acceptance_criteria,
        application_domains=application_domains,
        assets=assets,
        runtime_targets=runtime_targets,
        environment_requirements=environment_requirements,
        deployment_expectations=deployment_expectations,
        navigation_flows=navigation_flows,
        state_machines=state_machines,
        background_jobs=background_jobs,
        workers=workers,
        realtime_channels=realtime_channels,
        realtime_events=realtime_events,
        user_sessions=user_sessions,
        auth_roles=auth_roles,
        scenes=scenes,
        game_entities=game_entities,
        input_actions=input_actions,
        update_loops=update_loops,
        asset_references=asset_references,
    )
