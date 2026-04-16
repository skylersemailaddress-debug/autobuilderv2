from benchmarks.scoring import compute_benchmark_scores, compute_per_case_score


def test_compute_benchmark_scores_structure_and_values():
    results = [
        {
            "case": "a",
            "success": True,
            "confidence": 0.9,
            "repair_count": 1,
            "final_status": "complete",
            "expected_resumable": False,
            "approval_required": False,
        },
        {
            "case": "b",
            "success": False,
            "confidence": 0.5,
            "repair_count": 0,
            "final_status": "awaiting_approval",
            "expected_resumable": True,
            "resumed": False,
            "approval_required": True,
        },
    ]

    scores = compute_benchmark_scores(results)
    assert set(scores.keys()) == {
        "pass_rate",
        "average_confidence",
        "average_repair_count",
        "approval_pause_rate",
        "resumability_score",
    }
    assert scores["pass_rate"] == 0.5
    assert scores["average_confidence"] == 0.7
    assert scores["average_repair_count"] == 0.5
    assert scores["approval_pause_rate"] == 0.5
    assert scores["resumability_score"] == 0.0


def test_compute_per_case_score_shape():
    result = {
        "case": "simple",
        "run_id": "r1",
        "success": True,
        "confidence": 0.8,
        "repair_count": 1,
        "final_status": "complete",
        "approval_required": False,
        "resumed": False,
        "failure_reason": None,
    }

    score = compute_per_case_score(result)
    assert score["case"] == "simple"
    assert score["run_id"] == "r1"
    assert 0.0 <= score["quality_score"] <= 1.0
    assert score["final_status"] == "complete"
