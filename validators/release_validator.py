from __future__ import annotations

import json
from pathlib import Path


def run() -> dict:
    result = {
        "scorecard_exists": Path("artifacts/benchmark_scorecard.json").exists(),
        "package_exists": Path("generated_apps/latest.zip").exists(),
        "errors": [],
    }

    if not result["scorecard_exists"]:
        result["errors"].append("missing benchmark scorecard")
    if not result["package_exists"]:
        result["errors"].append("missing packaged artifact")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
