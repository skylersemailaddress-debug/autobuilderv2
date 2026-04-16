import json
import os
import subprocess
import sys
from pathlib import Path


def test_canonical_command_surface_in_help_output() -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )

    assert result.returncode == 0
    output = result.stdout
    for command in ("readiness", "build", "validate-app", "proof-app", "ship"):
        assert command in output


def test_commercial_example_ship_flow_succeeds(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    target_repo = tmp_path / "commercial_example"

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
    assert payload["status"] == "ok"
    assert payload["build_status"] == "ok"
    assert payload["validation_result"]["status"] == "passed"
    assert payload["readiness_result"]["status"] == "ready"


def test_unsupported_stack_is_rejected_for_commercial_lane(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    bad_specs = tmp_path / "unsupported_specs"
    bad_specs.mkdir()

    (bad_specs / "product.yaml").write_text(
        '{"name": "Unsupported Lane", "app_type": "saas_web_app"}\n', encoding="utf-8"
    )
    (bad_specs / "architecture.yaml").write_text(
        '{"entities": [], "workflows": [], "api_routes": [], "runtime_services": [], "permissions": []}\n',
        encoding="utf-8",
    )
    (bad_specs / "ui.yaml").write_text('{"pages": [{"name": "Home", "surface": "web", "route": "/"}]}\n', encoding="utf-8")
    (bad_specs / "acceptance.yaml").write_text('{"criteria": ["works"]}\n', encoding="utf-8")
    (bad_specs / "stack.yaml").write_text(
        '{"frontend": "future_frontend_placeholder", "backend": "fastapi", "database": "postgres", "deployment": "docker_compose", "deployment_target": "container"}\n',
        encoding="utf-8",
    )

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
    assert "Unsupported commercial lane stack selection" in payload["error"]


def test_ship_report_and_emitted_proof_are_consistent(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    target_repo = tmp_path / "consistency_app"

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

    proof_report = json.loads((target_repo / ".autobuilder" / "proof_report.json").read_text(encoding="utf-8"))
    readiness_report = json.loads((target_repo / ".autobuilder" / "readiness_report.json").read_text(encoding="utf-8"))
    package_summary = json.loads(
        (target_repo / ".autobuilder" / "package_artifact_summary.json").read_text(encoding="utf-8")
    )

    assert payload["proof_result"]["status"] == proof_report["proof_status"]
    assert payload["readiness_result"]["status"] == readiness_report["readiness_status"]
    assert payload["packaged_app_artifact_summary"]["packaging_status"] == package_summary["packaging_status"]
