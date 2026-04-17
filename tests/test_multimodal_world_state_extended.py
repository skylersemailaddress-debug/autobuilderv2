"""
Tests for multimodal/world-state practical scaffolds and contracts.
"""
from universal_capability.multimodal_world_state import (
    build_audio_processing_contract,
    build_image_document_contract,
    build_sensor_event_contract,
    validate_world_state_payload,
    build_world_state_snapshot,
    normalize_multimodal_payload,
    world_state_contract,
)


# ---------------------------------------------------------------------------
# Audio contract
# ---------------------------------------------------------------------------

def test_audio_contract_structure():
    contract = build_audio_processing_contract("first_class_enterprise_agent")
    assert contract["modality"] == "audio"
    assert contract["maturity"] == "structural_only"
    assert contract["live_execution_supported"] is False
    assert "accepted_formats" in contract
    assert "ingestion_semantics" in contract
    assert "processing_scaffold" in contract
    assert "proof_requirements" in contract
    assert len(contract["proof_requirements"]) >= 2


def test_audio_contract_has_signature():
    contract = build_audio_processing_contract("first_class_mobile")
    assert "contract_signature_sha256" in contract
    assert len(contract["contract_signature_sha256"]) == 64


def test_audio_contract_deterministic():
    c1 = build_audio_processing_contract("first_class_mobile")
    c2 = build_audio_processing_contract("first_class_mobile")
    assert c1["contract_signature_sha256"] == c2["contract_signature_sha256"]


def test_audio_contract_different_lanes():
    c1 = build_audio_processing_contract("first_class_mobile")
    c2 = build_audio_processing_contract("first_class_enterprise_agent")
    assert c1["contract_signature_sha256"] != c2["contract_signature_sha256"]


# ---------------------------------------------------------------------------
# Image/document contract
# ---------------------------------------------------------------------------

def test_image_document_contract_structure():
    contract = build_image_document_contract("first_class_commercial")
    assert contract["modality"] == "image_document"
    assert contract["maturity"] == "structural_only"
    assert contract["live_execution_supported"] is False
    assert "accepted_formats" in contract
    assert "images" in contract["accepted_formats"]
    assert "documents" in contract["accepted_formats"]
    assert "ingestion_semantics" in contract
    assert "processing_scaffold" in contract


def test_image_document_contract_has_signature():
    contract = build_image_document_contract("first_class_commercial")
    assert "contract_signature_sha256" in contract
    assert len(contract["contract_signature_sha256"]) == 64


# ---------------------------------------------------------------------------
# Sensor/event contract
# ---------------------------------------------------------------------------

def test_sensor_event_contract_structure():
    contract = build_sensor_event_contract("first_class_realtime")
    assert contract["modality"] == "sensor_event"
    assert contract["maturity"] == "structural_only"
    assert contract["live_execution_supported"] is False
    assert "ingestion_semantics" in contract
    assert "event_schema" in contract
    assert "world_state_semantics" in contract
    assert "action_coordination" in contract


def test_sensor_event_world_state_deterministic():
    contract = build_sensor_event_contract("first_class_realtime")
    assert contract["world_state_semantics"]["deterministic_ordering"] is True
    assert contract["world_state_semantics"]["replay_supported"] is True


def test_sensor_event_action_approval():
    contract = build_sensor_event_contract("first_class_realtime")
    action = contract["action_coordination"]
    assert action["approval_gate"] is not None
    assert action["audit_trail_required"] is True


# ---------------------------------------------------------------------------
# World state snapshot validation
# ---------------------------------------------------------------------------

def test_validate_world_state_valid_snapshot():
    snapshot = build_world_state_snapshot({
        "text": "hello",
        "documents": ["doc1.pdf"],
        "images": ["img1.png"],
        "audio": [],
        "video": [],
        "sensors": ["sensor_a"],
        "event_streams": ["stream_x"],
        "notifications": [],
        "actions": [],
    })
    result = validate_world_state_payload(snapshot)
    assert result["valid"] is True
    assert result["issues"] == []


def test_validate_world_state_missing_key():
    result = validate_world_state_payload({"world_state_version": "v2"})
    assert result["valid"] is False
    assert any("inputs" in issue for issue in result["issues"])


def test_validate_world_state_invalid_signature():
    snapshot = build_world_state_snapshot({"text": "test"})
    snapshot_bad = {**snapshot, "snapshot_signature_sha256": "bad"}
    result = validate_world_state_payload(snapshot_bad)
    assert result["valid"] is False
    assert "invalid_snapshot_signature" in result["issues"]


def test_validate_world_state_no_false_positives():
    # A correctly built snapshot should always pass validation
    for text in ["hello world", "", "sensor update event"]:
        snapshot = build_world_state_snapshot({"text": text, "sensors": ["s1"]})
        result = validate_world_state_payload(snapshot)
        assert result["valid"] is True, f"Failed for text={text!r}: {result['issues']}"
