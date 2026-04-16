from quality.reliability import build_reliability_summary, derive_build_reliability


def test_reliability_summary_generation_is_stable() -> None:
    summary = build_reliability_summary(
        "build",
        {
            "determinism": 1.0,
            "repair_success": 0.9,
            "proof_completeness": 1.0,
            "validation_completeness": 1.0,
            "rollback_availability": 1.0,
            "unsupported_feature_handling": 1.0,
            "reproducibility": 1.0,
        },
        proven=["proof certified"],
        repaired=["docs/READINESS.md"],
        reproducibility_notes=["build signature recorded"],
    )

    assert summary["flow"] == "build"
    assert 0.0 <= summary["score"] <= 1.0
    assert summary["grade"] in {"trusted", "strong", "acceptable", "watch", "weak"}
    assert summary["components"]["determinism"] == 1.0
    assert summary["proven"] == ["proof certified"]


def test_build_reliability_uses_proof_and_determinism_evidence() -> None:
    result = {
        "generated_app_validation": {
            "validation_status": "passed",
            "passed_count": 10,
            "total_checks": 10,
        },
        "repair_report": {"repaired_issues": [], "unrepaired_blockers": []},
        "determinism": {"verified": True},
        "proof_artifacts": {
            "proof_status": "certified",
            "artifact_paths": {
                "proof_report": "a",
                "readiness_report": "b",
                "validation_summary": "c",
                "determinism_signature": "d",
                "replay_harness": "e",
                "proof_bundle": "f",
            },
        },
    }

    summary = derive_build_reliability(result)
    assert summary["flow"] == "build"
    assert summary["components"]["determinism"] == 1.0
    assert summary["components"]["proof_completeness"] == 1.0
    assert summary["score"] >= 0.9