from pathlib import Path

from generator.executor import apply_build_plan
from generator.plan import prepare_build_plan
from ir.compiler import compile_specs_to_ir
from specs.loader import load_spec_bundle
from validator.generated_app import validate_generated_app


def test_validate_generated_app_passes_for_first_class_build(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    app_ir = compile_specs_to_ir(load_spec_bundle(project_root / "specs"))

    target = tmp_path / "generated_app"
    plan = prepare_build_plan(app_ir, target)
    apply_build_plan(plan)

    report = validate_generated_app(target)

    assert report["all_passed"] is True
    assert report["failed_count"] == 0
    assert report["passed_count"] == report["total_checks"]
