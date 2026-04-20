from __future__ import annotations

import json


def run() -> dict:
    result = {
        "benchmark_callable": False,
        "output_callable": False,
        "errors": [],
    }
    try:
        from benchmarks.runner import run_all
        score = run_all()
        result["benchmark_callable"] = isinstance(score, dict)
        if not result["benchmark_callable"]:
            result["errors"].append("benchmark runner did not return dict")
    except Exception as e:
        result["errors"].append(f"benchmark execution failed: {e}")

    try:
        from chat_build.output_lane import generate_app_from_spec
        output = generate_app_from_spec({"app": {"type": "web_app", "features": ["dashboard"]}, "stack": ["react", "fastapi"]})
        result["output_callable"] = isinstance(output, dict) and bool(output.get("root"))
        if not result["output_callable"]:
            result["errors"].append("output lane did not return valid artifact map")
    except Exception as e:
        result["errors"].append(f"output generation failed: {e}")

    result["ready"] = not result["errors"]
    print(json.dumps(result, indent=2))
    return result


if __name__ == "__main__":
    run()
