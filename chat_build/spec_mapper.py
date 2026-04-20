from __future__ import annotations

from typing import Dict


def map_to_spec(parsed: dict) -> dict:
    return {
        "app": {
            "type": parsed.get("app_type"),
            "features": parsed.get("features", []),
        },
        "stack": parsed.get("stack", []),
        "meta": {
            "source_tokens": parsed.get("tokens", []),
            "length": parsed.get("word_count", 0),
        },
    }
