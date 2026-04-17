import json
import os
import subprocess
import sys
from pathlib import Path


def _run_command(args: list[str]) -> tuple[int, dict[str, object]]:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [sys.executable, str(script_path)] + args + ["--json"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    return result.returncode, json.loads(result.stdout)


def test_command_surface_status_and_command_fields() -> None:
    code, readiness = _run_command(["readiness"])
    assert code == 0
    assert readiness["status"] == "ok"
    assert readiness["command"] == "readiness"


def test_build_error_has_predictable_contract(tmp_path: Path) -> None:
    bad_specs = tmp_path / "bad_specs"
    bad_specs.mkdir()
    (bad_specs / "product.yaml").write_text('{"name":"Broken","app_type":"saas_web_app"}\n', encoding="utf-8")

    code, payload = _run_command(["build", "--spec", str(bad_specs), "--target", str(tmp_path / "out")])
    assert code == 2
    assert payload["status"] == "error"
    assert payload["command"] == "build"
    assert "Missing required spec files" in str(payload["error"])
    assert payload["audit_record"]["failure_classification"] == "input_validation_error"
    assert payload["safety_contract"]["command"] == "build"


def test_first_class_ship_regression_contract(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    code, payload = _run_command(["ship", "--spec", str(project_root / "specs"), "--target", str(tmp_path / "ship")])

    assert code == 0
    assert payload["status"] == "ok"
    assert payload["command"] == "ship"
    assert payload["build_status"] == "ok"
    assert payload["validation_result"]["status"] == "passed"
    assert str(payload["proof_result"]["status"]).startswith("certified")
    assert payload["audit_record"]["command"] == "ship"
    assert payload["audit_record"]["rollback_ready"] is True
    assert payload["restore_payload"]["restore_references"]["checkpoint_id"]
    assert payload["safety_contract"]["rollback_behavior"] == "checkpoint_manifest_and_restore_plan_emitted"


def test_validate_and_proof_commands_emit_audit_and_safety_contract(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    build_code, _ = _run_command(["build", "--spec", str(project_root / "specs"), "--target", str(tmp_path / "app")])
    assert build_code == 0

    validate_code, validate_payload = _run_command(["validate-app", "--target", str(tmp_path / "app")])
    proof_code, proof_payload = _run_command(["proof-app", "--target", str(tmp_path / "app")])

    assert validate_code == 0
    assert validate_payload["command"] == "validate-app"
    assert validate_payload["audit_record"]["command"] == "validate-app"
    assert validate_payload["safety_contract"]["command"] == "validate-app"

    assert proof_code == 0
    assert proof_payload["command"] == "proof-app"
    assert proof_payload["audit_record"]["command"] == "proof-app"
    assert proof_payload["safety_contract"]["command"] == "proof-app"
