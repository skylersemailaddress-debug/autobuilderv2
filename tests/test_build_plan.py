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
    assert "frontend/" in plan.planned_repo_structure
    assert "backend/" in plan.planned_repo_structure
    assert ".autobuilder/build_plan.json" in plan.planned_modules
    assert "frontend/app/page.tsx" in plan.planned_modules
    assert "frontend/components/enterprise-shell.tsx" in plan.planned_modules
    assert "frontend/components/enterprise-states.tsx" in plan.planned_modules
    assert "frontend/app/settings/page.tsx" in plan.planned_modules
    assert "frontend/app/admin/page.tsx" in plan.planned_modules
    assert "frontend/app/activity/page.tsx" in plan.planned_modules
    assert "backend/api/main.py" in plan.planned_modules
    assert "backend/api/responses.py" in plan.planned_modules
    assert "backend/api/logging.py" in plan.planned_modules
    assert "backend/api/admin.py" in plan.planned_modules
    assert "backend/api/operator.py" in plan.planned_modules
    assert "backend/api/audit.py" in plan.planned_modules
    assert "docker-compose.yml" in plan.planned_modules
    assert "docs/ENTERPRISE_POLISH.md" in plan.planned_modules
    assert "docs/READINESS.md" in plan.planned_modules
    assert "docs/PROOF_OF_RUN.md" in plan.planned_modules
    assert ".autobuilder/proof_report.json" in plan.planned_modules
    assert ".autobuilder/readiness_report.json" in plan.planned_modules
    assert ".autobuilder/validation_summary.json" in plan.planned_modules
    assert ".autobuilder/determinism_signature.json" in plan.planned_modules
    assert "signup_to_activation" in plan.planned_validation_surface
    assert "frontend_build" in plan.planned_validation_surface
    assert "required_repo_structure_present" in plan.planned_validation_surface
    assert "frontend_shell_essentials_present" in plan.planned_validation_surface
    assert "backend_endpoint_essentials_present" in plan.planned_validation_surface
    assert "env_config_essentials_present" in plan.planned_validation_surface
    assert "docker_deployment_essentials_present" in plan.planned_validation_surface
    assert "proof_readiness_artifacts_present" in plan.planned_validation_surface
    assert "enterprise_polish_surface_presence" in plan.planned_validation_surface
    assert plan.planned_repo_structure == sorted(plan.planned_repo_structure)
    assert plan.planned_modules == sorted(plan.planned_modules)
    assert plan.planned_validation_surface == sorted(plan.planned_validation_surface)

    create_dirs = [op.path for op in plan.operations if op.op == "create_dir"]
    written_files = [op.path for op in plan.operations if op.op == "write_file"]
    assert create_dirs == sorted(create_dirs)
    assert written_files == sorted(written_files)
    assert "backend_pytest_endpoints" in plan.planned_validation_surface