import json
import os
import subprocess
import sys
from pathlib import Path

from nexus.mode import NexusMode


def test_nexus_mode_configuration_defaults():
    mode = NexusMode()

    assert mode.project_name == "Nexus0.5"
    assert mode.repo_mode is True
    assert mode.memory_enabled is True
    assert mode.approvals_enabled is True
    assert mode.resumability_enabled is True
    assert mode.contract_validation_enabled is True


def test_cli_run_persists_nexus_mode_fields(tmp_path):
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "run.py"
    run_dir = project_root / "runs"
    run_dir.mkdir(exist_ok=True)
    before_files = set(run_dir.glob("*.json"))

    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    result = subprocess.run(
        [sys.executable, str(script_path), "--nexus"],
        capture_output=True,
        text=True,
        env=env,
        cwd=str(project_root),
    )

    assert result.returncode == 0, f"CLI exited with non-zero status: {result.stderr}"
    saved_path_line = [line for line in result.stdout.splitlines() if line.startswith("saved_path=")][0]
    saved_path = Path(saved_path_line.split("=", 1)[1].strip())

    assert saved_path.exists()

    data = json.loads(saved_path.read_text(encoding="utf-8"))
    assert data["nexus_mode"] is True
    assert data["project_name"] == "Nexus0.5"
    assert data["approvals_enabled"] is True
    assert data["resumability_enabled"] is True
    assert data["contract_validation_enabled"] is True
    assert data["summary"]["nexus_mode"] is True
    assert data["summary"]["project_name"] == "Nexus0.5"
    assert data["summary"]["repo_mode"] is True
    assert data["summary"]["approvals_enabled"] is True
    assert data["summary"]["resumability_enabled"] is True

    saved_path.unlink()
