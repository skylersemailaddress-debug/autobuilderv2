import pytest

from platform_plugins.registry import PluginResolutionError, get_plugin_registry


def test_plugin_registration_lists_first_class_plugins() -> None:
    registry = get_plugin_registry()
    plugins = registry.list_plugins()

    plugin_ids = {item["plugin_id"] for item in plugins}
    assert "first_class_commercial.archetype" in plugin_ids
    assert "first_class_commercial.stack" in plugin_ids
    assert "first_class_commercial.generation" in plugin_ids
    assert "first_class_commercial.validation" in plugin_ids
    assert "first_class_commercial.repair" in plugin_ids
    assert "first_class_commercial.packaging" in plugin_ids
    assert "first_class_mobile.archetype" in plugin_ids
    assert "first_class_mobile.stack" in plugin_ids
    assert "first_class_mobile.generation" in plugin_ids
    assert "first_class_mobile.validation" in plugin_ids
    assert "first_class_mobile.repair" in plugin_ids
    assert "first_class_mobile.packaging" in plugin_ids
    assert "first_class_game.archetype" in plugin_ids
    assert "first_class_game.stack" in plugin_ids
    assert "first_class_game.generation" in plugin_ids
    assert "first_class_game.validation" in plugin_ids
    assert "first_class_game.repair" in plugin_ids
    assert "first_class_game.packaging" in plugin_ids


def test_plugin_resolution_is_deterministic() -> None:
    registry = get_plugin_registry()
    app_type = "saas_web_app"
    stack = {
        "frontend": "react_next",
        "backend": "fastapi",
        "database": "postgres",
        "deployment": "docker_compose",
    }

    first = registry.resolve_plugins(app_type, stack)
    second = registry.resolve_plugins(app_type, stack)

    assert first.archetype.metadata.plugin_id == second.archetype.metadata.plugin_id
    assert first.stack.metadata.plugin_id == second.stack.metadata.plugin_id
    assert first.generation.metadata.plugin_id == second.generation.metadata.plugin_id
    assert first.validation.metadata.plugin_id == second.validation.metadata.plugin_id
    assert first.repair.metadata.plugin_id == second.repair.metadata.plugin_id
    assert first.packaging.metadata.plugin_id == second.packaging.metadata.plugin_id


def test_plugin_resolution_selects_mobile_lane() -> None:
    registry = get_plugin_registry()
    resolved = registry.resolve_plugins(
        "mobile_app",
        {
            "frontend": "flutter_mobile",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
    )

    assert resolved.generation.metadata.lane_id == "first_class_mobile"
    assert resolved.validation.metadata.plugin_id == "first_class_mobile.validation"


def test_plugin_resolution_selects_game_lane() -> None:
    registry = get_plugin_registry()
    resolved = registry.resolve_plugins(
        "game_app",
        {
            "frontend": "godot_game",
            "backend": "fastapi",
            "database": "postgres",
            "deployment": "docker_compose",
        },
    )

    assert resolved.generation.metadata.lane_id == "first_class_game"
    assert resolved.validation.metadata.plugin_id == "first_class_game.validation"


def test_plugin_resolution_fails_when_no_valid_plugin_exists() -> None:
    registry = get_plugin_registry()
    with pytest.raises(PluginResolutionError, match="Unsupported commercial lane stack selection"):
        registry.resolve_plugins(
            "saas_web_app",
            {
                "frontend": "future_frontend_placeholder",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
        )


def test_plugin_resolution_fails_for_unsupported_mobile_game_combo() -> None:
    registry = get_plugin_registry()
    with pytest.raises(PluginResolutionError, match="Unsupported commercial lane stack selection"):
        registry.resolve_plugins(
            "mobile_app",
            {
                "frontend": "godot_game",
                "backend": "fastapi",
                "database": "postgres",
                "deployment": "docker_compose",
            },
        )
