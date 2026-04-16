import os
import subprocess
import sys
from pathlib import Path


def test_cli_run_script():
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "run.py"
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
