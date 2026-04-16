import pytest

from universal_capability.multimodal_world_state import (
    build_world_state_snapshot,
    normalize_multimodal_payload,
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


def test_multimodal_schema_rejects_invalid_types() -> None:
    with pytest.raises(ValueError, match="documents must be a list"):
        normalize_multimodal_payload({"documents": "not-a-list"})
