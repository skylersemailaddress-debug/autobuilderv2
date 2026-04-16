from specs.loader import NormalizedSpecBundle

from ir.model import AppIR


def compile_specs_to_ir(specs: NormalizedSpecBundle) -> AppIR:
    return AppIR(
        app_identity=specs.app_identity,
        app_type=specs.app_type,
        entities=specs.entities,
        workflows=specs.workflows,
        pages_surfaces=specs.pages,
        api_routes=specs.api_routes,
        runtime_services=specs.runtime_services,
        permissions=specs.permissions,
        deployment_target=specs.deployment_target,
        acceptance_criteria=specs.acceptance_criteria,
    )
