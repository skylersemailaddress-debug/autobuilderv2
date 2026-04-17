import json
import os
import subprocess
import sys
from pathlib import Path


def test_agent_runtime_cli_contract(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "agent-runtime",
            "--task",
            "open app and save result",
            "--approvals-json",
            '{"file_write": true}',
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
    assert payload["execution"]["overall_status"] in {"completed", "blocked"}
    assert payload["execution"]["replay_signature_sha256"]
    assert payload["task_model"]["task_model_version"] == "v2"
    assert payload["capability_contract"]["family"] == "agent-runtime"
    assert payload["audit_record"]["command"] == "agent-runtime"
    assert payload["audit_record"]["approval_state"] == "approved"


def test_self_extend_cli_contract(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "self-extend",
            "--lane",
            "first_class_commercial",
            "--needs",
            "custom_validator_for_geo",
            "--sandbox",
            str(tmp_path / "sandbox"),
            "--approve-core",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["status"] in {"extended", "no_gap", "partially_extended", "quarantined_only"}
    assert payload["lane_id"] == "first_class_commercial"
    assert payload["capability_contract"]["family"] == "self-extension"
    assert "activation_summary" in payload
    assert payload["audit_record"]["command"] == "self-extend"
    assert payload["audit_record"]["approval_state"] == "approved"
