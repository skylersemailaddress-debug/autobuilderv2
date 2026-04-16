from typing import Dict, List


def compute_per_case_score(result: Dict) -> Dict:
    final_status = result.get("final_status", "unknown")
    confidence = float(result.get("confidence", 0.0))
    repair_count = int(result.get("repair_count", 0))
    success = bool(result.get("success", False))
    approval_required = bool(result.get("approval_required", False))
    resumed = bool(result.get("resumed", False))
    reliability = float(result.get("reliability_summary", {}).get("score", 0.0))
    reproducible = bool(result.get("reproducible", False))
    replayable_failures = int(result.get("replayable_failures", 0))

    quality_score = max(confidence, reliability)
    if success:
        quality_score += 0.25
    if final_status == "complete":
        quality_score += 0.15
    if reproducible:
        quality_score += 0.1
    quality_score -= min(repair_count * 0.05, 0.2)
    quality_score = max(0.0, min(1.0, quality_score))

    return {
        "case": result.get("case"),
        "run_id": result.get("run_id"),
        "quality_score": quality_score,
        "success": success,
        "final_status": final_status,
        "confidence": confidence,
        "reliability": reliability,
        "repair_count": repair_count,
        "approval_required": approval_required,
        "resumed": resumed,
        "reproducible": reproducible,
        "replayable_failures": replayable_failures,
        "failure_reason": result.get("failure_reason"),
    }


def compute_benchmark_scores(results: List[Dict]) -> Dict:
    total = len(results)
    if total == 0:
        return {
            "pass_rate": 0.0,
            "average_confidence": 0.0,
            "average_reliability": 0.0,
            "average_repair_count": 0.0,
            "approval_pause_rate": 0.0,
            "resumability_score": 0.0,
            "unsupported_handling_rate": 0.0,
            "reproducibility_rate": 0.0,
            "replayable_failure_rate": 0.0,
        }

    passed = sum(1 for result in results if result.get("success") is True)
    approval_paused = sum(1 for result in results if result.get("final_status") == "awaiting_approval")
    resumable_cases = [result for result in results if result.get("expected_resumable")]
    resumed_success = sum(1 for result in resumable_cases if result.get("resumed") is True and result.get("success") is True)
    unsupported_handled = sum(1 for result in results if result.get("unsupported_handled") is True)
    reproducible = sum(1 for result in results if result.get("reproducible") is True)
    replayable_failures = sum(1 for result in results if int(result.get("replayable_failures", 0)) > 0)

    return {
        "pass_rate": passed / total,
        "average_confidence": sum(float(result.get("confidence", 0.0)) for result in results) / total,
        "average_reliability": sum(float(result.get("reliability_summary", {}).get("score", 0.0)) for result in results) / total,
        "average_repair_count": sum(float(result.get("repair_count", 0.0)) for result in results) / total,
        "approval_pause_rate": approval_paused / total,
        "resumability_score": (resumed_success / len(resumable_cases)) if resumable_cases else 1.0,
        "unsupported_handling_rate": unsupported_handled / total,
        "reproducibility_rate": reproducible / total,
        "replayable_failure_rate": replayable_failures / total,
    }