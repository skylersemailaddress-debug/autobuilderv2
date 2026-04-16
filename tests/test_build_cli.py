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
    assert payload["execution"]["operations_applied"]
    assert (target_repo / ".autobuilder" / "ir.json").exists()
