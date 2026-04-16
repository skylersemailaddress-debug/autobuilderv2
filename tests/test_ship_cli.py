import json
import os
import subprocess
import sys
from pathlib import Path


def test_ship_command_succeeds_with_machine_readable_report(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    target_repo = tmp_path / "shipped_app"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "ship",
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
    assert payload["archetype"] == "saas_web_app"
    assert payload["stack"]["frontend"] == "react_next"
    assert payload["stack"]["backend"] == "fastapi"
    assert payload["stack"]["database"] == "postgres"
    assert payload["stack"]["deployment"] == "docker_compose"
    assert payload["validation_result"]["status"] == "passed"
    assert str(payload["proof_result"]["status"]).startswith("certified")
    assert payload["readiness_result"]["status"] == "ready"
    assert payload["packaged_app_artifact_summary"]["packaging_status"] == "ready"
    assert payload["deployment_readiness_summary"]["status"] == "ready"
    assert payload["proof_summary"]["bundle_status"] == "complete"
    assert payload["final_target_path"] == str(target_repo.resolve())


def test_ship_command_fails_with_incomplete_specs(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    bad_specs = tmp_path / "bad_specs"
    bad_specs.mkdir()

    (bad_specs / "product.yaml").write_text('{"name": "Broken", "app_type": "saas_web_app"}\n', encoding="utf-8")
    (bad_specs / "architecture.yaml").write_text(
        '{"entities": [], "workflows": [], "api_routes": [], "runtime_services": [], "permissions": []}\n',
        encoding="utf-8",
    )
    (bad_specs / "ui.yaml").write_text('{"pages": []}\n', encoding="utf-8")
    (bad_specs / "stack.yaml").write_text(
        '{"frontend": "react_next", "backend": "fastapi", "database": "postgres", "deployment": "docker_compose", "deployment_target": "container"}\n',
        encoding="utf-8",
    )
    # acceptance.yaml intentionally omitted

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "ship",
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
    assert "Missing required spec files" in payload["error"]


def test_ship_command_output_structure_is_stable(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    target_repo = tmp_path / "shipped_app"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "ship",
            "--spec",
            str(project_root / "specs" / "examples" / "commercial_workspace"),
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
    expected_top_level_keys = {
        "status",
        "build_status",
        "archetype",
        "stack",
        "files_generated",
        "validation_result",
        "repair_actions_taken",
        "proof_result",
        "readiness_result",
        "packaged_app_artifact_summary",
        "deployment_readiness_summary",
        "proof_summary",
        "final_target_path",
        "determinism",
    }
    assert expected_top_level_keys.issubset(payload.keys())
