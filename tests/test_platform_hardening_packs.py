from platform_hardening.packs import get_pack_registry


def test_pack_registry_contains_required_pack_types_for_each_lane() -> None:
    registry = get_pack_registry()
    required = {
        "domain",
        "workflow",
        "ui",
        "validation",
        "repair",
        "deployment",
        "asset",
        "research",
        "security",
        "governance",
        "commerce",
    }

    for lane_id in (
        "first_class_commercial",
        "first_class_mobile",
        "first_class_game",
        "first_class_realtime",
        "first_class_enterprise_agent",
    ):
        profile = registry.compose_lane_profile(lane_id)
        assert set(profile["pack_types"]) == required
        assert profile["pack_count"] == len(required)


def test_pack_composition_is_deterministic() -> None:
    registry = get_pack_registry()
    first = registry.compose_lane_profile("first_class_commercial")
    second = registry.compose_lane_profile("first_class_commercial")

    assert first == second
