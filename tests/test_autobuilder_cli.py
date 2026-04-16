import json
import os
import subprocess
import sys
from pathlib import Path


def test_autobuilder_cli_help_shows_expected_subcommands():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"

    result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
    )

    assert result.returncode == 0
    assert "mission" in result.stdout
    assert "resume" in result.stdout
    assert "inspect" in result.stdout
    assert "benchmark" in result.stdout
    assert "readiness" in result.stdout
    assert "build" in result.stdout
    assert "chat-build" in result.stdout


def test_autobuilder_cli_reaches_core_flows():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    mission = subprocess.run(
        [sys.executable, str(script_path), "mission", "Delete production resources safely", "--json"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert mission.returncode == 0, mission.stderr
    mission_payload = json.loads(mission.stdout)
    run_id = mission_payload["run_id"]
    assert mission_payload["awaiting_approval"] is True

    inspect = subprocess.run(
        [sys.executable, str(script_path), "inspect", run_id, "--json"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert inspect.returncode == 0, inspect.stderr
    inspect_payload = json.loads(inspect.stdout)
    assert inspect_payload["run_id"] == run_id

    resume = subprocess.run(
        [sys.executable, str(script_path), "resume", run_id, "--approve", "--json"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert resume.returncode == 0, resume.stderr
    resume_payload = json.loads(resume.stdout)
    assert resume_payload["final_status"] == "complete"

    benchmark = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "benchmark",
            "--cases",
            "simple_low_risk_mission",
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert benchmark.returncode == 0, benchmark.stderr
    benchmark_payload = json.loads(benchmark.stdout)
    assert benchmark_payload["total_cases"] == 1

    readiness = subprocess.run(
        [sys.executable, str(script_path), "readiness", "--json"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert readiness.returncode == 0, readiness.stderr
    readiness_payload = json.loads(readiness.stdout)
    assert "readiness_status" in readiness_payload
    assert "readiness_reasons" in readiness_payload

    for payload in (mission_payload, resume_payload):
        saved_path = Path(payload["saved_path"])
        mission_result_path = Path(payload["mission_result_path"])
        if saved_path.exists():
            saved_path.unlink()
        if mission_result_path.exists():
            mission_result_path.unlink()

    for item in benchmark_payload.get("cases", []):
        run_file = project_root / "runs" / f"{item['run_id']}.json"
        if run_file.exists():
            run_file.unlink()
