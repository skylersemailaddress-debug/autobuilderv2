from pathlib import Path

from chat_builder.workflow import run_chat_first_workflow
from cli.autobuilder import run_ship_workflow


def test_chat_preview_flow_is_deterministic_for_same_prompt(tmp_path: Path) -> None:
    prompt = "Build a mobile app called Team Orbit for shift reminders"
    target = tmp_path / "preview_target"

    first = run_chat_first_workflow(
        prompt=prompt,
        target_path=str(target),
        approve=False,
        project_memory_root=tmp_path / "memory",
        ship_runner=run_ship_workflow,
    )
    second = run_chat_first_workflow(
        prompt=prompt,
        target_path=str(target),
        approve=False,
        project_memory_root=tmp_path / "memory",
        ship_runner=run_ship_workflow,
    )

    assert first["status"] in {"preview_ready", "needs_clarification"}
    assert first["status"] == second["status"]
    assert first["plan_summary"]["lane"] == second["plan_summary"]["lane"]
    assert first["plan_summary"]["stack"] == second["plan_summary"]["stack"]
    assert first["memory"]["session_id"] == second["memory"]["session_id"]


def test_chat_flow_honestly_rejects_unsupported_requests(tmp_path: Path) -> None:
    result = run_chat_first_workflow(
        prompt="Build a unity app with auto ship without preview",
        target_path=str(tmp_path / "unsupported"),
        approve=False,
        project_memory_root=tmp_path / "memory",
        ship_runner=run_ship_workflow,
    )

    assert result["status"] == "unsupported"
    assert result["plan_summary"]["unsupported"]
