from state.checkpoints import Checkpoint, create_checkpoint


def test_create_checkpoint_structure():
    checkpoint = create_checkpoint("execution", {"task_count": 3}, mutation_safety={"risk_level": "high"})

    assert isinstance(checkpoint, Checkpoint)
    assert checkpoint.stage == "execution"
    assert checkpoint.metadata == {"task_count": 3}
    assert checkpoint.checkpoint_id.startswith("execution-")
    assert checkpoint.created_at
    assert checkpoint.manifest_version == "v3"
    assert checkpoint.rollback_reference.startswith("rollback:")
    assert checkpoint.restore_hint["strategy"] == "checkpoint_restore"
    assert checkpoint.mutation_safety["risk_level"] == "high"
    assert checkpoint.manifest["stage"] == "execution"
    assert checkpoint.restore_metadata["durable"] is True
    assert checkpoint.failure_semantics["on_restore_failure"] == "halt_and_escalate"


def test_checkpoint_captures_restore_plan_and_actor_metadata():
    checkpoint = create_checkpoint(
        "ship",
        {"build_id": "build-1"},
        mutation_safety={"risk_level": "dangerous", "irreversible_operation": True},
        command="ship",
        actor="autobuilder",
    )

    assert checkpoint.command == "ship"
    assert checkpoint.actor == "autobuilder"
    assert checkpoint.manifest["command"] == "ship"
    assert checkpoint.restore_plan["dangerous_mutation_guard"] is True
    assert checkpoint.restore_metadata["restorable"] is False
    assert checkpoint.failure_semantics["on_irreversible_mutation"] == "block_without_approval"
