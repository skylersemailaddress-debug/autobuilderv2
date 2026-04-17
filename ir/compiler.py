from archetypes.catalog import resolve_archetype
from specs.loader import NormalizedSpecBundle
from stack_registry.registry import resolve_stack_bundle

from ir.model import AppIR


def _canonical_application_domains(app_type: str, declared_domains: list[str]) -> list[str]:
    if declared_domains:
        return list(declared_domains)
    if app_type == "mobile_app":
        return ["mobile_apps"]
    if app_type == "game_app":
        return ["games"]
    if app_type == "realtime_system":
        return ["realtime_systems"]
    if app_type == "enterprise_agent_system":
        return ["enterprise_systems"]
    return ["web_apps"]


def _canonical_assets(assets: dict[str, list[str]]) -> dict[str, list[str]]:
    canonical = {
        "images": [],
        "audio": [],
        "ui": [],
        "config": [],
    }
    for key, values in assets.items():
        if isinstance(values, list):
            canonical[key] = list(values)
    return canonical


def compile_specs_to_ir(specs: NormalizedSpecBundle) -> AppIR:
    archetype = resolve_archetype(specs.app_type)
    stack_entries = resolve_stack_bundle(specs.stack_selection)

    return AppIR(
        app_identity=specs.app_identity,
        app_type=specs.app_type,
        archetype=archetype.to_dict(),
        entities=specs.entities,
        workflows=specs.workflows,
        pages_surfaces=specs.pages,
        api_routes=specs.api_routes,
        runtime_services=specs.runtime_services,
        permissions=specs.permissions,
        stack_selection=specs.stack_selection,
        stack_entries={category: entry.to_dict() for category, entry in stack_entries.items()},
        deployment_target=specs.deployment_target,
        acceptance_criteria=specs.acceptance_criteria,
        application_domains=_canonical_application_domains(specs.app_type, list(specs.application_domains)),
        assets=_canonical_assets(dict(specs.assets)),
        runtime_targets=list(specs.runtime_targets),
        environment_requirements=list(specs.environment_requirements),
        deployment_expectations=list(specs.deployment_expectations),
        navigation_flows=list(specs.navigation_flows),
        state_machines=list(specs.state_machines),
        background_jobs=list(specs.background_jobs),
        workers=list(specs.workers),
        realtime_channels=list(specs.realtime_channels),
        realtime_events=list(specs.realtime_events),
        user_sessions=list(specs.user_sessions),
        auth_roles=list(specs.auth_roles),
        scenes=list(specs.scenes),
        game_entities=list(specs.game_entities),
        input_actions=list(specs.input_actions),
        update_loops=list(specs.update_loops),
        asset_references=list(specs.asset_references),
    )
