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
    deployment_target: str
    acceptance_criteria: list[str]


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
    "stack.yaml": ("deployment_target",),
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
    deployment_target = str(stack["deployment_target"]).strip()

    if not app_identity:
        raise SpecValidationError("product.yaml name must be non-empty")
    if not app_type:
        raise SpecValidationError("product.yaml app_type must be non-empty")
    if not deployment_target:
        raise SpecValidationError("stack.yaml deployment_target must be non-empty")

    entities = _normalize_dict_list(architecture["entities"], "architecture.entities")
    workflows = _normalize_dict_list(architecture["workflows"], "architecture.workflows")
    api_routes = _normalize_dict_list(architecture["api_routes"], "architecture.api_routes")
    runtime_services = _normalize_dict_list(
        architecture["runtime_services"], "architecture.runtime_services"
    )
    permissions = _normalize_dict_list(architecture["permissions"], "architecture.permissions")
    pages = _normalize_dict_list(ui["pages"], "ui.pages")
    acceptance_criteria = _normalize_str_list(acceptance["criteria"], "acceptance.criteria")

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
        deployment_target=deployment_target,
        acceptance_criteria=acceptance_criteria,
    )
