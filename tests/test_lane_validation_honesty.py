import json
from pathlib import Path

from cli.autobuilder import run_build_workflow, run_generated_app_validation_workflow


def _write_bundle(root: Path, app_type: str, frontend: str) -> None:
    files = {
        "product.yaml": json.dumps({"name": "Lane Honesty", "app_type": app_type}) + "\n",
        "architecture.yaml": json.dumps(
            {
                "entities": [{"name": "User"}],
                "workflows": [{"name": "Flow"}],
                "api_routes": [{"path": "/health"}],
                "runtime_services": [{"name": "api"}],
                "permissions": [{"role": "operator"}],
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


def test_mobile_lane_validation_fails_honestly_when_depth_missing(tmp_path: Path) -> None:
    spec_root = tmp_path / "mobile_specs"
    spec_root.mkdir()
    _write_bundle(spec_root, app_type="mobile_app", frontend="flutter_mobile")

    target = tmp_path / "mobile_output"
    result = run_build_workflow(str(spec_root), str(target))
    assert result["validation_status"] == "passed"

    # Remove a lane-specific depth file and confirm validate-app fails explicitly.
    (target / "lib" / "data" / "local_store.dart").unlink()
    validation = run_generated_app_validation_workflow(str(target), repair=False)

    assert validation["validation_status"] == "failed"
    assert validation["lane_validation"]["status"] == "failed"
    assert "mobile_offline_store_surface" in validation["lane_validation"]["failed_checks"]
