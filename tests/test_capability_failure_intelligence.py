from pathlib import Path

from universal_capability.failure_intelligence import (
    append_capability_failure,
    emit_capability_replay_case,
    summarize_capability_confidence,
)


def test_failure_replay_for_generated_capabilities(tmp_path: Path) -> None:
    failure = append_capability_failure(
        target_root=tmp_path,
        capability_id="tool::lane::validator",
        stage="sandbox_validation",
        error_message="quality below threshold",
        replay_inputs={"candidate": "validator"},
    )
    replay = emit_capability_replay_case(
        target_root=tmp_path,
        capability_id="tool::lane::validator",
        replay_inputs={"candidate": "validator"},
    )
    summary = summarize_capability_confidence(target_root=tmp_path)

    assert Path(failure["corpus_path"]).exists()
    assert Path(replay["replay_case_path"]).exists()
    assert summary["failure_count"] == 1
    assert summary["confidence"] in {"medium", "low"}
