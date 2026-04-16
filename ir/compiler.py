from platform_plugins.registry import get_plugin_registry
from specs.loader import NormalizedSpecBundle

from ir.model import AppIR


def compile_specs_to_ir(specs: NormalizedSpecBundle) -> AppIR:
    plugins = get_plugin_registry().resolve_plugins(specs.app_type, specs.stack_selection)
    archetype = plugins.archetype.resolve_archetype(specs.app_type)
    stack_entries = plugins.stack.resolve_stack_bundle(specs.stack_selection)

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
        application_domains=specs.application_domains,
        navigation_flows=specs.navigation_flows,
        state_machines=specs.state_machines,
        background_jobs=specs.background_jobs,
        workers=specs.workers,
        realtime_channels=specs.realtime_channels,
        realtime_events=specs.realtime_events,
        user_sessions=specs.user_sessions,
        auth_roles=specs.auth_roles,
        scenes=specs.scenes,
        game_entities=specs.game_entities,
        input_actions=specs.input_actions,
        update_loops=specs.update_loops,
        asset_references=specs.asset_references,
        assets=specs.assets,
        runtime_targets=specs.runtime_targets,
        environment_requirements=specs.environment_requirements,
        deployment_expectations=specs.deployment_expectations,
    )
