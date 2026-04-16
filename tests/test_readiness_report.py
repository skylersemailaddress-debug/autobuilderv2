from readiness.report import build_readiness_report


def test_readiness_report_includes_status_and_reasons():
    checks_result = {
        "checks": [
            {"name": "mission_runner_present", "passed": True},
            {"name": "quality_reporting_present", "passed": False},
        ]
    }

    report = build_readiness_report(
        checks_result,
        benchmark_summary={
            "total_cases": 2,
            "passed_cases": 1,
            "failed_cases": 1,
            "aggregate_scores": {"pass_rate": 0.5},
        },
        context={"total_test_count": 76},
    )

    assert "readiness_status" in report
    assert "readiness_reasons" in report
    assert report["readiness_status"] == "not-ready"
    assert isinstance(report["readiness_reasons"], list)
    assert report["total_test_count"] == 76
    assert "average_reliability" in report["benchmark_coverage_summary"]
