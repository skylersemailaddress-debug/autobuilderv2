import json
import os
import subprocess
import sys
from pathlib import Path


def test_chat_build_cli_help_and_preview_json(tmp_path: Path) -> None:
    project_root = Path(__file__).resolve().parents[1]
    script_path = project_root / "cli" / "autobuilder.py"
    env = os.environ.copy()
    env["PYTHONPATH"] = str(project_root)

    help_result = subprocess.run(
        [sys.executable, str(script_path), "--help"],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )
    assert help_result.returncode == 0
    assert "chat-build" in help_result.stdout

    preview_result = subprocess.run(
        [
            sys.executable,
            str(script_path),
            "chat-build",
            "--prompt",
            "Build a mobile app called Tiny Track for school team reminders",
            "--target",
            str(tmp_path / "chat_preview"),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(project_root),
        env=env,
    )

    assert preview_result.returncode == 0, preview_result.stderr
    payload = json.loads(preview_result.stdout)
    assert payload["status"] in {"preview_ready", "needs_clarification"}
    assert "plan_summary" in payload
    assert "conversation_surface" in payload
    assert isinstance(payload["conversation_surface"], dict)
    assert payload["capability_contract"]["family"] == "chat-first"
    assert payload["memory"]["memory_path"]
    assert payload["audit_record"]["command"] == "chat-build"
    assert payload["safety_contract"]["mutation_mode"] == "preview_only"
