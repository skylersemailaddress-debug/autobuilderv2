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
    assert (target_repo / ".autobuilder" / "ir.json").exists()
    assert (target_repo / ".autobuilder" / "build_plan.json").exists()


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
