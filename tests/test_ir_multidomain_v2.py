from pathlib import Path

from ir.compiler import compile_specs_to_ir
from specs.loader import load_spec_bundle


def _write_bundle(root: Path, app_type: str, extra: dict[str, str]) -> None:
    files = {
        "product.yaml": (
            '{"name": "Domain App", "app_type": "' + app_type + '", '
            '"application_domains": ["games", "mobile_apps"], '
            '"assets": {"images": ["hero.png"], "audio": ["theme.ogg"], '
            '"ui": ["hud.svg"], "config": ["controls.json"]}}\n'
        ),
        "architecture.yaml": (
            '{"entities": [{"name": "User"}], "workflows": [{"name": "Flow"}], '
            '"api_routes": [{"path": "/api/ping"}], "runtime_services": [{"name": "api"}], '
            '"permissions": [{"role": "user"}], '
            '"navigation_flows": [{"name": "B"}, {"name": "A"}], '
            '"state_machines": [{"name": "MachineB"}, {"name": "MachineA"}], '
            '"background_jobs": [{"name": "job-b"}, {"name": "job-a"}], '
            '"workers": [{"name": "worker-2"}, {"name": "worker-1"}], '
            '"realtime_channels": [{"channel": "z-room"}, {"channel": "a-room"}], '
            '"realtime_events": [{"event": "z-event"}, {"event": "a-event"}], '
            '"user_sessions": [{"name": "session-b"}, {"name": "session-a"}], '
            '"auth_roles": [{"name": "viewer"}, {"name": "admin"}], '
            '"scenes": [{"name": "scene-2"}, {"name": "scene-1"}], '
            '"game_entities": [{"name": "entity-b"}, {"name": "entity-a"}], '
            '"input_actions": [{"name": "jump"}, {"name": "attack"}], '
            '"update_loops": [{"name": "render"}, {"name": "physics"}], '
            '"asset_references": [{"asset": "z.tex"}, {"asset": "a.tex"}]}\n'
        ),
        "ui.yaml": '{"pages": [{"name": "Home", "route": "/"}], "navigation_flows": [{"name": "UI-B"}, {"name": "UI-A"}]}\n',
        "acceptance.yaml": '{"criteria": ["works"]}\n',
        "stack.yaml": (
            '{"frontend": "react_next", "backend": "fastapi", "database": "postgres", '
            '"deployment": "docker_compose", "deployment_target": "container", '
            '"runtime_targets": ["ios", "android", "web"], '
            '"environment_requirements": ["python3.12", "node20"], '
            '"deployment_expectations": ["docker_compose_local", "health_ready_version"]}\n'
        ),
    }
    files.update(extra)
    for file_name, content in files.items():
        (root / file_name).write_text(content, encoding="utf-8")


def test_ir_v2_compiles_multiple_domains(tmp_path: Path) -> None:
    for app_type in ("saas_web_app", "api_service", "mobile_app", "game_app", "realtime_system"):
        root = tmp_path / app_type
        root.mkdir()
        _write_bundle(root, app_type, {})

        bundle = load_spec_bundle(root)
        app_ir = compile_specs_to_ir(bundle)

        assert app_ir.app_type == app_type
        assert app_ir.application_domains == ["games", "mobile_apps"]
        assert app_ir.assets["images"] == ["hero.png"]
        assert app_ir.runtime_targets == ["android", "ios", "web"]
        assert app_ir.environment_requirements == ["node20", "python3.12"]
        assert app_ir.deployment_expectations == ["docker_compose_local", "health_ready_version"]


def test_ir_v2_constructs_have_stable_ordering(tmp_path: Path) -> None:
    root = tmp_path / "stable"
    root.mkdir()
    _write_bundle(root, "game_app", {})

    bundle = load_spec_bundle(root)
    app_ir = compile_specs_to_ir(bundle)

    assert [item["name"] for item in app_ir.navigation_flows] == ["UI-A", "UI-B"]
    assert [item["name"] for item in app_ir.state_machines] == ["MachineA", "MachineB"]
    assert [item["name"] for item in app_ir.background_jobs] == ["job-a", "job-b"]
    assert [item["name"] for item in app_ir.workers] == ["worker-1", "worker-2"]
    assert [item["channel"] for item in app_ir.realtime_channels] == ["a-room", "z-room"]
    assert [item["event"] for item in app_ir.realtime_events] == ["a-event", "z-event"]
    assert [item["name"] for item in app_ir.scenes] == ["scene-1", "scene-2"]
    assert [item["name"] for item in app_ir.game_entities] == ["entity-a", "entity-b"]
    assert [item["asset"] for item in app_ir.asset_references] == ["a.tex", "z.tex"]
