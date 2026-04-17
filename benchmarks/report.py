from typing import Dict, List

from benchmarks.scoring import compute_benchmark_scores, compute_per_case_score


def build_benchmark_report(results: List[Dict]) -> Dict:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.get("success") is True)
    failed_cases = total_cases - passed_cases
    average_confidence = (
        sum(float(result.get("confidence", 0.0)) for result in results) / total_cases
        if total_cases
        else 0.0
    )
    aggregate_scores = compute_benchmark_scores(results)
    per_case_scores = [compute_per_case_score(result) for result in results]
    failures = [
        {
            "case": result.get("case"),
            "run_id": result.get("run_id"),
            "reason": result.get("failure_reason", "unknown_failure"),
        }
        for result in results
        if result.get("success") is not True
    ]

    regression = {
        "score_vector": aggregate_scores,
        "case_outcomes": {
            result.get("case"): {
                "success": result.get("success"),
                "final_status": result.get("final_status"),
                "confidence": result.get("confidence"),
                "reliability": result.get("reliability_summary", {}).get("score"),
            }
            for result in results
        },
    }

    scenario_breakdown = {
        "ship": [result.get("case") for result in results if result.get("scenario_kind") == "ship"],
        "repair_flow": [result.get("case") for result in results if result.get("scenario_kind") == "repair_flow"],
        "unsupported_build": [result.get("case") for result in results if result.get("scenario_kind") == "unsupported_build"],
        "self_extend": [result.get("case") for result in results if result.get("scenario_kind") == "self_extend"],
        "mission": [result.get("case") for result in results if result.get("scenario_kind") in {None, "mission"}],
    }
    replay_intelligence = {
        "replayable_failure_cases": [
            {
                "case": result.get("case"),
                "replayable_failures": int(result.get("replayable_failures", 0)),
                "failure_reason": result.get("failure_reason"),
            }
            for result in results
            if int(result.get("replayable_failures", 0)) > 0
        ],
        "replayable_failure_rate": aggregate_scores.get("replayable_failure_rate", 0.0),
    }

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "average_confidence": average_confidence,
        "average_reliability": aggregate_scores.get("average_reliability", 0.0),
        "cases": results,
        "aggregate_scores": aggregate_scores,
        "per_case_scores": per_case_scores,
        "failure_reasons": failures,
        "regression": regression,
        "scenario_breakdown": scenario_breakdown,
        "replay_intelligence": replay_intelligence,
    }
