import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

from cli.inspect import inspect_run
from cli.mission import run_mission
from cli.run import perform_run


def test_inspect_run_exposes_expected_fields():
    run_id = f"inspect_{uuid.uuid4().hex[:12]}"
    _, saved_path = perform_run(run_id)

    payload = inspect_run(run_id)

    assert payload["run_id"] == run_id
    assert "goal" in payload
    assert "final_status" in payload
    assert "confidence" in payload
    assert "repair_count" in payload
    assert "approval_required" in payload
    assert "event_count" in payload
    assert "summary" in payload
    assert "failure_info" in payload

    Path(saved_path).unlink()


def test_inspect_cli_json_output():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "inspect.py"
    run_id = f"inspect_cli_{uuid.uuid4().hex[:12]}"
    _, saved_path = perform_run(run_id)

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    result = subprocess.run(
        [sys.executable, str(script_path), run_id, "--json"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )

    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["run_id"] == run_id
    assert "summary" in data

    Path(saved_path).unlink()


def test_inspect_includes_mutation_and_lineage_info_from_mission_run():
    mission_result = run_mission("Delete production resources safely")
    run_id = mission_result["run_id"]

    payload = inspect_run(run_id)

    assert "change_sets" in payload
    assert payload["change_sets"]
    assert "mutation_risk_summary" in payload
    assert payload["mutation_risk_summary"]["risk_level"] == "dangerous"
    assert payload["mutation_risk_summary"]["checkpoint_required"] is True
    assert "checkpoint_restore" in payload
    assert payload["checkpoint_restore"]["restore_possible"] is True
    assert "artifact_lineage_summary" in payload
    assert "artifact_lineage_count" in payload["artifact_lineage_summary"]

    Path(mission_result["saved_path"]).unlink()
    Path(mission_result["mission_result_path"]).unlink()