from __future__ import annotations

import json
from pathlib import Path


def run() -> dict:
    result = {"enforcement_refs_found": False, "errors": []}

    keywords = ["authz", "policy", "enforce", "approval"]
    hits = 0

    for path in Path(".").rglob("*.py"):
        text = path.read_text(errors="ignore").lower()
        if any(k in text for k in keywords):
            hits += 1

    result["enforcement_refs_found"] = hits > 5

    if not result["enforcement_refs_found"]:
        result["errors"].append("insufficient enforcement references in repo")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
