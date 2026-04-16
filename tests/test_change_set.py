from mutation.change_set import ChangeSet


def test_change_set_dataclass_fields():
    change_set = ChangeSet(
        change_id="change-123",
        action="update",
        target="README.md",
        risk_level="caution",
        requires_checkpoint=False,
        approved=True,
        applied=False,
    )

    assert change_set.change_id == "change-123"
    assert change_set.action == "update"
    assert change_set.target == "README.md"
    assert change_set.risk_level == "caution"
    assert change_set.requires_checkpoint is False
    assert change_set.approved is True
    assert change_set.applied is False
