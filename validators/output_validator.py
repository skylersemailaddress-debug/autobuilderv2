from __future__ import annotations

import json
from pathlib import Path


def run() -> dict:
    root = Path("generated_apps/latest")
    result = {
        "app_dir_exists": (root / "app").exists(),
        "backend_exists": (root / "api").exists(),
        "package_json_exists": (root / "package.json").exists(),
        "requirements_exists": (root / "requirements.txt").exists(),
        "errors": [],
    }

    if not result["app_dir_exists"]:
        result["errors"].append("Missing frontend app directory")
    if not result["backend_exists"]:
        result["errors"].append("Missing backend api directory")
    if not result["package_json_exists"]:
        result["errors"].append("Missing package.json")
    if not result["requirements_exists"]:
        result["errors"].append("Missing requirements.txt")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
