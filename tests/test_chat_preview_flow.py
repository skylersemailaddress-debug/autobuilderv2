from pathlib import Path

from chat_builder.workflow import run_chat_first_workflow
from cli.autobuilder import run_ship_workflow


def test_preview_first_flow_without_approval(tmp_path: Path) -> None:
    target = tmp_path / "preview_target"
    result = run_chat_first_workflow(
        prompt="Build a mobile app called Kid Quest for team checklists",
        target_path=str(target),
        approve=False,
        project_memory_root=tmp_path / "memory",
        ship_runner=run_ship_workflow,
    )

    assert result["status"] in {"preview_ready", "needs_clarification"}
    assert "plan_summary" in result
    assert "build_progress" in result
    assert result["build_progress"][0] == "preview_generated"


def test_preview_approval_starts_build_and_returns_proof(tmp_path: Path) -> None:
    target = tmp_path / "built_target"
    result = run_chat_first_workflow(
        prompt="Build a realtime app called Sensor Friend for team alerts and dashboards",
        target_path=str(target),
        approve=True,
        project_memory_root=tmp_path / "memory",
        ship_runner=run_ship_workflow,
    )

    assert result["status"] == "built"
    assert result["final_outputs"]["target_path"] == str(target.resolve())
    assert result["final_outputs"]["proof_result"]["status"].startswith("certified")
    assert result["final_outputs"]["readiness_result"]["status"] == "ready"


def test_unsupported_request_handling_is_explicit(tmp_path: Path) -> None:
    target = tmp_path / "unsupported_target"
    result = run_chat_first_workflow(
        prompt="Build an unreal game with kubernetes autoscaling",
        target_path=str(target),
        approve=False,
        project_memory_root=tmp_path / "memory",
        ship_runner=run_ship_workflow,
    )

    assert result["status"] == "unsupported"
    assert result["plan_summary"]["unsupported"]
