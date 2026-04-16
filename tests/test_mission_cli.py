import json
import os
import subprocess
import sys
from pathlib import Path

from cli.mission import resume_mission, run_mission


def _cleanup_result_files(result):
    for key in ("saved_path", "mission_result_path"):
        path_value = result.get(key)
        if path_value:
            path = Path(path_value)
            if path.exists():
                path.unlink()


def test_one_button_mission_low_risk_goal():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "mission.py"

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)
    result = subprocess.run(
        [sys.executable, str(script_path), "Build an autonomous execution plan", "--json"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["final_status"] == "complete"
    assert payload["approval_required"] is False
    assert payload["awaiting_approval"] is False
    assert Path(payload["saved_path"]).exists()
    assert Path(payload["mission_result_path"]).exists()

    _cleanup_result_files(payload)


def test_mission_result_contains_expected_fields():
    result = run_mission("Build an autonomous execution plan")

    expected_fields = {
        "run_id",
        "goal",
        "final_status",
        "approval_required",
        "awaiting_approval",
        "confidence",
        "repair_count",
        "summary",
        "saved_path",
        "mission_result_path",
    }
    assert expected_fields.issubset(result.keys())
    assert isinstance(result["summary"], dict)

    _cleanup_result_files(result)


def test_high_risk_goal_enters_approval_pause_cleanly():
    result = run_mission("Delete production resources safely")

    assert result["final_status"] == "awaiting_approval"
    assert result["approval_required"] is True
    assert result["awaiting_approval"] is True
    assert "resume_hint" in result

    _cleanup_result_files(result)


def test_resume_path_continues_after_approval_pause():
    paused_result = run_mission("Delete production resources safely")
    run_id = paused_result["run_id"]

    resumed_result = resume_mission(run_id, approve=True)

    assert resumed_result["run_id"] == run_id
    assert resumed_result["final_status"] == "complete"
    assert resumed_result["awaiting_approval"] is False

    _cleanup_result_files(resumed_result)