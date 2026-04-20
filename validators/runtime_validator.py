from __future__ import annotations

import importlib
import json


def run() -> dict:
    result = {
        "benchmark_runner_import": False,
        "output_lane_import": False,
        "release_scorecard_import": False,
        "errors": [],
    }
    try:
        mod = importlib.import_module("benchmarks.runner")
        result["benchmark_runner_import"] = hasattr(mod, "run_all") or hasattr(mod, "run_benchmark_cases")
        if not result["benchmark_runner_import"]:
            result["errors"].append("benchmarks.runner missing canonical runner export")
    except Exception as e:
        result["errors"].append(f"benchmarks.runner import failed: {e}")

    try:
        mod = importlib.import_module("chat_build.output_lane")
        result["output_lane_import"] = hasattr(mod, "generate_app_from_spec")
        if not result["output_lane_import"]:
            result["errors"].append("chat_build.output_lane missing generate_app_from_spec")
    except Exception as e:
        result["errors"].append(f"chat_build.output_lane import failed: {e}")

    try:
        mod = importlib.import_module("ops.release_scorecard")
        result["release_scorecard_import"] = hasattr(mod, "build_release_scorecard")
        if not result["release_scorecard_import"]:
            result["errors"].append("ops.release_scorecard missing build_release_scorecard")
    except Exception as e:
        result["errors"].append(f"ops.release_scorecard import failed: {e}")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
