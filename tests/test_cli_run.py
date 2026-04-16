import json
import os
import subprocess
import sys
from pathlib import Path


def test_cli_run_script():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "run.py"
    run_dir = project_root / "runs"
    run_dir.mkdir(exist_ok=True)
    before_files = set(run_dir.glob("*.json"))

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )

    assert result.returncode == 0, f"CLI exited with non-zero status: {result.stderr}"
    assert "run_id=" in result.stdout
    assert "status=" in result.stdout
    assert "saved_path=" in result.stdout

    saved_path_line = [line for line in result.stdout.splitlines() if line.startswith("saved_path=")][0]
    saved_path = Path(saved_path_line.split("=", 1)[1].strip())

    assert saved_path.exists()
    assert saved_path.suffix == ".json"

    run_files = set(run_dir.glob("*.json"))
    new_files = run_files - before_files
    assert len(new_files) == 1

    data = json.loads(saved_path.read_text(encoding="utf-8"))
    assert data["status"] == "complete"
    assert data["state_history"][-1] == "complete"
    assert data["run_id"]
    assert data["created_at"]
    assert data["goal"] == "Build an autonomous execution plan"
    assert isinstance(data.get("tasks"), list)
    assert len(data["tasks"]) == 3
    assert all(task["status"] == "complete" for task in data["tasks"])
    assert data.get("validation") is not None
    assert data.get("repair_used") is True
    assert isinstance(data.get("artifacts"), list)

    saved_path.unlink()
