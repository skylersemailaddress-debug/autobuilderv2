from pathlib import Path

from ir.compiler import compile_specs_to_ir
from specs.loader import load_spec_bundle


def test_compile_specs_to_ir_maps_canonical_sections():
    project_root = Path(__file__).resolve().parents[1]
    bundle = load_spec_bundle(project_root / "specs")
    app_ir = compile_specs_to_ir(bundle)

    assert app_ir.app_identity == "Autobuilder Demo App"
    assert app_ir.app_type == "saas_web_app"
    assert app_ir.archetype["name"] == "saas_web_app"
    assert isinstance(app_ir.entities, list)
    assert isinstance(app_ir.workflows, list)
    assert isinstance(app_ir.pages_surfaces, list)
    assert isinstance(app_ir.api_routes, list)
    assert isinstance(app_ir.runtime_services, list)
    assert isinstance(app_ir.permissions, list)
    assert app_ir.stack_selection["frontend"] == "react_next"
    assert app_ir.stack_entries["backend"]["name"] == "fastapi"
    assert app_ir.deployment_target == "container"
    assert len(app_ir.acceptance_criteria) >= 1
