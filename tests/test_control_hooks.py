import json
from pathlib import Path
from cli.run import perform_run
from cli.resume import resume_saved_run


def test_run_pauses_for_approval_and_persists_control_decision():
    run_id = "approval-pause-test"
    run_dir = Path(__file__).resolve().parents[1] / "runs"
    run_dir.mkdir(exist_ok=True)

    record, saved_path = perform_run(run_id, goal="Delete production data")

    assert record["status"] == "awaiting_approval"
    assert record["awaiting_approval"] is True
    assert record["control_state"]["requires_pause"] is True
    assert record["control_state"]["allowed"] is False
    assert record["control_state"]["action"] == "run_execution"
    assert record["control_state"]["reason"].startswith("Approval required")
    assert record["approval_request"]["status"] == "pending"
    assert Path(saved_path).exists()

    reread = json.loads(Path(saved_path).read_text(encoding="utf-8"))
    assert reread["status"] == "awaiting_approval"
    assert reread["awaiting_approval"] is True
    assert "control_state" in reread


def test_resume_after_approval_completes_run(tmp_path):
    from state.json_store import JsonRunStore

    run_id = "approval-resume-test"
    record, saved_path = perform_run(run_id, goal="Migrate production database")

    assert record["status"] == "awaiting_approval"
    run_file = Path(saved_path)
    data = json.loads(run_file.read_text(encoding="utf-8"))
    data["approval_request"]["status"] = "approved"
    run_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    resumed_record, resumed_path = resume_saved_run(run_id)
    assert resumed_record is not None
    assert resumed_record["status"] == "complete"
    assert resumed_record["awaiting_approval"] is False
    assert resumed_record["summary"]["awaiting_approval"] is False
    assert resumed_record["summary"]["control_state"] == data["control_state"]
    assert resumed_record["summary"]["run_id"] == run_id
