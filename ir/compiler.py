from archetypes.catalog import resolve_archetype
from specs.loader import NormalizedSpecBundle
from stack_registry.registry import resolve_stack_bundle

from ir.model import AppIR


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
    )
