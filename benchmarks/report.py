from typing import Dict, List


def build_benchmark_report(results: List[Dict]) -> Dict:
    total_cases = len(results)
    passed_cases = sum(1 for result in results if result.get("success") is True)
    failed_cases = total_cases - passed_cases
    average_confidence = (
        sum(float(result.get("confidence", 0.0)) for result in results) / total_cases
        if total_cases
        else 0.0
    )

    return {
        "total_cases": total_cases,
        "passed_cases": passed_cases,
        "failed_cases": failed_cases,
        "average_confidence": average_confidence,
        "cases": results,
    }
