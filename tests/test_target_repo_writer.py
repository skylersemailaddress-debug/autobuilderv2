from pathlib import Path
import json
import pytest

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
    assert (target / "backend" / "api" / "auth.py").exists()
    assert (target / "backend" / "api" / "security.py").exists()
    assert (target / "backend" / "security" / "auth_dependency.py").exists()
    assert (target / "backend" / "security" / "rbac.py").exists()
    assert (target / "backend" / "api" / "plans.py").exists()
    assert (target / "backend" / "api" / "billing_webhooks.py").exists()
    assert (target / "backend" / "api" / "billing_admin.py").exists()
    assert (target / "backend" / "services" / "entitlements.py").exists()
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
    assert "AuthContext" in backend_main
    assert "require_auth_context" in backend_main
    assert "security_scaffold_enabled" in backend_main
    assert "app.include_router(plans_router)" in backend_main
    assert "app.include_router(billing_router)" in backend_main

    lifecycle_decisions_path = target / ".autobuilder" / "lifecycle_regeneration_decisions.json"
    assert lifecycle_decisions_path.exists()
    lifecycle_payload = json.loads(lifecycle_decisions_path.read_text(encoding="utf-8"))
    assert lifecycle_payload["contract_version"] == "v1"
    assert lifecycle_payload["decision_count"] > 0
    assert any("regen_safety_level" in item for item in lifecycle_payload["decisions"])

    ops = result.operations_applied
    assert ops
    assert all(item["status"] == "ok" for item in ops)


def test_lifecycle_guardrail_blocks_overwrite_for_production_critical_file(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    app_ir = compile_specs_to_ir(load_spec_bundle(project_root / "specs"))

    target = tmp_path / "critical_target"
    initial_plan = prepare_build_plan(app_ir, target)
    apply_build_plan(initial_plan)

    # Simulate operator modification on a production-critical path.
    critical_file = target / "db" / "schema.sql"
    critical_file.write_text("ALTER TABLE users ADD COLUMN extra TEXT;\n", encoding="utf-8")

    regen_plan = prepare_build_plan(app_ir, target)
    with pytest.raises(RuntimeError, match="Lifecycle guardrail blocked overwrite"):
        apply_build_plan(regen_plan)
