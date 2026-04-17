from __future__ import annotations

import hashlib
import json


def _list_of_strings(value: object, field: str) -> list[str]:
    if value is None:
        return []
    if not isinstance(value, list):
        raise ValueError(f"{field} must be a list of strings")
    output: list[str] = []
    for idx, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{field}[{idx}] must be a non-empty string")
        output.append(item.strip())
    return output


def normalize_multimodal_payload(payload: dict[str, object]) -> dict[str, object]:
    return {
        "text": str(payload.get("text", "")).strip(),
        "documents": _list_of_strings(payload.get("documents"), "documents"),
        "images": _list_of_strings(payload.get("images"), "images"),
        "audio": _list_of_strings(payload.get("audio"), "audio"),
        "video": _list_of_strings(payload.get("video"), "video"),
        "sensors": _list_of_strings(payload.get("sensors"), "sensors"),
        "event_streams": _list_of_strings(payload.get("event_streams"), "event_streams"),
        "notifications": _list_of_strings(payload.get("notifications"), "notifications"),
        "actions": _list_of_strings(payload.get("actions"), "actions"),
    }


def world_state_contract() -> dict[str, object]:
    return {
        "contract_version": "v2",
        "maturity": "structural_only",
        "supports": [
            "schema_normalization",
            "world_state_snapshot",
            "deterministic_signature",
            "schema_consistency_validation",
        ],
        "unsupported": [
            "live_multimodal_execution",
            "hardware_control_side_effects",
        ],
        "schema": {
            "text": {"type": "string"},
            "documents": {"type": "list[string]", "semantic": "references_only"},
            "media": {
                "images": {"type": "list[string]"},
                "audio": {"type": "list[string]"},
                "video": {"type": "list[string]"},
            },
            "live": {
                "sensors": {"type": "list[string]", "semantic": "sensor_ids"},
                "event_streams": {"type": "list[string]", "semantic": "channel_names"},
            },
            "outputs": {
                "notifications": {"type": "list[string]"},
                "actions": {"type": "list[string]", "semantic": "declared_action_ids"},
            },
        },
    }


def _signature(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def build_world_state_snapshot(payload: dict[str, object]) -> dict[str, object]:
    normalized = normalize_multimodal_payload(payload)
    consistency = {
        "document_count": len(normalized["documents"]),
        "media_count": len(normalized["images"]) + len(normalized["audio"]) + len(normalized["video"]),
        "sensor_count": len(normalized["sensors"]),
        "event_stream_count": len(normalized["event_streams"]),
        "action_count": len(normalized["actions"]),
    }
    snapshot = {
        "inputs": {
            "text": normalized["text"],
            "documents": normalized["documents"],
            "media": {
                "images": normalized["images"],
                "audio": normalized["audio"],
                "video": normalized["video"],
            },
            "live": {
                "sensors": normalized["sensors"],
                "event_streams": normalized["event_streams"],
            },
        },
        "outputs": {
            "notifications": normalized["notifications"],
            "actions": normalized["actions"],
        },
        "world_state_version": "v2",
        "contract": world_state_contract(),
        "consistency": consistency,
    }
    snapshot["snapshot_signature_sha256"] = _signature(snapshot)
    return snapshot
