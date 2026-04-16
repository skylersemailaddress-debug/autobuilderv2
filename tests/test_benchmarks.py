from pathlib import Path

from benchmarks.cases import BENCHMARK_CASES
from benchmarks.report import build_benchmark_report
from benchmarks.runner import run_benchmark_cases


def test_benchmark_cases_exist():
    case_names = {case.name for case in BENCHMARK_CASES}
    assert "simple_low_risk_mission" in case_names
    assert "repair_required_mission" in case_names
    assert "approval_required_dangerous_mission" in case_names
    assert "repo_targeted_mission" in case_names
    assert "nexus_mission_mode_run" in case_names
    assert "interrupted_resumable_mission" in case_names


def test_runner_returns_structured_results():
    selected_cases = [
        case
        for case in BENCHMARK_CASES
        if case.name in {"simple_low_risk_mission", "approval_required_dangerous_mission", "nexus_mission_mode_run"}
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
        assert "repo_mode" in result
        assert "resumed" in result
        assert "expected_resumable" in result
        assert "failure_reason" in result
        assert isinstance(result["event_count"], int)

        run_path = Path(__file__).resolve().parents[1] / "runs" / f"{result['run_id']}.json"
        if run_path.exists():
            run_path.unlink()


def test_report_output_shape():
    results = [
        {
            "case": "simple_low_risk_mission",
            "run_id": "benchmark_simple",
            "success": True,
            "final_status": "complete",
            "repair_count": 1,
            "confidence": 0.9,
            "event_count": 10,
            "approval_required": False,
            "nexus_mode": False,
            "repo_mode": True,
            "resumed": False,
            "expected_resumable": False,
            "failure_reason": None,
        },
        {
            "case": "approval_required_dangerous_mission",
            "run_id": "benchmark_approval",
            "success": False,
            "final_status": "awaiting_approval",
            "repair_count": 0,
            "confidence": 0.0,
            "event_count": 3,
            "approval_required": True,
            "nexus_mode": False,
            "repo_mode": True,
            "resumed": False,
            "expected_resumable": False,
            "failure_reason": "awaiting approval",
        },
    ]

    report = build_benchmark_report(results)
    assert report["total_cases"] == 2
    assert report["passed_cases"] == 1
    assert report["failed_cases"] == 1
    assert "average_confidence" in report
    assert report["cases"] == results
    assert "aggregate_scores" in report
    assert "per_case_scores" in report
    assert "failure_reasons" in report
    assert "regression" in report
