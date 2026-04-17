from pathlib import Path

from platform_hardening.capability_maturity import CAPABILITY_FAMILY_MATURITY, LANE_CONTRACTS
from platform_hardening.composition import VALID_COMPOSITION_PATTERNS
from platform_hardening.packs import list_domain_vertical_foundations


def _docs_text() -> str:
    project_root = Path(__file__).resolve().parents[1]
    return "\n".join(
        [
            (project_root / "README.md").read_text(encoding="utf-8"),
            (project_root / "docs" / "SPEC_COMPILER.md").read_text(encoding="utf-8"),
            (project_root / "docs" / "OPERATOR_WORKFLOW.md").read_text(encoding="utf-8"),
        ]
    ).lower()


def test_docs_cover_registered_lane_ids_and_capability_families() -> None:
    text = _docs_text()

    for lane_id in sorted(LANE_CONTRACTS):
        assert lane_id in text

    for family in sorted(CAPABILITY_FAMILY_MATURITY):
        assert family in text



def test_docs_cover_registered_composition_patterns() -> None:
    text = _docs_text()

    for pattern_id in sorted(VALID_COMPOSITION_PATTERNS):
        assert pattern_id in text



def test_domain_foundations_include_breadth_categories_without_overclaiming() -> None:
    foundations = list_domain_vertical_foundations()
    merged = sorted({item for values in foundations.values() for item in values})

    assert any("coaching" in item for item in merged)
    assert any("enterprise" in item for item in merged)
    assert any("workflow" in item for item in merged)
    assert any("monitoring" in item or "realtime" in item for item in merged)
    assert any("legal" in item or "accounting" in item or "regulated" in item for item in merged)



def test_maturity_honesty_for_advanced_families_remains_bounded_or_structural() -> None:
    assert CAPABILITY_FAMILY_MATURITY["chat-first"]["maturity"] == "bounded_prototype"
    assert CAPABILITY_FAMILY_MATURITY["agent-runtime"]["maturity"] == "bounded_prototype"
    assert CAPABILITY_FAMILY_MATURITY["self-extension"]["maturity"] == "bounded_prototype"
    assert CAPABILITY_FAMILY_MATURITY["cross-lane-composition"]["maturity"] == "bounded_prototype"
    assert CAPABILITY_FAMILY_MATURITY["multimodal-world-state"]["maturity"] == "structural_only"
