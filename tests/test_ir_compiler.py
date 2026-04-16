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
    assert app_ir.application_domains == ["web_apps"]
    assert app_ir.navigation_flows == []
    assert app_ir.state_machines == []
    assert app_ir.background_jobs == []
    assert app_ir.workers == []
    assert app_ir.realtime_channels == []
    assert app_ir.realtime_events == []
    assert app_ir.user_sessions == []
    assert app_ir.auth_roles == []
    assert app_ir.scenes == []
    assert app_ir.game_entities == []
    assert app_ir.input_actions == []
    assert app_ir.update_loops == []
    assert app_ir.asset_references == []
    assert app_ir.assets == {"images": [], "audio": [], "ui": [], "config": []}
    assert app_ir.runtime_targets == []
    assert app_ir.environment_requirements == []
    assert app_ir.deployment_expectations == []
