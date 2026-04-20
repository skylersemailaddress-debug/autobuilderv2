from __future__ import annotations

import json
from pathlib import Path


def run() -> dict:
    result = {"dev_token_present": False, "errors": []}

    # naive scan for dev-token fallback
    for path in Path(".").rglob("*.py"):
        text = path.read_text(errors="ignore")
        if "dev-token" in text.lower():
            result["dev_token_present"] = True
            result["errors"].append(f"dev-token fallback found in {path}")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
