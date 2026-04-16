import json
import os
import subprocess
import sys
from pathlib import Path


def test_autobuilder_build_command_emits_machine_readable_summary(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    target_repo = tmp_path / "generated_app"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "build",
            "--spec",
            str(project_root / "specs"),
            "--target",
            str(target_repo),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] == "ok"
    assert payload["build_status"] == "ok"
    assert payload["validation_status"] == "passed"
    assert str(payload["proof_status"]).startswith("certified")
    assert payload["spec_root"].endswith("specs")
    assert payload["target_repo"] == str(target_repo.resolve())
    assert "plan" in payload
    assert "execution" in payload
    assert payload["plan"]["archetype_chosen"]["name"] == "saas_web_app"
    assert payload["plan"]["stack_chosen"]["frontend"]["name"] == "react_next"
    assert "planned_repo_structure" in payload["plan"]
    assert "planned_modules" in payload["plan"]
    assert "planned_validation_surface" in payload["plan"]
    assert payload["execution"]["operations_applied"]
    assert payload["execution"]["output_hash"]
    assert payload["execution"]["output_files"]
    assert payload["generated_app_validation"]["all_passed"] is True
    assert payload["generated_app_validation"]["failed_count"] == 0
    assert payload["repair_report"]["unrepaired_blockers"] == []
    assert payload["unrepaired_blockers"] == []
    assert payload["determinism"]["verified"] is True
    assert payload["determinism"]["repeat_build_match_required"] is True
    assert (target_repo / ".autobuilder" / "ir.json").exists()
    assert (target_repo / ".autobuilder" / "build_plan.json").exists()
    assert (target_repo / ".autobuilder" / "proof_report.json").exists()
    assert (target_repo / ".autobuilder" / "readiness_report.json").exists()
    assert (target_repo / ".autobuilder" / "validation_summary.json").exists()
    assert (target_repo / ".autobuilder" / "determinism_signature.json").exists()


def test_autobuilder_build_command_reports_resolution_errors(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    bad_specs = tmp_path / "bad_specs"
    bad_specs.mkdir()
    (bad_specs / "product.yaml").write_text('{"name": "Broken App", "app_type": "unknown_app"}\n', encoding="utf-8")
    (bad_specs / "architecture.yaml").write_text('{"entities": [], "workflows": [], "api_routes": [], "runtime_services": [], "permissions": []}\n', encoding="utf-8")
    (bad_specs / "ui.yaml").write_text('{"pages": []}\n', encoding="utf-8")
    (bad_specs / "acceptance.yaml").write_text('{"criteria": ["works"]}\n', encoding="utf-8")
    (bad_specs / "stack.yaml").write_text('{"frontend": "react_next", "backend": "fastapi", "database": "postgres", "deployment": "docker_compose", "deployment_target": "container"}\n', encoding="utf-8")

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "build",
            "--spec",
            str(bad_specs),
            "--target",
            str(tmp_path / "generated_app"),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["status"] == "error"
    assert "Unsupported app_type" in payload["error"]


def test_autobuilder_validate_and_proof_app_commands(tmp_path: Path):
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    target_repo = tmp_path / "generated_app"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    build_result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "build",
            "--spec",
            str(project_root / "specs"),
            "--target",
            str(target_repo),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert build_result.returncode == 0, build_result.stderr

    (target_repo / "docs" / "READINESS.md").unlink()

    validate_result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "validate-app",
            "--target",
            str(target_repo),
            "--repair",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert validate_result.returncode == 0, validate_result.stderr
    validate_payload = json.loads(validate_result.stdout)
    assert validate_payload["validation_status"] == "passed"
    assert validate_payload["repaired_issues"]

    proof_result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "proof-app",
            "--target",
            str(target_repo),
            "--repair",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert proof_result.returncode == 0, proof_result.stderr
    proof_payload = json.loads(proof_result.stdout)
    assert str(proof_payload["proof_status"]).startswith("certified")
    assert proof_payload["proof_artifacts"]["artifact_paths"]["proof_report"]
