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
    assert (target / ".autobuilder" / "generation_summary.json").exists()
    assert (target / "frontend" / "app" / "page.tsx").exists()
    assert (target / "frontend" / "tests" / "shell-check.js").exists()
    assert (target / "backend" / "api" / "main.py").exists()
    assert (target / "backend" / "tests" / "test_endpoints.py").exists()
    assert (target / "docker-compose.yml").exists()
    assert (target / ".env.example").exists()
    assert (target / "README.md").exists()

    frontend_page = (target / "frontend" / "app" / "page.tsx").read_text(encoding="utf-8")
    assert 'data-testid="workspace-shell"' in frontend_page
    assert "/api/workspace/execute" in frontend_page

    backend_main = (target / "backend" / "api" / "main.py").read_text(encoding="utf-8")
    assert "@app.get(\"/health\")" in backend_main
    assert "@app.get(\"/ready\")" in backend_main
    assert "@app.get(\"/version\")" in backend_main
    assert "@app.post(\"/api/workspace/execute\")" in backend_main

    ops = result.operations_applied
    assert ops
    assert all(item["status"] == "ok" for item in ops)
