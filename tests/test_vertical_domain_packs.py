"""
Tests for vertical domain pack foundations: universal packs, honesty checks,
pack registry consistency.
"""
from platform_hardening.packs import (
    get_pack_registry,
    list_domain_vertical_foundations,
    list_universal_vertical_packs,
)


# ---------------------------------------------------------------------------
# Universal vertical packs
# ---------------------------------------------------------------------------

def test_universal_vertical_packs_registered():
    packs = list_universal_vertical_packs()
    assert len(packs) >= 6
    pack_ids = [p["pack_id"] for p in packs]
    assert "vertical.operations_workflow.v1" in pack_ids
    assert "vertical.productivity_coordination.v1" in pack_ids
    assert "vertical.monitoring_realtime.v1" in pack_ids
    assert "vertical.coaching_feedback.v1" in pack_ids
    assert "vertical.regulated_policy_bound.v1" in pack_ids
    assert "vertical.enterprise_admin_reporting.v1" in pack_ids


def test_universal_vertical_packs_have_capabilities():
    packs = list_universal_vertical_packs()
    for pack in packs:
        assert len(pack["capabilities"]) >= 5, f"{pack['pack_id']} has too few capabilities"


def test_vertical_pack_maturity_honest():
    packs = list_universal_vertical_packs()
    for pack in packs:
        meta = pack.get("metadata", {})
        maturity = meta.get("maturity", "")
        assert maturity in ("bounded_prototype", "structural_only", "first_class"), \
            f"{pack['pack_id']} has invalid maturity: {maturity}"


def test_regulated_pack_is_structural_only():
    packs = list_universal_vertical_packs()
    regulated = next(p for p in packs if "regulated" in p["pack_id"])
    assert regulated["metadata"]["maturity"] == "structural_only"
    assert "regulated_boundary" in regulated["metadata"]


def test_vertical_packs_have_honesty_note():
    packs = list_universal_vertical_packs()
    for pack in packs:
        meta = pack.get("metadata", {})
        assert "honesty_note" in meta, f"{pack['pack_id']} missing honesty_note"


def test_operations_workflow_pack_capabilities():
    packs = list_universal_vertical_packs()
    ops = next(p for p in packs if p["pack_id"] == "vertical.operations_workflow.v1")
    caps = ops["capabilities"]
    assert "task_assignment" in caps
    assert "approval_routing" in caps
    assert "escalation_chain" in caps


def test_monitoring_realtime_pack_safety_elevated():
    packs = list_universal_vertical_packs()
    mon = next(p for p in packs if p["pack_id"] == "vertical.monitoring_realtime.v1")
    assert mon["safety_tier"] == "elevated"


# ---------------------------------------------------------------------------
# Lane domain foundations still intact
# ---------------------------------------------------------------------------

def test_domain_foundations_all_lanes():
    foundations = list_domain_vertical_foundations()
    for lane_id in (
        "first_class_commercial",
        "first_class_mobile",
        "first_class_game",
        "first_class_realtime",
        "first_class_enterprise_agent",
    ):
        assert lane_id in foundations
        assert len(foundations[lane_id]) >= 3, f"{lane_id} lacks domain capabilities"


def test_pack_registry_all_lanes_have_domain():
    registry = get_pack_registry()
    for lane_id in (
        "first_class_commercial",
        "first_class_mobile",
        "first_class_game",
        "first_class_realtime",
        "first_class_enterprise_agent",
    ):
        domain_packs = registry.list_packs(lane_id=lane_id, pack_type="domain")
        assert len(domain_packs) >= 1, f"No domain pack for {lane_id}"


def test_pack_registry_all_lanes_have_security():
    registry = get_pack_registry()
    for lane_id in (
        "first_class_commercial",
        "first_class_mobile",
        "first_class_game",
        "first_class_realtime",
        "first_class_enterprise_agent",
    ):
        security_packs = registry.list_packs(lane_id=lane_id, pack_type="security")
        assert len(security_packs) >= 1, f"No security pack for {lane_id}"


def test_pack_registry_compose_lane_profile():
    registry = get_pack_registry()
    profile = registry.compose_lane_profile("first_class_commercial")
    assert profile["pack_count"] >= 5
    assert "domain" in profile["pack_types"]
    assert "security" in profile["pack_types"]
    assert "governance" in profile["pack_types"]
