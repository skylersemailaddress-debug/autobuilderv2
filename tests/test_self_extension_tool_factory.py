from pathlib import Path

from universal_capability.governance import rollback_capability
from universal_capability.self_extension import synthesize_missing_capabilities


def test_tool_generation_validation_and_safe_registration(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    quarantine_path = tmp_path / "quarantine.json"
    sandbox = tmp_path / "sandbox"
    intelligence_root = tmp_path / "intelligence"

    result = synthesize_missing_capabilities(
        lane_id="first_class_commercial",
        requested_capabilities=["custom_validator_for_geo"],
        sandbox_root=str(sandbox),
        registry_path=str(registry_path),
        quarantine_path=str(quarantine_path),
        require_approval_for_core=True,
        approved=True,
        failure_intelligence_root=str(intelligence_root),
    )

    assert result["status"] == "extended"
    assert result["missing_capabilities"] == ["custom_validator_for_geo"]
    assert result["registered_tool_ids"]
    assert not result["quarantined_tool_ids"]
    assert "confidence" in result["confidence_summary"]


def test_quarantine_and_rollback_behavior(tmp_path: Path) -> None:
    registry_path = tmp_path / "registry.json"
    quarantine_path = tmp_path / "quarantine.json"
    sandbox = tmp_path / "sandbox"
    intelligence_root = tmp_path / "intelligence"

    quarantined = synthesize_missing_capabilities(
        lane_id="first_class_commercial",
        requested_capabilities=["core_runtime_connector"],
        sandbox_root=str(sandbox),
        registry_path=str(registry_path),
        quarantine_path=str(quarantine_path),
        require_approval_for_core=True,
        approved=False,
        failure_intelligence_root=str(intelligence_root),
    )

    assert quarantined["quarantined_tool_ids"]
    assert Path(quarantine_path).exists()
    assert quarantined["failure_intelligence"]

    accepted = synthesize_missing_capabilities(
        lane_id="first_class_commercial",
        requested_capabilities=["helper_retry_module"],
        sandbox_root=str(sandbox),
        registry_path=str(registry_path),
        quarantine_path=str(quarantine_path),
        require_approval_for_core=True,
        approved=True,
        failure_intelligence_root=str(intelligence_root),
    )

    tool_id = accepted["registered_tool_ids"][0]
    rollback = rollback_capability(registry_path=str(registry_path), tool_id=tool_id)
    assert rollback["status"] == "rolled_back"
