import json
from pathlib import Path

from cli.autobuilder import run_build_workflow


def _write_bundle(root: Path, app_type: str, frontend: str) -> None:
    files = {
        "product.yaml": json.dumps({"name": "Lane App", "app_type": app_type}) + "\n",
        "architecture.yaml": json.dumps(
            {
                "entities": [{"name": "Sensor"}],
                "workflows": [{"name": "Routing"}],
                "api_routes": [{"path": "/health"}],
                "runtime_services": [{"name": "api"}],
                "permissions": [{"role": "operator"}],
                "realtime_channels": [{"channel": "ops.events"}],
                "realtime_events": [{"event": "alert.raised"}],
            }
        )
        + "\n",
        "ui.yaml": json.dumps({"pages": [{"name": "Home", "route": "/"}]}) + "\n",
        "acceptance.yaml": json.dumps({"criteria": ["generated lane is runnable"]}) + "\n",
        "stack.yaml": json.dumps(
            {
                "frontend": frontend,
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
                "deployment_target": "container",
            }
        )
        + "\n",
    }
    for file_name, content in files.items():
        (root / file_name).write_text(content, encoding="utf-8")


def test_realtime_lane_build_and_validation(tmp_path: Path) -> None:
    spec_root = tmp_path / "realtime_specs"
    spec_root.mkdir()
    _write_bundle(spec_root, app_type="realtime_system", frontend="react_next")

    target = tmp_path / "realtime_output"
    result = run_build_workflow(str(spec_root), str(target))

    assert result["status"] == "ok"
    assert result["build_status"] == "ok"
    assert result["validation_status"] == "passed"
    assert str(result["proof_status"]).startswith("certified")
    assert result["generated_app_validation"]["all_passed"] is True
    assert "realtime_structure" in result["validation_plan"]
    assert "realtime_markers" in result["validation_plan"]
    assert "realtime_ws_gateway_present" in result["validation_plan"]
    assert "realtime_alert_action_path_present" in result["validation_plan"]

    generated = set(result["files_created_summary"]["paths"])
    assert "frontend/lib/realtime-client.ts" in generated
    assert "frontend/lib/alert-actions.ts" in generated
    assert "backend/connectors/sensors.py" in generated
    assert "backend/realtime/channels.py" in generated
    assert "backend/realtime/events.py" in generated
    assert "backend/realtime/world_state.py" in generated
    assert "backend/realtime/ws_gateway.py" in generated
    assert "backend/api/realtime.py" in generated
    assert "backend/services/alerts.py" in generated
    assert "docs/READINESS.md" in generated

    artifacts = result["proof_artifacts"]["artifact_paths"]
    assert Path(artifacts["runtime_verification"]).exists()
    assert Path(artifacts["failure_corpus"]).exists()
    assert Path(artifacts["replay_harness"]).exists()


def test_enterprise_agent_lane_build_and_validation(tmp_path: Path) -> None:
    spec_root = tmp_path / "enterprise_specs"
    spec_root.mkdir()
    _write_bundle(spec_root, app_type="enterprise_agent_system", frontend="react_next")

    target = tmp_path / "enterprise_output"
    result = run_build_workflow(str(spec_root), str(target))

    assert result["status"] == "ok"
    assert result["build_status"] == "ok"
    assert result["validation_status"] == "passed"
    assert str(result["proof_status"]).startswith("certified")
    assert result["generated_app_validation"]["all_passed"] is True
    assert "enterprise_structure" in result["validation_plan"]
    assert "enterprise_markers" in result["validation_plan"]
    assert "multi_role_workflow_surface" in result["validation_plan"]
    assert "enterprise_reporting_surface" in result["validation_plan"]

    generated = set(result["files_created_summary"]["paths"])
    assert "frontend/components/workflow-board.tsx" in generated
    assert "backend/workflows/router.py" in generated
    assert "backend/workflows/approvals.py" in generated
    assert "backend/memory/state_store.py" in generated
    assert "backend/agent/briefing.py" in generated
    assert "backend/api/enterprise.py" in generated
    assert "docs/READINESS.md" in generated

    artifacts = result["proof_artifacts"]["artifact_paths"]
    assert Path(artifacts["security_governance_contract"]).exists()
    assert Path(artifacts["commerce_pack_contract"]).exists()
    assert Path(artifacts["pack_composition"]).exists()
