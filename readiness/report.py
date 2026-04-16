from typing import Dict, Optional


def build_readiness_report(
    checks_result: Dict,
    benchmark_summary: Optional[Dict] = None,
    context: Optional[Dict] = None,
) -> Dict:
    context = context or {}
    checks = checks_result.get("checks", [])
    checks_by_name = {item.get("name"): item for item in checks}

    readiness_reasons = [
        f"{item['name']} failed" for item in checks if item.get("passed") is not True
    ]

    if benchmark_summary and benchmark_summary.get("failed_cases", 0) > 0:
        readiness_reasons.append("benchmark cases are failing")

    readiness_status = "max-power-ready" if not readiness_reasons else "not-ready"

    total_test_count = context.get("total_test_count")
    if total_test_count is None and benchmark_summary is not None:
        total_test_count = benchmark_summary.get("total_test_count")

    mission_support_summary = {
        "mission_runner_present": checks_by_name.get("mission_runner_present", {}).get("passed", False),
        "resume_path_present": checks_by_name.get("resume_path_present", {}).get("passed", False),
        "inspect_path_present": checks_by_name.get("inspect_path_present", {}).get("passed", False),
    }

    safety_control_summary = {
        "mutation_safety_present": checks_by_name.get("mutation_safety_present", {}).get("passed", False),
        "restore_support_present": checks_by_name.get("restore_support_present", {}).get("passed", False),
        "benchmark_harness_present": checks_by_name.get("benchmark_harness_present", {}).get("passed", False),
    }

    memory_intelligence_summary = {
        "memory_policy_present": checks_by_name.get("memory_policy_present", {}).get("passed", False),
        "quality_reporting_present": checks_by_name.get("quality_reporting_present", {}).get("passed", False),
    }

    benchmark_coverage_summary = {
        "total_cases": benchmark_summary.get("total_cases") if benchmark_summary else None,
        "passed_cases": benchmark_summary.get("passed_cases") if benchmark_summary else None,
        "failed_cases": benchmark_summary.get("failed_cases") if benchmark_summary else None,
        "pass_rate": (
            benchmark_summary.get("aggregate_scores", {}).get("pass_rate")
            if benchmark_summary
            else None
        ),
        "average_reliability": (
            benchmark_summary.get("aggregate_scores", {}).get("average_reliability")
            if benchmark_summary
            else None
        ),
        "reproducibility_rate": (
            benchmark_summary.get("aggregate_scores", {}).get("reproducibility_rate")
            if benchmark_summary
            else None
        ),
    }

    return {
        "total_test_count": total_test_count,
        "benchmark_coverage_summary": benchmark_coverage_summary,
        "mission_support_summary": mission_support_summary,
        "safety_control_summary": safety_control_summary,
        "memory_intelligence_summary": memory_intelligence_summary,
        "readiness_status": readiness_status,
        "readiness_reasons": readiness_reasons,
        "checks": checks_result,
    }
