from pathlib import Path


def test_support_matrix_categories_and_lanes_are_documented_consistently() -> None:
    project_root = Path(__file__).resolve().parents[1]
    readme = (project_root / "README.md").read_text(encoding="utf-8")
    spec = (project_root / "docs" / "SPEC_COMPILER.md").read_text(encoding="utf-8")
    operator = (project_root / "docs" / "OPERATOR_WORKFLOW.md").read_text(encoding="utf-8")

    categories = ["first_class", "bounded_prototype", "structural_only", "future"]
    for category in categories:
        assert category in readme
        assert category in spec

    lanes = [
        "first_class_commercial",
        "first_class_mobile",
        "first_class_game",
        "first_class_realtime",
        "first_class_enterprise_agent",
    ]
    for lane in lanes:
        assert lane in readme
        assert lane in spec

    assert "Support matrix scope" in operator
    assert "bounded_prototype" in operator
    assert "command safety guarantees" in readme.lower()
    assert "command safety guarantees" in spec.lower()
    assert "command safety guarantees" in operator.lower()

    capability_families = [
        "security",
        "commerce",
        "cross-lane-composition",
        "lifecycle",
        "enterprise-readiness",
    ]
    for family in capability_families:
        assert family in readme
        assert family in spec
        assert family in operator

    assert "auth dependency scaffold" in readme.lower()
    assert "billing webhook scaffold" in readme.lower()
    assert "lifecycle regeneration decisions" in readme.lower()
