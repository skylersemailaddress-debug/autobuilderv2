import pytest

from archetypes.catalog import ArchetypeResolutionError, resolve_archetype


def test_resolve_archetype_returns_expected_taxonomy_entry():
    archetype = resolve_archetype("copilot_chat_app")

    assert archetype.name == "copilot_chat_app"
    assert "chat_surface" in archetype.expected_surfaces
    assert "tool_safety" in archetype.expected_runtime_concerns
    assert "tool_invocation" in archetype.expected_validation_concerns


def test_resolve_archetype_rejects_unknown_app_type():
    with pytest.raises(ArchetypeResolutionError, match="Unsupported app_type"):
        resolve_archetype("desktop_suite")


def test_resolve_archetype_supports_multidomain_app_types():
    mobile = resolve_archetype("mobile_app")
    game = resolve_archetype("game_app")
    realtime = resolve_archetype("realtime_system")

    assert mobile.name == "mobile_app"
    assert "mobile_navigation" in mobile.expected_surfaces
    assert game.name == "game_app"
    assert "scene_transitions" in game.expected_validation_concerns
    assert realtime.name == "realtime_system"
    assert "event_ordering" in realtime.expected_runtime_concerns