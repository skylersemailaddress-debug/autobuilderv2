import pytest

from universal_capability.multimodal_world_state import (
    build_multimodal_runtime_contract,
    build_world_state_snapshot,
    emit_multimodal_runtime_scaffolds,
    normalize_multimodal_payload,
    world_state_contract,
)


def test_multimodal_world_state_schema_normalization() -> None:
    payload = {
        "text": "monitor facility",
        "documents": ["docs/runbook.pdf"],
        "images": ["img/cam1.jpg"],
        "audio": ["audio/alarm.wav"],
        "video": ["video/stream.mp4"],
        "sensors": ["temp_sensor"],
        "event_streams": ["ops.alerts"],
        "notifications": ["notify_operator"],
        "actions": ["dispatch_team"],
    }

    normalized = normalize_multimodal_payload(payload)
    snapshot = build_world_state_snapshot(payload)

    assert normalized["text"] == "monitor facility"
    assert normalized["sensors"] == ["temp_sensor"]
    assert snapshot["inputs"]["live"]["event_streams"] == ["ops.alerts"]
    assert snapshot["outputs"]["actions"] == ["dispatch_team"]
    assert snapshot["world_state_version"] == "v2"
    assert snapshot["contract"]["maturity"] == "structural_only"
    assert snapshot["consistency"]["sensor_count"] == 1
    assert snapshot["snapshot_signature_sha256"]


def test_multimodal_schema_rejects_invalid_types() -> None:
    with pytest.raises(ValueError, match="documents must be a list"):
        normalize_multimodal_payload({"documents": "not-a-list"})


def test_world_state_contract_is_stable() -> None:
    contract = world_state_contract()
    assert contract["contract_version"] == "v2"
    assert contract["maturity"] == "structural_only"
    assert "schema" in contract
    assert contract["schema"]["live"]["event_streams"]["type"] == "list[string]"


def test_multimodal_runtime_contract_and_scaffolds_are_emitted(tmp_path) -> None:
    contract = build_multimodal_runtime_contract("first_class_realtime")
    emitted = emit_multimodal_runtime_scaffolds(tmp_path, "first_class_realtime")

    assert contract["maturity"] == "structural_only"
    assert "proof_readiness_semantics" in contract
    assert "multimodal_runtime_contract.json" in emitted["runtime_contract_path"]
    assert "MULTIMODAL_RUNTIME.md" in emitted["runbook_path"]
