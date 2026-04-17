from debugger.classifier import FailureClassifier
from debugger.failures import classify_replayability, summarize_failure_intelligence


def test_replayable_failure_classification_has_deterministic_signature() -> None:
    classifier = FailureClassifier()
    failure = classifier.classify(
        {
            "status": "fail",
            "reason": "tasks not complete",
            "failed_tasks": ["task-1"],
            "failed_count": 1,
        }
    )

    classified_a = classify_replayability(failure)
    classified_b = classify_replayability(failure)

    assert classified_a["replayable"] is True
    assert classified_a["replay_signature_sha256"] == classified_b["replay_signature_sha256"]
    assert classified_a["benchmark_case"]["kind"] == "failure_replay"


def test_failure_intelligence_summary_tracks_replayable_cases() -> None:
    classifier = FailureClassifier()
    failures = [
        classifier.classify(
            {
                "status": "fail",
                "reason": "tasks not complete",
                "failed_tasks": ["task-1"],
                "failed_count": 1,
            }
        ),
        classifier.classify(
            {
                "status": "fail",
                "reason": "validation crashed",
                "failed_tasks": ["task-2"],
                "failed_count": 1,
            }
        ),
    ]

    summary = summarize_failure_intelligence(failures)
    assert summary["failure_count"] == 2
    assert summary["replayable_count"] == 2
    assert len(summary["benchmark_cases"]) == 2
