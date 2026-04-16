from pathlib import Path

from generator.plan import prepare_build_plan
from ir.compiler import compile_specs_to_ir
from specs.loader import load_spec_bundle


def test_prepare_build_plan_is_archetype_and_stack_aware():
    project_root = Path(__file__).resolve().parents[1]
    app_ir = compile_specs_to_ir(load_spec_bundle(project_root / "specs"))

    plan = prepare_build_plan(app_ir, project_root / "tmp_build_target")

    assert plan.archetype_chosen["name"] == "saas_web_app"
    assert plan.stack_chosen["frontend"]["name"] == "react_next"
    assert "api/" in plan.planned_repo_structure
    assert ".autobuilder/build_plan.json" in plan.planned_modules
    assert "signup_to_activation" in plan.planned_validation_surface
    assert "frontend_build" in plan.planned_validation_surface