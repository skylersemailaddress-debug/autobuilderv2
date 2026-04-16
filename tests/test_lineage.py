from execution.lineage import build_artifact_lineage, summarize_artifact_lineage


def test_build_artifact_lineage_links_artifacts_to_run_and_checkpoints():
    artifacts = [
        {"artifact_id": "task-1", "artifact_type": "task_output", "content": {"task_id": "task-1"}},
        {"artifact_id": "task-2", "artifact_type": "task_output", "content": {"task_id": "task-2"}},
    ]
    checkpoints = [
        {"checkpoint_id": "start-1", "stage": "start", "metadata": {}},
        {"checkpoint_id": "execute-2", "stage": "execute", "metadata": {}},
    ]

    lineage = build_artifact_lineage("run-123", artifacts, checkpoints)
    assert lineage["run_id"] == "run-123"
    assert lineage["artifact_ids"] == ["task-1", "task-2"]
    assert len(lineage["lineage"]) == 2
    assert lineage["lineage"][0]["task_id"] == "task-1"
    assert "start-1" in lineage["lineage"][0]["checkpoint_ids"]


def test_summarize_artifact_lineage_shape():
    summary = summarize_artifact_lineage("run-1", [{"artifact_id": "a-1"}], [])
    assert summary["run_id"] == "run-1"
    assert summary["artifact_lineage_count"] == 1
    assert summary["artifact_ids"] == ["a-1"]
