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
    application_domains: list[str]
    navigation_flows: list[dict[str, Any]]
    state_machines: list[dict[str, Any]]
    background_jobs: list[dict[str, Any]]
    workers: list[dict[str, Any]]
    realtime_channels: list[dict[str, Any]]
    realtime_events: list[dict[str, Any]]
    user_sessions: list[dict[str, Any]]
    auth_roles: list[dict[str, Any]]
    scenes: list[dict[str, Any]]
    game_entities: list[dict[str, Any]]
    input_actions: list[dict[str, Any]]
    update_loops: list[dict[str, Any]]
    asset_references: list[dict[str, Any]]
    assets: dict[str, list[str]]
    runtime_targets: list[str]
    environment_requirements: list[str]
    deployment_expectations: list[str]


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


DOMAIN_BY_APP_TYPE: dict[str, list[str]] = {
    "internal_tool": ["web_apps"],
    "workspace_app": ["web_apps"],
    "saas_web_app": ["web_apps"],
    "api_service": ["backend_services"],
    "workflow_system": ["backend_services"],
    "copilot_chat_app": ["web_apps", "realtime_systems"],
    "mobile_app": ["mobile_apps"],
    "game_app": ["games"],
    "realtime_system": ["realtime_systems"],
    "enterprise_agent_system": ["enterprise_systems"],
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


def _normalize_optional_dict_list(payload: dict[str, Any], key: str, field_name: str) -> list[dict[str, Any]]:
    if key not in payload:
        return []
    return _normalize_dict_list(payload[key], field_name)


def _normalize_optional_str_list(payload: dict[str, Any], key: str, field_name: str) -> list[str]:
    if key not in payload:
        return []
    return _normalize_str_list(payload[key], field_name)


def _stable_sort_dict_items(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    key_candidates = ("id", "name", "route", "channel", "event", "asset", "type")

    def _sort_key(item: dict[str, Any]) -> tuple[str, str]:
        for candidate in key_candidates:
            value = item.get(candidate)
            if isinstance(value, str) and value:
                return candidate, value
        return "", json.dumps(item, sort_keys=True)

    return sorted(items, key=_sort_key)


def _normalize_assets(product: dict[str, Any], ui: dict[str, Any]) -> dict[str, list[str]]:
    raw_assets = product.get("assets", ui.get("assets", {}))
    if raw_assets is None:
        raw_assets = {}
    if not isinstance(raw_assets, dict):
        raise SpecValidationError("assets must be an object mapping asset categories to string lists")

    categories = ("images", "audio", "ui", "config")
    normalized: dict[str, list[str]] = {}
    for category in categories:
        value = raw_assets.get(category, [])
        if value == []:
            normalized[category] = []
            continue
        normalized[category] = _normalize_str_list(value, f"assets.{category}")
    return normalized


def _infer_application_domains(app_type: str, product: dict[str, Any]) -> list[str]:
    if "application_domains" in product:
        return sorted(set(_normalize_str_list(product["application_domains"], "product.application_domains")))
    return list(DOMAIN_BY_APP_TYPE.get(app_type, ["web_apps"]))


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

    navigation_flows = _stable_sort_dict_items(
        _normalize_optional_dict_list(ui, "navigation_flows", "ui.navigation_flows")
    )
    state_machines = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "state_machines", "architecture.state_machines")
    )
    background_jobs = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "background_jobs", "architecture.background_jobs")
    )
    workers = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "workers", "architecture.workers")
    )
    realtime_channels = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "realtime_channels", "architecture.realtime_channels")
    )
    realtime_events = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "realtime_events", "architecture.realtime_events")
    )
    user_sessions = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "user_sessions", "architecture.user_sessions")
    )
    auth_roles = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "auth_roles", "architecture.auth_roles")
    )
    scenes = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "scenes", "architecture.scenes")
    )
    game_entities = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "game_entities", "architecture.game_entities")
    )
    input_actions = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "input_actions", "architecture.input_actions")
    )
    update_loops = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "update_loops", "architecture.update_loops")
    )
    asset_references = _stable_sort_dict_items(
        _normalize_optional_dict_list(architecture, "asset_references", "architecture.asset_references")
    )

    runtime_targets = sorted(
        set(_normalize_optional_str_list(stack, "runtime_targets", "stack.runtime_targets"))
    )
    environment_requirements = sorted(
        set(
            _normalize_optional_str_list(
                stack, "environment_requirements", "stack.environment_requirements"
            )
        )
    )
    deployment_expectations = sorted(
        set(
            _normalize_optional_str_list(
                stack, "deployment_expectations", "stack.deployment_expectations"
            )
        )
    )

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
        application_domains=_infer_application_domains(app_type, product),
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
        assets=_normalize_assets(product, ui),
        runtime_targets=runtime_targets,
        environment_requirements=environment_requirements,
        deployment_expectations=deployment_expectations,
    )
