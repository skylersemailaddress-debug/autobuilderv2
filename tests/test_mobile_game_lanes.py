import json
from pathlib import Path

from cli.autobuilder import run_build_workflow


def _write_bundle(root: Path, app_type: str, frontend: str) -> None:
    files = {
        "product.yaml": json.dumps({"name": "Lane App", "app_type": app_type}) + "\n",
        "architecture.yaml": json.dumps(
            {
                "entities": [{"name": "User"}],
                "workflows": [{"name": "Flow"}],
                "api_routes": [{"path": "/health"}],
                "runtime_services": [{"name": "api"}],
                "permissions": [{"role": "user"}],
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


def test_mobile_lane_build_and_validation(tmp_path: Path) -> None:
    spec_root = tmp_path / "mobile_specs"
    spec_root.mkdir()
    _write_bundle(spec_root, app_type="mobile_app", frontend="flutter_mobile")

    target = tmp_path / "mobile_output"
    result = run_build_workflow(str(spec_root), str(target))

    assert result["status"] == "ok"
    assert result["build_status"] == "ok"
    assert result["validation_status"] == "passed"
    assert str(result["proof_status"]).startswith("certified")
    assert result["generated_app_validation"]["all_passed"] is True

    stack = result["plan"]["stack_chosen"]
    assert stack["frontend"]["name"] == "flutter_mobile"
    assert "mobile_structure" in result["validation_plan"]
    assert "mobile_markers" in result["validation_plan"]
    assert "mobile_auth_scaffold" in result["validation_plan"]
    assert "mobile_offline_store_surface" in result["validation_plan"]

    generated = set(result["files_created_summary"]["paths"])
    assert "pubspec.yaml" in generated
    assert "lib/app.dart" in generated
    assert "lib/main.dart" in generated
    assert "lib/navigation/app_router.dart" in generated
    assert "lib/screens/settings_screen.dart" in generated
    assert "lib/screens/admin_screen.dart" in generated
    assert "lib/screens/activity_screen.dart" in generated
    assert "lib/auth/auth_guard.dart" in generated
    assert "lib/state/app_state.dart" in generated
    assert "lib/data/local_store.dart" in generated
    assert "lib/services/api_client.dart" in generated
    assert "docs/READINESS.md" in generated
    assert "docs/OPERATOR.md" in generated


def test_game_lane_build_and_validation(tmp_path: Path) -> None:
    spec_root = tmp_path / "game_specs"
    spec_root.mkdir()
    _write_bundle(spec_root, app_type="game_app", frontend="godot_game")

    target = tmp_path / "game_output"
    result = run_build_workflow(str(spec_root), str(target))

    assert result["status"] == "ok"
    assert result["build_status"] == "ok"
    assert result["validation_status"] == "passed"
    assert str(result["proof_status"]).startswith("certified")
    assert result["generated_app_validation"]["all_passed"] is True

    stack = result["plan"]["stack_chosen"]
    assert stack["frontend"]["name"] == "godot_game"
    assert "game_structure" in result["validation_plan"]
    assert "game_markers" in result["validation_plan"]
    assert "hud_surface_present" in result["validation_plan"]
    assert "game_export_guidance_present" in result["validation_plan"]

    generated = set(result["files_created_summary"]["paths"])
    assert "project.godot" in generated
    assert "scenes/Main.tscn" in generated
    assert "scenes/HUD.tscn" in generated
    assert "scripts/main.gd" in generated
    assert "scripts/player.gd" in generated
    assert "scripts/input_map.gd" in generated
    assert "scripts/game_state.gd" in generated
    assert "scripts/hud.gd" in generated
    assert "docs/EXPORT_AND_RUN.md" in generated
