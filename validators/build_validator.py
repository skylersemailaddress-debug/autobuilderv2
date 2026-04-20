from __future__ import annotations

import json
from pathlib import Path


def run() -> dict:
    root = Path("generated_apps/latest")
    result = {
        "frontend_index_exists": (root / "app" / "index.html").exists(),
        "backend_main_exists": (root / "api" / "main.py").exists(),
        "errors": [],
    }

    if not result["frontend_index_exists"]:
        result["errors"].append("frontend entry missing")
    if not result["backend_main_exists"]:
        result["errors"].append("backend main missing")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
