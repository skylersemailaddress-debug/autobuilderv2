from readiness.checks import run_readiness_checks


def test_readiness_checks_return_structured_results():
    result = run_readiness_checks()

    assert "checks" in result
    assert "passed_count" in result
    assert "failed_count" in result
    assert "total_checks" in result
    assert "all_passed" in result
    assert isinstance(result["checks"], list)
    assert result["total_checks"] >= 8
    assert result["passed_count"] + result["failed_count"] == result["total_checks"]
