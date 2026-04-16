from state.checkpoints import Checkpoint, create_checkpoint


def test_create_checkpoint_structure():
    checkpoint = create_checkpoint("execution", {"task_count": 3}, mutation_safety={"risk_level": "high"})

    assert isinstance(checkpoint, Checkpoint)
    assert checkpoint.stage == "execution"
    assert checkpoint.metadata == {"task_count": 3}
    assert checkpoint.checkpoint_id.startswith("execution-")
    assert checkpoint.created_at
    assert checkpoint.manifest_version == "v2"
    assert checkpoint.rollback_reference.startswith("rollback:")
    assert checkpoint.restore_hint["strategy"] == "checkpoint_restore"
    assert checkpoint.mutation_safety["risk_level"] == "high"
