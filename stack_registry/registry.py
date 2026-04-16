from __future__ import annotations

from dataclasses import asdict, dataclass


class StackRegistryResolutionError(ValueError):
    """Raised when a stack selection cannot be resolved."""


@dataclass(frozen=True)
class StackDefinition:
    name: str
    category: str
    support_tier: str
    required_files_modules: list[str]
    validation_expectations: list[str]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


STACK_REGISTRY: dict[str, dict[str, StackDefinition]] = {
    "frontend": {
        "react_next": StackDefinition(
            name="react_next",
            category="frontend",
            support_tier="first_class",
            required_files_modules=["app/", "next.config.js", "package.json"],
            validation_expectations=["page_routes", "ui_render", "frontend_build"],
        ),
        "flutter_mobile": StackDefinition(
            name="flutter_mobile",
            category="frontend",
            support_tier="first_class",
            required_files_modules=["pubspec.yaml", "lib/main.dart", "lib/navigation.dart", "lib/services/api_client.dart"],
            validation_expectations=["mobile_structure", "mobile_markers"],
        ),
        "godot_game": StackDefinition(
            name="godot_game",
            category="frontend",
            support_tier="first_class",
            required_files_modules=["project.godot", "scenes/Main.tscn", "scripts/main.gd", "scripts/player.gd"],
            validation_expectations=["game_structure", "game_markers"],
        ),
        "future_frontend_placeholder": StackDefinition(
            name="future_frontend_placeholder",
            category="frontend",
            support_tier="future",
            required_files_modules=[],
            validation_expectations=[],
        ),
    },
    "backend": {
        "fastapi": StackDefinition(
            name="fastapi",
            category="backend",
            support_tier="first_class",
            required_files_modules=["api/", "app/main.py", "requirements.txt"],
            validation_expectations=["route_contracts", "startup_checks", "backend_tests"],
        ),
        "future_backend_placeholder": StackDefinition(
            name="future_backend_placeholder",
            category="backend",
            support_tier="future",
            required_files_modules=[],
            validation_expectations=[],
        ),
    },
    "database": {
        "postgres": StackDefinition(
            name="postgres",
            category="database",
            support_tier="first_class",
            required_files_modules=["db/", "db/schema.sql", "docker-compose.yml"],
            validation_expectations=["schema_bootstrap", "connection_health", "migration_readiness"],
        ),
        "future_database_placeholder": StackDefinition(
            name="future_database_placeholder",
            category="database",
            support_tier="future",
            required_files_modules=[],
            validation_expectations=[],
        ),
    },
    "deployment": {
        "docker_compose": StackDefinition(
            name="docker_compose",
            category="deployment",
            support_tier="first_class",
            required_files_modules=["docker-compose.yml", ".env.example"],
            validation_expectations=["container_startup", "service_wiring", "local_boot"],
        ),
        "future_deployment_placeholder": StackDefinition(
            name="future_deployment_placeholder",
            category="deployment",
            support_tier="future",
            required_files_modules=[],
            validation_expectations=[],
        ),
    },
}


def resolve_stack_entry(category: str, name: str) -> StackDefinition:
    category_registry = STACK_REGISTRY.get(category)
    if category_registry is None:
        supported_categories = ", ".join(sorted(STACK_REGISTRY))
        raise StackRegistryResolutionError(
            f"Unsupported stack category '{category}'. Supported categories: {supported_categories}"
        )

    try:
        return category_registry[name]
    except KeyError as exc:
        supported_entries = ", ".join(sorted(category_registry))
        raise StackRegistryResolutionError(
            f"Unsupported {category} stack '{name}'. Supported values: {supported_entries}"
        ) from exc


def resolve_stack_bundle(selection: dict[str, str]) -> dict[str, StackDefinition]:
    required_categories = ("frontend", "backend", "database", "deployment")
    missing = [category for category in required_categories if category not in selection]
    if missing:
        raise StackRegistryResolutionError(
            "Missing stack selections for categories: " + ", ".join(missing)
        )

    return {
        category: resolve_stack_entry(category, selection[category])
        for category in required_categories
    }