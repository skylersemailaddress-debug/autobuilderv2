from execution.artifacts import Artifact


def test_artifact_dataclass_fields():
    artifact = Artifact(
        artifact_id="artifact-1",
        artifact_type="task_output",
        content={"message": "ok"},
        created_at="2026-01-01T00:00:00Z",
    )

    assert artifact.artifact_id == "artifact-1"
    assert artifact.artifact_type == "task_output"
    assert artifact.content == {"message": "ok"}
    assert artifact.created_at == "2026-01-01T00:00:00Z"
