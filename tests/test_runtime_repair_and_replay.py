import json
from pathlib import Path

from platform_hardening.failure_replay import append_failure_corpus, emit_replay_harness
from platform_hardening.repair_runtime import (
    classify_validation_failures,
    resolve_repair_policy,
    verify_runtime_startup,
)


def test_repair_policy_resolution_is_lane_specific_and_bounded() -> None:
    commercial = resolve_repair_policy("first_class_commercial", 99)
    mobile = resolve_repair_policy("first_class_mobile", 99)
    game = resolve_repair_policy("first_class_game", 99)

    assert commercial["effective_max_repairs"] == 24
    assert mobile["effective_max_repairs"] == 20
    assert game["effective_max_repairs"] == 20


def test_failure_classification_is_machine_readable() -> None:
    validation_report = {
        "failed_items": [
            {"check": "docker", "item": "docker-compose.yml", "details": "missing"},
            {"check": "proof", "item": ".autobuilder/proof_report.json", "details": "missing"},
        ]
    }

    classified = classify_validation_failures("first_class_commercial", validation_report)
    assert len(classified) == 2
    assert all("severity" in item for item in classified)
    assert all("category" in item for item in classified)


def test_runtime_verification_reports_missing_and_present_items(tmp_path: Path) -> None:
    (tmp_path / "docker-compose.yml").write_text("services:\n", encoding="utf-8")
    (tmp_path / "frontend/app").mkdir(parents=True)
    (tmp_path / "frontend/app/page.tsx").write_text("ok", encoding="utf-8")

    report = verify_runtime_startup("first_class_commercial", tmp_path)
    assert report["total_checks"] == 4
    assert report["failed_count"] >= 1
    assert report["runtime_status"] in {"failed", "passed"}


def test_failure_corpus_and_replay_harness_outputs(tmp_path: Path) -> None:
    determinism = {
        "verified": True,
        "build_signature_sha256": "abc",
        "proof_signature_sha256": "def",
    }
    runtime = {
        "runtime_status": "failed",
        "checks": [],
        "passed_count": 0,
        "failed_count": 1,
        "total_checks": 1,
    }
    failure_classification = [
        {
            "lane_id": "first_class_mobile",
            "severity": "high",
            "check": "mobile_structure",
            "item": "pubspec.yaml",
            "details": "missing",
            "category": "missing_file",
        }
    ]

    corpus = append_failure_corpus(
        target_repo=tmp_path,
        lane_id="first_class_mobile",
        validation_status="failed",
        failure_classification=failure_classification,
        runtime_report=runtime,
    )
    replay = emit_replay_harness(
        target_repo=tmp_path,
        lane_id="first_class_mobile",
        determinism=determinism,
        validation_status="failed",
        runtime_report=runtime,
    )

    corpus_path = Path(corpus["corpus_path"])
    replay_path = Path(replay["replay_harness_path"])
    assert corpus_path.exists()
    assert replay_path.exists()

    first_line = corpus_path.read_text(encoding="utf-8").splitlines()[0]
    parsed = json.loads(first_line)
    assert parsed["lane_id"] == "first_class_mobile"
    assert "entry_signature_sha256" in parsed

    replay_payload = json.loads(replay_path.read_text(encoding="utf-8"))
    assert replay_payload["lane_id"] == "first_class_mobile"
    assert replay_payload["determinism"]["verified"] is True
    assert "replay_signature_sha256" in replay_payload
