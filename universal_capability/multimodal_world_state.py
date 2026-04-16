from __future__ import annotations


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


def build_world_state_snapshot(payload: dict[str, object]) -> dict[str, object]:
    normalized = normalize_multimodal_payload(payload)
    return {
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
        "world_state_version": "v1",
    }
