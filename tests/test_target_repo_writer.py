from pathlib import Path

from generator.executor import apply_build_plan
from generator.plan import prepare_build_plan
from ir.compiler import compile_specs_to_ir
from specs.loader import load_spec_bundle


def test_apply_build_plan_writes_expected_files(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    app_ir = compile_specs_to_ir(load_spec_bundle(project_root / "specs"))

    target = tmp_path / "target_repo"
    plan = prepare_build_plan(app_ir, target)
    result = apply_build_plan(plan)

    assert result.target_repo == str(target.resolve())
    assert (target / ".autobuilder" / "ir.json").exists()
    assert (target / ".autobuilder" / "build_plan.json").exists()
    assert (target / "app" / "README.md").exists()
    assert (target / "api" / "README.md").exists()
    assert (target / "db" / "README.md").exists()
    assert (target / "validation" / "README.md").exists()
    assert (target / "README.md").exists()

    ops = result.operations_applied
    assert ops
    assert all(item["status"] == "ok" for item in ops)
