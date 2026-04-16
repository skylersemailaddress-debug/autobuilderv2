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