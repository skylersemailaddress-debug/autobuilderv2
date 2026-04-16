from pathlib import Path

from benchmarks.cases import BENCHMARK_CASES
from benchmarks.report import build_benchmark_report
from benchmarks.runner import run_benchmark_cases


def test_benchmark_cases_exist():
    case_names = {case.name for case in BENCHMARK_CASES}
    assert "simple_run" in case_names
    assert "repair_run" in case_names
    assert "approval_run" in case_names
    assert "nexus_run" in case_names


def test_runner_returns_structured_results():
    selected_cases = [
        case for case in BENCHMARK_CASES if case.name in {"simple_run", "approval_run", "nexus_run"}
    ]
    results = run_benchmark_cases(selected_cases)

    assert len(results) == 3
    for result in results:
        assert "case" in result
        assert "run_id" in result
        assert "success" in result
        assert "final_status" in result
        assert "repair_count" in result
        assert "confidence" in result
        assert "event_count" in result
        assert "approval_required" in result
        assert isinstance(result["event_count"], int)

        run_path = Path(__file__).resolve().parents[1] / "runs" / f"{result['run_id']}.json"
        if run_path.exists():
            run_path.unlink()


def test_report_output_shape():
    results = [
        {
            "case": "simple_run",
            "run_id": "benchmark_simple",
            "success": True,
            "final_status": "complete",
            "repair_count": 1,
            "confidence": 0.9,
            "event_count": 10,
            "approval_required": False,
            "nexus_mode": False,
        },
        {
            "case": "approval_run",
            "run_id": "benchmark_approval",
            "success": False,
            "final_status": "awaiting_approval",
            "repair_count": 0,
            "confidence": 0.0,
            "event_count": 3,
            "approval_required": True,
            "nexus_mode": False,
        },
    ]

    report = build_benchmark_report(results)
    assert report["total_cases"] == 2
    assert report["passed_cases"] == 1
    assert report["failed_cases"] == 1
    assert "average_confidence" in report
    assert report["cases"] == results
