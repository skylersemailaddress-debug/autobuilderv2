from quality.report import build_mission_quality_report


def test_quality_report_contains_required_sections():
    record = {
        "run_id": "run-1",
        "status": "complete",
        "confidence": 0.92,
        "repair_count": 1,
        "mutation_risk": "caution",
        "awaiting_approval": False,
        "policy": {"approval_required": False},
        "selected_memory_keys": ["summary", "goal"],
        "memory_policy_summary": {"max_memories": 3, "selected_count": 2},
    }

    report = build_mission_quality_report(record, benchmark_summary={"pass_rate": 1.0})
    assert report["run_id"] == "run-1"
    assert report["mission_status"] == "complete"
    assert report["confidence"] == 0.92
    assert report["repairs_used"] == 1
    assert report["mutation_risk"] == "caution"
    assert report["approval_usage"]["approval_required"] is False
    assert report["benchmark_context"]["pass_rate"] == 1.0
    assert report["selected_memories"]["count"] == 2
    assert "reliability_summary" in report
    assert "confidence_derivation" in report
    assert "operator_summary" in report
